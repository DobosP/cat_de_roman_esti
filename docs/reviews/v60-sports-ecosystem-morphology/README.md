# V60 sports-ecosystem-morphology funnel

This directory records the fixed 50-surface, two-reviewer funnel governed by ADR-0084.
It considered two genitive/dative forms for each of 25 existing sports-ecosystem
concepts. Forty-eight sense-qualified forms passed both reviews. `fileului` and
`fileurilor` were rejected because _fileu_ ordinarily also denotes general textile or
fishing netting, a shopping bag, or a hair net; the same articulated spelling can also
belong to _file_, a meat or fish fillet. No quota applied.

Qualifiers such as `golului marcat`, `sălilor de sport`, `porții de joc`, and
`fluierelor de arbitru` bind the accepted surfaces to sport rather than other ordinary
senses. The accepted forms add no concept or sense. They remain exact aliases consumed
only by typed Contexto input and otherwise-legal Lanț hops. The wave preserves
projections, graph topology, game records, ranking rows, the frozen derived payload,
session bounds, accounts, frontend, privacy, and deployment state.

Reproduce the focused contract with:

```bash
PYTHONPATH=. /home/dobo/work/cat_de_roman_esti/.venv/bin/python -m pytest tests/test_v60_sports_ecosystem_morphology.py -q
PYTHONPATH=. /home/dobo/work/cat_de_roman_esti/.venv/bin/python scripts/rank_games_pack.py
PYTHONPATH=. /home/dobo/work/cat_de_roman_esti/.venv/bin/python scripts/build_derived_catalog_v38.py
```
