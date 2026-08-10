import type {
  InteractionCaptureRequestSchema,
  InteractionCaptureResultSchema,
} from "./generated";

export class InteractionRequestError extends Error {
  constructor() {
    super("Interaction capture request failed");
    this.name = "InteractionRequestError";
  }
}

export async function captureInteraction(
  request: InteractionCaptureRequestSchema,
  signal?: AbortSignal,
): Promise<InteractionCaptureResultSchema> {
  let response: Response;
  try {
    response = await fetch("/api/interactions", {
      body: JSON.stringify(request),
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      method: "POST",
      signal,
    });
  } catch {
    throw new InteractionRequestError();
  }

  if (!response.ok) throw new InteractionRequestError();
  return (await response.json()) as InteractionCaptureResultSchema;
}
