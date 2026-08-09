"""Pure domain types for Network Compass facts and interaction evidence."""

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
from app.domain.enums import (
    DurationBucket,
    HireType,
    InteractionChannel,
    InteractionSource,
    InteractionType,
    RecommendationType,
    RelationshipState,
    Visibility,
)
from app.domain.interactions import InteractionEvent
from app.domain.value_objects import Confidence, ExternalIdentifier, PersonPair

__all__ = [
    "Activity",
    "Community",
    "CommunityMembership",
    "Confidence",
    "DurationBucket",
    "ExternalIdentifier",
    "HireType",
    "InteractionChannel",
    "InteractionEvent",
    "InteractionSource",
    "InteractionType",
    "OrganizationUnit",
    "Person",
    "PersonActivity",
    "PersonPair",
    "PersonSkill",
    "ProjectContext",
    "ProjectParticipation",
    "RecommendationType",
    "RelationshipState",
    "Skill",
    "UserRelationshipFeedback",
    "Visibility",
]
