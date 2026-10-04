# Agent Map — cat_de_roman_esti

## What this repo owns
- Romanian-language app/game behavior: the six-game arcade (Go backend + React SPA; Django offline oracle) and the terminal CLI hop game.
- Word-game session services and their tests.
- The curated content pipeline: fixtures, generation/validation scripts, and per-wave review evidence.

## Entry points
| Area | Path | Notes |
|---|---|---|
| Word games | `go-backend/internal/` | Per-game native packages, bounded `session` stores and sealed `content` export; Python `wordgames/` is the offline oracle. |
| Native HTTP | `go-backend/internal/httpapi`, `go-backend/cmd/cat-server` | Games, accounts, proposals, metadata/legal/static serving; Go-only runtime. |
| Accounts/auth | `go-backend/internal/accounts`, `shared-go/authcore` | Durable identity/consent/private progress; providers conditional; off in production. |
| CLI | `cat_de_roman_esti/cli.py`, `engine.py`, `graph.py`, `data.py` | Original semantic-hop game (`docs/ARCHITECTURE.md`). |
| Served KG build | `cat_de_roman_esti/fixtures/kg_sample.json` | V90 build; integration/landing state in STATUS. `kg_real.json` is a thin corpus export, **not** the served graph (data.py:27,34-36). |
| Curated pack | `cat_de_roman_esti/fixtures/games_pack.json` | Four pack games; Intrusul/Perechi come from `derived_catalog_v38.json`. |
| Frontend | `frontend/src/` | SPA screens/api/components (`frontend/README.md`). |
| Content scripts | `scripts/` | Validators, critique, import and review artifact assembly; `expand_content.py` is V2-only history. |
| Tests | `go-backend/**`, `shared-go/authcore/**`, `tests/` | Native race/PG contracts first; Python content/differential oracles separately; current totals in STATUS. |
| Wave evidence | `docs/reviews/<wave>/` | Dated per-wave records (history). |
| Workflows | `.claude/workflows/` | Claude-Code-only orchestration scripts (see `CLAUDE.md`). |
| Status | `docs/STATUS.md` | Single source of current truth. |

## Common task routes
| Task | Start here | Verify with |
|---|---|---|
| Refine or expand game content | [Repository content skill](../.agents/skills/romanian-game-content/SKILL.md), [ADR-0156](adr/0156-two-track-content-growth.md) | refinement, discovery pool and existing promotion gates |
| Start the next version | `docs/adr/0113-outcome-based-version-batches.md` + current STATUS backlog | explicit player outcomes, focused development checks, integrated gates and `scripts/report_content_delta.py` |
| Word-game session fix | `go-backend/internal/session` + matching engine/HTTP test; Python oracle for comparison | native race/vet + targeted parity (`docs/agent-testing.md`) |
| New pack-only content wave | `docs/PACK_ONLY_CONTENT_WAVES.md`, `docs/CRITIQUE_RUBRIC.md`, newest review README | bound review, both validators + full pytest |
| Serving API change | `go-backend/internal/httpapi`, `docs/MOBILE_CONTRACT.md` | native race/vet/HTTP parity + manifest hash in `docs/STATUS.md` |
| Frontend | `frontend/src/` | `npm test && npm run lint && npm run build`; commit `web/static` (ADR-0020) |
| Deploy | `docs/DEPLOY.md`, `docker-compose.prod.yml`, `deploy/Caddyfile` | smokes recorded in `docs/STATUS.md` |
| Docs | `docs/STATUS.md`, `README.md` | `check_docs.py` + `git diff --check` |

## Do not load by default
- `cat_de_roman_esti/web/static/` (tracked build bundle) and `frontend/node_modules/`.
- `docs/reviews/**/*.json` and the fixture JSONs in full (query large inventories with a script).
- `docs/compliance/` unless the task is legal.
- Caches, logs, and env files.

## Known pitfalls
- Session stores must stay bounded; do not reintroduce unbounded in-memory growth.
- Use deterministic tests for TTL/max-size behavior.
- The `romania_scraper` venv has no Django — use the interpreter named in `docs/agent-testing.md`.
- Go refuses `CAT_KG_FIXTURE`/pack/ranking overrides; approved content needs export + rebuild.
  Only the Python oracle/terminal client can load `kg_real.json`, which lacks curated category coverage.
- ADR-0020: frontend source changes ship the regenerated `web/static` bundle; backend-only changes must not.
- `tests/test_alchimie_sparse_recipes.py:293` asserts a 45 s wall-clock budget and fails under host load.
