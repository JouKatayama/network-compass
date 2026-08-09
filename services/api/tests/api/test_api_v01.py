from collections.abc import Iterator
from dataclasses import dataclass
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from network_compass_synthetic.generator import generate_dataset
from network_compass_synthetic.models import SyntheticDataset
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.dependencies import get_session
from app.application.persistence import DemoResetService
from app.domain.entities import Person
from app.domain.enums import Visibility
from app.domain.facts import CanonicalFactSet
from app.domain.value_objects import ExternalIdentifier
from app.infrastructure.database import Base, create_session_factory
from app.infrastructure.persistence import (
    SqlAlchemyFactRepository,
    SqlAlchemyRelationshipProfileRepository,
)
from app.main import create_app
from app.settings import ApiEnvironment, ApiSettings


@dataclass(frozen=True, slots=True)
class ApiFixture:
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


@pytest.fixture(scope="module")
def api_fixture() -> Iterator[ApiFixture]:
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
        yield ApiFixture(client, dataset, factory)
    Base.metadata.drop_all(engine)
    engine.dispose()


def _assert_error_envelope(response_status: int, body: dict[str, object]) -> None:
    assert response_status >= 400
    assert set(body) == {"error"}
    error = body["error"]
    assert isinstance(error, dict)
    assert set(error) == {"code", "message", "requestId"}
    assert isinstance(error["message"], str)
    assert isinstance(error["requestId"], str)
    assert error["requestId"].startswith("req_")


def test_network_uses_current_person_and_preserves_gate_b_bounds_and_privacy(
    api_fixture: ApiFixture,
) -> None:
    response = api_fixture.client.get("/api/v1/me/network")

    assert response.status_code == 200
    body = response.json()
    p001 = _person(api_fixture.dataset, "P001")
    p010 = _person(api_fixture.dataset, "P010")
    p018 = _person(api_fixture.dataset, "P018")
    p067 = _person(api_fixture.dataset, "P067")
    nodes = {node["personId"]: node for node in body["nodes"]}
    code_by_person_id = {
        str(person.id): person.external_identifiers[0].external_id
        for person in api_fixture.dataset.people
    }
    assert body["focalPersonId"] == str(p001.id)
    assert body["meta"]["oneHopCount"] <= 24
    assert body["meta"]["twoHopCount"] <= 12
    assert body["meta"]["visibleNodeCount"] == len(nodes)
    assert len(nodes) == len(body["nodes"])
    assert {code_by_person_id[person_id] for person_id in nodes} == {
        "P001",
        "P002",
        "P003",
        "P004",
        "P005",
        "P006",
        "P007",
        "P008",
        "P009",
        "P010",
        "P012",
        "P013",
        "P014",
        "P016",
        "P017",
        "P018",
        "P019",
        "P020",
        "P021",
        "P022",
        "P023",
        "P024",
        "P025",
        "P026",
        "P041",
        "P042",
        "P043",
        "P044",
        "P047",
        "P067",
        "P080",
        "P083",
        "P084",
        "P085",
        "P086",
        "P087",
        "P102",
    }
    assert nodes[str(p001.id)]["hop"] == 0
    assert nodes[str(p018.id)]["relationshipState"] == "DORMANT"
    assert nodes[str(p067.id)]["hop"] == 2
    assert nodes[str(p067.id)]["shortestPaths"] == [[str(p001.id), str(p010.id), str(p067.id)]]
    potential_edges = [edge for edge in body["edges"] if edge["edgeType"] == "POTENTIAL_PATH"]
    assert potential_edges
    for edge in potential_edges:
        assert "relationshipState" not in edge
        assert "relationshipStrength" not in edge
        assert "currentActivation" not in edge

    switched = api_fixture.client.get(
        "/api/v1/me/network",
        headers={"X-Network-Compass-Persona": "P201"},
    )
    assert switched.status_code == 200
    assert switched.json()["focalPersonId"] == str(_person(api_fixture.dataset, "P201").id)


def test_person_detail_has_factual_dormant_project_history_and_potential_path(
    api_fixture: ApiFixture,
) -> None:
    p001 = _person(api_fixture.dataset, "P001")
    p010 = _person(api_fixture.dataset, "P010")
    p018 = _person(api_fixture.dataset, "P018")
    p067 = _person(api_fixture.dataset, "P067")

    dormant_response = api_fixture.client.get(f"/api/v1/people/{p018.id}")
    assert dormant_response.status_code == 200
    dormant = dormant_response.json()
    assert dormant["relationship"]["connectionType"] == "DIRECT"
    assert dormant["relationship"]["state"] == "DORMANT"
    assert dormant["relationship"]["label"] == "久しぶりのつながり"
    assert dormant["relationship"]["knownDurationDays"] > 0
    assert dormant["commonContext"]["projects"]
    project_items = [item for item in dormant["timeline"] if item["itemType"] == "SHARED_PROJECT"]
    assert project_items
    assert project_items[0]["context"] in dormant["commonContext"]["projects"]
    serialized = dormant_response.text
    for forbidden in (
        "relationshipStrength",
        "currentActivation",
        "dataConfidence",
        "careerLevel",
        "externalIdentifiers",
    ):
        assert forbidden not in serialized

    potential_response = api_fixture.client.get(f"/api/v1/people/{p067.id}")
    assert potential_response.status_code == 200
    potential = potential_response.json()
    assert potential["relationship"]["connectionType"] == "TWO_HOP"
    assert potential["relationship"]["state"] is None
    assert potential["relationship"]["label"] == "まだ直接話したことはありません"
    assert potential["timeline"] == []
    assert potential["connectionPaths"] == [[str(p001.id), str(p010.id), str(p067.id)]]


def test_network_expansion_is_bounded_replayable_and_current_person_relative(
    api_fixture: ApiFixture,
) -> None:
    initial = api_fixture.client.get("/api/v1/me/network").json()
    visible_ids = {node["personId"] for node in initial["nodes"]}
    selected_id = next(
        node["personId"]
        for node in initial["nodes"]
        if node["hop"] == 1 and node["personId"] != initial["focalPersonId"]
    )

    response = api_fixture.client.post(
        "/api/v1/me/network/expand",
        json={"selectedPersonId": selected_id, "expandedFromPersonIds": []},
    )
    assert response.status_code == 200
    expanded = response.json()
    assert expanded["focalPersonId"] == initial["focalPersonId"]
    assert expanded["meta"]["expandedFromPersonIds"] == [selected_id]
    assert len(expanded["nodes"]) - len(initial["nodes"]) <= 8
    assert visible_ids <= {node["personId"] for node in expanded["nodes"]}
    assert expanded["meta"]["visibleNodeCount"] <= 80

    next_selected_id = next(
        node["personId"]
        for node in expanded["nodes"]
        if node["personId"] not in {selected_id, expanded["focalPersonId"]}
    )
    replayed = api_fixture.client.post(
        "/api/v1/me/network/expand",
        json={
            "selectedPersonId": next_selected_id,
            "expandedFromPersonIds": [selected_id],
        },
    )
    assert replayed.status_code == 200
    assert replayed.json()["meta"]["expandedFromPersonIds"] == [
        selected_id,
        next_selected_id,
    ]

    invalid = api_fixture.client.post(
        "/api/v1/me/network/expand",
        json={"selectedPersonId": str(UUID(int=0)), "expandedFromPersonIds": []},
    )
    assert invalid.status_code == 400
    _assert_error_envelope(invalid.status_code, invalid.json())
    assert invalid.json()["error"]["code"] == "INVALID_NETWORK_EXPANSION"

    p201 = _person(api_fixture.dataset, "P201")
    switched = api_fixture.client.post(
        "/api/v1/me/network/expand",
        headers={"X-Network-Compass-Persona": "P201"},
        json={"selectedPersonId": str(p201.id), "expandedFromPersonIds": []},
    )
    assert switched.status_code == 200
    assert switched.json()["focalPersonId"] == str(p201.id)


def test_search_supports_cursor_filters_paths_and_private_activity_visibility(
    api_fixture: ApiFixture,
) -> None:
    first = api_fixture.client.get(
        "/api/v1/people/search",
        params={"q": "Synthetic Person", "limit": 2},
    )
    assert first.status_code == 200
    first_body = first.json()
    assert len(first_body["items"]) == 2
    assert first_body["nextCursor"]

    second = api_fixture.client.get(
        "/api/v1/people/search",
        params={
            "q": "Synthetic Person",
            "limit": 2,
            "cursor": first_body["nextCursor"],
        },
    )
    assert second.status_code == 200
    first_ids = {item["person"]["personId"] for item in first_body["items"]}
    second_ids = {item["person"]["personId"] for item in second.json()["items"]}
    assert first_ids.isdisjoint(second_ids)
    criteria_mismatch = api_fixture.client.get(
        "/api/v1/people/search",
        params={"q": "different", "cursor": first_body["nextCursor"]},
    )
    assert criteria_mismatch.status_code == 400
    assert criteria_mismatch.json()["error"]["code"] == "INVALID_CURSOR"

    p001 = _person(api_fixture.dataset, "P001")
    p010 = _person(api_fixture.dataset, "P010")
    p018 = _person(api_fixture.dataset, "P018")
    p067 = _person(api_fixture.dataset, "P067")
    potential = api_fixture.client.get(
        "/api/v1/people/search",
        params={"q": "P067"},
    ).json()["items"]
    assert len(potential) == 1
    assert potential[0]["connectionType"] == "TWO_HOP"
    assert potential[0]["connectionPath"] == [str(p001.id), str(p010.id), str(p067.id)]

    p018_skill_id = next(
        item.skill_id for item in api_fixture.dataset.person_skills if item.person_id == p018.id
    )
    filtered = api_fixture.client.get(
        "/api/v1/people/search",
        params={"q": "P018", "skillId": str(p018_skill_id)},
    )
    assert [item["person"]["personId"] for item in filtered.json()["items"]] == [str(p018.id)]

    private_declaration = next(
        item
        for item in api_fixture.dataset.person_activities
        if item.person_id != p001.id and item.visibility is Visibility.PRIVATE
    )
    private_person = next(
        person
        for person in api_fixture.dataset.people
        if person.id == private_declaration.person_id
    )
    private_filtered = api_fixture.client.get(
        "/api/v1/people/search",
        params={
            "q": private_person.display_name,
            "activityId": str(private_declaration.activity_id),
        },
    )
    assert private_filtered.status_code == 200
    assert private_filtered.json()["items"] == []


def test_api_errors_are_safe_and_request_identified(api_fixture: ApiFixture) -> None:
    invalid_cursor = api_fixture.client.get(
        "/api/v1/people/search",
        params={"q": "Synthetic", "cursor": "not-a-cursor"},
    )
    assert invalid_cursor.status_code == 400
    _assert_error_envelope(invalid_cursor.status_code, invalid_cursor.json())
    assert invalid_cursor.json()["error"]["code"] == "INVALID_CURSOR"
    assert invalid_cursor.headers["X-Request-ID"] == invalid_cursor.json()["error"]["requestId"]

    missing = api_fixture.client.get(f"/api/v1/people/{UUID(int=0)}")
    assert missing.status_code == 404
    _assert_error_envelope(missing.status_code, missing.json())
    assert missing.json()["error"]["code"] == "PERSON_NOT_FOUND"

    malformed = api_fixture.client.get("/api/v1/people/not-a-uuid")
    assert malformed.status_code == 422
    _assert_error_envelope(malformed.status_code, malformed.json())

    unknown = api_fixture.client.get("/api/v1/not-a-route")
    assert unknown.status_code == 404
    _assert_error_envelope(unknown.status_code, unknown.json())

    invalid_persona = api_fixture.client.get(
        "/api/v1/me/network",
        headers={"X-Network-Compass-Persona": "not-persisted"},
    )
    assert invalid_persona.status_code == 401
    _assert_error_envelope(invalid_persona.status_code, invalid_persona.json())
    assert invalid_persona.json()["error"]["code"] == "INVALID_DEVELOPMENT_PERSONA"


def test_production_disables_development_persona_and_cors_is_restricted(
    api_fixture: ApiFixture,
) -> None:
    production_app = create_app(
        settings=ApiSettings(environment=ApiEnvironment.PRODUCTION),
        session_factory=api_fixture.session_factory,
    )
    with TestClient(production_app) as production_client:
        response = production_client.get(
            "/api/v1/me/network",
            headers={"X-Network-Compass-Persona": "P001"},
        )
    assert response.status_code == 401
    _assert_error_envelope(response.status_code, response.json())
    assert response.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"

    allowed = api_fixture.client.options(
        "/api/v1/me/network",
        headers={
            "Access-Control-Request-Method": "GET",
            "Origin": "http://localhost:3000",
        },
    )
    assert allowed.status_code == 200
    assert allowed.headers["access-control-allow-origin"] == "http://localhost:3000"
    blocked = api_fixture.client.options(
        "/api/v1/me/network",
        headers={
            "Access-Control-Request-Method": "GET",
            "Origin": "https://untrusted.example",
        },
    )
    assert blocked.status_code == 400
    assert "access-control-allow-origin" not in blocked.headers


def test_unexpected_errors_are_logged_but_return_only_safe_envelope(
    api_fixture: ApiFixture,
) -> None:
    failure_app = create_app(
        settings=ApiSettings(environment=ApiEnvironment.TEST),
        session_factory=api_fixture.session_factory,
    )

    def fail_session() -> Iterator[Session]:
        raise RuntimeError("internal database detail must not reach the client")
        yield

    failure_app.dependency_overrides[get_session] = fail_session
    with TestClient(failure_app, raise_server_exceptions=False) as client:
        response = client.get("/api/v1/me/network")

    assert response.status_code == 500
    _assert_error_envelope(response.status_code, response.json())
    assert response.json()["error"]["code"] == "INTERNAL_ERROR"
    assert "database" not in response.text
