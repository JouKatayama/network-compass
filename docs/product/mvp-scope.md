# MVP Scope v0.1 — Frozen

## Hypothesis to prove

Visualizing a person's internal network can increase meaningful interactions that otherwise would not have happened.

## P0 product scope

- Home: three people to remember / relevant network updates / short insight (later vertical slice)
- My Network: focal-user graph, <=24 1-hop, <=12 2-hop teaser, organization soft clusters, search, select/expand
- Person Detail: relationship state, last contact, fact-based timeline, shared contexts, mutual connections, why-now context when applicable
- Analog Interaction Capture: fast manual interaction entry and relationship refresh (later vertical slice)
- New Joiner Network Ramp: graduate and experienced hires (later vertical slice)

## Vertical Slice 001 scope

Only:

- deterministic synthetic facts
- relationship derivation
- persistence/read path
- personal graph projection
- `GET /api/v1/me/network`
- `GET /api/v1/people/{personId}`
- `GET /api/v1/people/search`
- `/network` graph UI
- Person Detail drawer
- 2-hop discovery

## Explicitly out of MVP / initial implementation

- real Teams/Outlook/Entra/HR integrations
- Neo4j or other graph DB
- graph ML / GNN / learning-to-rank
- admin relationship dashboard
- staffing/project recommendation
- opportunity/sales pipeline
- full production SSO
- native mobile app
- push notifications
- Kafka/Redis/Kubernetes/GraphQL/vector DB/agent framework
