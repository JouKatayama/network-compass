import type {
  GraphExpansionRequestSchema,
  GraphProjectionSchema,
} from "./generated";

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

export async function expandNetworkProjection(
  request: GraphExpansionRequestSchema,
  signal?: AbortSignal,
): Promise<GraphProjectionSchema> {
  let response: Response;
  try {
    response = await fetch("/api/network/expand", {
      body: JSON.stringify(request),
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      method: "POST",
      signal,
    });
  } catch {
    throw new NetworkRequestError();
  }

  if (!response.ok) throw new NetworkRequestError();
  return (await response.json()) as GraphProjectionSchema;
}
