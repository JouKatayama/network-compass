from typing import Self
from uuid import UUID

from pydantic import AwareDatetime, Field, model_validator

from app.domain.enums import RelationshipState
from app.domain.projections import (
    GraphEdgeOpacity,
    GraphEdgeStyle,
    GraphEdgeType,
    GraphEdgeWidth,
    GraphPersonNode,
    GraphProjection,
    GraphRelationshipEdge,
)
from app.models.domain import DomainSchema


class GraphClusterSchema(DomainSchema):
    id: str
    label: str
    member_count: int = Field(gt=0)


class GraphPersonNodeSchema(DomainSchema):
    person_id: UUID
    display_name: str
    short_role: str | None
    avatar_url: str | None
    hop: int = Field(ge=0, le=2)
    cluster_id: str
    relevance: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    is_potential: bool
    relationship_state: RelationshipState | None = None
    mutual_connection_ids: tuple[UUID, ...] | None = None
    shortest_paths: tuple[tuple[UUID, ...], ...] | None = None

    @classmethod
    def from_domain(cls, node: GraphPersonNode) -> Self:
        return cls(
            person_id=node.person_id,
            display_name=node.display_name,
            short_role=node.short_role,
            avatar_url=node.avatar_url,
            hop=node.hop,
            cluster_id=node.cluster_id,
            relevance=node.relevance,
            is_potential=node.is_potential,
            relationship_state=node.relationship_state,
            mutual_connection_ids=node.mutual_connection_ids if node.hop == 2 else None,
            shortest_paths=node.shortest_paths if node.hop == 2 else None,
        )


class GraphRelationshipEdgeSchema(DomainSchema):
    source_person_id: UUID
    target_person_id: UUID
    edge_type: GraphEdgeType
    width: GraphEdgeWidth
    opacity: GraphEdgeOpacity
    style: GraphEdgeStyle
    relationship_state: RelationshipState | None = None
    relationship_strength: float | None = Field(default=None, ge=0.0, le=1.0)
    current_activation: float | None = Field(default=None, ge=0.0, le=1.0)

    @classmethod
    def from_domain(cls, edge: GraphRelationshipEdge) -> Self:
        return cls.model_validate(edge)


class GraphProjectionMetaSchema(DomainSchema):
    lens: str
    hops: int = Field(ge=1, le=2)
    total_network_size: int = Field(ge=0)
    visible_node_count: int = Field(ge=1, le=80)
    one_hop_count: int = Field(ge=0, le=79)
    two_hop_count: int = Field(ge=0, le=79)
    projection_version: str
    generated_at: AwareDatetime
    expanded_from_person_ids: tuple[UUID, ...] = ()
    soft_limit_exceeded: bool = False


class GraphProjectionSchema(DomainSchema):
    focal_person_id: UUID
    nodes: tuple[GraphPersonNodeSchema, ...]
    edges: tuple[GraphRelationshipEdgeSchema, ...]
    clusters: tuple[GraphClusterSchema, ...]
    meta: GraphProjectionMetaSchema

    @model_validator(mode="after")
    def validate_projection_bounds(self) -> Self:
        if len(self.nodes) != self.meta.visible_node_count:
            raise ValueError("visible node count must match nodes")
        if sum(node.hop == 1 for node in self.nodes) != self.meta.one_hop_count:
            raise ValueError("one-hop count must match nodes")
        if sum(node.hop == 2 for node in self.nodes) != self.meta.two_hop_count:
            raise ValueError("two-hop count must match nodes")
        return self

    @classmethod
    def from_domain(cls, projection: GraphProjection) -> Self:
        return cls(
            focal_person_id=projection.focal_person_id,
            nodes=tuple(GraphPersonNodeSchema.from_domain(node) for node in projection.nodes),
            edges=tuple(GraphRelationshipEdgeSchema.from_domain(edge) for edge in projection.edges),
            clusters=tuple(GraphClusterSchema.model_validate(item) for item in projection.clusters),
            meta=GraphProjectionMetaSchema.model_validate(projection.meta),
        )


class GraphExpansionRequestSchema(DomainSchema):
    selected_person_id: UUID
    expanded_from_person_ids: tuple[UUID, ...] = Field(default=(), max_length=80)

    @model_validator(mode="after")
    def validate_expansion_history(self) -> Self:
        if len(self.expanded_from_person_ids) != len(set(self.expanded_from_person_ids)):
            raise ValueError("expanded person IDs must be unique")
        if self.selected_person_id in self.expanded_from_person_ids:
            raise ValueError("selected person must not already be expanded")
        return self
