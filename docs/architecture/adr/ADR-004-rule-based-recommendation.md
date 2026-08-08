# ADR-004: Rule-based recommendation first

**Status:** Accepted

## Context

Cold start, trust, explainability, synthetic evaluation, and privacy favor deterministic logic.

## Decision

Use deterministic explainable recommendation ranking in v0.1.

## Consequences

The repository and implementation must preserve this decision unless a replacement ADR is accepted. Prefer the simplest implementation consistent with the decision and product/privacy specifications.

## Reconsider when

Reconsider learning-to-rank only after sufficient outcome/feedback data and evaluation design exist.
