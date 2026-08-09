import type Sigma from "sigma";

import type {
  NetworkEdgeAttributes,
  NetworkGraphAttributes,
  NetworkGraphController,
  NetworkNodeAttributes,
} from "./types";

type NetworkSigma = Sigma<
  NetworkNodeAttributes,
  NetworkEdgeAttributes,
  NetworkGraphAttributes
>;

export function createCameraController(
  renderer: NetworkSigma,
): NetworkGraphController {
  return {
    centerOnFocal() {
      const graph = renderer.getGraph();
      const focalPersonId = graph.getAttribute("focalPersonId");
      const focal = graph.getNodeAttributes(focalPersonId);
      const viewportPoint = renderer.graphToViewport({
        x: focal.x,
        y: focal.y,
      });
      const framedPoint = renderer.viewportToFramedGraph(viewportPoint);
      void renderer.getCamera().animate(
        {
          angle: 0,
          ratio: Math.min(renderer.getCamera().ratio, 0.82),
          x: framedPoint.x,
          y: framedPoint.y,
        },
        { duration: 280 },
      );
    },
    fit() {
      void renderer.getCamera().animatedReset({ duration: 280 });
    },
    zoomIn() {
      void renderer.getCamera().animatedZoom({ duration: 180, factor: 1.35 });
    },
    zoomOut() {
      void renderer.getCamera().animatedUnzoom({ duration: 180, factor: 1.35 });
    },
  };
}
