import { fireEvent, render, screen, waitFor } from "@testing-library/react";

import { AppProviders } from "../app/providers";
import { NetworkScreen } from "../features/network/network-screen";
import {
  capturedDormantPersonDetail,
  capturedNetworkFixture,
  createLargeNetworkFixture,
  dormantPersonDetail,
  emptyNetworkFixture,
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
    vi.stubGlobal(
      "fetch",
      vi.fn(
        async () =>
          new Response(JSON.stringify(emptyNetworkFixture), { status: 200 }),
      ),
    );
    renderScreen();

    expect(
      await screen.findByText("あなたのNetworkはここから始まります"),
    ).toBeVisible();
  });

  it("communicates partial evidence and a practical 60-person view without calling it weak", async () => {
    const largeNetwork = createLargeNetworkFixture();
    vi.stubGlobal(
      "fetch",
      vi.fn(
        async () => new Response(JSON.stringify(largeNetwork), { status: 200 }),
      ),
    );
    renderScreen();

    expect(
      await screen.findByText(/一部のプロフィール情報は限定的です/),
    ).toBeVisible();
    expect(
      screen.getByText(/60人を表示しています/, {
        selector: ".large-network-notice",
      }),
    ).toBeVisible();
    expect(screen.queryByText(/弱い関係/)).not.toBeInTheDocument();
    expect(screen.getByTestId("network-graph-canvas")).toHaveTextContent(
      "graph:60",
    );

    fireEvent.click(screen.getByRole("button", { name: "1-hop" }));
    expect(screen.getByTestId("network-graph-canvas")).toHaveTextContent(
      "graph:25",
    );
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

    dormantNode.focus();
    fireEvent.click(dormantNode);
    expect(await screen.findByRole("dialog")).toHaveFocus();
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
    expect(dormantNode).toHaveFocus();
    expect(screen.getByText("表示の見かた")).toBeVisible();
  });

  it("validates and cancels analog capture inside Person Detail without writing", async () => {
    const fetchMock = vi.fn(
      async (input: RequestInfo | URL, _init?: RequestInit) => {
        void _init;
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
      },
    );
    vi.stubGlobal("fetch", fetchMock);
    renderScreen();

    fireEvent.click(
      await screen.findByRole("button", { name: "node:Ren Ito" }),
    );
    const captureButton = await screen.findByRole("button", {
      name: /接点を記録/,
    });
    fireEvent.click(captureButton);

    expect(
      screen.getByRole("heading", { level: 2, name: "接点を記録" }),
    ).toHaveFocus();
    expect(screen.getByText("Ren Ito")).toBeVisible();
    expect(screen.getByRole("radio", { name: "コーヒー" })).not.toBeChecked();
    expect(screen.getByRole("radio", { name: "しっかり" })).not.toBeChecked();

    fireEvent.click(screen.getByRole("button", { name: "この接点を保存" }));
    expect(screen.getByText("接点の種類を選んでください。")).toBeVisible();
    expect(screen.getByText("時間の長さを選んでください。")).toBeVisible();
    expect(
      fetchMock.mock.calls.some(([, init]) => init?.method === "POST"),
    ).toBe(false);

    fireEvent.keyDown(window, { key: "Escape" });
    await waitFor(() =>
      expect(screen.getByRole("button", { name: /接点を記録/ })).toHaveFocus(),
    );
    expect(
      screen.getByRole("heading", { level: 2, name: "Ren Ito" }),
    ).toBeVisible();
  });

  it("retains the factual capture and request identity across a safe retry, then refreshes detail and network", async () => {
    const captureBodies: Array<Record<string, unknown>> = [];
    let releaseFirstCapture: (() => void) | undefined;
    const firstCaptureGate = new Promise<void>((resolve) => {
      releaseFirstCapture = resolve;
    });
    let detailRequests = 0;
    let networkRequests = 0;
    let captureRequests = 0;
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
        const url = String(input);
        if (url === "/api/network") {
          networkRequests += 1;
          return new Response(
            JSON.stringify(
              networkRequests === 1 ? networkFixture : capturedNetworkFixture,
            ),
            { status: 200 },
          );
        }
        if (url === "/api/people/person-003") {
          detailRequests += 1;
          return new Response(
            JSON.stringify(
              detailRequests === 1
                ? dormantPersonDetail
                : capturedDormantPersonDetail,
            ),
            { status: 200 },
          );
        }
        if (url === "/api/interactions" && init?.method === "POST") {
          captureRequests += 1;
          captureBodies.push(JSON.parse(String(init.body)));
          if (captureRequests === 1) {
            await firstCaptureGate;
            return new Response("private database detail", { status: 502 });
          }
          return new Response(
            JSON.stringify({
              durationBucket: "MEDIUM",
              interactionId: "interaction-001",
              occurredAt: captureBodies[0].occurredAt,
              otherPersonId: "person-003",
              replayed: true,
              type: "COFFEE",
            }),
            { status: 200 },
          );
        }
        return new Response("not found", { status: 404 });
      }),
    );
    renderScreen();

    fireEvent.click(
      await screen.findByRole("button", { name: "node:Ren Ito" }),
    );
    fireEvent.click(await screen.findByRole("button", { name: /接点を記録/ }));
    fireEvent.click(screen.getByRole("radio", { name: "コーヒー" }));
    fireEvent.click(screen.getByRole("radio", { name: "しっかり" }));
    fireEvent.click(screen.getByRole("button", { name: "この接点を保存" }));

    await waitFor(() =>
      expect(
        screen.getByRole("button", { name: "保存しています…" }),
      ).toBeDisabled(),
    );
    releaseFirstCapture?.();

    const safeError = await screen.findByRole("alert");
    expect(safeError).toHaveTextContent("保存できませんでした");
    expect(safeError).not.toHaveTextContent("private database detail");
    expect(screen.getByRole("radio", { name: "コーヒー" })).toBeChecked();
    expect(screen.getByRole("radio", { name: "しっかり" })).toBeChecked();

    fireEvent.click(screen.getByRole("button", { name: "この接点を保存" }));
    expect(await screen.findByText("再びつながった関係")).toBeVisible();
    expect(screen.getByText("コーヒーを飲みながら話しました")).toBeVisible();
    expect(
      screen.getByRole("heading", { level: 2, name: "Ren Ito" }),
    ).toBeVisible();
    expect(screen.getByTestId("network-graph-canvas")).toHaveTextContent(
      "graph:5",
    );

    expect(captureBodies).toHaveLength(2);
    expect(captureBodies[1]).toEqual(captureBodies[0]);
    expect(captureBodies[0]).toMatchObject({
      durationBucket: "MEDIUM",
      otherPersonId: "person-003",
      type: "COFFEE",
    });
    expect(captureBodies[0]).not.toHaveProperty("confidence");
    expect(captureBodies[0]).not.toHaveProperty("relationshipState");
    expect(captureBodies[0]).not.toHaveProperty("currentPersonId");
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
    const result = await screen.findByRole("option", {
      name: /Yui Mori.*まだ直接話したことはありません/,
    });
    fireEvent.click(result);

    expect(
      await screen.findByRole("heading", { level: 2, name: "Yui Mori" }),
    ).toBeVisible();
    expect(screen.getByText("まだ直接話したことはありません")).toBeVisible();
    expect(screen.getByText("つながり方")).toBeVisible();
    expect(screen.getByText(/まだ直接話した記録はありません/)).toBeVisible();
    expect(screen.queryByText("Aurora Project")).not.toBeInTheDocument();
  });

  it("selects the first search result with ArrowDown and Enter, then restores search focus", async () => {
    const longDisplayName =
      "Yui Mori — Cross-functional Research and Partnership Practice Lead";
    const longDetail = {
      ...potentialPersonDetail,
      person: { ...potentialPersonDetail.person, displayName: longDisplayName },
    };
    const longSearchPage = {
      ...potentialSearchPage,
      items: [
        {
          ...potentialSearchPage.items[0],
          person: {
            ...potentialSearchPage.items[0].person,
            displayName: longDisplayName,
          },
        },
      ],
    };
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL) => {
        const url = String(input);
        if (url === "/api/network") {
          return new Response(JSON.stringify(networkFixture), { status: 200 });
        }
        if (url.startsWith("/api/people/search?")) {
          return new Response(JSON.stringify(longSearchPage), {
            status: 200,
          });
        }
        if (url === "/api/people/person-004") {
          return new Response(JSON.stringify(longDetail), {
            status: 200,
          });
        }
        return new Response("not found", { status: 404 });
      }),
    );
    renderScreen();

    const search = await screen.findByRole("combobox", { name: "人を検索" });
    fireEvent.change(search, { target: { value: "Yui" } });
    await screen.findByRole("option", { name: /Yui Mori/ });
    fireEvent.keyDown(search, { key: "ArrowDown" });
    fireEvent.keyDown(search, { key: "Enter" });

    expect(
      await screen.findByRole("heading", {
        level: 2,
        name: longDisplayName,
      }),
    ).toBeVisible();
    expect(screen.getByLabelText("プロフィール画像なし")).toBeVisible();
    fireEvent.keyDown(window, { key: "Escape" });
    await waitFor(() => expect(search).toHaveFocus());
  });

  it("shows a visible expansion failure and allows a retry", async () => {
    let expansionAttempts = 0;
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
        const url = String(input);
        if (url === "/api/network" && !init?.method) {
          return new Response(JSON.stringify(networkFixture), { status: 200 });
        }
        if (url === "/api/people/person-003") {
          return new Response(JSON.stringify(dormantPersonDetail), {
            status: 200,
          });
        }
        if (url === "/api/network/expand") {
          expansionAttempts += 1;
          if (expansionAttempts === 1)
            return new Response("safe", { status: 502 });
          return new Response(JSON.stringify(expandedNetworkFixture), {
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
    const expand = await screen.findByRole("button", {
      name: "この人からつながりを広げる",
    });
    fireEvent.click(expand);
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "つながりを広げられませんでした",
    );
    fireEvent.click(expand);
    await waitFor(() =>
      expect(screen.getByTestId("network-graph-canvas")).toHaveTextContent(
        "graph:6",
      ),
    );
  });

  it("keeps Person Detail loading and errors safe, visible, and retryable", async () => {
    let detailAttempts = 0;
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL) => {
        const url = String(input);
        if (url === "/api/network") {
          return new Response(JSON.stringify(networkFixture), { status: 200 });
        }
        if (url === "/api/people/person-003") {
          detailAttempts += 1;
          if (detailAttempts <= 2) {
            await new Promise((resolve) => window.setTimeout(resolve, 10));
            return new Response("private upstream detail", { status: 502 });
          }
          return new Response(JSON.stringify(dormantPersonDetail), {
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
    expect(
      screen.getByText("この人とのつながりを読み込んでいます"),
    ).toBeVisible();
    const detailError = await screen.findByRole("alert", undefined, {
      timeout: 3_000,
    });
    expect(detailError).toHaveTextContent("詳細を表示できませんでした");
    expect(detailError).not.toHaveTextContent("private upstream detail");

    fireEvent.click(screen.getByRole("button", { name: "再読み込み" }));
    expect(
      await screen.findByRole("heading", { level: 2, name: "Ren Ito" }),
    ).toBeVisible();
  });
});
