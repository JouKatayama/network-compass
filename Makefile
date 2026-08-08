.PHONY: build check db-check dev-api dev-web e2e format format-check install lint migrate migrate-current start stop test typecheck

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
	uv --directory services/api run ruff format .

format-check:
	corepack pnpm format:check:js
	uv --directory services/api run ruff format --check .

lint:
	corepack pnpm lint:web
	uv --directory services/api run ruff check .

typecheck:
	corepack pnpm typecheck:web
	uv --directory services/api run mypy app tests

test:
	corepack pnpm test:web
	uv --directory services/api run pytest

build:
	corepack pnpm build:web

e2e:
	corepack pnpm test:e2e

db-check:
	docker compose exec -T api python -m app.infrastructure.database

migrate:
	docker compose exec -T api alembic upgrade head

migrate-current:
	docker compose exec -T api alembic current

check: format-check lint typecheck test build
