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
- createdByPersonId for self-reported analog events
- sourceSystem / externalEventId when applicable
- createdAt

## Evidence principles

Co-presence is not equivalent to conversation. Large event attendance alone should have near-zero relationship evidence. An explicitly confirmed 1:1 conversation inside a large event uses the actual conversation group size.

Do not store message/email body, transcript, audio, GPS, or Bluetooth proximity.

## Analog capture

The intended later UX is <=10 seconds: select person(s) -> type/context -> rough depth -> save. Manual confirmation may strengthen an inferred event rather than creating a duplicate.
