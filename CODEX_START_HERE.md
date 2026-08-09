# Codex Start Here

Use this repository as a spec-driven implementation project. Do not infer future functionality from the product vision and implement it early.

## Current task

The current implementation task is **NC-004 Relationship Engine v0.1**. NC-001 through NC-003 are complete.

Read, in order:

1. `AGENTS.md`
2. `PROJECT_STATUS.md`
3. `docs/issues/NC-004-relationship-engine.md`
4. `docs/exec-plans/active/NC-004.md`
5. `docs/domain/relationship-model.md`
6. `docs/domain/relationship-model-v0.1-config.md`
7. `docs/domain/domain-model.md`
8. `docs/domain/interaction-event-model.md`
9. `docs/data/synthetic-data-spec.md`
10. accepted ADRs affecting domain derivation and source facts
11. `services/api/AGENTS.md`
12. `tools/synthetic-data/AGENTS.md`
13. `docs/testing/acceptance-criteria-vs001.md`
14. `docs/testing/testing-strategy.md`

## Required operating mode

Before editing, return a short plan containing: files/directories to create or modify, dependency/tooling choices within approved constraints, test strategy, and any unresolved assumption. Do not implement unrelated later issues.

After implementation, report: commands run, acceptance criteria satisfied/not satisfied, files changed, remaining risks/technical debt, and whether NC-004 is ready for Review Gate A.

## Runtime baseline

Use stable/LTS versions compatible with the approved stack. The intended baseline for the initial scaffold is Node.js 24 LTS, pnpm 10.x, and Python 3.13.x. Do not upgrade major runtime families during NC-001 unless required by a dependency and explicitly documented.
