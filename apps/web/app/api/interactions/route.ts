import { proxyNetworkCompassApi } from "../../../lib/server/api-proxy";

export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  return proxyNetworkCompassApi("/api/v1/interactions", {
    body: await request.text(),
    method: "POST",
  });
}
