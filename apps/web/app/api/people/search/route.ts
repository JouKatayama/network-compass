import { proxyNetworkCompassApi } from "../../../../lib/server/api-proxy";

export const dynamic = "force-dynamic";

const ALLOWED_QUERY_KEYS = [
  "q",
  "limit",
  "cursor",
  "organizationId",
  "communityId",
  "activityId",
  "skillId",
] as const;

export async function GET(request: Request) {
  const input = new URL(request.url).searchParams;
  const output = new URLSearchParams();
  for (const key of ALLOWED_QUERY_KEYS) {
    const value = input.get(key);
    if (value !== null) output.set(key, value);
  }
  return proxyNetworkCompassApi(`/api/v1/people/search?${output}`);
}
