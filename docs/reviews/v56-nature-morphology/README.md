# V56 nature-morphology funnel

This directory records the fixed 50-surface, two-reviewer funnel governed by ADR-0080.
It considered two genitive/dative forms for each of 25 existing animal, plant, weather,
and basic-science concepts. Forty-six forms passed both reviews. `peștelui` and `peștilor`
were rejected because _pește_ also denotes a procurer and its plural names Pisces;
`corpului` and `corpurilor` were rejected because _corp_ denotes an anatomical or physical
body, an organized group, and a geometric solid. No quota applied.

The accepted forms add no concept or sense. They remain exact aliases consumed only by
typed Contexto input and otherwise-legal Lanț hops. The wave preserves projections, graph
topology, game records, ranking rows, the frozen derived payload, session bounds, accounts,
frontend, privacy, and deployment state.

Reproduce the focused contract with:

```bash
PYTHONPATH=. /home/dobo/work/cat_de_roman_esti/.venv/bin/python -m pytest tests/test_v56_nature_morphology.py -q
PYTHONPATH=. /home/dobo/work/cat_de_roman_esti/.venv/bin/python scripts/rank_games_pack.py
PYTHONPATH=. /home/dobo/work/cat_de_roman_esti/.venv/bin/python scripts/build_derived_catalog_v38.py
```
