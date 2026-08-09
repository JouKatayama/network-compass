# Human / Architecture Review Gates

## NC-001 review

Confirm repo ergonomics, dependency choices, Docker reliability, CI, command discoverability, and absence of premature product/business implementation.

## Gate A — after NC-004

Review relationship formulas/configuration and fixture outputs before persistence/projection progresses. Validate the model is explainable and that shared context alone does not create relationships.

## Gate B — after NC-006

Inspect P001 GraphProjection JSON: composition, diversity, dormant/active mix, 2-hop path availability, bounds, and privacy. Do not proceed to UI if the projection is product-wrong.

NC-006 review artifact: `docs/review-artifacts/NC-006-p001-graph-projection.json`. Review the
`graphProjection` as the production-shaped read model and use the sibling `review` summary/synthetic
ID lookup to identify P018, P067, state/cluster counts, bound checks, and privacy checks.

**Decision:** Review Gate B completed on 2026-08-09. The P001 projection composition, diversity,
hero paths, bounds, and privacy shape were accepted for NC-007 consumption.

## Gate C — after NC-009

Human UX review: does the graph feel like a human relationship memory rather than Neo4j/analytics? Does selection preserve mental map? Does P018 evoke relationship history and P067 feel naturally reachable?

## NC-010 Go/No-Go

Evaluate all VS001 acceptance criteria, hero E2E, performance/error states, and known technical debt. Future Home/Recommendation/Analog/Ramp work begins only after this slice is coherent.
