import { proxyNetworkCompassApi } from "../../../../lib/server/api-proxy";

export const dynamic = "force-dynamic";

export async function GET(
  _request: Request,
  context: { params: Promise<{ personId: string }> },
) {
  const { personId } = await context.params;
  return proxyNetworkCompassApi(
    `/api/v1/people/${encodeURIComponent(personId)}`,
  );
}
