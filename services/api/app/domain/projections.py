from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from math import isfinite
from uuid import UUID

from app.domain.enums import RelationshipState
from app.domain.value_objects import normalize_optional_text, normalize_text, normalize_utc


class GraphEdgeType(StrEnum):
    DIRECT = "DIRECT"
    POTENTIAL_PATH = "POTENTIAL_PATH"


class GraphEdgeWidth(StrEnum):
    MUTED = "MUTED"
    THIN = "THIN"
    MEDIUM = "MEDIUM"
    THICK = "THICK"


class GraphEdgeOpacity(StrEnum):
    MUTED = "MUTED"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class GraphEdgeStyle(StrEnum):
    SOLID = "SOLID"
    DASHED = "DASHED"
    DOTTED = "DOTTED"


def _unit_interval(value: float, *, field_name: str) -> float:
    normalized = float(value)
    if not isfinite(normalized) or not 0.0 <= normalized <= 1.0:
        raise ValueError(f"{field_name} must be a finite value between 0 and 1")
    return normalized


@dataclass(frozen=True, slots=True)
class GraphCluster:
    id: str
    label: str
    member_count: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", normalize_text(self.id, field_name="id"))
        object.__setattr__(self, "label", normalize_text(self.label, field_name="label"))
        if (
            isinstance(self.member_count, bool)
            or not isinstance(self.member_count, int)
            or self.member_count <= 0
        ):
            raise ValueError("member_count must be a positive integer")


@dataclass(frozen=True, slots=True)
class GraphPersonNode:
    person_id: UUID
    display_name: str
    short_role: str | None
    avatar_url: str | None
    hop: int
    cluster_id: str
    relevance: float
    is_potential: bool
    relationship_state: RelationshipState | None = None
    mutual_connection_ids: tuple[UUID, ...] = ()
    shortest_paths: tuple[tuple[UUID, ...], ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "display_name",
            normalize_text(self.display_name, field_name="display_name"),
        )
        object.__setattr__(
            self,
            "short_role",
            normalize_optional_text(self.short_role, field_name="short_role"),
        )
        object.__setattr__(
            self,
            "avatar_url",
            normalize_optional_text(self.avatar_url, field_name="avatar_url"),
        )
        object.__setattr__(
            self,
            "cluster_id",
            normalize_text(self.cluster_id, field_name="cluster_id"),
        )
        object.__setattr__(
            self,
            "relevance",
            _unit_interval(self.relevance, field_name="relevance"),
        )
        if isinstance(self.hop, bool) or not isinstance(self.hop, int) or self.hop not in (0, 1, 2):
            raise ValueError("hop must be 0, 1, or 2")
        if not isinstance(self.is_potential, bool):
            raise ValueError("is_potential must be a boolean")
        if self.hop == 0 and (self.is_potential or self.relationship_state is not None):
            raise ValueError("the focal node cannot be potential or have a relationship state")
        if self.hop == 1 and (self.is_potential or self.relationship_state is None):
            raise ValueError("a one-hop node must be direct and have a relationship state")
        if self.hop == 2 and (not self.is_potential or self.relationship_state is not None):
            raise ValueError("a two-hop node must be potential and omit relationship state")
        if len(self.mutual_connection_ids) != len(set(self.mutual_connection_ids)):
            raise ValueError("mutual connection IDs must be unique")
        if self.hop < 2 and (self.mutual_connection_ids or self.shortest_paths):
            raise ValueError("only two-hop nodes may carry path context")
        for path in self.shortest_paths:
            if len(path) != 3 or path[-1] != self.person_id:
                raise ValueError("a two-hop shortest path must contain focal, mutual, and target")
        if self.hop == 2:
            if not self.shortest_paths:
                raise ValueError("a two-hop node must carry at least one shortest path")
            path_mutuals = tuple(path[1] for path in self.shortest_paths)
            if path_mutuals != self.mutual_connection_ids:
                raise ValueError("mutual connections must match shortest-path intermediates")


@dataclass(frozen=True, slots=True)
class GraphRelationshipEdge:
    source_person_id: UUID
    target_person_id: UUID
    edge_type: GraphEdgeType
    width: GraphEdgeWidth
    opacity: GraphEdgeOpacity
    style: GraphEdgeStyle
    relationship_state: RelationshipState | None = None
    relationship_strength: float | None = None
    current_activation: float | None = None

    def __post_init__(self) -> None:
        if self.source_person_id == self.target_person_id:
            raise ValueError("a graph edge cannot connect a person to themselves")
        if self.edge_type is GraphEdgeType.DIRECT:
            if (
                self.relationship_state is None
                or self.relationship_strength is None
                or self.current_activation is None
            ):
                raise ValueError("a direct edge requires focal-relative relationship metrics")
            object.__setattr__(
                self,
                "relationship_strength",
                _unit_interval(self.relationship_strength, field_name="relationship_strength"),
            )
            object.__setattr__(
                self,
                "current_activation",
                _unit_interval(self.current_activation, field_name="current_activation"),
            )
            if self.style is GraphEdgeStyle.DOTTED:
                raise ValueError("a direct edge cannot use potential-path styling")
        else:
            if any(
                value is not None
                for value in (
                    self.relationship_state,
                    self.relationship_strength,
                    self.current_activation,
                )
            ):
                raise ValueError("a third-party path edge must omit relationship metrics")
            if (
                self.width is not GraphEdgeWidth.MUTED
                or self.opacity is not GraphEdgeOpacity.MUTED
                or self.style is not GraphEdgeStyle.DOTTED
            ):
                raise ValueError("a potential path edge must use muted dotted presentation")


@dataclass(frozen=True, slots=True)
class GraphProjectionMeta:
    lens: str
    hops: int
    total_network_size: int
    visible_node_count: int
    one_hop_count: int
    two_hop_count: int
    projection_version: str
    generated_at: datetime
    expanded_from_person_ids: tuple[UUID, ...] = ()
    soft_limit_exceeded: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "lens", normalize_text(self.lens, field_name="lens"))
        object.__setattr__(
            self,
            "projection_version",
            normalize_text(self.projection_version, field_name="projection_version"),
        )
        object.__setattr__(
            self,
            "generated_at",
            normalize_utc(self.generated_at, field_name="generated_at"),
        )
        if self.hops not in (1, 2):
            raise ValueError("hops must be 1 or 2")
        for field_name in (
            "total_network_size",
            "visible_node_count",
            "one_hop_count",
            "two_hop_count",
        ):
            value = getattr(self, field_name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{field_name} must be a non-negative integer")
        if self.visible_node_count != 1 + self.one_hop_count + self.two_hop_count:
            raise ValueError("visible node count must equal focal plus one-hop and two-hop counts")
        if self.hops != (2 if self.two_hop_count else 1):
            raise ValueError("hops must reflect whether the projection contains two-hop nodes")
        if len(self.expanded_from_person_ids) != len(set(self.expanded_from_person_ids)):
            raise ValueError("expanded person IDs must be unique")
        if not isinstance(self.soft_limit_exceeded, bool):
            raise ValueError("soft_limit_exceeded must be a boolean")


@dataclass(frozen=True, slots=True)
class GraphProjection:
    focal_person_id: UUID
    nodes: tuple[GraphPersonNode, ...]
    edges: tuple[GraphRelationshipEdge, ...]
    clusters: tuple[GraphCluster, ...]
    meta: GraphProjectionMeta

    def __post_init__(self) -> None:
        node_ids = tuple(node.person_id for node in self.nodes)
        if len(node_ids) != len(set(node_ids)):
            raise ValueError("graph projection nodes must be unique")
        focal_nodes = [
            node for node in self.nodes if node.person_id == self.focal_person_id and node.hop == 0
        ]
        if len(focal_nodes) != 1:
            raise ValueError("graph projection must contain exactly one focal node")
        if len(self.nodes) != self.meta.visible_node_count:
            raise ValueError("projection metadata must match the node collection")
        if sum(node.hop == 1 for node in self.nodes) != self.meta.one_hop_count:
            raise ValueError("projection metadata must match one-hop nodes")
        if sum(node.hop == 2 for node in self.nodes) != self.meta.two_hop_count:
            raise ValueError("projection metadata must match two-hop nodes")
        if self.meta.total_network_size < len(self.nodes) - 1:
            raise ValueError("total network size cannot be below visible non-focal nodes")
        if len(self.nodes) > 80:
            raise ValueError("graph projection cannot exceed the hard visible limit")

        available_node_ids = set(node_ids)
        node_by_id = {node.person_id: node for node in self.nodes}
        for node in self.nodes:
            if node.hop == 2 and any(
                path[0] != self.focal_person_id for path in node.shortest_paths
            ):
                raise ValueError("every potential path must start at the focal person")
        edge_keys: set[tuple[UUID, UUID, GraphEdgeType]] = set()
        for edge in self.edges:
            if (
                edge.source_person_id not in available_node_ids
                or edge.target_person_id not in available_node_ids
            ):
                raise ValueError("graph edges must reference visible person nodes")
            key = (edge.source_person_id, edge.target_person_id, edge.edge_type)
            if key in edge_keys:
                raise ValueError("graph projection edges must be unique")
            edge_keys.add(key)
            source_node = node_by_id[edge.source_person_id]
            target_node = node_by_id[edge.target_person_id]
            if edge.edge_type is GraphEdgeType.DIRECT and not (
                edge.source_person_id == self.focal_person_id and target_node.hop == 1
            ):
                raise ValueError("direct edges must connect the focal person to a one-hop node")
            if edge.edge_type is GraphEdgeType.POTENTIAL_PATH and not (
                source_node.hop == 1
                and target_node.hop == 2
                and source_node.person_id in target_node.mutual_connection_ids
            ):
                raise ValueError("potential edges must connect a visible mutual to a two-hop node")

        expected_direct_targets = {node.person_id for node in self.nodes if node.hop == 1}
        actual_direct_targets = {
            edge.target_person_id for edge in self.edges if edge.edge_type is GraphEdgeType.DIRECT
        }
        if actual_direct_targets != expected_direct_targets:
            raise ValueError("every one-hop node must have exactly one focal direct edge")
        expected_path_edges = {
            (path[1], path[2])
            for node in self.nodes
            if node.hop == 2
            for path in node.shortest_paths
        }
        actual_path_edges = {
            (edge.source_person_id, edge.target_person_id)
            for edge in self.edges
            if edge.edge_type is GraphEdgeType.POTENTIAL_PATH
        }
        if actual_path_edges != expected_path_edges:
            raise ValueError("potential edges must exactly match serialized shortest paths")

        cluster_ids = tuple(cluster.id for cluster in self.clusters)
        if len(cluster_ids) != len(set(cluster_ids)):
            raise ValueError("graph projection clusters must be unique")
        cluster_members = {cluster_id: 0 for cluster_id in cluster_ids}
        for node in self.nodes:
            if node.cluster_id not in cluster_members:
                raise ValueError("every node must reference a visible cluster")
            cluster_members[node.cluster_id] += 1
        if any(cluster.member_count != cluster_members[cluster.id] for cluster in self.clusters):
            raise ValueError("cluster member counts must match visible nodes")
