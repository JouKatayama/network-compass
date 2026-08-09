# Codex Start Here

Use this repository as a spec-driven implementation project. Do not infer future functionality from the product vision and implement it early.

## Active task

**NC-008 Frontend Shell + Graph Foundation is implemented and verified, awaiting Human UI Review**
on `feat/nc-008-frontend-graph-foundation`. Follow `docs/exec-plans/active/NC-008.md`; do not
implement NC-009 person-detail or graph-interaction behavior until the review is accepted.

For NC-008, read in order:

1. `AGENTS.md`
2. `PROJECT_STATUS.md`
3. `docs/issues/NC-008-frontend-graph-foundation.md`
4. `docs/exec-plans/completed/NC-007.md`
5. the graph interaction, My Network, screen-state, information-architecture, projection,
   accessibility, privacy, and testing specifications
6. ADR-002 and the accepted frontend/modular-monolith architecture decisions
7. `apps/web/AGENTS.md`
8. `tests/e2e/AGENTS.md`

## Required operating mode

The implementation and review evidence are recorded at `docs/exec-plans/active/NC-008.md`. Keep that
plan active until Human UI Review is accepted. Do not implement NC-009 person-detail, selection,
path, or expansion behavior.

After implementation, report: commands run, acceptance criteria satisfied/not satisfied, files changed, and remaining risks/technical debt.

## Runtime baseline

Use stable/LTS versions compatible with the approved stack. The intended baseline for the initial scaffold is Node.js 24 LTS, pnpm 10.x, and Python 3.13.x. Do not upgrade major runtime families during NC-001 unless required by a dependency and explicitly documented.
