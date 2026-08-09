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
from app.domain.facts import CanonicalFactSet
from app.domain.interactions import InteractionEvent
from app.domain.network_projection import (
    PROJECTION_MODEL_VERSION,
    NetworkProjectionConfig,
    NetworkProjectionService,
)
from app.domain.projections import (
    GraphCluster,
    GraphEdgeOpacity,
    GraphEdgeStyle,
    GraphEdgeType,
    GraphEdgeWidth,
    GraphPersonNode,
    GraphProjection,
    GraphProjectionMeta,
    GraphRelationshipEdge,
)
from app.domain.relationship_config import RELATIONSHIP_MODEL_V1, RelationshipModelConfig
from app.domain.relationship_engine import RelationshipEngine
from app.domain.relationships import EvidenceCoverage, RelationshipContext, RelationshipProfile
from app.domain.value_objects import Confidence, ExternalIdentifier, PersonPair

__all__ = [
    "Activity",
    "Community",
    "CommunityMembership",
    "CanonicalFactSet",
    "Confidence",
    "DurationBucket",
    "EvidenceCoverage",
    "ExternalIdentifier",
    "GraphCluster",
    "GraphEdgeOpacity",
    "GraphEdgeStyle",
    "GraphEdgeType",
    "GraphEdgeWidth",
    "GraphPersonNode",
    "GraphProjection",
    "GraphProjectionMeta",
    "GraphRelationshipEdge",
    "HireType",
    "InteractionChannel",
    "InteractionEvent",
    "InteractionSource",
    "InteractionType",
    "NetworkProjectionConfig",
    "NetworkProjectionService",
    "OrganizationUnit",
    "Person",
    "PersonActivity",
    "PersonPair",
    "PersonSkill",
    "ProjectContext",
    "ProjectParticipation",
    "PROJECTION_MODEL_VERSION",
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
