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
import {
  captureCameraState,
  createCameraController,
  restoreCameraState,
} from "./camera-controller";
import { attachGraphInteractionEvents } from "./interaction-controller";
import type {
  NetworkEdgeAttributes,
  NetworkGraphAttributes,
  NetworkGraphController,
  NetworkGraphInteraction,
  NetworkGraphModel,
  NetworkNodeAttributes,
  NetworkCameraState,
} from "./types";

type NetworkSigma = Sigma<
  NetworkNodeAttributes,
  NetworkEdgeAttributes,
  NetworkGraphAttributes
>;

type NetworkGraphCanvasProps = {
  emphasizedPathPersonIds: ReadonlySet<string>;
  hoveredPersonId: string | null;
  model: NetworkGraphModel;
  onHoverPerson(personId: string | null): void;
  onSelectPerson(personId: string): void;
  selectedPersonId: string | null;
};

const containerStyle: CSSProperties = { height: "100%", width: "100%" };

export const NetworkGraphCanvas = forwardRef<
  NetworkGraphController,
  NetworkGraphCanvasProps
>(function NetworkGraphCanvas(
  {
    emphasizedPathPersonIds,
    hoveredPersonId,
    model,
    onHoverPerson,
    onSelectPerson,
    selectedPersonId,
  },
  ref,
) {
  const containerRef = useRef<HTMLDivElement>(null);
  const controllerRef = useRef<NetworkGraphController | null>(null);
  const rendererRef = useRef<NetworkSigma | null>(null);
  const cameraStateRef = useRef<NetworkCameraState | null>(null);
  const onHoverRef = useRef(onHoverPerson);
  const onSelectRef = useRef(onSelectPerson);
  const interactionRef = useRef<NetworkGraphInteraction>({
    emphasizedPathPersonIds,
    hoveredPersonId,
    selectedPersonId,
  });

  useEffect(() => {
    onHoverRef.current = onHoverPerson;
    onSelectRef.current = onSelectPerson;
  }, [onHoverPerson, onSelectPerson]);

  useEffect(() => {
    interactionRef.current = {
      emphasizedPathPersonIds,
      hoveredPersonId,
      selectedPersonId,
    };
    rendererRef.current?.refresh();
  }, [emphasizedPathPersonIds, hoveredPersonId, selectedPersonId]);

  useImperativeHandle(
    ref,
    () => ({
      centerOnFocal: () => controllerRef.current?.centerOnFocal(),
      fit: () => controllerRef.current?.fit(),
      focusPerson: (personId) => controllerRef.current?.focusPerson(personId),
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
    let detachInteractions: (() => void) | null = null;

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
        nodeReducer: (node, attributes) => {
          const interaction = interactionRef.current;
          const selected = interaction.selectedPersonId;
          const hovered = interaction.hoveredPersonId === node;
          const inPath = interaction.emphasizedPathPersonIds.has(node);
          const related =
            selected !== null &&
            model.graph.hasNode(selected) &&
            (node === selected || model.graph.areNeighbors(node, selected));
          const faded = selected !== null && !related && !inPath;
          return {
            ...attributes,
            color: hovered
              ? "#f2fbff"
              : node === selected || inPath
                ? "#b59cff"
                : faded
                  ? "#344054"
                  : attributes.color,
            forceLabel: attributes.forceLabel || hovered || related || inPath,
            highlighted: hovered,
            label:
              container!.clientWidth < 640 &&
              !attributes.isFocal &&
              !hovered &&
              node !== selected
                ? ""
                : attributes.label ||
                  (hovered || related || inPath ? attributes.displayName : ""),
            size:
              attributes.size *
              (node === selected ? 1.28 : hovered || inPath ? 1.16 : 1),
            zIndex:
              hovered || node === selected || inPath ? 12 : attributes.zIndex,
          };
        },
        renderEdgeLabels: false,
        renderLabels: true,
        stagePadding: 48,
        zIndex: true,
      });
      rendererRef.current = renderer;
      renderer.setCustomBBox(model.bounds);
      detachLayers = attachCanvasLayers(
        renderer,
        model.clusterLabels,
        () => interactionRef.current,
      );
      controllerRef.current = createCameraController(renderer);
      restoreCameraState(renderer, cameraStateRef.current);
      detachInteractions = attachGraphInteractionEvents(renderer, {
        onHoverPerson: (personId) => onHoverRef.current(personId),
        onSelectPerson: (personId) => onSelectRef.current(personId),
      });
    }
    void initialize();

    return () => {
      disposed = true;
      if (renderer) cameraStateRef.current = captureCameraState(renderer);
      rendererRef.current = null;
      controllerRef.current = null;
      detachInteractions?.();
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
