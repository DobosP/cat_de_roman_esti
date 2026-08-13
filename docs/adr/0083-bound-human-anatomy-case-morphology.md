# ADR-0083: Bound human-anatomy case morphology

Date: 2026-08-14
Status: accepted

## Decision

Add only independently unanimous, normalized-unique, human-qualified genitive/dative
forms of existing anatomy concepts to the shared typed resolver. Reject a form when one
ordinary surface has competing senses. V59 admits 48 forms from one fixed 50-surface
funnel and rejects `creierului` and `creierelor`; it adds no projection, node, edge,
puzzle, game record, hold disposition, or derived board.

Supersede ADR-0082 only where it fixed the resolver at 7,826 aliases and the fixture at
its V58 build identifier. Preserve its exact-alias rules, collision policy, topology,
pack, ranking payload, frozen derived boards, sessions, privacy, and owner-hold
constraints.

## Context / why

Existing anatomy concepts lacked bounded forms such as `inimilor umane`, `oaselor
umane`, `mâinilor umane`, `genunchiului uman`, and `sprâncenelor umane`. Two complete
reviews agreed on exact owners for 48 human-qualified forms. The noun _creier_ also
denotes mind or intelligence, an organizer or leader, a mountain interior, or a wheel
hub rather than only the anatomical organ. Its two unqualified inflected surfaces
cannot receive the organ node as their sole owner.

## Consequences

The KG remains at 2,364 nodes, 9,217 edges, and 180 puzzles while aliases increase from
7,826 to 7,874. Contexto's projection remains at 473 terms across 26 domains. Pack bytes,
ranking rows, and the frozen 336-board derived payload remain unchanged; only KG-bound
wrapper metadata changes. Any further paradigm, polyseme, projection, topology, or board
wave needs a new finite review and test contract.
