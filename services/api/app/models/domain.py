from typing import Self
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel

from app.domain.entities import Person
from app.domain.enums import (
    DurationBucket,
    HireType,
    InteractionChannel,
    InteractionSource,
    InteractionType,
)
from app.domain.interactions import InteractionEvent
from app.domain.value_objects import Confidence, ExternalIdentifier


class DomainSchema(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        extra="forbid",
        frozen=True,
        populate_by_name=True,
    )


class ExternalIdentifierSchema(DomainSchema):
    source_system: str
    external_id: str

    def to_domain(self) -> ExternalIdentifier:
        return ExternalIdentifier(
            source_system=self.source_system,
            external_id=self.external_id,
        )


class PersonSchema(DomainSchema):
    id: UUID
    display_name: str
    joined_at: AwareDatetime
    hire_type: HireType
    primary_organization_unit_id: UUID | None = None
    external_identifiers: tuple[ExternalIdentifierSchema, ...] = ()
    role: str | None = None
    career_level: str | None = None
    location: str | None = None
    avatar_url: str | None = None

    @model_validator(mode="after")
    def validate_domain_invariants(self) -> Self:
        self.to_domain()
        return self

    def to_domain(self) -> Person:
        return Person(
            id=self.id,
            display_name=self.display_name,
            joined_at=self.joined_at,
            hire_type=self.hire_type,
            primary_organization_unit_id=self.primary_organization_unit_id,
            external_identifiers=tuple(
                identifier.to_domain() for identifier in self.external_identifiers
            ),
            role=self.role,
            career_level=self.career_level,
            location=self.location,
            avatar_url=self.avatar_url,
        )


class InteractionEventSchema(DomainSchema):
    id: UUID
    occurred_at: AwareDatetime
    channel: InteractionChannel
    type: InteractionType
    participant_ids: tuple[UUID, ...]
    source: InteractionSource
    confidence: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    created_at: AwareDatetime
    conversation_participant_count: int | None = Field(default=None, ge=2)
    duration_bucket: DurationBucket | None = None
    activity_id: UUID | None = None
    community_id: UUID | None = None
    project_id: UUID | None = None
    initiator_person_id: UUID | None = None
    created_by_person_id: UUID | None = None
    source_system: str | None = None
    external_event_id: str | None = None

    @model_validator(mode="after")
    def validate_domain_invariants(self) -> Self:
        self.to_domain()
        return self

    def to_domain(self) -> InteractionEvent:
        return InteractionEvent(
            id=self.id,
            occurred_at=self.occurred_at,
            channel=self.channel,
            type=self.type,
            participant_ids=self.participant_ids,
            source=self.source,
            confidence=Confidence(self.confidence),
            created_at=self.created_at,
            conversation_participant_count=self.conversation_participant_count,
            duration_bucket=self.duration_bucket,
            activity_id=self.activity_id,
            community_id=self.community_id,
            project_id=self.project_id,
            initiator_person_id=self.initiator_person_id,
            created_by_person_id=self.created_by_person_id,
            source_system=self.source_system,
            external_event_id=self.external_event_id,
        )
