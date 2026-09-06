# V82 independent implementation and impact review

Valid until: the reviewed runtime, content artifacts, receipts or tests change — then treat as history.

Reviewed on 2026-09-06 by the independent `iteration_overhead_audit` agent against
baseline `953391999a8b9f43cb96885716f1413445465123`. No blocking implementation
or preservation defect found. This review does not certify the separately running
full integration gate or human enjoyment.

- The explicit `include_direct_neighbors=False` policy restricts burtă's new
  feedback to the exact soup target. The default remains `True`, preserving Gem's
  existing policy. Missing-anchor fallback, strong/reverse/bidirectional neighbor
  exclusions and the complete current-graph target boundary are tested.
- Guess and suggestion paths use the same anchor helper. The projection retains
  its public identity and nonwinning penalty; private anchors and the answer stay
  hidden before a win. Repeats, resume and the existing body meaning are covered.
  No session field, bound, random-selection algorithm or graph record changes.
- An independent direct comparison with Git proves all **621 prior pack records**
  exact, with precisely **eight new Contexto records**. All **336 frozen board
  payloads** are exact. Of the old ranking rows, 209 change only `rank` and/or
  `selection_weight`; the other three curated games' rankings remain exact.
- The inverse receipt reconstructs complete V81 pack, ranking and derived files
  to their original SHA-256 values. V80/V81 history helpers preserve their older
  assertions through this inverse. Spot checks of V25/V28/V45/V47/V50/V68/V72
  changes found refreshed current pins/counts while historical review, vocabulary,
  topology and frozen-board assertions remain intact. Updated V75/V80 public
  seeds reflect changed current selection; V82 independently checks exact totals.
- Runtime comparison source hashes match the reviewed files. Selection evidence
  is explicitly bounded sampling, and the 764-input comparison is not presented
  as exhaustive. The earlier reporting-tool review remains accepted within its
  declared inventory scope; aliases do not become claimed synonyms.

Independent targeted command:

```text
PYTHONPATH=. /home/dobo/work/cat_de_roman_esti/.venv/bin/python -m pytest -q -o addopts='' tests/test_v82_burta_feedback.py tests/test_v82_playable_content.py tests/test_v81_history.py
24 passed in 2.54s
```

The direct artifact comparison used the actual Git baseline and current files,
independently of the delta receipt. No heavy suite, deployment or production
verification was performed by this reviewer.

## Alchimie pair memo addendum

The later local memo in `_build_recipe_projection_cached` and its five focused
tests were independently reviewed on 2026-09-06. No blocking defect found.

Pair keys remain canonical through sorted combinations. `common_neighbors`
depends on the fixed service and category, while subtraction of the current
inventory still happens on every visit. Immutable cached results, including empty
sets, therefore preserve discovery and ordering. At 4,096 retained pairs, uncached
misses continue normal graph discovery; capacity does not prune routes.

The memo is local to one cold build and is not returned, stored in sessions or
shared across services/categories. The existing outer service-identity cache key
and invalidation remain unchanged. Its bound is 4,096 entries per concurrent cold
build, not a fixed byte budget: each result set is bounded by the graph's available
neighbors. The search, recipe and session limits are unchanged.

Independent focused execution: `tests/test_v82_alchimie_pair_memo.py` — **5 passed
in 0.47s**. The tests cover productive and empty repeated pairs, capacities zero,
one and two, identical resulting routes, fresh cold-build work and category
isolation. This reviewer did not rerun the heavy timing benchmark or independently
claim the orchestrator's broader projection-equivalence results.
