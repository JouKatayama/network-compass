# System Architecture v0.1

## Style

**Modular monolith**. One FastAPI application with strong module boundaries; one Next.js web application; one PostgreSQL database. Do not split services during MVP.

## Approved stack

Frontend: Next.js, React, TypeScript, Sigma.js, Graphology, TanStack Query, Tailwind CSS/CSS variables.

Backend: FastAPI, Python, Pydantic, SQLAlchemy 2.x, NetworkX.

Data/migrations: PostgreSQL, Alembic.

Testing: Vitest, React Testing Library, pytest, Playwright.

Local: Docker Compose. CI: GitHub Actions. Contract: FastAPI OpenAPI.

Runtime baseline for NC-001: Node.js 24 LTS, pnpm 10.x, Python 3.13.x unless Codex documents a concrete compatibility blocker.

## Backend layers

`api -> application -> domain -> infrastructure`

Routers handle HTTP only. Application services orchestrate use cases. Domain services compute relationships/projections/recommendations and should be testable without FastAPI/SQLAlchemy when practical. Infrastructure implements persistence and future external connectors.

## Frontend state

Server state: TanStack Query. Local presentation state: React. Graph state/controllers: graph feature/provider. Shareable selection/filter state may use URL query parameters. Do not introduce Redux without a demonstrated need/ADR.

## Request flows

My Network: browser -> `/api/v1/me/network` -> use case -> relationship repository -> projection service/NetworkX -> GraphProjection -> Graphology -> Sigma.

Person Detail: node click -> `/api/v1/people/{id}` -> aggregated read model -> drawer.

Analog interaction (later): POST interaction -> persist fact -> recalc affected relationship -> invalidate relevant read models.

## Not in v0.1

Neo4j, microservices, Kafka/RabbitMQ, Redis, GraphQL, vector DB, Kubernetes, agent framework, production SSO integration.
