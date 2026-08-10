# Vertical Slice 002 / NC-011 Implementation Acceptance Matrix

**Recommendation:** GO for human NC-011/VS002 review. The implementation and automated gates are
green as of 2026-08-10; NC-011 remains pending the required human GO/NO-GO and is not marked
accepted or complete by this document.

## Domain and application

| AC | Status | Evidence |
| --- | --- | --- |
| AC-D01 | PASS | `test_capture_creates_factual_event_and_only_upserts_the_affected_pair` creates one immutable `ANALOG` + `SELF_REPORTED` fact for the current/other pair. |
| AC-D02 | PASS | The same application test and `test_capture_is_atomic_idempotent_and_refreshes_dormant_detail` assert server-fixed creator, confidence `1.0`, participant count two, and absent initiator. |
| AC-D03 | PASS | `test_all_frozen_analog_types_are_retained`, `test_all_frozen_duration_buckets_are_retained`, and strict request-schema coverage prove the exact seven/three value sets. |
| AC-D04 | PASS | Application/API tests reject self, unknown, before-join, future, older-than-30-day, and digital input without writes; the valid-event test asserts `createdAt >= occurredAt`. |
| AC-D05 | PASS | `test_same_request_replays_without_a_second_event_or_recalculation` and the API integration test cover replay and conflict behavior. |
| AC-D06 | PASS | `test_profile_failure_rolls_back_the_event` forces the derived-write failure and observes neither source nor profile change. PostgreSQL E2E verifies the committed success boundary. |
| AC-D07 | PASS | Application and potential-person API tests compare every profile and find only the canonical target pair changed. |
| AC-D08 | PASS | New profile assertions retain `relationship-v0.1.0`; no relationship configuration or formula file changed. |
| AC-D09 | PASS | The application test derives first-contact `NEW`; the API/PostgreSQL journey derives P001↔P018 `RECONNECTED`. |

## Persistence and API

| AC | Status | Evidence |
| --- | --- | --- |
| AC-A01 | PASS | `POST /api/v1/interactions` uses the existing current-person dependency and accepts only `otherPersonId`, `clientRequestId`, type, duration, and occurrence time. |
| AC-A02 | PASS | API integration asserts first creation is `201` with only the non-numeric capture result. |
| AC-A03 | PASS | API integration and Docker E2E assert replay is `200`, `replayed: true`, and retains the original interaction ID. |
| AC-A04 | PASS | Invalid payload integration asserts safe request-identified errors and no upstream/database serialization. Web tests assert private error text is not rendered. |
| AC-A05 | PASS | Test settings exercise P001 current-person isolation; the production-shaped app remains `401 AUTHENTICATION_REQUIRED` even with a development persona header. |
| AC-A06 | PASS | `test_openapi_artifact_is_current_and_scoped_to_nc011`, OpenAPI `--check`, stable generated-file hashes, TypeScript, and production build all pass. |
| AC-A07 | PASS | API integration reconstructs relational participants and verifies the event, P018 profile update, and unchanged unrelated profile. The same endpoint succeeds through the real Compose PostgreSQL stack in Playwright. |

## UX and accessibility

| AC | Status | Evidence |
| --- | --- | --- |
| AC-U01 | PASS | Connected P018 and potential-person component flows expose `接点を記録`; graph selection rejects the focal/current person, so no current-person detail entry exists. |
| AC-U02 | PASS | Drawer component tests and browser inspection show the fixed person, no default type/duration, and a current-time default inside the existing Person Detail drawer. |
| AC-U03 | PASS | The visible happy path is type, duration, optional time change, and save. Human browser inspection found the complete form in one drawer view. |
| AC-U04 | PASS | Vitest observes a disabled `保存しています…` control, retained selections, and byte-equal payload/client request identity after a forced safe retry. |
| AC-U05 | PASS | Success refetches selected detail and current network only after the response, keeps the drawer/person/canvas mounted, and passes refreshed timeline/graph assertions. Existing-position layout preservation remains covered by the accepted expansion-layout tests. |
| AC-U06 | PASS | Vitest and Playwright cover associated required-group errors, safe server errors, Escape cancellation without a write, and restored `接点を記録` focus. |
| AC-U07 | PASS | Native labelled radios are keyboard-operated in Playwright; existing missing-avatar/long-name tests pass; the form has no horizontal overflow at 390×844. |
| AC-U08 | PASS | Request-body assertions exclude confidence, relationship state, current-person ID, numeric strength/activation, and formula fields; the form displays none of them. |

## End-to-end and review evidence

| AC | Status | Evidence |
| --- | --- | --- |
| AC-E01 | PASS | Deterministic Compose reset followed by P001→P018 `COFFEE` + `MEDIUM` yields `再びつながった関係` and a newest factual coffee timeline item. |
| AC-E02 | PASS | The captured request is replayed through `/api/interactions`; response is `200`/`replayed: true` and the coffee-item count remains baseline + one. |
| AC-E03 | PASS | `test_potential_capture_creates_only_the_current_person_pair` creates P001↔P067 as `NEW` and proves no other pair changed. |
| AC-E04 | PASS | Docker Playwright passes seven serial tests covering success, validation/cancel, safe retry, keyboard/focus, 390 px, existing graph behavior, and API health. All repository gates listed below are green. |
| AC-E05 | REVIEW | Automated semantics and browser inspection are factual/non-judgmental with no score UI; final product-feel approval remains intentionally reserved for the human NC-011 Review Gate. |

## Gate results

- API: pytest 101 tests; strict mypy 77 sources; Ruff lint/format; OpenAPI drift.
- Web: Vitest 22 tests; strict TypeScript; ESLint with zero warnings; Prettier; generated API type
  reproducibility; Next.js production build.
- Integration: Compose image builds; PostgreSQL migration/reset/connection; Playwright 7 tests.
- Repository: `git diff --check`; no migration or dependency-lock change; relationship calibration
  unchanged.
- Browser review: desktop drawer and refreshed P018 state inspected with no console entries; 390×844
  interaction and overflow behavior verified by real Chromium.

## Go/No-Go recommendation

**GO recommended for human Review Gate.** AC-D01–D09, AC-A01–A07, AC-U01–U08, and
AC-E01–E04 pass. AC-E05 is the sole human judgment and is deliberately not self-approved. No later
slice, production SSO, correction semantics, inferred reconciliation, multi-person capture, or
formula recalibration is included.
