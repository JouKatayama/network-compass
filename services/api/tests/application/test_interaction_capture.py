from collections.abc import Iterable, Iterator, Mapping
from contextlib import contextmanager
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest

from app.application.interactions import (
    CaptureInteractionCommand,
    IdempotencyConflictError,
    InteractionCaptureService,
    InvalidInteractionError,
)
from app.domain.entities import Person
from app.domain.enums import DurationBucket, HireType, InteractionType, RelationshipState
from app.domain.interactions import InteractionEvent
from app.domain.relationships import RelationshipContext, RelationshipProfile
from app.domain.value_objects import PersonPair

NOW = datetime(2026, 8, 10, 12, tzinfo=UTC)
CURRENT_ID = UUID(int=1)
OTHER_ID = UUID(int=2)
THIRD_ID = UUID(int=3)
EVENT_ID = UUID(int=100)
REQUEST_ID = UUID(int=200)


def _person(person_id: UUID, *, joined_at: datetime | None = None) -> Person:
    return Person(
        id=person_id,
        display_name=f"Person {person_id.int}",
        joined_at=joined_at or NOW - timedelta(days=365),
        hire_type=HireType.OTHER,
    )


class FakeFactStore:
    def __init__(self) -> None:
        self.people = {
            CURRENT_ID: _person(CURRENT_ID),
            OTHER_ID: _person(OTHER_ID),
            THIRD_ID: _person(THIRD_ID),
        }
        self.events: list[InteractionEvent] = []

    def get_person(self, person_id: UUID) -> Person | None:
        return self.people.get(person_id)

    def get_interaction_by_source(
        self,
        source_system: str,
        external_event_id: str,
    ) -> InteractionEvent | None:
        return next(
            (
                event
                for event in self.events
                if event.source_system == source_system
                and event.external_event_id == external_event_id
            ),
            None,
        )

    def add_interaction_event(self, event: InteractionEvent) -> None:
        self.events.append(event)

    def list_interaction_events_for_pair(
        self,
        pair: PersonPair,
    ) -> tuple[InteractionEvent, ...]:
        return tuple(
            event
            for event in self.events
            if pair.person_a_id in event.participant_ids
            and pair.person_b_id in event.participant_ids
        )

    def relationship_contexts(
        self,
        pairs: Iterable[PersonPair],
        *,
        calculated_at: datetime,
    ) -> Mapping[PersonPair, RelationshipContext]:
        del calculated_at
        return {pair: RelationshipContext() for pair in pairs}


class FakeProfileStore:
    def __init__(self, *, fail: bool = False) -> None:
        self.profiles: dict[PersonPair, RelationshipProfile] = {}
        self.upsert_count = 0
        self.fail = fail

    def upsert(self, profile: RelationshipProfile) -> None:
        if self.fail:
            raise RuntimeError("forced profile failure")
        self.profiles[profile.pair] = profile
        self.upsert_count += 1


def _command(**changes: object) -> CaptureInteractionCommand:
    values: dict[str, object] = {
        "current_person_id": CURRENT_ID,
        "other_person_id": OTHER_ID,
        "type": InteractionType.COFFEE,
        "duration_bucket": DurationBucket.MEDIUM,
        "occurred_at": NOW - timedelta(minutes=5),
        "client_request_id": REQUEST_ID,
    }
    values.update(changes)
    return CaptureInteractionCommand(**values)  # type: ignore[arg-type]


def _service(
    facts: FakeFactStore,
    profiles: FakeProfileStore,
) -> InteractionCaptureService:
    @contextmanager
    def transaction() -> Iterator[object]:
        event_snapshot = list(facts.events)
        profile_snapshot = dict(profiles.profiles)
        try:
            yield object()
        except Exception:
            facts.events[:] = event_snapshot
            profiles.profiles.clear()
            profiles.profiles.update(profile_snapshot)
            raise

    return InteractionCaptureService(
        facts,
        profiles,
        transaction=transaction,
        clock=lambda: NOW,
        id_factory=lambda: EVENT_ID,
    )


def test_capture_creates_factual_event_and_only_upserts_the_affected_pair() -> None:
    facts = FakeFactStore()
    profiles = FakeProfileStore()
    unrelated_pair = PersonPair.between(CURRENT_ID, THIRD_ID)
    existing = _service(facts, profiles).capture(_command(other_person_id=THIRD_ID))
    unrelated_profile = profiles.profiles[unrelated_pair]
    facts.events.clear()
    profiles.upsert_count = 0

    result = _service(facts, profiles).capture(_command())

    assert not result.replayed
    assert result.interaction_id == EVENT_ID
    assert len(facts.events) == 1
    event = facts.events[0]
    assert event.participant_ids == (CURRENT_ID, OTHER_ID)
    assert event.type is InteractionType.COFFEE
    assert event.duration_bucket is DurationBucket.MEDIUM
    assert event.confidence.value == 1.0
    assert event.created_at >= event.occurred_at
    assert event.created_by_person_id == CURRENT_ID
    assert event.initiator_person_id is None
    assert event.source_system == "network-compass-self-report"
    assert event.external_event_id == f"{CURRENT_ID}:{REQUEST_ID}"
    target_profile = profiles.profiles[PersonPair.between(CURRENT_ID, OTHER_ID)]
    assert target_profile.state is RelationshipState.NEW
    assert target_profile.model_version == "relationship-v0.1.0"
    assert profiles.profiles[unrelated_pair] == unrelated_profile
    assert profiles.upsert_count == 1
    assert existing.other_person_id == THIRD_ID


@pytest.mark.parametrize(
    "interaction_type",
    [
        InteractionType.OFFICE_CHAT,
        InteractionType.COFFEE,
        InteractionType.LUNCH,
        InteractionType.DINNER,
        InteractionType.COMMUNITY,
        InteractionType.ACTIVITY,
        InteractionType.OTHER,
    ],
)
def test_all_frozen_analog_types_are_retained(interaction_type: InteractionType) -> None:
    facts = FakeFactStore()
    profiles = FakeProfileStore()

    _service(facts, profiles).capture(_command(type=interaction_type))

    assert facts.events[0].type is interaction_type


@pytest.mark.parametrize("duration", list(DurationBucket))
def test_all_frozen_duration_buckets_are_retained(duration: DurationBucket) -> None:
    facts = FakeFactStore()
    profiles = FakeProfileStore()

    _service(facts, profiles).capture(_command(duration_bucket=duration))

    assert facts.events[0].duration_bucket is duration


def test_same_request_replays_without_a_second_event_or_recalculation() -> None:
    facts = FakeFactStore()
    profiles = FakeProfileStore()
    service = _service(facts, profiles)

    created = service.capture(_command())
    replayed = service.capture(_command())

    assert replayed == replace(created, replayed=True)
    assert len(facts.events) == 1
    assert profiles.upsert_count == 1

    with pytest.raises(IdempotencyConflictError):
        service.capture(_command(type=InteractionType.LUNCH))
    assert len(facts.events) == 1
    assert profiles.upsert_count == 1


@pytest.mark.parametrize(
    "changes",
    [
        {"other_person_id": CURRENT_ID},
        {"type": InteractionType.TEAMS_CHAT},
        {"occurred_at": NOW + timedelta(seconds=1)},
        {"occurred_at": NOW - timedelta(days=30, seconds=1)},
    ],
)
def test_invalid_interactions_leave_source_and_profiles_unchanged(
    changes: dict[str, object],
) -> None:
    facts = FakeFactStore()
    profiles = FakeProfileStore()

    with pytest.raises(InvalidInteractionError):
        _service(facts, profiles).capture(_command(**changes))

    assert facts.events == []
    assert profiles.profiles == {}


def test_profile_failure_rolls_back_the_event() -> None:
    facts = FakeFactStore()
    profiles = FakeProfileStore(fail=True)

    with pytest.raises(RuntimeError, match="forced profile failure"):
        _service(facts, profiles).capture(_command())

    assert facts.events == []
    assert profiles.profiles == {}


def test_interaction_before_a_participant_joined_leaves_no_writes() -> None:
    facts = FakeFactStore()
    facts.people[OTHER_ID] = _person(OTHER_ID, joined_at=NOW)
    profiles = FakeProfileStore()

    with pytest.raises(InvalidInteractionError):
        _service(facts, profiles).capture(_command())

    assert facts.events == []
    assert profiles.profiles == {}
