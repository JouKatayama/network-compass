import { NextResponse } from "next/server";

const DEFAULT_API_URL = "http://127.0.0.1:8000";

export const dynamic = "force-dynamic";

export async function GET() {
  const apiUrl = (
    process.env.NETWORK_COMPASS_API_INTERNAL_URL ?? DEFAULT_API_URL
  ).replace(/\/$/, "");
  try {
    const response = await fetch(`${apiUrl}/api/v1/me/network`, {
      cache: "no-store",
      headers: { Accept: "application/json" },
    });
    if (!response.ok) {
      return new NextResponse(await response.text(), {
        headers: { "content-type": "application/json" },
        status: response.status,
      });
    }
    return NextResponse.json(await response.json());
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
