# Agent Map — cat_de_roman_esti

## What this repo owns
- Romanian-language app/game behavior: the six-game arcade (Django BFF + React SPA) and the terminal CLI hop game.
- Word-game session services and their tests.
- The curated content pipeline: fixtures, generation/validation scripts, and per-wave review evidence.

## Entry points
| Area | Path | Notes |
|---|---|---|
| Word games | `cat_de_roman_esti/wordgames/` | `service.py` owns sessions; one module per game (alchimie, conexiuni, contexto, intrusul, lant, perechi); `packs.py` loads the curated pack. |
| BFF | `cat_de_roman_esti/web/` | `settings.py`, `urls.py`, `http.py`, `legal.py`, `spa.py`; run with `python -m cat_de_roman_esti.web`. |
| CLI | `cat_de_roman_esti/cli.py`, `engine.py`, `graph.py`, `data.py` | Original semantic-hop game (`docs/ARCHITECTURE.md`). |
| Served KG build | `cat_de_roman_esti/fixtures/kg_sample.json` | V72 build. `kg_real.json` is a thin corpus export, **not** the served graph (data.py:27,34-36). |
| Curated pack | `cat_de_roman_esti/fixtures/games_pack.json` | Four pack games; Intrusul/Perechi come from `derived_catalog_v38.json`. |
| Frontend | `frontend/src/` | SPA screens/api/components (`frontend/README.md`). |
| Content scripts | `scripts/` | `validate_fixture.py`, `validate_games_pack.py`, `critique_pack.py`, `import_candidates.py`, versioned `apply_*`; `expand_content.py` is V2-only history. |
| Tests | `tests/` | 898 tests; `tests/accounts/` only with `CAT_ACCOUNTS_ENABLED=1`. |
| Wave evidence | `docs/reviews/<wave>/` | Dated per-wave records (history). |
| Workflows | `.claude/workflows/` | Claude-Code-only orchestration scripts (see `CLAUDE.md`). |
| Status | `docs/STATUS.md` | Single source of current truth. |

## Common task routes
| Task | Start here | Verify with |
|---|---|---|
| Word-game session fix | `cat_de_roman_esti/wordgames/service.py` + matching test | targeted pytest (`docs/agent-testing.md`) |
| New pack-only content wave | `docs/PACK_ONLY_CONTENT_WAVES.md`, `docs/CRITIQUE_RUBRIC.md`, newest review README | bound review, both validators + full pytest |
| BFF / API change | `cat_de_roman_esti/web/urls.py`, `docs/MOBILE_CONTRACT.md` | pytest + manifest hash in `docs/STATUS.md` |
| Frontend | `frontend/src/` | `npm test && npm run lint && npm run build`; commit `web/static` (ADR-0020) |
| Deploy | `docs/DEPLOY.md`, `docker-compose.prod.yml`, `deploy/Caddyfile` | smokes recorded in `docs/STATUS.md` |
| Docs | `docs/STATUS.md`, `README.md` | `check_docs.py` + `git diff --check` |

## Do not load by default
- `cat_de_roman_esti/web/static/` (tracked build bundle) and `frontend/node_modules/`.
- `docs/reviews/**/*.json` and the fixture JSONs in full (2,364 nodes — query them with a script).
- `docs/compliance/` unless the task is legal.
- Caches, logs, and env files.

## Known pitfalls
- Session stores must stay bounded; do not reintroduce unbounded in-memory growth.
- Use deterministic tests for TTL/max-size behavior.
- The `romania_scraper` venv has no Django — use the interpreter named in `docs/agent-testing.md`.
- Pointing `CAT_KG_FIXTURE` at `kg_real.json` silently empties every curated category (data.py:34-36).
- ADR-0020: frontend source changes ship the regenerated `web/static` bundle; backend-only changes must not.
- `tests/test_alchimie_sparse_recipes.py:211` asserts a 45 s wall-clock budget and fails under host load.
