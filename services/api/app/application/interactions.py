from collections.abc import Callable, Iterable, Mapping
from contextlib import AbstractContextManager
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Protocol
from uuid import UUID, uuid4

from app.domain.entities import Person
from app.domain.enums import (
    DurationBucket,
    InteractionChannel,
    InteractionSource,
    InteractionType,
)
from app.domain.interactions import InteractionEvent
from app.domain.relationship_engine import RelationshipEngine
from app.domain.relationships import RelationshipContext, RelationshipProfile
from app.domain.value_objects import Confidence, PersonPair, normalize_utc

SELF_REPORT_SOURCE_SYSTEM = "network-compass-self-report"
MAXIMUM_CAPTURE_AGE = timedelta(days=30)
ALLOWED_ANALOG_TYPES = frozenset(
    {
        InteractionType.OFFICE_CHAT,
        InteractionType.COFFEE,
        InteractionType.LUNCH,
        InteractionType.DINNER,
        InteractionType.COMMUNITY,
        InteractionType.ACTIVITY,
        InteractionType.OTHER,
    }
)


class InteractionPersonNotFoundError(LookupError):
    pass


class InvalidInteractionError(ValueError):
    pass


class IdempotencyConflictError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class CaptureInteractionCommand:
    current_person_id: UUID
    other_person_id: UUID
    type: InteractionType
    duration_bucket: DurationBucket
    occurred_at: datetime
    client_request_id: UUID

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "occurred_at",
            normalize_utc(self.occurred_at, field_name="occurred_at"),
        )


@dataclass(frozen=True, slots=True)
class CaptureInteractionResult:
    interaction_id: UUID
    other_person_id: UUID
    occurred_at: datetime
    type: InteractionType
    duration_bucket: DurationBucket
    replayed: bool


class InteractionFactStore(Protocol):
    def get_person(self, person_id: UUID) -> Person | None: ...

    def get_interaction_by_source(
        self,
        source_system: str,
        external_event_id: str,
    ) -> InteractionEvent | None: ...

    def add_interaction_event(self, event: InteractionEvent) -> None: ...

    def list_interaction_events_for_pair(
        self,
        pair: PersonPair,
    ) -> tuple[InteractionEvent, ...]: ...

    def relationship_contexts(
        self,
        pairs: Iterable[PersonPair],
        *,
        calculated_at: datetime,
    ) -> Mapping[PersonPair, RelationshipContext]: ...


class InteractionProfileStore(Protocol):
    def upsert(self, profile: RelationshipProfile) -> None: ...


class InteractionCaptureService:
    def __init__(
        self,
        fact_store: InteractionFactStore,
        profile_store: InteractionProfileStore,
        *,
        transaction: Callable[[], AbstractContextManager[object]],
        clock: Callable[[], datetime] | None = None,
        id_factory: Callable[[], UUID] | None = None,
        engine: RelationshipEngine | None = None,
    ) -> None:
        self._fact_store = fact_store
        self._profile_store = profile_store
        self._transaction = transaction
        self._clock = clock or (lambda: datetime.now(UTC))
        self._id_factory = id_factory or uuid4
        self._engine = engine or RelationshipEngine()

    def capture(self, command: CaptureInteractionCommand) -> CaptureInteractionResult:
        calculated_at = normalize_utc(self._clock(), field_name="calculated_at")
        external_event_id = f"{command.current_person_id}:{command.client_request_id}"

        with self._transaction():
            current_person = self._fact_store.get_person(command.current_person_id)
            other_person = self._fact_store.get_person(command.other_person_id)
            if current_person is None or other_person is None:
                raise InteractionPersonNotFoundError("an interaction participant was not found")

            existing = self._fact_store.get_interaction_by_source(
                SELF_REPORT_SOURCE_SYSTEM,
                external_event_id,
            )
            if existing is not None:
                if not self._matches(existing, command):
                    raise IdempotencyConflictError(
                        "client_request_id was already used for different interaction content"
                    )
                return self._result(existing, command.other_person_id, replayed=True)

            self._validate(command, current_person, other_person, calculated_at)
            event = InteractionEvent(
                id=self._id_factory(),
                occurred_at=command.occurred_at,
                channel=InteractionChannel.ANALOG,
                type=command.type,
                participant_ids=(command.current_person_id, command.other_person_id),
                source=InteractionSource.SELF_REPORTED,
                confidence=Confidence(1.0),
                created_at=calculated_at,
                conversation_participant_count=2,
                duration_bucket=command.duration_bucket,
                created_by_person_id=command.current_person_id,
                source_system=SELF_REPORT_SOURCE_SYSTEM,
                external_event_id=external_event_id,
            )
            self._fact_store.add_interaction_event(event)

            pair = PersonPair.between(command.current_person_id, command.other_person_id)
            events = self._fact_store.list_interaction_events_for_pair(pair)
            context = self._fact_store.relationship_contexts(
                (pair,),
                calculated_at=calculated_at,
            )[pair]
            profile = self._engine.derive_profile(
                pair,
                events,
                calculated_at=calculated_at,
                context=context,
            )
            if profile is None:
                raise RuntimeError(
                    "the persisted interaction did not derive a relationship profile"
                )
            self._profile_store.upsert(profile)
            return self._result(event, command.other_person_id, replayed=False)

    @staticmethod
    def _validate(
        command: CaptureInteractionCommand,
        current_person: Person,
        other_person: Person,
        calculated_at: datetime,
    ) -> None:
        if command.current_person_id == command.other_person_id:
            raise InvalidInteractionError("self interactions are not permitted")
        if command.type not in ALLOWED_ANALOG_TYPES:
            raise InvalidInteractionError("the interaction type is not an analog capture type")
        if command.occurred_at > calculated_at:
            raise InvalidInteractionError("future interactions are not permitted")
        if calculated_at - command.occurred_at > MAXIMUM_CAPTURE_AGE:
            raise InvalidInteractionError("the interaction is outside the capture window")
        if current_person.joined_at > command.occurred_at:
            raise InvalidInteractionError("the interaction predates the current person's join date")
        if other_person.joined_at > command.occurred_at:
            raise InvalidInteractionError("the interaction predates the other person's join date")

    @staticmethod
    def _matches(event: InteractionEvent, command: CaptureInteractionCommand) -> bool:
        participants = tuple(
            sorted(
                (command.current_person_id, command.other_person_id),
                key=lambda item: item.int,
            )
        )
        return (
            event.channel is InteractionChannel.ANALOG
            and event.type is command.type
            and event.participant_ids == participants
            and event.source is InteractionSource.SELF_REPORTED
            and event.confidence == Confidence(1.0)
            and event.conversation_participant_count == 2
            and event.duration_bucket is command.duration_bucket
            and event.occurred_at == command.occurred_at
            and event.created_by_person_id == command.current_person_id
            and event.initiator_person_id is None
            and event.activity_id is None
            and event.community_id is None
            and event.project_id is None
        )

    @staticmethod
    def _result(
        event: InteractionEvent,
        other_person_id: UUID,
        *,
        replayed: bool,
    ) -> CaptureInteractionResult:
        if event.duration_bucket is None:
            raise RuntimeError("a captured analog interaction must retain its duration")
        return CaptureInteractionResult(
            interaction_id=event.id,
            other_person_id=other_person_id,
            occurred_at=event.occurred_at,
            type=event.type,
            duration_bucket=event.duration_bucket,
            replayed=replayed,
        )
