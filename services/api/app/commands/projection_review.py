import argparse
import json
from collections import Counter
from typing import cast
from uuid import UUID

from app.application.network_projection import PersonalNetworkProjectionQueryService
from app.application.projection_serialization import projection_to_primitive
from app.domain.entities import Person
from app.domain.projections import GraphEdgeType, GraphProjection
from app.domain.value_objects import ExternalIdentifier
from app.infrastructure.database import create_database_engine, create_session_factory
from app.infrastructure.persistence import (
    SqlAlchemyFactRepository,
    SqlAlchemyRelationshipProfileRepository,
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render a deterministic personal GraphProjection review artifact."
    )
    parser.add_argument("--source-system", default="synthetic")
    parser.add_argument("--external-id", default="P001")
    return parser.parse_args()


def _resolve_person(
    people: tuple[Person, ...],
    *,
    source_system: str,
    external_id: str,
) -> Person:
    identifier = ExternalIdentifier(source_system, external_id)
    matches = [person for person in people if identifier in person.external_identifiers]
    if len(matches) != 1:
        raise ValueError(
            f"expected exactly one person for {identifier.source_system}/{identifier.external_id}"
        )
    return matches[0]


def _external_id_by_person(
    people: tuple[Person, ...],
    *,
    source_system: str,
) -> dict[UUID, str]:
    return {
        person.id: identifier.external_id
        for person in people
        for identifier in person.external_identifiers
        if identifier.source_system == source_system.casefold()
    }


def _hero_fixture_review(
    projection: GraphProjection,
    external_id_by_person: dict[UUID, str],
) -> dict[str, object]:
    node_by_external_id = {
        external_id_by_person[node.person_id]: node
        for node in projection.nodes
        if node.person_id in external_id_by_person
    }
    p018 = node_by_external_id.get("P018")
    p067 = node_by_external_id.get("P067")
    return {
        "P018": {
            "hop": p018.hop if p018 is not None else None,
            "relationshipState": (
                p018.relationship_state.value
                if p018 is not None and p018.relationship_state is not None
                else None
            ),
            "visible": p018 is not None,
        },
        "P067": {
            "hop": p067.hop if p067 is not None else None,
            "shortestPaths": (
                [
                    [external_id_by_person.get(person_id, str(person_id)) for person_id in path]
                    for path in p067.shortest_paths
                ]
                if p067 is not None
                else []
            ),
            "visible": p067 is not None,
        },
    }


def build_review_artifact(
    fact_repository: SqlAlchemyFactRepository,
    profile_repository: SqlAlchemyRelationshipProfileRepository,
    *,
    source_system: str = "synthetic",
    external_id: str = "P001",
) -> dict[str, object]:
    people = fact_repository.list_people()
    focal_person = _resolve_person(
        people,
        source_system=source_system,
        external_id=external_id,
    )
    projection = PersonalNetworkProjectionQueryService(
        fact_repository,
        profile_repository,
    ).get_for_current_user(focal_person.id)
    primitive = projection_to_primitive(projection)
    external_ids = _external_id_by_person(people, source_system=source_system)
    visible_external_ids = {
        str(node.person_id): external_ids[node.person_id]
        for node in projection.nodes
        if node.person_id in external_ids
    }
    direct_state_counts = Counter(
        node.relationship_state.value
        for node in projection.nodes
        if node.relationship_state is not None
    )
    potential_edges = [
        edge for edge in projection.edges if edge.edge_type is GraphEdgeType.POTENTIAL_PATH
    ]
    edge_primitives = cast(list[object], primitive["edges"])
    potential_edge_primitives = [
        cast(dict[str, object], edge)
        for edge in edge_primitives
        if isinstance(edge, dict) and edge.get("edgeType") == GraphEdgeType.POTENTIAL_PATH.value
    ]
    private_metric_keys = {
        "currentActivation",
        "relationshipState",
        "relationshipStrength",
    }
    hero_fixtures = _hero_fixture_review(projection, external_ids)
    p067_review = hero_fixtures["P067"]
    p067_paths = p067_review["shortestPaths"] if isinstance(p067_review, dict) else []
    return {
        "artifactVersion": "nc006-gate-b-v1",
        "graphProjection": primitive,
        "persona": {
            "externalId": external_id,
            "personId": str(focal_person.id),
            "sourceSystem": source_system.casefold(),
        },
        "review": {
            "bounds": {
                "defaultOneHopLimit": 24,
                "defaultTeaserLimit": 12,
                "hardVisibleLimit": 80,
                "oneHopWithinLimit": projection.meta.one_hop_count <= 24,
                "teaserWithinLimit": projection.meta.two_hop_count <= 12,
                "visibleWithinHardLimit": projection.meta.visible_node_count <= 80,
            },
            "composition": {
                "clusterCounts": {
                    cluster.label: cluster.member_count for cluster in projection.clusters
                },
                "directRelationshipStateCounts": dict(sorted(direct_state_counts.items())),
                "oneHopCount": projection.meta.one_hop_count,
                "twoHopCount": projection.meta.two_hop_count,
                "visibleNodeCount": projection.meta.visible_node_count,
            },
            "heroFixtures": hero_fixtures,
            "heroPathAvailable": ["P001", "P010", "P067"] in p067_paths,
            "privacy": {
                "focalRelativeMetricsOnlyOnDirectEdges": all(
                    not private_metric_keys.intersection(edge) for edge in potential_edge_primitives
                ),
                "potentialPathEdgeCount": len(potential_edges),
                "thirdPartyPathMetricsOmitted": all(
                    edge.relationship_state is None
                    and edge.relationship_strength is None
                    and edge.current_activation is None
                    for edge in potential_edges
                ),
            },
            "visibleExternalIdsByPersonId": visible_external_ids,
        },
    }


def review_artifact_json(artifact: dict[str, object]) -> str:
    return json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def render_review_artifact(*, source_system: str, external_id: str) -> str:
    engine = create_database_engine()
    session_factory = create_session_factory(engine)
    try:
        with session_factory() as session:
            artifact = build_review_artifact(
                SqlAlchemyFactRepository(session),
                SqlAlchemyRelationshipProfileRepository(session),
                source_system=source_system,
                external_id=external_id,
            )
        return review_artifact_json(artifact)
    finally:
        engine.dispose()


def main() -> None:
    args = _parse_args()
    print(
        render_review_artifact(
            source_system=args.source_system,
            external_id=args.external_id,
        ),
        end="",
    )


if __name__ == "__main__":
    main()
