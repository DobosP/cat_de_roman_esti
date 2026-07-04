# cat_de_roman_esti

A terminal "semantic network hop" game over the Romanian knowledge graph. You get a
START concept and a TARGET concept; hop along semantic edges to reach the target in as
few hops as possible. Two modes: **easy** (distractors filtered, edge labels + hints
shown) and **hard** (decoys kept, labels + hints hidden).

The name is a pun on *"cât de român ești"* — "how Romanian are you".

## Web app — the word-game arcade

The web app is a **text-only arcade** of four word games over the same Romanian concept
graph (**325 concepts / 734 links / 108 puzzles**, `fixture-v4-dense` — no graph
visualization). All four are **server-authoritative** (the BFF validates moves and hides
answers):

- **Alchimie** *(à la Infinite Craft)* — combine two concepts into a new one (their shared
  link) and keep crafting until you reach the target.
- **Cald sau Rece** *(à la Contexto/Semantle)* — a hidden secret concept; each guess tells
  you how close you are (hot ↔ cold); find it.
- **Lanțul Cuvintelor** *(à la The Wiki Game)* — type a concept linked to the current one
  and hop word-by-word to the target in as few moves as possible.
- **Conexiuni** *(à la NYT Connections)* — group 16 concepts into 4 hidden categories,
  4 mistakes allowed.

The terminal CLI below is the original semantic-hop game.

## Stack

- **Python >= 3.11**, standard library only at runtime (no hard deps).
- Vendored stdlib HTTP client (`roedu_client.py`, urllib) for the RO-EDU data platform.
- Dev tooling: `pytest` + `ruff` (line-length 100, select E,F,I,UP,B).
- Data source: the `kg_nodes` / `kg_edges` / `kg_puzzles` products served by
  `ro_data_server` (producer: `romania_scraper`). Plays fully offline against a bundled
  fixture too.

## Quick start

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

The animated SPA + FastAPI BFF play **fully offline** against the bundled fixture — no
server, no API key. Pick whichever of the three paths suits you.

### One command (local)

```bash
./run.sh            # builds the SPA if missing, then serves the BFF
# open the printed URL, e.g. http://127.0.0.1:8000
```

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

Multi-stage build: stage 1 (`node:18-slim`) builds the SPA; stage 2 (`python:3.11-slim`)
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

## Demo

```
$ cat-de-roman --offline --category literatura --difficulty easy

Start: Mihai Eminescu  ->  Target: Romantism
Type a number to hop, 'q' to quit.

================================================================
  HOPS: 0   PAR: 2   MODE: easy
  TARGET : Romantism  (literatura)
           Curent literar din secolul al XIX-lea.
  CURRENT: Mihai Eminescu  (person)
           Poet roman, autor al poemului Luceafarul.
----------------------------------------------------------------
  Neighbours you can hop to:
  [1] Luceafarul — a scris   <hint>
  [2] Ion Creanga — prieten cu
  [3] Junimea — membru al

hop > 1
  → hopped to Luceafarul
  ...
  [1] Romantism — apartine curentului   <hint>
hop > 1
  → hopped to Romantism

################################################################
  WIN! 2 hops (par 2).  SCORE: 1000
################################################################
```

## Tests & lint

```bash
python -m pytest -q
ruff check
```

Tests run entirely against a fake in-process client / the bundled fixture — **no live
server required**.

## Contributing

Direct **local** merges to `main` are allowed once the CI gate is green; **pushing to
`origin` stays explicit-request-only**. See [`CONTRIBUTING.md`](CONTRIBUTING.md) and
[`docs/adr/0004-branch-merge-policy.md`](docs/adr/0004-branch-merge-policy.md).

## Docs

- [`docs/KG_CONTRACT.md`](docs/KG_CONTRACT.md) — the authoritative KG contract v1 (ADR-0002).
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — the **terminal hop game** architecture; the web product is the word-game arcade (ADR-0001).
- [`docs/MOBILE_CONTRACT.md`](docs/MOBILE_CONTRACT.md) — stable operationIds + `GET /api/manifest` for the generated mobile client (ADR-0003).
- [`docs/ROEDU_INTEGRATION.md`](docs/ROEDU_INTEGRATION.md) — products, key, field mapping, fail-closed gate, offline fixture.
- [`docs/STATUS.md`](docs/STATUS.md) — phase / built / wired / blockers / next.
- [`docs/adr/`](docs/adr/) — architecture decision records (0001 = arcade pivot, no graph UI).
