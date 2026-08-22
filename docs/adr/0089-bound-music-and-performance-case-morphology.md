# ADR-0089: Bound music and performance case morphology

Date: 2026-08-22
Status: accepted

## Decision

Add only independently unanimous, normalized-unique, sense-qualified genitive/dative
forms of existing music and performance concepts to the shared typed resolver. Reject a
form when one ordinary surface has competing senses. V65 admits 48 forms from one fixed
50-surface funnel and rejects `notei` and `notelor`; it adds no projection, node, edge,
puzzle, game record, hold disposition, or derived board.

Supersede ADR-0088 only where it fixed the resolver at 8,114 aliases and the fixture at
its V64 build identifier. Preserve its exact-alias rules, collision policy, topology,
pack, ranking payload, frozen derived boards, sessions, privacy, and owner-hold
constraints.

## Context / why

Existing music and performance concepts lacked bounded forms such as `cântăreților
pop`, `scenelor principale de festival`, `albumelor muzicale`, and `căștilor audio`.
Two complete reviews agreed on exact owners for 48 qualified forms. The noun _notă_
also ordinarily denotes a school or examination grade, a brief written record, an
annotation, a bill or accounting statement, a diplomatic communication, and a
characteristic nuance or trait rather than only a musical pitch or notation sign. Its
two unqualified inflected surfaces cannot receive the music-note node as their sole
owner.

The reviewed spellings follow the direct paradigms: `DJ-lor`, not `DJ-ilor`, is the
genitive/dative plural; the musical plural yields `albumelor`; and _cască_ yields
`căștii` and `căștilor`. `Scenă principală de festival` names the existing physical
stage sense without admitting the separate music-ecosystem sense of _scenă muzicală_.

## Consequences

The KG remains at 2,364 nodes, 9,217 edges, and 180 puzzles while aliases increase from
8,114 to 8,162. Contexto's projection remains at 473 terms across 26 domains. Pack
bytes, ranking rows, and the frozen 336-board derived payload remain unchanged; only
KG-bound wrapper metadata changes. Any further paradigm, polyseme, projection,
topology, or board wave needs a new finite review and test contract.
