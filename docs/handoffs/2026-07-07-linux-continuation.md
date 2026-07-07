# Handoff — curated-games content program → Linux continuation

Valid until: the round-2/round-3 content batches land on `main` and Paul reviews the
pending pool — then treat as history.

Written 2026-07-07 on the Windows box (Claude Code session, ADR-0011 + ADR-0012 work).

## Where main is

- `main` @ `e80a6e7` (pushed): curated games layer (ADR-0011) + alias/play-density
  enrichment (ADR-0012). All gates green: pytest, ruff, `validate_fixture.py`,
  `validate_games_pack.py`, eslint, vite build.
- Graph: ~856 nodes / ~3,427 edges / 2,829 aliases, mean degree 8.0 (`fixture-v6-enriched`).
- Pack: 184+ approved instances (90 cx / 114 ct / 91 lt / 8 al) + ~116 `pending`.
- Docs of record: `docs/STATUS.md`, `docs/adr/0011-*.md`, `docs/adr/0012-*.md`.

## In flight at write time (Windows session)

Two codex-fleet batches were generating when this was written; the session intended to
import + land them (check `git log origin/main` — if you see a commit mentioning
"round-2 instances" / "vocab gap-fill v7", they LANDED and this section is history):

1. **Round-2 instances** (`cat-instances-round2`): 6 cx / 6 ct / 8 lt / 8 al per
   category on the dense graph — meant to fatten the thin pools (alchimie 8, știință
   conexiuni 0, meme_net lant 0).
2. **Vocab gap-fill round 3** (`cat-vocab-round3`): ≤10 everyday guess-words/category,
   ≤40 extra aliases/category, 30–70 edges lifting the last 63 degree≤3 nodes.

If they did NOT land: the raw outputs live only in this Windows session's scratchpad —
**regenerate on Linux instead of hunting for them** (cheap, ~30 min of Codex): the whole
pipeline is in the repo, see next section.

## The content pipeline (all committed, OS-agnostic)

```
inventory export (ad-hoc python over fixtures/kg_sample.json — see the TSV shapes below)
   → codex fleet generates per-category candidates.json (+ Sonnet verify JSONs)
   → scripts/import_candidates.py --dir <dir> [--skip-merge]   # game INSTANCES batches
   → scripts/import_enrichment.py --dir <dir>                  # alias/node/edge batches
   → both validators + pytest  → commit both fixture copies + both pack copies
```

- `import_candidates.py`: expects `<dir>/<cat>/candidates.json`
  (`{nodes,edges,conexiuni,contexto,lant,alchimie}`) + `verify_factual.json` +
  `verify_quality.json`. Quality `keep`→approved, `fix`→pending, factual `fix` demotes,
  `block` cascades. Re-derives every number on the merged graph — never trusts the
  generator. `--skip-merge` = pack-only (no new nodes/edges).
- `import_enrichment.py`: expects `<dir>/<cat>/candidates.json`
  (`{aliases,nodes,edges}`) + `verify.json`. Alias hygiene (one meaning per typed
  word), duplicate-concept remap, then FULL pack re-derivation.
- Verifier ref grammar: `conexiuni[3]` / node id / `edge src->dst` /
  `alias:<node_id>:<alias text>`.
- After ANY fixture change: `python scripts/export_mobile_app_pack.py
  tests/fixtures/cat_mobile_app_pack_contract.json` (snapshot test fails otherwise).

## Follow-ups, in priority order

1. **Review the ~116 `pending` pack items** (many failed one rubric axis only).
   Flip `status` to `approved`/`rejected` in BOTH `cat_de_roman_esti/fixtures/games_pack.json`
   and `tests/fixtures/games_pack.json` (byte-identical!), then
   `python scripts/validate_games_pack.py && pytest -q`.
2. **Docker gate** (standing since the Django port): first `docker compose up --build`
   validates the `[web]` closure — still not run.
3. **User submissions end-to-end**: backend is live (`POST /api/submissions`, needs
   `CAT_SUBMISSIONS_DIR`; compose already mounts a volume). Frontend submission UI not
   built. Review queue: `python scripts/review_submissions.py list|promote|reject`.
4. **ai_corpus lane**: when the scraper gold layer produces clean data, generate
   candidates in the same JSON shapes and reuse the two importers unchanged
   (`source: ai_corpus` is already a valid enum).
5. Small tails: ~13 degree≤2 nodes; a few generic guess words still unknown
   (e.g. "mâncare" pre-round-3); alchimie pool thinnest of the four.

## Gotchas (hard-won today)

- Codex JSON generation can TRUNCATE silently on long outputs — always check counts
  (e.g. edges) against what the brief requested before importing.
- Sonnet verifiers produce false positives — a final editorial pass matters. Overridden
  today: Gică Popescu WAS Galatasaray's captain; Covrigii de Buzău DO hold EU PGI (2022);
  "#eroina" IS the official "Sub pielea mea" subtitle.
- Dense graph ⇒ same-label homonyms both reachable ⇒ Lanț resolve is target-aware now;
  keep labels collision-free (validator `alias_unique` enforces).
- Parallel sessions switch this repo's checked-out branch — verify `git branch` after
  long waits.
- Linux venv per repo docs: `/home/dobo/work/romania_scraper/.venv` is the shared one;
  cat has its own `.venv` on Windows — on Linux follow `AGENTS.md` command paths.
