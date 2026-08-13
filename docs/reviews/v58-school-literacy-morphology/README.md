# V58 school-literacy-morphology funnel

This directory records the fixed 50-surface, two-reviewer funnel governed by ADR-0082.
It considered two genitive/dative forms for each of 25 existing school, language, and
literacy concepts. Forty-eight forms passed both reviews. `cărții` and `cărților` were
rejected because _carte_ ordinarily denotes a book, playing card, or official document.
No quota applied.

Potentially broad literacy nouns use qualified forms such as `bibliotecii școlare`,
`capitolului de carte`, `jurnalului personal`, and `revistei literare`. The accepted
forms add no concept or sense. They remain exact aliases consumed only by typed Contexto
input and otherwise-legal Lanț hops. The wave preserves projections, graph topology,
game records, ranking rows, the frozen derived payload, session bounds, accounts,
frontend, privacy, and deployment state.

Reproduce the focused contract with:

```bash
PYTHONPATH=. /home/dobo/work/cat_de_roman_esti/.venv/bin/python -m pytest tests/test_v58_school_literacy_morphology.py -q
PYTHONPATH=. /home/dobo/work/cat_de_roman_esti/.venv/bin/python scripts/rank_games_pack.py
PYTHONPATH=. /home/dobo/work/cat_de_roman_esti/.venv/bin/python scripts/build_derived_catalog_v38.py
```
