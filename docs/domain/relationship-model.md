# Relationship Strength & State Model v0.1

## Objective

Represent a continuous relationship using explainable evidence while separating current activation from historical depth. Shared interests/communities can strengthen context but cannot create a relationship by themselves.

## Event evidence

For interaction event `e`:

`E_e = B_e * G_e * D_e * C_e * T_e`

where type weight `B`, group-size factor `G`, duration factor `D`, source confidence `C`, and recency decay `T` are versioned configuration.

Recommended initial type-weight direction: online 1:1 / coffee / lunch / dinner / activity can provide stronger evidence than raw chat-active-day or large meeting, but these are calibratable evidence weights, not statements that one social behavior is universally better.

Group-size factor: approximately `1/sqrt(n-1)`. Recency uses type-dependent exponential half-lives. Raw message count should be aggregated to active day/session rather than counted per message.

## Components

Digital evidence: saturating transform of digital event evidence.

Analog evidence: saturating transform of analog event evidence.

Current Activation combines digital/analog evidence with a small cross-channel synergy.

Historical Depth uses much slower decay and can include past shared projects/communities/meaningful interactions.

Social Context can combine user-declared interest/activity similarity, community overlap, social context, and organizational proximity but is not sufficient to create a relationship.

Reciprocity compares directional interaction where meaningful. Channel Diversity is a small factor.

## Final strength

Use a base dominated by Current Activation and Historical Depth, then small bounded boosts from Social Context, Reciprocity, and Channel Diversity. Persist the decomposition, not only final strength.

## Required RelationshipProfile fields

`currentActivation`, `historicalDepth`, `digitalEvidence`, `analogEvidence`, `socialContext`, `reciprocity`, `channelDiversity`, `relationshipStrength`, `state`, `firstMeaningfulInteractionAt`, `lastMeaningfulInteractionAt`, `expectedCadenceDays`, `dormancyRatio`, `dataConfidence`, `modelVersion`, `calculatedAt`.

## Adaptive dormancy

Estimate expected cadence from historical meaningful interaction intervals when enough history exists. Conceptually:

`DormancyRatio = DaysSinceLastMeaningfulContact / ExpectedCadenceDays`

Use thresholds/configuration plus minimum elapsed periods to avoid noisy state changes. A strong-history/low-current relationship becomes DORMANT; a dormant relationship with recent meaningful interaction may become RECONNECTED.

## Critical invariants/tests

- digital-only close relationship can exist
- analog-only close relationship can exist
- same community/activity with zero meaningful interaction does not create a relationship
- large-event co-presence alone gives minimal evidence
- missing analog data lowers confidence, not relationship strength by fiat
- user correction is evidence and does not rewrite raw events
