# V50 synonym and basic-word funnel

This directory records the finite, two-reviewer lexical funnel governed by ADR-0074.
The 50 normalized-unique candidates produced eight exact shared aliases, twelve bounded
Contexto-only projections, eight deferrals, and twenty-two rejections. No acceptance
quota was used.

The alias set is limited to exact same-referent forms. The projection set remains
non-winning with rank penalty one. Disputed exact aliases, competing anchors or domains,
accent-fold collisions, and hard homonyms remain outside runtime content.

The review preserves the graph topology, all game records, ranking rows, the frozen
336-board derived payload, session bounds, and the tap-only games. The shared resolver
change benefits only the typed Contexto and Lanț inputs; projections remain Contexto-only.

Reproduce the focused contract with:

```bash
PYTHONPATH=. .venv/bin/python -m pytest tests/test_v50_synonyms_basic_words.py -q
PYTHONPATH=. .venv/bin/python scripts/rank_games_pack.py
PYTHONPATH=. .venv/bin/python scripts/build_derived_catalog_v38.py
```
