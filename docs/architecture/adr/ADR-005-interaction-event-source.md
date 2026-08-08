# ADR-005: Interaction events as relationship-evidence source

**Status:** Accepted

## Context

Relationship formulas will change and must be recalculable.

## Decision

Persist interaction/context facts and materialize RelationshipProfile as derived data.

## Consequences

The repository and implementation must preserve this decision unless a replacement ADR is accepted. Prefer the simplest implementation consistent with the decision and product/privacy specifications.

## Reconsider when

Keep unless a future evidence architecture provides equal auditability/recomputability.
