# Codex Start Here

Use this repository as a spec-driven implementation project. Do not infer future functionality from the product vision and implement it early.

## Active task

**NC-009 Person Detail + Graph Interaction is implemented and verified, awaiting Review Gate C** on
`feat/nc-009-person-detail-graph-interaction`. Follow `docs/exec-plans/active/NC-009.md`; do not
start NC-010 until the P001→P018→P067 interaction is accepted.

For NC-009, read in order:

1. `AGENTS.md`
2. `PROJECT_STATUS.md`
3. `docs/issues/NC-009-person-detail-graph-interaction.md`
4. `docs/exec-plans/completed/NC-008.md`
5. the graph interaction, My Network, Person Detail, screen-state, user-journey, API contract,
   projection, accessibility, privacy, and testing specifications
6. ADR-002 and the accepted frontend/modular-monolith architecture decisions
7. `apps/web/AGENTS.md`
8. `tests/e2e/AGENTS.md`

## Required operating mode

Record implementation and review evidence at `docs/exec-plans/active/NC-009.md`. Keep that plan
active until Review Gate C is accepted. Do not implement NC-010 or later product areas.

After implementation, report: commands run, acceptance criteria satisfied/not satisfied, files changed, and remaining risks/technical debt.

## Runtime baseline

Use stable/LTS versions compatible with the approved stack. The intended baseline for the initial scaffold is Node.js 24 LTS, pnpm 10.x, and Python 3.13.x. Do not upgrade major runtime families during NC-001 unless required by a dependency and explicitly documented.
