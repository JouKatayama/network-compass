# Codex Start Here

Use this repository as a spec-driven implementation project. Do not infer future functionality from the product vision and implement it early.

## Active task

**No implementation task is active.** NC-010 received a human GO decision on 2026-08-09 and VS001
is complete. NC-011 Analog Interaction Capture specifications are drafted but await the human
pre-implementation Review Gate; no active execution plan may be created before freeze approval.

Before any future implementation, read in order:

1. `AGENTS.md`
2. `PROJECT_STATUS.md`
3. the new frozen issue/specification supplied for that work; NC-011 drafts do not qualify until
   their Review Gate decision is recorded
4. `docs/exec-plans/completed/NC-010.md`
5. the accepted VS001 matrix and every product/domain/UX/architecture specification referenced by
   the new issue
6. ADR-002 and the accepted frontend/modular-monolith architecture decisions
7. `apps/web/AGENTS.md`
8. `tests/e2e/AGENTS.md`

## Required operating mode

Do not begin future product areas from the vision alone. Create a new active execution plan only
after a concrete frozen issue exists, and keep its implementation within that issue's boundaries.

After implementation, report: commands run, acceptance criteria satisfied/not satisfied, files changed, and remaining risks/technical debt.

## Runtime baseline

Use stable/LTS versions compatible with the approved stack. The intended baseline for the initial scaffold is Node.js 24 LTS, pnpm 10.x, and Python 3.13.x. Do not upgrade major runtime families during NC-001 unless required by a dependency and explicitly documented.
