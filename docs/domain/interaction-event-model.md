# Interaction Event Model v0.1

`InteractionEvent` is a primary relationship-evidence fact and is conceptually immutable.

## Fields

- id
- occurredAt
- channel: DIGITAL/ANALOG
- type: TEAMS_CHAT, EMAIL, ONLINE_1ON1, GROUP_MEETING, OFFICE_CHAT, COFFEE, LUNCH, DINNER, COMMUNITY, ACTIVITY, OTHER
- participantIds (>=2)
- conversationParticipantCount when relevant
- durationBucket: SHORT/MEDIUM/LONG when known
- optional activityId/communityId/projectId
- source
- confidence
- optional initiatorPersonId for directional evidence when the source provides it
- createdByPersonId for self-reported analog events
- sourceSystem / externalEventId when applicable
- createdAt

When `initiatorPersonId` is present it must be one of `participantIds`. It records event direction only; absence means direction is unknown rather than reciprocal.

## Evidence principles

Co-presence is not equivalent to conversation. Large event attendance alone should have near-zero relationship evidence. An explicitly confirmed 1:1 conversation inside a large event uses the actual conversation group size.

Do not store message/email body, transcript, audio, GPS, or Bluetooth proximity.

## Analog capture

The intended later UX is <=10 seconds: select person(s) -> type/context -> rough depth -> save. Manual confirmation may strengthen an inferred event rather than creating a duplicate.

The NC-011 draft narrows its first write slice to the authenticated current user plus exactly one
other person and is specified in `analog-interaction-capture.md`. It permits no inferred source, so
inferred/self-reported consolidation remains blocked until a later immutable-linkage specification
exists.
