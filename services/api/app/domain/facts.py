from dataclasses import dataclass

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
from app.domain.interactions import InteractionEvent


@dataclass(frozen=True, slots=True)
class CanonicalFactSet:
    people: tuple[Person, ...]
    organization_units: tuple[OrganizationUnit, ...]
    communities: tuple[Community, ...]
    community_memberships: tuple[CommunityMembership, ...]
    activities: tuple[Activity, ...]
    person_activities: tuple[PersonActivity, ...]
    skills: tuple[Skill, ...]
    person_skills: tuple[PersonSkill, ...]
    projects: tuple[ProjectContext, ...]
    project_participations: tuple[ProjectParticipation, ...]
    interaction_events: tuple[InteractionEvent, ...]
    user_relationship_feedback: tuple[UserRelationshipFeedback, ...] = ()
