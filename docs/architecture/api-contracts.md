# API Contract v0.1

Base path: `/api/v1`. Current-user operations use `/me`; normal clients do not pass an arbitrary current user ID.

## Vertical Slice 001

### GET `/api/v1/me/network`

Returns `GraphProjection`. The final v0.1 endpoint has no query inputs and returns the accepted default
projection: <=24 1-hop and <=12 2-hop teaser people. Potential-path edges omit relationship state,
strength, and activation.

### POST `/api/v1/me/network/expand`

Accepts one selected visible person ID plus the ordered IDs of people already expanded in the
current session. The server rebuilds the authenticated current person's projection, safely replays
that history, and adds at most eight newly authorized adjacent people for the selected person. The
client never submits a focal-person ID or projection payload; invalid/non-visible histories are
rejected. The hard visible limit remains 80 and third-party path metrics remain omitted.

### GET `/api/v1/people/{personId}`

Returns `PersonDetail` relative to the current user: identity, natural-language relationship summary,
factual timeline, permitted common context, and a bounded connection path. It does not expose numeric
relationship scores or arbitrary third-party relationship metrics. Potential/none detail has no
fabricated interaction timeline.

### GET `/api/v1/people/search`

Structured search with `q` (1..100), `limit` (1..50), opaque criteria-bound `cursor`, and optional
`organizationId`, `communityId`, `activityId`, and `skillId` UUID filters. Returns person summary plus
direct/two-hop/none relationship context and bounded permitted common context. Ordering is
deterministic and does not use seniority, career level, centrality, degree, or relationship count.

## Current person and visibility

Development/test uses the optional `X-Network-Compass-Persona` synthetic external-ID header with a
configured `P001` default. The header resolves only persisted synthetic identities and is disabled in
production; arbitrary current-person UUIDs are never accepted. Production returns
`AUTHENTICATION_REQUIRED` until SSO integration is implemented.

Visibility is enforced before serialization. A private activity declaration is visible only to its
declaring person, network visibility requires a direct relationship, and organization visibility
requires a shared primary organization. The rule applies equally to detail, search text/filtering,
and common context.

## Later endpoints

`GET /me/recommendations`, recommendation feedback, `POST /interactions`, relationship feedback, `/me/network-ramp`, `/me/networking-profile`, `/me/home` are specified for later slices and must not be implemented during NC-001.

## Error envelope

```json
{
  "error": {
    "code": "MACHINE_READABLE_CODE",
    "message": "Safe client message",
    "requestId": "req_xxx"
  }
}
```

API contract source of truth is FastAPI OpenAPI. The canonical generated artifact is
`packages/contracts/openapi.json`; `make openapi-check` and CI reject drift. Frontend types should be
generated from OpenAPI rather than maintained as drifting duplicates.
