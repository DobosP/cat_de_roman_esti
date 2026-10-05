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

The native `apppack` decoder and terminal `--fixture` autodetection support the shared
RO-EDU app-pack envelope through bounded synthetic/offline input. Real endpoint integration
remains outside this migration. The expected public packs are:

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

## API configuration

The native online client reads `ROEDU_API_KEY`; `ROEDU_API_URL` or explicit `--api-url`
selects the approved producer. Values are not written into source, reports or errors.
The three-product public scope is configured by the producer; unknown permissions refuse.

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
(as stored in SQLite/served) or an already-parsed list — see native `roeduclient.IDList` (retained `engine._as_id_list` reference).
`is_distractor` / `bidirectional` are tolerated as int, "1"/"0", or bool — see native
`hopcli` record parsing (retained `graph._as_bool` reference).

## Fail-closed gate

Native REST loads refuse unavailable/torn pages, repeated cursors/IDs, changed snapshots,
redirects, malformed/ambiguous Unicode JSON and byte/page/record cap overruns. Legal
redistribution and non-personal metadata is required, and provenance/page identities
survive private fixture export. Limits: 200 records/page, 500 pages/product, 4 MiB/page,
10,000 nodes, 50,000 edges and 5,000 puzzles; request/operation deadlines are explicit.
No partial corpus is committed on refusal. Native tagged app-pack input caps 16 MiB/512
packs and the same product counts; mismatched/private/unknown legal rows are withheld.
The independent original client/loader/tests remain available as optional references.

## Offline fixture

For development and tests without a live server, `cat_de_roman_esti/fixtures/kg_sample.json`
is a hand-authored KG snapshot conforming to the contract field shapes. `--offline`
plays against it; the CLI also auto-falls-back to it if the server probe (`/v1/health`)
fails. Native REST tests use local synthetic HTTP peers; native app-pack/terminal tests preserve
exact fixture tags/facets, public filtering and playable paths. Retained Python fake-client
tests independently describe the same original integration.

`tests/fixtures/kg_app_pack_sample.json` is a synthetic redistributable app-pack
fixture. It contains no internal source URLs, checksums, internal paths, `llms.txt`
entries, or TDM-only item bodies.

## Explicit transport/fixture qualification

Use a synthetic or separately authorized RO-EDU endpoint; no live import was used here.

```bash
./cat-de-roman --api-url http://127.0.0.1:8077 --category istorie --difficulty hard
./cat-de-roman --offline --fixture tests/fixtures/kg_app_pack_sample.json --list
go -C go-backend run ./cmd/cat-roedu smoke --url http://127.0.0.1:8077 --difficulty easy
go -C go-backend run ./cmd/cat-roedu export --url http://127.0.0.1:8077 --out <scratch>/kg.json
```

The terminal retains health-only offline fallback. Smoke/export never turn missing
required infrastructure, license refusal or a partial corpus into success/skip. The
original `scripts/e2e_smoke.py` and `gen_real_fixture.py` remain optional historical
references; active bounded operators and receipts are in [NATIVE_TOOLCHAIN](NATIVE_TOOLCHAIN.md).
