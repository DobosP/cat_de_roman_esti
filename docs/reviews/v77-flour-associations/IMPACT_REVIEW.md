# V77 flour-association cross-game impact review

Baseline: commit `9ef9dc71fd26896596f513299137cfa02f26e767`, fixture raw SHA-256
`fa9575db4819fa314e43218a0ad953f52c3e6ee2e34cac105dbc88e2d2247106`
(2,364 nodes / 9,217 edges). The repository was read-only for this reviewer; all
prospective fixture material was written under this scratch directory.

## Reproduction

Reconstruct the independent baseline even if the worktree has a dirty candidate:

```bash
mkdir -p /home/dobo/work/_temp/v77-flour-associations/impact-review/gitbase
git show 9ef9dc7:cat_de_roman_esti/fixtures/kg_sample.json \
  > /home/dobo/work/_temp/v77-flour-associations/impact-review/gitbase/kg_sample.json
```

Rejected three-edge trial:

```bash
V77_BASE_KG=/home/dobo/work/_temp/v77-flour-associations/impact-review/gitbase/kg_sample.json \
DJANGO_SETTINGS_MODULE=cat_de_roman_esti.web.settings PYTHONPATH=. \
/home/dobo/work/cat_de_roman_esti/.venv/bin/python \
  /home/dobo/work/_temp/v77-flour-associations/impact-review/impact.py
```

Copy `report.json` to `report-three-rejected.json` before the final run. Final accepted
two-edge experiment:

```bash
V77_BASE_KG=/home/dobo/work/_temp/v77-flour-associations/impact-review/gitbase/kg_sample.json \
V77_TARGETS=n_gas_cozonac,n_v3gas_clatite \
DJANGO_SETTINGS_MODULE=cat_de_roman_esti.web.settings PYTHONPATH=. \
/home/dobo/work/cat_de_roman_esti/.venv/bin/python \
  /home/dobo/work/_temp/v77-flour-associations/impact-review/impact.py
```

Both commands exited 0. Evidence hashes:

- rejected three-edge report: `3a25d24565ddfa5bd9eae6218bd4b96b6278b6a9f5300c1af1109b23361a12fa`
- final two-edge report: `ac35a984fd86b5497d6034c20b9afff47e4858c6a559f4cbd52d191b98a2bb99`

## Final two-edge result

- All 620 curated records validate before and after (232 Conexiuni, 209 Contexto,
  97 Lanț, 82 Alchimie; approved and pending included).
- All 232 Conexiuni fairness/contested/engine-parity results are identical. Ten boards
  mention Cozonac or Clătite, but none contains Făină, so no new on-board or symmetric
  critique crossing exists.
- All 97 Lanț distances, branch profiles, and bounded shortest-path witnesses are
  identical, including `lt_gastronomie_018` (Cozonac target) and
  `lt_gastronomie_105` (Cozonac start). Făină gains the intended two forward choices
  outside those curated boards; neither dish gains a reverse choice.
- All 82 Alchimie closures, pars, opening counts, minimum recipes, and exact private
  recipe projections are identical. Prospectively, the common-neighbor rule admits
  27 new future pair/output associations involving Făină (19 producing Cozonac and
  8 producing Clătite); this does not enter a current curated projection.
- Frozen derivation remains exact: 123 frozen Conexiuni sources produce raw
  Intrusul/Perechi counts 800/9,164, selected counts 183/153, and all 336 board
  payloads, scores, and ranks byte-equivalent to the frozen catalog. Only one frozen
  source mentions a proposed target (`cx_personalitati_213`, Cozonac); none contains
  Făină.
- Contexto reachability stays identical. Făină/Zahăr paths change for 95 approved
  curated targets; responsive counts are unchanged for 75, +1 for 16, and +2 for 4.
  Ordinal ranks change for 52,043 guess/target pairs; 51,854 unaffected guesses merely
  move +1 or +2 because Făină/Zahăr enter earlier buckets. The intended mined-target
  behavior is Făină→Cozonac rank 498/Rece to rank 2/Fierbinte and Făină→Clătite rank
  1,696/Înghețat to rank 2/Fierbinte.
- No unrelated-category target makes Făină or Zahăr newly Fierbinte. The only new
  unrelated `Cald` result is Făină→Chefi la cuțite (hop 5/rank 1,883/Înghețat to hop
  2/rank 66/Cald), through Cozonac; it is a direct culinary association. The only new
  unrelated `Călduț` results are Sarmalele de Crăciun and Calendarul obiceiurilor,
  both via the Cozonac/holiday neighborhood. Zahăr gains no unrelated `Cald` or
  `Călduț` result.

## Rejected third edge

Adding Făină→Pâine de casă also left every curated non-Contexto artifact structurally
unchanged, but made Făină a misleading warm opener for `ct_stiinta_102` Stiloul cu
rezervor: hop 6/rank 2,124/Înghețat became hop 3/rank 220/Călduț (closeness 90) through
Făină→Pâine de casă (`0.97`)→Lapte și corn (`0.42`)→Stiloul cu rezervor (`0.56`).
Reducing only the new edge strength does not remove the hop-first tier promotion.
Deferring that edge is the smallest safe boundary.

## Direction interpretation

The live service honors `bidirectional: 0`: the source gains a forward route and the
dish does not gain a route back to Făină. Contexto inbound distance, Lanț traversal,
and Alchimie common-neighbor inputs therefore use the proposed ingredient→dish
direction. `critique_pack.load_all` and `build_derived_catalog_v38._edge_maps`
deliberately symmetrize non-distractor edges for cross-group evidence and derived-board
separation. That mismatch has no current board effect, but future derived candidates
containing both endpoints will treat the association as linked in both directions.
Do not infer reverse live traversal from the offline symmetry.
