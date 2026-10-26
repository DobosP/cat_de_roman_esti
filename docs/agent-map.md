# Agent Map — cat_de_roman_esti

## What this repo owns
- Romanian-language game behavior: Go arcade + current Preact SPA (all eight app paths in the M3 source, ADR-0202/0204); accepted rollout is in STATUS. Frozen React is retained for explicit rollback; Django is an offline oracle. The terminal CLI remains the hop game.
- Word-game session services and their tests.
- The curated content pipeline: fixtures, generation/validation scripts, and per-wave review evidence.

## Entry points
| Area | Path | Notes |
|---|---|---|
| Word games | `go-backend/internal/` | Per-game native packages, bounded `session` stores and sealed `content` export; Python `wordgames/` is the offline oracle. |
| Native HTTP | `go-backend/internal/httpapi`, `go-backend/cmd/cat-server` | Games, accounts, proposals, metadata/legal/static serving; Go-only runtime. |
| Accounts/auth | `go-backend/internal/accounts`, `shared-go/authcore` | Durable identity/consent/private progress; providers conditional; off in production. |
| CLI/REST | `cat-de-roman`, `go-backend/internal/hopcli`, `roeduclient` | Native original hop game and bounded provenance client; Python retained reference. |
| Served KG build | `cat_de_roman_esti/fixtures/kg_sample.json` | V90 build; integration/landing state in STATUS. `kg_real.json` is a thin corpus export, **not** the served graph (data.py:27,34-36). |
| Curated pack | `cat_de_roman_esti/fixtures/games_pack.json` | Four pack games; Intrusul/Perechi come from `derived_catalog_v38.json`. |
| Frontend | `frontend/src/` | SPA screens/api/components (`frontend/README.md`). |
| Content tools | `go-backend/internal/contentbuild`, `contentops`, `contentrails` | Native source/review/builder rails; Python scripts and `expand_content.py` retained history. |
| Tests | `go-backend/**`, `shared-go/authcore/**`, `tests/` | Native race/PG contracts first; Python content/differential oracles separately; current totals in STATUS. |
| Wave evidence | `docs/reviews/<wave>/` | Dated per-wave records (history). |
| Workflows | `.claude/workflows/` | Claude-Code-only orchestration scripts (see `CLAUDE.md`). |
| Status | `docs/STATUS.md` | Single source of current truth. |

## Common task routes
| Task | Start here | Verify with |
|---|---|---|
| Refine or expand game content | [Repository content skill](../.agents/skills/romanian-game-content/SKILL.md), [ADR-0156](adr/0156-two-track-content-growth.md) | refinement, discovery pool and existing promotion gates |
| Start the next version | `docs/adr/0113-outcome-based-version-batches.md` + current STATUS backlog | explicit player outcomes, focused development checks, integrated gates and `cat-content-ops delta --baseline <commit> --text` |
| Word-game session fix | `go-backend/internal/session` + matching engine/HTTP test; Python oracle for comparison | native race/vet + targeted parity (`docs/agent-testing.md`) |
| Content loop (V3) / landing review | `docs/CONTENT_LOOP.md`, ADR-0220, `docs/CRITIQUE_RUBRIC.md` | C0 baseline, 4i gates, test-pin packet |
| New pack-only content wave | `docs/PACK_ONLY_CONTENT_WAVES.md`, `docs/CRITIQUE_RUBRIC.md`, newest review README | bound native review/validators/race/source/operator gates |
| Serving API change | `go-backend/internal/httpapi`, `docs/MOBILE_CONTRACT.md` | native race/vet/HTTP parity + manifest hash in `docs/STATUS.md` |
| Frontend | `frontend/src/`, `docs/agent-testing.md` | owning pinned frontend/unit/browser checks; native TS7/Oxlint + SDK AST; managed `dist` → Go embedfs (ADR-0184, ADR-0202/0204) |
| Deploy | `docs/DEPLOY.md`, `docker-compose.prod.yml`, `deploy/Caddyfile` | smokes recorded in `docs/STATUS.md` |
| Docs | `docs/STATUS.md`, `README.md` | pinned-shell `go -C go-backend run ./cmd/cat-doc-check --root .. --inventory docs/tracked-markdown.json` + whitespace; no game rebuild |

## Do not load by default
- Frozen `cat_de_roman_esti/web/static/`, legacy archives, generated embedfs assets and `frontend/node_modules/`.
- `docs/reviews/**/*.json` and the fixture JSONs in full (query large inventories with a script).
- `docs/compliance/` unless the task is legal.
- Caches, logs, and env files.

## Known pitfalls
- Session stores must stay bounded; do not reintroduce unbounded in-memory growth.
- Use deterministic tests for TTL/max-size behavior.
- The `romania_scraper` venv has no Django — use the interpreter named in `docs/agent-testing.md`.
- Go refuses `CAT_KG_FIXTURE`/pack/ranking overrides; approved content needs export + rebuild.
  Native terminal `--fixture` and the retained oracle can load `kg_real.json`; it lacks curated coverage.
- ADR-0184 supersedes ADR-0020 tooling/output instructions: sync managed `frontend/dist` before Go compilation; never regenerate frozen original30. GUI gates use the owning pinned wrapper, not host npm/Go; ADR-0199/0200 define cadence and no-device policy.
- `tests/test_alchimie_sparse_recipes.py:293` asserts a 45 s wall-clock budget and fails under host load.
