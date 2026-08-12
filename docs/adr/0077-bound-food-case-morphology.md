# ADR-0077: Bound food case morphology

Date: 2026-08-12
Status: superseded-by ADR-0078

## Decision

Add only independently unanimous, normalized-unique genitive/dative forms of existing
food concepts to the shared typed resolver. Reject a form when one ordinary surface has
competing senses. V53 admits 48 forms from one fixed 50-surface funnel and rejects `mesei`
and `meselor`; it adds no projection, node, edge, puzzle, game record, hold disposition,
or derived board.

Supersede ADR-0076 only where it fixed the resolver at 7,540 aliases and the fixture at its
V52 build identifier. Preserve its exact-alias rules, collision policy, topology, pack,
ranking payload, frozen derived boards, sessions, privacy, and owner-hold constraints.

## Context / why

Existing food concepts lacked ordinary case forms such as `mâncării`, `pâinii`, `merelor`,
and `piersicilor`. Two complete reviews agreed on exact owners for 48 forms. The noun
_masă_ ordinarily means either a meal or a piece of furniture, so assigning `mesei` or
`meselor` only to the food node would silently discard a common competing sense.

## Consequences

The KG remains at 2,364 nodes, 9,217 edges, and 180 puzzles while aliases increase from
7,540 to 7,588. Contexto's projection remains at 473 terms across 26 domains. Pack bytes,
ranking rows, and the frozen 336-board derived payload remain unchanged; only KG-bound
wrapper metadata changes. Any further paradigm, polyseme, projection, topology, or board
wave needs a new finite review and test contract.
