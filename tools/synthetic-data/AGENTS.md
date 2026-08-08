# Synthetic Data Tool Instructions

Applies to `tools/synthetic-data/**`.

- Deterministic generation with explicit seed/version.
- Generate facts/events, never make RelationshipState the source of truth.
- Never reuse real employee names/data or add unnecessary sensitive attributes.
- Keep generator logic separate from Relationship Engine logic.
- NC-003 owns implementation; NC-001 should create only any minimal tooling/package structure required by repository scaffolding.
