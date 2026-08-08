# Graph Interaction & Visualization Specification v0.1

## Renderer and responsibilities

Sigma.js + Graphology render person nodes/relationship edges and handle camera/hit detection. React owns toolbar, search, drawer, filters, and overlays. Organization/community territories are overlays, not fake graph nodes.

## Projection limits

Default: 1 focal + <=24 primary 1-hop + <=12 2-hop teaser. Expand <=8. Soft visible limit 60, hard visible limit 80. Backend samples; frontend never receives the full organization graph.

## Layout

Use deterministic, cluster-aware force layout with focal gravity, relationship attraction, soft organization attraction, repulsion/collision avoidance. Organization is a **soft constraint**, not a hard container.

Preserve coordinates during a session and prefer deterministic seed across equivalent projections. Expansion only locally relaxes added nodes. Lens changes use bounded transition rather than global reshuffle.

## Visual semantics

- current user: slightly larger, purple accent, `あなた`
- node size: current relevance with narrow range; never seniority
- edge width: relationship-strength bucket
- edge opacity: current activation
- dormant: dashed + low opacity
- potential/2-hop: dotted/muted
- recommendation: purple outer ring
- organization/community: low-opacity soft territory
- relationship direction is visually undirected

## Semantic zoom

LANDSCAPE -> NETWORK -> PERSON -> DETAIL. Labels and role/context details appear progressively; the canvas never becomes a wall of profile cards. Full context remains in Person Detail.

## Performance/control

Avoid full clique edges; emphasize focal direct edges, selected-person edges, relevant cross edges, and active path edges. No 3D, continuous floating, decorative particles, excessive neon, or forced right-click interactions.
