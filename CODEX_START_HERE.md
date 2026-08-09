# Codex Start Here

Use this repository as a spec-driven implementation project. Do not infer future functionality from the product vision and implement it early.

## Active task

**NC-007 API v0.1 is implemented and verified, awaiting human review** on
`feat/nc-007-api-v01`. Follow the evidence in `docs/exec-plans/active/NC-007.md`; do not start NC-008
until NC-007 is accepted.

For NC-007, read in order:

1. `AGENTS.md`
2. `PROJECT_STATUS.md`
3. `docs/issues/NC-007-api-v01.md`
4. `docs/exec-plans/completed/NC-006.md`
5. the API contract, GraphProjection, PersonDetail, search, privacy, UX, synthetic-data, and testing specifications affecting the implemented endpoints
6. accepted ADRs affecting the API contract, modular-monolith layering, PostgreSQL access, graph projection, and server-side visibility
7. `services/api/AGENTS.md`
8. `tools/synthetic-data/AGENTS.md`

## Required operating mode

The required plan exists at `docs/exec-plans/active/NC-007.md` and covers endpoints/schemas,
current-user authorization, search and PersonDetail reads, privacy, OpenAPI/contract strategy, tests,
and unresolved assumptions. Keep it current during implementation. Do not implement NC-008 graph UI.

After implementation, report: commands run, acceptance criteria satisfied/not satisfied, files changed, and remaining risks/technical debt.

## Runtime baseline

Use stable/LTS versions compatible with the approved stack. The intended baseline for the initial scaffold is Node.js 24 LTS, pnpm 10.x, and Python 3.13.x. Do not upgrade major runtime families during NC-001 unless required by a dependency and explicitly documented.
