# ADR-0115: Reuse Alchimie pair results within one projection build

- Status: accepted
- Date: 2026-09-06

## Context

V82's integrated gate hit the existing 45-second Alchimie generation ceiling at 52.73
seconds on a fully loaded host. The graph and Alchimie implementation were unchanged.
Profiling the twelve fixed-seed mined sessions found 20,606,576 common-neighbor queries;
the projection search repeatedly queried identical pairs in different owned-inventory states.
This is redundant work in actual game generation, independently of the load-sensitive test.

## Decision

Within each call to `_build_recipe_projection_cached`, memoize immutable common-neighbor
results for at most 4,096 pairs. A pair's result depends only on the pinned service and fixed
category, while the fresh outputs are that result minus the state's owned concepts. Once
the memo is full, compute additional misses normally; the cap never drops a route or result.
Discard the local memo when the call returns. Retain the existing 512-entry projection LRU,
service-identity invalidation, session limits and all search/recipe bounds.

Keep frontier sorting, pair order, random choices, state limits, route pruning and quality
selection exact. Do not alter the 45-second gate or substitute CPU time for elapsed time.
Acceptance compared complete projections for all 82 curated records
and complete sessions for the twelve mined seeds against the unchanged baseline, including
recipes, routes, par, seeds, target and private candidate-quality data. Every compared field remains exact. Five synthetic memo-limit/isolation tests and the
existing 45-second generation gate passed; see the
[V82 performance receipt](../reviews/v82-playable-content-batch/performance-receipt.json).

## Consequences

The change removes repeated graph work during cold generation without changing authored
content or game choices. The temporary memo has an explicit size ceiling and no cross-call
lifetime. The benchmark remains sensitive to competing host work; measured results and
their scope belong in the V82 receipt, not an unsupported general latency guarantee.
