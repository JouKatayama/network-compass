"""Pure domain types and derivation services for Network Compass."""

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
from app.domain.relationship_config import RELATIONSHIP_MODEL_V1, RelationshipModelConfig
from app.domain.relationship_engine import RelationshipEngine
from app.domain.relationships import EvidenceCoverage, RelationshipContext, RelationshipProfile
from app.domain.value_objects import Confidence, ExternalIdentifier, PersonPair

__all__ = [
    "Activity",
    "Community",
    "CommunityMembership",
    "Confidence",
    "DurationBucket",
    "EvidenceCoverage",
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
    "RELATIONSHIP_MODEL_V1",
    "RecommendationType",
    "RelationshipContext",
    "RelationshipEngine",
    "RelationshipModelConfig",
    "RelationshipProfile",
    "RelationshipState",
    "Skill",
    "UserRelationshipFeedback",
    "Visibility",
]
