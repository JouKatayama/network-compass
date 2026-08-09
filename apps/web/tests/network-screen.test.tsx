import { fireEvent, render, screen, waitFor } from "@testing-library/react";

import { AppProviders } from "../app/providers";
import { NetworkScreen } from "../features/network/network-screen";
import { networkFixture } from "./network-fixture";

vi.mock("../features/network/graph/network-graph-canvas", () => ({
  NetworkGraphCanvas: ({ model }: { model: { graph: { order: number } } }) => (
    <div data-testid="network-graph-canvas">graph:{model.graph.order}</div>
  ),
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
});
