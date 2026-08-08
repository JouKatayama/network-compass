# Architecture Summary

Network Compass v0.1 uses a **modular monolith** to maximize iteration speed while preserving clear domain boundaries.

```text
Browser
  Next.js / React / Sigma.js / Graphology
        |
        | REST / OpenAPI
        v
FastAPI modular monolith
  API -> Application -> Domain -> Infrastructure
        |
        +-- Relationship Engine
        +-- Network Projection Service / NetworkX
        +-- Recommendation Engine (later slice)
        +-- Network Ramp (later slice)
        |
        v
PostgreSQL / Alembic
```

The browser never receives the full enterprise graph. The backend produces a user-specific `GraphProjection` read model.

The authoritative architecture specification is `docs/architecture/overview.md`. Accepted decisions are under `docs/architecture/adr/`.
