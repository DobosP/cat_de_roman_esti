# ADR-0087: Bound film and television case morphology

Date: 2026-08-21
Status: accepted

## Decision

Add only independently unanimous, normalized-unique, sense-qualified genitive/dative
forms of existing film and television concepts to the shared typed resolver. Reject a
form when one ordinary surface has competing senses. V63 admits 48 forms from one fixed
50-surface funnel and rejects `rolului` and `rolurilor`; it adds no projection, node,
edge, puzzle, game record, hold disposition, or derived board.

Supersede ADR-0086 only where it fixed the resolver at 8,018 aliases and the fixture at
its V62 build identifier. Preserve its exact-alias rules, collision policy, topology,
pack, ranking payload, frozen derived boards, sessions, privacy, and owner-hold
constraints.

## Context / why

Existing screen-production concepts lacked bounded forms such as `actorilor de film`,
`scenariului de film`, `subtitrărilor de film`, and `coloanelor sonore de film`. Two
complete reviews agreed on exact owners for 48 qualified forms. The noun _rol_ also
ordinarily denotes a function or mission, a court docket, a fiscal or maritime
register, and a rolled collar rather than only a performed character. Its two
unqualified inflected surfaces cannot receive the film-role node as their sole owner.

Bare `canalului` and `canalelor` were not selected as the rejected pair: V62 already
binds qualified navigable-channel forms to a geography owner, while the fixture also
contains a television-channel owner. Reusing that lemma would create a direct
cross-owner interaction; `rol` leaves the accepted V63 batch and all inherited owner
bindings isolated.

## Consequences

The KG remains at 2,364 nodes, 9,217 edges, and 180 puzzles while aliases increase from
8,018 to 8,066. Contexto's projection remains at 473 terms across 26 domains. Pack
bytes, ranking rows, and the frozen 336-board derived payload remain unchanged; only
KG-bound wrapper metadata changes. Any further paradigm, polyseme, projection,
topology, or board wave needs a new finite review and test contract.
