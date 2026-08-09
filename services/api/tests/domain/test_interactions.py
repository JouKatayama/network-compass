from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest

from app.domain.enums import InteractionChannel, InteractionSource, InteractionType
from app.domain.interactions import InteractionEvent
from app.domain.value_objects import Confidence

PERSON_A = UUID(int=1)
PERSON_B = UUID(int=2)
PERSON_C = UUID(int=3)
OCCURRED_AT = datetime(2026, 8, 8, 10, tzinfo=UTC)
CREATED_AT = OCCURRED_AT + timedelta(minutes=5)


def make_event(
    *,
    participant_ids: tuple[UUID, ...] = (PERSON_A, PERSON_B),
    channel: InteractionChannel = InteractionChannel.DIGITAL,
    source: InteractionSource = InteractionSource.SYSTEM,
    created_by_person_id: UUID | None = None,
    initiator_person_id: UUID | None = None,
    conversation_participant_count: int | None = None,
    source_system: str | None = None,
    external_event_id: str | None = None,
    occurred_at: datetime = OCCURRED_AT,
    created_at: datetime = CREATED_AT,
) -> InteractionEvent:
    return InteractionEvent(
        id=UUID(int=100),
        occurred_at=occurred_at,
        channel=channel,
        type=InteractionType.ONLINE_1ON1,
        participant_ids=participant_ids,
        source=source,
        confidence=Confidence(0.8),
        created_at=created_at,
        conversation_participant_count=conversation_participant_count,
        initiator_person_id=initiator_person_id,
        created_by_person_id=created_by_person_id,
        source_system=source_system,
        external_event_id=external_event_id,
    )


def test_interaction_event_normalizes_participant_order_and_provenance() -> None:
    event = make_event(
        participant_ids=(PERSON_B, PERSON_A),
        conversation_participant_count=2,
        source_system="  Teams  ",
        external_event_id=" event-1 ",
    )

    assert event.participant_ids == (PERSON_A, PERSON_B)
    assert event.source_system == "teams"
    assert event.external_event_id == "event-1"


@pytest.mark.parametrize(
    "participant_ids",
    [(PERSON_A,), (PERSON_A, PERSON_A)],
)
def test_interaction_event_requires_two_unique_participants(
    participant_ids: tuple[UUID, ...],
) -> None:
    with pytest.raises(ValueError, match="at least two|must be unique"):
        make_event(participant_ids=participant_ids)


def test_conversation_count_cannot_be_smaller_than_recorded_participants() -> None:
    with pytest.raises(ValueError, match="cannot be smaller"):
        make_event(
            participant_ids=(PERSON_A, PERSON_B, PERSON_C),
            conversation_participant_count=2,
        )


def test_self_reported_analog_event_requires_reporting_participant() -> None:
    with pytest.raises(ValueError, match="requires created_by_person_id"):
        make_event(
            channel=InteractionChannel.ANALOG,
            source=InteractionSource.SELF_REPORTED,
        )


def test_interaction_initiator_must_be_a_participant() -> None:
    event = make_event(initiator_person_id=PERSON_A)

    assert event.initiator_person_id == PERSON_A
    with pytest.raises(ValueError, match="initiator_person_id must be an interaction participant"):
        make_event(initiator_person_id=PERSON_C)

    with pytest.raises(ValueError, match="must be an interaction participant"):
        make_event(
            channel=InteractionChannel.ANALOG,
            source=InteractionSource.SELF_REPORTED,
            created_by_person_id=PERSON_C,
        )


def test_external_event_provenance_fields_must_be_provided_together() -> None:
    with pytest.raises(ValueError, match="provided together"):
        make_event(source_system="teams")


def test_created_at_cannot_precede_occurrence() -> None:
    with pytest.raises(ValueError, match="cannot be before"):
        make_event(created_at=OCCURRED_AT - timedelta(seconds=1))
