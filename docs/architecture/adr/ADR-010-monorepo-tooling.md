# ADR-010: pnpm workspace + Python backend tooling split

**Status:** Accepted

## Context

The repo contains a TypeScript web app and Python service; each ecosystem should use its native lock/tooling while sharing one git repository.

## Decision

Use pnpm 10.x/workspaces for JS/TS and a standard Python project/lock setup selected by NC-001 without inventing a JS-Python mega-build system.

## Consequences

The repository and implementation must preserve this decision unless a replacement ADR is accepted. Prefer the simplest implementation consistent with the decision and product/privacy specifications.

## Reconsider when

Reconsider only if build orchestration complexity later justifies an additional monorepo tool via ADR.
