# Screen State & Interaction Specification v0.1

## My Network states

INITIAL -> LOADING -> NORMAL, with NODE_HOVER, NODE_SELECTED, NODE_EXPANDED, 2HOP_EXPANDED, SEARCH_ACTIVE, RECOMMENDATION_HIGHLIGHTED, LENS_CHANGED, EMPTY, PARTIAL_DATA, LARGE_NETWORK, ERROR.

### Selection

Node click opens the right Person Detail drawer, emphasizes direct edges/neighbors, fades unrelated context, and **does not globally re-center/re-layout** the graph. Minimal camera pan is allowed only if the drawer would obscure the selected node.

### Expansion

Add <=8 relevant adjacent people around the selected person. Preserve existing positions; use local/bounded relaxation only.

### 2-hop

Potential people are visually weaker than direct relationships. Selecting one highlights the path from current user through an intermediate person and prioritizes "how you are connected" in Person Detail.

### Search

Search does not replace the graph. Existing visible result -> focus/highlight. Non-visible relevant result -> add minimal path/context projection rather than the entire graph.

### Empty/partial data

Use neutral language such as "あなたのNetworkはここから始まります". Missing data is communicated as partial evidence, not a weak relationship.

## Person Detail states

CLOSED -> LOADING -> CONNECTED_PERSON (including dormant/active/reconnected/limited history) or POTENTIAL_PERSON or ERROR.

## Accessibility baseline

Main controls keyboard reachable, Esc closes drawer, zoom buttons exist, state is never expressed by color alone, missing avatar falls back cleanly, and search provides a non-graph route to person selection.
