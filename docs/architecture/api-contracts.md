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

### NC-011 Frozen v0.1: POST `/api/v1/interactions`

**Status:** Frozen v0.1 — NC-011 pre-implementation Review Gate approved on 2026-08-09.

The authenticated current person records one self-reported 1:1 analog interaction. The client does
not submit the current-person ID, participant list, channel, source, confidence, initiator, or any
relationship output.

Request body:

```json
{
  "clientRequestId": "8bd688d6-ec9e-4d4f-806d-a412a6fdbd2c",
  "otherPersonId": "00000000-0000-0000-0000-000000000067",
  "type": "COFFEE",
  "durationBucket": "MEDIUM",
  "occurredAt": "2026-08-09T12:30:00Z"
}
```

`type` accepts only `OFFICE_CHAT | COFFEE | LUNCH | DINNER | COMMUNITY | ACTIVITY | OTHER`.
`durationBucket` is required. `occurredAt` is required at the API boundary; the web client supplies
its default current time. Extra fields are forbidden.

First creation returns `201`:

```json
{
  "interactionId": "a7d787d8-e2c3-44db-b818-13b5bb52503a",
  "otherPersonId": "00000000-0000-0000-0000-000000000067",
  "occurredAt": "2026-08-09T12:30:00Z",
  "type": "COFFEE",
  "durationBucket": "MEDIUM",
  "replayed": false
}
```

The same `(current person, clientRequestId)` and normalized payload returns `200` with the original
interaction result and `replayed: true`. The response exposes no relationship state, numeric
strength, activation, evidence decomposition, confidence, creator, or third-party metrics. Person
Detail and network refetches are the display source of truth after commit.

Errors use the standard envelope:

- `400 INVALID_INTERACTION` for self-interaction, occurrence-time, or participant join-time
  violations
- `401 AUTHENTICATION_REQUIRED` at the existing production boundary
- `404 PERSON_NOT_FOUND` for an unavailable other person
- `409 IDEMPOTENCY_CONFLICT` when a key is reused with different normalized content
- `422` for request-shape, type-enum, or duration-enum failures

The server validates the occurrence time against its clock: no more than 30 days old and not in the
future. Event write and pair-profile upsert are atomic. The client refetches Person Detail and the
current network projection only after the response commits.

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
