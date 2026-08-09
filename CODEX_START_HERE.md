# Codex Start Here

Use this repository as a spec-driven implementation project. Do not infer future functionality from the product vision and implement it early.

## Current task

The current implementation issue is **NC-005 Persistence + Demo Reset**. NC-001 through NC-004 are complete, and Review Gate A is approved.

Read in order:

1. `AGENTS.md`
2. `PROJECT_STATUS.md`
3. `docs/issues/NC-005-persistence-demo-reset.md`
4. `docs/exec-plans/active/NC-005.md`
5. `docs/exec-plans/completed/NC-004.md`
6. the domain, architecture, privacy, data, and testing specifications affecting persistence and deterministic rebuilds
7. accepted ADRs affecting the database and source/derived separation
8. `services/api/AGENTS.md`
9. `tools/synthetic-data/AGENTS.md`

## Required operating mode

Before editing implementation code, return a short plan containing: files/directories to create or modify, dependency/tooling choices within approved constraints, migration and reset strategy, test strategy, and any unresolved assumption. Keep `docs/exec-plans/active/NC-005.md` current. Do not implement unrelated later issues.

After implementation, report: commands run, acceptance criteria satisfied/not satisfied, files changed, and remaining risks/technical debt.

## Runtime baseline

Use stable/LTS versions compatible with the approved stack. The intended baseline for the initial scaffold is Node.js 24 LTS, pnpm 10.x, and Python 3.13.x. Do not upgrade major runtime families during NC-001 unless required by a dependency and explicitly documented.
