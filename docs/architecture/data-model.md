# Canonical Data Model & Read Models v0.1

## Facts

Person, OrganizationUnit, Community/Membership, Activity/PersonActivity, Skill/PersonSkill, ProjectContext/Participation, InteractionEvent, UserRelationshipFeedback.

Person identity facts may include optional role, career level, location, and avatar URL. InteractionEvent may include an optional participant initiator for directional evidence. These attributes are facts and do not imply relationship strength, state, or rank.

## Derived

RelationshipProfile, Recommendation(+feature breakdown/feedback), NetworkingProfile, NetworkRampProfile, NetworkHealthProfile.

## GraphProjection

Required shape conceptually:

- focalPersonId
- nodes: GraphPersonNode[]
- edges: GraphRelationshipEdge[]
- clusters: GraphCluster[]
- meta: lens, hops, totalNetworkSize, visibleNodeCount, projectionVersion, generatedAt

GraphPersonNode: personId/displayName/shortRole/avatar, hop 0|1|2, clusterId, optional relationshipState, relevance, recommended/type, isPotential.

GraphRelationshipEdge: source/target, optional relationship state/strength/currentActivation, edgeType DIRECT|POTENTIAL_PATH, and presentation buckets for width/opacity/style.

## PersonDetail

Aggregates current-user-relative connection summary, mutual connections, common visible activities/communities/skills/shared projects, fact-based timeline, and optional recommendation/path context.

## Persistence invariants

Normalize person-pair order and make it unique. Interaction participants should be relational, not only JSON. Derived models must include calculation/model version where relevant.
