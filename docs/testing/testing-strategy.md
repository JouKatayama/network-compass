# Testing Strategy v0.1

## Pyramid

1. Domain unit tests — highest volume; especially Relationship/Projection logic
2. Application/integration tests
3. API tests
4. Frontend component/state tests
5. Small number of Playwright E2E hero/smoke tests

## NC-001 foundation requirements

CI must run formatting/lint, typecheck, backend tests, frontend tests/build, and at least a minimal E2E/smoke path that is stable in the scaffold. NC-001 should not invent fake domain tests for business logic not yet implemented.

## Graph testing later

Prefer state/transform/controller tests over brittle WebGL pixel assertions. Use deterministic layout seed and selected screenshot regression states when graph implementation exists.

## Persistence and reset testing

Use fast isolated SQLAlchemy repository tests for mapping, constraints, context visibility, source/
derived separation, repeatability, and transaction rollback. CI additionally runs Alembic and the
deterministic demo reset twice against PostgreSQL, then checks that ORM metadata has no uncommitted
migration diff. Docker Compose remains the executable integration boundary.

## Merge rule

Green tests are necessary but not sufficient. Acceptance criteria, architecture/privacy compliance, and human UX review are also required.
