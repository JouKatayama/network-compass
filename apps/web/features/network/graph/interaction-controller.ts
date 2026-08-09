import type Sigma from "sigma";

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

export function attachGraphInteractionEvents(
  renderer: NetworkSigma,
  callbacks: {
    onHoverPerson(personId: string | null): void;
    onSelectPerson(personId: string): void;
  },
): () => void {
  const enterNode = ({ node }: { node: string }) =>
    callbacks.onHoverPerson(node);
  const leaveNode = () => callbacks.onHoverPerson(null);
  const clickNode = ({ node }: { node: string }) =>
    callbacks.onSelectPerson(node);
  renderer.on("enterNode", enterNode);
  renderer.on("leaveNode", leaveNode);
  renderer.on("clickNode", clickNode);
  return () => {
    renderer.off("enterNode", enterNode);
    renderer.off("leaveNode", leaveNode);
    renderer.off("clickNode", clickNode);
  };
}
