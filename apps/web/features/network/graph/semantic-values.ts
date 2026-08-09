import type {
  GraphEdgeOpacity,
  GraphEdgeStyle,
  GraphEdgeWidth,
} from "../../../lib/api/generated";

const CLUSTER_COLORS = [
  "#67d7c4",
  "#7aa7ff",
  "#f1b86b",
  "#f08fba",
  "#9c8df2",
  "#8dd17e",
] as const;

export const FOCAL_NODE_COLOR = "#b49cff";
export const POTENTIAL_NODE_COLOR = "#8292ad";

function stableHash(value: string): number {
  let hash = 2166136261;
  for (let index = 0; index < value.length; index += 1) {
    hash ^= value.charCodeAt(index);
    hash = Math.imul(hash, 16777619);
  }
  return hash >>> 0;
}

export function clusterColor(clusterId: string): string {
  return CLUSTER_COLORS[stableHash(clusterId) % CLUSTER_COLORS.length];
}

export function edgeWidth(width: GraphEdgeWidth): number {
  return {
    MUTED: 0.8,
    THIN: 1.1,
    MEDIUM: 1.8,
    THICK: 2.7,
  }[width];
}

export function edgeOpacity(opacity: GraphEdgeOpacity): number {
  return {
    MUTED: 0.18,
    LOW: 0.28,
    MEDIUM: 0.46,
    HIGH: 0.7,
  }[opacity];
}

export function edgeDash(style: GraphEdgeStyle): readonly number[] {
  return {
    SOLID: [],
    DASHED: [7, 6],
    DOTTED: [2, 7],
  }[style];
}

export function nodeSize(
  relevance: number,
  isFocal: boolean,
  isPotential: boolean,
): number {
  if (isFocal) return 17;
  if (isPotential) return 7;
  return 8.5 + Math.max(0, Math.min(1, relevance)) * 3.5;
}

export function withAlpha(hex: string, alpha: number): string {
  const value = hex.replace("#", "");
  const red = Number.parseInt(value.slice(0, 2), 16);
  const green = Number.parseInt(value.slice(2, 4), 16);
  const blue = Number.parseInt(value.slice(4, 6), 16);
  return `rgba(${red}, ${green}, ${blue}, ${alpha})`;
}
