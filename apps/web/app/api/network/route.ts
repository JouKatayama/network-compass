import { proxyNetworkCompassApi } from "../../../lib/server/api-proxy";

export const dynamic = "force-dynamic";

export async function GET() {
  return proxyNetworkCompassApi("/api/v1/me/network");
}
