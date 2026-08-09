# Vertical Slice 002 / NC-011 Acceptance Criteria — Frozen v0.1

**Status:** Frozen v0.1 — NC-011 pre-implementation Review Gate approved on 2026-08-09.

## Domain and application

- AC-D01 A valid command creates one immutable `ANALOG` + `SELF_REPORTED` `InteractionEvent` for the
  authenticated current user and exactly one other person.
- AC-D02 The server fixes participant count to two, creator to current user, confidence to `1.0`,
  initiator to absent, and accepts no client override for these fields.
- AC-D03 The seven allowed analog types and three duration mappings are exact and deterministic.
- AC-D04 Self, unknown-person, before-join, older-than-30-day, and future interactions are rejected
  without persistence while preserving `createdAt >= occurredAt`.
- AC-D05 Same-key/same-payload retry returns the original result without a second event or second
  recalculation; same-key/different-payload returns an idempotency conflict.
- AC-D06 Event insert and canonical pair-profile upsert commit atomically; a forced derivation or
  persistence failure leaves neither partial change.
- AC-D07 Only the affected canonical pair is re-derived; unrelated materialized profiles remain
  unchanged.
- AC-D08 The accepted `relationship-v0.1.0` configuration/version is used without recalibration or
  user-feedback formula effects.
- AC-D09 One recent first contact can derive `NEW`; a factual recent coffee after the accepted old
  strong fixture can derive `RECONNECTED`.

## Persistence and API

- AC-A01 `POST /api/v1/interactions` resolves the current person server-side and never accepts a
  focal/current-person ID or arbitrary participant list.
- AC-A02 Valid first creation returns `201` with the documented non-numeric capture result.
- AC-A03 Idempotent replay returns `200`, `replayed: true`, and the original interaction ID.
- AC-A04 Invalid payloads use safe standard errors; no database/upstream detail is exposed.
- AC-A05 Development persona isolation works and the existing production boundary remains closed
  with `401 AUTHENTICATION_REQUIRED` until production SSO exists.
- AC-A06 OpenAPI and generated TypeScript contracts include exactly the frozen NC-011 route/schema
  changes and pass drift checks.
- AC-A07 API integration verifies the committed event, relational participants, updated profile,
  and unchanged unrelated profile in PostgreSQL.

## UX and accessibility

- AC-U01 Person Detail for a non-current connected or potential person exposes `接点を記録`; the
  current user never does.
- AC-U02 Capture stays inside Person Detail, preselects the person, requires type and duration, and
  defaults occurrence time without preselecting factual type/depth.
- AC-U03 The normal preselected-person path requires at most type, duration, optional date/time, and
  save decisions and can be completed in a human review target of 10 seconds.
- AC-U04 Saving disables repeat submission; failure retains inputs and the same `clientRequestId` for
  safe retry.
- AC-U05 Success is announced accessibly, refreshes detail/timeline and the graph projection, keeps
  the selected person visible, and does not globally re-layout existing nodes.
- AC-U06 Back/Escape cancels without a write and restores focus; validation and server errors are
  associated/announced without relying on color.
- AC-U07 The form is keyboard-operable, supports missing avatar/long name states, and has no
  horizontal overflow at 390 CSS pixels.
- AC-U08 The UI never sends or displays confidence, strength, activation, formula weights, or a
  user-selected relationship state.

## E2E and review evidence

- AC-E01 After deterministic demo reset, P001 records `COFFEE` + `MEDIUM` with dormant P018; after
  the committed write, the detail refetch derives `RECONNECTED` with a new factual timeline item.
- AC-E02 Retrying the same saved request produces no duplicate timeline item or evidence change.
- AC-E03 A potential-person integration case creates only the P001↔person relationship and no
  third-party pair.
- AC-E04 Docker Playwright covers success, validation/cancel, safe retry, keyboard/focus, and API
  health; repository lint, format, strict types, unit/integration tests, OpenAPI drift, build, and
  `git diff --check` pass.
- AC-E05 Human review confirms the flow is factual, non-judgmental, usable within about 10 seconds,
  and does not feel like relationship scoring or employee monitoring.

## Explicit non-acceptance scope

NC-011 acceptance does not cover multi-person capture, event edit/delete, `また話したい`,
Recommendations/Home, user relationship correction, inferred/imported event reconciliation,
production SSO, production observability, or production-scale qualification.
