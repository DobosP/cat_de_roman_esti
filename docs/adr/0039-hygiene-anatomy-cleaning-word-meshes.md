# ADR-0039: Add hygiene, anatomy, and cleaning word meshes

Date: 2026-07-18
Status: accepted

## Decision
Add seventeen first-class easy concepts for personal hygiene, lower-limb anatomy, and
household cleaning, with 61 collision-screened inflections and 51 explicit directed
semantic edges. Use three strongly connected local meshes with exactly two outgoing
choices per new node. Point one legacy bridge into every new concept and no edge back to
the legacy graph. Keep bare neighboring senses such as `periuță`, `pastă`, `burete`, and
all accent-folded forms of `mătură` outside the new ownership. Add no board or promotion.

## Context / why
These concrete beginner terms had no honest resolver owner. Qualifying the dental and
dishwashing concepts avoids collapsing them into broader neighboring senses, while
ordinary inflections remain useful input aliases. Isolated spokes would make the terms
poor Cald sau Rece targets, and new-to-legacy or bidirectional bridges could change old
shortest paths. Inbound-only bridges give each mesh the mature graph's reachability while
the one-way sink cut preserves every old-to-old route.

## Consequences
The fixture becomes 2,251 nodes, 9,014 edges, 7,264 aliases, and 180 legacy puzzles;
combined eligible beginner probes resolve 286/286. Every V31 target is reachable from
2,221–2,222 concepts and has 196–1,397 guesses in its responsive one-to-five-hop band.
All old Contexto, Lanț, and Alchimie profiles remain unchanged; deterministic regeneration
changes six science/everyday-life legacy puzzles. Both critique reports and the
794-record pack remain byte-identical. The public mobile contract moves to
`fixture-v31-hygiene-lower-limb-cleaning`; session TTL and caps do not change.
