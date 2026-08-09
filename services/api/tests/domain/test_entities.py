from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta, timezone
from uuid import UUID

import pytest

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
    UserRelationshipFeedback,
)
from app.domain.enums import HireType, Visibility
from app.domain.value_objects import ExternalIdentifier, PersonPair


def test_person_normalizes_text_and_joined_at_to_utc() -> None:
    joined_in_tokyo = datetime(2026, 8, 8, 9, tzinfo=timezone(timedelta(hours=9)))

    person = Person(
        id=UUID(int=1),
        display_name="  Nao Katayama  ",
        joined_at=joined_in_tokyo,
        hire_type=HireType.EXPERIENCED,
        external_identifiers=(ExternalIdentifier(" HR ", " 001 "),),
    )

    assert person.display_name == "Nao Katayama"
    assert person.joined_at == datetime(2026, 8, 8, tzinfo=UTC)
    assert person.external_identifiers[0].source_system == "hr"


def test_person_rejects_duplicate_external_identifier_mappings() -> None:
    identifier = ExternalIdentifier("hr", "001")

    with pytest.raises(ValueError, match="must be unique"):
        Person(
            id=UUID(int=1),
            display_name="Nao",
            joined_at=datetime(2026, 8, 8, tzinfo=UTC),
            hire_type=HireType.OTHER,
            external_identifiers=(identifier, identifier),
        )


def test_domain_entities_reject_naive_timestamps() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        Person(
            id=UUID(int=1),
            display_name="Nao",
            joined_at=datetime(2026, 8, 8),
            hire_type=HireType.OTHER,
        )


def test_context_facts_preserve_visibility_and_valid_lifecycle_intervals() -> None:
    started_at = datetime(2026, 1, 1, tzinfo=UTC)
    ended_at = datetime(2026, 8, 1, tzinfo=UTC)
    person_id = UUID(int=1)
    community_id = UUID(int=2)
    activity_id = UUID(int=3)
    skill_id = UUID(int=4)
    project_id = UUID(int=5)

    assert OrganizationUnit(UUID(int=6), "Technology").name == "Technology"
    assert Community(community_id, "AI Community").name == "AI Community"
    assert CommunityMembership(person_id, community_id, started_at, ended_at).left_at == ended_at
    assert Activity(activity_id, "Cycling").name == "Cycling"
    assert (
        PersonActivity(person_id, activity_id, started_at, Visibility.NETWORK).visibility
        is Visibility.NETWORK
    )
    assert Skill(skill_id, "Python").name == "Python"
    assert PersonSkill(person_id, skill_id, started_at).declared_at == started_at
    assert ProjectContext(project_id, "Compass", started_at, ended_at).ended_at == ended_at
    assert ProjectParticipation(person_id, project_id, started_at, ended_at).ended_at == ended_at


def test_lifecycle_interval_rejects_end_before_start() -> None:
    with pytest.raises(ValueError, match="cannot be before"):
        ProjectParticipation(
            person_id=UUID(int=1),
            project_id=UUID(int=2),
            started_at=datetime(2026, 8, 8, tzinfo=UTC),
            ended_at=datetime(2026, 8, 7, tzinfo=UTC),
        )


def test_feedback_is_immutable_and_must_be_authored_by_a_pair_member() -> None:
    pair = PersonPair.between(UUID(int=1), UUID(int=2))
    feedback = UserRelationshipFeedback(
        id=UUID(int=10),
        pair=pair,
        created_by_person_id=UUID(int=1),
        created_at=datetime(2026, 8, 8, tzinfo=UTC),
    )

    assert feedback.pair == pair
    with pytest.raises(FrozenInstanceError):
        feedback.__setattr__("created_by_person_id", UUID(int=2))

    with pytest.raises(ValueError, match="created by a person in the pair"):
        UserRelationshipFeedback(
            id=UUID(int=11),
            pair=pair,
            created_by_person_id=UUID(int=3),
            created_at=datetime(2026, 8, 8, tzinfo=UTC),
        )
