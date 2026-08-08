# Codex Execution Prompt — NC-001

Implement **NC-001 Repository Foundation** in this repository.

Before editing, read in this exact order:

1. `/AGENTS.md`
2. `/PROJECT_STATUS.md`
3. `/docs/issues/NC-001-repository-foundation.md`
4. `/docs/exec-plans/active/NC-001.md`
5. `/docs/architecture/overview.md`
6. `/docs/architecture/repository-structure.md`
7. `/docs/architecture/privacy-security.md`
8. `/docs/architecture/adr/ADR-003-modular-monolith.md`
9. `/docs/architecture/adr/ADR-007-desktop-first.md`
10. `/docs/architecture/adr/ADR-009-openapi-contract.md`
11. `/docs/architecture/adr/ADR-010-monorepo-tooling.md`
12. `/docs/testing/testing-strategy.md`

Then inspect the repository and return an **NC-001 implementation plan before coding**. The plan must state:

- target files/directories
- exact JS/Python dependency/tooling choices within the approved runtime families
- Docker Compose topology
- local developer commands
- CI jobs/checks
- test/smoke strategy
- any assumption/conflict

After the plan is internally consistent, implement only NC-001. Do **not** implement Person/domain models, synthetic employees, Relationship Engine, graph projection, API product endpoints, Sigma graph product UI, recommendations, Network Ramp, or production SSO.

Definition of done is exactly the acceptance criteria in `docs/issues/NC-001-repository-foundation.md`. Run all available checks and report the final acceptance matrix. If any check fails, report the failure instead of declaring NC-001 complete.
