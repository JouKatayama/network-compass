# Codex Start Here

Use this repository as a spec-driven implementation project. Do not infer future functionality from the product vision and implement it early.

## Active task

**Active task:** NC-011 Analog Interaction Capture v0.1. Its UX/domain/API and VS002 acceptance
specifications were frozen by human approval on 2026-08-09. Follow
`docs/exec-plans/active/NC-011.md`; implementation has not started.

Before any future implementation, read in order:

1. `AGENTS.md`
2. `PROJECT_STATUS.md`
3. `docs/issues/NC-011-analog-interaction-capture.md`
4. `docs/exec-plans/active/NC-011.md`
5. `docs/exec-plans/completed/NC-010.md`
6. the accepted VS001 matrix and every product/domain/UX/architecture specification referenced by
   NC-011
7. ADR-002 and the accepted frontend/modular-monolith architecture decisions
8. `services/api/AGENTS.md`
9. `apps/web/AGENTS.md`
10. `tests/e2e/AGENTS.md`

## Required operating mode

Implement only the active NC-011 plan. Do not infer Home, Recommendation, user-correction,
multi-person, inferred-event, production SSO, or other later scope from the product vision.

After implementation, report: commands run, acceptance criteria satisfied/not satisfied, files changed, and remaining risks/technical debt.

## Runtime baseline

Use stable/LTS versions compatible with the approved stack. The intended baseline for the initial scaffold is Node.js 24 LTS, pnpm 10.x, and Python 3.13.x. Do not upgrade major runtime families during NC-001 unless required by a dependency and explicitly documented.
