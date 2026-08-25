# ADR-0091: Bound online-content and social-media case morphology

Date: 2026-08-24
Status: superseded-by ADR-0092

## Decision

Add only independently unanimous, normalized-unique, sense-qualified genitive/dative
forms of existing online-content and social-media concepts to the shared typed
resolver. Reject a form when one ordinary surface has competing senses. V67 admits 48
forms from one fixed 50-surface funnel and rejects `fluxului` and `fluxurilor`; it adds
no projection, node, edge, puzzle, game record, hold disposition, or derived board.

Supersede ADR-0090 only where it fixed the resolver at 8,210 aliases and the fixture at
its V66 build identifier. Preserve its exact-alias rules, collision policy, topology,
pack, ranking payload, frozen derived boards, sessions, privacy, and owner-hold
constraints.

## Context / why

Existing online-content and social-media concepts lacked bounded forms such as
`comentariilor publice de pe internet`, `algoritmilor platformelor sociale`,
`audiențelor românești online`, and `capturilor de ecran salvate`. Two complete reviews
agreed on exact owners for 48 qualified forms. The noun _flux_ also ordinarily denotes
an ocean or sea tide and figurative surge, a physical, technological, or information
flow, and the continuously updated feed of posts and clips on a social platform. The
two reviewed unqualified surfaces cannot receive the online-feed node as their sole
owner.

The accepted qualifiers distinguish public internet comments from commentary in other
media, platform algorithms from algorithms generally, saved screen captures from the
act of capturing, and Romanian online audiences from audiences generally. They narrow
existing concepts without adding a new sense or changing graph topology.

## Consequences

The KG remains at 2,364 nodes, 9,217 edges, and 180 puzzles while aliases increase from
8,210 to 8,258. Contexto's projection remains at 473 terms across 26 domains. Pack
bytes, ranking rows, and the frozen 336-board derived payload remain unchanged; only
KG-bound wrapper metadata changes. Any further paradigm, polyseme, projection,
topology, or board wave needs a new finite review and test contract.
