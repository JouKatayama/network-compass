# Recommendation Model v0.1

## Deterministic first

v0.1 ranking is rule-based and explainable. Do not use an LLM or opaque ML for ranking.

## Recommendation categories

RECONNECT, DISCOVER, KEEP_IN_TOUCH, RAMP, WELCOME, INTRODUCE.

## Reason-code priority

1. STRONG_PAST_RELATIONSHIP
2. BECOMING_DORMANT
3. COMMON_ACTIVITY
4. COMMON_COMMUNITY
5. MUTUAL_CONNECTION
6. ORG_PROXIMITY
7. RECENT_PERSON_CHANGE
8. SKILL_COMMONALITY
9. PROFESSIONAL_RELEVANCE

Social/activity reasons only use user-declared visible data.

## Reconnect

Conceptually favors high historical depth, low current activation, relevant timing/context, and confidence. Default recommendation cooldown is about 28 days, with different suppression for `later`, `not now`, and explicit reduce-similar feedback.

## Discover

Requires no direct meaningful relationship. Uses commonality, accessibility, contextual relevance, networking preference, and 2-hop introduction paths. Introduction through a mutual connection should be preferred over cold outreach when appropriate.

## Networking preferences

Continuous axes: explorationPreference, depthPreference, interactionStyle, workSocialBalance. Initial onboarding values may adapt from user feedback/behavior but user adjustment has priority.

## New Joiner Ramp

Graduate and experienced hires share the same foundation but use different initial priors. Graduate ranking emphasizes accessibility/role-model fit; experienced ranking can raise professional/context fit and network-gap fill earlier. Hire type never permanently determines behavior.
