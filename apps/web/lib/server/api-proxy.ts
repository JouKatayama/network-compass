import { NextResponse } from "next/server";

const DEFAULT_API_URL = "http://127.0.0.1:8000";

export async function proxyNetworkCompassApi(
  path: string,
  init?: RequestInit,
): Promise<NextResponse> {
  const apiUrl = (
    process.env.NETWORK_COMPASS_API_INTERNAL_URL ?? DEFAULT_API_URL
  ).replace(/\/$/, "");
  try {
    const response = await fetch(`${apiUrl}${path}`, {
      ...init,
      cache: "no-store",
      headers: {
        Accept: "application/json",
        ...(init?.body ? { "Content-Type": "application/json" } : {}),
        ...init?.headers,
      },
    });
    return new NextResponse(await response.text(), {
      headers: { "content-type": "application/json" },
      status: response.status,
    });
  } catch {
    return NextResponse.json(
      {
        error: {
          code: "NETWORK_UNAVAILABLE",
          message: "Network service is temporarily unavailable.",
          requestId: `req_${crypto.randomUUID().replaceAll("-", "")}`,
        },
      },
      { status: 502 },
    );
  }
}
