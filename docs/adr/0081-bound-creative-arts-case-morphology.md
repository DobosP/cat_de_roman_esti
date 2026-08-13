# ADR-0081: Bound creative-arts case morphology

Date: 2026-08-13
Status: accepted

## Decision

Add only independently unanimous, normalized-unique genitive/dative forms of existing
creative-arts concepts to the shared typed resolver. Reject a form when one ordinary
surface has competing senses. V57 admits 48 forms from one fixed 50-surface funnel and
rejects `tabloului` and `tablourilor`; it adds no projection, node, edge, puzzle, game
record, hold disposition, or derived board.

Supersede ADR-0080 only where it fixed the resolver at 7,730 aliases and the fixture at
its V56 build identifier. Preserve its exact-alias rules, collision policy, topology,
pack, ranking payload, frozen derived boards, sessions, privacy, and owner-hold
constraints.

## Context / why

Existing creative-arts concepts lacked ordinary forms such as `spectacolelor`,
`orchestrei`, `ceramicii populare`, `galeriilor de artă`, and `picturii românești`.
Two complete reviews agreed on exact owners for 48 forms. The noun _tablou_ also denotes
a table, chart, dashboard, or control panel rather than only a painted or drawn artwork.
Those two inflected surfaces cannot receive the artwork node as their sole owner.

## Consequences

The KG remains at 2,364 nodes, 9,217 edges, and 180 puzzles while aliases increase from
7,730 to 7,778. Contexto's projection remains at 473 terms across 26 domains. Pack bytes,
ranking rows, and the frozen 336-board derived payload remain unchanged; only KG-bound
wrapper metadata changes. Any further paradigm, polyseme, projection, topology, or board
wave needs a new finite review and test contract.
