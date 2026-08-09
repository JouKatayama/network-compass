import type {
  GraphPersonNodeSchema,
  GraphRelationshipEdgeSchema,
} from "../../../lib/api/generated";
import type { GraphPoint } from "./types";

type MutablePoint = { x: number; y: number };

const ITERATIONS = 180;
const EPSILON = 0.000_001;

function stableHash(value: string): number {
  let hash = 2166136261;
  for (let index = 0; index < value.length; index += 1) {
    hash ^= value.charCodeAt(index);
    hash = Math.imul(hash, 16777619);
  }
  return hash >>> 0;
}

function hashUnit(value: string): number {
  return stableHash(value) / 4_294_967_295;
}

function clusterCenters(
  nodes: readonly GraphPersonNodeSchema[],
  focalPersonId: string,
): Map<string, GraphPoint> {
  const clusterIds = [...new Set(nodes.map((node) => node.clusterId))].sort();
  const rotation = hashUnit(`rotation:${focalPersonId}`) * Math.PI * 2;
  return new Map(
    clusterIds.map((clusterId, index) => {
      const angle =
        rotation + (index / Math.max(1, clusterIds.length)) * Math.PI * 2;
      return [
        clusterId,
        { x: Math.cos(angle) * 3.1, y: Math.sin(angle) * 2.6 },
      ];
    }),
  );
}

function initialPosition(
  node: GraphPersonNodeSchema,
  focalPersonId: string,
  center: GraphPoint,
): MutablePoint {
  if (node.personId === focalPersonId) return { x: 0, y: 0 };

  const angle =
    hashUnit(`angle:${node.clusterId}:${node.personId}`) * Math.PI * 2;
  const radius =
    (node.hop === 2 ? 1.75 : 0.75) + hashUnit(`radius:${node.personId}`) * 1.1;
  return {
    x: center.x + Math.cos(angle) * radius,
    y: center.y + Math.sin(angle) * radius,
  };
}

function addForce(force: MutablePoint, x: number, y: number): void {
  force.x += x;
  force.y += y;
}

export function calculateDeterministicLayout(
  nodes: readonly GraphPersonNodeSchema[],
  edges: readonly GraphRelationshipEdgeSchema[],
  focalPersonId: string,
): ReadonlyMap<string, GraphPoint> {
  const orderedNodes = [...nodes].sort((left, right) =>
    left.personId.localeCompare(right.personId),
  );
  const nodeById = new Map(orderedNodes.map((node) => [node.personId, node]));
  const centers = clusterCenters(orderedNodes, focalPersonId);
  const positions = new Map<string, MutablePoint>();

  for (const node of orderedNodes) {
    const center = centers.get(node.clusterId) ?? { x: 0, y: 0 };
    positions.set(node.personId, initialPosition(node, focalPersonId, center));
  }

  const orderedEdges = [...edges]
    .filter(
      (edge) =>
        nodeById.has(edge.sourcePersonId) && nodeById.has(edge.targetPersonId),
    )
    .sort((left, right) => {
      const leftKey = `${left.sourcePersonId}:${left.targetPersonId}:${left.edgeType}`;
      const rightKey = `${right.sourcePersonId}:${right.targetPersonId}:${right.edgeType}`;
      return leftKey.localeCompare(rightKey);
    });

  for (let iteration = 0; iteration < ITERATIONS; iteration += 1) {
    const forces = new Map(
      orderedNodes.map((node) => [node.personId, { x: 0, y: 0 }]),
    );
    const cooling = 1 - iteration / ITERATIONS;

    for (let leftIndex = 0; leftIndex < orderedNodes.length; leftIndex += 1) {
      const left = orderedNodes[leftIndex];
      const leftPosition = positions.get(left.personId)!;
      for (
        let rightIndex = leftIndex + 1;
        rightIndex < orderedNodes.length;
        rightIndex += 1
      ) {
        const right = orderedNodes[rightIndex];
        const rightPosition = positions.get(right.personId)!;
        let deltaX = leftPosition.x - rightPosition.x;
        let deltaY = leftPosition.y - rightPosition.y;
        let distanceSquared = deltaX * deltaX + deltaY * deltaY;
        if (distanceSquared < EPSILON) {
          const angle =
            hashUnit(`${left.personId}:${right.personId}`) * Math.PI * 2;
          deltaX = Math.cos(angle) * 0.01;
          deltaY = Math.sin(angle) * 0.01;
          distanceSquared = deltaX * deltaX + deltaY * deltaY;
        }
        const distance = Math.sqrt(distanceSquared);
        const minimumDistance = left.hop === 2 && right.hop === 2 ? 0.42 : 0.56;
        const collision = Math.max(0, minimumDistance - distance) * 0.075;
        const repulsion = 0.018 / Math.max(distanceSquared, 0.04) + collision;
        const forceX = (deltaX / distance) * repulsion;
        const forceY = (deltaY / distance) * repulsion;
        addForce(forces.get(left.personId)!, forceX, forceY);
        addForce(forces.get(right.personId)!, -forceX, -forceY);
      }
    }

    for (const edge of orderedEdges) {
      const source = positions.get(edge.sourcePersonId)!;
      const target = positions.get(edge.targetPersonId)!;
      const deltaX = target.x - source.x;
      const deltaY = target.y - source.y;
      const distance = Math.max(
        EPSILON,
        Math.sqrt(deltaX * deltaX + deltaY * deltaY),
      );
      const idealDistance = edge.edgeType === "DIRECT" ? 1.75 : 1.25;
      const strength = edge.edgeType === "DIRECT" ? 0.012 : 0.006;
      const pull = (distance - idealDistance) * strength;
      const forceX = (deltaX / distance) * pull;
      const forceY = (deltaY / distance) * pull;
      addForce(forces.get(edge.sourcePersonId)!, forceX, forceY);
      addForce(forces.get(edge.targetPersonId)!, -forceX, -forceY);
    }

    for (const node of orderedNodes) {
      if (node.personId === focalPersonId) continue;
      const position = positions.get(node.personId)!;
      const clusterCenter = centers.get(node.clusterId) ?? { x: 0, y: 0 };
      const clusterPull = node.hop === 2 ? 0.004 : 0.007;
      const force = forces.get(node.personId)!;
      addForce(
        force,
        (clusterCenter.x - position.x) * clusterPull,
        (clusterCenter.y - position.y) * clusterPull,
      );
      addForce(force, -position.x * 0.0008, -position.y * 0.0008);
    }

    for (const node of orderedNodes) {
      const position = positions.get(node.personId)!;
      if (node.personId === focalPersonId) {
        position.x = 0;
        position.y = 0;
        continue;
      }
      const force = forces.get(node.personId)!;
      const magnitude = Math.sqrt(force.x * force.x + force.y * force.y);
      const maximumStep = 0.11 * (0.35 + cooling * 0.65);
      const scale = magnitude > maximumStep ? maximumStep / magnitude : 1;
      position.x += force.x * scale;
      position.y += force.y * scale;
    }
  }

  const maximumRadius = Math.max(
    1,
    ...[...positions.values()].map(({ x, y }) => Math.sqrt(x * x + y * y)),
  );
  const graphScale = 8.5 / maximumRadius;
  return new Map(
    orderedNodes.map((node) => {
      const position = positions.get(node.personId)!;
      return [
        node.personId,
        node.personId === focalPersonId
          ? { x: 0, y: 0 }
          : { x: position.x * graphScale, y: position.y * graphScale },
      ];
    }),
  );
}
