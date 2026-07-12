# ADR-0021: Graded Contexto similarity + fuzzy input suggestions

Date: 2026-07-12
Status: accepted

## Decision
Make the similarity/input feel of Cald sau Rece (Contexto) and Lanțul Cuvintelor smarter
without changing any hidden-answer boundary or public API shape.

1. **Fuzzy suggestions.** Add `WordGameService.suggest(text, limit=3)` — a
   `difflib.get_close_matches` (cutoff 0.78) over the same normalized index keys resolution
   uses, mapped back to node labels, de-duplicated per node, deterministic order.
   `resolve()` stays exact-match. Contexto and Lanț embed the top hint into their existing
   Romanian error message and add an additive `suggestions: [labels]` array. Contexto
   excludes any suggestion that resolves to the secret target (ADR-0009); Lanț does not
   (its target is public). Unresolved guesses still never count as attempts.
2. **Graded distance.** Add `WordGameService.weighted_distances_to(target)` — Dijkstra over
   the SAME reversed non-distractor adjacency ADR-0018 mandates (guess → target), with edge
   cost `2.0 − clamp(strength, 0, 1)` (missing/invalid strength → 1.5). At Contexto session
   creation, precompute per-hop-bucket sorted arrays of these weighted distances in one
   O(N log N) pass. Refined rank = `closer_than[d] + bisect_left(sorted_weighted[d], w) + 1`,
   so hop ordering is preserved across buckets while a tighter (stronger-edged) path ranks
   strictly better within a bucket. Closeness derives from the refined rank
   (`round(100*(reachable−rank)/(reachable−1))`, clamped [1,99]; 100 reserved for the win).
   Temperature is a per-target rank percentile (d==0 Găsit; pct≤0.005 or d==1 Fierbinte;
   ≤0.03 Cald; ≤0.10 Căldut; ≤0.40 Rece; else/unreachable Înghețat) — monotonically
   non-increasing in rank, replacing the fixed hop table.
3. **Dead-end escape.** In Lanț's hint, when the current node can no longer reach the
   target, walk the player's own chain back to the nearest node with a finite
   `distances_to(target)` and name it ("Fundătură — întoarce-te la <label>"). Only visited
   chain nodes may be named.

## Context / why
Guess resolution was exact-match only, so a single typo read as an unknown concept with no
help. Contexto ranked by pure unweighted hop count (ADR-0018), never using the fixture's
per-edge `strength`; ~74% of nodes piled into hops 4–5, so the fixed hop→tier table made
most guesses read identically "Rece" and every guess in a hop bucket shared one rank and
closeness. The graph already carries a `strength` in [0.12, 0.98] on every edge — a real,
unused semantic signal.

Dijkstra over the existing reversed adjacency reuses ADR-0018's direction rather than
introducing a second graph, so it cannot contradict the hop-count reachability floors
(`MIN_REACHABLE`/`MIN_RESPONSIVE`) or the packs validator, which stay on unweighted
`distances_to`. Bucketing weighted distances *within* each hop layer (not globally) was
chosen over a purely weighted global rank so hop order — the coarse signal players trust —
is never inverted by an accumulation of many weak edges; the refinement only ever reorders
guesses that are the same number of hops away. Treating a missing strength as the weakest
edge was rejected (it would punish absent data); the neutral middle cost 1.5 is used
instead. Suggestions ride the existing message plus an additive array so no frontend change
is required and the mobile contract (ADR-0003) stays additive.

## Consequences
`reachable_count`, hidden-answer boundaries (ADR-0009), clue logic/penalties (ADR-0005),
`score_for` (2 attempts → 940), the OpenAPI operationIds, and the session-store bounds are
unchanged. Ranks and closeness now vary within a hop bucket and temperatures spread across
all tiers, so formula-level Contexto tests that assumed the flat hop table are updated
deliberately; the win-100 and Găsit invariants are pinned. Each live Contexto session now
also holds an O(N) weighted-distance map plus its sorted buckets — bounded by the existing
per-game session cap, but a larger per-session footprint than the histogram-only model, to
revisit if concurrency on the launch VM grows. `weighted_distances_to` and `suggest` are
new reusable service primitives other games can adopt later.
