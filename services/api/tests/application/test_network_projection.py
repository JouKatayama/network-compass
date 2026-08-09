from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

import pytest

from app.application.network_projection import PersonalNetworkProjectionQueryService
from app.domain.entities import OrganizationUnit, Person
from app.domain.enums import HireType
from app.domain.projections import GraphProjection
from app.domain.relationships import RelationshipProfile


@dataclass
class FactReader:
    people: tuple[Person, ...]
    organizations: tuple[OrganizationUnit, ...]

    def list_people(self) -> tuple[Person, ...]:
        return self.people

    def list_organization_units(self) -> tuple[OrganizationUnit, ...]:
        return self.organizations


@dataclass
class ProfileReader:
    profiles: tuple[RelationshipProfile, ...] = ()

    def list_all(self) -> tuple[RelationshipProfile, ...]:
        return self.profiles


def _empty_projection_service() -> tuple[PersonalNetworkProjectionQueryService, Person]:
    now = datetime(2026, 8, 9, 12, tzinfo=UTC)
    person = Person(
        id=UUID(int=1),
        display_name="Current person",
        joined_at=now,
        hire_type=HireType.OTHER,
    )
    service = PersonalNetworkProjectionQueryService(
        FactReader((person,), ()),
        ProfileReader(),
        clock=lambda: now,
    )
    return service, person


def test_query_service_builds_only_current_users_personal_projection() -> None:
    service, person = _empty_projection_service()
    projection = service.get_for_current_user(person.id)
    assert projection.focal_person_id == person.id
    assert projection.nodes[0].person_id == person.id
    assert projection.meta.visible_node_count == 1

    with pytest.raises(ValueError, match="focal person does not exist"):
        service.get_for_current_user(UUID(int=2))


def test_query_service_rejects_expanding_someone_elses_projection() -> None:
    service, person = _empty_projection_service()
    projection: GraphProjection = service.get_for_current_user(person.id)
    with pytest.raises(PermissionError, match="focal user"):
        service.expand_for_current_user(
            UUID(int=2),
            projection,
            selected_person_id=person.id,
        )
