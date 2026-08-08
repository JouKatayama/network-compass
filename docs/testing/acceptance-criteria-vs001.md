# Vertical Slice 001 Acceptance Criteria

## Backend/domain

- AC-B01 InteractionEvent can derive RelationshipProfile
- AC-B02 Relationship Engine unit-testable without DB/FastAPI
- AC-B03 Digital-only and analog-only supported
- AC-B04 old-strong/recent-none fixture -> DORMANT
- AC-B05 dormant + recent coffee -> RECONNECTED
- AC-B06 shared community/activity only -> no direct relationship
- AC-B07 modelVersion retained
- AC-B08 dataConfidence retained
- AC-B09 no self relationship
- AC-B10 unique normalized relationship pair

## Synthetic data

- AC-S01 fixed seed reproducible
- AC-S02 demo contains 250 people
- AC-S03 multiple organization clusters
- AC-S04 P001 ~40 direct relationships
- AC-S05 P001 mixed close/active/weak/dormant
- AC-S06 P018 dormant fixture
- AC-S07 P102 reconnected fixture
- AC-S08 P067 not direct
- AC-S09 P067 reachable as 2-hop via expected path
- AC-S10 no interaction before joinedAt
- AC-S11 validation report generated

## API

- AC-A01 `/api/v1/me/network` returns GraphProjection
- AC-A02 <=24 default 1-hop
- AC-A03 <=12 default 2-hop teaser
- AC-A04 current user always included
- AC-A05 no duplicate nodes
- AC-A06 visibility enforcement
- AC-A07 `/people/{id}` returns PersonDetail
- AC-A08 timeline included when factual history exists
- AC-A09 no fabricated potential-person history
- AC-A10 structured people search works
- AC-A11 consistent error envelope
- AC-A12 OpenAPI generated

## Graph

- AC-G01 focal user near center
- AC-G02 focal user visually distinct
- AC-G03 person-only primary nodes
- AC-G04 edge width reflects strength bucket
- AC-G05 opacity reflects activation bucket
- AC-G06 dormant dashed
- AC-G07 2-hop visually weaker
- AC-G08 hover summary
- AC-G09 click opens drawer
- AC-G10 selection does not globally re-layout
- AC-G11 expand <=8 nodes
- AC-G12 existing positions largely preserved
- AC-G13 zoom/pan/fit/center-on-me
- AC-G14 soft organization cluster support
- AC-G15 practical at ~37–60 visible nodes

## Person Detail/UX

Identity, natural-language relationship state, last contact, factual timeline, shared project/activity/community/mutual connection where present; no default relationship score; potential person prioritizes connection path; closing drawer preserves graph mental map; loading/error/missing-avatar/long-name states work; design tokens are semantic and relationship state is not color-only; search can select a person without graph-only interaction.
