# ADR-0043: Lanț uses visible local route corridors

Date: 2026-07-18
Status: accepted

## Decision

Keep ADR-0016's strict curated-content gate: every approved board still needs at least
two shortest-path first hops and width two at every intermediate shortest layer. Add a
private, directed near-shortest corridor containing concepts that can sit on a route no
longer than par + 2. Prefer easy boards with at least three corridor first hops and
width-three intermediate layers, but fall back to the existing playable pool when a
filtered category is thin.

At each position, expose at most six ID-free local choices as only a label and concise
relation. Choose up to three unmarked corridor hops, reserve room for target-reachable
safe detours, exclude visited/dead-end suggestions, deduplicate normalized homonyms,
and softly penalize live degree above 20. Never backfill a fourth corridor hop when no
safe detour exists; such a position may show fewer than four rather than leak more of the
route web. Recompute the private menu when a label is submitted so a unique visible
homonym binds to its authored unvisited node without adding an ID to the payload. Never
serialize corridor membership, route budget, or a complete route. Typing any other real
direct neighbour remains legal.

Escalate voluntary hints at an unchanged position: first reveal only a relation
direction, second name at most two useful local alternatives, and third reveal one
shortest-path hop. If shortest continuations are already on the walked chain, guide an
unvisited target-reachable local route when one remains; only otherwise expose an explicit
backtrack stage that points to free undo. Dead ends use that same recovery. The three-step
counter is capped and resets on every real move or undo. This
supersedes only decision 2 of ADR-0022. Its confident typo auto-accept and dead-end
warning remain accepted. Free undo, score math, daily/seed determinism, operation IDs,
two-hour TTL, and the 1,000-session cap are unchanged.

## Context / why

A technically correct typed-only ladder asks beginners to search the whole vocabulary,
while a strict shortest-path diamond makes many boards feel like a narrow hidden rail.
Publishing all neighbours or the corridor would replace navigation with route reading;
showing only correct hops would leak which branch is on track. English wiki-navigation
games instead make a bounded local action space visible while leaving the global route
unknown. The ID-free mixed menu preserves that uncertainty and still teaches why each
suggestion is legal. Generic hubs remain available for sparse graphs, but should not
dominate every menu merely because they connect to many concepts.

## Consequences

The browser has a two-column phone grid and three-column wide grid of immediately
playable relation chips, plus free typing below it. Coarse-pointer entry no longer
forces the keyboard open. Mobile clients may rely on local choices carrying no concept
ID; only the third explicit hint may reveal one hop ID. Backend tests pin corridor
bounds, the three-corridor quota, deterministic homonym binding, hub ranking, unrestricted
off-menu moves, secrecy, hint stages, forward/revisit recovery, bounded counter state,
undo, and score preservation. Frontend tests pin the typed contract, responsive controls,
count-neutral alternative copy, live status, and tap actions.

Directed route profiles share one graph traversal and a service-scoped, bounded cache;
representative warm board creation remains within a single-digit millisecond budget.
