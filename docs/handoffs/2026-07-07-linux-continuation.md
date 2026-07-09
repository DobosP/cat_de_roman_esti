# Handoff — curated-games content program → Linux continuation

Valid until: Paul reviews the ~360-item pending pool — then treat as history.
(The core-vocab batch v8 LANDED on `main` `72f49d8`; the "in flight" section below is history.)

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

- `main` @ (v9 commit — see `git log`): curated games (ADR-0011) + alias/density (ADR-0012)
  + batches v5–v9. All gates green: pytest, ruff, `validate_fixture.py`,
  `validate_games_pack.py`, eslint, vite build.
- Graph: **~1,304 nodes / ~5,400 edges / 4,538 aliases**, mean degree ~7.9, degree≤2: 20.
- Pack (after v9): **737 instances — 585 approved / 152 pending** (238 cx / 275 ct /
  209 lt / 15 al). v9 re-reviewed all pending (154 promoted, 36 rejected) + added 135
  premium approved.
- Core complaint FIXED: everyday guess-words (mâncare/apă/pădure/muzică/biserică/masă/
  copil/film/carte/munte/drum/bani…) resolve and return warm in Cald sau Rece.
- Tools: `scripts/apply_rereview.py` (promote/reject pending from `<game>_verdicts.json`),
  `scripts/import_candidates.py --skip-merge` (instance-only, no graph change).
- Docs of record: `docs/STATUS.md`, `docs/adr/0011-*.md`, `docs/adr/0012-*.md`.

## ⚠️ Alchimie is degraded on the dense graph (needs a design fix before growing its pool)

The combine-closure (`_closure_generations`) now reaches **~the whole graph (1,299 of 1,304
nodes) from 6 seeds** — mean degree 8 means common-neighbors cascade everywhere. Consequences:
(1) every target is craftable in ~2 generations, so the game loses its "deliberate steps"
structure and becomes trivial; (2) each closure takes ~1–2s, so validating/mining Alchimie is
slow (a batch of 140 timed out; runtime `_build_session` mining fallback is also slow). v9
therefore **dropped 140 new Alchimie candidates** and kept only the 15 existing curated ones.
**Fix options (pick one before minting more Alchimie):** compute the closure over the
node's CATEGORY subgraph instead of the full graph (restores sparsity + speed); or cap
closure size / generation depth; or gate Alchimie combines to stronger edges only
(`strength ≥ τ`). This is a `wordgames/alchimie.py` + `wordgames/packs.py` change, then a
category-scoped Alchimie generation round. Until then Alchimie ships its 15 curated games.

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

## ⚠️ Scaling bottleneck discovered at ~1,350 nodes (densify puzzle regen)

`densify_content.run()` regenerates the whole `kg_puzzles` layer by doing an ALL-PAIRS
BFS per category **plus the `mixed` bucket over every node pair** — O(n²) BFS. At ~1,350
nodes the mixed bucket alone is ~900k pairs and the import blew past a 10-min foreground
cap (had to run it backgrounded: `python scripts/import_enrichment.py --dir … &`, then
gate). Each future batch makes this worse.

**The fix is safe and cheap** (do it before the next big batch): `kg_puzzles` is LEGACY —
only the terminal `HopGame`/CLI reads it; the web word games ignore it entirely
(`WordGameService` uses the graph, never `KgBundle.puzzles`). So the puzzle layer is now
pure validator overhead. Options: (a) cap the mixed-bucket pool in
`densify_content.run()` to high-salience nodes (puzzles already need `salience ≥ 0.42`
on an endpoint and only 6/bucket are kept — the validator VALIDATES existing puzzles, it
does NOT regenerate, so shrinking the generation pool is safe and won't fail
`validate_fixture.py`); or (b) stop regenerating puzzles for categories that already have
6 valid in-band ones. Either drops the import back to seconds. Don't touch the validator's
puzzle checks — only the generator in densify.

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
