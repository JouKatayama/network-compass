from __future__ import annotations

import base64
import binascii
import json
from collections import defaultdict
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from hashlib import sha256
from typing import Protocol
from uuid import UUID

from app.domain.entities import (
    Activity,
    Community,
    CommunityMembership,
    OrganizationUnit,
    Person,
    PersonActivity,
    PersonSkill,
    ProjectContext,
    ProjectParticipation,
    Skill,
)
from app.domain.enums import InteractionType, RelationshipState, Visibility
from app.domain.interactions import InteractionEvent
from app.domain.relationships import RelationshipProfile
from app.domain.value_objects import PersonPair, normalize_utc


class PersonNotFoundError(LookupError):
    pass


class InvalidSearchCursorError(ValueError):
    pass


class ConnectionType(StrEnum):
    SELF = "SELF"
    DIRECT = "DIRECT"
    TWO_HOP = "TWO_HOP"
    NONE = "NONE"


class TimelineItemType(StrEnum):
    INTERACTION = "INTERACTION"
    SHARED_PROJECT = "SHARED_PROJECT"


@dataclass(frozen=True, slots=True)
class NamedContext:
    id: UUID
    name: str


@dataclass(frozen=True, slots=True)
class PersonIdentity:
    person_id: UUID
    display_name: str
    role: str | None
    organization: NamedContext | None
    location: str | None
    avatar_url: str | None


@dataclass(frozen=True, slots=True)
class RelationshipSummary:
    connection_type: ConnectionType
    state: RelationshipState | None
    label: str
    last_contact_at: datetime | None
    known_since: datetime | None
    known_duration_days: int | None
    history_note: str | None


@dataclass(frozen=True, slots=True)
class TimelineItem:
    item_type: TimelineItemType
    title: str
    occurred_at: datetime
    ended_at: datetime | None = None
    context: NamedContext | None = None


@dataclass(frozen=True, slots=True)
class CommonContext:
    mutual_connections: tuple[PersonIdentity, ...] = ()
    activities: tuple[NamedContext, ...] = ()
    communities: tuple[NamedContext, ...] = ()
    skills: tuple[NamedContext, ...] = ()
    projects: tuple[NamedContext, ...] = ()


@dataclass(frozen=True, slots=True)
class PersonDetail:
    person: PersonIdentity
    relationship: RelationshipSummary
    timeline: tuple[TimelineItem, ...]
    common_context: CommonContext
    connection_paths: tuple[tuple[UUID, ...], ...]


@dataclass(frozen=True, slots=True)
class PersonSearchResult:
    person: PersonIdentity
    connection_type: ConnectionType
    relationship_state: RelationshipState | None
    relationship_label: str
    connection_path: tuple[UUID, ...]
    common_context: CommonContext


@dataclass(frozen=True, slots=True)
class PersonSearchPage:
    items: tuple[PersonSearchResult, ...]
    next_cursor: str | None


@dataclass(frozen=True, slots=True)
class PersonSearchCriteria:
    query: str
    limit: int = 20
    cursor: str | None = None
    organization_id: UUID | None = None
    community_id: UUID | None = None
    activity_id: UUID | None = None
    skill_id: UUID | None = None

    def __post_init__(self) -> None:
        query = self.query.strip()
        if not 1 <= len(query) <= 100:
            raise ValueError("query must contain between 1 and 100 characters")
        if isinstance(self.limit, bool) or not 1 <= self.limit <= 50:
            raise ValueError("limit must be between 1 and 50")
        object.__setattr__(self, "query", query)


class PeopleFactReader(Protocol):
    def list_people(self) -> tuple[Person, ...]: ...

    def list_organization_units(self) -> tuple[OrganizationUnit, ...]: ...

    def list_communities(self) -> tuple[Community, ...]: ...

    def list_community_memberships(self) -> tuple[CommunityMembership, ...]: ...

    def list_activities(self) -> tuple[Activity, ...]: ...

    def list_person_activities(self) -> tuple[PersonActivity, ...]: ...

    def list_skills(self) -> tuple[Skill, ...]: ...

    def list_person_skills(self) -> tuple[PersonSkill, ...]: ...

    def list_projects(self) -> tuple[ProjectContext, ...]: ...

    def list_project_participations(self) -> tuple[ProjectParticipation, ...]: ...

    def list_interaction_events(self) -> tuple[InteractionEvent, ...]: ...


class PeopleProfileReader(Protocol):
    def list_all(self) -> tuple[RelationshipProfile, ...]: ...


@dataclass(frozen=True, slots=True)
class _Snapshot:
    people: tuple[Person, ...]
    organizations: tuple[OrganizationUnit, ...]
    communities: tuple[Community, ...]
    memberships: tuple[CommunityMembership, ...]
    activities: tuple[Activity, ...]
    person_activities: tuple[PersonActivity, ...]
    skills: tuple[Skill, ...]
    person_skills: tuple[PersonSkill, ...]
    projects: tuple[ProjectContext, ...]
    participations: tuple[ProjectParticipation, ...]
    interactions: tuple[InteractionEvent, ...]
    profiles: tuple[RelationshipProfile, ...]
    as_of: datetime


_RELATIONSHIP_LABELS = {
    RelationshipState.NEW: "新しいつながり",
    RelationshipState.CLOSE: "親しいつながり",
    RelationshipState.ACTIVE: "最近も続いているつながり",
    RelationshipState.WEAK: "接点の少ないつながり",
    RelationshipState.DORMANT: "久しぶりのつながり",
    RelationshipState.RECONNECTED: "再びつながった関係",
}

_INTERACTION_LABELS = {
    InteractionType.TEAMS_CHAT: "Teamsでやり取りしました",
    InteractionType.EMAIL: "メールでやり取りしました",
    InteractionType.ONLINE_1ON1: "オンライン1on1で話しました",
    InteractionType.GROUP_MEETING: "ミーティングで一緒になりました",
    InteractionType.OFFICE_CHAT: "オフィスで話しました",
    InteractionType.COFFEE: "コーヒーを飲みながら話しました",
    InteractionType.LUNCH: "ランチで話しました",
    InteractionType.DINNER: "食事をしながら話しました",
    InteractionType.COMMUNITY: "コミュニティで一緒になりました",
    InteractionType.ACTIVITY: "アクティビティで一緒になりました",
    InteractionType.OTHER: "やり取りがありました",
}


class PeopleQueryService:
    def __init__(
        self,
        fact_reader: PeopleFactReader,
        profile_reader: PeopleProfileReader,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._fact_reader = fact_reader
        self._profile_reader = profile_reader
        self._clock = clock or (lambda: datetime.now(UTC))

    def get_detail(self, current_person_id: UUID, target_person_id: UUID) -> PersonDetail:
        snapshot = self._load_snapshot()
        people_by_id = {person.id: person for person in snapshot.people}
        self._require_person(current_person_id, people_by_id)
        target = self._require_person(target_person_id, people_by_id)
        profiles_by_pair = {profile.pair: profile for profile in snapshot.profiles}
        adjacency = self._adjacency(snapshot.profiles)
        connection_type, paths = self._connection(
            current_person_id,
            target_person_id,
            adjacency,
            profiles_by_pair,
        )
        profile = self._profile(current_person_id, target_person_id, profiles_by_pair)
        summary = self._relationship_summary(connection_type, profile, snapshot)
        common_context = self._common_context(
            snapshot,
            current_person_id,
            target_person_id,
            connection_type,
            adjacency,
        )
        timeline = self._timeline(
            snapshot,
            current_person_id,
            target_person_id,
            connection_type,
            common_context.projects,
        )
        return PersonDetail(
            person=self._identity(target, snapshot),
            relationship=summary,
            timeline=timeline,
            common_context=common_context,
            connection_paths=paths,
        )

    def search(
        self,
        current_person_id: UUID,
        criteria: PersonSearchCriteria,
    ) -> PersonSearchPage:
        snapshot = self._load_snapshot()
        people_by_id = {person.id: person for person in snapshot.people}
        self._require_person(current_person_id, people_by_id)
        profiles_by_pair = {profile.pair: profile for profile in snapshot.profiles}
        adjacency = self._adjacency(snapshot.profiles)
        cursor_after = self._decode_cursor(criteria)
        organizations_by_id = {item.id: item for item in snapshot.organizations}
        memberships_by_person = self._active_memberships(snapshot)
        skills_by_person = self._skills_by_person(snapshot)
        visible_activities_by_person = self._visible_activities_by_person(
            snapshot,
            current_person_id,
            adjacency,
        )
        query = criteria.query.casefold()

        matches: list[Person] = []
        for person in snapshot.people:
            if person.id == current_person_id:
                continue
            if criteria.organization_id is not None and (
                person.primary_organization_unit_id != criteria.organization_id
            ):
                continue
            if criteria.community_id is not None and (
                criteria.community_id not in memberships_by_person[person.id]
            ):
                continue
            if criteria.activity_id is not None and (
                criteria.activity_id not in visible_activities_by_person[person.id]
            ):
                continue
            if (
                criteria.skill_id is not None
                and criteria.skill_id not in skills_by_person[person.id]
            ):
                continue

            searchable = [person.display_name, person.role or "", person.location or ""]
            organization = (
                organizations_by_id.get(person.primary_organization_unit_id)
                if person.primary_organization_unit_id is not None
                else None
            )
            if organization is not None:
                searchable.append(organization.name)
            searchable.extend(
                skill.name for skill in snapshot.skills if skill.id in skills_by_person[person.id]
            )
            if any(query in value.casefold() for value in searchable):
                matches.append(person)

        matches.sort(key=lambda person: (person.display_name.casefold(), str(person.id)))
        if cursor_after is not None:
            matches = [
                person
                for person in matches
                if (person.display_name.casefold(), str(person.id)) > cursor_after
            ]
        selected = matches[: criteria.limit]
        items = tuple(
            self._search_result(
                snapshot,
                current_person_id,
                person,
                adjacency,
                profiles_by_pair,
            )
            for person in selected
        )
        next_cursor = None
        if len(matches) > criteria.limit and selected:
            last = selected[-1]
            next_cursor = self._encode_cursor(criteria, last.display_name.casefold(), last.id)
        return PersonSearchPage(items=items, next_cursor=next_cursor)

    def _load_snapshot(self) -> _Snapshot:
        profiles = self._profile_reader.list_all()
        as_of = (
            max(profile.calculated_at for profile in profiles)
            if profiles
            else normalize_utc(self._clock(), field_name="clock")
        )
        return _Snapshot(
            people=self._fact_reader.list_people(),
            organizations=self._fact_reader.list_organization_units(),
            communities=self._fact_reader.list_communities(),
            memberships=self._fact_reader.list_community_memberships(),
            activities=self._fact_reader.list_activities(),
            person_activities=self._fact_reader.list_person_activities(),
            skills=self._fact_reader.list_skills(),
            person_skills=self._fact_reader.list_person_skills(),
            projects=self._fact_reader.list_projects(),
            participations=self._fact_reader.list_project_participations(),
            interactions=self._fact_reader.list_interaction_events(),
            profiles=profiles,
            as_of=as_of,
        )

    @staticmethod
    def _require_person(person_id: UUID, people_by_id: dict[UUID, Person]) -> Person:
        try:
            return people_by_id[person_id]
        except KeyError as error:
            raise PersonNotFoundError("person not found") from error

    @staticmethod
    def _profile(
        first_id: UUID,
        second_id: UUID,
        profiles_by_pair: dict[PersonPair, RelationshipProfile],
    ) -> RelationshipProfile | None:
        if first_id == second_id:
            return None
        return profiles_by_pair.get(PersonPair.between(first_id, second_id))

    @staticmethod
    def _adjacency(profiles: Iterable[RelationshipProfile]) -> dict[UUID, set[UUID]]:
        adjacency: dict[UUID, set[UUID]] = defaultdict(set)
        for profile in profiles:
            first = profile.pair.person_a_id
            second = profile.pair.person_b_id
            adjacency[first].add(second)
            adjacency[second].add(first)
        return adjacency

    @staticmethod
    def _connection(
        current_person_id: UUID,
        target_person_id: UUID,
        adjacency: dict[UUID, set[UUID]],
        profiles_by_pair: dict[PersonPair, RelationshipProfile],
    ) -> tuple[ConnectionType, tuple[tuple[UUID, ...], ...]]:
        if current_person_id == target_person_id:
            return ConnectionType.SELF, ()
        if PersonPair.between(current_person_id, target_person_id) in profiles_by_pair:
            return ConnectionType.DIRECT, ()
        mutual_ids = sorted(
            adjacency[current_person_id] & adjacency[target_person_id],
            key=lambda person_id: person_id.int,
        )
        if mutual_ids:
            return (
                ConnectionType.TWO_HOP,
                tuple(
                    (current_person_id, mutual_id, target_person_id) for mutual_id in mutual_ids[:3]
                ),
            )
        return ConnectionType.NONE, ()

    @staticmethod
    def _relationship_summary(
        connection_type: ConnectionType,
        profile: RelationshipProfile | None,
        snapshot: _Snapshot,
    ) -> RelationshipSummary:
        if connection_type is ConnectionType.SELF:
            return RelationshipSummary(connection_type, None, "あなた", None, None, None, None)
        if profile is None:
            return RelationshipSummary(
                connection_type,
                None,
                "まだ直接話したことはありません",
                None,
                None,
                None,
                None,
            )
        event_count = sum(
            len(event.participant_ids) == 2
            and profile.pair.person_a_id in event.participant_ids
            and profile.pair.person_b_id in event.participant_ids
            for event in snapshot.interactions
        )
        history_note = (
            "記録されている履歴が限られています"
            if event_count <= 1 or profile.data_confidence < 0.45
            else None
        )
        return RelationshipSummary(
            connection_type=connection_type,
            state=profile.state,
            label=_RELATIONSHIP_LABELS[profile.state],
            last_contact_at=profile.last_meaningful_interaction_at,
            known_since=profile.first_meaningful_interaction_at,
            known_duration_days=(
                profile.calculated_at - profile.first_meaningful_interaction_at
            ).days,
            history_note=history_note,
        )

    @staticmethod
    def _identity(person: Person, snapshot: _Snapshot) -> PersonIdentity:
        organization_by_id = {item.id: item for item in snapshot.organizations}
        organization = (
            organization_by_id.get(person.primary_organization_unit_id)
            if person.primary_organization_unit_id is not None
            else None
        )
        return PersonIdentity(
            person_id=person.id,
            display_name=person.display_name,
            role=person.role,
            organization=(
                NamedContext(organization.id, organization.name)
                if organization is not None
                else None
            ),
            location=person.location,
            avatar_url=person.avatar_url,
        )

    def _common_context(
        self,
        snapshot: _Snapshot,
        current_person_id: UUID,
        target_person_id: UUID,
        connection_type: ConnectionType,
        adjacency: dict[UUID, set[UUID]],
    ) -> CommonContext:
        people_by_id = {person.id: person for person in snapshot.people}
        mutual_ids = sorted(
            adjacency[current_person_id] & adjacency[target_person_id],
            key=lambda person_id: (
                people_by_id[person_id].display_name.casefold(),
                str(person_id),
            ),
        )
        memberships_by_person = self._active_memberships(snapshot)
        skills_by_person = self._skills_by_person(snapshot)
        projects_by_person = self._projects_by_person(snapshot)
        visible_activities_by_person = self._visible_activities_by_person(
            snapshot,
            current_person_id,
            adjacency,
        )
        return CommonContext(
            mutual_connections=tuple(
                self._identity(people_by_id[person_id], snapshot) for person_id in mutual_ids[:8]
            ),
            activities=self._named_intersection(
                snapshot.activities,
                visible_activities_by_person[current_person_id],
                visible_activities_by_person[target_person_id],
            ),
            communities=self._named_intersection(
                snapshot.communities,
                memberships_by_person[current_person_id],
                memberships_by_person[target_person_id],
            ),
            skills=self._named_intersection(
                snapshot.skills,
                skills_by_person[current_person_id],
                skills_by_person[target_person_id],
            ),
            projects=self._named_intersection(
                snapshot.projects,
                projects_by_person[current_person_id],
                projects_by_person[target_person_id],
            ),
        )

    @staticmethod
    def _named_intersection(
        entities: Iterable[Activity | Community | Skill | ProjectContext],
        first_ids: set[UUID],
        second_ids: set[UUID],
        *,
        limit: int = 8,
    ) -> tuple[NamedContext, ...]:
        shared_ids = first_ids & second_ids
        items = sorted(
            (
                NamedContext(entity.id, entity.name)
                for entity in entities
                if entity.id in shared_ids
            ),
            key=lambda item: (item.name.casefold(), str(item.id)),
        )
        return tuple(items[:limit])

    @staticmethod
    def _active_memberships(snapshot: _Snapshot) -> dict[UUID, set[UUID]]:
        result: dict[UUID, set[UUID]] = defaultdict(set)
        for membership in snapshot.memberships:
            if membership.joined_at <= snapshot.as_of and (
                membership.left_at is None or membership.left_at >= snapshot.as_of
            ):
                result[membership.person_id].add(membership.community_id)
        return result

    @staticmethod
    def _skills_by_person(snapshot: _Snapshot) -> dict[UUID, set[UUID]]:
        result: dict[UUID, set[UUID]] = defaultdict(set)
        for person_skill in snapshot.person_skills:
            if person_skill.declared_at <= snapshot.as_of:
                result[person_skill.person_id].add(person_skill.skill_id)
        return result

    @staticmethod
    def _projects_by_person(snapshot: _Snapshot) -> dict[UUID, set[UUID]]:
        result: dict[UUID, set[UUID]] = defaultdict(set)
        for participation in snapshot.participations:
            if participation.started_at <= snapshot.as_of:
                result[participation.person_id].add(participation.project_id)
        return result

    @staticmethod
    def _visible_activities_by_person(
        snapshot: _Snapshot,
        current_person_id: UUID,
        adjacency: dict[UUID, set[UUID]],
    ) -> dict[UUID, set[UUID]]:
        people_by_id = {person.id: person for person in snapshot.people}
        current = people_by_id[current_person_id]
        result: dict[UUID, set[UUID]] = defaultdict(set)
        for declaration in snapshot.person_activities:
            if declaration.declared_at > snapshot.as_of:
                continue
            if declaration.person_id == current_person_id:
                result[declaration.person_id].add(declaration.activity_id)
                continue
            target = people_by_id.get(declaration.person_id)
            if target is None or declaration.visibility is Visibility.PRIVATE:
                continue
            if (
                declaration.visibility is Visibility.NETWORK
                and declaration.person_id in adjacency[current_person_id]
            ) or (
                declaration.visibility is Visibility.ORGANIZATION
                and current.primary_organization_unit_id is not None
                and current.primary_organization_unit_id == target.primary_organization_unit_id
            ):
                result[declaration.person_id].add(declaration.activity_id)
        return result

    @staticmethod
    def _timeline(
        snapshot: _Snapshot,
        current_person_id: UUID,
        target_person_id: UUID,
        connection_type: ConnectionType,
        shared_projects: tuple[NamedContext, ...],
    ) -> tuple[TimelineItem, ...]:
        if connection_type is not ConnectionType.DIRECT:
            return ()
        project_by_id = {project.id: project for project in snapshot.projects}
        shared_project_ids = {project.id for project in shared_projects}
        timeline: list[TimelineItem] = []
        for event in snapshot.interactions:
            if (
                current_person_id in event.participant_ids
                and target_person_id in event.participant_ids
            ):
                context = (
                    NamedContext(event.project_id, project_by_id[event.project_id].name)
                    if event.project_id in project_by_id and event.project_id in shared_project_ids
                    else None
                )
                timeline.append(
                    TimelineItem(
                        item_type=TimelineItemType.INTERACTION,
                        title=_INTERACTION_LABELS[event.type],
                        occurred_at=event.occurred_at,
                        context=context,
                    )
                )
        for shared_project in shared_projects:
            project = project_by_id[shared_project.id]
            timeline.append(
                TimelineItem(
                    item_type=TimelineItemType.SHARED_PROJECT,
                    title=f"{project.name}で一緒に活動",
                    occurred_at=project.started_at,
                    ended_at=project.ended_at,
                    context=shared_project,
                )
            )
        timeline.sort(key=lambda item: (item.occurred_at, item.title), reverse=True)
        return tuple(timeline[:12])

    def _search_result(
        self,
        snapshot: _Snapshot,
        current_person_id: UUID,
        target: Person,
        adjacency: dict[UUID, set[UUID]],
        profiles_by_pair: dict[PersonPair, RelationshipProfile],
    ) -> PersonSearchResult:
        connection_type, paths = self._connection(
            current_person_id,
            target.id,
            adjacency,
            profiles_by_pair,
        )
        profile = self._profile(current_person_id, target.id, profiles_by_pair)
        summary = self._relationship_summary(connection_type, profile, snapshot)
        common = self._common_context(
            snapshot,
            current_person_id,
            target.id,
            connection_type,
            adjacency,
        )
        bounded_common = CommonContext(
            mutual_connections=common.mutual_connections[:3],
            activities=common.activities[:3],
            communities=common.communities[:3],
            skills=common.skills[:3],
            projects=common.projects[:3],
        )
        return PersonSearchResult(
            person=self._identity(target, snapshot),
            connection_type=connection_type,
            relationship_state=profile.state if profile is not None else None,
            relationship_label=summary.label,
            connection_path=paths[0] if paths else (),
            common_context=bounded_common,
        )

    @classmethod
    def _criteria_digest(cls, criteria: PersonSearchCriteria) -> str:
        payload = {
            "activityId": str(criteria.activity_id) if criteria.activity_id else None,
            "communityId": str(criteria.community_id) if criteria.community_id else None,
            "organizationId": str(criteria.organization_id) if criteria.organization_id else None,
            "query": criteria.query.casefold(),
            "skillId": str(criteria.skill_id) if criteria.skill_id else None,
        }
        encoded = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
        return sha256(encoded).hexdigest()

    @classmethod
    def _encode_cursor(cls, criteria: PersonSearchCriteria, name: str, person_id: UUID) -> str:
        payload = {
            "afterId": str(person_id),
            "afterName": name,
            "criteria": cls._criteria_digest(criteria),
            "version": 1,
        }
        encoded = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
        return base64.urlsafe_b64encode(encoded).decode().rstrip("=")

    @classmethod
    def _decode_cursor(cls, criteria: PersonSearchCriteria) -> tuple[str, str] | None:
        if criteria.cursor is None:
            return None
        try:
            padding = "=" * (-len(criteria.cursor) % 4)
            payload = json.loads(base64.urlsafe_b64decode(criteria.cursor + padding))
            if not isinstance(payload, dict):
                raise TypeError
            if payload.get("version") != 1:
                raise ValueError
            if payload.get("criteria") != cls._criteria_digest(criteria):
                raise ValueError
            after_name = payload["afterName"]
            after_id = payload["afterId"]
            if not isinstance(after_name, str) or not isinstance(after_id, str):
                raise TypeError
            UUID(after_id)
            return after_name, after_id
        except (
            KeyError,
            TypeError,
            ValueError,
            json.JSONDecodeError,
            binascii.Error,
        ) as error:
            raise InvalidSearchCursorError("search cursor is invalid") from error
