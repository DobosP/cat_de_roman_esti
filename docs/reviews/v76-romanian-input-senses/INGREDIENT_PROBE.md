# V76 served-KG ingredient and holiday probe

Valid until: the next relevant graph or input wave — then treat as history.

Read-only probe against `cat_de_roman_esti/fixtures/kg_sample.json` at `d127abb91538a10cdf1297b418f44defb61262e0`.

| Target | Existing ID | Input / resolution | Directed distance to target | Finding |
|---|---|---|---:|---|
| Cozonac | `n_gas_cozonac` | Făină → `n_v24_food_pantry_faina`; zahăr → `n_v24_food_pantry_zahar` | 4 / 4 | Both inputs exist; neither has a direct edge to target. |
| Pâine de casă | `n_gas_paine_de_casa` | Făină → `n_v24_food_pantry_faina` | 4 | Input exists; no direct edge. `cuptor` resolves to no node. |
| Clătite | `n_v3gas_clatite` | Făină → `n_v24_food_pantry_faina`; ouă → `n_v4gas_ou`; lapte → `n_v4gas_lapte` | 6 / 1 / 2 | Făină exists but has no direct edge; egg and milk already give short routes. |

Holiday/input behavior: `Crăciun`, `sărbători`, and `Revelion` resolve to no node. `Paște` resolves to `n_v3gas_paste` (Paste, food), hence a true lexical/sense collision rather than a missing graph edge. Existing holiday-meal nodes are `n_gas_masa_craciun`, `n_gas_masa_paste`, `n_gas_mese_sarbatori`; their longer aliases deliberately do not claim the bare holiday terms.

A minimal topology hypothesis worth separately reviewing is three directed existing-node edges from `n_v24_food_pantry_faina` to the three existing dish nodes. The current importer accepts topology candidates through normal `import_candidates.py --dir` (not `--pack-only`), with complete factual review coverage for edge refs and transactional `densify_content.run`; the edge schema is `src`, `dst`, `relation`, `weight`. The analogous existing edges use `part_of` from ingredient to dish (`Ou → Clătite`, `Apă → Pâine de casă`, `Fruct → Cozonac`), so a proposed edge needs to justify that established direction, its label and strength rather than introduce a new relation. This is not a promotion recommendation: a topology change re-derives the pack and can affect all game mechanics.
