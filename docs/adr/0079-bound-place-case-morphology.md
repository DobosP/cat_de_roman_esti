# ADR-0079: Bound place case morphology

Date: 2026-08-13
Status: accepted

## Decision

Add only independently unanimous, normalized-unique genitive/dative forms of existing
place and geography concepts to the shared typed resolver. Reject a form when one ordinary
surface has competing senses. V55 admits 48 forms from one fixed 50-surface funnel and
rejects `golfului` and `golfurilor`; it adds no projection, node, edge, puzzle, game record,
hold disposition, or derived board.

Supersede ADR-0078 only where it fixed the resolver at 7,636 aliases and the fixture at its
V54 build identifier. Preserve its exact-alias rules, collision policy, topology, pack,
ranking payload, frozen derived boards, sessions, privacy, and owner-hold constraints.

## Context / why

Existing place concepts lacked ordinary case forms such as `țării`, `pădurilor`,
`izvorului`, and `peninsulelor`. Two complete reviews agreed on exact owners for 48 forms.
The noun _golf_ ordinarily means either a geographic inlet or the sport, so assigning
`golfului` or `golfurilor` only to the geography node would discard a common competing
sense. The rejected forms were also checked against exact, projection, and fuzzy runtime
resolution so rejection remains effective in typed play.

## Consequences

The KG remains at 2,364 nodes, 9,217 edges, and 180 puzzles while aliases increase from
7,636 to 7,684. Contexto's projection remains at 473 terms across 26 domains. Pack bytes,
ranking rows, and the frozen 336-board derived payload remain unchanged; only KG-bound
wrapper metadata changes. Any further paradigm, polyseme, projection, topology, or board
wave needs a new finite review and test contract.
