# ADR-002: Sigma.js for graph rendering

**Status:** Accepted

## Context

The main UI requires performant interactive person-network visualization with custom rendering and WebGL rather than diagram editing.

## Decision

Use Sigma.js with Graphology.

## Consequences

The repository and implementation must preserve this decision unless a replacement ADR is accepted. Prefer the simplest implementation consistent with the decision and product/privacy specifications.

## Reconsider when

Reconsider if compound/diagram-editing requirements dominate or a specific unsupported interaction becomes critical.
