import { calculateDeterministicLayout } from "../features/network/graph/deterministic-layout";
import { calculateExpandedLayout } from "../features/network/graph/expanded-layout";
import { addSearchResultToProjection } from "../features/network/graph/search-projection";
import {
  expandedNetworkFixture,
  networkFixture,
  potentialSearchPage,
} from "./network-fixture";

describe("graph interaction transforms", () => {
  it("places only new expansion nodes while preserving every existing coordinate exactly", () => {
    const initial = calculateDeterministicLayout(
      networkFixture.nodes,
      networkFixture.edges,
      networkFixture.focalPersonId,
    );
    const expanded = calculateExpandedLayout(
      initial,
      expandedNetworkFixture.nodes,
      expandedNetworkFixture.edges,
      "person-003",
    );
    const repeated = calculateExpandedLayout(
      initial,
      expandedNetworkFixture.nodes,
      expandedNetworkFixture.edges,
      "person-003",
    );

    for (const [personId, position] of initial) {
      expect(expanded.get(personId)).toEqual(position);
    }
    expect(expanded.get("person-006")).toEqual(repeated.get("person-006"));
    expect(expanded.get("person-006")).toBeDefined();
    expect(
      Math.hypot(
        expanded.get("person-006")!.x - expanded.get("person-003")!.x,
        expanded.get("person-006")!.y - expanded.get("person-003")!.y,
      ),
    ).toBeLessThan(2.5);
  });

  it("adds only a search-authorized minimal potential path when a result is not visible", () => {
    const result = {
      ...potentialSearchPage.items[0],
      connectionPath: ["person-001", "person-002", "person-099"],
      person: {
        ...potentialSearchPage.items[0].person,
        displayName: "Nao Fujita",
        personId: "person-099",
      },
    };
    const added = addSearchResultToProjection(networkFixture, result);

    expect(added.anchorPersonId).toBe("person-002");
    expect(added.projection.nodes).toHaveLength(
      networkFixture.nodes.length + 1,
    );
    expect(added.projection.nodes.at(-1)).toMatchObject({
      hop: 2,
      isPotential: true,
      personId: "person-099",
    });
    expect(added.projection.edges.at(-1)).toMatchObject({
      edgeType: "POTENTIAL_PATH",
      sourcePersonId: "person-002",
      targetPersonId: "person-099",
    });
    expect(added.projection.edges.at(-1)).not.toHaveProperty(
      "relationshipStrength",
    );
  });

  it("does not imply a graph relationship for an unconnected search result", () => {
    const result = {
      ...potentialSearchPage.items[0],
      connectionPath: [],
      connectionType: "NONE" as const,
      person: {
        ...potentialSearchPage.items[0].person,
        personId: "person-099",
      },
    };
    const unchanged = addSearchResultToProjection(networkFixture, result);

    expect(unchanged.projection).toBe(networkFixture);
  });
});
