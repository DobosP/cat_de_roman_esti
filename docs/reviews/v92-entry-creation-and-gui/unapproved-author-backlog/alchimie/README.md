# Session 02 Alchimie proposals

Valid until: the bound world, recipe source, builder or critique rubric changes.

Three **unapproved** recipe candidates reuse only current world identities:

| Recipe ID | Pair → result | First outgoing use for |
|---|---|---|
| `salata-cartofi-ou-fiert` | Ou fiert + Cartof → Salată de cartofi | Ou fiert |
| `sandvis-omleta` | Omletă + Pâine → Sandviș | Omletă |
| `tarta-mousse-biscuit` | Mousse de ciocolată + Biscuit → Tartă | Mousse de ciocolată |

[candidates.json](candidates.json) contains exact current IDs, proposed recipe rows,
source URLs, source-access notes, original explanations, player routes, author reasoning,
review risks and excluded ideas. Its SHA-256 is
`00e7ef03a8025c88fd9e5b92faee082b8f6df552cdf75aad44828caa6bf16b5e`.
No acceptance judgment is asserted or substituted for an independent review.

The current repository world has 221 concepts and 285 recipes. Adding these proposals
in memory gives 288 recipes, with 117 discoveries and all twelve supply tiers reachable.
Terminal results fall 70 → 67; reusable crafted concepts rise 47 → 50. Existing concept,
recipe, world, supply and goal records are preserved exactly. Productive opening pairs
remain 9/28; results with alternatives remain 77. The number of recipes for potato salad
grows 2 → 3, sandwich 18 → 19, and tart 3 → 4. No unordered pair conflicts occur.

[mechanical-audit.json](mechanical-audit.json) records the existing world builder's audit
on the baseline and hypothetical addition, checks preservation, and identifies the three
newly reusable IDs. [candidate-witnesses.json](candidate-witnesses.json) gives a complete
deterministic craft/unlock trace for each proposal: its result is first discovered through
that proposed recipe, after which the trace finishes all 117 discoveries, 221 owned
concepts and twelve tiers. This is a scratch mechanics replay, not live API verification.

The author recommends these for independent review, with the potato-salad and omelette
routes strongest. The mousse route has a nearby Ganache + Biscuit precedent, so its
quality value rests on giving the existing mousse a further use. The sandwich route
also needs a freshness judgment because many sandwich alternatives are already served.
Neither candidate claims a new result or new concept. The rubric's seed/target criteria
apply to the unchanged exploration world; these are extra recipes, not new scored boards.

Cozonac + Ou → Frigănele was excluded despite real recipes because the accepted
Frigănele definition currently specifies bread; this batch preserves concept records.
Compot + Frișcă → Tort Diplomat was excluded as an underdetermined shortcut. A cluster of
additional bread-filling recipes was left out to avoid repetitive sandwich growth.

Evidence comes from primary recipe creators or their own publisher pages. The recipe
pages for [potato salad](https://www.bucatarmaniac.ro/2022/05/salata-de-cartofi-cu-oua-si-ceapa-calita-reteta-video.html),
[omelette sandwiches](https://pofta-buna.com/sandvisuri-cu-omleta/) and
[mousse tart](https://madelicii.ro/reteta/tarta-cu-mousse-de-ciocolata-si-tonka/)
were read directly. Supporting pages read through the search index are marked as such,
including the Laura Laurențiu article whose direct request presented browser verification.
No recipe text, photos or license claim is copied into the world.

Reproduce from any working directory:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/dobo/work/cat_de_roman_esti/.venv/bin/python \
  /home/dobo/work/_temp/feat__v92-entry-creation-02/session-02/alchimie/author_candidates.py \
  --repo /home/dobo/work/_worktrees/cat_de_roman_esti/feat__v92-entry-creation-02
```

The script pins the baseline catalog SHA and refuses output outside its assigned scratch
directory. A second generation reproduced all three JSON artifacts byte for byte.
`ruff check --no-cache author_candidates.py` passes. The author changed no repository
file and wrote no hypothetical full-world artifact or serving fixture.

Before any serving change, independent factual and quality judgments must bind the exact
candidate/world, and the existing generator's full review gates and final API checks still
apply. The modified recipe mechanics also require reviewed compatibility history for the
current 221-concept collection; this authoring artifact does not authorize that migration.
