# ADR-006: Personal Graph Projection instead of full graph

**Status:** Accepted

## Context

Full enterprise graphs harm readability, privacy, performance, and product relevance.

## Decision

Backend creates a current-user-specific bounded GraphProjection.

## Consequences

The repository and implementation must preserve this decision unless a replacement ADR is accepted. Prefer the simplest implementation consistent with the decision and product/privacy specifications.

## Reconsider when

Reconsider limits/algorithms, not the privacy/readability principle, as scale changes.
