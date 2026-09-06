# V81 walnut input

Valid until: the bound word, recipe edges, Contexto policies or game content changes — then treat as history.

V81 adds the real culinary concept **Nucă** and its unambiguous `nucile` form,
with four reviewed ingredient links. It follows [ADR-0112](../../adr/0112-add-reviewed-walnut-input.md).
It does not add or promote a game target.

## Player-facing result

| Walnut guess against target | Before | V81 |
|---|---|---|
| Cozonac — fixed target, still awaiting content review | 4 hops / rank 504 / Rece | 1 hop / rank 2 / Fierbinte |
| Baclava dobrogeană — approved target | 5 hops / rank 1873 / Înghețat | 1 hop / rank 2 / Fierbinte |
| Colivă and Cornulețe — reviewed recipe associations | Approximate Miere feedback | 1 hop / rank 2 / Fierbinte |

`Nucă`, accentless `nuca` and `nucile` use one real KG identity. Repeats deduplicate
and resume retains progress. A walnut guess cannot win a different target, even
when its private feedback anchor is that target. Exact walnut self-play wins in
fixed-target tests; this does not make the new node a selectable Contexto target.

Only `nucile` is added as an alias. `nuci`, `nucii`, `nucilor` and tree names remain
unresolved because they overlap walnut-tree forms; kernel phrases are part/whole,
and coconut is a different concept. They are not silently admitted as aliases.
Suggestions remain advisory and target-aware. The existing confident-typo rule
can complete a real walnut answer, while confirmation details remain suppressed
for a hidden walnut or Miere fallback target.

## Real relations with bounded feedback

The one new node has four outgoing, one-way, non-distractor `part_of` edges labeled
`ingredient pentru`: Cozonac and Colivă at 0.97, Baclava dobrogeană at 0.95, and
Cornulețe at 0.90. Independent sources support these common preparations; neither
the edge nor its editorial weight asserts that every variant uses walnuts.
This meets the existing meaningful-neighbor floor without changing the applier.
ADR-0112 permits four outgoing links only for this node, partially superseding
ADR-0033's three-edge cap. No old node gains an outgoing edge or an old-to-old path.

Unrestricted one-edge and four-edge simulations were rejected: they made walnuts
warm for unrelated savory foods and, with four edges, places and historical figures.
The final Contexto policy uses the native walnut edge only for exact self or a
forward non-distractor `part_of`/`ingredient pentru` edge at strength ≥0.90.
Elsewhere it retains the old penalized Miere approximation. That residual fallback
is not a synonym claim. Guesses, fuzzy handling, suggestions and warmer clues share
the effective-anchor helper; playing the Baclava Nucă clue reproduces its rank.

Nucă's synthetic projection is retired; the other **472 projection rows**, all
**71 legacy common-word proxies**, and the Gem policy remain exact. There is no
new per-session field, cache, graph search, reverse edge or promotion.

## Actual impact and preservation

The generated graph is `fixture-v81-nuca-feedback`: **2,365 nodes / 9,223 edges /
8,451 aliases / 180 puzzles**. The complete **621 game records** and eight holds,
all **336 frozen boards**, and all 180 puzzle records remain exact. Package/test
mirrors match; mobile and catalog metadata are regenerated through supported tools.

The actual API sweep covers **208 approved / 204 eligible** Contexto targets.
Only Baclava gains a warmer walnut result. The other 207 retain the old Miere-based
distance and temperature; their public identity is now the real walnut node, and
145 ranks move +1 while 62 stay unchanged. All nonwinning targets remain hidden.

Adding a reachable word also affects existing guesses' ordinal normalization.
Across **491,712 old-node/target scores**, no old distance or path changes;
222,582 ranks move +1, 7,151 closeness values change, and **121 marginal temperature
crossings** occur across 31 targets: 93 Înghețat→Foarte rece, 15 Rece→Foarte rece,
11 Călduț→Rece and two Cald→Călduț. These small boundary effects are disclosed;
this wave does not claim unchanged scoring for every old guess.

All 232 Conexiuni fairness/critique results, 97 Lanț profiles and 82 Alchimie
closures/pars/openings/private recipe projections remain exact. Derived mining
retains raw 800/9,164 candidates and the same 183/153 frozen boards. Selection
samples over 100 seeds and September's 30 daily dates match before/after and on
repeat runs across all six games plus Contexto's gastronomie/usor shelf. This is
bounded sampling, not an assertion about every possible future seed.

Only Baclava's private ranking estimates increase (familiarity 55→56, play quality
88→89, score 68→69), moving it from rank 121 to 117. Four adjacent Contexto rows
move one place. No approval, eligibility or selection weight changes. These are
selection heuristics, not measured human familiarity or enjoyment.

## Evidence and reproduction

- `proposal.json`, `FACTUAL_REVIEW.md`, `factual-review.json`: the exact word,
  sole alias, exclusions, four weighted recipe facts and feedback boundary.
- `artifact-delta.json`: complete before/after bindings and the reversible delta.
  Tests reconstruct the full pre-V81 KG, ranking and derived artifacts by their
  original hashes, then retain V77/V80 history checks. V76's original 13,177
  surface mappings and V79's original 473-row projection fingerprint remain checked.
- `impact/FINAL_IMPACT_REVIEW.md` and `impact/final-impact-receipt.json`: independent
  acceptance, exact source/capture hashes, all-six-game and old-guess audits.
- `impact/` captures and `.py.txt` runners preserve both rejected simulations and
  the accepted actual result. Earlier provisional aliases belong only to rejected
  experiments; the final node has exactly `nucile`.
- `performance-diagnosis.json`: the load-sensitive benchmark investigation; no timing
  threshold or mining algorithm was changed, and the unexecuted paired benchmark is not claimed.
- `IMPLEMENTATION_REVIEW.md`, `implementation-review.json`, `verification.json`
  and `review-manifest.json`: independent review, actual gates and archive bindings.

Restore baseline `dbbcf6e8b810fb990c9acffb42d6426138551637` in a task worktree,
apply `scripts/apply_nuca_feedback_v81.py` through the V24 transaction, and run
ranking/frozen-catalog builders. Update the trusted catalog digest only after
proving the frozen payload exact. The transaction regenerates mobile and refuses
approved-pack drift. Archived runners can be copied to scratch without `.txt`;
adjust the original root/scratch paths recorded in the impact report.

The reviews are independent Codex-agent judgments with Romanian source checks,
not human playtests. Cozonac needs a fresh target review; bread remains deferred.
No push, deployment, accounts enablement or production re-verification occurred.
External beta gates remain in [BETA_CANDIDATE](../../BETA_CANDIDATE.md).
