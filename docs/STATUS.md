# Status — cat_de_roman_esti

_As of 2026-07-07. Update whenever `main` or the test baseline moves._
_Last verified: 2026-07-07_

## Phase

**v1.2 — text word-game arcade (web), on a densified KG.** The web app is a **text-only
arcade of four server-authoritative word games** over the KG (no graph visualization):
**Alchimie** (Infinite-Craft combine), **Cald sau Rece** (Contexto hot/cold + bounded
category clue), **Lanțul Cuvintelor** (word-ladder), **Conexiuni** (NYT-Connections
grouping + one redacted label-pattern clue after two mistakes). Each has difficulty
tiers, a seeded **daily challenge**, score + shareable result, and offline leaderboard/history.
Backed by `cat_de_roman_esti/wordgames/` (shared `service.py` over the offline KG + DRF
views per game under `/api/wordgames/*`). The BFF is **Django 5.2 + DRF** as of
2026-07-06 (`claude/django-backend` — fleet operational uniformity; ported from FastAPI
with a byte-compatible contract, verified against 46 golden flows + 194 tests; stateless
Django: no DB/migrations, WhiteNoise serves the SPA, uvicorn ASGI single-process). The old graph SPA and its game-session
API were **removed in `7308ce9` (2026-06-22)**; see `docs/adr/0001-pivot-to-word-game-arcade.md` —
**no graph UI unless Paul explicitly reopens it**.

**KG densified for richer play** (`scripts/densify_content.py` + `scripts/dense_data.json`):
**330 nodes / 750 edges / 108 puzzles** in `fixtures/kg_sample.json` (byte-identical copy in
`tests/fixtures/`), mean non-distractor degree **2.95 → 4.22**, incl. **198 cross-category
bridges**, plus a 2026-07-04 aviation-heritage batch (Vuia I, Vlaicu II, Coanda-1910,
Aeroportul Baneasa Aurel Vlaicu, Muzeul National al Aviatiei Romane), all fact-checked,
validator-green by construction. NOTE: the legacy
`kg_puzzles`/`HopGame`/CLI are unused by the word games but still validated.

_Pipeline note:_ the `romania_scraper → ro_data_server` corpus path is **blocked**
(`/mnt/roedu/data/processed/*` permission-restricted; `kg build` only sees `curriculum.db`,
78 nodes) — the curated **densification above is the delivered path**. The **terminal CLI**
remains the original `easy|hard` semantic-hop game.

## What's built

### Game core (Python, stdlib-only — powers the terminal CLI)
- `engine.py` `HopGame`, `graph.py`, `data.py`, vendored `roedu_client.py`, and `cli.py`
  remain the original offline/live semantic-hop core.

### Web app
- `cat_de_roman_esti/web/` — Django 5.2 + DRF BFF (fleet-uniform): urls.py mounts the four wordgame view modules
  under `/api/wordgames/{alchimie,contexto,lant,conexiuni}` (server-authoritative: hidden
  answers, bounded in-memory game stores, fail-closed board generation), plus `/api/health`
  and `/api/manifest` (offline-KG trust manifest: version + `schema_version` + content hash);
  stable OpenAPI operationIds (`<tag>_<name>`, e.g. `contexto_guess`); serves the built SPA
  (placeholder page if the build is absent). Offline KG loaded once at startup; live
  ro_data_server pull stays optional + fail-soft. Conexiuni fair-board generation remains
  bounded at 16 validated samples after the denser graph/content batch. Contexto exposes a
  one-use category clue after 3 counted guesses, with a score penalty and a
  hidden-answer rank view-model: guesses expose rank/temperature/closeness, while target
  id/label/description and any solution payload stay absent until win/give-up. Conexiuni
  uses a hidden-answer-safe public view model: before win/loss responses expose only
  public remaining tiles, solved/remaining counts, status/clue fields, and safe guess
  feedback; category keys, full category labels, solved group membership, and solution
  arrays are reveal-gated until terminal state. Its one-use redacted category-label
  pattern after two mistakes keeps the same score penalty and leak boundary.
- `frontend/` — React 18 + Vite + TS SPA: arcade home + four screens sharing `GameShell`,
  `DifficultyPicker`, `ResultCard`, `Toast`, `SoundToggle`; `framer-motion`, Web-Audio SFX,
  persisted mute, and lean deps (`react`, `react-dom`, `framer-motion`). Builds into
  `cat_de_roman_esti/web/static/`.
- **v1.2 UX:** share/copy payloads, offline localStorage leaderboard/history, daily/recent
  slices, bounded per-puzzle bests, "Record puzzle" badge, JSON import/export.

### Mobile contract (2026-07-04)
- `docs/MOBILE_CONTRACT.md`: stable operationIds + `GET /api/manifest` + hidden-answer
  invariants for roedu-mobile, including Contexto rank-bearing guesses with pre-reveal
  target id/label/solution absence; exports via `scripts/export_openapi.py` and
  `scripts/export_mobile_app_pack.py` (ADR-0006). Guarded by mobile/app-pack tests.

### Curated games layer (ADR-0011, 2026-07-07)
- `fixtures/games_pack.json` (+ byte-identical tests copy): curated instances per game with
  `category` / `source` (`user|ai|ai_corpus`) / `status`; only `approved` served. Taxonomy =
  8 KG categories + pop-culture shelf (`muzica`, `film_tv`, `meme_net`, `sport`,
  `viata_de_roman`, `gastronomie`) — single source `wordgames/categories.py`.
- All four create endpoints take additive `?category=`: curated-first, mined fallback
  (Conexiuni = curated-only per category, with authored `group_labels`); shared daily goes
  curated via rendezvous hash once a pool reaches 8. `GET /api/categories` feeds the SPA's
  CategoryPicker. `POST /api/submissions` (opt-in via `CAT_SUBMISSIONS_DIR`, pending queue)
  + `scripts/review_submissions.py` promote/reject. CI gate: `scripts/validate_games_pack.py`.
- **Content batch v5 (2026-07-07)**: codex-fleet generated, dual-verified (factual +
  game-quality Sonnet lenses), imported via `scripts/import_candidates.py` (re-derives all
  numbers on the merged graph; blocks cascade; factual-fix demotes to pending). Fixture now
  **~660 nodes / ~1870 edges / 168 puzzles** (`fixture-v5-pop`); pack ships **184 approved**
  (90 Conexiuni / 114 Contexto / 94 Lanț / 9 Alchimie) + 116 pending for review. All 6 pop
  categories playable in all four games. Lanț text-resolve is now target-aware for homonyms.
- **Alias + play-density batch v6 (ADR-0012, 2026-07-07)**: every node carries exact alias
  surface forms (inflections/synonyms/short titles — **2,829 aliases**, resolver-indexed,
  labels win; `alias_unique` + `label_style` validator classes, concepts ≤5 words); 161
  guess-vocabulary hub nodes + ~1,575 intuitive edges lift the graph to **~856 nodes /
  ~3,427 edges, mean degree 8.0** — degree≤2 dead-ends fell 170 → 13, so Cald sau Rece
  and Lanțul stay responsive. `scripts/import_enrichment.py` re-derives the whole pack
  on any graph merge.
- **Batch v7 (rounds 2+3, 2026-07-07)**: +867 aliases / +139 vocab nodes / +781 edges
  (vocab gap-fill) then a full round-2 instance batch on the dense graph. Graph now
  **~995 nodes / ~4,107 edges / 3,696 aliases**. Pack grew to **554 instances**
  (173 cx / 198 ct / 165 lt / 18 al — Alchimie pool tripled on the denser graph;
  ~390 approved, ~360 pending review). Known gap: universal guess-words ("mâncare",
  "apă", "muzică", "pădure") still absent — a targeted core-vocab fleet is the next batch.
- **Batch v8 core-vocab (2026-07-07)**: +309 everyday guess-word nodes / +842 aliases /
  +1,294 edges wired to anchors — the universal words a player types first ("mâncare",
  "apă", "pădure", "muzică", "biserică", "masă", "copil"…) now RESOLVE and come back warm
  in Cald sau Rece (verified). Graph **~1,304 nodes / ~5,400 edges / 4,538 aliases**.
  Perf: `densify_content` mixed-bucket puzzle regen is now capped (MIXED_POOL_CAP) so
  imports stay ~1 min instead of O(n²) blowup — kg_puzzles is legacy (terminal CLI only).

### Hardening
- `scripts/validate_fixture.py` — stdlib CI-gate validator, **13 invariant classes** (incl.
  no-distractor-shortcut-below-par); `tests/test_fixture_invariants.py` runs it every test.

- Deploy/docs: Multi-stage Docker, `run.sh`/`Makefile`, pinned web deps, and the existing
  docs/ADR set remain current; `docs/STATUS.md` is the current-truth index.

## Tests / quality
- Suite spans engine/graph/CLI/data-client, fixture invariants, web BFF, the four wordgames,
  session store, mobile + app-pack contracts.
- **CI** gates backend (`validate_fixture.py`, ruff, pytest on py3.11/3.12) and frontend
  (`npm ci`, eslint, `npm run build`).

## Run
```
./run.sh                 # local, offline, auto-port from 8000   (or: make run)
make dev                 # vite + uvicorn --reload (hot reload)
docker build -t cat-de-roman . && docker run --rm -p 8000:8000 cat-de-roman
# live data: ROEDU_API_URL=http://localhost:8077 ROEDU_API_KEY=cat-de-roman-dev ./run.sh
```

## Integration
Consumes `kg_nodes` / `kg_edges` / `kg_puzzles` from `ro_data_server` via the vendored
`RoeduClient` (api key `cat-de-roman-dev`, scope-isolated); producer artifacts live in
`romania_scraper`. Tagged app-pack ingest is fixture-backed for the shared RO-EDU contract.
Live pulls are capped (10k nodes / 50k edges / 5k puzzles); the live path itself remains
unexercised here.

## Next / future work
Post Django-port (2026-07-06 — that session was code-only by direction; these remain):
- **Docker gate:** the image has NOT been built since the FastAPI→Django port; the first
  `docker compose up --build` (or the CI docker job) validates the new `[web]` closure +
  unchanged CMD. Expected no-op — verify once, then drop this line.
- **Manual browser pass of session resume:** the resume flow (refresh/deep-link →
  "Joc reluat.") is verified at API level + typecheck only; click through all four games
  once in a real browser, incl. the expired-session fallback to the intro.
- **Regenerate the mobile TS client** from `scripts/export_openapi.py` when mobile work
  resumes: operationIds/paths are identical, but drf-spectacular's schema differs
  cosmetically from FastAPI's (component naming / nullability style).
- **Daily-puzzle discontinuity (one-time, accepted):** the BFS determinism fix maps
  seeds/dailies to different — now stable — puzzles than the FastAPI era.
- **Scaling constraint:** live games are in-memory (`SessionStore`) — the server MUST stay
  single-process (uvicorn 1 worker / gunicorn `--workers 1`). If real load arrives, move
  session state to shared storage (redis) before adding workers.
- **@roedu/ui consumption:** the vendored tarball (`frontend/vendor/roedu-ui-0.3.0.tgz`)
  is the working pattern; GitHub Packages publishing (PAT + publish step) remains the
  documented upgrade path if the fleet standardizes on it.

Standing items:
- **Real graph data:** run `romania-scraper kg build --commit` on the RO fleet host and point
  `ROEDU_API_URL` at live `ro_data_server`. _(blocked on fleet-host infra)_
- **Live end-to-end smoke** against `ro_data_server`. _(needs a live server)_
- **More content:** keep expanding nodes/puzzles/bridges via the content scripts.
