# E2E Test Instructions

Applies to `tests/e2e/**`.

- Keep E2E tests few, deterministic, and centered on critical user flows.
- NC-001 creates smoke infrastructure only; do not encode the VS001 product hero flow before product implementation exists.
- Prefer stable user-facing semantics over implementation-detail selectors; use explicit test IDs only where appropriate.
