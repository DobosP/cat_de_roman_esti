# ADR-0088: Bound history and heritage case morphology

Date: 2026-08-21
Status: superseded-by ADR-0089

## Decision

Add only independently unanimous, normalized-unique, sense-qualified genitive/dative
forms of existing history and heritage concepts to the shared typed resolver. Reject a
form when one ordinary surface has competing senses. V64 admits 48 forms from one fixed
50-surface funnel and rejects `frontului` and `fronturilor`; it adds no projection,
node, edge, puzzle, game record, hold disposition, or derived board.

Supersede ADR-0087 only where it fixed the resolver at 8,066 aliases and the fixture at
its V63 build identifier. Preserve its exact-alias rules, collision policy, topology,
pack, ranking payload, frozen derived boards, sessions, privacy, and owner-hold
constraints.

## Context / why

Existing history and heritage concepts lacked bounded forms such as `bătăliilor
istorice`, `principatelor medievale`, `tratatelor diplomatice`, and `cetăților
medievale`. Two complete reviews agreed on exact owners for 48 qualified forms. The noun
_front_ also ordinarily denotes a formation line, an organized political or social
grouping, a mining work face, an architectural frontage, a meteorological boundary, and
a physical wavefront rather than only a military battle line. Its two unqualified
inflected surfaces cannot receive the history-front node as their sole owner.

The treaty forms use `diplomatic` rather than `istoric`: the qualifier names the
existing concept's treaty sense directly and keeps the pair isolated from ordinary
historical descriptions of documents or events.

## Consequences

The KG remains at 2,364 nodes, 9,217 edges, and 180 puzzles while aliases increase from
8,066 to 8,114. Contexto's projection remains at 473 terms across 26 domains. Pack
bytes, ranking rows, and the frozen 336-board derived payload remain unchanged; only
KG-bound wrapper metadata changes. Any further paradigm, polyseme, projection,
topology, or board wave needs a new finite review and test contract.
