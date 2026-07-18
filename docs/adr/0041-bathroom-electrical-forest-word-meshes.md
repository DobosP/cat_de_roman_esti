# ADR-0041: Add bathroom, electrical, and forest word meshes

Date: 2026-07-18
Status: accepted

## Decision
Add eighteen first-class easy concepts for bathroom fixtures and supplies, qualified
household electrical equipment, and familiar forest animals, with 67 collision-screened
inflections and 54 explicit directed semantic edges. Use three strongly connected local
meshes with exactly two outgoing choices per new node. Point one legacy bridge into every
new concept and no edge back to the mature graph. Keep broad `Cadă`, `Toaletă`, `Priză`,
`Întrerupător`, `Prelungitor`, and `Cablu` senses outside the new ownership. Add no board
or promotion.

## Context / why
These concrete beginner terms had no honest resolver owner. Ordinary inflections make
input forgiving, while qualified bathroom and electrical labels avoid verb-shaped or
multi-domain bare senses after accent folding. Functional plumbing and power-flow links,
plus habitat, food, and predator links, give more useful choices than isolated spokes or
generic `related_to` edges. Edges from a new mesh back into the mature graph were rejected
because they could shorten established game routes.

## Consequences
The fixture becomes 2,287 nodes, 9,122 edges, 7,400 aliases, and 180 legacy puzzles;
combined eligible beginner probes resolve 322/322. Every new target is reachable from
2,222–2,228 concepts and has 322–1,413 responsive guesses within five hops. Only the
computed degree changes on ten legacy bridge anchors. Deterministic rebuilding changes
eight stored hard puzzles while retaining all 180 validated IDs. Both critique reports,
all legacy Contexto, Lanț, and Alchimie profiles, and the 794-record pack remain unchanged;
the public mobile contract moves to `fixture-v33-bathroom-electric-forest`. Session TTL
and caps do not change.
