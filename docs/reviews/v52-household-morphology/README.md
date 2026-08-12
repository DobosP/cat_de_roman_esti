# V52 household-morphology funnel

This directory records the fixed 50-surface, two-reviewer funnel governed by ADR-0076.
It considered two genitive/dative forms for each of 25 already accepted household nouns.
Forty-eight forms passed both reviews; `păturile` and `păturilor` were rejected because
accent folding makes their keys valid forms of both _pătură_ and _pat_. No quota applied.

The accepted forms add no concept or sense. They remain exact aliases consumed only by
typed Contexto input and otherwise-legal Lanț hops. The wave preserves graph topology,
all projections and game records, ranking rows, the frozen derived payload, session
bounds, tap-only games, accounts, frontend, privacy, and deployment state.

Reproduce the focused contract with:

```bash
PYTHONPATH=. /home/dobo/work/cat_de_roman_esti/.venv/bin/python -m pytest tests/test_v52_typed_vocabulary.py -q
PYTHONPATH=. /home/dobo/work/cat_de_roman_esti/.venv/bin/python scripts/rank_games_pack.py
PYTHONPATH=. /home/dobo/work/cat_de_roman_esti/.venv/bin/python scripts/build_derived_catalog_v38.py
```
