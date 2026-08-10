import type {
  GraphProjectionSchema,
  PersonDetailSchema,
  PersonSearchPageSchema,
} from "../lib/api/generated";

export const networkFixture: GraphProjectionSchema = {
  clusters: [
    { id: "organization:alpha", label: "Alpha", memberCount: 3 },
    { id: "organization:beta", label: "Beta", memberCount: 2 },
  ],
  edges: [
    {
      currentActivation: 0.9,
      edgeType: "DIRECT",
      opacity: "HIGH",
      relationshipState: "CLOSE",
      relationshipStrength: 0.82,
      sourcePersonId: "person-001",
      style: "SOLID",
      targetPersonId: "person-002",
      width: "THICK",
    },
    {
      currentActivation: 0.2,
      edgeType: "DIRECT",
      opacity: "LOW",
      relationshipState: "DORMANT",
      relationshipStrength: 0.4,
      sourcePersonId: "person-001",
      style: "DASHED",
      targetPersonId: "person-003",
      width: "THIN",
    },
    {
      edgeType: "POTENTIAL_PATH",
      opacity: "MUTED",
      sourcePersonId: "person-002",
      style: "DOTTED",
      targetPersonId: "person-004",
      width: "MUTED",
    },
    {
      edgeType: "POTENTIAL_PATH",
      opacity: "MUTED",
      sourcePersonId: "person-003",
      style: "DOTTED",
      targetPersonId: "person-005",
      width: "MUTED",
    },
  ],
  focalPersonId: "person-001",
  meta: {
    generatedAt: "2026-08-09T00:00:00Z",
    hops: 2,
    lens: "DEFAULT",
    oneHopCount: 2,
    projectionVersion: "graph-projection-v0.1.0",
    totalNetworkSize: 42,
    twoHopCount: 2,
    visibleNodeCount: 5,
  },
  nodes: [
    {
      avatarUrl: null,
      clusterId: "organization:alpha",
      displayName: "Mina Nakamura",
      hop: 0,
      isPotential: false,
      personId: "person-001",
      relevance: 1,
      relationshipState: null,
      shortRole: "Product Lead",
    },
    {
      avatarUrl: null,
      clusterId: "organization:alpha",
      displayName: "Aoi Sato",
      hop: 1,
      isPotential: false,
      personId: "person-002",
      relevance: 0.88,
      relationshipState: "CLOSE",
      shortRole: "Designer",
    },
    {
      avatarUrl: null,
      clusterId: "organization:beta",
      displayName: "Ren Ito",
      hop: 1,
      isPotential: false,
      personId: "person-003",
      relevance: 0.48,
      relationshipState: "DORMANT",
      shortRole: "Engineer",
    },
    {
      avatarUrl: null,
      clusterId: "organization:alpha",
      displayName: "Yui Mori",
      hop: 2,
      isPotential: true,
      personId: "person-004",
      relevance: 0.3,
      relationshipState: null,
      shortRole: "Researcher",
    },
    {
      avatarUrl: null,
      clusterId: "organization:beta",
      displayName: "Kai Abe",
      hop: 2,
      isPotential: true,
      personId: "person-005",
      relevance: 0.25,
      relationshipState: null,
      shortRole: null,
    },
  ],
};

export const expandedNetworkFixture: GraphProjectionSchema = {
  ...networkFixture,
  edges: [
    ...networkFixture.edges,
    {
      edgeType: "POTENTIAL_PATH",
      opacity: "MUTED",
      sourcePersonId: "person-003",
      style: "DOTTED",
      targetPersonId: "person-006",
      width: "MUTED",
    },
  ],
  meta: {
    ...networkFixture.meta,
    expandedFromPersonIds: ["person-003"],
    twoHopCount: 3,
    visibleNodeCount: 6,
  },
  nodes: [
    ...networkFixture.nodes,
    {
      avatarUrl: null,
      clusterId: "organization:beta",
      displayName: "Sora Kato",
      hop: 2,
      isPotential: true,
      personId: "person-006",
      relevance: 0.22,
      relationshipState: null,
      shortRole: "Analyst",
    },
  ],
};

export const dormantPersonDetail: PersonDetailSchema = {
  commonContext: {
    activities: [],
    communities: [],
    mutualConnections: [],
    projects: [{ id: "project-001", name: "Aurora Project" }],
    skills: [],
  },
  connectionPaths: [],
  person: {
    avatarUrl: null,
    displayName: "Ren Ito",
    location: "Tokyo",
    organization: { id: "beta", name: "Beta" },
    personId: "person-003",
    role: "Engineer",
  },
  relationship: {
    connectionType: "DIRECT",
    historyNote: "以前のプロジェクトで一緒に取り組みました。",
    knownDurationDays: 900,
    knownSince: "2024-02-01T00:00:00Z",
    label: "久しぶりのつながり",
    lastContactAt: "2025-01-12T00:00:00Z",
    state: "DORMANT",
  },
  timeline: [
    {
      context: { id: "project-001", name: "Aurora Project" },
      endedAt: "2024-08-01T00:00:00Z",
      itemType: "SHARED_PROJECT",
      occurredAt: "2024-02-01T00:00:00Z",
      title: "Aurora Projectで一緒に取り組みました",
    },
  ],
};

export const potentialPersonDetail: PersonDetailSchema = {
  commonContext: {
    activities: [],
    communities: [],
    mutualConnections: [
      {
        avatarUrl: null,
        displayName: "Aoi Sato",
        location: null,
        organization: { id: "alpha", name: "Alpha" },
        personId: "person-002",
        role: "Designer",
      },
    ],
    projects: [],
    skills: [],
  },
  connectionPaths: [["person-001", "person-002", "person-004"]],
  person: {
    avatarUrl: null,
    displayName: "Yui Mori",
    location: "Osaka",
    organization: { id: "alpha", name: "Alpha" },
    personId: "person-004",
    role: "Researcher",
  },
  relationship: {
    connectionType: "TWO_HOP",
    historyNote: null,
    knownDurationDays: null,
    knownSince: null,
    label: "まだ直接話したことはありません",
    lastContactAt: null,
    state: null,
  },
  timeline: [],
};

export const capturedDormantPersonDetail: PersonDetailSchema = {
  ...dormantPersonDetail,
  relationship: {
    ...dormantPersonDetail.relationship,
    historyNote: "最近、あらためて接点がありました。",
    label: "再びつながった関係",
    lastContactAt: "2026-08-10T00:00:00Z",
    state: "RECONNECTED",
  },
  timeline: [
    {
      context: null,
      endedAt: null,
      itemType: "INTERACTION",
      occurredAt: "2026-08-10T00:00:00Z",
      title: "コーヒーを飲みながら話しました",
    },
    ...dormantPersonDetail.timeline,
  ],
};

export const capturedNetworkFixture: GraphProjectionSchema = {
  ...networkFixture,
  edges: networkFixture.edges.map((edge) =>
    edge.targetPersonId === "person-003"
      ? {
          ...edge,
          currentActivation: 0.91,
          opacity: "HIGH",
          relationshipState: "RECONNECTED",
          style: "SOLID",
          width: "THICK",
        }
      : edge,
  ),
  meta: {
    ...networkFixture.meta,
    generatedAt: "2026-08-10T00:00:01Z",
  },
  nodes: networkFixture.nodes.map((node) =>
    node.personId === "person-003"
      ? { ...node, relationshipState: "RECONNECTED" }
      : node,
  ),
};

export const potentialSearchPage: PersonSearchPageSchema = {
  items: [
    {
      commonContext: potentialPersonDetail.commonContext,
      connectionPath: potentialPersonDetail.connectionPaths[0],
      connectionType: "TWO_HOP",
      person: potentialPersonDetail.person,
      relationshipLabel: potentialPersonDetail.relationship.label,
      relationshipState: null,
    },
  ],
  nextCursor: null,
};

export const emptyNetworkFixture: GraphProjectionSchema = {
  clusters: [{ id: "organization:alpha", label: "Alpha", memberCount: 1 }],
  edges: [],
  focalPersonId: networkFixture.focalPersonId,
  meta: {
    ...networkFixture.meta,
    oneHopCount: 0,
    totalNetworkSize: 1,
    twoHopCount: 0,
    visibleNodeCount: 1,
  },
  nodes: [networkFixture.nodes[0]],
};

export function createLargeNetworkFixture(
  nodeCount = 60,
): GraphProjectionSchema {
  if (nodeCount < 25 || nodeCount > 80) {
    throw new Error("large network fixture must contain 25 to 80 nodes");
  }
  const personId = (index: number) =>
    `large-person-${index.toString().padStart(3, "0")}`;
  const nodes: GraphProjectionSchema["nodes"] = Array.from(
    { length: nodeCount },
    (_, index) => {
      const hop = index === 0 ? 0 : index <= 24 ? 1 : 2;
      return {
        avatarUrl: null,
        clusterId: `organization:${index % 4}`,
        displayName:
          index === 59
            ? "Very Long Synthetic Person Name For Responsive Validation P060"
            : `Synthetic Large Person P${(index + 1).toString().padStart(3, "0")}`,
        hop,
        isPotential: hop === 2,
        personId: personId(index),
        relevance: Math.max(0.1, 1 - index / 80),
        relationshipState:
          hop === 1 ? (index % 5 === 0 ? "DORMANT" : "ACTIVE") : null,
        shortRole: index % 11 === 0 && index > 0 ? null : "Synthetic role",
      };
    },
  );
  const edges: GraphProjectionSchema["edges"] = nodes
    .slice(1)
    .map((node, offset) => {
      const index = offset + 1;
      if (index <= 24) {
        const dormant = index % 5 === 0;
        return {
          currentActivation: dormant ? 0.2 : 0.75,
          edgeType: "DIRECT" as const,
          opacity: dormant ? ("LOW" as const) : ("HIGH" as const),
          relationshipState: dormant
            ? ("DORMANT" as const)
            : ("ACTIVE" as const),
          relationshipStrength: dormant ? 0.4 : 0.72,
          sourcePersonId: personId(0),
          style: dormant ? ("DASHED" as const) : ("SOLID" as const),
          targetPersonId: node.personId,
          width: dormant ? ("THIN" as const) : ("MEDIUM" as const),
        };
      }
      return {
        edgeType: "POTENTIAL_PATH" as const,
        opacity: "MUTED" as const,
        sourcePersonId: personId(((index - 25) % 24) + 1),
        style: "DOTTED" as const,
        targetPersonId: node.personId,
        width: "MUTED" as const,
      };
    });

  return {
    clusters: Array.from({ length: 4 }, (_, index) => ({
      id: `organization:${index}`,
      label: `Organization ${index + 1}`,
      memberCount: nodes.filter(
        (node) => node.clusterId === `organization:${index}`,
      ).length,
    })),
    edges,
    focalPersonId: personId(0),
    meta: {
      expandedFromPersonIds: [personId(1), personId(2), personId(3)],
      generatedAt: "2026-08-09T00:00:00Z",
      hops: 2,
      lens: "DEFAULT",
      oneHopCount: 24,
      projectionVersion: "graph-projection-v0.1.0",
      totalNetworkSize: 92,
      twoHopCount: nodeCount - 25,
      visibleNodeCount: nodeCount,
    },
    nodes,
  };
}
