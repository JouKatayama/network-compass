# Codex Start Here

Use this repository as a spec-driven implementation project. Do not infer future functionality from the product vision and implement it early.

## Active task

**NC-010 VS001 E2E + Hardening is implemented and verified, awaiting Go/No-Go review** on
`feat/nc-010-vs001-e2e-hardening`. Follow `docs/exec-plans/active/NC-010.md` and the final VS001
acceptance matrix; Review Gate C is accepted and NC-009 is merged.

For NC-010, read in order:

1. `AGENTS.md`
2. `PROJECT_STATUS.md`
3. `docs/issues/NC-010-e2e-hardening.md`
4. `docs/exec-plans/completed/NC-009.md`
5. the VS001 acceptance, hero E2E, testing strategy, graph interaction, My Network, Person Detail,
   screen-state, accessibility, and privacy specifications
6. ADR-002 and the accepted frontend/modular-monolith architecture decisions
7. `apps/web/AGENTS.md`
8. `tests/e2e/AGENTS.md`

## Required operating mode

Record implementation and review evidence at `docs/exec-plans/active/NC-010.md`. Keep that plan
active until the human VS001 Go/No-Go decision. Do not implement later product areas.

After implementation, report: commands run, acceptance criteria satisfied/not satisfied, files changed, and remaining risks/technical debt.

## Runtime baseline

Use stable/LTS versions compatible with the approved stack. The intended baseline for the initial scaffold is Node.js 24 LTS, pnpm 10.x, and Python 3.13.x. Do not upgrade major runtime families during NC-001 unless required by a dependency and explicitly documented.
