# Network Compass

Network Compass is a person-first internal networking product that visualizes an employee's internal network as a **second social memory** and helps them remember people, reconnect dormant ties, discover reachable people, and build meaningful relationships. It also provides a Network Ramp journey for both graduate and experienced new joiners so initial network gaps do not unnecessarily suppress access to people and opportunities.

## Current status

**Specification complete; implementation begins with Vertical Slice 001 / NC-001.** See `PROJECT_STATUS.md`.

## Start here

For humans: read `docs/index.md` and `docs/product/vision.md`.

For Codex: read `AGENTS.md`, then `CODEX_START_HERE.md`, then the relevant issue specification.

## Vertical Slice 001

The first slice proves this experience:

`Synthetic facts -> Relationship Engine -> Personal Network Projection -> My Network Graph -> Person Detail -> Relationship Timeline -> 2-hop discovery`

It deliberately excludes Home recommendations, analog-interaction writes, Network Ramp UI, enterprise integrations, admin analytics, ML ranking, and production SSO.

## Approved architecture

Modular monolith: Next.js/React/TypeScript + Sigma.js/Graphology frontend; FastAPI/Python + NetworkX domain logic; PostgreSQL/Alembic persistence; OpenAPI contract; Docker Compose local environment.

See `ARCHITECTURE.md` and `docs/architecture/overview.md`.

## Repository layout target

```text
network-compass/
├── AGENTS.md
├── README.md
├── CODEX_START_HERE.md
├── PROJECT_STATUS.md
├── ARCHITECTURE.md
├── docs/
├── apps/web/
├── services/api/
├── packages/contracts/
├── tools/synthetic-data/
└── tests/e2e/
```

NC-001 creates the executable application foundation inside that layout.
