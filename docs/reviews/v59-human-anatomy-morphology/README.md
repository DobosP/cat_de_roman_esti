# V59 human-anatomy-morphology funnel

This directory records the fixed 50-surface, two-reviewer funnel governed by ADR-0083.
It considered two genitive/dative forms for each of 25 existing human-anatomy concepts.
Forty-eight human-qualified forms passed both reviews. `creierului` and `creierelor`
were rejected because _creier_ ordinarily also denotes intelligence, an organizer or
leader, a mountain interior, or a wheel hub. No quota applied.

Qualifiers such as `inimii umane`, `capetelor umane`, and `sprâncenelor umane` bind the
accepted surfaces to anatomy rather than other ordinary senses. The accepted forms add
no concept or sense. They remain exact aliases consumed only by typed Contexto input
and otherwise-legal Lanț hops. The wave preserves projections, graph topology, game
records, ranking rows, the frozen derived payload, session bounds, accounts, frontend,
privacy, and deployment state.

Reproduce the focused contract with:

```bash
PYTHONPATH=. /home/dobo/work/cat_de_roman_esti/.venv/bin/python -m pytest tests/test_v59_human_anatomy_morphology.py -q
PYTHONPATH=. /home/dobo/work/cat_de_roman_esti/.venv/bin/python scripts/rank_games_pack.py
PYTHONPATH=. /home/dobo/work/cat_de_roman_esti/.venv/bin/python scripts/build_derived_catalog_v38.py
```
