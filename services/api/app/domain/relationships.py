from dataclasses import dataclass
from datetime import datetime
from math import isfinite

from app.domain.enums import RelationshipState
from app.domain.value_objects import PersonPair, normalize_text, normalize_utc


def _normalize_unit_interval(value: float, *, field_name: str) -> float:
    normalized = float(value)
    if not isfinite(normalized) or not 0.0 <= normalized <= 1.0:
        raise ValueError(f"{field_name} must be a finite value between 0 and 1")
    return normalized


def _normalize_non_negative_count(value: int, *, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{field_name} must be a non-negative integer")
    return value


@dataclass(frozen=True, slots=True)
class RelationshipContext:
    shared_community_count: int = 0
    shared_activity_count: int = 0
    shared_project_count: int = 0
    same_primary_organization: bool = False

    def __post_init__(self) -> None:
        for field_name in (
            "shared_community_count",
            "shared_activity_count",
            "shared_project_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_non_negative_count(getattr(self, field_name), field_name=field_name),
            )
        if not isinstance(self.same_primary_organization, bool):
            raise ValueError("same_primary_organization must be a boolean")


@dataclass(frozen=True, slots=True)
class EvidenceCoverage:
    digital: float = 1.0
    analog: float = 1.0

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "digital",
            _normalize_unit_interval(self.digital, field_name="digital"),
        )
        object.__setattr__(
            self,
            "analog",
            _normalize_unit_interval(self.analog, field_name="analog"),
        )


@dataclass(frozen=True, slots=True)
class RelationshipProfile:
    pair: PersonPair
    current_activation: float
    historical_depth: float
    digital_evidence: float
    analog_evidence: float
    social_context: float
    reciprocity: float
    channel_diversity: float
    relationship_strength: float
    state: RelationshipState
    first_meaningful_interaction_at: datetime
    last_meaningful_interaction_at: datetime
    expected_cadence_days: float
    dormancy_ratio: float
    data_confidence: float
    model_version: str
    calculated_at: datetime

    def __post_init__(self) -> None:
        for field_name in (
            "current_activation",
            "historical_depth",
            "digital_evidence",
            "analog_evidence",
            "social_context",
            "reciprocity",
            "channel_diversity",
            "relationship_strength",
            "data_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_interval(getattr(self, field_name), field_name=field_name),
            )

        cadence = float(self.expected_cadence_days)
        if not isfinite(cadence) or cadence <= 0.0:
            raise ValueError("expected_cadence_days must be finite and positive")
        object.__setattr__(self, "expected_cadence_days", cadence)

        dormancy_ratio = float(self.dormancy_ratio)
        if not isfinite(dormancy_ratio) or dormancy_ratio < 0.0:
            raise ValueError("dormancy_ratio must be finite and non-negative")
        object.__setattr__(self, "dormancy_ratio", dormancy_ratio)

        first_at = normalize_utc(
            self.first_meaningful_interaction_at,
            field_name="first_meaningful_interaction_at",
        )
        last_at = normalize_utc(
            self.last_meaningful_interaction_at,
            field_name="last_meaningful_interaction_at",
        )
        calculated_at = normalize_utc(self.calculated_at, field_name="calculated_at")
        if first_at > last_at:
            raise ValueError("first meaningful interaction cannot be after the last")
        if last_at > calculated_at:
            raise ValueError("last meaningful interaction cannot be after calculation time")
        object.__setattr__(self, "first_meaningful_interaction_at", first_at)
        object.__setattr__(self, "last_meaningful_interaction_at", last_at)
        object.__setattr__(self, "calculated_at", calculated_at)
        object.__setattr__(
            self,
            "model_version",
            normalize_text(self.model_version, field_name="model_version"),
        )
