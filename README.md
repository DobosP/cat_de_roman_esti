# cat_de_roman_esti

A **text-only arcade of six Romanian word games** over one concept graph
(**2,406 concepts / 9,410 links / 8,603 typed aliases / 180 puzzles**,
`fixture-v87-snack-and-action-quality` — generated hashes and gate state are
recorded in `docs/STATUS.md`; no graph visualization). All six are **server-authoritative**:
the Django BFF validates every move and hides the answers.

- **Alchimie** *(à la Infinite Craft)* — combine two concepts into a new one (their shared
  link) and keep crafting until you reach the target.
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

- **Python >= 3.11**; the CLI is stdlib-only; the web app needs the `web` extra (Django 5.2 +
  DRF + uvicorn, pinned by `constraints.txt`).
- Frontend: React 19.2 + Vite 8.1 + TypeScript, Node 24 — see [`frontend/README.md`](frontend/README.md).
- Vendored stdlib HTTP client (`roedu_client.py`, urllib) for the RO-EDU data platform.
- Dev tooling: `pytest` + `ruff` (line-length 100, select E,F,I,UP,B).
- Data source: the `kg_nodes` / `kg_edges` / `kg_puzzles` products served by
  `ro_data_server` (producer: `romania_scraper`). Plays fully offline against a bundled
  fixture too.

## Quick start (CLI)

```bash
# install (editable, with dev tools)
python -m pip install -e ".[dev]"

# play offline against the bundled fixture — no server needed
cat-de-roman --offline

# list what's available
cat-de-roman --offline --list

# play online against a live RO-EDU server
cp .env.example .env          # ROEDU_API_URL + ROEDU_API_KEY=cat-de-roman-dev
cat-de-roman --category istorie --difficulty hard
```

If the server probe (`/v1/health`) fails, the CLI automatically falls back to the
offline fixture.

## Run (web app)

The animated SPA + Django BFF play **fully offline** against the bundled fixture — no
server, no API key. Pick whichever of the three paths suits you.

### One command (local)

```bash
pip install -c constraints.txt -e ".[dev,web]"   # backend + web extra, pinned
./run.sh            # builds the SPA if missing, then serves the BFF
# open the printed URL, e.g. http://127.0.0.1:8000
```

On the fleet laptop: `CDR_PYTHON=~/work/cat_de_roman_esti/.venv/bin/python ./run.sh` —
run.sh's default interpreter (run.sh:26) has no Django.

`./run.sh` (or `make run`) builds the React SPA into `cat_de_roman_esti/web/static`
only if the build is missing, then boots the BFF on port **8000** (auto-falling back to
the next free port if 8000 is taken) and prints the URL. Override the port with
`PORT=9000 ./run.sh`.

### Dev (hot-reload)

```bash
./run.sh dev        # or: make dev
# open http://localhost:5173  (Vite proxies /api -> the uvicorn BFF)
```

Runs the Vite dev server (hot SPA) **and** `uvicorn --reload` (hot API) together. Open
the **Vite** URL (`:5173`) for the live UI; it proxies `/api` to the BFF on `:8000`.

### Docker (build + run)

```bash
./run.sh docker                       # build the image + run it, or:
docker compose up --build             # same, via compose
# open http://localhost:8000
```

Multi-stage build: stage 1 (`node:24-slim`) builds the SPA; stage 2 (`python:3.12-slim`)
`pip install`s the package with its `web` extra and runs `uvicorn` as a non-root user on
port **8000**. `docker compose down` stops it. Override the host port with
`PORT=9000 docker compose up`.

### Live server (optional env)

By default the web app is offline. To point it at a live `ro_data_server`, set these
**before** running any of the paths above (the BFF reads them server-side; the API key
never reaches the browser, and an unreachable/unhealthy server **fails soft** back to
the offline fixture):

| Env var          | Default            | Meaning                                        |
| ---------------- | ------------------ | ---------------------------------------------- |
| `ROEDU_API_URL`  | _(unset = offline)_| Base URL of the live `ro_data_server`.         |
| `ROEDU_API_KEY`  | `cat-de-roman-dev` | API key for the live server.                   |
| `PORT`           | `8000`             | Port the BFF binds (host port for Docker).     |
| `HOST`           | `127.0.0.1`        | Bind host for the local launcher.              |

```bash
ROEDU_API_URL=http://localhost:8077 ROEDU_API_KEY=cat-de-roman-dev ./run.sh
# or with compose: ROEDU_API_URL=... docker compose up --build
```

## Tests & lint

The CI gate set (`.github/workflows/ci.yml`), runnable locally:

```bash
python scripts/validate_fixture.py                       # KG fixture content gate
python scripts/validate_games_pack.py                    # curated pack content gate
ruff check                                               # lint
pytest -q                                                # backend (accounts off)
CAT_ACCOUNTS_ENABLED=1 CAT_DEBUG=1 pytest -q tests/accounts
( cd frontend && npm test && npm run lint && npm run build )
```

Tests run entirely against a fake in-process client / the bundled fixture — **no live
server required**. Interpreter and expected outputs: [`docs/agent-testing.md`](docs/agent-testing.md).

## Contributing

Direct **local** merges to `main` are allowed once the CI gate is green; **pushing to
`origin` stays explicit-request-only**. See [`CONTRIBUTING.md`](CONTRIBUTING.md) and
[`docs/adr/0004-branch-merge-policy.md`](docs/adr/0004-branch-merge-policy.md).

## Docs

- [`docs/STATUS.md`](docs/STATUS.md) — current truth: state, pins, verification record, next actions.
- [`docs/BETA_CANDIDATE.md`](docs/BETA_CANDIDATE.md) — anonymous-beta evidence, bounded quality waves, outstanding gates and Romanian-player playtest protocol.
- [`AGENTS.md`](AGENTS.md) — operating contract for agent sessions (Claude Code and Codex).
- [`docs/agent-map.md`](docs/agent-map.md) — entry points, task routes, do-not-load list.
- [`docs/agent-testing.md`](docs/agent-testing.md) — gate commands with expected output.
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
  graph UI; newest 0126) · [`docs/reviews/`](docs/reviews/) per-wave evidence ·
  [`docs/handoffs/`](docs/handoffs/) dated records · [`docs/archive/`](docs/archive/)
  superseded snapshots.
