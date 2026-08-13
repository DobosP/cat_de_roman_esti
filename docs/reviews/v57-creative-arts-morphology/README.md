# V57 creative-arts-morphology funnel

This directory records the fixed 50-surface, two-reviewer funnel governed by ADR-0081.
It considered two genitive/dative forms for each of 25 existing creative-arts concepts.
Forty-eight forms passed both reviews. `tabloului` and `tablourilor` were rejected because
_tablou_ ordinarily denotes both a painted or drawn artwork and a table, chart, dashboard,
or control panel. No quota applied.

The accepted forms add no concept or sense. They remain exact aliases consumed only by
typed Contexto input and otherwise-legal Lanț hops. The wave preserves projections, graph
topology, game records, ranking rows, the frozen derived payload, session bounds, accounts,
frontend, privacy, and deployment state.

Reproduce the focused contract with:

```bash
PYTHONPATH=. /home/dobo/work/cat_de_roman_esti/.venv/bin/python -m pytest tests/test_v57_creative_arts_morphology.py -q
PYTHONPATH=. /home/dobo/work/cat_de_roman_esti/.venv/bin/python scripts/rank_games_pack.py
PYTHONPATH=. /home/dobo/work/cat_de_roman_esti/.venv/bin/python scripts/build_derived_catalog_v38.py
```
