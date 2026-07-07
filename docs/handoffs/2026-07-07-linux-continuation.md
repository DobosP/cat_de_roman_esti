# Handoff — curated-games content program → Linux continuation

Valid until: the core-vocab batch lands on `main` and Paul reviews the pending pool —
then treat as history.

Written 2026-07-07 on the Windows box (Claude Code session, ADR-0011 + ADR-0012 work).
Last updated after batch v7 landed.

## How the graph travels between machines (Windows ⇄ Linux)

**The graph IS data committed to this repo — it travels through git, not the machine.**
- The whole graph is four tracked files: `cat_de_roman_esti/fixtures/kg_sample.json` +
  `tests/fixtures/kg_sample.json` (KG: nodes/edges/aliases) and the two
  `fixtures/games_pack.json` copies (curated games). All pushed to `origin/main`.
- On Linux: `git pull` gives you the **byte-identical** graph. No machine-local state,
  no export step. Same when you return to this Windows box later.
- **What does NOT travel:** the raw Codex fleet outputs (`candidates.json` etc.) live in
  the Windows session's scratchpad (`%TEMP%\claude\...\<session-id>\scratchpad`), which is
  session- and machine-local. A batch only persists once it is IMPORTED into the fixture
  and committed. So: land fleets before relying on them; never plan to `git pull` raw
  fleet output — regenerate it instead (cheap, reproducible; see the pipeline below).
- The importers write BOTH copies of each fixture and both are validated as byte-identical
  — never hand-edit one copy.

## Where main is

- `main` @ `1936c37` (pushed): curated games (ADR-0011) + alias/density (ADR-0012) +
  batch v7 (round-2 instances + vocab gap-fill). All gates green: pytest, ruff,
  `validate_fixture.py`, `validate_games_pack.py`, eslint, vite build.
- Graph: **~995 nodes / ~4,107 edges / 3,696 aliases**, mean degree ~7.8.
- Pack: **554 instances** — 173 cx / 198 ct / 165 lt / 18 al (~390 approved, ~360
  `pending` review; Alchimie pool tripled from 7 → 18 on the dense graph).
- Docs of record: `docs/STATUS.md`, `docs/adr/0011-*.md`, `docs/adr/0012-*.md`.

## In flight at write time (Windows session)

**One codex-fleet batch running** — `cat-core-vocab` (run id in `/workflows`). Check
`git log origin/main`: a commit mentioning "core-vocab" means it LANDED and this
section is history.

- **Core universal guess-words** (`cat-core-vocab`): 20–30 everyday words per category
  (mâncare/apă/pădure/muzică/biserică/masă class — the words a player types FIRST that
  were STILL missing after v7), each with 2–4 inflection aliases and **3–6 edges to
  existing anchor nodes** so they're findable, not islands. Verifier flags near-islands
  (<2 edges) as `fix`. Every node carries an explicit `category` (one of the 14).
- **Land it with:** `python scripts/import_enrichment.py --dir <scratch>/vocab4`
  (nodes+edges+aliases → graph merge → pack re-derivation → both validators). Then
  regenerate the mobile snapshot and run the full gate (see pipeline below).

If it did NOT land: the raw outputs live only in this Windows session's scratchpad —
**regenerate on Linux instead of hunting for them** (~30 min of Codex). The reusable
workflow script is saved at
`.claude/.../workflows/scripts/cat-core-vocab-wf_bce79175-63d.js`; or just re-author the
brief (it's short) — the whole pipeline is in the repo, see next section.

### Known remaining gap this batch targets
After v7, `svc.resolve()` still returned None for "mâncare", "apă", "muzică", "pădure",
"biserică", "masă", "copil", "automobil" — the category workers added domain concepts but
skipped the truly universal vocabulary. `cat-core-vocab` is the fix. After landing, smoke-
test: `svc.resolve("mancare")` etc. should return a node, and Contexto guesses of those
words should come back warm instead of "Nu cunosc acest concept".

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
