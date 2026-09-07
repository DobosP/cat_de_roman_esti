# V84: six-game guidance and culinary graph quality

Valid until: the bound graph, content, game behavior or review artifacts change — then treat as history.

Baseline: `83538809d4913c4b22f36cf92c4f1502f50f83f3` (V83, already on local main).
Candidate: `feat/v84-six-game-graph-quality`. Target audience remains the public anonymous
Romanian beta. Decisions: [ADR-0118](../../adr/0118-reviewed-culinary-graph-corrections.md)
and [ADR-0119](../../adr/0119-in-round-help-and-earned-link-explanations.md).

## What players gain

| Game | V84 improvement | New curated rounds |
|---|---|---:|
| Alchimie | Earned discoveries show the actual two oriented graph relations, including after resume and in the winning recap; rules stay accessible | 0 |
| Intrusul | In-round rules explain the three-member relation, excluded wrong choices, free repeats and available hint | 0 |
| Perechi | In-round help clarifies intended relationships, immediate pair checking, deselection and hint recovery | 0 |
| Conexiuni | In-round help explains four-member groups and near misses; keyboard help cannot accidentally submit selected tiles | 0 |
| Cald sau Rece | Fifteen real concepts, clearer ingredient/production feedback and three fresh targets; rank/guess help stays accessible | 3 |
| Lanțul Cuvintelor | Sixty-seven newly valid directed graph moves, a fresh two-route board and accessible direct-link/recovery help | 1 |

Every help disclosure starts closed, supports native keyboard/touch operation and preserves
selection, typed text, attempts and scores. It makes no API request. Alchimie explanations
contain only already visible parents/results, omit nonexistent or unlabelled evidence and
add no session fields. Recipes describe associations; their exact labels retain direction.

## Actual content delta

- **15 new concepts:** Drojdie, Aluat, Cuptor de bucătărie, Zer, Saramură, Grâu, Orz, Ovăz,
  Secară, Mălai, Griș, Arpacaș, Cheag alimentar, Tavă de copt and Sucitor.
- **57 new graph links; one false link removed.** Telemea→Poale-n brâu no longer claims
  both endpoints are cheeses. Net graph growth is 56 links, not 58.
- **42 accepted forms** across the new concepts; all 8,475 prior aliases remain exact.
  These include inflections and qualified names. The independent lexical review explicitly
  supports one equivalent expression, `făină de porumb` for Mălai; do not count all forms as synonyms.
- **Three new Contexto rounds:** Plăcintă cu mere, Salam de biscuiți and Pâine, IDs
  `ct_gastronomie_334`–`336`. Approved stock 221→224; selectable 217→220.
- **One new Lanț round:** Făină→Cornulețe, `lt_gastronomie_220`, with two shortest routes
  through Aluat or Cozonac. Approved/selectable stock 94→95.
- Whole pack 634→638, approved 626→630, original eight pending holds unchanged.
  Conexiuni/Alchimie stock and all 336 derived Intrusul/Perechi boards remain unchanged.

The served graph grows from 2,365/9,223 to **2,380 concepts/9,279 links**. Only 25 old node
degree fields change. All 9,222 retained edge records, 634 old pack records and 180 legacy
puzzles remain exact. Of old ranking rows, 292 change after graph and stock updates; exact
historical KG/pack/ranking/derived bytes reconstruct from [artifact-delta.json](artifact-delta.json).
The review and final inventory distinguish new records, approvals and runtime eligibility.

## Realism and bounds

New labels distinguish ingredients, variants, production steps, equipment and categories.
Examples include flour/water→dough, salt/water→brine, whey→urdă and apples/biscuits→their
respective desserts. Cereal similarity is not a claim of ingredient interchangeability.
Every new node has at least four incident neighbors, but this is not four outgoing moves:
Drojdie, Cheag alimentar, Sucitor and Tavă de copt are source-only concepts. They are usable
Contexto guesses and graph sources, not automatically hidden targets or Lanț destinations.

The bare-input exclusions remain. Qualified oven, tray and food-rennet labels avoid capturing
unrelated senses; the old bare Tavă projection and Sculptor confirmation for `cuptorului`
are preserved, not newly redirected to kitchen nodes. New projection ownership retires only
Drojdie's generic Mâncare row, leaving 471 terms and every other row unchanged.

The independent graph comparison checks all 82 old Alchimie recipe projections and 97 old
Lanț route profiles: **all remain exact and valid**. Every old eligible pool is retained.
All 67 directions allowed by the 57 new links succeed in real one-hop Lanț API journeys.
Two material recipes, flour+water→dough and salt+water→brine, also work through the engine
with earned explanations; this does not imply a new public curated Alchimie board.
The broader theoretical closure used by content analysis changes for eight food records,
adding Zer/Saramură; the removed false edge delays ten generation entries across three
records. This is distinct from the unchanged playable recipe books. Exact differences
are retained in [alchimie-closure-delta.json](alchimie-closure-delta.json).

Across 3,757 first-guess observations per checkout, most changes reflect formerly unknown
inputs becoming native. They are not thousands of individually reviewed repairs. Specific
gains include Biscuit→Salam de biscuiți and Măr→Plăcintă cu mere at rank 3, Zer→Urdă at 4,
and Saramură→Telemea at 5, all direct, hot and nonwinning. Drojdie→Sarmale cools from hot
rank 8/distance 1 to cold rank 246/distance 3. Six former false-hot meat/cheese targets cool.

Remaining imperfections are explicit: cinnamon is spuriously hot for bread (rank 4), while
dough/yeast/qualified oven are hot at 7 and flour is warm at 45. The no-bake biscuit dessert
has oven/tray at warm 36, ahead of cocoa at warm 62; butter is cold for apple pie. Drojdie→
Telemea remains lukewarm. Final judges assessed these defects and accepted the clear direct
cores, not just validator floors. Generic Pâine is distinct from the previously deferred
Pâine de casă edge; that edge remains absent and the V77 flour-to-pen guard remains cold.

## Review and verification

- [GRAPH_REVIEW.md](GRAPH_REVIEW.md) and [graph-review.json](graph-review.json): independent
  factual/lexical review of the exact module and candidate bytes; accepted 15/42/57/1.
- [CANDIDATE_SCREEN.md](CANDIDATE_SCREEN.md), `gastronomie/`, `analyst-review.json`,
  [VERIFIER_REVIEW.md](VERIFIER_REVIEW.md), `verifier-review.json` and `verdicts/`: four
  complete raw screens and separate bound promotion judgments. Strict critique found zero
  FAIL and one justified salience WARN; supported serializer/applier promoted all four.
- [impact/IMPACT_REVIEW.md](impact/IMPACT_REVIEW.md): independent six-game comparison,
  compact summaries, full-capture hashes and reproducible scripts. Expanded final review
  adds 93 private opener probes, three clue/win journeys and both new Lanț routes.
- [IMPLEMENTATION_REVIEW.md](IMPLEMENTATION_REVIEW.md): independent runtime/UI/history and
  transaction review. A duplicate-baseline-ID removal flaw was reproduced and fixed;
  stale/partial removals, interrupted writes and dry runs have meaningful regression checks.
- Current test expectations remain manually reviewed literals. Historical hashes stay
  fixed; inverse helpers remove only this exact reviewed delta before old-wave checks.
  Old Gem/Nucă observations are retained on their original graph; live checks verify the
same intended fallback against the current graph.

Selection sampling covers 22 scopes, 100 seeds and 30 September dates. Independent repeated
candidate processes match exactly and all eight earlier fixed-date observations remain.
Conexiuni, Alchimie, Intrusul and Perechi show no remapping in those samples. Contexto and
Lanț remapping after four new records is quantified in [selection-impact.json](selection-impact.json),
including the actual Lanț easy selector. Sampling does not prove every future selection.

Focused V84 checks: **62 passed**, including all 42 forms and all four public create/play/
resume/win journeys. Independent implementation checks: 15 passed. New help adds 14 browser
cases. The frontend build passes its unchanged **120 KiB** budget at **118.87 KiB**.
Visual inspection also covered the built [desktop discovery explanations](screenshots/alchimie-earned.png)
and [mobile in-round help](screenshots/perechi-help-mobile.png); see `visual-review.json`.
Final integration: **1,207 backend tests passed on each runtime** (Python 3.12.3: 767.72s; Python 3.14.6: 667.85s), with **53 accounts tests each**,
**177 native frontend tests and 122 browser checks**. No skips or browser retries. Both
validators, pending gate, lint/typecheck/build/bundle, Ruff, docs and whitespace pass.

The initial full run exposed five stale historical expectations; they were corrected
without discarding original observations or relaxing limits. Two diagnostic Python 3.14
runs were interrupted to load those test fixes. The final fresh full runs pass on both
versions, including their unchanged timing checks. Exact results and initial findings:
[verification.json](verification.json). Source and review bindings: [review-manifest.json](review-manifest.json).
V84 is complete on its task branch, ready for its next local landing request.

Reproduce the graph with `scripts/apply_common_words_v24.py --data-module kitchen_graph_v84_data`
from the baseline, then the documented pack-only import/critique/review/apply flow and the
ranking/derived/mobile builders. Report quantities with
`python3 scripts/report_content_delta.py --baseline 8353880 --text`.
No push, deployment, human playtest or real-device acceptance was performed.
