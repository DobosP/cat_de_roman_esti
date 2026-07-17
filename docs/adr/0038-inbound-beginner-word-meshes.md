# ADR-0038: Add inbound-reachable beginner word meshes

Date: 2026-07-18
Status: accepted

## Decision
Add eighteen first-class easy concepts for farm animals, clothing, and kitchen/table
items, with 60 collision-screened inflections and 54 explicit directed semantic edges.
Use three strongly connected local meshes with exactly two forward choices per new node.
Point all 18 legacy bridges into those meshes and no edge back to the legacy graph, so
every new target inherits mature inbound reachability without creating old-to-old paths.
Add no curated board or promotion.

## Context / why
The terms are concrete beginner vocabulary but had no honest resolver owner. Broad
synonyms would merge neighboring concepts, while the tempting `Cal` aliases `cai` and
`caii` collide with `căi` and `căii` after accent folding. An initial new-to-legacy
orientation left each new target reachable from only its five-to-seven-node local mesh,
below the Cald sau Rece target floor. Mixed or bidirectional bridges could instead alter
existing routes. Inbound-only bridges make the words viable targets while making each
mesh a one-way sink; eight extra local chords retain two meaningful outgoing choices.

## Consequences
The fixture becomes 2,234 nodes, 8,963 edges, 7,203 aliases, and 180 legacy puzzles;
combined eligible beginner probes resolve 269/269. Every V30 target is reachable from
2,221–2,223 concepts and has 161–1,632 guesses in its responsive one-to-five-hop band.
All old Contexto scores, 201 Lanț profiles, and 98 Alchimie profiles remain unchanged;
deterministic regeneration changes six gastronomy puzzles to exercise the kitchen mesh.
Both critique reports and the 794-record pack remain byte-identical. The public mobile
contract moves to `fixture-v30-farm-wardrobe-kitchen`; session TTL and caps do not change.
