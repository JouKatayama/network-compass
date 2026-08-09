from collections import defaultdict
from collections.abc import Iterable, Mapping
from datetime import datetime
from itertools import combinations
from math import exp, sqrt
from statistics import median_low
from uuid import UUID

from app.domain.enums import InteractionChannel, RelationshipState
from app.domain.interactions import InteractionEvent
from app.domain.relationship_config import RELATIONSHIP_MODEL_V1, RelationshipModelConfig
from app.domain.relationships import EvidenceCoverage, RelationshipContext, RelationshipProfile
from app.domain.value_objects import PersonPair, normalize_utc

SECONDS_PER_DAY = 86_400.0


def _clamp_unit(value: float) -> float:
    return min(max(value, 0.0), 1.0)


def _saturate(raw_evidence: float, *, scale: float) -> float:
    return 1.0 - exp(-raw_evidence / scale)


def _union(first: float, second: float) -> float:
    return first + second - first * second


class RelationshipEngine:
    def __init__(self, config: RelationshipModelConfig = RELATIONSHIP_MODEL_V1) -> None:
        self._config = config

    @property
    def config(self) -> RelationshipModelConfig:
        return self._config

    def derive_profile(
        self,
        pair: PersonPair,
        events: Iterable[InteractionEvent],
        *,
        calculated_at: datetime,
        context: RelationshipContext | None = None,
        coverage: EvidenceCoverage | None = None,
    ) -> RelationshipProfile | None:
        calculation_time = normalize_utc(calculated_at, field_name="calculated_at")
        relevant_events = tuple(
            sorted(
                (
                    event
                    for event in events
                    if event.occurred_at <= calculation_time
                    and pair.person_a_id in event.participant_ids
                    and pair.person_b_id in event.participant_ids
                ),
                key=lambda event: (event.occurred_at, event.id.int),
            )
        )
        if not relevant_events:
            return None

        relationship_context = context or RelationshipContext()
        evidence_coverage = coverage or EvidenceCoverage()
        social_context = self._social_context(relationship_context)

        current_raw: dict[InteractionChannel, float] = defaultdict(float)
        historical_raw: dict[InteractionChannel, float] = defaultdict(float)
        directional_raw: dict[UUID, float] = defaultdict(float)
        confidence_numerator = 0.0
        confidence_denominator = 0.0

        for event in relevant_events:
            participant_count = event.conversation_participant_count or len(event.participant_ids)
            group_factor = 1.0 / sqrt(max(participant_count - 1, 1))
            duration_factor = self._config.duration_weights[event.duration_bucket]
            unconfident_evidence = (
                self._config.type_weights[event.type] * group_factor * duration_factor
            )
            evidence = unconfident_evidence * event.confidence.value
            age_days = max(
                (calculation_time - event.occurred_at).total_seconds() / SECONDS_PER_DAY,
                0.0,
            )
            current_half_life = self._config.current_half_life_days[event.type]
            current_decay = 2.0 ** (-age_days / current_half_life)
            historical_decay = 2.0 ** (
                -age_days / (current_half_life * self._config.historical_half_life_multiplier)
            )
            current_event_evidence = evidence * current_decay
            current_raw[event.channel] += current_event_evidence
            historical_raw[event.channel] += evidence * historical_decay
            if event.initiator_person_id is not None and pair.contains(event.initiator_person_id):
                directional_raw[event.initiator_person_id] += current_event_evidence
            confidence_numerator += unconfident_evidence * event.confidence.value
            confidence_denominator += unconfident_evidence

        digital_evidence = _saturate(
            current_raw[InteractionChannel.DIGITAL],
            scale=self._config.digital_saturation_scale,
        )
        analog_evidence = _saturate(
            current_raw[InteractionChannel.ANALOG],
            scale=self._config.analog_saturation_scale,
        )
        current_activation = _clamp_unit(
            _union(digital_evidence, analog_evidence)
            + self._config.cross_channel_synergy * min(digital_evidence, analog_evidence)
        )

        historical_digital = _saturate(
            historical_raw[InteractionChannel.DIGITAL],
            scale=self._config.historical_saturation_scale,
        )
        historical_analog = _saturate(
            historical_raw[InteractionChannel.ANALOG],
            scale=self._config.historical_saturation_scale,
        )
        historical_depth = _clamp_unit(
            _union(historical_digital, historical_analog)
            + self._config.historical_context_boost * social_context
        )

        reciprocity = self._reciprocity(pair, directional_raw)
        channel_diversity = float(
            current_raw[InteractionChannel.DIGITAL] > 0.0
            and current_raw[InteractionChannel.ANALOG] > 0.0
        )
        relationship_strength = _clamp_unit(
            self._config.current_activation_weight * current_activation
            + self._config.historical_depth_weight * historical_depth
            + self._config.social_context_boost * social_context
            + self._config.reciprocity_boost * reciprocity
            + self._config.channel_diversity_boost * channel_diversity
        )

        interaction_times = tuple(sorted({event.occurred_at for event in relevant_events}))
        first_interaction_at = interaction_times[0]
        last_interaction_at = interaction_times[-1]
        expected_cadence_days = self._expected_cadence_days(interaction_times)
        days_since_last = max(
            (calculation_time - last_interaction_at).total_seconds() / SECONDS_PER_DAY,
            0.0,
        )
        dormancy_ratio = days_since_last / expected_cadence_days
        state = self._state(
            current_activation=current_activation,
            historical_depth=historical_depth,
            relationship_strength=relationship_strength,
            interaction_times=interaction_times,
            calculated_at=calculation_time,
            dormancy_ratio=dormancy_ratio,
        )
        average_event_confidence = (
            confidence_numerator / confidence_denominator if confidence_denominator > 0.0 else 0.0
        )
        evidence_volume_confidence = 1.0 - exp(-len(relevant_events) / 3.0)
        collection_coverage = (evidence_coverage.digital + evidence_coverage.analog) / 2.0
        data_confidence = _clamp_unit(
            0.60 * average_event_confidence
            + 0.25 * collection_coverage
            + 0.15 * evidence_volume_confidence
        )

        return RelationshipProfile(
            pair=pair,
            current_activation=current_activation,
            historical_depth=historical_depth,
            digital_evidence=digital_evidence,
            analog_evidence=analog_evidence,
            social_context=social_context,
            reciprocity=reciprocity,
            channel_diversity=channel_diversity,
            relationship_strength=relationship_strength,
            state=state,
            first_meaningful_interaction_at=first_interaction_at,
            last_meaningful_interaction_at=last_interaction_at,
            expected_cadence_days=expected_cadence_days,
            dormancy_ratio=dormancy_ratio,
            data_confidence=data_confidence,
            model_version=self._config.model_version,
            calculated_at=calculation_time,
        )

    def derive_profiles(
        self,
        events: Iterable[InteractionEvent],
        *,
        calculated_at: datetime,
        contexts: Mapping[PersonPair, RelationshipContext] | None = None,
        coverages: Mapping[PersonPair, EvidenceCoverage] | None = None,
    ) -> tuple[RelationshipProfile, ...]:
        calculation_time = normalize_utc(calculated_at, field_name="calculated_at")
        event_tuple = tuple(events)
        pairs = {
            PersonPair.between(first_person_id, second_person_id)
            for event in event_tuple
            if event.occurred_at <= calculation_time
            for first_person_id, second_person_id in combinations(event.participant_ids, 2)
        }
        context_by_pair = contexts or {}
        coverage_by_pair = coverages or {}
        profiles = (
            self.derive_profile(
                pair,
                event_tuple,
                calculated_at=calculation_time,
                context=context_by_pair.get(pair),
                coverage=coverage_by_pair.get(pair),
            )
            for pair in pairs
        )
        return tuple(
            sorted(
                (profile for profile in profiles if profile is not None),
                key=lambda profile: (
                    profile.pair.person_a_id.int,
                    profile.pair.person_b_id.int,
                ),
            )
        )

    def _social_context(self, context: RelationshipContext) -> float:
        raw_context = (
            self._config.community_context_weight * context.shared_community_count
            + self._config.activity_context_weight * context.shared_activity_count
            + self._config.project_context_weight * context.shared_project_count
            + self._config.organization_context_weight * float(context.same_primary_organization)
        )
        return _clamp_unit(1.0 - exp(-raw_context))

    def _reciprocity(
        self,
        pair: PersonPair,
        directional_raw: Mapping[UUID, float],
    ) -> float:
        first = directional_raw.get(pair.person_a_id, 0.0)
        second = directional_raw.get(pair.person_b_id, 0.0)
        total = first + second
        if total <= 0.0:
            return 0.0
        return _clamp_unit(2.0 * min(first, second) / total)

    def _expected_cadence_days(self, interaction_times: tuple[datetime, ...]) -> float:
        intervals = tuple(
            (later - earlier).total_seconds() / SECONDS_PER_DAY
            for earlier, later in zip(interaction_times, interaction_times[1:], strict=False)
            if later > earlier
        )
        if len(intervals) < self._config.minimum_cadence_intervals:
            return self._config.default_cadence_days
        return min(
            max(float(median_low(intervals)), self._config.minimum_cadence_days),
            self._config.maximum_cadence_days,
        )

    def _state(
        self,
        *,
        current_activation: float,
        historical_depth: float,
        relationship_strength: float,
        interaction_times: tuple[datetime, ...],
        calculated_at: datetime,
        dormancy_ratio: float,
    ) -> RelationshipState:
        days_since_last = (calculated_at - interaction_times[-1]).total_seconds() / SECONDS_PER_DAY
        if len(interaction_times) >= 2:
            gap_before_latest = (
                interaction_times[-1] - interaction_times[-2]
            ).total_seconds() / SECONDS_PER_DAY
        else:
            gap_before_latest = 0.0
        prior_expected_cadence_days = self._expected_cadence_days(interaction_times[:-1])
        reconnected_gap_threshold = max(
            self._config.reconnected_minimum_gap_days,
            self._config.reconnected_gap_ratio * prior_expected_cadence_days,
        )
        if (
            len(interaction_times) >= 3
            and historical_depth >= self._config.dormancy_history_threshold
            and days_since_last <= self._config.reconnected_recent_days
            and gap_before_latest >= reconnected_gap_threshold
        ):
            return RelationshipState.RECONNECTED
        if (
            historical_depth >= self._config.dormancy_history_threshold
            and current_activation <= self._config.dormancy_activation_ceiling
            and days_since_last >= self._config.dormancy_minimum_elapsed_days
            and dormancy_ratio >= self._config.dormancy_ratio_threshold
        ):
            return RelationshipState.DORMANT
        if (
            relationship_strength >= self._config.close_strength_threshold
            and current_activation >= self._config.close_activation_threshold
        ):
            return RelationshipState.CLOSE

        relationship_age_days = (
            calculated_at - interaction_times[0]
        ).total_seconds() / SECONDS_PER_DAY
        if (
            relationship_age_days <= self._config.new_relationship_max_age_days
            and len(interaction_times) <= 2
        ):
            return RelationshipState.NEW
        if (
            relationship_strength >= self._config.active_strength_threshold
            and current_activation >= self._config.active_activation_threshold
        ):
            return RelationshipState.ACTIVE
        return RelationshipState.WEAK
