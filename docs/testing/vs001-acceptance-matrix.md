# Vertical Slice 001 Final Acceptance Matrix

**Assessment:** GO recommended for accepting VS001 as the coherent internal-demo vertical slice.
This is not a production-launch approval and does not include production SSO or later product areas.

## Backend/domain

| AC | Status | Evidence |
|---|---|---|
| AC-B01 | PASS | Relationship Engine derives `RelationshipProfile` from factual `InteractionEvent` series in `test_relationship_engine.py`. |
| AC-B02 | PASS | Relationship Engine tests instantiate the domain service without DB or FastAPI. |
| AC-B03 | PASS | `test_digital_only_and_analog_only_can_both_be_close`. |
| AC-B04 | PASS | `test_adaptive_dormancy_and_reconnection_use_historical_cadence` derives DORMANT from old strong evidence. |
| AC-B05 | PASS | The same test derives RECONNECTED after recent factual coffee evidence. |
| AC-B06 | PASS | `test_shared_context_without_interaction_does_not_create_relationship`. |
| AC-B07 | PASS | Versioned configuration and `profile.model_version` assertions. |
| AC-B08 | PASS | Source/coverage confidence is retained in `data_confidence` assertions. |
| AC-B09 | PASS | `test_person_pair_rejects_self_relationship`. |
| AC-B10 | PASS | Canonical pair-order and bulk unique-pair tests. |

## Synthetic data

| AC | Status | Evidence |
|---|---|---|
| AC-S01 | PASS | `test_fixed_seed_is_byte_reproducible_and_seed_changes_output`. |
| AC-S02 | PASS | Demo composition test and Docker reset report exactly 250 people. |
| AC-S03 | PASS | Demo composition/projection tests cover multiple organization clusters. |
| AC-S04 | PASS | P001 fixture test asserts forty counterparts. |
| AC-S05 | PASS | Projection review asserts mixed CLOSE/ACTIVE/WEAK/DORMANT states. |
| AC-S06 | PASS | P018 is derived DORMANT and has factual shared-project history. |
| AC-S07 | PASS | P102 is derived RECONNECTED. |
| AC-S08 | PASS | P067 has no direct P001 relationship. |
| AC-S09 | PASS | P067 has only the expected P001→P010→P067 two-hop path. |
| AC-S10 | PASS | Validator rejection test covers interaction before `joinedAt`. |
| AC-S11 | PASS | Output writer test verifies the dataset summary and validation report. |

## API

| AC | Status | Evidence |
|---|---|---|
| AC-A01 | PASS | `/api/v1/me/network` integration test validates the production-shaped projection. |
| AC-A02 | PASS | Default one-hop count is server-bounded at 24. |
| AC-A03 | PASS | Default two-hop teaser count is server-bounded at 12. |
| AC-A04 | PASS | Current P001 is always the focal node; persona switching remains current-person-relative. |
| AC-A05 | PASS | API test asserts unique serialized person IDs. |
| AC-A06 | PASS | Current-person enforcement plus private-activity filtering and third-party metric omission tests. |
| AC-A07 | PASS | `/people/{id}` returns connected and potential `PersonDetail`. |
| AC-A08 | PASS | P018 detail contains factual project timeline items. |
| AC-A09 | PASS | P067 detail has an empty timeline and only permitted path/context. |
| AC-A10 | PASS | Structured search covers query, filters, cursor paging, visibility, and connection path. |
| AC-A11 | PASS | 400/401/404/422/500 cases share the safe request-identified error envelope. |
| AC-A12 | PASS | Checked-in OpenAPI and generated TypeScript drift checks pass. |

## Graph

| AC | Status | Evidence |
|---|---|---|
| AC-G01 | PASS | Deterministic layout fixes the focal person at `(0, 0)`. |
| AC-G02 | PASS | Graph transform labels `あなた` and gives the focal person distinct semantic styling. |
| AC-G03 | PASS | Graphology transform contains only projection person nodes. |
| AC-G04 | PASS | Direct edge width consumes the backend strength bucket. |
| AC-G05 | PASS | Edge opacity consumes the backend activation bucket. |
| AC-G06 | PASS | DORMANT edges are dashed and identified in the non-color legend. |
| AC-G07 | PASS | Two-hop nodes/edges are potential, dotted, muted, and labelled in the legend. |
| AC-G08 | PASS | Sigma enter/leave delegation and factual hover summary component test. |
| AC-G09 | PASS | Sigma click delegation opens the labelled Person Detail dialog. |
| AC-G10 | PASS | Selection changes reducers only; camera/layout preservation is unit- and browser-verified. |
| AC-G11 | PASS | Domain/API expansion tests assert at most eight additions per action. |
| AC-G12 | PASS | Expansion test proves every pre-existing coordinate remains exactly equal. |
| AC-G13 | PASS | Zoom, pan, Fit, and Center-on-me controller tests plus Docker smoke. |
| AC-G14 | PASS | Deterministic layout and browser evidence preserve soft organization clustering. |
| AC-G15 | PASS | 60-node layout/build/hop test stays under 1.5 s; Docker E2E renders the state under 8 s; an actual P001 server expansion reached 60 with responsive controls and no console errors. |

## Person Detail and UX

| Requirement | Status | Evidence |
|---|---|---|
| Identity and relationship memory | PASS | P018 hero shows identity, natural DORMANT wording, last contact, and factual shared-project timeline. |
| Potential connection priority | PASS | P067 prioritizes P001→P010→P067 and mutual P010 with no fabricated timeline. |
| No default numeric score | PASS | API serialization and drawer assertions omit strength/activation/confidence metrics. |
| Mental-map-preserving close | PASS | Exact coordinate/camera tests; Gate C approval; Esc closes and restores prior keyboard focus. |
| Loading/error/retry | PASS | Network, Person Detail, search implementation, and expansion cover safe loading/error/retry states; Docker E2E verifies network retry without leaking upstream detail. |
| Empty/partial data | PASS | Focal-only projection uses `あなたのNetworkはここから始まります`; limited profiles state only known facts and never calls missing evidence weak. |
| Missing avatar and long name | PASS | Initials fallback has an accessible label; long identity uses wrapping and is component-tested. |
| Semantic/non-color state | PASS | Semantic tokens plus solid/dashed/dotted treatments and a textual relationship legend. |
| Non-graph selection | PASS | Labelled ARIA combobox supports Arrow keys, Enter, pointer selection, active descendant, and focus restoration. |
| Responsive baseline | PASS | 390×844 drawer is 390 px wide with no horizontal overflow; controls and factual content remain usable. |

## End-to-end and visual evidence

- Docker/PostgreSQL Playwright passes five deterministic tests: shell/controls, P001→P018→P067 hero,
  safe network retry, 60-person partial projection, and API health.
- Review Gate C accepted the human relationship-memory feel and mental-map behavior.
- NC-010 browser inspection found no warning/error console entries and captured:
  - `docs/review-artifacts/NC-010-desktop-p067-focus.png`
  - `docs/review-artifacts/NC-010-responsive-p067.png`
  - `docs/review-artifacts/NC-010-60-person-network.png`
- WebGL pixel diffs remain intentionally avoided because they are renderer/platform brittle. Visual
  regressions are guarded by deterministic graph transforms/controller assertions, semantic E2E
  checks, and the checked-in human-review artifacts.

## Go/No-Go recommendation

**GO** for VS001 acceptance. All 48 named backend/synthetic/API/graph acceptance criteria pass, the
Person Detail/UX requirements pass, and the factual hero journey is green against the real Docker
stack. No unresolved privacy, architecture, contract, or product-coherence blocker remains.

Remaining boundaries are not VS001 failures: production SSO, user-correction semantics, later
Home/Recommendation/Analog/Network Health/Network Ramp slices, production observability, and
production-scale performance qualification require their own frozen scope and review.
