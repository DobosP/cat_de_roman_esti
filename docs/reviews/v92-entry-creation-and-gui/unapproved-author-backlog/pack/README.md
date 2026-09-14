Valid until: any candidate, source, runtime, KG, inventory or rubric changes — then regenerate the author evidence.

Eight **unapproved** raw pack candidates: two Conexiuni boards, three Cald sau Rece targets and three Lanț routes. Import-shaped files live in `candidates/<category>/candidates.json`; their six arrays include empty `nodes`, `edges` and `alchimie`. No pack ID has been allocated and nothing has been staged. `preview_…` IDs and `pending` envelopes exist only for in-memory validator/dossier calls.

The Conexiuni boards use 32 distinct existing concepts and eight fresh groups. The first combines scoarță polysemy, culinary powders, finger-operated controls and watering equipment. The second combines forms of bate, leavening ingredients, zipper closures and milk-derived foods. Both pass strict prospective critique against the complete pack and durable tombstones, with zero unfair or contested tiles. An additional check against all five raw boards from the previous wave, including its discarded board, finds no three-of-four group reuse or half-board reskin. Author semantic reasoning and sources are in `sources-quality.json`; mechanical absence of edges does not establish a unique semantic partition.

The three targets are Nadia Comăneci, Ion Creangă and Alba Iulia. Each has at least five native incoming neighbors and clears the actual reachable/responsive floors. `contexto-api-probes.json` retains accepted guesses, ranks and wins. It also retains the weaker broad openers: sport is cool for Nadia; oraș is only warmish for Alba Iulia. Specific gymnastics, work/author and union/citadel routes provide the stronger cues.

Lanț proposes Vioară→Ateneul Român, Poarta Sărutului→Oltenia and Ștefan cel Mare→Bucovina. All nine native shortest two-step routes were solved through the actual API (18 accepted moves); responses and displayed relationship text are in `lant-api-routes.json`. The Enescu/festival bridges are more concrete than its extra classical-music route. The two geographical puzzles still need independent judgment of how satisfying their closely related alternatives feel. Current captions are used as-is.

Six salience warnings remain across five records. They concern familiar school/cultural identities under-rated by the graph and require explicit independent judgment; no thresholds were changed. `authoring-exclusions.json` records discarded group reskins, factual/semantic repairs and weaker ladder ideas. `scout_groups.py` is historical author exploration, contains rejected notions, and is not the candidate generator.

Reproduce the raw candidates and author evidence from the task worktree:

```bash
PYTHONPATH=. /home/dobo/work/cat_de_roman_esti/.venv/bin/python /home/dobo/work/_temp/feat__v92-entry-creation-02/session-02/pack/author_candidates.py
```

The candidate bytes, preview records and dossiers are deterministic. API response artifacts contain fresh ephemeral session IDs on each run. The generator asserts the served pack and KG hashes remain unchanged. Source citations are author evidence, never independent factual approval. Next: separate factual and quality coverage bound to each exact raw file; only then any authorized staging, fresh allocated-ID dossiers, analyst/adversarial gates, prospective critique and live selector/repeat/hint/privacy checks.
