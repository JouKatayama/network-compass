import type {
  GraphPersonNodeSchema,
  GraphRelationshipEdgeSchema,
} from "../../../lib/api/generated";
import type { GraphPoint } from "./types";

type MutablePoint = { x: number; y: number };

function stableUnit(value: string): number {
  let hash = 2166136261;
  for (let index = 0; index < value.length; index += 1) {
    hash ^= value.charCodeAt(index);
    hash = Math.imul(hash, 16777619);
  }
  return (hash >>> 0) / 4_294_967_295;
}

export function calculateExpandedLayout(
  previous: ReadonlyMap<string, GraphPoint>,
  nodes: readonly GraphPersonNodeSchema[],
  edges: readonly GraphRelationshipEdgeSchema[],
  selectedPersonId: string,
): ReadonlyMap<string, GraphPoint> {
  const positions = new Map<string, MutablePoint>(
    [...previous].map(([personId, point]) => [personId, { ...point }]),
  );
  const selectedPosition = previous.get(selectedPersonId) ?? { x: 0, y: 0 };
  const newNodes = nodes
    .filter((node) => !positions.has(node.personId))
    .sort((left, right) => left.personId.localeCompare(right.personId));
  const newIds = new Set(newNodes.map((node) => node.personId));

  for (const [index, node] of newNodes.entries()) {
    const angle =
      stableUnit(`${selectedPersonId}:${node.personId}`) * Math.PI * 2;
    const radius = 1.05 + index * 0.16;
    positions.set(node.personId, {
      x: selectedPosition.x + Math.cos(angle) * radius,
      y: selectedPosition.y + Math.sin(angle) * radius,
    });
  }

  const anchorsByPerson = new Map<string, GraphPoint[]>();
  for (const edge of edges) {
    const sourceNew = newIds.has(edge.sourcePersonId);
    const targetNew = newIds.has(edge.targetPersonId);
    if (sourceNew === targetNew) continue;
    const newId = sourceNew ? edge.sourcePersonId : edge.targetPersonId;
    const anchorId = sourceNew ? edge.targetPersonId : edge.sourcePersonId;
    const anchor = previous.get(anchorId);
    if (!anchor) continue;
    const anchors = anchorsByPerson.get(newId) ?? [];
    anchors.push(anchor);
    anchorsByPerson.set(newId, anchors);
  }

  for (let iteration = 0; iteration < 56; iteration += 1) {
    for (const node of newNodes) {
      const position = positions.get(node.personId)!;
      const anchors = anchorsByPerson.get(node.personId) ?? [selectedPosition];
      const center = anchors.reduce<MutablePoint>(
        (sum, anchor) => ({ x: sum.x + anchor.x, y: sum.y + anchor.y }),
        { x: 0, y: 0 },
      );
      center.x /= anchors.length;
      center.y /= anchors.length;
      position.x += (center.x - position.x) * 0.018;
      position.y += (center.y - position.y) * 0.018;

      for (const [otherId, other] of positions) {
        if (otherId === node.personId) continue;
        let deltaX = position.x - other.x;
        let deltaY = position.y - other.y;
        const distance = Math.max(0.05, Math.hypot(deltaX, deltaY));
        if (distance >= 0.72) continue;
        if (distance < 0.06) {
          const angle = stableUnit(`${node.personId}:${otherId}`) * Math.PI * 2;
          deltaX = Math.cos(angle) * 0.06;
          deltaY = Math.sin(angle) * 0.06;
        }
        const push = (0.72 - distance) * 0.055;
        position.x += (deltaX / distance) * push;
        position.y += (deltaY / distance) * push;
      }
    }
  }

  return new Map(
    nodes.map((node) => [node.personId, positions.get(node.personId)!]),
  );
}
