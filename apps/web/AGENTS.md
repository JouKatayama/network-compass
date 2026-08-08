# Web App Instructions

Applies to `apps/web/**` in addition to root `AGENTS.md`.

- Keep product/business calculation out of React. Consume backend read models.
- Graph-specific logic belongs under the graph feature/subsystem rather than page components.
- Server state should use TanStack Query; local presentation state should remain local unless a demonstrated cross-feature need exists.
- Use semantic design tokens; do not scatter hard-coded colors.
- Preserve keyboard-accessible non-graph paths for critical selection/search actions.
- During NC-001, build only the application/test/tooling scaffold and a minimal foundation page. Do not implement `/network` product behavior ahead of NC-008.
