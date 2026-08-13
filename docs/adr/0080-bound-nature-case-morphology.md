# ADR-0080: Bound nature case morphology

Date: 2026-08-13
Status: accepted

## Decision

Add only independently unanimous, normalized-unique genitive/dative forms of existing
animal, plant, weather, and basic-science concepts to the shared typed resolver. Reject a
form when one ordinary surface has competing senses. V56 admits 46 forms from one fixed
50-surface funnel and rejects `peștelui`, `peștilor`, `corpului`, and `corpurilor`; it adds
no projection, node, edge, puzzle, game record, hold disposition, or derived board.

Supersede ADR-0079 only where it fixed the resolver at 7,684 aliases and the fixture at its
V55 build identifier. Preserve its exact-alias rules, collision policy, topology, pack,
ranking payload, frozen derived boards, sessions, privacy, and owner-hold constraints.

## Context / why

The initial animal-only inventory found only 19 genuine animal concepts, too few for the
fixed 25-concept funnel without inventing nodes or misclassifying cultural works. The
nearest coherent boundary is nature and basic natural science, whose existing concepts
lacked ordinary forms such as `animalelor`, `păsării`, `zăpezilor`, `moleculei`, and
`vaccinurilor`. Two complete reviews agreed on exact owners for 46 forms. _Pește_ also
ordinarily denotes a procurer, while its plural names the Pisces constellation and zodiac
sign. The noun _corp_ denotes an anatomical or physical body, an organized professional
or military group, and a geometric solid. Those four surfaces cannot receive one owner.

## Consequences

The KG remains at 2,364 nodes, 9,217 edges, and 180 puzzles while aliases increase from
7,684 to 7,730. Contexto's projection remains at 473 terms across 26 domains. Pack bytes,
ranking rows, and the frozen 336-board derived payload remain unchanged; only KG-bound
wrapper metadata changes. Any further paradigm, polyseme, projection, topology, or board
wave needs a new finite review and test contract.
