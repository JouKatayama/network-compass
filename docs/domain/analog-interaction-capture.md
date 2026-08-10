# Self-Reported Analog Interaction v0.1 — Frozen

**Status:** Frozen v0.1 — NC-011 pre-implementation Review Gate approved on 2026-08-09. The accepted
`InteractionEvent` and `relationship-v0.1.0` specifications remain unchanged.

## Command boundary

The application command receives:

- authenticated `currentPersonId` from the server boundary
- `otherPersonId`
- one analog interaction type: `OFFICE_CHAT`, `COFFEE`, `LUNCH`, `DINNER`, `COMMUNITY`, `ACTIVITY`,
  or `OTHER`
- one duration bucket: `SHORT`, `MEDIUM`, or `LONG`
- aware `occurredAt`
- UUID `clientRequestId`

It does not accept arbitrary participant IDs, channel, source, confidence, initiator, creator,
relationship fields, or model version from the client.

## Created fact

After validation, the command creates one canonical immutable `InteractionEvent`:

| Field                          | Value                                  |
| ------------------------------ | -------------------------------------- |
| `id`                           | server-generated UUID                  |
| `occurredAt`                   | request value normalized to UTC        |
| `channel`                      | `ANALOG`                               |
| `type`                         | validated request type                 |
| `participantIds`               | normalized current user + other person |
| `conversationParticipantCount` | `2`                                    |
| `durationBucket`               | validated request value                |
| `source`                       | `SELF_REPORTED`                        |
| `confidence`                   | `1.0`                                  |
| `initiatorPersonId`            | absent                                 |
| `createdByPersonId`            | current user                           |
| `createdAt`                    | server transaction time                |
| context IDs                    | absent in NC-011                       |
| `sourceSystem`                 | `network-compass-self-report`          |
| `externalEventId`              | `<currentPersonId>:<clientRequestId>`  |

The idempotency identity is `(currentPersonId, clientRequestId)`, represented by the existing unique
`(sourceSystem, externalEventId)` provenance fields. It is retry safety, not relationship evidence
and not a user-visible identifier.

## Validation invariants

- The other person exists and differs from the current user.
- Both participants joined on or before `occurredAt`.
- `occurredAt` is no earlier than 30 days before server time and not in the future. The stored
  `createdAt` therefore remains greater than or equal to stored `occurredAt`.
- The current user is always the creator and a participant.
- Unsupported digital/group types, unknown duration values, extra fields, and arbitrary confidence
  are rejected before persistence.
- A repeated idempotency identity with the same normalized payload is a replay. The original event
  and result are returned without creating or recalculating anything.
- A repeated identity with a different normalized payload is an idempotency conflict.

## Atomic derivation

Within one database transaction:

1. establish or validate the idempotency identity;
2. insert the event and its two relational participants;
3. load all facts and already-authorized relationship context needed for only the canonical pair;
4. derive the pair with the accepted `RelationshipEngine` at server transaction time;
5. upsert that pair's materialized `RelationshipProfile`;
6. commit and return the capture result.

Any failure rolls back both fact and derived changes. Existing event facts are never rewritten.
Unrelated profiles remain byte-for-byte unchanged. The command belongs to the application layer;
FastAPI routers perform HTTP translation only and SQLAlchemy repositories perform persistence only.

## Source and correction separation

A self-reported contact asserts that an interaction occurred; it does not assert the desired
relationship label or directly change relationship strength. `UserRelationshipFeedback` remains a
different fact family with intentionally deferred kinds/payload/formula semantics. NC-011 must not
populate it or alter `relationship-v0.1.0`.

No `INFERRED` event is created or accepted through NC-011. Before a future inferred/imported source
can coexist with capture, a separate frozen specification must define immutable event linkage and a
single consolidated evidence unit so confirmation cannot double-count one real interaction.
