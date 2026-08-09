# Graph Projection Configuration `graph-projection-v0.1.0`

This document fixes the first deterministic personal-network projection for Review Gate B. The
source representation is `NetworkProjectionConfig`; calibration changes require a new projection
version and must not silently change `graph-projection-v0.1.0`.

## Source graph and scope

The graph contains `Person` nodes and materialized `RelationshipProfile` edges. Organization units
are soft cluster metadata, never graph nodes. Community, activity, project, skill, career level,
seniority, centrality, degree, relationship count, influence, and network score are not candidate
ranking inputs.

Only the authenticated current person's projection may be requested. The service traverses the
observed graph to shortest-path distance two. `totalNetworkSize` is the number of non-focal people
reachable within those two hops before sampling.

## Direct relevance

For a focal-relative profile, recency is:

`recency = exp(-daysSinceLastMeaningfulInteraction / max(expectedCadenceDays, 30))`

Direct relevance is bounded to `[0, 1]`:

`0.28 * currentActivation + 0.24 * historicalDepth + 0.15 * relationshipStrength + 0.10 * dataConfidence + 0.08 * recency + 0.15 * memoryUtility(state)`

| State | Memory utility |
|---|---:|
| DORMANT | 1.00 |
| RECONNECTED | 0.95 |
| NEW | 0.75 |
| ACTIVE | 0.72 |
| CLOSE | 0.68 |
| WEAK | 0.62 |

Memory utility keeps useful dormant/reconnected context discoverable; it is not an employee-value
score. Default direct sampling first retains the best available candidate from each relationship
state, then the best from each organization cluster, then fills to 24 using deterministic
maximal-marginal-relevance:

`0.72 * relevance + 0.16 / (1 + selectedStateCount) + 0.12 / (1 + selectedClusterCount)`

This deliberately differs from taking the top 24 relationship strengths.

## Two-hop teaser relevance

A teaser must have NetworkX shortest-path distance exactly two and at least one selected/visible
one-hop intermediary. For an intermediary-to-potential profile:

`pathQuality = 0.44 * currentActivation + 0.31 * historicalDepth + 0.15 * relationshipStrength + 0.10 * dataConfidence`

`accessibility = 0.58 * pathQuality + 0.42 * focalToIntermediaryRelevance`

`teaserRelevance = 0.90 * bestAccessibility + 0.10 * newOrganizationCluster`

During explicit expansion, a path through the selected visible intermediary receives a bounded
`+0.12` accessibility preference. Teaser fill uses `0.78 * relevance`, organization novelty
`0.13 / (1 + selectedClusterCount)`, and intermediary novelty
`0.09 / (1 + selectedGatewayCount)`. Mutual-connection count is reported as context but is never a
ranking feature. Numeric third-party path quality is internal-only and is not serialized.

At most three equally short, deterministically ordered intermediary paths are retained for a teaser.
The public path edge carries only person IDs and muted `POTENTIAL_PATH` presentation; it omits the
third-party relationship state, strength, activation, and evidence decomposition.

## Bounds and deterministic order

- default: one focal + at most 24 direct + at most 12 teaser people
- expansion: at most 8 new people per previously unexpanded selected person
- soft visible limit: 60; hard visible limit: 80
- traversal never passes two hops in v0.1
- equivalent inputs are tied and ordered by canonical UUID, not insertion/database order
- `generatedAt` uses the materialized profile calculation timestamp

## Presentation buckets

Direct edge width uses relationship strength: `THICK >= 0.64`, `MEDIUM >= 0.35`, otherwise `THIN`.
Opacity uses current activation: `HIGH >= 0.60`, `MEDIUM >= 0.25`, otherwise `LOW`. DORMANT edges are
`DASHED`; other direct edges are `SOLID`. Potential edges are always `MUTED` width/opacity and
`DOTTED`.

These values drive a narrow visual relevance treatment later; raw numeric values must not be shown as
employee or default relationship rankings in the UI.
