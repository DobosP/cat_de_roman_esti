# ADR-0092: Bound Romanian-language and grammar case morphology

Date: 2026-08-24
Status: superseded-by ADR-0095

## Decision

Add only independently unanimous, normalized-unique, sense-qualified genitive/dative
forms of existing Romanian-language and grammar concepts to the shared typed resolver.
Reject a form when one ordinary surface has competing senses. V68 admits 48 forms from
one fixed 50-surface funnel and rejects `punctului` and `punctelor`; it adds no
projection, node, edge, puzzle, game record, hold disposition, or derived board.

Supersede ADR-0091 only where it fixed the resolver at 8,258 aliases and the fixture at
its V67 build identifier. Preserve its exact-alias rules, collision policy, topology,
pack, ranking payload, frozen derived boards, sessions, privacy, and owner-hold
constraints.

## Context / why

Existing Romanian-language and grammar concepts lacked bounded forms such as
`scrierilor alfabetice ale limbilor romanice`, `părților de vorbire în română`,
`persoanelor gramaticale ale verbului`, and `ortografiilor limbilor romanice`.
Two complete reviews agreed on exact owners for 48 qualified forms. The noun _punct_
also ordinarily denotes a punctuation mark, geometric point, place or position, score
or measurement unit, list item, viewpoint, or focus. The two reviewed
unqualified surfaces cannot receive the punctuation-mark node as their sole owner.

The accepted qualifiers distinguish language sounds from sounds generally,
alphabetic writing from authored works, grammatical person from a human individual,
and Romanian or Romance-language orthographies from correct writing generally. They
narrow existing concepts without adding a new sense or changing graph topology.

## Consequences

The KG remains at 2,364 nodes, 9,217 edges, and 180 puzzles while aliases increase from
8,258 to 8,306. Contexto's projection remains at 473 terms across 26 domains. Pack
bytes, ranking rows, and the frozen 336-board derived payload remain unchanged; only
KG-bound wrapper metadata changes. Any further paradigm, polyseme, projection,
topology, or board wave needs a new finite review and test contract.
