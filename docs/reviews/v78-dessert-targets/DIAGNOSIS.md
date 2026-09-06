# V78 dessert-target negative screening and V79 repair boundary

Valid until: the next relevant Contexto feedback/projection wave changes the reviewed
source or behavior — then treat this diagnosis as history.

Baseline reviewed: `9abbc52`, served V77 graph unchanged. This reviewer made no
repository or fixture changes. The planned selection snapshot was stopped before artifact
creation when the runtime quality failures reproduced.

## V78 verdict

Drop both proposed targets in V78.

- **Cozonac:** the ordinary guess `nucă` does not resolve to a KG node. Its Contexto-only
  projection borrows `n_v24_food_breakfast_miere` (Miere), so it returns distance 4,
  rank 504, `Rece`, closeness 78. Meanwhile generic `fruct` is distance 1, rank 17,
  `Fierbinte`, closeness 99. This inverts the expected usefulness of a defining filling
  and a broad optional ingredient.
- **Clătite:** `gem` also projects to Miere and returns distance 6, rank 1,699,
  `Înghețat`, closeness 26. The exact KG concept `dulceață` is distance 1, rank 7,
  `Fierbinte`, closeness 99. Romanian players do not receive coherent feedback for two
  ordinary names of the familiar filling.

Făină is correctly `Fierbinte` for both targets after V77. That does not cure the
contradictory opener feedback. The negative decision agrees with the raw runtime screen;
neither candidate should be promoted merely to grow the shelf.

## Exact source identities

- `gem`, `nucă`, and `alună` are synthetic Contexto projection surfaces. They have no
  exact KG owner. All three are explicitly clustered to
  `n_v24_food_breakfast_miere` at `contexto_projection.py:947`, with rank penalty 1.
- Their public IDs derive only from normalized surface text. `gem` is
  `ctxp_fab0f46e7bcd5932442e`; the private Miere anchor is not encoded or returned.
- `unt` and `miere` resolve exactly to `n_v24_food_breakfast_unt` and
  `n_v24_food_breakfast_miere`. Both are V24 breakfast concepts with sparse generic
  topology. Projection remapping cannot intercept them because exact KG resolution wins
  before projection lookup.
- `dulceață` resolves exactly to the existing `n_v17gas_dulceata`, whose graph has the
  reviewed direct `Dulceață → Clătite` edge (`umplutură de clătite`, strength 0.70).

## Smallest hypothesized V79 correction

The proposed smallest future experiment is to split only `gem` from the current cluster and map it explicitly to
`n_v17gas_dulceata`. Keep its surface, domain `ingrediente`, penalty 1, mapping kind,
and public ID unchanged. Do not add a node, alias, edge, target, recipe, or Lanț move.
No such mapping was made during V78.

Counterfactual fixed-target calculations against the unchanged V77 graph predict:

- Against Clătite, Gem borrows Dulceață's distance 1/rank 7 and applies the projection
  penalty, yielding rank 8 and `Fierbinte`; it remains a synthetic guess and cannot win.
- Against Cozonac, Gem changes from distance 4/rank 504/`Rece` to distance 2/rank
  81/`Călduț`. This is better, but it does not repair the cold `nucă` feedback and does
  not make Cozonac promotion-ready.
- If Dulceață itself is the secret, projected Gem must remain nonwinning: public ID
  `ctxp_fab0f46e7bcd5932442e`, rank at least 2, closeness below 100, answer hidden.
  An exact `dulceață` guess must still use `n_v17gas_dulceata` and win normally.

The proposed source edit is confined to Contexto's projection table, but its full target
impact still requires a reproducible V79 before/after receipt. A preliminary unarchived
exploration sampled all 207 currently approved Contexto targets; it is deliberately not
accepted here as V79 impact evidence because no standalone runner and bound compact result
were preserved. V79 must rerun and archive that sweep before accepting the mapping.

## Required V79 tests

1. Resolver behavior after the proposed change: normalized `gem` variants retain the same public ID, domain,
   penalty 1, and explicit mapping kind while the anchor becomes Dulceață. Projection
   inventory count, uniqueness, collision screening, and all other surface mappings stay
   exact.
2. Real Contexto guess against fixed Clătite: verify whether accepted Gem is rank 8/`Fierbinte`, remains
   nonwinning, increments attempts once, keeps the answer hidden, and repeated normalized
   variants deduplicate.
3. Fixed Dulceață secret: prove Gem never wins or reveals the target; exact Dulceață does win.
   Typo suggestions anchored on the secret remain filtered.
4. Preservation after implementation: KG, games pack, rankings, frozen 336 boards, mobile contract, and the
   other five games remain byte-identical. Selection results remain exact because the
   projection table is not a target or board-selection input.
5. Keep `nucă`/`alună` and exact Unt/Miere behavior explicit in the evidence. Their
   separate quality problems require a separately reviewed anchor/proxy or topology wave;
   silently treating Gem's correction as their repair would be false coverage.

## Commands used

```bash
DJANGO_SETTINGS_MODULE=cat_de_roman_esti.web.settings PYTHONPATH=. \
/home/dobo/work/cat_de_roman_esti/.venv/bin/python - <<'PY'
from cat_de_roman_esti.wordgames.contexto_projection import resolve_projection
from cat_de_roman_esti.wordgames.service import get_service
svc = get_service()
for surface in ('gem', 'nucă', 'alună', 'unt', 'miere', 'dulceață'):
    term = resolve_projection(surface)
    print(surface, svc.resolve(surface), term)
PY
```

Runtime endpoint evidence is preserved in
`/home/dobo/work/_temp/v78-dessert-targets/runtime-openers.json`; it used temporary fixed
target sessions and deleted them after each probe.
