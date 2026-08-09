from collections.abc import Callable
from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID

from app.domain.entities import OrganizationUnit, Person
from app.domain.network_projection import NetworkProjectionService
from app.domain.projections import GraphProjection
from app.domain.relationships import RelationshipProfile
from app.domain.value_objects import normalize_utc


class ProjectionFactReader(Protocol):
    def list_people(self) -> tuple[Person, ...]: ...

    def list_organization_units(self) -> tuple[OrganizationUnit, ...]: ...


class ProjectionProfileReader(Protocol):
    def list_all(self) -> tuple[RelationshipProfile, ...]: ...


class PersonalNetworkProjectionQueryService:
    """Build only the authenticated person's own personal graph projection.

    Authentication and development-persona resolution belong to the later API boundary. This use
    case deliberately accepts `current_person_id`, not an arbitrary target-person query parameter.
    """

    def __init__(
        self,
        fact_reader: ProjectionFactReader,
        profile_reader: ProjectionProfileReader,
        *,
        projection_service: NetworkProjectionService | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._fact_reader = fact_reader
        self._profile_reader = profile_reader
        self._projection_service = projection_service or NetworkProjectionService()
        self._clock = clock or (lambda: datetime.now(UTC))

    def get_for_current_user(
        self,
        current_person_id: UUID,
        *,
        generated_at: datetime | None = None,
    ) -> GraphProjection:
        people = self._fact_reader.list_people()
        organizations = self._fact_reader.list_organization_units()
        profiles = self._profile_reader.list_all()
        calculation_time = self._calculation_time(profiles, generated_at)
        return self._projection_service.build(
            focal_person_id=current_person_id,
            people=people,
            organization_units=organizations,
            relationship_profiles=profiles,
            generated_at=calculation_time,
        )

    def expand_for_current_user(
        self,
        current_person_id: UUID,
        projection: GraphProjection,
        *,
        selected_person_id: UUID,
    ) -> GraphProjection:
        if projection.focal_person_id != current_person_id:
            raise PermissionError("a personal graph can only be expanded by its focal user")
        return self._projection_service.expand(
            projection,
            selected_person_id=selected_person_id,
            people=self._fact_reader.list_people(),
            organization_units=self._fact_reader.list_organization_units(),
            relationship_profiles=self._profile_reader.list_all(),
        )

    def _calculation_time(
        self,
        profiles: tuple[RelationshipProfile, ...],
        generated_at: datetime | None,
    ) -> datetime:
        if generated_at is not None:
            return normalize_utc(generated_at, field_name="generated_at")
        if profiles:
            return max(profile.calculated_at for profile in profiles)
        return normalize_utc(self._clock(), field_name="clock")
