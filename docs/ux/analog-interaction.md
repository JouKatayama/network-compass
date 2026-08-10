# Analog Interaction Capture v0.1 — Frozen

**Status:** Frozen v0.1 — NC-011 pre-implementation Review Gate approved on 2026-08-09.

## Product goal

Let the current user record one meaningful offline/social contact in at most 10 seconds, preserve it
as a factual `InteractionEvent`, and immediately refresh only that user's relationship with the
selected person. This extends the accepted VS001 loop from remembering/understanding a relationship
to learning from a contact that actually happened.

## Entry point and supported flow

NC-011 adds `接点を記録` to Person Detail for any person other than the current user, including a
two-hop/potential person. The selected person is fixed when the capture form opens.

1. Open Person Detail and choose `接点を記録`.
2. Choose exactly one interaction type.
3. Choose exactly one rough duration.
4. Accept the default occurrence time or optionally change it.
5. Review and save.

The form is rendered inside the existing Person Detail drawer rather than as a nested dialog. Back
returns to the unchanged detail state. Save success returns to refreshed Person Detail while keeping
the selected graph node and existing node coordinates stable.

## Frozen inputs

The UI sends only user-entered facts; it never sends source, confidence, current-person ID,
relationship state, strength, or evidence weight.

| UI label       | Canonical value |
| -------------- | --------------- |
| オフィスで会話 | `OFFICE_CHAT`   |
| コーヒー       | `COFFEE`        |
| ランチ         | `LUNCH`         |
| ディナー       | `DINNER`        |
| コミュニティ   | `COMMUNITY`     |
| アクティビティ | `ACTIVITY`      |
| その他         | `OTHER`         |

| UI label | Canonical value |
| -------- | --------------- |
| 少し     | `SHORT`         |
| しっかり | `MEDIUM`        |
| 長く     | `LONG`          |

Both selections are required and have no preselected default. `occurredAt` defaults to the current
time and can be changed to an aware date/time no more than 30 days in the past. The server is the
authority for current time, UTC normalization, and participant join-time validation.

Free text, contact notes, location, message content, photos, audio, GPS, and Bluetooth data are not
accepted. The earlier optional `また話したい` idea is deferred because it is user intent or
recommendation feedback, not interaction evidence.

## Interaction and relationship semantics

- One capture represents exactly two participants: the authenticated current user and the selected
  other person. Multi-person capture is deferred because one reporter must not assert relationships
  between third parties.
- The server creates an immutable `ANALOG` + `SELF_REPORTED` event with
  `conversationParticipantCount = 2`, the selected duration bucket, `createdByPersonId` equal to the
  current user, no initiator, and server-derived confidence `1.0`.
- Self-reporting does not mean the current user initiated the conversation; direction remains
  unknown.
- The accepted `relationship-v0.1.0` weights and formula do not change. The new fact is evaluated by
  that existing model and retains its existing model version.
- Event insertion and the canonical pair's `RelationshipProfile` upsert are one transaction.
  Unrelated profiles are not rebuilt or changed.
- The client invalidates/refetches the selected Person Detail and current network projection only
  after the committed response. It never predicts a relationship state optimistically.
- A potential person may become a direct `NEW` relationship. An old strong relationship may become
  `RECONNECTED` when the accepted relationship rules derive that result.

## Retry and duplicate boundary

Every form opening generates a UUID `clientRequestId` that is reused for retry. The server stores an
idempotency identity scoped to the current user using the event's existing source-system/external-ID
provenance fields. Repeating the same key and payload returns the original result without a second
event or recalculation; reusing the key with different content is a conflict.

NC-011 has no external or inferred write path. It therefore does not attempt heuristic matching of
similar events. A future connector/inferred-event issue must define immutable confirmation/linkage
and consolidated evidence before inferred and self-reported records can coexist; they must never be
blindly double-counted.

## UI states and accessibility

`DETAIL -> CAPTURE_EDITING -> CAPTURE_SAVING -> CAPTURE_SUCCESS -> REFRESHED_DETAIL`

From `CAPTURE_SAVING`, failures enter `CAPTURE_ERROR`; inputs and `clientRequestId` are retained and
retry returns to saving. The save control is disabled while pending. Safe errors never expose
upstream or database details.

On entry, focus moves to the capture heading. Type and duration groups use labelled native controls
with keyboard-visible focus. Validation errors are associated with their group. Escape/back returns
to Person Detail without saving and restores focus to `接点を記録`. Closing Person Detail retains the
accepted VS001 focus-restoration behavior. Success is announced through an `aria-live` status and is
not expressed by color alone.

The form must remain usable at 390 CSS pixels without horizontal overflow. The preselected-person
hero path requires at most four decisions/taps after entry: type, duration, optional occurrence-time
change, and save.

## Explicitly out of NC-011

- multi-person/group interaction capture
- editing or deleting an accepted event
- user relationship-correction kinds or formula effects
- `また話したい`, recommendation feedback, Home, Recommendations, Network Health, Network Ramp
- inferred/imported event reconciliation and real Teams/Outlook/Entra/HR connectors
- production SSO, notifications, offline synchronization, free-text notes, attachments
- relationship formula recalibration or a new relationship model version

## Review Gate decisions required

The human reviewer approved the 1:1-only boundary, seven types, required duration, 30-day occurrence
window, confidence `1.0`, drawer-contained flow, idempotency behavior, and the deferral of
intent/feedback and inferred-event reconciliation on 2026-08-09. This approval authorizes the NC-011
execution plan only; it does not authorize later slices.
