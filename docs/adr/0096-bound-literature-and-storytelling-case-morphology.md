# ADR-0096: Bound literature-and-storytelling case morphology

Date: 2026-08-26
Status: superseded-by ADR-0097

## Decision

Add only independently unanimous, normalized-unique, natural genitive/dative forms of
existing literature-and-storytelling concepts to the shared typed resolver. Reject a form
when one ordinary surface has competing senses. V71 admits 48 forms from one fixed
50-surface funnel and rejects `intrigii` and `intrigilor`; it adds no projection, node,
edge, puzzle, game record, hold disposition, ranking row, or derived board.

Put those two rejected surfaces in the runtime resolver's finite fuzzy-deny set. They
remain eligible for non-playing advisory suggestions, but neither Contexto nor Lanț may
silently reinterpret them as the literary Intrigă owner through typo correction.

Supersede ADR-0095 only where it fixed the resolver at 8,352 aliases and the fixture at
its V70 build identifier. Preserve its exact-alias rules, inherited nonaccepted ledger,
collision policy, topology, pack, frozen ranking/derived payloads, sessions, privacy, and
owner bounds. Preserve ADR-0093's Contexto reserve/filtered-shelf weighting and ADR-0094's
navigation contracts.

Add one narrowly scoped exception to ADR-0022 and ADR-0062: their confidence threshold
does not actionably resolve these two reviewed polysemes. Preserve their thresholds,
confirmation flow, target-typo wins, advisory suggestions, and all behavior for every
other surface. The landed ADRs remain historical and unchanged.

## Context / why

Existing literary concepts lacked bounded forms such as `basmelor culte`,
`conflictelor narative`, `personajelor literare`, and `satelor din literatura română`.
Two complete independent reviews agreed on exact owners for 48 forms across 24 existing
concepts, with no deferrals or projection additions.

The bare forms `intrigii` and `intrigilor` can denote the narrative plot of a literary
work or an interpersonal, political, or conspiratorial scheme. Without a qualifier they
cannot bind only the existing literary Intrigă owner. Rejecting both keeps the shared
resolver bounded without inventing a new sense or owner.

Before V71, `intrigii` crossed the generic fuzzy threshold because it is one character
from the existing exact alias `intrigi`; `intrigilor` did not. An alias-only rejection
would therefore have been incomplete: one surface could still play the rejected owner.
The exact two-surface deny closes that path without weakening fuzzy typo help generally.

The accepted qualifiers distinguish narrative conflict from conflict generally, dramatic
plays from other pieces, literary titles and messages from other works, textual rows from
queues, the Romanian village as a literary motif from a geographic settlement, and the
mythical zmeu from a kite.

## Consequences

The alias-only application keeps the KG at 2,364 nodes, 9,217 edges, and 180 puzzles while
aliases increase from 8,352 to 8,400 under build
`fixture-v71-literature-and-storytelling-morphology`. Contexto's projection remains at
473 terms across 26 domains. Pack bytes, ranking rows, the frozen 336-board derived
payload, graph topology, sessions, and frontend behavior remain unchanged; only
alias-bearing records and KG-bound wrapper metadata change.

Typed Contexto guesses and otherwise-legal Lanț hops gain the 48 accepted forms. The two
rejected forms remain outside exact/projection resolution and cannot auto-play through
fuzzy correction; advisory suggestions remain available. Any further
paradigm, polyseme, projection, topology, or board wave needs a new finite review and test
contract.
