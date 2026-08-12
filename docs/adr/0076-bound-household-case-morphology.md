# ADR-0076: Bound household case morphology

Date: 2026-08-12
Status: accepted

## Decision

Add only independently unanimous, normalized-unique genitive/dative forms of existing
household concepts to the shared typed resolver. Reject a form when accent folding gives
its key a competing ordinary owner. V52 admits 48 forms from one fixed 50-surface funnel
and rejects `păturile` and `păturilor`; it adds no projection, node, edge, puzzle, game
record, hold disposition, or derived board.

Supersede ADR-0075 only where it fixed the resolver at 7,492 aliases and the fixture at its
V51 build identifier. Preserve its exact-alias/non-winning-projection separation, collision
rules, archive/live provenance boundary, topology, pack, ranking-payload, session, privacy,
and owner-hold constraints.

## Context / why

The everyday household inventory already contained common nominative/accusative forms but
often omitted equally ordinary case forms such as `camerei`, `ferestrelor`, and `scaunului`.
Two complete reviews agreed on 48 exact owners. Although `păturile` and `păturilor` are valid
forms of _pătură_, diacritic-insensitive normalization also makes them valid typed forms of
_pat_; assigning either key only to the blanket node would silently choose the wrong concept
for a common spelling.

## Consequences

The KG remains at 2,364 nodes, 9,217 edges, and 180 puzzles while aliases increase from
7,492 to 7,540. Contexto's projection remains at 473 terms across 26 domains. Pack bytes,
ranking rows, and the frozen 336-board derived payload remain unchanged; only KG-bound
wrapper metadata changes. Any further case paradigm, folded collision, projection, topology,
or board wave needs a new finite review and test contract.
