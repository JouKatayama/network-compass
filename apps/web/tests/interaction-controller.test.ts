import { attachGraphInteractionEvents } from "../features/network/graph/interaction-controller";

describe("graph interaction controller", () => {
  it("delegates Sigma enter, leave, and click events and detaches cleanly", () => {
    const handlers = new Map<string, (event?: { node: string }) => void>();
    const renderer = {
      off: vi.fn((event: string) => handlers.delete(event)),
      on: vi.fn(
        (event: string, handler: (event?: { node: string }) => void) => {
          handlers.set(event, handler);
        },
      ),
    } as unknown as Parameters<typeof attachGraphInteractionEvents>[0];
    const onHoverPerson = vi.fn();
    const onSelectPerson = vi.fn();

    const detach = attachGraphInteractionEvents(renderer, {
      onHoverPerson,
      onSelectPerson,
    });
    handlers.get("enterNode")?.({ node: "person-018" });
    handlers.get("clickNode")?.({ node: "person-018" });
    handlers.get("leaveNode")?.();

    expect(onHoverPerson).toHaveBeenNthCalledWith(1, "person-018");
    expect(onHoverPerson).toHaveBeenNthCalledWith(2, null);
    expect(onSelectPerson).toHaveBeenCalledWith("person-018");

    detach();
    expect(handlers.size).toBe(0);
  });
});
