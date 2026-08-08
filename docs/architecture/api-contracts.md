# API Contract v0.1

Base path: `/api/v1`. Current-user operations use `/me`; normal clients do not pass an arbitrary current user ID.

## Vertical Slice 001

### GET `/api/v1/me/network`

Returns `GraphProjection`. Default projection <=24 1-hop and <=12 2-hop teaser. Optional later-compatible query inputs may include lens/hops/selected/expand/filter fields, but NC-007 owns the final implementation.

### GET `/api/v1/people/{personId}`

Returns `PersonDetail` relative to the current user. Does not expose arbitrary third-party relationship strengths.

### GET `/api/v1/people/search`

Structured search with query, limit/cursor and optional organization/community/activity/skill filters. Returns person summary plus direct/two-hop/none relationship context and permitted common context.

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

API contract source of truth is FastAPI OpenAPI once implementation begins. Frontend types should be generated from OpenAPI rather than maintained as drifting duplicates.
