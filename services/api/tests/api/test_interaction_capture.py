from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from network_compass_synthetic.generator import generate_dataset
from network_compass_synthetic.models import SyntheticDataset
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.application.persistence import DemoResetService
from app.domain.entities import Person
from app.domain.enums import (
    DurationBucket,
    InteractionChannel,
    InteractionSource,
    RelationshipState,
)
from app.domain.facts import CanonicalFactSet
from app.domain.value_objects import ExternalIdentifier, PersonPair
from app.infrastructure.database import Base, create_session_factory
from app.infrastructure.persistence import (
    SqlAlchemyFactRepository,
    SqlAlchemyRelationshipProfileRepository,
)
from app.main import create_app
from app.settings import ApiEnvironment, ApiSettings


@dataclass(frozen=True, slots=True)
class InteractionApiFixture:
    client: TestClient
    dataset: SyntheticDataset
    session_factory: sessionmaker[Session]


def _facts(dataset: SyntheticDataset) -> CanonicalFactSet:
    return CanonicalFactSet(
        people=dataset.people,
        organization_units=dataset.organization_units,
        communities=dataset.communities,
        community_memberships=dataset.community_memberships,
        activities=dataset.activities,
        person_activities=dataset.person_activities,
        skills=dataset.skills,
        person_skills=dataset.person_skills,
        projects=dataset.projects,
        project_participations=dataset.project_participations,
        interaction_events=dataset.interaction_events,
    )


def _person(dataset: SyntheticDataset, code: str) -> Person:
    return next(
        person
        for person in dataset.people
        if ExternalIdentifier("synthetic", code) in person.external_identifiers
    )


@pytest.fixture
def interaction_api() -> Iterator[InteractionApiFixture]:
    engine: Engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = create_session_factory(engine)
    dataset = generate_dataset("demo")
    with factory() as session, session.begin():
        DemoResetService(
            SqlAlchemyFactRepository(session),
            SqlAlchemyRelationshipProfileRepository(session),
        ).reset(
            _facts(dataset),
            dataset_version=dataset.dataset_version,
            seed=dataset.seed,
            calculated_at=dataset.generated_at,
        )
    app = create_app(
        settings=ApiSettings(environment=ApiEnvironment.TEST),
        session_factory=factory,
    )
    with TestClient(app) as client:
        yield InteractionApiFixture(client, dataset, factory)
    Base.metadata.drop_all(engine)
    engine.dispose()


def _payload(other_person_id: UUID, **changes: object) -> dict[str, object]:
    values: dict[str, object] = {
        "clientRequestId": str(uuid4()),
        "otherPersonId": str(other_person_id),
        "type": "COFFEE",
        "durationBucket": "MEDIUM",
        "occurredAt": (datetime.now(UTC) - timedelta(minutes=1)).isoformat(),
    }
    values.update(changes)
    return values


def test_capture_is_atomic_idempotent_and_refreshes_dormant_detail(
    interaction_api: InteractionApiFixture,
) -> None:
    p001 = _person(interaction_api.dataset, "P001")
    p002 = _person(interaction_api.dataset, "P002")
    p018 = _person(interaction_api.dataset, "P018")
    target_pair = PersonPair.between(p001.id, p018.id)
    unrelated_pair = PersonPair.between(p001.id, p002.id)
    with interaction_api.session_factory() as session:
        facts = SqlAlchemyFactRepository(session)
        profiles = SqlAlchemyRelationshipProfileRepository(session)
        event_count = len(facts.list_interaction_events())
        dormant = profiles.get(target_pair)
        unrelated = profiles.get(unrelated_pair)
    assert dormant is not None and dormant.state is RelationshipState.DORMANT
    assert unrelated is not None

    payload = _payload(p018.id)
    created = interaction_api.client.post("/api/v1/interactions", json=payload)

    assert created.status_code == 201
    created_body = created.json()
    assert created_body.keys() == {
        "interactionId",
        "otherPersonId",
        "occurredAt",
        "type",
        "durationBucket",
        "replayed",
    }
    assert created_body["otherPersonId"] == str(p018.id)
    assert datetime.fromisoformat(created_body["occurredAt"]) == datetime.fromisoformat(
        str(payload["occurredAt"])
    )
    assert created_body["type"] == "COFFEE"
    assert created_body["durationBucket"] == "MEDIUM"
    assert created_body["replayed"] is False
    serialized = created.text
    for forbidden in (
        "relationshipState",
        "relationshipStrength",
        "currentActivation",
        "confidence",
        "createdByPersonId",
    ):
        assert forbidden not in serialized

    with interaction_api.session_factory() as session:
        facts = SqlAlchemyFactRepository(session)
        profiles = SqlAlchemyRelationshipProfileRepository(session)
        events = facts.list_interaction_events_for_pair(target_pair)
        refreshed = profiles.get(target_pair)
        unchanged = profiles.get(unrelated_pair)
        total_event_count = len(facts.list_interaction_events())
    assert total_event_count == event_count + 1
    captured_event = events[-1]
    assert captured_event.participant_ids == tuple(
        sorted((p001.id, p018.id), key=lambda person_id: person_id.int)
    )
    assert captured_event.channel is InteractionChannel.ANALOG
    assert captured_event.source is InteractionSource.SELF_REPORTED
    assert captured_event.confidence.value == 1.0
    assert captured_event.conversation_participant_count == 2
    assert captured_event.duration_bucket is DurationBucket.MEDIUM
    assert captured_event.initiator_person_id is None
    assert captured_event.source_system == "network-compass-self-report"
    assert captured_event.created_by_person_id == p001.id
    assert refreshed is not None and refreshed.state is RelationshipState.RECONNECTED
    assert refreshed.model_version == "relationship-v0.1.0"
    assert unchanged == unrelated

    detail = interaction_api.client.get(f"/api/v1/people/{p018.id}")
    assert detail.status_code == 200
    assert detail.json()["relationship"]["state"] == "RECONNECTED"
    assert detail.json()["timeline"][0]["title"] == "コーヒーを飲みながら話しました"

    replay = interaction_api.client.post("/api/v1/interactions", json=payload)
    assert replay.status_code == 200
    assert replay.json() == {**created_body, "replayed": True}
    with interaction_api.session_factory() as session:
        facts = SqlAlchemyFactRepository(session)
        profiles = SqlAlchemyRelationshipProfileRepository(session)
        assert len(facts.list_interaction_events()) == event_count + 1
        after_replay = profiles.get(target_pair)
    assert after_replay == refreshed

    conflict = interaction_api.client.post(
        "/api/v1/interactions",
        json={**payload, "type": "LUNCH"},
    )
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "IDEMPOTENCY_CONFLICT"


def test_potential_capture_creates_only_the_current_person_pair(
    interaction_api: InteractionApiFixture,
) -> None:
    p001 = _person(interaction_api.dataset, "P001")
    p067 = _person(interaction_api.dataset, "P067")
    target_pair = PersonPair.between(p001.id, p067.id)
    with interaction_api.session_factory() as session:
        profiles = SqlAlchemyRelationshipProfileRepository(session)
        before = {profile.pair: profile for profile in profiles.list_all()}
    assert target_pair not in before

    response = interaction_api.client.post(
        "/api/v1/interactions",
        json=_payload(p067.id, type="OFFICE_CHAT", durationBucket="SHORT"),
    )

    assert response.status_code == 201
    with interaction_api.session_factory() as session:
        profiles = SqlAlchemyRelationshipProfileRepository(session)
        after = {profile.pair: profile for profile in profiles.list_all()}
    changed_pairs = {
        pair for pair in before.keys() | after.keys() if before.get(pair) != after.get(pair)
    }
    assert changed_pairs == {target_pair}
    assert after[target_pair].state is RelationshipState.NEW


def test_capture_rejects_invalid_boundaries_without_writes(
    interaction_api: InteractionApiFixture,
) -> None:
    p001 = _person(interaction_api.dataset, "P001")
    p018 = _person(interaction_api.dataset, "P018")
    with interaction_api.session_factory() as session:
        initial_count = len(SqlAlchemyFactRepository(session).list_interaction_events())

    invalid_requests = (
        (_payload(p001.id), 400, "INVALID_INTERACTION"),
        (
            _payload(p018.id, occurredAt=(datetime.now(UTC) + timedelta(days=1)).isoformat()),
            400,
            "INVALID_INTERACTION",
        ),
        (
            _payload(p018.id, occurredAt=(datetime.now(UTC) - timedelta(days=31)).isoformat()),
            400,
            "INVALID_INTERACTION",
        ),
        (_payload(UUID(int=0)), 404, "PERSON_NOT_FOUND"),
        (_payload(p018.id, type="TEAMS_CHAT"), 422, "INVALID_REQUEST"),
        ({**_payload(p018.id), "confidence": 0.2}, 422, "INVALID_REQUEST"),
    )
    for payload, expected_status, expected_code in invalid_requests:
        response = interaction_api.client.post("/api/v1/interactions", json=payload)
        assert response.status_code == expected_status
        assert response.json()["error"]["code"] == expected_code
        assert "requestId" in response.json()["error"]

    with interaction_api.session_factory() as session:
        assert len(SqlAlchemyFactRepository(session).list_interaction_events()) == initial_count


def test_production_capture_remains_closed_without_sso(
    interaction_api: InteractionApiFixture,
) -> None:
    p018 = _person(interaction_api.dataset, "P018")
    production_app = create_app(
        settings=ApiSettings(environment=ApiEnvironment.PRODUCTION),
        session_factory=interaction_api.session_factory,
    )
    with TestClient(production_app) as client:
        response = client.post(
            "/api/v1/interactions",
            headers={"X-Network-Compass-Persona": "P001"},
            json=_payload(p018.id),
        )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"
