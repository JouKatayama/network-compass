from dataclasses import dataclass
from datetime import UTC, datetime
from math import isfinite
from uuid import UUID


def normalize_utc(value: datetime, *, field_name: str) -> datetime:
    if value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def normalize_text(value: str, *, field_name: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    return normalized


def normalize_optional_text(value: str | None, *, field_name: str) -> str | None:
    if value is None:
        return None
    return normalize_text(value, field_name=field_name)


@dataclass(frozen=True, slots=True)
class ExternalIdentifier:
    source_system: str
    external_id: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "source_system",
            normalize_text(self.source_system, field_name="source_system").casefold(),
        )
        object.__setattr__(
            self,
            "external_id",
            normalize_text(self.external_id, field_name="external_id"),
        )


@dataclass(frozen=True, slots=True)
class PersonPair:
    person_a_id: UUID
    person_b_id: UUID

    def __post_init__(self) -> None:
        if self.person_a_id == self.person_b_id:
            raise ValueError("a relationship pair cannot contain the same person twice")
        if self.person_a_id.int > self.person_b_id.int:
            raise ValueError("person pair IDs must be in canonical UUID order")

    @classmethod
    def between(cls, first_person_id: UUID, second_person_id: UUID) -> "PersonPair":
        if first_person_id.int <= second_person_id.int:
            return cls(first_person_id, second_person_id)
        return cls(second_person_id, first_person_id)

    def contains(self, person_id: UUID) -> bool:
        return person_id in (self.person_a_id, self.person_b_id)


@dataclass(frozen=True, slots=True)
class Confidence:
    value: float

    def __post_init__(self) -> None:
        normalized = float(self.value)
        if not isfinite(normalized) or not 0.0 <= normalized <= 1.0:
            raise ValueError("confidence must be a finite value between 0 and 1")
        object.__setattr__(self, "value", normalized)
