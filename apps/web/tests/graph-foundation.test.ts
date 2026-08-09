import { buildNetworkGraph } from "../features/network/graph/build-network-graph";
import { calculateDeterministicLayout } from "../features/network/graph/deterministic-layout";
import { createLargeNetworkFixture, networkFixture } from "./network-fixture";

describe("graph foundation", () => {
  it("produces deterministic, input-order-independent coordinates centered on the focal person", () => {
    const forward = calculateDeterministicLayout(
      networkFixture.nodes,
      networkFixture.edges,
      networkFixture.focalPersonId,
    );
    const reversed = calculateDeterministicLayout(
      [...networkFixture.nodes].reverse(),
      [...networkFixture.edges].reverse(),
      networkFixture.focalPersonId,
    );

    expect([...forward]).toEqual([...reversed]);
    expect(forward.get(networkFixture.focalPersonId)).toEqual({ x: 0, y: 0 });
    for (const position of forward.values()) {
      expect(Math.hypot(position.x, position.y)).toBeLessThanOrEqual(8.500_001);
    }
  });

  it("creates a person-only Graphology model and maps backend presentation semantics", () => {
    const model = buildNetworkGraph(networkFixture, "TWO_HOP");

    expect(model.graph.order).toBe(5);
    expect(model.graph.size).toBe(4);
    expect(model.graph.getNodeAttribute("person-001", "label")).toBe("あなた");
    expect(model.graph.getNodeAttribute("person-001", "size")).toBeGreaterThan(
      model.graph.getNodeAttribute("person-002", "size"),
    );
    const dormantEdge = model.graph.findEdge(
      (_edge, attributes) => attributes.relationshipState === "DORMANT",
    );
    expect(dormantEdge).toBeDefined();
    expect(model.graph.getEdgeAttribute(dormantEdge!, "style")).toBe("DASHED");
    expect(model.graph.getEdgeAttribute(dormantEdge!, "hidden")).toBe(true);
  });

  it("filters two-hop presentation without moving the remaining mental map", () => {
    const complete = buildNetworkGraph(networkFixture, "TWO_HOP");
    const oneHop = buildNetworkGraph(networkFixture, "ONE_HOP");

    expect(oneHop.graph.order).toBe(3);
    expect(oneHop.bounds).toEqual(complete.bounds);
    expect(oneHop.graph.nodes().sort()).toEqual([
      "person-001",
      "person-002",
      "person-003",
    ]);
    for (const personId of oneHop.graph.nodes()) {
      expect(oneHop.graph.getNodeAttributes(personId)).toMatchObject(
        complete.graph.getNodeAttributes(personId),
      );
    }
  });

  it("keeps same-organization people softer and closer than cross-organization pairs", () => {
    const positions = calculateDeterministicLayout(
      networkFixture.nodes,
      networkFixture.edges,
      networkFixture.focalPersonId,
    );
    const distance = (left: string, right: string) => {
      const leftPosition = positions.get(left)!;
      const rightPosition = positions.get(right)!;
      return Math.hypot(
        leftPosition.x - rightPosition.x,
        leftPosition.y - rightPosition.y,
      );
    };
    const withinCluster =
      (distance("person-002", "person-004") +
        distance("person-003", "person-005")) /
      2;
    const crossCluster =
      (distance("person-002", "person-003") +
        distance("person-002", "person-005") +
        distance("person-004", "person-003") +
        distance("person-004", "person-005")) /
      4;

    expect(withinCluster).toBeLessThan(crossCluster);
  });

  it("keeps a deterministic 60-person projection practical and preserves coordinates across hop views", () => {
    const projection = createLargeNetworkFixture();
    const startedAt = performance.now();
    const positions = calculateDeterministicLayout(
      projection.nodes,
      projection.edges,
      projection.focalPersonId,
    );
    const complete = buildNetworkGraph(projection, "TWO_HOP", positions);
    const oneHop = buildNetworkGraph(projection, "ONE_HOP", positions);
    const durationMs = performance.now() - startedAt;

    expect(complete.graph.order).toBe(60);
    expect(complete.graph.size).toBe(59);
    expect(oneHop.graph.order).toBe(25);
    expect(complete.positions).toBe(positions);
    expect(oneHop.positions).toBe(positions);
    expect(positions.get(projection.focalPersonId)).toEqual({ x: 0, y: 0 });
    expect(durationMs).toBeLessThan(1_500);
  });
});
