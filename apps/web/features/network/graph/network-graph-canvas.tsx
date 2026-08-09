"use client";

import {
  forwardRef,
  useEffect,
  useImperativeHandle,
  useRef,
  type CSSProperties,
} from "react";
import type Sigma from "sigma";

import { attachCanvasLayers } from "./canvas-layers";
import { createCameraController } from "./camera-controller";
import type {
  NetworkEdgeAttributes,
  NetworkGraphAttributes,
  NetworkGraphController,
  NetworkGraphModel,
  NetworkNodeAttributes,
} from "./types";

type NetworkSigma = Sigma<
  NetworkNodeAttributes,
  NetworkEdgeAttributes,
  NetworkGraphAttributes
>;

type NetworkGraphCanvasProps = {
  model: NetworkGraphModel;
};

const containerStyle: CSSProperties = { height: "100%", width: "100%" };

export const NetworkGraphCanvas = forwardRef<
  NetworkGraphController,
  NetworkGraphCanvasProps
>(function NetworkGraphCanvas({ model }, ref) {
  const containerRef = useRef<HTMLDivElement>(null);
  const controllerRef = useRef<NetworkGraphController | null>(null);

  useImperativeHandle(
    ref,
    () => ({
      centerOnFocal: () => controllerRef.current?.centerOnFocal(),
      fit: () => controllerRef.current?.fit(),
      zoomIn: () => controllerRef.current?.zoomIn(),
      zoomOut: () => controllerRef.current?.zoomOut(),
    }),
    [],
  );

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    let disposed = false;
    let renderer: NetworkSigma | null = null;
    let detachLayers: (() => void) | null = null;

    async function initialize() {
      const { default: SigmaConstructor } = await import("sigma");
      if (disposed) return;
      renderer = new SigmaConstructor(model.graph, container!, {
        allowInvalidContainer: true,
        defaultEdgeType: "line",
        defaultNodeType: "circle",
        enableCameraPanning: true,
        enableCameraRotation: false,
        enableCameraZooming: true,
        hideEdgesOnMove: false,
        hideLabelsOnMove: true,
        labelColor: { color: "#eef3ff" },
        labelDensity: 0.72,
        labelFont: "Inter, ui-sans-serif, system-ui, sans-serif",
        labelGridCellSize: 110,
        labelRenderedSizeThreshold: 8,
        labelSize: 12,
        labelWeight: "600",
        maxCameraRatio: 3.2,
        minCameraRatio: 0.24,
        nodeReducer: (_node, attributes) =>
          container!.clientWidth < 640 && !attributes.isFocal
            ? { ...attributes, label: "" }
            : attributes,
        renderEdgeLabels: false,
        renderLabels: true,
        stagePadding: 48,
        zIndex: true,
      });
      renderer.setCustomBBox(model.bounds);
      detachLayers = attachCanvasLayers(renderer, model.clusterLabels);
      controllerRef.current = createCameraController(renderer);
    }
    void initialize();

    return () => {
      disposed = true;
      controllerRef.current = null;
      detachLayers?.();
      renderer?.kill();
    };
  }, [model]);

  return (
    <div
      aria-label="あなたを中心とした人のつながりのグラフ。ドラッグで移動、ホイールで拡大縮小できます。"
      className="network-graph-canvas"
      data-testid="network-graph-canvas"
      ref={containerRef}
      role="img"
      style={containerStyle}
    />
  );
});
