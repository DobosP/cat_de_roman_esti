# ADR-0085: Bound home-care and maintenance case morphology

Date: 2026-08-14
Status: accepted

## Decision

Add only independently unanimous, normalized-unique, sense-qualified genitive/dative
forms of existing home-care and maintenance concepts to the shared typed resolver.
Reject a form when one ordinary surface has competing senses. V61 admits 48 forms from
one fixed 50-surface funnel and rejects `cheii` and `cheilor`; it adds no projection,
node, edge, puzzle, game record, hold disposition, or derived board.

Supersede ADR-0084 only where it fixed the resolver at 7,922 aliases and the fixture at
its V60 build identifier. Preserve its exact-alias rules, collision policy, topology,
pack, ranking payload, frozen derived boards, sessions, privacy, and owner-hold
constraints.

## Context / why

Existing household, hygiene, cleaning, workshop, garden, and bathroom concepts lacked
bounded forms such as `prosoapelor de baie`, `bureților pentru vase`, `ciocanului de
atelier`, `lopeților de grădină`, and `chiuvetelor de baie`. Two complete reviews agreed
on exact owners for 48 qualified forms. The noun _cheie_ also ordinarily denotes an
explanation or cipher key, a wrench or winding or tuning tool, a musical clef, an
architectural keystone, or a mountain gorge rather than only the metal object used with
a door lock. The two unqualified inflected surfaces cannot receive the door-key node as
their sole owner.

## Consequences

The KG remains at 2,364 nodes, 9,217 edges, and 180 puzzles while aliases increase from
7,922 to 7,970. Contexto's projection remains at 473 terms across 26 domains. Pack bytes,
ranking rows, and the frozen 336-board derived payload remain unchanged; only KG-bound
wrapper metadata changes. Any further paradigm, polyseme, projection, topology, or board
wave needs a new finite review and test contract.
