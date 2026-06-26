# RO-EDU integration — cat_de_roman_esti

This repo is a **consumer** on the RO-EDU data platform. The platform
(`romania_scraper.dataapi`, served over HTTP by `ro_data_server`) is the producer of
the Romanian knowledge graph; we read three products and play a game on top of them.

## Products consumed

| Product | kind | What we use it for | Filters we pass |
|---------|------|--------------------|-----------------|
| `kg_nodes` | graph | graph vertices (concepts/people/places/...) | `category` |
| `kg_edges` | graph | graph edges (semantic relations + distractor flag) | (none — pulled whole; cross-category edges are harmless) |
| `kg_puzzles` | graph | START/TARGET + par + solution_path + hints | `category`, `difficulty` |

We use only the **read** transport: `GET /v1/health`, `GET /v1/products`,
`GET /v1/products/{name}` with `cursor` + `limit` pagination.

## Tagged app-pack contract

The repo also has fixture-backed support for the shared RO-EDU app-pack envelope while
the real `ro_data_server` endpoint is being integrated. The expected public packs are:

- `pack_id`: `roedu:cat_de_roman_esti:kg_nodes:v1`,
  `roedu:cat_de_roman_esti:kg_edges:v1`, `roedu:cat_de_roman_esti:kg_puzzles:v1`
- `app`: `cat_de_roman_esti`
- `layer`: `redistributable`
- `schema_version`: `1`
- top-level fields used: `items`, `pagination.next_cursor`, `withheld`, `errors`
- item fields used by the game contract: `id`, `kind`, `title`, `tags`, `facets`,
  `source`, `provenance`, `license`, `access_type`, `legal_basis`, `gdpr_relevant`,
  `redistributable`, `confidence`, plus the KG-specific node/edge/puzzle fields below

`kind` maps to products as `kg_node` -> `kg_nodes`, `kg_edge` -> `kg_edges`,
`kg_puzzle` -> `kg_puzzles`. `tags` and `facets` are retained on `Node`, `Edge`, and
`Puzzle` so puzzle selectors can use topic/category/difficulty/source facets without
re-reading producer internals.

Public ingestion is fail-closed. The consumer accepts only `layer=redistributable`,
`redistributable=true`, `access_type` in `public_document|open_license|public_domain`,
non-empty `legal_basis`, and `gdpr_relevant=false`. Missing or unknown metadata,
`tdm_exception`, non-redistributable records, and `internal` packs are withheld from the
game bundle. Public records also drop internal-only provenance keys such as `source_url`,
`sha256`, internal paths, and `llms.txt` references.

## API key

```
ROEDU_API_KEY = cat-de-roman-dev
```

On the platform this resolves to:

```
Scope(app="cat-de-roman-esti", products={"kg_nodes","kg_edges","kg_puzzles"}, internal=False)
```

Scope isolation: `social-app-dev` and `ro-teacher-dev` keys do **not** get KG access;
`admin-dev` wildcard covers everything. This key is dev-only — production keys are
issued separately.

## Field mapping (served record → our model)

`kg_nodes` → `graph.Node`:

| served field | model field | notes |
|---|---|---|
| `id` | `Node.id` | content-addressed id (blake2b hex in prod; readable slug in the fixture) |
| `node_type` | `Node.node_type` | concept/person/place/work/event/org/competency |
| `label_ro` | `Node.label_ro` | display label, diacritics preserved |
| `category` | `Node.category` | one game category |
| `description` | `Node.description` | gloss, may be `""` |
| `salience` | `Node.salience` | 0..1 obscurity lever |
| `difficulty_tier` | `Node.difficulty_tier` | easy/medium/hard band |
| `degree` | `Node.degree` | centrality proxy |
| `tags`,`facets`,`source`,`redistributable` | same | retained for app-pack puzzle selection |

`kg_edges` → `graph.Edge`:

| served field | model field | notes |
|---|---|---|
| `id`,`src_id`,`dst_id` | same | |
| `relation` | `Edge.relation` | is_a/part_of/created_by/located_in/... |
| `label_ro` | `Edge.label_ro` | edge label (lever 3, easy only) |
| `strength` | `Edge.strength` | 0..1 |
| `is_distractor` | `Edge.is_distractor` | coerced 1/0/"true" → bool (lever 4) |
| `bidirectional` | `Edge.bidirectional` | coerced; default True |
| `tags`,`facets`,`source`,`redistributable` | same | retained for app-pack puzzle selection |

`kg_puzzles` → `engine.Puzzle`:

| served field | model field | notes |
|---|---|---|
| `id`,`start_id`,`target_id`,`category`,`difficulty` | same | |
| `optimal_hops`,`par` | same | lever 1 |
| `solution_path` | `Puzzle.solution_path` | json-array string OR list → list[str] |
| `hint_neighbors` | `Puzzle.hint_neighbors` | json-array string OR list → list[str] |
| `tags`,`facets`,`source`,`redistributable` | same | retained for app-pack puzzle selection |

`solution_path` / `hint_neighbors` are tolerated as either a JSON-array **string**
(as stored in SQLite/served) or an already-parsed list — see `engine._as_id_list`.
`is_distractor` / `bidirectional` are tolerated as int, "1"/"0", or bool — see
`graph._as_bool`.

## Fail-closed gate

The server is fail-closed and enforces the license gate (`GatePolicy.permits`). The
vendored client trusts the server but is itself fail-closed: `RoeduClient.iter` returns
immediately on any page with `available=false`, so a gate refusal or an unbuilt store
yields **zero** records. `data.load_from_client` therefore degrades to a smaller (never
fabricated) bundle, and `HopGame.load` refuses puzzles whose nodes aren't present.
Client pulls are bounded by default (`10_000` nodes, `50_000` edges, `5_000` puzzles);
callers may override those caps for tests or controlled deployments.

## Offline fixture

For development and tests without a live server, `cat_de_roman_esti/fixtures/kg_sample.json`
is a hand-authored KG snapshot conforming to the contract field shapes. `--offline`
plays against it; the CLI also auto-falls-back to it if the server probe (`/v1/health`)
fails. The test suite drives a **fake in-process client** (`tests/conftest.py::FakeRoeduClient`)
that re-implements the page/cursor/availability contract over the same sample — so the
loader, pagination, and fail-closed path are all exercised with no network.

`tests/fixtures/kg_app_pack_sample.json` is a synthetic redistributable app-pack
fixture. It contains no internal source URLs, checksums, internal paths, `llms.txt`
entries, or TDM-only item bodies.

## Running against a live server

```
cp .env.example .env            # ROEDU_API_URL + ROEDU_API_KEY=cat-de-roman-dev
# start the platform (in the ro_data_server repo):
#   ROEDU_DATA_DIR=/path/to/data python -m ro_data_server --port 8077
cat-de-roman --category istorie --difficulty hard
```
