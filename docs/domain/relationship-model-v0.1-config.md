# Relationship Model Configuration `relationship-v0.1.0`

This document fixes the first implemented calibration for Review Gate A. The source representation is the immutable `RELATIONSHIP_MODEL_V1` domain configuration. All output components are bounded to `[0, 1]` except cadence and dormancy ratio.

## Per-event evidence

For pair-relevant event `e`:

`E_e = B(type) * 1/sqrt(max(conversationParticipants - 1, 1)) * D(duration) * confidence * 2^(-ageDays/halfLife(type))`

Historical evidence uses the same expression with the half-life multiplied by `6`. Future events are excluded. If conversation participant count is absent, the recorded participant count is used.

| Interaction type | Base weight | Current half-life days |
|---|---:|---:|
| TEAMS_CHAT | 0.85 | 45 |
| EMAIL | 0.65 | 60 |
| ONLINE_1ON1 | 1.40 | 75 |
| GROUP_MEETING | 0.55 | 45 |
| OFFICE_CHAT | 1.00 | 60 |
| COFFEE | 1.35 | 120 |
| LUNCH | 1.45 | 120 |
| DINNER | 1.45 | 150 |
| COMMUNITY | 0.30 | 30 |
| ACTIVITY | 1.20 | 120 |
| OTHER | 0.50 | 45 |

Duration factors are unknown `1.00`, short `0.75`, medium `1.00`, and long `1.25`.

## Component composition

The saturation function is `S(raw, scale) = 1 - exp(-raw/scale)`.

- `digitalEvidence = S(sum current digital event evidence, 2.20)`
- `analogEvidence = S(sum current analog event evidence, 2.20)`
- `currentActivation = union(digitalEvidence, analogEvidence) + 0.08 * min(digitalEvidence, analogEvidence)`, then bounded
- channel union is `a + b - a*b`; it allows either channel to independently support a close relationship
- historical digital/analog evidence is independently saturated with scale `4.00`, combined by union, then receives at most `0.08 * socialContext`

Social context raw input is `0.16 * sharedCommunities + 0.20 * sharedActivities + 0.24 * sharedProjects + 0.08 * samePrimaryOrganization`. It becomes `1 - exp(-raw)`. Context cannot create a profile without an observed pair event.

Directional reciprocity is `2 * min(directionA, directionB) / (directionA + directionB)`. Direction-unknown and one-sided evidence receive no boost and no penalty. Channel diversity is `1` when both digital and analog evidence exist, otherwise `0`.

Final strength is:

`0.62 * currentActivation + 0.32 * historicalDepth + 0.03 * socialContext + 0.015 * reciprocity + 0.015 * channelDiversity`

The decomposition is retained on `RelationshipProfile`; the numeric final strength is not a default user-facing employee or relationship score.

## Cadence and state precedence

Expected cadence is the lower median of distinct positive interaction intervals when at least two intervals exist, bounded to `7–180` days. Otherwise it defaults to `60` days. Dormancy ratio is `daysSinceLast / expectedCadenceDays`.

State rules run in this order:

1. `RECONNECTED`: at least three distinct interactions, historical depth `>=0.28`, latest interaction within `30` days, and the prior gap is at least `max(120 days, 2 * prior expected cadence)`.
2. `DORMANT`: historical depth `>=0.28`, current activation `<=0.25`, at least `90` days elapsed, and dormancy ratio `>=1.80`.
3. `CLOSE`: strength `>=0.64` and current activation `>=0.60`.
4. `NEW`: relationship age `<=45` days with at most two distinct interaction timestamps.
5. `ACTIVE`: strength `>=0.35` and current activation `>=0.25`.
6. `WEAK`: every remaining observed pair.

These labels describe relationship evidence for the focal product user. They never rank people or imply employee value.

## Data confidence and missing coverage

Collection coverage is explicit input with independent digital and analog values. It never enters evidence, component, strength, cadence, or state formulas.

`dataConfidence = 0.60 * evidence-weighted mean event confidence + 0.25 * mean collection coverage + 0.15 * (1 - exp(-eventCount/3))`

Therefore missing analog coverage lowers only `dataConfidence`; a digital-only close relationship remains possible. Event confidence still affects both evidence and data confidence because it is a property of the observed source fact.

## Source and output boundary

- Input source remains immutable `InteractionEvent` plus explicit context and collection-coverage facts.
- Application callers must supply only context facts already authorized for the focal user; in particular, private declared activities must be excluded before creating `RelationshipContext`.
- `RelationshipProfile` is recalculable derived data with canonical `PersonPair`, `modelVersion`, and `calculatedAt`.
- Bulk derivation emits at most one normalized profile per observed pair and never creates self-pairs.
- No database, FastAPI, API schema, recommendation, graph projection, or persistence behavior is part of this model version.
