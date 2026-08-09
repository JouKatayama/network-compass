# Network Compass — Repository Instructions

Network Compass is a **person-first internal networking platform**. The repository documentation under `docs/` is the system of record. This file is intentionally short: use it as a map, then read the relevant specification before editing code.

## Before any implementation

1. Read `docs/index.md`.
2. Read the issue file under `docs/issues/`.
3. Read every specification referenced by that issue.
4. Read accepted ADRs that affect the touched area.
5. Inspect existing code before proposing changes.
6. Produce a concise implementation plan before coding.
7. If the issue conflicts with an accepted spec or ADR, stop and report the conflict instead of silently changing the design.

## Product invariants

- The default graph is **Person ↔ Person**. Organization, Community, Activity, Skill, and Project are context.
- The product helps people **remember, reconnect, discover, meet, and introduce**; it is not an employee-ranking, monitoring, staffing, or sales-CRM product.
- Do not rank people by centrality, relationship count, network score, influence, or seniority.
- Missing data is not evidence of a weak relationship.
- New joiners include both **graduate hires and experienced hires**; Network Ramp must not assume one group only.
- Recommendations and relationship state are deterministic/explainable in v0.1. Do not add opaque ML ranking.

## Privacy invariants

- A user's individual relationship graph is visible to that user, not to administrators.
- Enforce visibility server-side; do not rely on frontend hiding.
- Never ingest or expose Teams message bodies, email bodies, transcripts, private audio, GPS, or Bluetooth proximity.
- Activities/interests are used only when explicitly user-declared and visibility permits.

## Approved v0.1 stack

- Frontend: Next.js, React, TypeScript, Sigma.js, Graphology, TanStack Query
- Backend: FastAPI, Python, Pydantic, SQLAlchemy 2.x
- Data: PostgreSQL, Alembic
- Graph computation: NetworkX
- Tests: Vitest, React Testing Library, pytest, Playwright
- Local: Docker Compose
- API contract: FastAPI OpenAPI

Do **not** add Neo4j, Redis, Kafka/RabbitMQ, Kubernetes, GraphQL, vector databases, agent frameworks, or split microservices without an approved ADR.

## Layering

Backend: `api -> application -> domain -> infrastructure`.

Business logic must not live in React components or FastAPI routers. Relationship calculation, recommendation ranking, network-ramp phase determination, graph candidate ranking, and network-health calculation belong in backend domain/application services.

## Source-of-truth model

Fact/source data -> derived models -> UI read models.

`InteractionEvent` and other facts are the source. `RelationshipProfile`, `Recommendation`, and `NetworkHealthProfile` are recalculable derived data. Never make synthetic `RelationshipState` the source of truth.

## Graph UX invariants

- Preserve the user's mental map; do not globally re-layout after every click.
- Initial projection: 1 focal user, <=24 primary 1-hop people, <=12 2-hop teaser people.
- Expand: <=8 new nodes per action.
- Soft visible limit: 60; hard visible limit: 80.
- Node size = current relevance, never career level.
- Edge width = relationship strength; edge opacity = current activation.
- Dormant = dashed/lower opacity; potential/2-hop = dotted or muted.
- Detailed content belongs in the Person Detail drawer, not on the canvas.

## Quality gate

A task is complete only when acceptance criteria are satisfied, tests/lint/typecheck pass, API/specs are updated when needed, privacy and architecture boundaries are preserved, and no unrelated future scope is added.

## Key navigation

- Product: `docs/product/index.md`
- Domain: `docs/domain/index.md`
- UX: `docs/ux/index.md`
- Architecture/ADRs: `docs/architecture/index.md`
- Synthetic data: `docs/data/synthetic-data-spec.md`
- Testing: `docs/testing/index.md`
- Issues: `docs/issues/index.md`
- Codex workflow: `docs/codex/index.md`
- Active NC-007 plan: `docs/exec-plans/active/NC-007.md`; NC-006 is completed and accepted at Review Gate B.
