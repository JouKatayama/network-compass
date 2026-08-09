# Privacy & Security Architecture v0.1

## Privacy boundary

The application returns only information the current user is permitted to view. Visibility checks happen before serialization. The frontend is not a security boundary.

An individual user's relationship graph is personal; no MVP admin endpoint may fetch another user's graph.

For 2-hop navigation, return only the minimal path/context required. Do not expose arbitrary A↔B private relationship metrics between two third parties.

NC-006 enforces this in the internal projection serializer: a two-hop node contains only selected
person identity plus at most three mutual-person/shortest-path IDs, and a third-party path edge never
contains relationship state, strength, activation, or evidence decomposition. Numeric path quality is
used only inside bounded candidate generation and is not serialized.

## Data minimization

Never ingest/store message/email bodies, transcripts, private audio, GPS, or Bluetooth proximity for this product. Use metadata/evidence events only.

Activities/interests are user-declared; respect PRIVATE/NETWORK/ORGANIZATION visibility. Avoid unnecessary sensitive attributes in synthetic and production schemas.

## Application security baseline

- secrets excluded from git; `.env.example` contains names only
- strict server-side validation
- SQL parameterization/ORM
- restricted CORS for local/prod environments
- structured logs without personal graph content or secrets
- request IDs and safe error envelopes
- dependency lockfiles and CI checks

Production SSO is explicitly out of NC-001; development persona switching must remain development-only.
