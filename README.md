# cat_de_roman_esti

V1.6 is independently accepted and published on `origin/main` at `dccd401`.
V1.7 has complete prospective evidence and reviewed isolated native Source7 candidates;
live installation and release gates remain pending. See [current status](docs/STATUS.md)
and the [V1.7 review](docs/reviews/v1-7-recognizable-content/README.md).

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
- Frontend: React 19.2.7 + Vite 8.3.3 + TypeScript 7.0.2; selected Node 26.10.0/npm 12.2.0 ([ADR-0184](docs/adr/0184-native-spa-toolchain-and-managed-output.md)). [Startup accounting](docs/adr/0185-accepted-eager-startup-bundle-accounting.md) is integrated with retained122743/122880 startup bytes and remains unqualified; see the current [owning handover](docs/GUI_MIGRATION_HANDOFF.md) and [`frontend/README.md`](frontend/README.md).
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

Use the actual trusted fleet task worktree, Docker and Python 3. Supply
`GATE_SHA` and `GATE_TREE_SHA256` from the owner's matching pinned-wrapper proof:

```bash
./run.sh
# open http://127.0.0.1:8000
```

The launcher invokes the existing owning `build` wrapper, then verifies its real
PASS receipt, source/tree, registered executable and compiled managed-asset identity.
It uses no host Node/npm/Go compiler, stale static probe or new tree-digest recipe.
`./run.sh build` performs the same fresh managed preparation without starting an app.
Current source implementation/static checks do not establish successful launcher,
HMR or full application qualification; see [STATUS](docs/STATUS.md).
The separate standalone qualifier alignment prepares the exact Node 26.10.0 guard per ADR-0184;
it is **UNAPPLIED, UNQUALIFIED and NOT RUN**, and separate from the owning GUI wrapper.
Its retained checks and pending qualification are described in [NATIVE_TOOLCHAIN](docs/NATIVE_TOOLCHAIN.md).
`PORT=9000 ./run.sh` changes the listener; a busy port fails explicitly.
Native source/build/operator and qualification commands are in
[`docs/NATIVE_TOOLCHAIN.md`](docs/NATIVE_TOOLCHAIN.md); Python remains an optional oracle.

### Frontend development

```bash
./run.sh dev
# open http://localhost:5173
```

Vite reloads frontend changes and proxies `/api` to Go on `127.0.0.1:8000`.
The prepared API and selected Vite run in the same pinned toolchain container,
with only loopback ports exposed and accounts/submissions off. Source/index changes
hot-reload; restart after backend, configuration or dependency changes. Development
edits do not create a new qualified source identity. `make run`, `make dev` and
`make build` wrap the same launcher and require the same actual qualified pair.

### Docker

```bash
./run.sh docker
# open http://127.0.0.1:8000
```

The canonical Dockerfile builds the SPA with Node and the backend with Go. Its
nonroot runtime contains the executable, compiled static files and an HTTP health
probe; it contains no Python server. Local and anonymous-production Compose use
this image, a read-only application filesystem and container port 8000, matching
Caddy. Change the local published port with `PORT=9000 docker compose up`.
The canonical recipe prepares selected Node/managed embedfs output per
[ADR-0184](docs/adr/0184-native-spa-toolchain-and-managed-output.md). The launcher
requires the actual owner-qualified pair bound to clean checkout HEAD, builds with
those explicit arguments and runs the immutable resulting image ID. An ordinary
clean checkout can use this Docker mode; managed run/build/dev require the fleet
worktree. Current image binding/qualification remains pending; no deployment follows.

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
The separate source alignment of `scripts/qualify_go_toolchain.sh` follows the exact selected Node 26.10.0 pin
([ADR-0184](docs/adr/0184-native-spa-toolchain-and-managed-output.md)); application, execution and complete qualification remain pending.
Explicit task scratch/PG and all independent native obligations remain; see [NATIVE_TOOLCHAIN](docs/NATIVE_TOOLCHAIN.md). Retained Python validators/Ruff/pytest are optional independent
references; commands and the owning GUI context are in
[`docs/agent-testing.md`](docs/agent-testing.md). GitHub Actions use manual dispatch;
retained Python/Rust reference jobs are opt-in ([ADR-0164](docs/adr/0164-manual-github-actions.md)).

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
