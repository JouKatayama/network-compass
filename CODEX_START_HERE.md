# Codex Start Here

Use this repository as a spec-driven implementation project. Do not infer future functionality from the product vision and implement it early.

## Next task

**NC-006 Network Projection Service is complete and human-reviewed at Review Gate B.** No
implementation issue is currently active. The next issue is **NC-007 API v0.1**.

Before starting NC-007, read in order:

1. `AGENTS.md`
2. `PROJECT_STATUS.md`
3. `docs/issues/NC-007-api-v01.md`
4. `docs/exec-plans/completed/NC-006.md`
5. the API contract, GraphProjection, PersonDetail, search, privacy, UX, synthetic-data, and testing specifications affecting the implemented endpoints
6. accepted ADRs affecting the API contract, modular-monolith layering, PostgreSQL access, graph projection, and server-side visibility
7. `services/api/AGENTS.md`
8. `tools/synthetic-data/AGENTS.md`

## Required operating mode

Before editing implementation code, create `docs/exec-plans/active/NC-007.md` and return a short
plan covering endpoints/schemas, current-user authorization, search and PersonDetail reads, privacy,
OpenAPI/contract strategy, tests, and unresolved assumptions. Do not implement NC-008 graph UI.

After implementation, report: commands run, acceptance criteria satisfied/not satisfied, files changed, and remaining risks/technical debt.

## Runtime baseline

Use stable/LTS versions compatible with the approved stack. The intended baseline for the initial scaffold is Node.js 24 LTS, pnpm 10.x, and Python 3.13.x. Do not upgrade major runtime families during NC-001 unless required by a dependency and explicitly documented.
