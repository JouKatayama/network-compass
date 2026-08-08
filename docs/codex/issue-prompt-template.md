# Codex Issue Prompt Template

Implement GitHub Issue **NC-XXX**.

Before coding:

1. Read `/AGENTS.md`.
2. Read `/PROJECT_STATUS.md`.
3. Read `/docs/issues/NC-XXX-....md`.
4. Read every specification and accepted ADR referenced by the issue.
5. Inspect the current repository implementation.
6. Produce a concise implementation plan first.
7. Identify assumptions, conflicts, or missing information. Do not silently reinterpret specifications.

Implementation rules:

- implement only NC-XXX scope
- do not implement future issues
- keep business logic out of React components and HTTP routers
- preserve server-side privacy boundaries
- do not add unapproved technologies/architecture
- add/update tests for the issue's acceptance criteria
- keep changes small enough to review

After implementation:

1. run relevant tests
2. run lint/format checks
3. run typecheck
4. run build/smoke/E2E where relevant
5. list acceptance criteria satisfied/not satisfied
6. summarize files/architecture choices
7. list remaining risks or technical debt
8. do not claim completion when checks fail
