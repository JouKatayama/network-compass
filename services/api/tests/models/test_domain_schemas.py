from datetime import UTC, datetime
from uuid import UUID

import pytest
from pydantic import ValidationError

from app.domain.enums import HireType, InteractionSource
from app.models.domain import InteractionEventSchema, PersonSchema


def valid_interaction_payload() -> dict[str, object]:
    return {
        "id": str(UUID(int=100)),
        "occurredAt": "2026-08-08T10:00:00+09:00",
        "channel": "ANALOG",
        "type": "COFFEE",
        "participantIds": [str(UUID(int=2)), str(UUID(int=1))],
        "source": "SELF_REPORTED",
        "confidence": 0.9,
        "createdAt": "2026-08-08T01:05:00Z",
        "conversationParticipantCount": 2,
        "createdByPersonId": str(UUID(int=1)),
    }


def test_interaction_schema_accepts_camel_case_and_converts_to_domain() -> None:
    schema = InteractionEventSchema.model_validate(valid_interaction_payload())
    event = schema.to_domain()

    assert event.participant_ids == (UUID(int=1), UUID(int=2))
    assert event.occurred_at == datetime(2026, 8, 8, 1, tzinfo=UTC)
    assert event.source is InteractionSource.SELF_REPORTED
    assert schema.model_dump(by_alias=True)["participantIds"] == (UUID(int=2), UUID(int=1))


def test_interaction_schema_rejects_domain_invariant_violations() -> None:
    payload = valid_interaction_payload()
    payload["participantIds"] = [str(UUID(int=1)), str(UUID(int=1))]

    with pytest.raises(ValidationError, match="participants must be unique"):
        InteractionEventSchema.model_validate(payload)


def test_interaction_schema_rejects_naive_datetimes_and_unknown_fields() -> None:
    payload = valid_interaction_payload()
    payload["occurredAt"] = "2026-08-08T10:00:00"
    payload["messageBody"] = "must never be accepted"

    with pytest.raises(ValidationError) as error:
        InteractionEventSchema.model_validate(payload)

    messages = [entry["msg"] for entry in error.value.errors()]
    assert any("timezone" in message.lower() for message in messages)
    assert any("extra" in message.lower() for message in messages)


def test_person_schema_keeps_external_ids_separate_and_rejects_duplicates() -> None:
    payload = {
        "id": str(UUID(int=1)),
        "displayName": "  Nao  ",
        "joinedAt": "2026-08-08T00:00:00Z",
        "hireType": "EXPERIENCED",
        "externalIdentifiers": [
            {"sourceSystem": " HR ", "externalId": " employee-1 "},
        ],
    }

    person = PersonSchema.model_validate(payload).to_domain()

    assert person.display_name == "Nao"
    assert person.hire_type is HireType.EXPERIENCED
    assert person.external_identifiers[0].source_system == "hr"

    payload["externalIdentifiers"] = [
        {"sourceSystem": "HR", "externalId": "employee-1"},
        {"sourceSystem": " hr ", "externalId": "employee-1"},
    ]
    with pytest.raises(ValidationError, match="must be unique"):
        PersonSchema.model_validate(payload)
