# Person Detail v0.1

Purpose: answer **"この人誰だっけ？"** in seconds without leaving the graph.

## Connected-person order

1. Identity: photo/name/role/organization/location
2. Relationship summary: natural-language state, last contact, known duration when available
3. Why now (only when a recommendation exists; not required VS001)
4. Fact-based Relationship Timeline
5. Common context: mutual connections, activities, communities, skills, shared projects
6. Actions (later slices)

DORMANT displays `久しぶりのつながり`, not deterioration language. Numeric relationship strength is not shown by default.

## Potential person

Show `まだ直接話したことはありません` and prioritize the path/intermediate person plus visible common context. Do not fabricate a relationship timeline.

## Limited history

Say there is not enough known history and show only known facts. Never use an LLM to invent relationship events.
