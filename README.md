# cat_de_roman_esti

A **text-only arcade of six Romanian word games** using a shared concept graph
(current counts, fixture version, generated hashes and gate state are recorded in
`docs/STATUS.md`; no graph visualization). Alchimie exploration also has its
own reviewed vocabulary and recipe catalog. All six are **server-authoritative**:
the Go server validates every move and hides the answers.

- **Alchimie** — explore a saved Romanian kitchen collection with consistent recipes
  and optional goals, search your earned recipes, or play short scored target challenges ([ADR-0151](docs/adr/0151-expand-game-vocabulary-and-search-earned-recipes.md)).
- **Intrusul** — tap the one word that does not belong with the other three.
- **Perechi** — match eight words into four hidden semantic pairs.
- **Conexiuni** *(à la NYT Connections)* — group 16 concepts into 4 hidden categories,
  4 mistakes allowed.
- **Cald sau Rece** *(à la Contexto/Semantle)* — a hidden secret concept; each guess tells
  you how close you are (hot ↔ cold); find it.
- **Lanțul Cuvintelor** *(à la The Wiki Game)* — type a concept linked to the current one
  and hop word-by-word to the target in as few moves as possible.

The terminal CLI `cat-de-roman` is the original semantic-hop game: from a START concept,
hop along semantic edges to a TARGET in as few hops as possible, in **easy** (distractors
filtered, edge labels + hints shown) or **hard** (decoys kept, labels + hints hidden) mode.
The name is a pun on *"cât de român ești"* — "how Romanian are you".

## Stack

- **Go 1.27.1** serves the six games, exploration, site/API routes, optional PostgreSQL
  accounts and private pending proposals ([ADR-0162](docs/adr/0162-select-go-production-backend.md),
  [ADR-0163](docs/adr/0163-complete-native-go-accounts.md)). Accounts/proposals remain off publicly.
- Native content export/validators/review builders, REST operators, the original terminal
  command and private qualification tools run in Go with pinned Unicode 15 tables
  ([native tooling](docs/NATIVE_TOOLCHAIN.md), [ADR-0166](docs/adr/0166-native-content-operators-and-builder-rails.md)).
- **Python/Rust** sources, tests and rollback profiles remain independent references.
  Legacy Python web dependencies are pinned by `constraints.txt`.
- Frontend: React 19.2 + Vite 8.1 + TypeScript, Node 24 — see [`frontend/README.md`](frontend/README.md).
- Native bounded RO-EDU REST client and provenance-preserving fixture/smoke operators;
  the original vendored Python client remains an independent reference.
- Native race/vet/source/HTTP/browser gates; retained `pytest`/`ruff` reference commands
  are listed separately in the testing guide.
- Data source: the `kg_nodes` / `kg_edges` / `kg_puzzles` products served by
  `ro_data_server` (producer: `romania_scraper`). Plays fully offline against a bundled
  fixture too.

## Quick start (CLI)

```bash
# Go 1.27.1 builds the original terminal game into workspace scratch.
./cat-de-roman --offline
./cat-de-roman --offline --list

# Explicit online play uses ROEDU_API_KEY when configured.
./cat-de-roman --api-url http://127.0.0.1:8077 --category istorie --difficulty hard
```

If the server probe (`/v1/health`) fails, the CLI automatically falls back to the
offline fixture.

## Run (web app)

The compiled SPA and Go server play fully offline against the reviewed embedded
content. The Go runtime serves all six games and Alchimie exploration, with optional native
accounts and pending proposals, without a Python server. The React/TypeScript frontend
remains JavaScript in the browser. Build and deployment details are in
[`docs/NATIVE_BACKENDS.md`](docs/NATIVE_BACKENDS.md); current qualification is in
[`docs/STATUS.md`](docs/STATUS.md).

### One command (local)

Install the qualified Go 1.27.1 compiler, then:

```bash
./run.sh
# open http://127.0.0.1:8000
```

The launcher builds Go with an incremental cache under `~/work/_temp/` and builds
React only when its compiled bundle is missing. Node 24 is needed for that frontend
build. `PORT=9000 ./run.sh` changes the listener; a busy port fails explicitly.
Native source/build/operator and qualification commands are in
[`docs/NATIVE_TOOLCHAIN.md`](docs/NATIVE_TOOLCHAIN.md); Python remains an optional oracle.

### Frontend development

```bash
./run.sh dev
# open http://localhost:5173
```

Vite reloads frontend changes and proxies `/api` to Go on `127.0.0.1:8000`.
Restart the command after backend changes. `make run`, `make dev` and `make build`
wrap the same Go launcher.

### Docker

```bash
./run.sh docker
# or:
docker compose up --build
# open http://127.0.0.1:8000
```

The canonical Dockerfile builds the SPA with Node and the backend with Go. Its
nonroot runtime contains the executable, compiled static files and an HTTP health
probe; it contains no Python server. Local and anonymous-production Compose use
this image, a read-only application filesystem and container port 8000, matching
Caddy. Change the local published port with `PORT=9000 docker compose up`.

The public runtime is anonymous; accounts and submissions remain off. Native account
staging uses the canonical Go image through `docker-compose.accounts.yml` or
`docker-compose.prod.yml`; activation still requires the [go-live gates](docs/DEPLOY.md).
`Dockerfile.python-reference` and `docker-compose.python-reference.yml` are explicitly
retained reference/rollback artifacts, outside the active serving path.

## Tests & lint

The CI gate set (`.github/workflows/ci.yml`), runnable locally:

```bash
go -C go-backend test -race ./... && go -C go-backend vet ./...
go -C shared-go/authcore test -race ./... && go -C shared-go/authcore vet ./...
go -C go-backend run ./cmd/cat-content validate --root ..
go -C go-backend run ./cmd/cat-content export --root .. --check
go -C go-backend run ./cmd/cat-content-ops rank --root .. --check
go -C go-backend run ./cmd/cat-content-ops derive --root .. --check
go -C go-backend run ./cmd/cat-content-rail all --root .. --check
go -C go-backend run ./cmd/cat-mobile-pack --root .. --check
go -C go-backend run ./cmd/cat-doc-check --root ..
( cd frontend && npm test && npm run lint && npm run build )
```

Game/content tests use bundled fixtures and local fake providers, with no live upstream.
Native account and combined HTTP release gates also require an explicit disposable
PostgreSQL fixture; ordinary Go runs skip those contracts when no DSN is supplied.
The complete native-only gate is `scripts/qualify_go_toolchain.sh`, with explicit task
scratch/PG and Python/Rust absent from PATH. Retained Python validators/Ruff/pytest are
optional independent references, with complete commands in
[`docs/agent-testing.md`](docs/agent-testing.md). The active Python reference CI job remains
automatic until the exact manual-routing proposal receives human approval (ADR-0168).

## Contributing

Direct **local** merges to `main` are allowed once the CI gate is green; **pushing to
`origin` stays explicit-request-only**. See [`CONTRIBUTING.md`](CONTRIBUTING.md) and
[`docs/adr/0004-branch-merge-policy.md`](docs/adr/0004-branch-merge-policy.md).

## Docs

- [`docs/GO_BACKEND.md`](docs/GO_BACKEND.md) — Go serving runtime, retained Rust research and verification history.
- [`docs/STATUS.md`](docs/STATUS.md) — current truth: state, pins, verification record, next actions.
- [`docs/TESTARE_V1.md`](docs/TESTARE_V1.md) — Romanian V1 tester guide: six-game session, feedback form,
  same-Wi-Fi phone setup for the organizer.
- [`romanian-game-content`](.agents/skills/romanian-game-content/SKILL.md) — repository skill for
  refinement and experimental concept discovery; workflow: [ADR-0156](docs/adr/0156-two-track-content-growth.md).
- [`docs/BETA_CANDIDATE.md`](docs/BETA_CANDIDATE.md) — anonymous-beta evidence, bounded quality waves, outstanding gates and Romanian-player playtest protocol.
- [`AGENTS.md`](AGENTS.md) — operating contract for agent sessions (Claude Code and Codex).
- [`docs/agent-map.md`](docs/agent-map.md) — entry points, task routes, do-not-load list.
- [`docs/agent-testing.md`](docs/agent-testing.md) — gate commands with expected output.
- [`docs/NATIVE_TOOLCHAIN.md`](docs/NATIVE_TOOLCHAIN.md) — native source, terminal, REST and independent qualification commands.
- [`docs/adr/0098-protect-real-browser-game-journeys.md`](docs/adr/0098-protect-real-browser-game-journeys.md) — real browser regression gate across all six games.
- [`docs/KG_CONTRACT.md`](docs/KG_CONTRACT.md) — the authoritative KG contract v1 (ADR-0002).
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — the **terminal hop game** architecture; the web product is the word-game arcade (ADR-0001).
- [`docs/MOBILE_CONTRACT.md`](docs/MOBILE_CONTRACT.md) — stable operationIds + `GET /api/manifest` for the generated mobile client (ADR-0003).
- [`docs/CRITIQUE_RUBRIC.md`](docs/CRITIQUE_RUBRIC.md) — content critique rubric every pack item passes before `approved` (ADR-0067; ADR-0023 superseded).
- [`docs/PACK_ONLY_CONTENT_WAVES.md`](docs/PACK_ONLY_CONTENT_WAVES.md) — bounded authored-instance wave checklist (ADR-0102).
- [`docs/DEPLOY.md`](docs/DEPLOY.md) — anonymous vs accounts stack, Hetzner/Cloudflare/Caddy, go-live compliance checklist.
- [`docs/compliance/README.md`](docs/compliance/README.md) — DRAFT legal pack RO/EN (not agent-facing).
- [`docs/PILOT_BOARD_RANKING.md`](docs/PILOT_BOARD_RANKING.md) — private V37 pre-playtest
  board estimate: reproduction and interpretation (ADR-0051).
- [`docs/V38_DERIVED_GAMES.md`](docs/V38_DERIVED_GAMES.md) — private V38 derived-game
  catalog, ranking, and regeneration contract (ADR-0052).
- [`docs/V39_REFINEMENT.md`](docs/V39_REFINEMENT.md) — V39 replay, starter, exposure,
  local-circuit, and verified-record contracts (ADR-0054/0061; ADR-0053 superseded).
- [`docs/V40_REFINEMENT.md`](docs/V40_REFINEMENT.md) — V40 critique-clean selection,
  sticky parental holds, and actionable daily-circuit rows (ADR-0055–0057).
- [`docs/V41_REFINEMENT.md`](docs/V41_REFINEMENT.md) — V41 playable category choices,
  recoverable ranking states, and the private-history boundary (ADR-0058, ADR-0059,
  ADR-0061).
- [`docs/V42_REFINEMENT.md`](docs/V42_REFINEMENT.md) — V42 bounded recovery, truthful
  category dailies, and the local streak/diploma loop (ADR-0062–0064).
- [`docs/ROEDU_INTEGRATION.md`](docs/ROEDU_INTEGRATION.md) — products, key, field mapping, fail-closed gate, offline fixture.
- [`frontend/README.md`](frontend/README.md) — SPA develop/build/layout.
- History (never edited): [`docs/adr/`](docs/adr/) decision records (0001 = arcade pivot, no
  graph UI; newest in [`docs/adr/README.md`](docs/adr/README.md)) · [`docs/reviews/`](docs/reviews/) per-wave evidence ·
  [`docs/handoffs/`](docs/handoffs/) dated records · [`docs/archive/`](docs/archive/)
  superseded snapshots.
