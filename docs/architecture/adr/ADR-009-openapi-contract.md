# ADR-009: OpenAPI as implemented API contract source

**Status:** Accepted

## Context

Hand-maintained duplicated TypeScript/Python interfaces drift.

## Decision

FastAPI OpenAPI becomes the canonical implemented API contract; generate frontend API types.

## Consequences

The repository and implementation must preserve this decision unless a replacement ADR is accepted. Prefer the simplest implementation consistent with the decision and product/privacy specifications.

## Reconsider when

Reconsider only if API technology changes.
