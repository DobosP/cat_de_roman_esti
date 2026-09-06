# ADR-0108: Add bounded flour ingredient associations

Date: 2026-09-06
Status: accepted

## Context

The V75 review rejected Cozonac, Pâine de casă and Clătite as new Contexto targets:
the familiar ingredient guess `făină` was four, four and six directed hops away.
V76 corrected the separate Paște/Paste input collision and left these graph gaps
for an independently reviewed content wave.

## Decision

Add exactly two non-distractor, directed `part_of` links from the existing Făină
node to Cozonac and Clătite. Defer the Pâine de casă link: its recipe fact is
valid, but it makes Făină warm for Stiloul cu rezervor through the existing
Pâine de casă → Lapte și corn → Stiloul cu rezervor route. Repairing that
misleading route needs a separate review. The Romanian edge label is `ingredient pentru`;
strength 0.97 is an editorial association weight, following the bounded V25
enrichment convention, rather than a recipe quantity or measured probability.
Recipe evidence must support each association independently. Do not add reverse
edges, aliases, nodes or game records as part of this wave.

Use the existing rollback-safe `apply_common_words_v24.py` transaction with the
V77 data module. It checks approved records against graph rederivation and
preserves both complete pack copies; changes that would rewrite approved records
abort. Regenerate puzzles, rankings and mobile content through their builders.
The frozen 336 derived boards must remain exact; only their metadata may refresh.

Acceptance also requires exact graph-delta evidence, unchanged editorial holds,
cross-game critique and runtime checks, independent factual and impact review,
both content validators and the repository's full integration gate. Preserve
historical review records when refreshing assertions for the current artifacts.

Generated dense-edge IDs advance above the largest present numeric `de`/`dd`
ID, rather than filling holes. The trial allocator reused V43-retired e-SIGUR
edge IDs; a merge-path regression now protects that cleanup. This does not
claim a durable high-water ledger if the largest ID itself is later removed.

## Consequences

The intended improvement is a direct, legible ingredient route. It is preparation
for a fresh food-target review, not approval of the three rejected candidates.
Changes to other graph distances and ranking scores need explicit impact review;
technical checks do not establish player enjoyment or authorize deployment.

Evidence: [V77 review](../reviews/v77-flour-associations/README.md).
