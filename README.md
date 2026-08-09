# Network Compass

Network Compass is a person-first internal networking product. The repository contains one Next.js
web application, one FastAPI modular monolith, and one PostgreSQL database. Canonical domain facts,
the versioned Relationship Engine, deterministic synthetic fixtures, their persistence/reset
workflow, and the internal personal GraphProjection service are implemented; product graph APIs/UI,
recommendations, and production authentication remain later scope.

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

Compose waits for PostgreSQL, upgrades the Alembic schema, starts the API, and then starts
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
| `make synthetic-demo` / `make synthetic-edge-cases` | Generate deterministic fact datasets and validation reports |
| `make demo-reset` | Start the local DB, replace demo facts, and rebuild relationship profiles |
| `make projection-review-p001` | Reset demo data and write the deterministic P001 Review Gate B JSON |
| `make db-check` | Run `SELECT 1` inside the started API container |
| `make migrate` / `make migrate-current` | Upgrade or report the Alembic revision |

`make demo-reset` is intentionally destructive to the local demo database. It runs the fixed
synthetic seed in one transaction, replaces canonical source facts, and rebuilds the recalculable
`relationship-v0.1.0` materialization. Running it repeatedly produces the same source/profile
counts without duplicate rows.

`make projection-review-p001` performs that reset and then writes the bounded personal projection to
`docs/review-artifacts/NC-006-p001-graph-projection.json`. The command is intentionally a review
workflow, not an HTTP product endpoint; NC-007 owns the authenticated API contract.

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
tools/synthetic-data Deterministic demo/edge-case fact generator and tests
tests/e2e/         Playwright smoke tests
docs/              Product and architecture system of record
```

FastAPI's generated OpenAPI document is the implemented API-contract source. Later issues may
generate frontend types from it; NC-001 does not add product API schemas.

Read `AGENTS.md`, `PROJECT_STATUS.md`, and the relevant issue specification before implementation.
