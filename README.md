# Network Compass

Network Compass is a person-first internal networking product. This repository currently contains
the NC-001 executable foundation: one Next.js web application, one FastAPI modular monolith, and one
PostgreSQL database. Product screens, domain models, graph logic, recommendations, and production
authentication are intentionally not part of this foundation.

## Runtime baseline

- Node.js 24 LTS
- pnpm 10.34.5 via Corepack
- Python 3.13
- uv 0.11.16 or a lock-compatible newer uv release
- Docker with Docker Compose

The JavaScript dependency graph is locked in `pnpm-lock.yaml`; the Python dependency graph is locked
in `services/api/uv.lock`. Container base images are pinned to the verified multi-architecture
repository digests used by this scaffold.

## Quick start with Docker Compose

No local Node or Python installation is required for this path.

```bash
cp .env.example .env
docker compose up --build
```

The local services are:

| Service | URL or port | Purpose |
|---|---|---|
| Web | <http://localhost:3000> | Minimal NC-001 foundation page |
| API | <http://localhost:8000/health> | FastAPI liveness endpoint |
| API docs | <http://localhost:8000/docs> | FastAPI-generated OpenAPI UI |
| PostgreSQL | `localhost:5432` | Local application database |

Compose waits for PostgreSQL, upgrades the empty Alembic baseline, starts the API, and then starts
the web application. Stop the stack without deleting its database volume with:

```bash
docker compose down
```

## Local development

Install the locked dependencies:

```bash
corepack pnpm install --frozen-lockfile
uv --directory services/api sync --frozen
```

Start PostgreSQL only, then run the applications with reload enabled in separate terminals:

```bash
docker compose up db
corepack pnpm dev:web
uv --directory services/api run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Copy `.env.example` to `.env` when overriding Compose ports or database settings. Compose reads that
file automatically. For host-run API commands, export `DATABASE_URL` in the shell when the default
local URL is not suitable. The checked-in example contains local-only values and no production
secrets.

## Quality commands

The root `Makefile` provides the common entry points:

| Command | Checks or action |
|---|---|
| `make install` | Install both locked dependency graphs |
| `make start` / `make stop` | Start/build or stop the full Compose stack |
| `make dev-web` / `make dev-api` | Start one application with reload |
| `make format` / `make format-check` | Format or verify JS/TS/Python formatting |
| `make lint` | Run ESLint and Ruff |
| `make typecheck` | Run TypeScript and mypy |
| `make test` | Run Vitest and pytest |
| `make build` | Build the production Next.js application |
| `make e2e` | Run Playwright smoke tests with local web/API servers |
| `make check` | Run format, lint, typecheck, unit tests, and web build |
| `make db-check` | Run `SELECT 1` inside the started API container |
| `make migrate` / `make migrate-current` | Upgrade or report the Alembic revision |

To run the Playwright smoke directly, install Chromium once and then execute the test:

```bash
corepack pnpm exec playwright install chromium
corepack pnpm test:e2e
```

The test runner starts the local web and API development servers unless
`PLAYWRIGHT_EXTERNAL_SERVERS=1` is set. CI sets that variable after bringing up the Compose stack.

## Repository layout

```text
apps/web/          Next.js application and frontend unit tests
services/api/      FastAPI application, Alembic, and backend tests
packages/contracts Future generated OpenAPI contracts (no handwritten duplicate contract)
tests/e2e/         Playwright smoke tests
docs/              Product and architecture system of record
```

FastAPI's generated OpenAPI document is the implemented API-contract source. Later issues may
generate frontend types from it; NC-001 does not add product API schemas.

Read `AGENTS.md`, `PROJECT_STATUS.md`, and the relevant issue specification before implementation.
