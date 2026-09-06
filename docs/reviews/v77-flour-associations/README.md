# V77 flour associations

Valid until: the next relevant graph or food-target wave — then treat as history.

V77 adds two reviewed ingredient routes to the existing graph using
[ADR-0108](../../adr/0108-add-bounded-flour-ingredient-associations.md) and the
rollback-safe V24 enrichment tool. It adds no targets or aliases. Cozonac, Pâine
de casă and Clătite remain rejected V75 candidates awaiting a fresh review.

## Player-facing result

The fixed-target API probes use ordinary `făină` input and the actual Contexto
scoring path. These probes do not add the targets to the playable pack.

| Fixed target | Before: hops / rank / temperature | V77 |
|---|---|---|
| Cozonac | 4 / 498 / Rece | 1 / 2 / Fierbinte |
| Pâine de casă — deferred | 4 / 603 / Rece | 4 / 577 / Rece |
| Clătite | 6 / 1696 / Inghetat | 1 / 2 / Fierbinte |

The 14 final V77 regressions cover spelling variants, private answers, repeats,
resume, wins, directed Lanț steps and exact artifact preservation. They also
prevent the rejected bread shortcut from making flour warm for a fountain pen.
Paște/Paste protections remain intact. The initial three-edge experiment had
15 failing route checks before application; the final batch is narrower.

The bread association is factually valid but fails gameplay review: through
Pâine de casă → Lapte și corn → Stiloul cu rezervor, it made flour `Caldut` for a
fountain pen. Deferring it leaves that unrelated guess `Foarte rece` and keeps
bread at four hops. This is why validators alone cannot approve an enrichment.

## Preservation and graph effects

Baseline is local main `9ef9dc71fd26896596f513299137cfa02f26e767`.
The generated difference is exactly two non-distractor, one-way `part_of` links
and three incident-degree counts. All 2,364 node meanings and 8,450 aliases remain
exact. The builder recomputed all 180 terminal puzzles and produced identical
puzzle records. No previous edge changed.

Both full pack copies remain byte-identical: 620 records, including all eight
pending holds. All 620 board-ranking rows, their eligibility/weights and all 336
frozen Intrusul/Perechi boards remain exact. Their wrappers bind the new KG hash.
The mobile snapshot carries the two public links and new manifest hash.

Graph routes affect Contexto guess ranks beyond the repaired targets: 95
approved target sessions have changed flour/sugar paths, with unchanged
reachability and responsive counts rising by at most two. Of 52,043 changed
ordinal guess ranks, 51,854 move down just one or two places as flour/sugar move
ahead. These are guess ranks, separate from unchanged board-selection rankings.
The only newly warm cross-category cases are culinary/holiday associations;
[IMPACT_REVIEW](IMPACT_REVIEW.md) records the full refute-first review, the rejected
bread route and direction differences between runtime and offline critique.

The generator also advances new edge IDs above the largest present numeric
`de`/`dd` suffix. The initial experiment reused V43-retired e-SIGUR edge IDs;
the final IDs are `de8555` and `de8556`, and the original retirement check passes.
A focused merge-path test covers gaps, mixed prefixes and deterministic repeats.

## Evidence and reproduction

- `review-manifest.json`: archive/source SHA-256 inventory for the final reviewed scope.
- `FACTUAL_REVIEW.md` and `factual-review.json`: independent recipe/source review
  of all three associations, including direction and editorial weight.
- `artifact-delta.json`: exact before/after artifact hashes, original metadata,
  the two generated edge records and three node-degree changes. The V77 test
  reverses only the allowed delta and reconstructs the exact V76 fixture hash.
- `impact-final.json` / `impact-rejected-bread.json`: independent full-pack impact
  evidence for the final batch and the rejected trial; `impact.py.txt` preserves
  its runner and IMPACT_REVIEW records the invocation.
- `critique-comparison.json`: unchanged findings/payloads for all eight pending
  holds, ten final candidate-affected Conexiuni boards and both V75 targets.
- `implementation-review.json`: independent review bound to the final module,
  wrapper, regression tests, graph and factual review; one missing ranking-payload
  assertion was added and independently verified.
- `runtime-openers.json`: before/after API evidence for the three proposed food
  targets, both already-served V75 targets and the fountain-pen guard. Archived
  `.py.txt` scripts retain original local reproduction paths; set their ROOT and
  scratch paths for another checkout. Full intermediate dossiers are reproducible
  but not stored; the compact comparison includes their exact digests.

Using V77 tooling with the generated artifacts restored from the baseline, run
`PYTHONPATH=. <python> scripts/apply_flour_associations_v77.py`; regenerate the
ranking and frozen catalog with their respective `--write` builders. The graph
transaction validates fixtures and pack, refuses approved-record changes and
refreshes mobile. Running it again fails closed without modifying artifacts.
The checked-in runtime catalog digest advances only after the frozen board
payload is confirmed exact. Do not run historical wave modules on the new graph.

Verification totals are recorded in [STATUS](../../STATUS.md). Reviews are
independently authored Codex-agent judgments, not human playtests. This local
wave does not change the public-rollout gates or enable accounts.

Next bounded wave: re-evaluate Cozonac and Clătite against the repaired graph,
with fresh ordinary-guess probes and strict independent candidate review.
The bread route and missing holiday/oven concepts remain separate questions; they must not be
substituted with unrelated aliases to make a target pass.
