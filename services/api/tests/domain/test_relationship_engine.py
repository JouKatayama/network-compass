from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest

from app.domain.enums import (
    DurationBucket,
    InteractionChannel,
    InteractionSource,
    InteractionType,
    RelationshipState,
)
from app.domain.interactions import InteractionEvent
from app.domain.relationship_config import RELATIONSHIP_MODEL_V1
from app.domain.relationship_engine import RelationshipEngine
from app.domain.relationships import EvidenceCoverage, RelationshipContext
from app.domain.value_objects import Confidence, PersonPair

CALCULATED_AT = datetime(2026, 8, 9, 12, tzinfo=UTC)


def _person_id(index: int) -> UUID:
    return UUID(int=index)


def _event(
    index: int,
    participant_ids: tuple[UUID, ...],
    *,
    days_ago: int,
    channel: InteractionChannel,
    interaction_type: InteractionType,
    confidence: float = 0.9,
    initiator_person_id: UUID | None = None,
    conversation_participant_count: int | None = None,
    duration_bucket: DurationBucket | None = DurationBucket.MEDIUM,
) -> InteractionEvent:
    occurred_at = CALCULATED_AT - timedelta(days=days_ago)
    return InteractionEvent(
        id=UUID(int=10_000 + index),
        occurred_at=occurred_at,
        channel=channel,
        type=interaction_type,
        participant_ids=participant_ids,
        source=(
            InteractionSource.SYSTEM
            if channel is InteractionChannel.DIGITAL
            else InteractionSource.MUTUAL_CONFIRMED
        ),
        confidence=Confidence(confidence),
        created_at=occurred_at + timedelta(minutes=5),
        conversation_participant_count=conversation_participant_count,
        duration_bucket=duration_bucket,
        initiator_person_id=initiator_person_id,
    )


def _series(
    first_person_id: UUID,
    second_person_id: UUID,
    *,
    channel: InteractionChannel,
    interaction_type: InteractionType,
    confidence: float = 0.9,
) -> tuple[InteractionEvent, ...]:
    return tuple(
        _event(
            index,
            (first_person_id, second_person_id),
            days_ago=days_ago,
            channel=channel,
            interaction_type=interaction_type,
            confidence=confidence,
            initiator_person_id=first_person_id,
        )
        for index, days_ago in enumerate((4, 12, 20, 28, 36, 44), start=1)
    )


def test_versioned_configuration_covers_every_evidence_dimension() -> None:
    assert RELATIONSHIP_MODEL_V1.model_version == "relationship-v0.1.0"
    assert set(RELATIONSHIP_MODEL_V1.type_weights) == set(InteractionType)
    assert set(RELATIONSHIP_MODEL_V1.current_half_life_days) == set(InteractionType)
    assert set(RELATIONSHIP_MODEL_V1.duration_weights) == {None, *DurationBucket}


def test_relationship_context_and_coverage_reject_invalid_values() -> None:
    with pytest.raises(ValueError, match="non-negative integer"):
        RelationshipContext(shared_community_count=-1)
    with pytest.raises(ValueError, match="non-negative integer"):
        RelationshipContext(shared_project_count=True)
    with pytest.raises(ValueError, match="between 0 and 1"):
        EvidenceCoverage(analog=-0.1)


def test_digital_only_and_analog_only_can_both_be_close() -> None:
    engine = RelationshipEngine()
    digital_pair = PersonPair.between(_person_id(1), _person_id(2))
    analog_pair = PersonPair.between(_person_id(3), _person_id(4))

    digital_profile = engine.derive_profile(
        digital_pair,
        _series(
            digital_pair.person_a_id,
            digital_pair.person_b_id,
            channel=InteractionChannel.DIGITAL,
            interaction_type=InteractionType.TEAMS_CHAT,
        ),
        calculated_at=CALCULATED_AT,
    )
    analog_profile = engine.derive_profile(
        analog_pair,
        _series(
            analog_pair.person_a_id,
            analog_pair.person_b_id,
            channel=InteractionChannel.ANALOG,
            interaction_type=InteractionType.COFFEE,
        ),
        calculated_at=CALCULATED_AT,
    )

    assert digital_profile is not None
    assert analog_profile is not None
    assert digital_profile.state is RelationshipState.CLOSE
    assert analog_profile.state is RelationshipState.CLOSE
    assert digital_profile.analog_evidence == 0.0
    assert analog_profile.digital_evidence == 0.0


def test_shared_context_without_interaction_does_not_create_relationship() -> None:
    profile = RelationshipEngine().derive_profile(
        PersonPair.between(_person_id(1), _person_id(2)),
        (),
        calculated_at=CALCULATED_AT,
        context=RelationshipContext(
            shared_community_count=3,
            shared_activity_count=2,
            shared_project_count=4,
            same_primary_organization=True,
        ),
    )

    assert profile is None


def test_context_is_bounded_and_only_boosts_existing_evidence() -> None:
    engine = RelationshipEngine()
    pair = PersonPair.between(_person_id(1), _person_id(2))
    events = (
        _event(
            1,
            (pair.person_a_id, pair.person_b_id),
            days_ago=50,
            channel=InteractionChannel.DIGITAL,
            interaction_type=InteractionType.ONLINE_1ON1,
        ),
    )

    plain = engine.derive_profile(pair, events, calculated_at=CALCULATED_AT)
    contextual = engine.derive_profile(
        pair,
        events,
        calculated_at=CALCULATED_AT,
        context=RelationshipContext(
            shared_community_count=8,
            shared_activity_count=8,
            shared_project_count=8,
            same_primary_organization=True,
        ),
    )

    assert plain is not None
    assert contextual is not None
    assert contextual.social_context < 1.0
    assert contextual.historical_depth > plain.historical_depth
    assert contextual.relationship_strength > plain.relationship_strength


def test_large_event_co_presence_contributes_only_minimal_evidence() -> None:
    participant_ids = tuple(_person_id(index) for index in range(1, 21))
    pair = PersonPair.between(participant_ids[0], participant_ids[1])
    profile = RelationshipEngine().derive_profile(
        pair,
        (
            _event(
                1,
                participant_ids,
                days_ago=25,
                channel=InteractionChannel.ANALOG,
                interaction_type=InteractionType.COMMUNITY,
                confidence=0.2,
                conversation_participant_count=len(participant_ids),
                duration_bucket=None,
            ),
        ),
        calculated_at=CALCULATED_AT,
    )

    assert profile is not None
    assert profile.state is RelationshipState.NEW
    assert profile.relationship_strength < 0.05
    assert profile.current_activation < 0.05


def test_reciprocity_uses_directional_evidence_without_penalizing_unknown_direction() -> None:
    engine = RelationshipEngine()
    one_sided_pair = PersonPair.between(_person_id(1), _person_id(2))
    reciprocal_pair = PersonPair.between(_person_id(3), _person_id(4))
    unknown_pair = PersonPair.between(_person_id(5), _person_id(6))
    one_sided_events = _series(
        one_sided_pair.person_a_id,
        one_sided_pair.person_b_id,
        channel=InteractionChannel.DIGITAL,
        interaction_type=InteractionType.TEAMS_CHAT,
    )
    reciprocal_events = tuple(
        _event(
            100 + index,
            (reciprocal_pair.person_a_id, reciprocal_pair.person_b_id),
            days_ago=days_ago,
            channel=InteractionChannel.DIGITAL,
            interaction_type=InteractionType.TEAMS_CHAT,
            initiator_person_id=(
                reciprocal_pair.person_a_id if index % 2 else reciprocal_pair.person_b_id
            ),
        )
        for index, days_ago in enumerate((4, 12, 20, 28, 36, 44), start=1)
    )
    unknown_events = tuple(
        _event(
            200 + index,
            (unknown_pair.person_a_id, unknown_pair.person_b_id),
            days_ago=days_ago,
            channel=InteractionChannel.DIGITAL,
            interaction_type=InteractionType.TEAMS_CHAT,
        )
        for index, days_ago in enumerate((4, 12, 20, 28, 36, 44), start=1)
    )

    one_sided = engine.derive_profile(
        one_sided_pair,
        one_sided_events,
        calculated_at=CALCULATED_AT,
    )
    reciprocal = engine.derive_profile(
        reciprocal_pair,
        reciprocal_events,
        calculated_at=CALCULATED_AT,
    )
    unknown = engine.derive_profile(
        unknown_pair,
        unknown_events,
        calculated_at=CALCULATED_AT,
    )

    assert one_sided is not None
    assert reciprocal is not None
    assert unknown is not None
    assert one_sided.reciprocity == 0.0
    assert unknown.reciprocity == 0.0
    assert reciprocal.reciprocity > 0.8
    assert reciprocal.relationship_strength > one_sided.relationship_strength
    assert unknown.relationship_strength == one_sided.relationship_strength


def test_adaptive_dormancy_and_reconnection_use_historical_cadence() -> None:
    engine = RelationshipEngine()
    pair = PersonPair.between(_person_id(1), _person_id(2))
    old_events = tuple(
        _event(
            300 + index,
            (pair.person_a_id, pair.person_b_id),
            days_ago=days_ago,
            channel=InteractionChannel.ANALOG,
            interaction_type=InteractionType.COFFEE,
            confidence=1.0,
        )
        for index, days_ago in enumerate((500, 430, 360, 300), start=1)
    )

    dormant = engine.derive_profile(pair, old_events, calculated_at=CALCULATED_AT)
    reconnected = engine.derive_profile(
        pair,
        (
            *old_events,
            _event(
                400,
                (pair.person_a_id, pair.person_b_id),
                days_ago=4,
                channel=InteractionChannel.ANALOG,
                interaction_type=InteractionType.COFFEE,
                confidence=1.0,
                duration_bucket=DurationBucket.LONG,
            ),
        ),
        calculated_at=CALCULATED_AT,
    )

    assert dormant is not None
    assert reconnected is not None
    assert dormant.state is RelationshipState.DORMANT
    assert dormant.expected_cadence_days == pytest.approx(70.0)
    assert reconnected.state is RelationshipState.RECONNECTED
    assert reconnected.expected_cadence_days == pytest.approx(70.0)


def test_missing_analog_coverage_lowers_confidence_not_strength() -> None:
    engine = RelationshipEngine()
    pair = PersonPair.between(_person_id(1), _person_id(2))
    events = _series(
        pair.person_a_id,
        pair.person_b_id,
        channel=InteractionChannel.DIGITAL,
        interaction_type=InteractionType.TEAMS_CHAT,
    )

    fully_observed = engine.derive_profile(
        pair,
        events,
        calculated_at=CALCULATED_AT,
        coverage=EvidenceCoverage(digital=1.0, analog=1.0),
    )
    analog_missing = engine.derive_profile(
        pair,
        events,
        calculated_at=CALCULATED_AT,
        coverage=EvidenceCoverage(digital=1.0, analog=0.0),
    )

    assert fully_observed is not None
    assert analog_missing is not None
    assert analog_missing.relationship_strength == fully_observed.relationship_strength
    assert analog_missing.state is fully_observed.state
    assert analog_missing.data_confidence < fully_observed.data_confidence


def test_source_confidence_affects_evidence_and_is_retained_in_data_confidence() -> None:
    engine = RelationshipEngine()
    high_pair = PersonPair.between(_person_id(1), _person_id(2))
    low_pair = PersonPair.between(_person_id(3), _person_id(4))
    high = engine.derive_profile(
        high_pair,
        _series(
            high_pair.person_a_id,
            high_pair.person_b_id,
            channel=InteractionChannel.DIGITAL,
            interaction_type=InteractionType.ONLINE_1ON1,
            confidence=1.0,
        ),
        calculated_at=CALCULATED_AT,
    )
    low = engine.derive_profile(
        low_pair,
        _series(
            low_pair.person_a_id,
            low_pair.person_b_id,
            channel=InteractionChannel.DIGITAL,
            interaction_type=InteractionType.ONLINE_1ON1,
            confidence=0.2,
        ),
        calculated_at=CALCULATED_AT,
    )

    assert high is not None
    assert low is not None
    assert low.relationship_strength < high.relationship_strength
    assert low.data_confidence < high.data_confidence
    assert high.model_version == RELATIONSHIP_MODEL_V1.model_version


def test_bulk_derivation_returns_one_normalized_profile_per_observed_pair() -> None:
    first, second, third, fourth = (_person_id(index) for index in range(1, 5))
    events = (
        _event(
            1,
            (third, first, second),
            days_ago=10,
            channel=InteractionChannel.DIGITAL,
            interaction_type=InteractionType.GROUP_MEETING,
            conversation_participant_count=3,
        ),
        _event(
            2,
            (second, first),
            days_ago=5,
            channel=InteractionChannel.ANALOG,
            interaction_type=InteractionType.COFFEE,
        ),
        _event(
            3,
            (third, fourth),
            days_ago=-1,
            channel=InteractionChannel.DIGITAL,
            interaction_type=InteractionType.ONLINE_1ON1,
        ),
    )

    profiles = RelationshipEngine().derive_profiles(events, calculated_at=CALCULATED_AT)

    assert len(profiles) == 3
    assert len({profile.pair for profile in profiles}) == 3
    assert all(profile.pair.person_a_id.int < profile.pair.person_b_id.int for profile in profiles)
    assert all(not profile.pair.contains(fourth) for profile in profiles)
    first_second = next(
        profile for profile in profiles if profile.pair == PersonPair.between(first, second)
    )
    assert first_second.channel_diversity == pytest.approx(1.0)
