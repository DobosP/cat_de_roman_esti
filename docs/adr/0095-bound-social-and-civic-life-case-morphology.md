# ADR-0095: Bound social-and-civic-life case morphology

Date: 2026-08-26
Status: accepted

## Decision

Add only independently unanimous, normalized-unique, natural genitive/dative forms of
existing social-and-civic-life concepts to the shared typed resolver. Reject a form when
one ordinary surface has competing senses. V70 admits 46 forms from one fixed 50-surface
funnel and rejects legii, legilor, băncii, and băncilor; it adds no projection, node,
edge, puzzle, game record, hold disposition, ranking row, or derived board.

Supersede ADR-0092 only where it fixed the resolver at 8,306 aliases and the fixture at
its V68 build identifier. Preserve its exact-alias rules, collision policy, topology,
pack, frozen ranking/derived payloads, sessions, privacy, and owner bounds. Preserve
ADR-0093's Contexto reserve/filtered-shelf weighting and ADR-0094's navigation contracts.

## Context / why

Existing social and civic concepts lacked direct case forms such as apartamentelor,
referendumurilor, partidelor politice, and diasporelor. Two complete independent reviews
agreed on exact owners for 46 forms across 23 existing concepts, with no deferrals.

The bare forms legii and legilor can denote a juridical statute, scientific or natural
law, or a moral, religious, or customary rule, so they cannot bind only the existing
juridical Lege owner. The bare forms băncii and băncilor can denote the financial Bancă
owner, the distinct classroom desk/bench owner, or ordinary seating. Rejecting all four
keeps the shared resolver bounded without inventing a new sense or owner.

## Consequences

The KG remains at 2,364 nodes, 9,217 edges, and 180 puzzles while aliases increase from
8,306 to 8,352 under build fixture-v70-social-and-civic-life-morphology. Contexto's
projection remains at 473 terms across 26 domains. Pack bytes, ranking rows, the frozen
336-board derived payload, graph topology, and V69 selection behavior remain unchanged;
only alias-bearing records and KG-bound wrapper metadata change.

Typed Contexto guesses and otherwise-legal Lanț hops gain the 46 accepted forms. The four
rejected forms remain absent from exact, projection, and fuzzy resolution. Any further
paradigm, polyseme, projection, topology, or board wave needs a new finite review and test
contract.
