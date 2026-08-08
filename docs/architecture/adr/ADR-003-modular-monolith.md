# ADR-003: Modular monolith

**Status:** Accepted

## Context

The product/domain is early and services are tightly evolving; distributed infrastructure would add operational cost without validated scaling need.

## Decision

Use one FastAPI backend with strict internal modules and one web app.

## Consequences

The repository and implementation must preserve this decision unless a replacement ADR is accepted. Prefer the simplest implementation consistent with the decision and product/privacy specifications.

## Reconsider when

Reconsider after measured scaling/team/deployment boundaries justify independent services.
