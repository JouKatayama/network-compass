# Synthetic Data Specification v0.1

## Dataset families

- `demo`: deterministic 250-person consulting-like organization for UI/product development
- `edge_cases`: explicit relationship-model fixtures
- `stress`: later larger performance dataset

## Demo composition

Approximately: Technology/AI & Data 80, Strategy 35, Industry 45, Operations 30, HR/People 20, Global/Regional 25, Corporate/Other 15. Include multiple career levels, locations, communities, skills, and user-declared activities without treating seniority as network value.

About 20–30 people joined within 180 days, containing both graduate and experienced hires.

## Primary demo personas

- P001 Existing Employee: ~40 direct relationships with CLOSE/ACTIVE/WEAK/DORMANT mix and 40–60 reachable 2-hop people
- P201 Graduate New Joiner: ~30 days, cohort/team-heavy network
- P202 Experienced New Joiner: ~45 days, richer professional context but thin internal network

Hero fixtures: P018 dormant reconnect context, P067 2-hop potential via a mutual path, P102 reconnected after a dormant interval.

## Generation principles

Do not randomize RelationshipState directly. Generate people/context/project history and digital/analog InteractionEvents, then run the Relationship Engine. Use community-structured/small-world-like topology with cross-unit bridges. No interactions before a person's joinedAt.

Include digital-heavy, hybrid, analog-heavy, group-size variation, large-event co-presence, 1:1 interactions, dormant/reconnected temporal patterns, partial-data/confidence cases, missing avatar/long name cases.

Use deterministic seed and datasetVersion. Generator and Relationship Engine must be separate. Generate a validation report comparing expected scenarios to derived outputs.

## Required edge cases

Digital-only close; analog-only close; dormant; reconnected; same community/no interaction; same activity/no interaction; large event only; 1:1 lunch; one-sided digital; reciprocal; old project; missing analog; new joiner; no network; multiple org context; duplicate analog entry; long names; missing avatar.
