from collections.abc import Iterator
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from network_compass_synthetic.generator import DEFAULT_SEED, generate_dataset
from network_compass_synthetic.models import SyntheticDataset
from sqlalchemy import Engine, create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.application.persistence import (
    DemoResetResult,
    DemoResetService,
    RelationshipRebuildService,
)
from app.domain.entities import (
    Activity,
    Community,
    CommunityMembership,
    OrganizationUnit,
    Person,
    PersonActivity,
    ProjectContext,
    ProjectParticipation,
    UserRelationshipFeedback,
)
from app.domain.enums import HireType, RelationshipState, Visibility
from app.domain.facts import CanonicalFactSet
from app.domain.value_objects import ExternalIdentifier, PersonPair
from app.infrastructure.database import Base
from app.infrastructure.persistence import (
    SqlAlchemyFactRepository,
    SqlAlchemyRelationshipProfileRepository,
)


@pytest.fixture
def database_engine() -> Iterator[Engine]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


def _canonical_facts(dataset: SyntheticDataset) -> CanonicalFactSet:
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


def _reset(engine: Engine, dataset: SyntheticDataset) -> DemoResetResult:
    with Session(engine) as session, session.begin():
        facts = SqlAlchemyFactRepository(session)
        profiles = SqlAlchemyRelationshipProfileRepository(session)
        return DemoResetService(facts, profiles).reset(
            _canonical_facts(dataset),
            dataset_version=dataset.dataset_version,
            seed=dataset.seed,
            calculated_at=dataset.generated_at,
        )


def _person_by_code(people: tuple[Person, ...], code: str) -> Person:
    return next(
        person
        for person in people
        if ExternalIdentifier("synthetic", code) in person.external_identifiers
    )


def test_fact_repository_round_trips_people_and_relational_interactions(
    database_engine: Engine,
) -> None:
    dataset = generate_dataset("edge_cases")

    with Session(database_engine) as session, session.begin():
        repository = SqlAlchemyFactRepository(session)
        repository.replace_all(_canonical_facts(dataset))
        people = repository.list_people()
        events = repository.list_interaction_events()
        counts = repository.counts()

    assert {person.id: person for person in people} == {
        person.id: person for person in dataset.people
    }
    assert {event.id: event for event in events} == {
        event.id: event for event in dataset.interaction_events
    }
    assert counts["people"] == len(dataset.people)
    assert counts["interaction_events"] == len(dataset.interaction_events)
    assert counts["interaction_participants"] == sum(
        len(event.participant_ids) for event in dataset.interaction_events
    )


def test_relationship_context_excludes_private_activity_and_keeps_visible_context(
    database_engine: Engine,
) -> None:
    now = datetime(2026, 8, 9, 12, tzinfo=UTC)
    first_id = UUID(int=1)
    second_id = UUID(int=2)
    organization_id = UUID(int=10)
    community_id = UUID(int=11)
    private_activity_id = UUID(int=12)
    visible_activity_id = UUID(int=13)
    project_id = UUID(int=14)
    pair = PersonPair(first_id, second_id)
    people = tuple(
        Person(
            id=person_id,
            display_name=f"Person {index}",
            joined_at=now - timedelta(days=365),
            hire_type=HireType.OTHER,
            primary_organization_unit_id=organization_id,
        )
        for index, person_id in enumerate((first_id, second_id), start=1)
    )
    facts = CanonicalFactSet(
        people=people,
        organization_units=(OrganizationUnit(organization_id, "Shared Org"),),
        communities=(Community(community_id, "Shared Community"),),
        community_memberships=tuple(
            CommunityMembership(person.id, community_id, now - timedelta(days=100))
            for person in people
        ),
        activities=(
            Activity(private_activity_id, "Private Activity"),
            Activity(visible_activity_id, "Visible Activity"),
        ),
        person_activities=tuple(
            PersonActivity(person.id, activity_id, now - timedelta(days=90), visibility)
            for person in people
            for activity_id, visibility in (
                (private_activity_id, Visibility.PRIVATE),
                (visible_activity_id, Visibility.NETWORK),
            )
        ),
        skills=(),
        person_skills=(),
        projects=(ProjectContext(project_id, "Shared Project", now - timedelta(days=200)),),
        project_participations=tuple(
            ProjectParticipation(person.id, project_id, now - timedelta(days=180))
            for person in people
        ),
        interaction_events=(),
        user_relationship_feedback=(UserRelationshipFeedback(UUID(int=15), pair, first_id, now),),
    )

    with Session(database_engine) as session, session.begin():
        repository = SqlAlchemyFactRepository(session)
        repository.replace_all(facts)
        context = repository.relationship_contexts((pair,), calculated_at=now)[pair]
        counts = repository.counts()

    assert context.shared_community_count == 1
    assert context.shared_activity_count == 1
    assert context.shared_project_count == 1
    assert context.same_primary_organization
    assert counts["user_relationship_feedback"] == 1


def test_demo_reset_and_relationship_rebuild_are_repeatable_without_rewriting_facts(
    database_engine: Engine,
) -> None:
    dataset = generate_dataset("demo", seed=DEFAULT_SEED)
    first_result = _reset(database_engine, dataset)

    with Session(database_engine) as session:
        fact_repository = SqlAlchemyFactRepository(session)
        profile_repository = SqlAlchemyRelationshipProfileRepository(session)
        first_events = fact_repository.list_interaction_events()
        first_profiles = profile_repository.list_all()
        people = fact_repository.list_people()

    p001 = _person_by_code(people, "P001")
    p018 = _person_by_code(people, "P018")
    p102 = _person_by_code(people, "P102")
    profile_by_pair = {profile.pair: profile for profile in first_profiles}

    assert first_result.relationship_profile_count == 535
    assert profile_by_pair[PersonPair.between(p001.id, p018.id)].state is RelationshipState.DORMANT
    assert (
        profile_by_pair[PersonPair.between(p001.id, p102.id)].state is RelationshipState.RECONNECTED
    )
    assert {profile.model_version for profile in first_profiles} == {"relationship-v0.1.0"}

    with Session(database_engine) as session, session.begin():
        fact_repository = SqlAlchemyFactRepository(session)
        profile_repository = SqlAlchemyRelationshipProfileRepository(session)
        profile_repository.clear_all()
        rebuilt = RelationshipRebuildService(fact_repository, profile_repository).rebuild(
            calculated_at=dataset.generated_at
        )
        assert fact_repository.list_interaction_events() == first_events

    assert rebuilt == first_profiles

    second_result = _reset(database_engine, dataset)
    with Session(database_engine) as session:
        second_profiles = SqlAlchemyRelationshipProfileRepository(session).list_all()
        second_events = SqlAlchemyFactRepository(session).list_interaction_events()

    assert second_result == first_result
    assert second_profiles == first_profiles
    assert second_events == first_events


def test_failed_demo_reset_rolls_back_source_and_derived_replacement(
    database_engine: Engine,
) -> None:
    dataset = generate_dataset("edge_cases", seed=DEFAULT_SEED)
    successful_result = _reset(database_engine, dataset)
    original_event = dataset.interaction_events[0]
    assert original_event.source_system is not None
    assert original_event.external_event_id is not None
    duplicate_source_event = replace(
        original_event,
        id=UUID("ffffffff-ffff-ffff-ffff-ffffffffffff"),
    )
    invalid_facts = replace(
        _canonical_facts(dataset),
        interaction_events=(*dataset.interaction_events, duplicate_source_event),
    )

    with (
        pytest.raises(IntegrityError),
        Session(database_engine) as session,
        session.begin(),
    ):
        facts = SqlAlchemyFactRepository(session)
        profiles = SqlAlchemyRelationshipProfileRepository(session)
        DemoResetService(facts, profiles).reset(
            invalid_facts,
            dataset_version=dataset.dataset_version,
            seed=dataset.seed,
            calculated_at=dataset.generated_at,
        )

    with Session(database_engine) as session:
        facts = SqlAlchemyFactRepository(session)
        profiles = SqlAlchemyRelationshipProfileRepository(session)
        assert facts.list_interaction_events() == tuple(
            sorted(dataset.interaction_events, key=lambda event: (event.occurred_at, event.id))
        )
        assert profiles.count() == successful_result.relationship_profile_count
