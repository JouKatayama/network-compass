# Codex Start Here

Use this repository as a spec-driven implementation project. Do not infer future functionality from the product vision and implement it early.

## Current task

The first implementation task is **NC-001 Repository Foundation**.

Read, in order:

1. `AGENTS.md`
2. `PROJECT_STATUS.md`
3. `docs/issues/NC-001-repository-foundation.md`
4. `docs/exec-plans/active/NC-001.md`
5. `docs/architecture/overview.md`
6. `docs/architecture/repository-structure.md`
7. accepted ADRs linked from NC-001
8. `docs/testing/testing-strategy.md`

Then use `docs/codex/NC-001-execution-prompt.md` as the task prompt.

## Required operating mode

Before editing, return a short plan containing: files/directories to create or modify, dependency/tooling choices within approved constraints, test strategy, and any unresolved assumption. Do not implement unrelated later issues.

After implementation, report: commands run, acceptance criteria satisfied/not satisfied, files changed, remaining risks/technical debt, and whether NC-001 is ready for human review.

## Runtime baseline

Use stable/LTS versions compatible with the approved stack. The intended baseline for the initial scaffold is Node.js 24 LTS, pnpm 10.x, and Python 3.13.x. Do not upgrade major runtime families during NC-001 unless required by a dependency and explicitly documented.
