import json
from datetime import UTC, datetime
from uuid import UUID

from app.domain.projections import GraphEdgeType, GraphPersonNode, GraphProjection


def _uuid(value: UUID) -> str:
    return str(value)


def _timestamp(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _node_primitive(node: GraphPersonNode) -> dict[str, object]:
    result: dict[str, object] = {
        "avatarUrl": node.avatar_url,
        "clusterId": node.cluster_id,
        "displayName": node.display_name,
        "hop": node.hop,
        "isPotential": node.is_potential,
        "personId": _uuid(node.person_id),
        "relevance": node.relevance,
        "shortRole": node.short_role,
    }
    if node.relationship_state is not None:
        result["relationshipState"] = node.relationship_state.value
    if node.hop == 2:
        result["mutualConnectionIds"] = [
            _uuid(person_id) for person_id in node.mutual_connection_ids
        ]
        result["shortestPaths"] = [
            [_uuid(person_id) for person_id in path] for path in node.shortest_paths
        ]
    return result


def projection_to_primitive(projection: GraphProjection) -> dict[str, object]:
    edges: list[dict[str, object]] = []
    for edge in projection.edges:
        item: dict[str, object] = {
            "edgeType": edge.edge_type.value,
            "opacity": edge.opacity.value,
            "sourcePersonId": _uuid(edge.source_person_id),
            "style": edge.style.value,
            "targetPersonId": _uuid(edge.target_person_id),
            "width": edge.width.value,
        }
        if edge.edge_type is GraphEdgeType.DIRECT:
            if (
                edge.relationship_state is None
                or edge.relationship_strength is None
                or edge.current_activation is None
            ):
                raise ValueError("direct edge metrics are required before serialization")
            item.update(
                {
                    "currentActivation": edge.current_activation,
                    "relationshipState": edge.relationship_state.value,
                    "relationshipStrength": edge.relationship_strength,
                }
            )
        edges.append(item)

    return {
        "clusters": [
            {
                "id": cluster.id,
                "label": cluster.label,
                "memberCount": cluster.member_count,
            }
            for cluster in projection.clusters
        ],
        "edges": edges,
        "focalPersonId": _uuid(projection.focal_person_id),
        "meta": {
            "expandedFromPersonIds": [
                _uuid(person_id) for person_id in projection.meta.expanded_from_person_ids
            ],
            "generatedAt": _timestamp(projection.meta.generated_at),
            "hops": projection.meta.hops,
            "lens": projection.meta.lens,
            "oneHopCount": projection.meta.one_hop_count,
            "projectionVersion": projection.meta.projection_version,
            "softLimitExceeded": projection.meta.soft_limit_exceeded,
            "totalNetworkSize": projection.meta.total_network_size,
            "twoHopCount": projection.meta.two_hop_count,
            "visibleNodeCount": projection.meta.visible_node_count,
        },
        "nodes": [_node_primitive(node) for node in projection.nodes],
    }


def canonical_projection_json(projection: GraphProjection, *, pretty: bool = False) -> str:
    primitive = projection_to_primitive(projection)
    if pretty:
        return json.dumps(primitive, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    return json.dumps(primitive, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n"
