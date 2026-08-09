from collections import Counter
from dataclasses import dataclass, replace
from uuid import UUID

import pytest
from network_compass_synthetic.generator import generate_dataset
from network_compass_synthetic.models import SyntheticDataset

from app.application.projection_serialization import canonical_projection_json
from app.domain.entities import Person
from app.domain.enums import RelationshipState
from app.domain.network_projection import NetworkProjectionConfig, NetworkProjectionService
from app.domain.projections import (
    GraphEdgeOpacity,
    GraphEdgeStyle,
    GraphEdgeType,
    GraphEdgeWidth,
    GraphProjection,
)
from app.domain.relationship_engine import RelationshipEngine
from app.domain.relationships import RelationshipProfile
from app.domain.value_objects import PersonPair


@dataclass(frozen=True, slots=True)
class DemoProjectionContext:
    dataset: SyntheticDataset
    profiles: tuple[RelationshipProfile, ...]
    people_by_code: dict[str, Person]
    code_by_person_id: dict[UUID, str]
    projection: GraphProjection


@pytest.fixture(scope="module")
def demo_context() -> DemoProjectionContext:
    dataset = generate_dataset("demo")
    people_by_code = {
        identifier.external_id: person
        for person in dataset.people
        for identifier in person.external_identifiers
        if identifier.source_system == "synthetic"
    }
    profiles = RelationshipEngine().derive_profiles(
        dataset.interaction_events,
        calculated_at=dataset.generated_at,
    )
    projection = NetworkProjectionService().build(
        focal_person_id=people_by_code["P001"].id,
        people=dataset.people,
        organization_units=dataset.organization_units,
        relationship_profiles=profiles,
        generated_at=dataset.generated_at,
    )
    return DemoProjectionContext(
        dataset=dataset,
        profiles=profiles,
        people_by_code=people_by_code,
        code_by_person_id={person.id: code for code, person in people_by_code.items()},
        projection=projection,
    )


def test_p001_default_projection_is_bounded_diverse_and_person_only(
    demo_context: DemoProjectionContext,
) -> None:
    projection = demo_context.projection
    assert projection.focal_person_id == demo_context.people_by_code["P001"].id
    assert projection.meta.one_hop_count == 24
    assert projection.meta.two_hop_count == 12
    assert projection.meta.visible_node_count == 37
    assert projection.meta.total_network_size == 92
    assert len({node.person_id for node in projection.nodes}) == len(projection.nodes)
    assert {node.person_id for node in projection.nodes} <= {
        person.id for person in demo_context.dataset.people
    }

    direct_nodes = [node for node in projection.nodes if node.hop == 1]
    state_counts = Counter(node.relationship_state for node in direct_nodes)
    assert {
        RelationshipState.CLOSE,
        RelationshipState.ACTIVE,
        RelationshipState.WEAK,
        RelationshipState.DORMANT,
        RelationshipState.RECONNECTED,
    } <= set(state_counts)
    assert len(projection.clusters) >= 2
    assert sum(cluster.member_count for cluster in projection.clusters) == len(projection.nodes)


def test_diversity_sampling_is_not_top_relationship_strength_only(
    demo_context: DemoProjectionContext,
) -> None:
    focal_id = demo_context.people_by_code["P001"].id
    selected_ids = {node.person_id for node in demo_context.projection.nodes if node.hop == 1}
    direct_profiles = [
        profile for profile in demo_context.profiles if profile.pair.contains(focal_id)
    ]
    selected_profiles = [
        profile
        for profile in direct_profiles
        if (
            profile.pair.person_b_id
            if profile.pair.person_a_id == focal_id
            else profile.pair.person_a_id
        )
        in selected_ids
    ]
    omitted_profiles = [profile for profile in direct_profiles if profile not in selected_profiles]

    assert min(profile.relationship_strength for profile in selected_profiles) < max(
        profile.relationship_strength for profile in omitted_profiles
    )
    assert any(profile.state is RelationshipState.WEAK for profile in selected_profiles)
    assert any(profile.state is RelationshipState.DORMANT for profile in selected_profiles)


def test_p001_hero_nodes_and_shortest_path_are_reviewable(
    demo_context: DemoProjectionContext,
) -> None:
    node_by_code = {
        demo_context.code_by_person_id[node.person_id]: node
        for node in demo_context.projection.nodes
    }
    p018 = node_by_code["P018"]
    assert p018.hop == 1
    assert p018.relationship_state is RelationshipState.DORMANT
    p018_edge = next(
        edge for edge in demo_context.projection.edges if edge.target_person_id == p018.person_id
    )
    assert p018_edge.style is GraphEdgeStyle.DASHED
    assert p018_edge.opacity is GraphEdgeOpacity.LOW

    p067 = node_by_code["P067"]
    assert p067.hop == 2
    assert p067.is_potential
    assert p067.relationship_state is None
    assert [
        tuple(demo_context.code_by_person_id[person_id] for person_id in path)
        for path in p067.shortest_paths
    ] == [("P001", "P010", "P067")]
    assert tuple(
        demo_context.code_by_person_id[person_id] for person_id in p067.mutual_connection_ids
    ) == ("P010",)


def test_potential_paths_omit_third_party_relationship_metrics(
    demo_context: DemoProjectionContext,
) -> None:
    path_edges = [
        edge
        for edge in demo_context.projection.edges
        if edge.edge_type is GraphEdgeType.POTENTIAL_PATH
    ]
    assert path_edges
    assert all(
        edge.relationship_state is None
        and edge.relationship_strength is None
        and edge.current_activation is None
        and edge.width is GraphEdgeWidth.MUTED
        and edge.opacity is GraphEdgeOpacity.MUTED
        and edge.style is GraphEdgeStyle.DOTTED
        for edge in path_edges
    )

    serialized = canonical_projection_json(demo_context.projection)
    potential_fragments = serialized.split('"edgeType":"POTENTIAL_PATH"')
    assert len(potential_fragments) > 1
    for fragment in potential_fragments[1:]:
        edge_fragment = fragment.split("}", maxsplit=1)[0]
        assert "relationshipStrength" not in edge_fragment
        assert "currentActivation" not in edge_fragment
        assert "relationshipState" not in edge_fragment
    assert "careerLevel" not in serialized
    assert "centrality" not in serialized.casefold()
    assert "networkScore" not in serialized
    assert "activity" not in serialized.casefold()


def test_projection_is_deterministic_across_equivalent_input_order(
    demo_context: DemoProjectionContext,
) -> None:
    service = NetworkProjectionService()
    reordered = service.build(
        focal_person_id=demo_context.people_by_code["P001"].id,
        people=reversed(demo_context.dataset.people),
        organization_units=reversed(demo_context.dataset.organization_units),
        relationship_profiles=reversed(demo_context.profiles),
        generated_at=demo_context.dataset.generated_at,
    )
    assert reordered == demo_context.projection
    assert canonical_projection_json(reordered) == canonical_projection_json(
        demo_context.projection
    )


def test_mutual_connections_and_shortest_paths_are_bounded_to_three(
    demo_context: DemoProjectionContext,
) -> None:
    focal = demo_context.people_by_code["P001"]
    mutuals = tuple(demo_context.people_by_code[code] for code in ("P002", "P003", "P004", "P005"))
    target = demo_context.people_by_code["P067"]
    base_profile = demo_context.profiles[0]
    profiles = tuple(
        replace(
            base_profile,
            pair=PersonPair.between(focal.id, mutual.id),
            state=RelationshipState.ACTIVE,
        )
        for mutual in mutuals
    ) + tuple(
        replace(
            base_profile,
            pair=PersonPair.between(mutual.id, target.id),
            current_activation=0.40 + index * 0.10,
            relationship_strength=0.40 + index * 0.10,
            state=RelationshipState.ACTIVE,
        )
        for index, mutual in enumerate(mutuals)
    )
    projection = NetworkProjectionService().build(
        focal_person_id=focal.id,
        people=(focal, *mutuals, target),
        organization_units=demo_context.dataset.organization_units,
        relationship_profiles=profiles,
        generated_at=demo_context.dataset.generated_at,
        one_hop_limit=4,
        teaser_limit=1,
    )
    potential = next(node for node in projection.nodes if node.hop == 2)
    assert potential.person_id == target.id
    assert len(potential.mutual_connection_ids) == 3
    assert len(potential.shortest_paths) == 3
    assert len(set(potential.mutual_connection_ids)) == 3
    assert all(path[0] == focal.id and path[-1] == target.id for path in potential.shortest_paths)


def test_projection_limits_are_server_bounded(demo_context: DemoProjectionContext) -> None:
    service = NetworkProjectionService()
    with pytest.raises(ValueError, match="one_hop_limit"):
        service.build(
            focal_person_id=demo_context.people_by_code["P001"].id,
            people=demo_context.dataset.people,
            organization_units=demo_context.dataset.organization_units,
            relationship_profiles=demo_context.profiles,
            generated_at=demo_context.dataset.generated_at,
            one_hop_limit=25,
        )
    focal_only = service.build(
        focal_person_id=demo_context.people_by_code["P001"].id,
        people=demo_context.dataset.people,
        organization_units=demo_context.dataset.organization_units,
        relationship_profiles=demo_context.profiles,
        generated_at=demo_context.dataset.generated_at,
        one_hop_limit=0,
    )
    assert focal_only.meta.visible_node_count == 1
    assert not focal_only.edges


def test_expansion_adds_at_most_eight_and_preserves_existing_projection(
    demo_context: DemoProjectionContext,
) -> None:
    service = NetworkProjectionService()
    initial = demo_context.projection
    expanded = service.expand(
        initial,
        selected_person_id=initial.focal_person_id,
        people=demo_context.dataset.people,
        organization_units=demo_context.dataset.organization_units,
        relationship_profiles=demo_context.profiles,
    )
    assert len(expanded.nodes) - len(initial.nodes) == 8
    assert expanded.nodes[: len(initial.nodes)] == initial.nodes
    assert expanded.edges[: len(initial.edges)] == initial.edges
    assert expanded.meta.expanded_from_person_ids == (initial.focal_person_id,)
    assert len(expanded.nodes) <= 80
    assert (
        service.expand(
            expanded,
            selected_person_id=initial.focal_person_id,
            people=demo_context.dataset.people,
            organization_units=demo_context.dataset.organization_units,
            relationship_profiles=demo_context.profiles,
        )
        == expanded
    )


def test_expansion_never_crosses_hard_visible_limit(
    demo_context: DemoProjectionContext,
) -> None:
    service = NetworkProjectionService(
        NetworkProjectionConfig(default_one_hop_limit=40, default_teaser_limit=39)
    )
    full = service.build(
        focal_person_id=demo_context.people_by_code["P001"].id,
        people=demo_context.dataset.people,
        organization_units=demo_context.dataset.organization_units,
        relationship_profiles=demo_context.profiles,
        generated_at=demo_context.dataset.generated_at,
    )
    assert len(full.nodes) == 80
    expanded = service.expand(
        full,
        selected_person_id=full.focal_person_id,
        people=demo_context.dataset.people,
        organization_units=demo_context.dataset.organization_units,
        relationship_profiles=demo_context.profiles,
    )
    assert len(expanded.nodes) == 80
    assert expanded.meta.soft_limit_exceeded
