# V51 typed-vocabulary funnel

This directory records the fixed 50-surface, two-reviewer funnel governed by ADR-0075.
It produced 32 exact grammatical forms of already accepted shared aliases, eight bounded
Contexto-only projections, seven deferrals, and three unanimous rejections. No acceptance
quota was used.

The shared forms remain normalized-unique and exact. Projected guesses remain non-winning
with rank penalty one. Reviewer disagreement, competing anchors, alternate projection
spellings, and hard homonyms stay absent.

The wave preserves graph topology, all game records, the V49 rejection ledger, ranking
rows, the frozen 336-board derived payload, session bounds, and tap-only games. Only typed
Contexto/Lanț inputs consume aliases; projections remain Contexto-only.

Reproduce the focused contract with:

```bash
PYTHONPATH=. .venv/bin/python -m pytest tests/test_v51_typed_vocabulary.py -q
PYTHONPATH=. .venv/bin/python scripts/rank_games_pack.py
PYTHONPATH=. .venv/bin/python scripts/build_derived_catalog_v38.py
```
