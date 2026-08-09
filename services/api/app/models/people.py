from uuid import UUID

from pydantic import AwareDatetime

from app.application.people import ConnectionType, TimelineItemType
from app.domain.enums import RelationshipState
from app.models.domain import DomainSchema


class NamedContextSchema(DomainSchema):
    id: UUID
    name: str


class PersonIdentitySchema(DomainSchema):
    person_id: UUID
    display_name: str
    role: str | None
    organization: NamedContextSchema | None
    location: str | None
    avatar_url: str | None


class RelationshipSummarySchema(DomainSchema):
    connection_type: ConnectionType
    state: RelationshipState | None
    label: str
    last_contact_at: AwareDatetime | None
    known_since: AwareDatetime | None
    known_duration_days: int | None
    history_note: str | None


class TimelineItemSchema(DomainSchema):
    item_type: TimelineItemType
    title: str
    occurred_at: AwareDatetime
    ended_at: AwareDatetime | None = None
    context: NamedContextSchema | None = None


class CommonContextSchema(DomainSchema):
    mutual_connections: tuple[PersonIdentitySchema, ...] = ()
    activities: tuple[NamedContextSchema, ...] = ()
    communities: tuple[NamedContextSchema, ...] = ()
    skills: tuple[NamedContextSchema, ...] = ()
    projects: tuple[NamedContextSchema, ...] = ()


class PersonDetailSchema(DomainSchema):
    person: PersonIdentitySchema
    relationship: RelationshipSummarySchema
    timeline: tuple[TimelineItemSchema, ...]
    common_context: CommonContextSchema
    connection_paths: tuple[tuple[UUID, ...], ...]


class PersonSearchResultSchema(DomainSchema):
    person: PersonIdentitySchema
    connection_type: ConnectionType
    relationship_state: RelationshipState | None
    relationship_label: str
    connection_path: tuple[UUID, ...]
    common_context: CommonContextSchema


class PersonSearchPageSchema(DomainSchema):
    items: tuple[PersonSearchResultSchema, ...]
    next_cursor: str | None
