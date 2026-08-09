import type Graph from "graphology";

import type {
  GraphEdgeOpacity,
  GraphEdgeStyle,
  GraphEdgeType,
  GraphEdgeWidth,
  RelationshipState,
} from "../../../lib/api/generated";

export type GraphPoint = Readonly<{ x: number; y: number }>;

export type NetworkNodeAttributes = {
  clusterId: string;
  color: string;
  displayName: string;
  forceLabel: boolean;
  hidden: boolean;
  hop: number;
  isFocal: boolean;
  isPotential: boolean;
  label: string;
  relevance: number;
  relationshipState: RelationshipState | null;
  shortRole: string | null;
  size: number;
  type: "circle";
  x: number;
  y: number;
  zIndex: number;
};

export type NetworkEdgeAttributes = {
  color: string;
  edgeType: GraphEdgeType;
  hidden: boolean;
  opacity: GraphEdgeOpacity;
  relationshipState: RelationshipState | null;
  size: number;
  style: GraphEdgeStyle;
  type: "line";
  width: GraphEdgeWidth;
  zIndex: number;
};

export type NetworkGraphAttributes = {
  focalPersonId: string;
};

export type NetworkGraph = Graph<
  NetworkNodeAttributes,
  NetworkEdgeAttributes,
  NetworkGraphAttributes
>;

export type VisibleHopMode = "ONE_HOP" | "TWO_HOP";

export type NetworkGraphModel = {
  bounds: { x: [number, number]; y: [number, number] };
  clusterLabels: ReadonlyMap<string, string>;
  graph: NetworkGraph;
  positions: ReadonlyMap<string, GraphPoint>;
};

export type NetworkGraphController = {
  centerOnFocal(): void;
  fit(): void;
  zoomIn(): void;
  zoomOut(): void;
};
