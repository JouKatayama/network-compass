import Graph from "graphology";

import type { GraphProjectionSchema } from "../../../lib/api/generated";
import { calculateDeterministicLayout } from "./deterministic-layout";
import {
  FOCAL_NODE_COLOR,
  POTENTIAL_NODE_COLOR,
  clusterColor,
  edgeWidth,
  nodeSize,
  withAlpha,
} from "./semantic-values";
import type {
  NetworkEdgeAttributes,
  NetworkGraph,
  NetworkGraphAttributes,
  NetworkGraphModel,
  NetworkNodeAttributes,
  VisibleHopMode,
} from "./types";

function selectLabelNodeIds(
  projection: GraphProjectionSchema,
  positions: ReadonlyMap<string, { x: number; y: number }>,
): Set<string> {
  const selected = new Set([projection.focalPersonId]);
  const selectedPositions = [
    positions.get(projection.focalPersonId) ?? { x: 0, y: 0 },
  ];
  const addCandidates = (
    candidates: typeof projection.nodes,
    limit: number,
    minimumDistance: number,
  ) => {
    let added = 0;
    for (const node of candidates) {
      if (added >= limit) break;
      const position = positions.get(node.personId);
      if (!position) continue;
      const hasRoom = selectedPositions.every(
        (labelPosition) =>
          Math.hypot(
            position.x - labelPosition.x,
            position.y - labelPosition.y,
          ) >= minimumDistance,
      );
      if (!hasRoom) continue;
      selected.add(node.personId);
      selectedPositions.push(position);
      added += 1;
    }
  };
  const direct = projection.nodes
    .filter((node) => node.hop === 1)
    .sort((left, right) => {
      const statePriority = (state: string | null | undefined) =>
        state === "DORMANT" ? 0 : state === "RECONNECTED" ? 1 : 2;
      return (
        statePriority(left.relationshipState) -
          statePriority(right.relationshipState) ||
        right.relevance - left.relevance ||
        left.personId.localeCompare(right.personId)
      );
    });
  const potential = projection.nodes
    .filter((node) => node.hop === 2)
    .sort(
      (left, right) =>
        right.relevance - left.relevance ||
        left.personId.localeCompare(right.personId),
    );
  addCandidates(direct, 7, 1.45);
  addCandidates(potential, 2, 1.7);
  return selected;
}

export function buildNetworkGraph(
  projection: GraphProjectionSchema,
  hopMode: VisibleHopMode,
): NetworkGraphModel {
  const positions = calculateDeterministicLayout(
    projection.nodes,
    projection.edges,
    projection.focalPersonId,
  );
  const visibleNodes = projection.nodes.filter(
    (node) => hopMode === "TWO_HOP" || node.hop <= 1,
  );
  const visibleNodeIds = new Set(visibleNodes.map((node) => node.personId));
  const labelNodeIds = selectLabelNodeIds(projection, positions);
  const graph = new Graph<
    NetworkNodeAttributes,
    NetworkEdgeAttributes,
    NetworkGraphAttributes
  >({ multi: true, type: "undirected" }) as NetworkGraph;
  graph.setAttribute("focalPersonId", projection.focalPersonId);

  for (const node of visibleNodes) {
    const isFocal = node.personId === projection.focalPersonId;
    const position = positions.get(node.personId) ?? { x: 0, y: 0 };
    graph.addNode(node.personId, {
      clusterId: node.clusterId,
      color: isFocal
        ? FOCAL_NODE_COLOR
        : node.isPotential
          ? POTENTIAL_NODE_COLOR
          : clusterColor(node.clusterId),
      displayName: node.displayName,
      forceLabel: isFocal,
      hidden: false,
      hop: node.hop,
      isFocal,
      isPotential: node.isPotential,
      label: isFocal
        ? "あなた"
        : labelNodeIds.has(node.personId)
          ? node.displayName
          : "",
      relevance: node.relevance,
      relationshipState: node.relationshipState ?? null,
      shortRole: node.shortRole,
      size: nodeSize(node.relevance, isFocal, node.isPotential),
      type: "circle",
      x: position.x,
      y: position.y,
      zIndex: isFocal ? 3 : node.hop === 1 ? 2 : 1,
    });
  }

  projection.edges.forEach((edge, index) => {
    if (
      !visibleNodeIds.has(edge.sourcePersonId) ||
      !visibleNodeIds.has(edge.targetPersonId)
    ) {
      return;
    }
    const potential = edge.edgeType === "POTENTIAL_PATH";
    graph.addUndirectedEdgeWithKey(
      `${edge.edgeType}:${edge.sourcePersonId}:${edge.targetPersonId}:${index}`,
      edge.sourcePersonId,
      edge.targetPersonId,
      {
        color: potential
          ? withAlpha("#91a0b9", 0.72)
          : withAlpha("#9fb1ce", 0.92),
        edgeType: edge.edgeType,
        hidden: true,
        opacity: edge.opacity,
        relationshipState: edge.relationshipState ?? null,
        size: edgeWidth(edge.width),
        style: edge.style,
        type: "line",
        width: edge.width,
        zIndex: potential ? 0 : 1,
      },
    );
  });

  const allPositions = [...positions.values()];
  const xValues = allPositions.map((position) => position.x);
  const yValues = allPositions.map((position) => position.y);

  return {
    bounds: {
      x: [Math.min(...xValues, -1) - 0.5, Math.max(...xValues, 1) + 0.5],
      y: [Math.min(...yValues, -1) - 0.5, Math.max(...yValues, 1) + 0.5],
    },
    clusterLabels: new Map(
      projection.clusters.map((cluster) => [cluster.id, cluster.label]),
    ),
    graph,
    positions,
  };
}
