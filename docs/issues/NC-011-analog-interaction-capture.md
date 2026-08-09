# NC-011 — Analog Interaction Capture v0.1

**Status:** Draft specification review; do not implement until the NC-011 pre-implementation Review
Gate records Frozen v0.1 approval.

Implement a fast factual 1:1 analog-contact write path from Person Detail through
`POST /api/v1/interactions`: validate and persist one immutable self-reported `InteractionEvent`,
atomically re-derive only the affected relationship pair with accepted `relationship-v0.1.0`, then
refresh Person Detail/network without global graph re-layout.

Read and implement only the frozen versions of:

- `docs/ux/analog-interaction.md`
- `docs/domain/analog-interaction-capture.md`
- `docs/domain/interaction-event-model.md`
- `docs/domain/relationship-model.md`
- `docs/domain/relationship-model-v0.1-config.md`
- `docs/architecture/api-contracts.md`
- `docs/architecture/privacy-security.md`
- `docs/testing/acceptance-criteria-vs002.md`

Preserve current-person server authority, immutable fact/derived separation, safe errors, generated
OpenAPI types, keyboard/focus behavior, and deterministic Docker E2E. Do not add multi-person
capture, event edit/delete, recommendation or user-correction semantics, inferred-event
reconciliation, Home/Health/Ramp behavior, production SSO, or formula recalibration.

Stop after CI-green implementation evidence for a human NC-011/VS002 Go/No-Go; do not begin a later
slice.
