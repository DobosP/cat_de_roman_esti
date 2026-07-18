# ADR-0042: Bound broad Contexto guesses and progressive clues outside the shared graph

Date: 2026-07-18
Status: accepted

## Decision

Give Cald sau Rece a project-authored, Contexto-only projection of 444 normalized
everyday Romanian guess terms across 26 reviewed domains. Each exact surface maps to one
of 89 existing KG anchors and may add only a zero- or one-rank penalty. Every mapping is
either an authored semantic cluster or a named, justified broad-domain fallback; it is
never inferred from a term's position. A domain without an honest fallback requires an
explicit cluster for every live term. Screen every
surface against KG labels, ids, and true aliases; expose a deterministic `ctxp_` guess id;
deduplicate by normalized submitted surface; and borrow only the anchor's directed
rank/closeness/temperature scale. A projection term is guess-only: even when its anchor
is the target and its penalty is zero, it remains a non-win at rank 2 or worse. Only an
accepted KG label/alias/correction can solve the target.

Supersede ADR-0005's one-use clue with two bounded stages after three counted guesses:
first reveal the already-coarse category, then allow one familiar non-target word whose
rank is strictly better than the player's current best and never 1. An explicitly themed
board skips the paid category stage because its category is already public. Do not offer
the warmer stage at rank 2 or after no safe unplayed improvement remains, and advertise
it only after resolving a concrete candidate. Charge the existing score penalty only for
a clue actually issued. A browser receiving a stale 400 refreshes authoritative clue
availability so the disabled state cannot get stuck.

Keep target selection, KG/pack bytes, graph scoring, true resolver aliases, and session
TTL/cap unchanged. Compute a warmer candidate on demand for post-threshold availability
and clue issuance, preferring salience >= 0.55 with a safe fallback; do not add
per-session graph maps or candidate lists. The browser renders the two server-authored
clues as short, mobile-first cards and does not derive candidates or scoring.

## Context / why

The exact KG resolver rejects many ordinary words, while adding hundreds of shared nodes
or edges would expand Alchimie recipes, Lanț routes, target pools, and review obligations.
A hidden embedding model would add runtime dependencies and an unreviewed similarity
boundary. The projection widens only the guess vocabulary and keeps its semantic
compromises explicit: 80 authored sub-clusters, 26 named domain policies, and a
representative audit for all domains. Three policies explicitly forbid fallback because
the KG has no honest broad anchor. Mechanical round-robin assignment was rejected after
review because nearby terms such as drinks and ingredients must not borrow arbitrary
anchors merely to create more rank buckets.

One category clue still leaves a cold player without a playable next step. A guaranteed
warmer word follows the established Semantle recovery pattern without returning the
target, a full ranking, or a path. Precomputing all candidates per session was rejected:
at the 1,000-session cap it would duplicate thousands of records per game; one on-demand
reverse traversal is bounded and occurs only while producing post-threshold state or clue
responses.

## Consequences

The checked inventory has 444 unique terms, at least 14 per domain, no fixture collision,
and no missing anchor. Across 12 approved easy targets it spans at least 40 ranks and
three temperature bands, no single rank holds more than 15% of terms, and at least 24 of
26 domains span multiple ranks. Projection public ids cannot equal or reveal target ids,
and target-anchored typo suggestions are filtered.

API state adds optional `next_clue_kind` and `warm_clue`; the existing clue route returns
`clue_kind` and an optional direct `word`. These additions preserve the pre-terminal
hidden-answer boundary. Clue counts can now reach two on an unthemed game, so final score
and share text apply the existing per-clue penalty/count twice. The shared fixture,
curated pack, selection, two-hour sliding TTL, and 1,000-session LRU cap remain unchanged.
