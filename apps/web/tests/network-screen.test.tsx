import { fireEvent, render, screen, waitFor } from "@testing-library/react";

import { AppProviders } from "../app/providers";
import { NetworkScreen } from "../features/network/network-screen";
import {
  dormantPersonDetail,
  expandedNetworkFixture,
  networkFixture,
  potentialPersonDetail,
  potentialSearchPage,
} from "./network-fixture";

vi.mock("../features/network/graph/network-graph-canvas", () => ({
  NetworkGraphCanvas: ({
    model,
    onHoverPerson,
    onSelectPerson,
  }: {
    model: {
      graph: {
        forEachNode(
          callback: (
            personId: string,
            attributes: { displayName: string },
          ) => void,
        ): void;
        order: number;
      };
    };
    onHoverPerson(personId: string | null): void;
    onSelectPerson(personId: string): void;
  }) => {
    const nodes: Array<{ displayName: string; personId: string }> = [];
    model.graph.forEachNode((personId, attributes) => {
      nodes.push({ displayName: attributes.displayName, personId });
    });
    return (
      <div data-testid="network-graph-canvas">
        graph:{model.graph.order}
        {nodes.map(({ displayName, personId }) => (
          <button
            key={personId}
            onClick={() => onSelectPerson(personId)}
            onMouseEnter={() => onHoverPerson(personId)}
            onMouseLeave={() => onHoverPerson(null)}
            type="button"
          >
            node:{displayName}
          </button>
        ))}
      </div>
    );
  },
}));

function renderScreen() {
  return render(
    <AppProviders>
      <NetworkScreen />
    </AppProviders>,
  );
}

describe("NetworkScreen", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("shows loading and then the normal graph foundation", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(
        async () =>
          new Response(JSON.stringify(networkFixture), { status: 200 }),
      ),
    );
    renderScreen();

    expect(
      screen.getByLabelText("ネットワークを読み込み中"),
    ).toBeInTheDocument();
    expect(
      await screen.findByRole("heading", { level: 1, name: "My Network" }),
    ).toBeVisible();
    await waitFor(() =>
      expect(screen.getByTestId("network-graph-canvas")).toHaveTextContent(
        "graph:5",
      ),
    );
    expect(screen.getByRole("button", { name: "拡大" })).toBeVisible();
    expect(screen.getByText("久しぶり")).toBeVisible();

    fireEvent.click(screen.getByRole("button", { name: "1-hop" }));
    expect(screen.getByTestId("network-graph-canvas")).toHaveTextContent(
      "graph:3",
    );
  });

  it("renders a neutral empty state", async () => {
    const emptyFixture = { ...networkFixture, nodes: [] };
    vi.stubGlobal(
      "fetch",
      vi.fn(
        async () => new Response(JSON.stringify(emptyFixture), { status: 200 }),
      ),
    );
    renderScreen();

    expect(
      await screen.findByText("表示できるつながりがまだありません"),
    ).toBeVisible();
  });

  it("renders a safe retryable error without exposing response detail", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => new Response("database exploded", { status: 500 })),
    );
    renderScreen();

    expect(
      await screen.findByRole("alert", undefined, { timeout: 3_000 }),
    ).toHaveTextContent("ネットワークを表示できませんでした");
    expect(screen.queryByText("database exploded")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "再読み込み" })).toBeVisible();
  });

  it("shows hover context, opens factual dormant detail, and closes with Escape", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL) => {
        const url = String(input);
        if (url === "/api/network") {
          return new Response(JSON.stringify(networkFixture), { status: 200 });
        }
        if (url === "/api/people/person-003") {
          return new Response(JSON.stringify(dormantPersonDetail), {
            status: 200,
          });
        }
        return new Response("not found", { status: 404 });
      }),
    );
    renderScreen();

    const dormantNode = await screen.findByRole("button", {
      name: "node:Ren Ito",
    });
    fireEvent.mouseEnter(dormantNode);
    expect(
      screen.getByText("あなたのつながり").parentElement,
    ).toHaveTextContent("久しぶりのつながり");

    fireEvent.click(dormantNode);
    expect(
      await screen.findByRole("heading", { level: 2, name: "Ren Ito" }),
    ).toBeVisible();
    expect(screen.getByText("久しぶりのつながり")).toBeVisible();
    expect(
      screen.getByText("Aurora Projectで一緒に取り組みました"),
    ).toBeVisible();
    expect(screen.getByText("共通のプロジェクト")).toBeVisible();

    fireEvent.keyDown(window, { key: "Escape" });
    await waitFor(() =>
      expect(
        screen.queryByRole("heading", { level: 2, name: "Ren Ito" }),
      ).not.toBeInTheDocument(),
    );
    expect(screen.getByText("表示の見かた")).toBeVisible();
  });

  it("expands at most the server result and selects a potential person through search", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
        const url = String(input);
        if (url === "/api/network" && !init?.method) {
          return new Response(JSON.stringify(networkFixture), { status: 200 });
        }
        if (url === "/api/network/expand" && init?.method === "POST") {
          return new Response(JSON.stringify(expandedNetworkFixture), {
            status: 200,
          });
        }
        if (url === "/api/people/person-003") {
          return new Response(JSON.stringify(dormantPersonDetail), {
            status: 200,
          });
        }
        if (url.startsWith("/api/people/search?")) {
          return new Response(JSON.stringify(potentialSearchPage), {
            status: 200,
          });
        }
        if (url === "/api/people/person-004") {
          return new Response(JSON.stringify(potentialPersonDetail), {
            status: 200,
          });
        }
        return new Response("not found", { status: 404 });
      }),
    );
    renderScreen();

    fireEvent.click(
      await screen.findByRole("button", { name: "node:Ren Ito" }),
    );
    fireEvent.click(
      await screen.findByRole("button", {
        name: "この人からつながりを広げる",
      }),
    );
    await waitFor(() =>
      expect(screen.getByTestId("network-graph-canvas")).toHaveTextContent(
        "graph:6",
      ),
    );
    expect(
      screen.getByRole("button", { name: "この人から展開済み" }),
    ).toBeDisabled();

    const search = screen.getByRole("combobox", { name: "人を検索" });
    fireEvent.change(search, { target: { value: "Yui" } });
    fireEvent.click(
      await screen.findByRole("button", {
        name: /Yui Mori.*まだ直接話したことはありません/,
      }),
    );

    expect(
      await screen.findByRole("heading", { level: 2, name: "Yui Mori" }),
    ).toBeVisible();
    expect(screen.getByText("まだ直接話したことはありません")).toBeVisible();
    expect(screen.getByText("つながり方")).toBeVisible();
    expect(screen.getByText(/まだ直接話した記録はありません/)).toBeVisible();
    expect(screen.queryByText("Aurora Project")).not.toBeInTheDocument();
  });
});
