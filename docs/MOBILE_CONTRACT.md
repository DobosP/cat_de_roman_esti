# Mobile API contract — cat_de_roman_esti BFF

This is the contract a **generated mobile client** (Track A: Expo / React Native + TS)
depends on. It is additive over the existing `/api/wordgames/*` routes — no route paths,
or methods changed. Conexiuni's earned-group semantics are defined by
[ADR-0014](adr/0014-conexiuni-earned-group-reveal.md). Guarded by
`tests/test_mobile_contract.py` and the manifest tests in `tests/test_app_pack_contract.py`.

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
endpoints accept an optional `?category=` query param. Contexto, Lanț, and Conexiuni echo
`board_category` only for an explicit theme request. Alchimie is always themed: omitting the
query lets the server deterministically select and echo a bounded theme instead of using the
full graph.

Additive in V41 ([ADR-0058](adr/0058-difficulty-aware-playable-category-availability.md)):
each category also carries
`available_by_difficulty.<game>.<usor|normal|greu>`. `available.<game>` summarizes whether
any difficulty is playable, while `curated.<game>` remains a raw approved-inventory count
and is not a runtime-playability promise. Clients that offer a difficulty and category
together should use the nested field for that exact pair.

V42 ([ADR-0063](adr/0063-four-board-category-daily-floor.md)) gives an explicit
category daily a curated floor of four records for the exact game/category/difficulty
shelf; the unscoped floor stays eight. Below four, Alchimie, Contexto, and Lanț use their
existing deterministic miner inside the requested theme, while Conexiuni returns its
themed-unavailable 503. A successful response must never borrow an unscoped board and
relabel it as `board_category`.

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
  "build_version": "fixture-v52-household-morphology",
  "generated_at": "2026-06-21T00:00:00Z",
  "content_hash": "sha256:…",   // canonical hash over kg_nodes+kg_edges+kg_puzzles
  "counts": { "nodes": 2364, "edges": 9217, "puzzles": 180 }
}
```

`content_hash` is computed over records sorted by `id` with sorted keys, so it depends only on
**content** — not file formatting or record/key order. Any fixture regeneration that changes a
record changes the hash; a mobile client compares it against its cached bundle to detect drift.

## 3. Hidden-answer invariant (server-authoritative gameplay)

No game's public responses leak an unearned secret answer. Tests guard both the hidden and
positive reveal boundaries:

| Game | Secret | Pre-win exposure | Revealed when |
|------|--------|------------------|---------------|
| contexto | target id/label/solution | no `target` or `solution` key; target id/label absent everywhere; guesses carry rank feedback | won / gave up |
| alchimie | target id | `target.id = null`, `revealed = false` (label shown as the goal by design) | crafted (won) |
| lant | full route corridor | only `start` + `target` ids; up to six local choices carry label + relation but no id/on-track flag; hints prefer an unvisited target-reachable route, with an ID-free `backtrack` stage only when free undo is the safe recovery | per-hop by playing; at most one hop id from the third help request in the session, unless safe recovery is ID-free backtrack |
| conexiuni | unsolved category grouping | no `solution`; remaining tiles carry only `{id,label}`; each correctly solved group exposes its own key/label/tiles; up to two optional clues stay redacted | that group: correct guess; full solution: won / lost |

Seeds/daily are deterministic by design (shared daily challenge); offline play inherently ships
the whole KG, so this guards the **API surface**, keeping gameplay server-authoritative rather
than claiming the offline answer is unknowable.

### Alchimie additive projection views

Alchimie inventory entries add the boolean view metadata `recent`, `useful`, `ready`, and
`depleted`; `inventory_summary` carries only active/depleted/total counts. `recipe_summary`
contains only bounded pair/route/result counts — recipe ids and full routes are never public.
`attempted_count` is the only public experiment-history aggregate. A combine response adds
`already_tried` for its submitted unordered pair; a repeat changes no move, score, dry-spell,
hint, or inventory state, and no response serializes attempted ingredient IDs or results.
The first progressive hint has `hint_kind = output|category`, `hint = null`, and may include
only a non-target output **label** in `hint_output`; later hints may return one owned pair with
`hint_kind = pair`. Until win, none of these additive fields may contain the hidden target id.
V42 unlocks that hint after two consecutive distinct barren combines. From the fourth total
barren combine, `message` may append one deterministic generic strategy sentence; this is
not a new field or score penalty, and repeated pairs advance neither dry counter.

### Lanț progress and help

Successful `usor` and `normal` moves may add `progress: {kind, message}`, where `kind` is
`closer`, `lateral`, `farther`, `dead_end`, or `won`. `greu` omits automatic progress. No
response adds an exact remaining distance, corridor flag, or route marker.
`backtrack_recommended` remains an easy-only boolean.

Voluntary help has three session-wide stages: direction, alternatives, then one hop. The
counter is capped at three and survives moves and undo; only a new game resets it. Hint
content is recomputed from the current position, and a dead end can still return the ID-free
`backtrack` recovery instead of a hop.

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
  "closeness": 99,
  "attempt_number": 3
}
```

`rank` is one-based (`1` is the secret target). Within a hop-distance bucket, weighted path
tightness orders ranks and only equal weighted distances tie; the whole nearer-hop bucket
still ranks before the next one. Unreachable guesses rank after the reachable set. Distances
are directed from the guess to the target; `rank`, `closeness`, and `reachable_count` use
that same inbound distance population. `attempt_number` is the stable one-based ordinal of
each distinct accepted guess; best-first list sorting and free repeats never change it.
`temperature` is one of `Gasit`, `Fierbinte`, `Cald`, `Caldut`, `Rece`,
`Foarte rece`, or `Inghetat`. For a reachable non-target rank percentile, the boundaries
are 0.5%, 3%, 10%, 40%, and 70% before the final frozen band; a direct distance-one guess
remains `Fierbinte`.

Every successful guess response also carries one bounded comparison authored by the server:

```json
{
  "feedback": {
    "kind": "new-best",
    "message": "Cel mai bun: cu 4 locuri mai aproape.",
    "rank_delta": 4
  }
}
```

`kind` is one of `first`, `new-best`, `warmer`, `colder`, `same`, `repeat`, or `found`.
It compares only ranks already exposed to this session; `rank_delta` is optional, and clients
render the message without deriving target proximity. Pre-reveal responses keep the target id,
target label, and any
`solution` payload absent across create/get/guess/clue. The exact target object appears only
on win or give-up.

### Contexto fuzzy confirmation

An exact label, alias, or diacritic-insensitive match still plays immediately. A confident
fuzzy resolution to a non-target concept first returns without spending an attempt:

```json
{
  "ok": false,
  "needs_confirmation": true,
  "resolved_label": "București",
  "resolved_token": "ctxc_…",
  "message": "Am înțeles: București. Confirmă sau corectează.",
  "suggestions": [],
  "attempts": 0
}
```

The client accepts it by resubmitting the same `text` with optional request field
`confirm: "<resolved_token>"`. Handles are opaque and game-bound; stale, invented, or
different-resolution handles re-offer confirmation without mutation. A fuzzy resolution
that is itself the hidden target remains a direct win, so confirmation never names the
answer before it is earned.

### Contexto broad guesses and progressive clues

Cald sau Rece additionally accepts a server-owned, guess-only projection of common
Romanian surfaces. A projected guess has an opaque `ctxp_…` id and uses an existing
concept's rank/temperature scale, but it is never a target: even a surface mapped to the
target's scoring anchor remains a non-win with `rank >= 2`. Clients must treat ids and all
feedback as opaque server values and must not infer or cache projection anchors.

After three counted guesses, state may expose `next_clue_kind: "category" | "warmer"`.
The first unthemed clue retains `clue.category`; the optional second stage adds:

```json
{
  "warm_clue": {
    "label": "cuvânt familiar",
    "rank": 12,
    "message": "Mai cald: cuvânt familiar (#12)."
  }
}
```

`warm_clue.rank` is strictly better than the player's best rank when issued, is never 1,
and its label never names the target. A board created with `?category=` skips the redundant
category stage because `board_category` is already public. The clue endpoint also returns
`clue_kind` plus optional direct `category` or `word`; all fields are additive and the
operationId remains `contexto_clue`.

## 5. Conexiuni earned state and clue endpoint

`POST /api/wordgames/conexiuni/games/{game_id}/clue` is additive. It unlocks after two
mistakes; a second clue unlocks at three mistakes. At most two may be used, and each applies
the existing score penalty. The first targets the deterministic first unsolved category and
the second advances to another unsolved category when one exists. A first-clue response can
look like:

```json
{
  "ok": true,
  "clue": { "pattern": "L_________", "message": "Un grup ramas are eticheta: L_________." },
  "clues_used": 1,
  "clue_available": false,
  "clues": [{ "pattern": "L_________", "message": "Un grup ramas are eticheta: L_________." }]
}
```

The clue payload itself stays redacted: it contains no category `key`, exact category label,
tile ids, or membership. `clues_used` can reach two; after both are spent
`clue_available` remains false and another request is rejected.

Pre-terminal Conexiuni create/get/guess/clue responses use the same public view model:
`tiles` contains only public tile `{id,label}` objects still playable on the board,
and `solved` contains only groups already accepted as correct, each shaped as
`{key,label,tiles}`. Unsolved keys, labels, membership, and the full `solution` remain
absent until win/loss. A correct guess also returns its earned `{key,label}` in
`category`. Re-submitting the same four ids in another order returns HTTP 409 and leaves
lives, mistakes, clues, score, and history unchanged.

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
