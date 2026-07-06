# Status — cat_de_roman_esti

_As of 2026-07-06. Update whenever `main` or the test baseline moves._
_Last verified: 2026-07-06_

## Phase

**v1.2 — text word-game arcade (web), on a densified KG.** The web app is a **text-only
arcade of four server-authoritative word games** over the KG (no graph visualization):
**Alchimie** (Infinite-Craft combine), **Cald sau Rece** (Contexto hot/cold + bounded
category clue), **Lanțul Cuvintelor** (word-ladder), **Conexiuni** (NYT-Connections
grouping + one redacted label-pattern clue after two mistakes). Each has difficulty
tiers, a seeded **daily challenge**, score + shareable result, and offline leaderboard/history.
Backed by `cat_de_roman_esti/wordgames/` (shared `service.py` over the offline KG + one
DRF views per game under `/api/wordgames/*`). The old graph SPA and its game-session
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
- **Real graph data:** run `romania-scraper kg build --commit` on the RO fleet host and point
  `ROEDU_API_URL` at live `ro_data_server`. _(blocked on fleet-host infra)_
- **Live end-to-end smoke** against `ro_data_server`. _(needs a live server)_
- **More content:** keep expanding nodes/puzzles/bridges via the content scripts.
