from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.domain.enums import (
    DurationBucket,
    InteractionChannel,
    InteractionSource,
    InteractionType,
)
from app.domain.value_objects import Confidence, normalize_optional_text, normalize_utc


@dataclass(frozen=True, slots=True)
class InteractionEvent:
    id: UUID
    occurred_at: datetime
    channel: InteractionChannel
    type: InteractionType
    participant_ids: tuple[UUID, ...]
    source: InteractionSource
    confidence: Confidence
    created_at: datetime
    conversation_participant_count: int | None = None
    duration_bucket: DurationBucket | None = None
    activity_id: UUID | None = None
    community_id: UUID | None = None
    project_id: UUID | None = None
    initiator_person_id: UUID | None = None
    created_by_person_id: UUID | None = None
    source_system: str | None = None
    external_event_id: str | None = None

    def __post_init__(self) -> None:
        occurred_at = normalize_utc(self.occurred_at, field_name="occurred_at")
        created_at = normalize_utc(self.created_at, field_name="created_at")
        if created_at < occurred_at:
            raise ValueError("created_at cannot be before occurred_at")
        object.__setattr__(self, "occurred_at", occurred_at)
        object.__setattr__(self, "created_at", created_at)

        participants = tuple(sorted(self.participant_ids, key=lambda participant: participant.int))
        if len(participants) < 2:
            raise ValueError("an interaction event requires at least two participants")
        if len(participants) != len(set(participants)):
            raise ValueError("interaction event participants must be unique")
        object.__setattr__(self, "participant_ids", participants)

        participant_count = self.conversation_participant_count
        if participant_count is not None:
            if isinstance(participant_count, bool) or participant_count < 2:
                raise ValueError("conversation_participant_count must be at least 2")
            if participant_count < len(participants):
                raise ValueError(
                    "conversation_participant_count cannot be smaller than participant_ids"
                )

        if self.created_by_person_id is not None and self.created_by_person_id not in participants:
            raise ValueError("created_by_person_id must be an interaction participant")
        if self.initiator_person_id is not None and self.initiator_person_id not in participants:
            raise ValueError("initiator_person_id must be an interaction participant")
        if (
            self.channel is InteractionChannel.ANALOG
            and self.source is InteractionSource.SELF_REPORTED
            and self.created_by_person_id is None
        ):
            raise ValueError("a self-reported analog event requires created_by_person_id")

        source_system = normalize_optional_text(self.source_system, field_name="source_system")
        external_event_id = normalize_optional_text(
            self.external_event_id,
            field_name="external_event_id",
        )
        if (source_system is None) != (external_event_id is None):
            raise ValueError("source_system and external_event_id must be provided together")
        object.__setattr__(
            self,
            "source_system",
            source_system.casefold() if source_system is not None else None,
        )
        object.__setattr__(self, "external_event_id", external_event_id)
