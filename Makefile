.PHONY: build check db-check demo-reset demo-reset-host dev-api dev-web e2e format format-check install lint migrate migrate-current start stop synthetic-demo synthetic-edge-cases test typecheck

install:
	corepack pnpm install --frozen-lockfile
	uv --directory services/api sync --frozen

start:
	docker compose up --build

stop:
	docker compose down

dev-web:
	corepack pnpm dev:web

dev-api:
	uv --directory services/api run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

format:
	corepack pnpm format:js
	uv --directory services/api run ruff format . ../../tools/synthetic-data

format-check:
	corepack pnpm format:check:js
	uv --directory services/api run ruff format --check . ../../tools/synthetic-data

lint:
	corepack pnpm lint:web
	uv --directory services/api run ruff check . ../../tools/synthetic-data

typecheck:
	corepack pnpm typecheck:web
	uv --directory services/api run mypy app tests ../../tools/synthetic-data/network_compass_synthetic ../../tools/synthetic-data/tool_tests

test:
	corepack pnpm test:web
	uv --directory services/api run pytest

synthetic-demo:
	PYTHONPATH=$(CURDIR)/services/api:$(CURDIR)/tools/synthetic-data uv --directory services/api run python -m network_compass_synthetic --family demo --output $(CURDIR)/tools/synthetic-data/output/demo

synthetic-edge-cases:
	PYTHONPATH=$(CURDIR)/services/api:$(CURDIR)/tools/synthetic-data uv --directory services/api run python -m network_compass_synthetic --family edge_cases --output $(CURDIR)/tools/synthetic-data/output/edge_cases

build:
	corepack pnpm build:web

e2e:
	corepack pnpm test:e2e

db-check:
	docker compose exec -T api python -m app.infrastructure.database

demo-reset:
	docker compose up -d --wait db
	docker compose build api
	docker compose run --rm --no-deps api alembic upgrade head
	docker compose run --rm --no-deps api python -m app.commands.demo_reset --family demo

demo-reset-host:
	PYTHONPATH=$(CURDIR)/services/api:$(CURDIR)/tools/synthetic-data uv --directory services/api run python -m app.commands.demo_reset --family demo

migrate:
	docker compose exec -T api alembic upgrade head

migrate-current:
	docker compose exec -T api alembic current

check: format-check lint typecheck test build
