# ADR-001: PostgreSQL first; no Neo4j for MVP

**Status:** Accepted

## Context

The required graph operations are predominantly 1-hop/2-hop traversal, mutual connections, small personal projections, and NetworkX analysis.

## Decision

Use PostgreSQL for persistence and NetworkX for graph computation.

## Consequences

The repository and implementation must preserve this decision unless a replacement ADR is accepted. Prefer the simplest implementation consistent with the decision and product/privacy specifications.

## Reconsider when

Reconsider when deep/complex graph-pattern traversal, very large graph-native path workloads, or graph-native recommendation creates measured complexity/performance issues.
