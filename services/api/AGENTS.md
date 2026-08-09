# API Service Instructions

Applies to `services/api/**` in addition to root `AGENTS.md`.

- Layer `api -> application -> domain -> infrastructure`.
- Routers translate HTTP only; do not put relationship/projection calculations in routers.
- Domain code should avoid FastAPI/SQLAlchemy coupling where practical.
- Pydantic schemas validate boundaries; persistence models are not automatically public API schemas.
- SQLAlchemy records and repositories belong in infrastructure; transactions and rebuild workflows are orchestrated by application/command layers.
- Keep canonical facts separate from recalculable materializations, and keep Alembic migrations aligned with ORM metadata.
- OpenAPI becomes the implemented API-contract source.
- During NC-001, implement only foundation and `/health`; do not create future business endpoints or domain tables.
