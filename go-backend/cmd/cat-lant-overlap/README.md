# Lanț near-duplicate screen

Read-only S1 check for Lanț prospects. A prospect that passes blind play and
factual review can still replay a served board: the 2026-11 Transilvania →
Munții Apuseni prospect shared both shortest routes and every visible choice with
the Transilvania branch of served `lt_geografie_239` (see
`docs/content-registry/OWNER_QUEUE.md`). Run this command before authoring a
prospect, not after four review jobs.

```sh
go -C go-backend build -o "$SCRATCH/cat-lant-overlap" ./cmd/cat-lant-overlap
"$SCRATCH/cat-lant-overlap" --root "$REPO" --start n_transilvania --target n_muntii_apuseni [--par N]
"$SCRATCH/cat-lant-overlap" --root "$REPO" --prospects "$SCRATCH/prospects.json"
"$SCRATCH/cat-lant-overlap" --root "$REPO" --served-sanity
```

`--root` is a checkout holding `go-backend/internal/content/bundled.json`. The
prospect list is a JSON array of `{"start","target","par"?}` (at most 256). `par`
defaults to the shortest distance and may not be below it. `--served-sanity`
checks every served Lanț board against the rest of the pack (itself excluded)
and shows how often the screen fires on content that is known to be served.

## Rules

Routes are the complete shortest-route DAG from `BoardShortestRoutesForReview`.
Lanț moves follow directed legal adjacency (a link is walkable backwards only when
it is bidirectional), so routes are compared in order and direction; a reversed
sub-path does not match.

- `subpath` is true for a served board when every shortest route of the prospect
  is a contiguous run of node ids inside some shortest route of that one board.
  `near_duplicate` is true when any served board has `subpath`. The check is per
  board, not a union across boards: a prospect whose routes are covered only by
  different boards is not flagged.
- `menu_overlap` is the share of the prospect's distinct visible choices that also
  appear in the served board's route menus. A choice is the node the menu is shown
  at, the offered node id and its short caption. Menus come from
  `BoardRouteMenusForReview` at every shortest-route prefix, detours included.
- `shared_nodes` and `shared_steps` list the route nodes and directed route steps
  common to both boards. A board is listed when it has `subpath`, a shared step or
  any shared menu choice. Matches sort sub-paths first, then by routes covered,
  menu share and board id; at most 20 are listed and `matches_total` counts all.

The output is `cat-lant-overlap-1` JSON with the bundle SHA-256 and manifest content
hash, deterministic and without timestamps. Exit zero means the screen completed;
a `near_duplicate` is data for the screen, not an error. Treat it as a park (S1) of the
prospect and register it.

## Threat model

The orchestrator controls the executable, `--root` and every path. The prospect
list is untrusted: strict UTF-8 JSON that rejects duplicate and unknown fields,
trailing data, empty or oversized lists (256 prospects, 1 MiB) and over-long ids.
The list must be a regular file, not a symlink, and is read once within its bound.
Prospect values only name graph nodes; they cannot select a path, write a file or
reach the network. The bundle is read through `os.Root`, must be a regular file of at
most 32 MiB and passes strict JSON and native decoding, so a bundle outside the
checkout is unreachable. Work is bounded: a board or prospect with more than 4096
shortest routes or more than 2048 route menus is refused rather than truncated.
The command never starts a server, uses no network and writes only its report to
stdout. It does not change serving code. The bundle holds private answers: redirect
the report to a private scratch path. A same-user process replacing the executable
or the checkout concurrently is outside this model. The screen finds structural
replays; it does not judge fun, accuracy or wording, and a prospect that shares
only some routes or hubs with a board still needs reviewer judgement.
