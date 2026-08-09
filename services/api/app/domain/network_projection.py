from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from math import exp
from uuid import UUID

import networkx as nx

from app.domain.entities import OrganizationUnit, Person
from app.domain.enums import RelationshipState
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
from app.domain.relationships import RelationshipProfile
from app.domain.value_objects import PersonPair, normalize_text, normalize_utc

PROJECTION_MODEL_VERSION = "graph-projection-v0.1.0"


@dataclass(frozen=True, slots=True)
class NetworkProjectionConfig:
    projection_version: str = PROJECTION_MODEL_VERSION
    lens: str = "RELATIONSHIP_RELEVANCE"
    default_one_hop_limit: int = 24
    default_teaser_limit: int = 12
    expansion_limit: int = 8
    soft_visible_limit: int = 60
    hard_visible_limit: int = 80
    max_paths_per_teaser: int = 3

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "projection_version",
            normalize_text(self.projection_version, field_name="projection_version"),
        )
        object.__setattr__(self, "lens", normalize_text(self.lens, field_name="lens"))
        for field_name in (
            "default_one_hop_limit",
            "default_teaser_limit",
            "expansion_limit",
            "soft_visible_limit",
            "hard_visible_limit",
            "max_paths_per_teaser",
        ):
            value = getattr(self, field_name)
            if isinstance(value, bool) or not isinstance(value, int):
                raise ValueError(f"{field_name} must be an integer")
        if not 0 < self.default_one_hop_limit < self.hard_visible_limit:
            raise ValueError("default one-hop limit must be positive and below the hard limit")
        if not 0 <= self.default_teaser_limit < self.hard_visible_limit:
            raise ValueError("default teaser limit must be non-negative and below the hard limit")
        if not 0 < self.expansion_limit <= 8:
            raise ValueError("expansion limit must be between 1 and 8")
        if not 0 < self.soft_visible_limit <= self.hard_visible_limit <= 80:
            raise ValueError("visible limits must satisfy 0 < soft <= hard <= 80")
        if not 0 < self.max_paths_per_teaser <= 3:
            raise ValueError("path context must contain between one and three paths")


@dataclass(frozen=True, slots=True)
class _DirectCandidate:
    person: Person
    profile: RelationshipProfile
    relevance: float
    cluster_id: str


@dataclass(frozen=True, slots=True)
class _TeaserCandidate:
    person: Person
    relevance: float
    cluster_id: str
    paths: tuple[tuple[UUID, UUID, UUID], ...]
    gateway_ids: tuple[UUID, ...]


_STATE_MEMORY_UTILITY: Mapping[RelationshipState, float] = {
    RelationshipState.DORMANT: 1.0,
    RelationshipState.RECONNECTED: 0.95,
    RelationshipState.NEW: 0.75,
    RelationshipState.ACTIVE: 0.72,
    RelationshipState.CLOSE: 0.68,
    RelationshipState.WEAK: 0.62,
}

_STATE_DIVERSITY_ORDER = (
    RelationshipState.DORMANT,
    RelationshipState.RECONNECTED,
    RelationshipState.CLOSE,
    RelationshipState.ACTIVE,
    RelationshipState.WEAK,
    RelationshipState.NEW,
)


class NetworkProjectionService:
    def __init__(self, config: NetworkProjectionConfig | None = None) -> None:
        self.config = config or NetworkProjectionConfig()

    def build(
        self,
        *,
        focal_person_id: UUID,
        people: Iterable[Person],
        organization_units: Iterable[OrganizationUnit],
        relationship_profiles: Iterable[RelationshipProfile],
        generated_at: datetime,
        one_hop_limit: int | None = None,
        teaser_limit: int | None = None,
    ) -> GraphProjection:
        calculation_time = normalize_utc(generated_at, field_name="generated_at")
        person_by_id, organization_by_id, profile_by_pair, graph = self._prepare_inputs(
            people,
            organization_units,
            relationship_profiles,
        )
        if focal_person_id not in person_by_id:
            raise ValueError("focal person does not exist in the authorized projection facts")

        direct_limit = self._bounded_limit(
            one_hop_limit,
            default=self.config.default_one_hop_limit,
            maximum=self.config.default_one_hop_limit,
            field_name="one_hop_limit",
        )
        potential_limit = self._bounded_limit(
            teaser_limit,
            default=self.config.default_teaser_limit,
            maximum=self.config.default_teaser_limit,
            field_name="teaser_limit",
        )

        direct_candidates = self._direct_candidates(
            focal_person_id,
            graph,
            person_by_id,
            profile_by_pair,
            calculation_time,
        )
        selected_direct = self._select_direct(direct_candidates, direct_limit)
        selected_direct_ids = {candidate.person.id for candidate in selected_direct}
        teaser_candidates = self._teaser_candidates(
            focal_person_id,
            graph,
            person_by_id,
            profile_by_pair,
            calculation_time,
            visible_gateway_ids=selected_direct_ids,
            visible_cluster_ids={candidate.cluster_id for candidate in selected_direct},
        )
        selected_teasers = self._select_teasers(teaser_candidates, potential_limit)
        return self._assemble(
            focal_person_id=focal_person_id,
            person_by_id=person_by_id,
            organization_by_id=organization_by_id,
            graph=graph,
            direct_candidates=selected_direct,
            teaser_candidates=selected_teasers,
            generated_at=calculation_time,
            expanded_from_person_ids=(),
        )

    def expand(
        self,
        projection: GraphProjection,
        *,
        selected_person_id: UUID,
        people: Iterable[Person],
        organization_units: Iterable[OrganizationUnit],
        relationship_profiles: Iterable[RelationshipProfile],
    ) -> GraphProjection:
        person_by_id, organization_by_id, profile_by_pair, graph = self._prepare_inputs(
            people,
            organization_units,
            relationship_profiles,
        )
        if projection.focal_person_id not in person_by_id:
            raise ValueError("the focal person is no longer available")
        visible_nodes = {node.person_id: node for node in projection.nodes}
        if selected_person_id not in visible_nodes:
            raise ValueError("selected person must already be visible")
        if selected_person_id in projection.meta.expanded_from_person_ids:
            return projection

        remaining_capacity = min(
            self.config.expansion_limit,
            self.config.hard_visible_limit - len(projection.nodes),
        )
        expanded_from = (*projection.meta.expanded_from_person_ids, selected_person_id)
        if remaining_capacity <= 0:
            return self._replace_meta(projection, expanded_from)

        focal_person_id = projection.focal_person_id
        distance_by_person = nx.single_source_shortest_path_length(
            graph,
            focal_person_id,
            cutoff=2,
        )
        eligible_ids = {
            person_id
            for person_id in graph.neighbors(selected_person_id)
            if person_id not in visible_nodes and distance_by_person.get(person_id) in (1, 2)
        }
        if not eligible_ids:
            return self._replace_meta(projection, expanded_from)

        calculation_time = projection.meta.generated_at
        all_direct = self._direct_candidates(
            focal_person_id,
            graph,
            person_by_id,
            profile_by_pair,
            calculation_time,
        )
        direct_by_id = {candidate.person.id: candidate for candidate in all_direct}
        selected_new_direct = self._select_direct(
            [direct_by_id[person_id] for person_id in eligible_ids if person_id in direct_by_id],
            remaining_capacity,
        )
        remaining_capacity -= len(selected_new_direct)

        new_visible_gateway_ids = {node.person_id for node in projection.nodes if node.hop == 1} | {
            candidate.person.id for candidate in selected_new_direct
        }
        new_teasers: list[_TeaserCandidate] = []
        if remaining_capacity:
            all_teasers = self._teaser_candidates(
                focal_person_id,
                graph,
                person_by_id,
                profile_by_pair,
                calculation_time,
                visible_gateway_ids=new_visible_gateway_ids,
                visible_cluster_ids={node.cluster_id for node in projection.nodes},
                preferred_gateway_id=(
                    selected_person_id if selected_person_id in new_visible_gateway_ids else None
                ),
            )
            new_teasers = self._select_teasers(
                [
                    candidate
                    for candidate in all_teasers
                    if candidate.person.id in eligible_ids
                    and candidate.person.id not in visible_nodes
                ],
                remaining_capacity,
            )

        return self._extend_projection(
            projection,
            graph=graph,
            organization_by_id=organization_by_id,
            new_direct=selected_new_direct,
            new_teasers=new_teasers,
            expanded_from_person_ids=expanded_from,
        )

    @staticmethod
    def _bounded_limit(
        value: int | None,
        *,
        default: int,
        maximum: int,
        field_name: str,
    ) -> int:
        normalized = default if value is None else value
        if (
            isinstance(normalized, bool)
            or not isinstance(normalized, int)
            or not 0 <= normalized <= maximum
        ):
            raise ValueError(f"{field_name} must be between 0 and {maximum}")
        return normalized

    @staticmethod
    def _prepare_inputs(
        people: Iterable[Person],
        organization_units: Iterable[OrganizationUnit],
        relationship_profiles: Iterable[RelationshipProfile],
    ) -> tuple[
        dict[UUID, Person],
        dict[UUID, OrganizationUnit],
        dict[PersonPair, RelationshipProfile],
        nx.Graph[UUID],
    ]:
        person_items = tuple(people)
        person_by_id = {person.id: person for person in person_items}
        if len(person_items) != len(person_by_id):
            raise ValueError("people must have unique IDs")
        organization_items = tuple(organization_units)
        organization_by_id = {organization.id: organization for organization in organization_items}
        if len(organization_items) != len(organization_by_id):
            raise ValueError("organization units must have unique IDs")

        profile_items = tuple(relationship_profiles)
        profile_by_pair = {profile.pair: profile for profile in profile_items}
        if len(profile_items) != len(profile_by_pair):
            raise ValueError("relationship profiles must have unique person pairs")

        graph: nx.Graph[UUID] = nx.Graph()
        graph.add_nodes_from(person_by_id)
        for profile in profile_items:
            if (
                profile.pair.person_a_id in person_by_id
                and profile.pair.person_b_id in person_by_id
            ):
                graph.add_edge(
                    profile.pair.person_a_id,
                    profile.pair.person_b_id,
                    profile=profile,
                )
        return person_by_id, organization_by_id, profile_by_pair, graph

    def _direct_candidates(
        self,
        focal_person_id: UUID,
        graph: nx.Graph[UUID],
        person_by_id: Mapping[UUID, Person],
        profile_by_pair: Mapping[PersonPair, RelationshipProfile],
        generated_at: datetime,
    ) -> list[_DirectCandidate]:
        return [
            _DirectCandidate(
                person=person_by_id[person_id],
                profile=profile_by_pair[PersonPair.between(focal_person_id, person_id)],
                relevance=self._direct_relevance(
                    profile_by_pair[PersonPair.between(focal_person_id, person_id)],
                    generated_at,
                ),
                cluster_id=self._cluster_id(person_by_id[person_id]),
            )
            for person_id in graph.neighbors(focal_person_id)
        ]

    @staticmethod
    def _direct_relevance(profile: RelationshipProfile, generated_at: datetime) -> float:
        age_days = max(
            (generated_at - profile.last_meaningful_interaction_at).total_seconds() / 86_400.0,
            0.0,
        )
        recency = exp(-age_days / max(profile.expected_cadence_days, 30.0))
        relevance = (
            0.28 * profile.current_activation
            + 0.24 * profile.historical_depth
            + 0.15 * profile.relationship_strength
            + 0.10 * profile.data_confidence
            + 0.08 * recency
            + 0.15 * _STATE_MEMORY_UTILITY[profile.state]
        )
        return round(min(max(relevance, 0.0), 1.0), 6)

    def _select_direct(
        self,
        candidates: Sequence[_DirectCandidate],
        limit: int,
    ) -> list[_DirectCandidate]:
        if limit <= 0:
            return []
        by_id = {candidate.person.id: candidate for candidate in candidates}
        selected: list[_DirectCandidate] = []
        selected_ids: set[UUID] = set()

        def add(candidate: _DirectCandidate | None) -> None:
            if (
                candidate is not None
                and candidate.person.id not in selected_ids
                and len(selected) < limit
            ):
                selected.append(candidate)
                selected_ids.add(candidate.person.id)

        for state in _STATE_DIVERSITY_ORDER:
            add(
                self._best(
                    candidate for candidate in candidates if candidate.profile.state is state
                )
            )

        cluster_ids = sorted({candidate.cluster_id for candidate in candidates})
        for cluster_id in cluster_ids:
            add(
                self._best(
                    candidate for candidate in candidates if candidate.cluster_id == cluster_id
                )
            )

        while len(selected) < min(limit, len(by_id)):
            state_counts = Counter(candidate.profile.state for candidate in selected)
            cluster_counts = Counter(candidate.cluster_id for candidate in selected)
            remaining = [
                candidate for candidate in candidates if candidate.person.id not in selected_ids
            ]
            if not remaining:
                break
            add(
                max(
                    remaining,
                    key=lambda candidate: (
                        round(
                            0.72 * candidate.relevance
                            + 0.16 / (1 + state_counts[candidate.profile.state])
                            + 0.12 / (1 + cluster_counts[candidate.cluster_id]),
                            9,
                        ),
                        candidate.relevance,
                        -candidate.person.id.int,
                    ),
                )
            )

        return sorted(
            selected, key=lambda candidate: (-candidate.relevance, candidate.person.id.int)
        )

    def _teaser_candidates(
        self,
        focal_person_id: UUID,
        graph: nx.Graph[UUID],
        person_by_id: Mapping[UUID, Person],
        profile_by_pair: Mapping[PersonPair, RelationshipProfile],
        generated_at: datetime,
        *,
        visible_gateway_ids: set[UUID],
        visible_cluster_ids: set[str],
        preferred_gateway_id: UUID | None = None,
    ) -> list[_TeaserCandidate]:
        distance_by_person = nx.single_source_shortest_path_length(
            graph,
            focal_person_id,
            cutoff=2,
        )
        candidates: list[_TeaserCandidate] = []
        for person_id, distance in distance_by_person.items():
            if distance != 2:
                continue
            path_records: list[tuple[float, tuple[UUID, UUID, UUID]]] = []
            for raw_path in nx.all_shortest_paths(graph, focal_person_id, person_id):
                path = (raw_path[0], raw_path[1], raw_path[2])
                gateway_id = path[1]
                if gateway_id not in visible_gateway_ids:
                    continue
                focal_profile = profile_by_pair[PersonPair.between(focal_person_id, gateway_id)]
                path_profile = profile_by_pair[PersonPair.between(gateway_id, person_id)]
                gateway_relevance = self._direct_relevance(focal_profile, generated_at)
                path_quality = (
                    0.44 * path_profile.current_activation
                    + 0.31 * path_profile.historical_depth
                    + 0.15 * path_profile.relationship_strength
                    + 0.10 * path_profile.data_confidence
                )
                accessibility = 0.58 * path_quality + 0.42 * gateway_relevance
                if gateway_id == preferred_gateway_id:
                    accessibility += 0.12
                path_records.append((min(accessibility, 1.0), path))
            if not path_records:
                continue
            path_records.sort(key=lambda item: (-item[0], tuple(value.int for value in item[1])))
            selected_path_records = path_records[: self.config.max_paths_per_teaser]
            cluster_id = self._cluster_id(person_by_id[person_id])
            cluster_novelty = 1.0 if cluster_id not in visible_cluster_ids else 0.0
            relevance = round(
                min(0.90 * selected_path_records[0][0] + 0.10 * cluster_novelty, 1.0),
                6,
            )
            paths = tuple(record[1] for record in selected_path_records)
            candidates.append(
                _TeaserCandidate(
                    person=person_by_id[person_id],
                    relevance=relevance,
                    cluster_id=cluster_id,
                    paths=paths,
                    gateway_ids=tuple(path[1] for path in paths),
                )
            )
        return candidates

    def _select_teasers(
        self,
        candidates: Sequence[_TeaserCandidate],
        limit: int,
    ) -> list[_TeaserCandidate]:
        selected: list[_TeaserCandidate] = []
        remaining = list(candidates)
        while remaining and len(selected) < limit:
            cluster_counts = Counter(candidate.cluster_id for candidate in selected)
            gateway_counts = Counter(
                gateway_id for candidate in selected for gateway_id in candidate.gateway_ids[:1]
            )
            candidate = max(
                remaining,
                key=lambda item: (
                    round(
                        0.78 * item.relevance
                        + 0.13 / (1 + cluster_counts[item.cluster_id])
                        + 0.09 / (1 + gateway_counts[item.gateway_ids[0]]),
                        9,
                    ),
                    item.relevance,
                    -item.person.id.int,
                ),
            )
            selected.append(candidate)
            remaining.remove(candidate)
        return sorted(
            selected, key=lambda candidate: (-candidate.relevance, candidate.person.id.int)
        )

    @staticmethod
    def _best(candidates: Iterable[_DirectCandidate]) -> _DirectCandidate | None:
        return max(
            candidates,
            key=lambda candidate: (candidate.relevance, -candidate.person.id.int),
            default=None,
        )

    def _assemble(
        self,
        *,
        focal_person_id: UUID,
        person_by_id: Mapping[UUID, Person],
        organization_by_id: Mapping[UUID, OrganizationUnit],
        graph: nx.Graph[UUID],
        direct_candidates: Sequence[_DirectCandidate],
        teaser_candidates: Sequence[_TeaserCandidate],
        generated_at: datetime,
        expanded_from_person_ids: tuple[UUID, ...],
    ) -> GraphProjection:
        focal_person = person_by_id[focal_person_id]
        nodes = [self._focal_node(focal_person)]
        nodes.extend(self._direct_node(candidate) for candidate in direct_candidates)
        nodes.extend(self._teaser_node(candidate) for candidate in teaser_candidates)
        edges = [
            self._direct_edge(focal_person_id, candidate.person.id, candidate.profile)
            for candidate in direct_candidates
        ]
        edges.extend(
            self._potential_edge(path[1], path[2])
            for candidate in teaser_candidates
            for path in candidate.paths
        )
        return self._projection(
            focal_person_id=focal_person_id,
            nodes=nodes,
            edges=edges,
            organization_by_id=organization_by_id,
            total_network_size=self._total_network_size(graph, focal_person_id),
            generated_at=generated_at,
            expanded_from_person_ids=expanded_from_person_ids,
        )

    def _extend_projection(
        self,
        projection: GraphProjection,
        *,
        graph: nx.Graph[UUID],
        organization_by_id: Mapping[UUID, OrganizationUnit],
        new_direct: Sequence[_DirectCandidate],
        new_teasers: Sequence[_TeaserCandidate],
        expanded_from_person_ids: tuple[UUID, ...],
    ) -> GraphProjection:
        nodes = list(projection.nodes)
        nodes.extend(self._direct_node(candidate) for candidate in new_direct)
        nodes.extend(self._teaser_node(candidate) for candidate in new_teasers)
        edges = list(projection.edges)
        edges.extend(
            self._direct_edge(projection.focal_person_id, candidate.person.id, candidate.profile)
            for candidate in new_direct
        )
        existing_edge_keys = {
            (edge.source_person_id, edge.target_person_id, edge.edge_type) for edge in edges
        }
        for candidate in new_teasers:
            for path in candidate.paths:
                edge = self._potential_edge(path[1], path[2])
                key = (edge.source_person_id, edge.target_person_id, edge.edge_type)
                if key not in existing_edge_keys:
                    edges.append(edge)
                    existing_edge_keys.add(key)
        return self._projection(
            focal_person_id=projection.focal_person_id,
            nodes=nodes,
            edges=edges,
            organization_by_id=organization_by_id,
            total_network_size=self._total_network_size(graph, projection.focal_person_id),
            generated_at=projection.meta.generated_at,
            expanded_from_person_ids=expanded_from_person_ids,
        )

    def _replace_meta(
        self,
        projection: GraphProjection,
        expanded_from_person_ids: tuple[UUID, ...],
    ) -> GraphProjection:
        return GraphProjection(
            focal_person_id=projection.focal_person_id,
            nodes=projection.nodes,
            edges=projection.edges,
            clusters=projection.clusters,
            meta=GraphProjectionMeta(
                lens=projection.meta.lens,
                hops=projection.meta.hops,
                total_network_size=projection.meta.total_network_size,
                visible_node_count=projection.meta.visible_node_count,
                one_hop_count=projection.meta.one_hop_count,
                two_hop_count=projection.meta.two_hop_count,
                projection_version=projection.meta.projection_version,
                generated_at=projection.meta.generated_at,
                expanded_from_person_ids=expanded_from_person_ids,
                soft_limit_exceeded=projection.meta.soft_limit_exceeded,
            ),
        )

    def _projection(
        self,
        *,
        focal_person_id: UUID,
        nodes: Sequence[GraphPersonNode],
        edges: Sequence[GraphRelationshipEdge],
        organization_by_id: Mapping[UUID, OrganizationUnit],
        total_network_size: int,
        generated_at: datetime,
        expanded_from_person_ids: tuple[UUID, ...],
    ) -> GraphProjection:
        cluster_counts = Counter(node.cluster_id for node in nodes)
        cluster_labels = {
            self._organization_cluster_id(organization_id): organization.name
            for organization_id, organization in organization_by_id.items()
        }
        cluster_labels["organization:unassigned"] = "Unassigned"
        clusters = tuple(
            GraphCluster(
                id=cluster_id,
                label=cluster_labels.get(cluster_id, "Unknown organization"),
                member_count=member_count,
            )
            for cluster_id, member_count in sorted(cluster_counts.items())
        )
        one_hop_count = sum(node.hop == 1 for node in nodes)
        two_hop_count = sum(node.hop == 2 for node in nodes)
        return GraphProjection(
            focal_person_id=focal_person_id,
            nodes=tuple(nodes),
            edges=tuple(edges),
            clusters=clusters,
            meta=GraphProjectionMeta(
                lens=self.config.lens,
                hops=2 if two_hop_count else 1,
                total_network_size=total_network_size,
                visible_node_count=len(nodes),
                one_hop_count=one_hop_count,
                two_hop_count=two_hop_count,
                projection_version=self.config.projection_version,
                generated_at=generated_at,
                expanded_from_person_ids=expanded_from_person_ids,
                soft_limit_exceeded=len(nodes) > self.config.soft_visible_limit,
            ),
        )

    @staticmethod
    def _focal_node(person: Person) -> GraphPersonNode:
        return GraphPersonNode(
            person_id=person.id,
            display_name=person.display_name,
            short_role=person.role,
            avatar_url=person.avatar_url,
            hop=0,
            cluster_id=NetworkProjectionService._cluster_id(person),
            relevance=1.0,
            is_potential=False,
        )

    @staticmethod
    def _direct_node(candidate: _DirectCandidate) -> GraphPersonNode:
        return GraphPersonNode(
            person_id=candidate.person.id,
            display_name=candidate.person.display_name,
            short_role=candidate.person.role,
            avatar_url=candidate.person.avatar_url,
            hop=1,
            cluster_id=candidate.cluster_id,
            relevance=candidate.relevance,
            is_potential=False,
            relationship_state=candidate.profile.state,
        )

    @staticmethod
    def _teaser_node(candidate: _TeaserCandidate) -> GraphPersonNode:
        return GraphPersonNode(
            person_id=candidate.person.id,
            display_name=candidate.person.display_name,
            short_role=candidate.person.role,
            avatar_url=candidate.person.avatar_url,
            hop=2,
            cluster_id=candidate.cluster_id,
            relevance=candidate.relevance,
            is_potential=True,
            mutual_connection_ids=candidate.gateway_ids,
            shortest_paths=candidate.paths,
        )

    @staticmethod
    def _direct_edge(
        focal_person_id: UUID,
        target_person_id: UUID,
        profile: RelationshipProfile,
    ) -> GraphRelationshipEdge:
        if profile.relationship_strength >= 0.64:
            width = GraphEdgeWidth.THICK
        elif profile.relationship_strength >= 0.35:
            width = GraphEdgeWidth.MEDIUM
        else:
            width = GraphEdgeWidth.THIN

        if profile.current_activation >= 0.60:
            opacity = GraphEdgeOpacity.HIGH
        elif profile.current_activation >= 0.25:
            opacity = GraphEdgeOpacity.MEDIUM
        else:
            opacity = GraphEdgeOpacity.LOW
        style = (
            GraphEdgeStyle.DASHED
            if profile.state is RelationshipState.DORMANT
            else GraphEdgeStyle.SOLID
        )
        return GraphRelationshipEdge(
            source_person_id=focal_person_id,
            target_person_id=target_person_id,
            edge_type=GraphEdgeType.DIRECT,
            relationship_state=profile.state,
            relationship_strength=profile.relationship_strength,
            current_activation=profile.current_activation,
            width=width,
            opacity=opacity,
            style=style,
        )

    @staticmethod
    def _potential_edge(source_person_id: UUID, target_person_id: UUID) -> GraphRelationshipEdge:
        return GraphRelationshipEdge(
            source_person_id=source_person_id,
            target_person_id=target_person_id,
            edge_type=GraphEdgeType.POTENTIAL_PATH,
            width=GraphEdgeWidth.MUTED,
            opacity=GraphEdgeOpacity.MUTED,
            style=GraphEdgeStyle.DOTTED,
        )

    @staticmethod
    def _cluster_id(person: Person) -> str:
        if person.primary_organization_unit_id is None:
            return "organization:unassigned"
        return NetworkProjectionService._organization_cluster_id(
            person.primary_organization_unit_id
        )

    @staticmethod
    def _organization_cluster_id(organization_id: UUID) -> str:
        return f"organization:{organization_id}"

    @staticmethod
    def _total_network_size(graph: nx.Graph[UUID], focal_person_id: UUID) -> int:
        return max(
            len(nx.single_source_shortest_path_length(graph, focal_person_id, cutoff=2)) - 1,
            0,
        )
