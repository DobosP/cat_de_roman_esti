# ADR-0086: Bound transport and mobility case morphology

Date: 2026-08-21
Status: accepted

## Decision

Add only independently unanimous, normalized-unique, sense-qualified genitive/dative
forms of existing transport and mobility concepts to the shared typed resolver. Reject
a form when one ordinary surface has competing senses. V62 admits 48 forms from one
fixed 50-surface funnel and rejects `portului` and `porturilor`; it adds no projection,
node, edge, puzzle, game record, hold disposition, or derived board.

Supersede ADR-0085 only where it fixed the resolver at 7,970 aliases and the fixture at
its V61 build identifier. Preserve its exact-alias rules, collision policy, topology,
pack, ranking payload, frozen derived boards, sessions, privacy, and owner-hold
constraints.

## Context / why

Existing rail, road, air, water, terminal, route, and travel concepts lacked bounded
forms such as `trenurilor de călători`, `autobuzului urban`, `gărilor feroviare`,
`canalelor navigabile`, and `pașapoartelor de călătorie`. Two complete reviews agreed
on exact owners for 48 qualified forms. The noun _port_ also ordinarily denotes the
act or right of carrying, conduct or bearing, traditional clothing, and a computer or
USB interface rather than only a harbor facility or port city. The two unqualified
inflected surfaces cannot receive the harbor node as their sole owner.

## Consequences

The KG remains at 2,364 nodes, 9,217 edges, and 180 puzzles while aliases increase from
7,970 to 8,018. Contexto's projection remains at 473 terms across 26 domains. Pack bytes,
ranking rows, and the frozen 336-board derived payload remain unchanged; only KG-bound
wrapper metadata changes. Any further paradigm, polyseme, projection, topology, or board
wave needs a new finite review and test contract.
