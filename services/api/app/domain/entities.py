from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.domain.enums import HireType, Visibility
from app.domain.value_objects import (
    ExternalIdentifier,
    PersonPair,
    normalize_optional_text,
    normalize_text,
    normalize_utc,
)


def _normalize_interval(
    started_at: datetime,
    ended_at: datetime | None,
    *,
    started_field: str,
    ended_field: str,
) -> tuple[datetime, datetime | None]:
    normalized_start = normalize_utc(started_at, field_name=started_field)
    normalized_end = (
        normalize_utc(ended_at, field_name=ended_field) if ended_at is not None else None
    )
    if normalized_end is not None and normalized_end < normalized_start:
        raise ValueError(f"{ended_field} cannot be before {started_field}")
    return normalized_start, normalized_end


@dataclass(frozen=True, slots=True)
class Person:
    id: UUID
    display_name: str
    joined_at: datetime
    hire_type: HireType
    primary_organization_unit_id: UUID | None = None
    external_identifiers: tuple[ExternalIdentifier, ...] = ()
    role: str | None = None
    career_level: str | None = None
    location: str | None = None
    avatar_url: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "display_name",
            normalize_text(self.display_name, field_name="display_name"),
        )
        object.__setattr__(
            self,
            "joined_at",
            normalize_utc(self.joined_at, field_name="joined_at"),
        )
        identifiers = tuple(self.external_identifiers)
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("external identifiers must be unique per person")
        object.__setattr__(self, "external_identifiers", identifiers)
        for field_name in ("role", "career_level", "location", "avatar_url"):
            object.__setattr__(
                self,
                field_name,
                normalize_optional_text(getattr(self, field_name), field_name=field_name),
            )


@dataclass(frozen=True, slots=True)
class OrganizationUnit:
    id: UUID
    name: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", normalize_text(self.name, field_name="name"))


@dataclass(frozen=True, slots=True)
class Community:
    id: UUID
    name: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", normalize_text(self.name, field_name="name"))


@dataclass(frozen=True, slots=True)
class CommunityMembership:
    person_id: UUID
    community_id: UUID
    joined_at: datetime
    left_at: datetime | None = None

    def __post_init__(self) -> None:
        joined_at, left_at = _normalize_interval(
            self.joined_at,
            self.left_at,
            started_field="joined_at",
            ended_field="left_at",
        )
        object.__setattr__(self, "joined_at", joined_at)
        object.__setattr__(self, "left_at", left_at)


@dataclass(frozen=True, slots=True)
class Activity:
    id: UUID
    name: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", normalize_text(self.name, field_name="name"))


@dataclass(frozen=True, slots=True)
class PersonActivity:
    person_id: UUID
    activity_id: UUID
    declared_at: datetime
    visibility: Visibility

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "declared_at",
            normalize_utc(self.declared_at, field_name="declared_at"),
        )


@dataclass(frozen=True, slots=True)
class Skill:
    id: UUID
    name: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", normalize_text(self.name, field_name="name"))


@dataclass(frozen=True, slots=True)
class PersonSkill:
    person_id: UUID
    skill_id: UUID
    declared_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "declared_at",
            normalize_utc(self.declared_at, field_name="declared_at"),
        )


@dataclass(frozen=True, slots=True)
class ProjectContext:
    id: UUID
    name: str
    started_at: datetime
    ended_at: datetime | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", normalize_text(self.name, field_name="name"))
        started_at, ended_at = _normalize_interval(
            self.started_at,
            self.ended_at,
            started_field="started_at",
            ended_field="ended_at",
        )
        object.__setattr__(self, "started_at", started_at)
        object.__setattr__(self, "ended_at", ended_at)


@dataclass(frozen=True, slots=True)
class ProjectParticipation:
    person_id: UUID
    project_id: UUID
    started_at: datetime
    ended_at: datetime | None = None

    def __post_init__(self) -> None:
        started_at, ended_at = _normalize_interval(
            self.started_at,
            self.ended_at,
            started_field="started_at",
            ended_field="ended_at",
        )
        object.__setattr__(self, "started_at", started_at)
        object.__setattr__(self, "ended_at", ended_at)


@dataclass(frozen=True, slots=True)
class UserRelationshipFeedback:
    id: UUID
    pair: PersonPair
    created_by_person_id: UUID
    created_at: datetime

    def __post_init__(self) -> None:
        if not self.pair.contains(self.created_by_person_id):
            raise ValueError("relationship feedback must be created by a person in the pair")
        object.__setattr__(
            self,
            "created_at",
            normalize_utc(self.created_at, field_name="created_at"),
        )
