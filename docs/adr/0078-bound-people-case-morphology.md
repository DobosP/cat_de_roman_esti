# ADR-0078: Bound people case morphology

Date: 2026-08-13
Status: superseded-by ADR-0079

## Decision

Add only independently unanimous, normalized-unique genitive/dative forms of existing
people and role concepts to the shared typed resolver. Reject a form when one ordinary
surface has competing senses. V54 admits 48 forms from one fixed 50-surface funnel and
rejects `părintelui` and `părinților`; it adds no projection, node, edge, puzzle, game
record, hold disposition, or derived board.

Supersede ADR-0077 only where it fixed the resolver at 7,588 aliases and the fixture at its
V53 build identifier. Preserve its exact-alias rules, collision policy, topology, pack,
ranking payload, frozen derived boards, sessions, privacy, and owner-hold constraints.

## Context / why

Existing people and role concepts lacked ordinary case forms such as `omului`, `copiilor`,
`medicului`, and `cercetătorilor`. Two complete reviews agreed on exact owners for 48
forms. The noun _părinte_ ordinarily means either a parent or a cleric, so assigning
`părintelui` or `părinților` only to the family node would discard common religious senses.

## Consequences

The KG remains at 2,364 nodes, 9,217 edges, and 180 puzzles while aliases increase from
7,588 to 7,636. Contexto's projection remains at 473 terms across 26 domains. Pack bytes,
ranking rows, and the frozen 336-board derived payload remain unchanged; only KG-bound
wrapper metadata changes. Any further paradigm, polyseme, projection, topology, or board
wave needs a new finite review and test contract.
