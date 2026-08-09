# Codex Start Here

Use this repository as a spec-driven implementation project. Do not infer future functionality from the product vision and implement it early.

## Next task

**NC-005 Persistence + Demo Reset is complete and human-reviewed.** No implementation issue is currently active. The next issue is **NC-006 Network Projection Service**, which stops at Review Gate B.

Before starting NC-006, read in order:

1. `AGENTS.md`
2. `PROJECT_STATUS.md`
3. `docs/issues/NC-006-network-projection.md`
4. `docs/exec-plans/completed/NC-005.md`
5. the relationship, graph projection, privacy, UX, synthetic-data, and testing specifications affecting personal network sampling
6. accepted ADRs affecting graph projection and server-side visibility
7. `services/api/AGENTS.md`
8. `tools/synthetic-data/AGENTS.md`

## Required operating mode

Before editing implementation code, create `docs/exec-plans/active/NC-006.md` and return a short plan containing: files/directories to create or modify, projection/candidate/sampling choices within approved constraints, privacy boundary, P001 review JSON strategy, test strategy, and any unresolved assumption. Do not implement unrelated later issues or continue past Review Gate B.

After implementation, report: commands run, acceptance criteria satisfied/not satisfied, files changed, and remaining risks/technical debt.

## Runtime baseline

Use stable/LTS versions compatible with the approved stack. The intended baseline for the initial scaffold is Node.js 24 LTS, pnpm 10.x, and Python 3.13.x. Do not upgrade major runtime families during NC-001 unless required by a dependency and explicitly documented.
