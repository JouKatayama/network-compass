# NC-001 — Repository Foundation

**Status:** Ready

## Goal

Create a clean, reproducible monorepo foundation for Network Compass so later issues can add domain functionality without changing the approved architecture.

## Read first

`AGENTS.md`, `docs/architecture/overview.md`, `docs/architecture/repository-structure.md`, ADR-003, ADR-007, ADR-009, ADR-010, `docs/testing/testing-strategy.md`.

## Required implementation

- Next.js + React + TypeScript app under `apps/web`
- FastAPI Python app under `services/api`
- PostgreSQL service via root Docker Compose
- Alembic migration foundation
- pytest foundation
- Vitest + React Testing Library foundation
- Playwright foundation
- GitHub Actions CI
- lint/format/typecheck commands for both ecosystems
- root developer commands/scripts for install/start/test/lint/typecheck where practical
- `/health` endpoint on API
- minimal frontend landing/health placeholder proving the web app runs; do not implement product screens
- `.env.example` with non-secret variable names/default-safe local values
- lockfiles and reproducible dependency configuration
- scoped `AGENTS.md` files remain preserved

## Runtime/tooling baseline

Node 24 LTS, pnpm 10.x, Python 3.13.x. If a concrete dependency requires a different supported minor/major, stop and explain before changing a major runtime family.

## Acceptance criteria

- `docker compose up --build` (or documented equivalent) starts web, API, PostgreSQL
- web available locally and renders a minimal foundation page
- API `GET /health` returns 200 and a minimal healthy response
- database connectivity can be verified without creating future domain tables
- Alembic initializes and can report/upgrade the current baseline
- frontend lint, typecheck, unit test, and production build pass
- backend lint, typecheck, and pytest pass
- Playwright smoke infrastructure executes successfully against the scaffold
- GitHub Actions runs the relevant checks
- no Neo4j/Redis/Kafka/GraphQL/vector DB/Kubernetes/microservice split introduced
- no Relationship/Recommendation/Graph product logic implemented
- root README contains accurate local development commands after implementation

## Non-goals

Domain models, synthetic people, Relationship Engine, graph projection, `/api/v1/me/network`, Sigma graph UI, Home, Network Ramp, production authentication.

## Human review

Review dependency choices, repository ergonomics, Docker reliability, commands, CI duration/clarity, and whether later issue directories/boundaries are easy to extend without premature abstraction.
