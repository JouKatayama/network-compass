import {
  captureCameraState,
  createCameraController,
  restoreCameraState,
} from "../features/network/graph/camera-controller";

describe("camera controller", () => {
  it("delegates zoom, fit, and focal centering to Sigma's camera", () => {
    const camera = {
      animate: vi.fn(() => Promise.resolve()),
      animatedReset: vi.fn(() => Promise.resolve()),
      animatedUnzoom: vi.fn(() => Promise.resolve()),
      animatedZoom: vi.fn(() => Promise.resolve()),
      ratio: 1,
    };
    const renderer = {
      getCamera: () => camera,
      getGraph: () => ({
        getAttribute: () => "person-001",
        getNodeAttributes: () => ({ x: 0, y: 0 }),
      }),
      graphToViewport: () => ({ x: 400, y: 300 }),
      viewportToFramedGraph: () => ({ x: 0.5, y: 0.5 }),
    } as unknown as Parameters<typeof createCameraController>[0];
    const controller = createCameraController(renderer);

    controller.zoomIn();
    controller.zoomOut();
    controller.fit();
    controller.centerOnFocal();

    expect(camera.animatedZoom).toHaveBeenCalledWith({
      duration: 180,
      factor: 1.35,
    });
    expect(camera.animatedUnzoom).toHaveBeenCalledWith({
      duration: 180,
      factor: 1.35,
    });
    expect(camera.animatedReset).toHaveBeenCalledWith({ duration: 280 });
    expect(camera.animate).toHaveBeenCalledWith(
      { angle: 0, ratio: 0.82, x: 0.5, y: 0.5 },
      { duration: 280 },
    );
  });

  it("captures and restores the exact Sigma camera state across graph replacement", () => {
    const state = { angle: 0.12, ratio: 0.74, x: 0.42, y: 0.61 };
    const camera = { getState: vi.fn(() => state), setState: vi.fn() };
    const renderer = {
      getCamera: () => camera,
    } as unknown as Parameters<typeof captureCameraState>[0];

    expect(captureCameraState(renderer)).toEqual(state);
    restoreCameraState(renderer, state);
    expect(camera.setState).toHaveBeenCalledWith(state);
  });
});
