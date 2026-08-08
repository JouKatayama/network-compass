# Repository Bootstrap Procedure

This package is the **specification baseline** that should be committed before NC-001 implementation.

## 1. Create the repository

Create a GitHub repository named `network-compass` (private is recommended if the project contains internal-company concepts). Do not initialize it with an unrelated README/license template if you plan to copy this package as the first commit.

## 2. Copy this bootstrap package into the repository root

The root must contain `AGENTS.md`, `CODEX_START_HERE.md`, `PROJECT_STATUS.md`, `ARCHITECTURE.md`, and `docs/`.

## 3. Commit the specification baseline

Suggested first commit message:

```text
docs: establish Network Compass v0.1 specification baseline
```

This makes all later Codex-generated code reviewable against a stable spec commit.

## 4. Create GitHub issue NC-001

Use `docs/issues/NC-001-repository-foundation.md` as the issue body (or link to it from a short issue). Title:

```text
NC-001: Repository Foundation
```

## 5. Start Codex on NC-001

Give Codex access to the repository, then submit `docs/codex/NC-001-execution-prompt.md`. Codex must first return its implementation plan. Review that plan before allowing implementation if your Codex workflow supports a plan/review step.

## 6. Human review after implementation

Use the acceptance criteria in `docs/issues/NC-001-repository-foundation.md` and the PR template. Do not merge solely because Codex says the task is complete.

## 7. Next issue

Only after NC-001 is accepted, proceed to NC-002. Keep `PROJECT_STATUS.md` and `docs/exec-plans/` current as implementation progresses.
