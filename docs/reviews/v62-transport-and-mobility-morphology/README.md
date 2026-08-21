# V62 transport-and-mobility-morphology funnel

This directory records the fixed 50-surface, two-reviewer funnel governed by ADR-0086.
It considered two genitive/dative forms for each of 25 existing transport and mobility
concepts. Forty-eight sense-qualified forms passed both reviews. `portului` and
`porturilor` were rejected because _port_ ordinarily denotes not only a harbor facility
or port city, but also carrying or possession, conduct or bearing, traditional clothing,
and a computer-network or USB interface. No quota applied.

Qualifiers such as `trenului de călători`, `autobuzelor urbane`, `canalului navigabil`,
and `pașapoartelor de călătorie` bind the accepted surfaces to one existing transport or
travel sense. The accepted forms add no concept or sense. They remain exact aliases
consumed only by typed Contexto input and otherwise-legal Lanț hops. The wave preserves
projections, graph topology, game records, ranking rows, the frozen derived payload,
session bounds, accounts, frontend, privacy, and deployment state.

Reproduce the focused contract with:

```bash
PYTHONPATH=. /home/dobo/work/cat_de_roman_esti/.venv/bin/python -m pytest tests/test_v62_transport_and_mobility_morphology.py -q
PYTHONPATH=. /home/dobo/work/cat_de_roman_esti/.venv/bin/python scripts/rank_games_pack.py
PYTHONPATH=. /home/dobo/work/cat_de_roman_esti/.venv/bin/python scripts/build_derived_catalog_v38.py
```
