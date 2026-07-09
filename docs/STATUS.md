# Status — cat_de_roman_esti

_As of 2026-07-09. Update whenever `main` or the test baseline moves._
_Last verified: 2026-07-09 (v12.1 diacritics: data gates green — `validate_games_pack.py` + `validate_fixture.py`
+ 81 stdlib pytest; the Django/DRF web-layer suite needs a Django venv, absent on this host, and runs in CI)._

**Latest — v12.1 KG-diacritics pass (2026-07-09):** restored Romanian diacritics on **134 KG node labels**
that were stored ASCII-folded (`Stefan cel Mare`→`Ștefan cel Mare`, `Tara Romaneasca`→`Țara Românească`,
`Nadia Comaneci`→`Nadia Comăneci`, `Romania`→`România`…) via a 16-worker Codex fleet, each fix gated by the
invariant `normalize(new)==normalize(old)` (diacritics/case only — 0 letter changes, so `alias_unique`/resolver
are provably unaffected since both key on the accent-stripped form). Display-only quality: no resolution/pack
change (games reference node ids). Mobile app-pack snapshot regenerated; same fixes mirrored into
`scripts/dense_data.json` (+43) / `expansion_data.json` (+17) so rebuilds don't regress. Remaining v12.1 work
(member-swaps, tier recalibration, 15 modify calls) still in `docs/handoffs/2026-07-09-v12-continuation.md`.

**v12 quality-consolidation pass (2026-07-09):** a full Codex-fleet editorial audit of all 865
games (56 game×category workers) → **adversarial re-check** (53 defender/skeptic workers, which overturned
**35% of flags as false positives** — e.g. the correct "Ioni de manual" boards, since I.L. = _Ion_ Luca
Caragiale) → exact-duplicate scan. Structural apply: **removed 101** (92 exact duplicates incl. 78
same-target Contexto, + 9 confirmed-broken approved boards e.g. Paris/Medicină miscategorised as
"personalități"), **demoted 29** off-theme approved boards to pending, **promoted 86** independently-verified
pending candidates. Pack **865 → 764 games (657 → 638 approved / 126 pending)**, redundancy-free; every
category keeps ≥3 approved boards per game. Graph unchanged (**1,453 nodes / 5,644 edges / 4,684 aliases**).
Deferred to **v12.1** (35 content fixes incl. a systemic KG missing-diacritics finding + 15 modify calls):
`docs/handoffs/2026-07-09-v12-continuation.md`.

**v11 curation-fix pass (2026-07-09):** 130 editorial fixes to the v11 batch (label
precision, alias hygiene, distractor-relation correctness, board fairness; 2 correct overrides of
verifier false-positives) via a two-round codex fix → independent-reverify pipeline, rebuilt from the
pre-v11 base through `import_candidates.py`. Graph **1,453 nodes / 5,644 edges / 4,684 aliases**; pack
**865 games (657 approved / 208 pending)** — the fixes rescued 28 boards the first import had dropped.
`docs/COMPARISON.md` + artifact comparators updated to the English originals (Wordle RO → Wordle).

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
- **Batch v9 (2026-07-07)** — quality consolidation + premium content. Re-reviewed all 258
  pending games (4 Codex judges, strict per-game rubric): **154 promoted to approved**, 36
  rejected, 68 kept pending (`scripts/apply_rereview.py`). Plus a premium instance batch
  (dual-verified) on the dense graph: +135 approved Conexiuni/Contexto/Lanț. Pack now
  **737 instances — 585 approved / 152 pending** (238 cx / 275 ct / 209 lt / 15 al).
  ⚠️ **Alchimie deferred on the dense graph:** the combine-closure now reaches ~the whole
  graph (1,299 nodes from 6 seeds), so every target is craftable in ~2 gens — the game loses
  structure AND closure validation is slow. 140 new Alchimie candidates were dropped; the
  15 curated ones stay. Alchimie needs a design fix (closure over the CATEGORY subgraph, or
  a size cap) before its pool grows — see the handoff.
- **Batch v10 (ADR-0013, 2026-07-07) — Alchimie fixed.** Combines are now category-scoped:
  `common_neighbors(a,b,category=…)` restricts the closure to a theme (~90 nodes / 0.005s
  vs the whole graph / 1.5s), so targets regain real depth (gens 1–5). Every Alchimie game
  is themed; mined games pick a category. Pack re-derived under scoping (4 legacy dropped),
  then the pool regrown from **9 → 48 approved** (+48 pending) via algorithmically-minted,
  quality-judged scoped instances. Pack now **818 instances / 620 approved**. All four games
  are now healthy on the dense graph.
- **Batch v11 (2026-07-07) — refinement + difficulty calibration + comparison.**
  Audit-driven: merged **10 duplicate concepts** (survivor absorbs edges+aliases;
  games redirected; Moldova kept as homonym); **recalibrated salience** (declared +
  degree blend, rank-normalized) so tiers are balanced (easy 441 / med 517 / **hard
  336**, was 906/382/**16**). Difficulty now selects meaningfully: Contexto usor 0.77
  → greu 0.32; Lanț endpoint-salience weighted per tier (usor 16 / normal 9 / greu 2).
  `scripts/refine_dataset.py` (+ extracted `densify_content.rebuild`). Graph now
  **1,294 nodes / 5,370 edges / 4,538 aliases**; pack **815 (619 approved)**.
  `docs/COMPARISON.md` positions the game vs NYT Connections / Contexto / Infinite
  Craft / Wordle RO (only 4-format curated-RO-cultural game; verified-bounded vs
  uncurated-infinite).
- **v11 content add**: +145 high-interest nodes (realistic salience — anti-inflation
  verifier) + cross-category bridges + 23 premium Conexiuni boards; alias hygiene on
  import dropped 6 duplicate-label nodes + 36 colliding aliases. Graph now **1,449 nodes
  / 5,632 edges**; pack **836 (631 approved / 205 pending)**. Tiers stay balanced
  (easy 479 / med 634 / hard 336).
- **Batch v12 (2026-07-09) — quality consolidation (audit → adversarial verify → apply).**
  Two Codex fleets: (1) 56 workers audited every game per game×category on a resolved
  (id→label+description) view; (2) 53 workers independently re-checked the 249 highest-stakes
  verdicts with a **defender bias on served content / skeptic bias on promotes** — overturning
  **35%** as false positives (the load-bearing safeguard: the first pass confidently mis-flagged
  correct boards). Applied structurally to both pack copies (status/existence only, no content
  authoring): **−101 remove** (exact-dedup 92 + 9 verified-broken), **−29 demote**, **+86 promote**.
  Contexto same-target duplicates were the dominant defect (78 removed — no two served Contexto games
  now share a hidden target). Pack **764 (638 approved / 126 pending)**; per-game approved:
  195 cx / 182 ct / 186 lt / 75 al. Pure data change — `validate_games_pack.py` (playability of all
  approved via the same runtime functions the server uses) + `validate_fixture.py` green. Deferred
  content fixes (diacritics/member-swaps/tier recalibration/modifies) tracked for v12.1.

### Hardening
- `scripts/validate_fixture.py` — stdlib CI-gate validator, **15 invariant classes** (incl.
  no-distractor-shortcut-below-par, plus `alias_unique` + `label_style` from ADR-0012);
  `tests/test_fixture_invariants.py` runs it every test. `scripts/validate_games_pack.py`
  is the sibling gate for the curated pack.

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
