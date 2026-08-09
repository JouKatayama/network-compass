import type Sigma from "sigma";

import {
  clusterColor,
  edgeDash,
  edgeOpacity,
  withAlpha,
} from "./semantic-values";
import type {
  NetworkEdgeAttributes,
  NetworkGraphAttributes,
  NetworkNodeAttributes,
} from "./types";

type NetworkSigma = Sigma<
  NetworkNodeAttributes,
  NetworkEdgeAttributes,
  NetworkGraphAttributes
>;

function prepareCanvas(
  renderer: NetworkSigma,
  canvas: HTMLCanvasElement,
): CanvasRenderingContext2D | null {
  const context = canvas.getContext("2d");
  if (!context) return null;
  const { width, height } = renderer.getDimensions();
  const pixelRatio = window.devicePixelRatio || 1;
  const physicalWidth = Math.max(1, Math.floor(width * pixelRatio));
  const physicalHeight = Math.max(1, Math.floor(height * pixelRatio));
  canvas.style.width = `${width}px`;
  canvas.style.height = `${height}px`;
  if (canvas.width !== physicalWidth || canvas.height !== physicalHeight) {
    canvas.width = physicalWidth;
    canvas.height = physicalHeight;
  }
  context.setTransform(pixelRatio, 0, 0, pixelRatio, 0, 0);
  context.clearRect(0, 0, width, height);
  return context;
}

function drawOrganizationRegions(
  renderer: NetworkSigma,
  canvas: HTMLCanvasElement,
  clusterLabels: ReadonlyMap<string, string>,
): void {
  const context = prepareCanvas(renderer, canvas);
  if (!context) return;
  const dimensions = renderer.getDimensions();
  const graph = renderer.getGraph();
  const clusters = new Map<string, Array<{ x: number; y: number }>>();

  graph.forEachNode((_node, attributes) => {
    const point = renderer.graphToViewport({
      x: attributes.x,
      y: attributes.y,
    });
    const points = clusters.get(attributes.clusterId) ?? [];
    points.push(point);
    clusters.set(attributes.clusterId, points);
  });

  for (const [clusterId, points] of [...clusters].sort(([left], [right]) =>
    left.localeCompare(right),
  )) {
    if (points.length < 2) continue;
    const center = points.reduce(
      (value, point) => ({ x: value.x + point.x, y: value.y + point.y }),
      { x: 0, y: 0 },
    );
    center.x /= points.length;
    center.y /= points.length;
    const spread = Math.max(
      74,
      ...points.map((point) =>
        Math.sqrt((point.x - center.x) ** 2 + (point.y - center.y) ** 2),
      ),
    );
    const color = clusterColor(clusterId);
    const radius = Math.min(280, spread + 58);
    const gradient = context.createRadialGradient(
      center.x,
      center.y,
      radius * 0.1,
      center.x,
      center.y,
      radius,
    );
    gradient.addColorStop(0, withAlpha(color, 0.11));
    gradient.addColorStop(0.72, withAlpha(color, 0.055));
    gradient.addColorStop(1, withAlpha(color, 0));
    context.fillStyle = gradient;
    context.beginPath();
    context.ellipse(
      center.x,
      center.y,
      radius * 1.22,
      radius,
      0,
      0,
      Math.PI * 2,
    );
    context.fill();

    context.fillStyle = withAlpha(color, 0.55);
    context.font = "600 11px Inter, system-ui, sans-serif";
    context.letterSpacing = "0.04em";
    context.fillText(
      clusterLabels.get(clusterId) ?? "所属未設定",
      Math.max(16, Math.min(dimensions.width - 160, center.x - radius)),
      Math.max(20, Math.min(dimensions.height - 16, center.y - radius * 0.56)),
    );
  }
}

function drawRelationshipEdges(
  renderer: NetworkSigma,
  canvas: HTMLCanvasElement,
): void {
  const context = prepareCanvas(renderer, canvas);
  if (!context) return;
  const graph = renderer.getGraph();

  graph.forEachEdge((_edge, attributes, source, target) => {
    const sourceAttributes = graph.getNodeAttributes(source);
    const targetAttributes = graph.getNodeAttributes(target);
    const sourcePoint = renderer.graphToViewport(sourceAttributes);
    const targetPoint = renderer.graphToViewport(targetAttributes);

    context.beginPath();
    context.moveTo(sourcePoint.x, sourcePoint.y);
    context.lineTo(targetPoint.x, targetPoint.y);
    context.strokeStyle = attributes.color;
    context.globalAlpha = edgeOpacity(attributes.opacity);
    context.lineWidth = attributes.size;
    context.lineCap = attributes.style === "DOTTED" ? "round" : "butt";
    context.setLineDash([...edgeDash(attributes.style)]);
    context.stroke();
  });
  context.globalAlpha = 1;
  context.setLineDash([]);
}

export function attachCanvasLayers(
  renderer: NetworkSigma,
  clusterLabels: ReadonlyMap<string, string>,
): () => void {
  const organizationCanvas = renderer.createCanvas("organization-regions", {
    beforeLayer: "edges",
    style: { pointerEvents: "none" },
  });
  const relationshipCanvas = renderer.createCanvas("semantic-edges", {
    beforeLayer: "edges",
    style: { pointerEvents: "none" },
  });

  const draw = () => {
    drawOrganizationRegions(renderer, organizationCanvas, clusterLabels);
    drawRelationshipEdges(renderer, relationshipCanvas);
  };
  renderer.on("afterRender", draw);
  renderer.on("resize", draw);
  renderer.refresh();

  return () => {
    renderer.off("afterRender", draw);
    renderer.off("resize", draw);
  };
}
