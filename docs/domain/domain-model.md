# Canonical Domain Model v0.1

## Data layers

### Fact/source

`Person`, `OrganizationUnit`, `Community`, `CommunityMembership`, `Activity`, `PersonActivity`, `Skill`, `PersonSkill`, `ProjectContext`, `ProjectParticipation`, `InteractionEvent`, `UserRelationshipFeedback`.

### Derived/materialized

`RelationshipProfile`, `Recommendation`, `RecommendationFeatureBreakdown`, `NetworkRampProfile`, `NetworkHealthProfile`.

### UI read models

`GraphProjection`, `PersonDetail`, `HomeView`, `NetworkRampView`.

Derived models are recalculable and must include a `modelVersion` where applicable.

## Core graph

The user-facing canonical relationship is:

`Person -[RELATES_TO derived from evidence]- Person`

`POTENTIAL` is **not** a relationship state; it describes a discover candidate without a direct meaningful relationship.

## Core enums

RelationshipState: `NEW | CLOSE | ACTIVE | WEAK | DORMANT | RECONNECTED`

HireType: `GRADUATE | EXPERIENCED | OTHER`

RecommendationType: `RECONNECT | DISCOVER | KEEP_IN_TOUCH | RAMP | WELCOME | INTRODUCE`

InteractionChannel: `DIGITAL | ANALOG`

InteractionSource: `SYSTEM | SELF_REPORTED | MUTUAL_CONFIRMED | INFERRED`

## Key invariants

- internal UUIDs are canonical; external IDs are separate mappings
- timestamps are UTC in storage/API
- no self relationships
- one normalized relationship pair per person pair
- user-declared Activity visibility is enforced server-side
- project/skill/community are relationship context, not primary graph protagonists

## Person fact attributes

In addition to canonical UUID, display name, join timestamp, hire type, organization mapping, and external identifiers, `Person` may carry optional `role`, `careerLevel`, `location`, and `avatarUrl` facts. These attributes support synthetic composition and UI identity states; career level must never be used as relationship value, node importance, or recommendation rank.
