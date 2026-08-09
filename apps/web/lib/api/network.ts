import type { GraphProjectionSchema } from "./generated";

export class NetworkRequestError extends Error {
  constructor() {
    super("Network projection request failed");
    this.name = "NetworkRequestError";
  }
}

export async function fetchNetworkProjection(
  signal?: AbortSignal,
): Promise<GraphProjectionSchema> {
  let response: Response;
  try {
    response = await fetch("/api/network", {
      headers: { Accept: "application/json" },
      signal,
    });
  } catch {
    throw new NetworkRequestError();
  }

  if (!response.ok) throw new NetworkRequestError();
  return (await response.json()) as GraphProjectionSchema;
}
