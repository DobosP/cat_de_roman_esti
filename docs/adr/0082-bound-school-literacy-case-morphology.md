# ADR-0082: Bound school/literacy case morphology

Date: 2026-08-13
Status: superseded-by ADR-0083

## Decision

Add only independently unanimous, normalized-unique genitive/dative forms of existing
school, language, and literacy concepts to the shared typed resolver. Reject a form when
one ordinary surface has competing senses. V58 admits 48 forms from one fixed 50-surface
funnel and rejects `cărții` and `cărților`; it adds no projection, node, edge, puzzle,
game record, hold disposition, or derived board.

Supersede ADR-0081 only where it fixed the resolver at 7,778 aliases and the fixture at
its V57 build identifier. Preserve its exact-alias rules, collision policy, topology,
pack, ranking payload, frozen derived boards, sessions, privacy, and owner-hold
constraints.

## Context / why

Existing school and literacy concepts lacked ordinary forms such as `școlilor`,
`dicționarelor`, `propoziției`, `paginilor`, and `liceelor`. Two complete reviews agreed
on exact owners for 48 forms; qualifiers bound otherwise broad forms to their intended
school or literary senses. The noun _carte_ also denotes a playing card or official
document rather than only a book. Those two inflected surfaces cannot receive the book
node as their sole owner. An exact `paginilor` alias also replaces its prior fuzzy
misroute to the bread node without changing fuzzy policy.

## Consequences

The KG remains at 2,364 nodes, 9,217 edges, and 180 puzzles while aliases increase from
7,778 to 7,826. Contexto's projection remains at 473 terms across 26 domains. Pack bytes,
ranking rows, and the frozen 336-board derived payload remain unchanged; only KG-bound
wrapper metadata changes. Any further paradigm, polyseme, projection, topology, or board
wave needs a new finite review and test contract.
