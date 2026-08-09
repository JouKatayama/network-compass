from collections.abc import Mapping
from dataclasses import dataclass
from math import isfinite
from types import MappingProxyType

from app.domain.enums import DurationBucket, InteractionType
from app.domain.value_objects import normalize_text


def _validate_positive(value: float, *, field_name: str) -> float:
    normalized = float(value)
    if not isfinite(normalized) or normalized <= 0.0:
        raise ValueError(f"{field_name} must be finite and positive")
    return normalized


def _validate_unit_interval(value: float, *, field_name: str) -> float:
    normalized = float(value)
    if not isfinite(normalized) or not 0.0 <= normalized <= 1.0:
        raise ValueError(f"{field_name} must be finite and between 0 and 1")
    return normalized


@dataclass(frozen=True, slots=True)
class RelationshipModelConfig:
    model_version: str
    type_weights: Mapping[InteractionType, float]
    duration_weights: Mapping[DurationBucket | None, float]
    current_half_life_days: Mapping[InteractionType, float]
    historical_half_life_multiplier: float
    digital_saturation_scale: float
    analog_saturation_scale: float
    historical_saturation_scale: float
    cross_channel_synergy: float
    historical_context_boost: float
    current_activation_weight: float
    historical_depth_weight: float
    social_context_boost: float
    reciprocity_boost: float
    channel_diversity_boost: float
    community_context_weight: float
    activity_context_weight: float
    project_context_weight: float
    organization_context_weight: float
    default_cadence_days: float
    minimum_cadence_days: float
    maximum_cadence_days: float
    minimum_cadence_intervals: int
    dormancy_history_threshold: float
    dormancy_activation_ceiling: float
    dormancy_ratio_threshold: float
    dormancy_minimum_elapsed_days: float
    reconnected_recent_days: float
    reconnected_gap_ratio: float
    reconnected_minimum_gap_days: float
    close_strength_threshold: float
    close_activation_threshold: float
    active_strength_threshold: float
    active_activation_threshold: float
    new_relationship_max_age_days: float

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "model_version",
            normalize_text(self.model_version, field_name="model_version"),
        )
        type_weights = dict(self.type_weights)
        half_lives = dict(self.current_half_life_days)
        duration_weights = dict(self.duration_weights)
        if set(type_weights) != set(InteractionType):
            raise ValueError("type_weights must configure every InteractionType")
        if set(half_lives) != set(InteractionType):
            raise ValueError("current_half_life_days must configure every InteractionType")
        if set(duration_weights) != {None, *DurationBucket}:
            raise ValueError("duration_weights must configure None and every DurationBucket")
        object.__setattr__(
            self,
            "type_weights",
            MappingProxyType(
                {
                    key: _validate_positive(value, field_name=f"type_weights[{key.value}]")
                    for key, value in type_weights.items()
                }
            ),
        )
        object.__setattr__(
            self,
            "current_half_life_days",
            MappingProxyType(
                {
                    key: _validate_positive(
                        value,
                        field_name=f"current_half_life_days[{key.value}]",
                    )
                    for key, value in half_lives.items()
                }
            ),
        )
        object.__setattr__(
            self,
            "duration_weights",
            MappingProxyType(
                {
                    key: _validate_positive(
                        value,
                        field_name=(
                            "duration_weights[None]"
                            if key is None
                            else f"duration_weights[{key.value}]"
                        ),
                    )
                    for key, value in duration_weights.items()
                }
            ),
        )

        positive_fields = (
            "historical_half_life_multiplier",
            "digital_saturation_scale",
            "analog_saturation_scale",
            "historical_saturation_scale",
            "default_cadence_days",
            "minimum_cadence_days",
            "maximum_cadence_days",
            "dormancy_ratio_threshold",
            "dormancy_minimum_elapsed_days",
            "reconnected_recent_days",
            "reconnected_gap_ratio",
            "reconnected_minimum_gap_days",
            "new_relationship_max_age_days",
        )
        for field_name in positive_fields:
            object.__setattr__(
                self,
                field_name,
                _validate_positive(getattr(self, field_name), field_name=field_name),
            )

        unit_interval_fields = (
            "cross_channel_synergy",
            "historical_context_boost",
            "current_activation_weight",
            "historical_depth_weight",
            "social_context_boost",
            "reciprocity_boost",
            "channel_diversity_boost",
            "community_context_weight",
            "activity_context_weight",
            "project_context_weight",
            "organization_context_weight",
            "dormancy_history_threshold",
            "dormancy_activation_ceiling",
            "close_strength_threshold",
            "close_activation_threshold",
            "active_strength_threshold",
            "active_activation_threshold",
        )
        for field_name in unit_interval_fields:
            object.__setattr__(
                self,
                field_name,
                _validate_unit_interval(getattr(self, field_name), field_name=field_name),
            )

        if (
            isinstance(self.minimum_cadence_intervals, bool)
            or not isinstance(self.minimum_cadence_intervals, int)
            or self.minimum_cadence_intervals < 1
        ):
            raise ValueError("minimum_cadence_intervals must be a positive integer")
        if not (
            self.minimum_cadence_days <= self.default_cadence_days <= self.maximum_cadence_days
        ):
            raise ValueError("default cadence must be within configured cadence bounds")
        if self.active_strength_threshold >= self.close_strength_threshold:
            raise ValueError("active strength threshold must be below close strength threshold")
        if self.active_activation_threshold >= self.close_activation_threshold:
            raise ValueError("active activation threshold must be below close activation threshold")
        total_strength_weight = (
            self.current_activation_weight
            + self.historical_depth_weight
            + self.social_context_boost
            + self.reciprocity_boost
            + self.channel_diversity_boost
        )
        if total_strength_weight > 1.0:
            raise ValueError("relationship strength weights and boosts must total at most one")


RELATIONSHIP_MODEL_V1 = RelationshipModelConfig(
    model_version="relationship-v0.1.0",
    type_weights={
        InteractionType.TEAMS_CHAT: 0.85,
        InteractionType.EMAIL: 0.65,
        InteractionType.ONLINE_1ON1: 1.40,
        InteractionType.GROUP_MEETING: 0.55,
        InteractionType.OFFICE_CHAT: 1.00,
        InteractionType.COFFEE: 1.35,
        InteractionType.LUNCH: 1.45,
        InteractionType.DINNER: 1.45,
        InteractionType.COMMUNITY: 0.30,
        InteractionType.ACTIVITY: 1.20,
        InteractionType.OTHER: 0.50,
    },
    duration_weights={
        None: 1.00,
        DurationBucket.SHORT: 0.75,
        DurationBucket.MEDIUM: 1.00,
        DurationBucket.LONG: 1.25,
    },
    current_half_life_days={
        InteractionType.TEAMS_CHAT: 45.0,
        InteractionType.EMAIL: 60.0,
        InteractionType.ONLINE_1ON1: 75.0,
        InteractionType.GROUP_MEETING: 45.0,
        InteractionType.OFFICE_CHAT: 60.0,
        InteractionType.COFFEE: 120.0,
        InteractionType.LUNCH: 120.0,
        InteractionType.DINNER: 150.0,
        InteractionType.COMMUNITY: 30.0,
        InteractionType.ACTIVITY: 120.0,
        InteractionType.OTHER: 45.0,
    },
    historical_half_life_multiplier=6.0,
    digital_saturation_scale=2.20,
    analog_saturation_scale=2.20,
    historical_saturation_scale=4.00,
    cross_channel_synergy=0.08,
    historical_context_boost=0.08,
    current_activation_weight=0.62,
    historical_depth_weight=0.32,
    social_context_boost=0.03,
    reciprocity_boost=0.015,
    channel_diversity_boost=0.015,
    community_context_weight=0.16,
    activity_context_weight=0.20,
    project_context_weight=0.24,
    organization_context_weight=0.08,
    default_cadence_days=60.0,
    minimum_cadence_days=7.0,
    maximum_cadence_days=180.0,
    minimum_cadence_intervals=2,
    dormancy_history_threshold=0.28,
    dormancy_activation_ceiling=0.25,
    dormancy_ratio_threshold=1.80,
    dormancy_minimum_elapsed_days=90.0,
    reconnected_recent_days=30.0,
    reconnected_gap_ratio=2.0,
    reconnected_minimum_gap_days=120.0,
    close_strength_threshold=0.64,
    close_activation_threshold=0.60,
    active_strength_threshold=0.35,
    active_activation_threshold=0.25,
    new_relationship_max_age_days=45.0,
)
