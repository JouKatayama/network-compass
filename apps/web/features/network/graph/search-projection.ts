import type {
  GraphProjectionSchema,
  PersonSearchResultSchema,
} from "../../../lib/api/generated";

export type SearchProjectionResult = {
  anchorPersonId: string;
  projection: GraphProjectionSchema;
};

export function addSearchResultToProjection(
  projection: GraphProjectionSchema,
  result: PersonSearchResultSchema,
): SearchProjectionResult {
  const personId = result.person.personId;
  if (projection.nodes.some((node) => node.personId === personId)) {
    return { anchorPersonId: personId, projection };
  }

  const visibleIds = new Set(projection.nodes.map((node) => node.personId));
  const anchorPersonId =
    [...result.connectionPath]
      .reverse()
      .find((pathPersonId) => visibleIds.has(pathPersonId)) ??
    projection.focalPersonId;
  if (result.connectionType === "NONE") {
    return { anchorPersonId, projection };
  }

  const organizationId = result.person.organization?.id;
  const clusterId = organizationId
    ? `organization:${organizationId}`
    : "organization:unassigned";
  const hop = result.connectionType === "DIRECT" ? 1 : 2;
  const node = {
    avatarUrl: result.person.avatarUrl,
    clusterId,
    displayName: result.person.displayName,
    hop,
    isPotential: result.connectionType === "TWO_HOP",
    mutualConnectionIds:
      result.commonContext.mutualConnections?.map(
        (person) => person.personId,
      ) ?? [],
    personId,
    relationshipState: result.relationshipState,
    relevance: 0.45,
    shortRole: result.person.role,
    shortestPaths:
      result.connectionPath.length > 0 ? [result.connectionPath] : [],
  } as const;
  const pathEdge =
    result.connectionType === "TWO_HOP" && anchorPersonId !== personId
      ? [
          {
            edgeType: "POTENTIAL_PATH" as const,
            opacity: "MUTED" as const,
            sourcePersonId: anchorPersonId,
            style: "DOTTED" as const,
            targetPersonId: personId,
            width: "MUTED" as const,
          },
        ]
      : [];
  const existingCluster = projection.clusters.find(
    (cluster) => cluster.id === clusterId,
  );
  const clusters = existingCluster
    ? projection.clusters.map((cluster) =>
        cluster.id === clusterId
          ? { ...cluster, memberCount: cluster.memberCount + 1 }
          : cluster,
      )
    : [
        ...projection.clusters,
        {
          id: clusterId,
          label: result.person.organization?.name ?? "所属未設定",
          memberCount: 1,
        },
      ];

  return {
    anchorPersonId,
    projection: {
      ...projection,
      clusters,
      edges: [...projection.edges, ...pathEdge],
      meta: {
        ...projection.meta,
        oneHopCount: projection.meta.oneHopCount + (hop === 1 ? 1 : 0),
        twoHopCount: projection.meta.twoHopCount + (hop === 2 ? 1 : 0),
        visibleNodeCount: projection.meta.visibleNodeCount + 1,
      },
      nodes: [...projection.nodes, node],
    },
  };
}
