# Mobile API contract — cat_de_roman_esti BFF

This is the contract a **generated mobile client** (Track A: Expo / React Native + TS)
depends on. It is additive over the existing `/api/wordgames/*` routes — no route paths,
methods, or gameplay semantics changed. Guarded by `tests/test_mobile_contract.py` and the
manifest tests in `tests/test_app_pack_contract.py`.

## 1. Stable OpenAPI operationIds

The app pins operationIds via `@extend_schema(operation_id=...)` on every DRF view
(drf-spectacular; see `cat_de_roman_esti/wordgames/*.py`) to `<tag>_<endpoint-name>`, e.g. `contexto_guess`, `alchimie_combine`, `lant_move`,
`conexiuni_guess`, `conexiuni_clue`, `meta_manifest`. A generated TS client turns these into method names
(`contextoGuess`, …). Unlike a framework default, they do **not** bake in the HTTP path, so a
route refactor never churns the client surface. The full expected set is asserted in
`test_openapi_operation_ids_are_stable`.

Additive since 2026-07-07 (ADR-0011): `meta_categories` (`GET /api/categories` — category
taxonomy + per-game availability) and `submissions_create` (`POST /api/submissions` —
user-submitted games; 503 unless the deployment enables `CAT_SUBMISSIONS_DIR`). Game create
endpoints accept an optional `?category=` query param; when (and only when) it is sent, game
state gains an optional `board_category` string. All pre-existing routes, fields, and
hidden-answer invariants are unchanged.

Export the schema for client generation (deterministic, offline — no server/live data):

```bash
python scripts/export_openapi.py openapi.json   # or print to stdout with no arg
# then e.g.  npx openapi-typescript openapi.json -o src/api/schema.ts
```

## 2. Trust manifest — `GET /api/manifest`

Lets a mobile app verify its **bundled offline KG copy** is in sync with the server and pick
the right generated types. Deterministic, side-effect-free (`data.fixture_manifest`):

```json
{
  "app": "cat_de_roman_esti",
  "schema_version": 1,          // KG record schema (APP_PACK_SCHEMA_VERSION)
  "manifest_version": 1,        // shape of THIS manifest
  "build_version": "fixture-v4-dense",
  "generated_at": "2026-06-21T00:00:00Z",
  "content_hash": "sha256:…",   // canonical hash over kg_nodes+kg_edges+kg_puzzles
  "counts": { "nodes": 330, "edges": 750, "puzzles": 108 }
}
```

`content_hash` is computed over records sorted by `id` with sorted keys, so it depends only on
**content** — not file formatting or record/key order. Any fixture regeneration that changes a
record changes the hash; a mobile client compares it against its cached bundle to detect drift.

## 3. Hidden-answer invariant (server-authoritative gameplay)

No game's public responses leak its secret answer before the win/lose state. This already held
in the code; the tests are regression guards that also assert the *reveal* boundary:

| Game | Secret | Pre-win exposure | Revealed when |
|------|--------|------------------|---------------|
| contexto | target id/label/solution | no `target` or `solution` key; target id/label absent everywhere; guesses carry rank feedback | won / gave up |
| alchimie | target id | `target.id = null`, `revealed = false` (label shown as the goal by design) | crafted (won) |
| lant | solution path | only `start` + `target` ids exposed; no intermediate path node; hint is on-demand | per-hop, by playing / `…/hint` |
| conexiuni | category grouping | no `solution`; tiles carry only `{id,label}` for the remaining public board; solved groups are counts only; optional clue returns one redacted category-label pattern only, with no category key/label or tile membership | won / lost |

Seeds/daily are deterministic by design (shared daily challenge); offline play inherently ships
the whole KG, so this guards the **API surface**, keeping gameplay server-authoritative rather
than claiming the offline answer is unknowable.

## 4. Contexto rank view-model

Contexto guess responses expose a bounded rank view of the player's own guesses without
shipping the hidden answer. Each accepted guess has:

```json
{
  "id": "n_banat",
  "label": "Banat",
  "distance": 1,
  "rank": 2,
  "temperature": "Fierbinte",
  "closeness": 99
}
```

`rank` is one-based (`1` is the secret target), ties share the same rank for a distance
bucket, and unreachable guesses rank after the reachable set. Pre-reveal responses keep
the target id, target label, and any `solution` payload absent across create/get/guess/clue.
The exact target object appears only on win or give-up.

## 5. Conexiuni clue endpoint

`POST /api/wordgames/conexiuni/games/{game_id}/clue` is additive. It unlocks after two
mistakes, can be used once, applies a score penalty, and returns:

```json
{
  "ok": true,
  "clue": { "pattern": "L_________", "message": "Un grup ramas are eticheta: L_________." },
  "clues_used": 1,
  "clue_available": false,
  "clues": [{ "pattern": "L_________", "message": "Un grup ramas are eticheta: L_________." }]
}
```

The clue payload is intentionally redacted: no category `key`, exact category label, tile ids,
or solution membership appears before win/loss.

Pre-terminal Conexiuni create/get/guess/clue responses use the same public view model:
`tiles` contains only public tile `{id,label}` objects still playable on the board,
`solved` stays `[]`, and progress is exposed through `solved_count` and
`remaining_groups`. Correct guesses may return `correct: true`, but category `key`,
category `label`, solved group tiles, and `solution` are reveal-gated until `won` or
`lost`.

## 6. Public app-pack fixture for roedu-mobile

`scripts/export_mobile_app_pack.py` exports a deterministic, public-only app-pack snapshot
from the bundled KG (ADR-0008). The checked-in cat fixture is:

```text
tests/fixtures/cat_mobile_app_pack_contract.json
```

It is copied into roedu-mobile as:

```text
apps/cat-mobile/src/fixtures/cat-contract-fixture.json
```

The fixture intentionally uses the cat-exported field names mobile must consume:

| Section | Public fields |
|---------|---------------|
| `manifest` | `app`, `schema_version`, `manifest_version`, `build_version`, `generated_at`, `content_hash`, `counts` |
| `kg_nodes` | `id`, `label_ro` |
| `kg_edges` | `id`, `src_id`, `dst_id` |
| `kg_puzzles` | `id`, `start_id`, `target_id`, `difficulty` |

Hidden gameplay helper fields such as `solution_path` and `hint_neighbors` are excluded.
The fixture's `content_hash` is computed over the normalized public mobile projection
(`label`, undirected edge pairs, `start`/`target`) so roedu-mobile can verify its importer
without importing Python code or contacting a live server.
