# Architecture — cat_de_roman_esti

A thin, stdlib-only consumer of the Romanian KG products. It builds an in-memory
semantic graph from served records and runs a terminal "semantic network hop" game.

## Module map

```
cat_de_roman_esti/
  roedu_client.py   vendored stdlib HTTP client (urllib) — health/products/page/iter,
                    cursor pagination, fail-closed on available=false.
  graph.py          Node / Edge dataclasses + Graph (adjacency index). neighbors(),
                    node(), edge_between(). Distractor + bidirectional aware.
  engine.py         Puzzle dataclass + HopGame: load, options, hop validation, win
                    detection, scoring vs par. Mode = easy|hard.
  data.py           loading layer: load_from_client() (live server) and load_fixture()
                    (offline) both return a KgBundle (graph + puzzles).
  cli.py            terminal game loop: pick category+difficulty, fetch puzzle, render
                    current node + neighbour options + hop count, read stdin, score.
  fixtures/
    kg_sample.json  hand-authored KG snapshot for --offline play and tests.
```

Data flows in one direction:

```
ro_data_server  --HTTP /v1--> RoeduClient --records--> Graph + [Puzzle]  --> HopGame --> CLI
   (or)  fixtures/kg_sample.json --load_fixture--^
```

## Game model

A **puzzle** gives a START node and a TARGET node inside a category subgraph. The
player stands on a node and is shown its **neighbours** (one-hop reachable nodes).
Choosing a neighbour traverses the edge to it; reaching TARGET wins.

- **State**: `HopGame.path` is the list of visited node ids, starting at `start_id`.
  `current_id` is the tail. `hops == len(path) - 1`.
- **Hop validation**: a hop to `dst` is legal only if `Graph.edge_between(current, dst)`
  returns an edge *in the active mode's view*. There is no teleporting; every move is
  along a real, served edge. Distractor edges are not traversable in easy mode.
- **Win**: `current_id == target_id`.
- **Score**: base 1000; perfect at/under par; −100 per hop over par, floored at 100 for
  a finished game; 0 if not won. `par == optimal_hops` from the puzzle.

Edges are **bidirectional by default** (contract `bidirectional=1`), so they are
indexed in both directions; a `bidirectional=0` edge is one-way.

## How difficulty maps to data (the four contract levers)

| Lever | Contract field(s) | Where it's applied |
|-------|-------------------|--------------------|
| 1. Hop distance | `puzzles.optimal_hops` / `par` | Set at build time; the engine **scores against** it (`HopGame.score`), it does not change distance. |
| 2. Concept obscurity | `nodes.salience`, `nodes.difficulty_tier` | Encoded at puzzle-selection time on the producer; the engine surfaces salience/tier but does not alter it. |
| 3. Edge visibility / hints | `edges.label_ro`, `puzzles.hint_neighbors` | **Engine-controlled**: `HopGame.show_labels` and `hint_neighbors()` return content only in easy mode; hard mode returns empty. |
| 4. Distractor density | `edges.is_distractor`, `edges.strength` | **Engine-controlled**: `HopGame.include_distractors` is True only in hard mode; `options()`/`edge_between()` filter decoys out in easy mode. |

Mode → view mapping:

| | easy | hard |
|---|------|------|
| distractor edges (`is_distractor=1`) | filtered out of options + not traversable | kept as decoys, traversable |
| edge labels (`label_ro`) | shown next to each option | hidden |
| hints (`hint_neighbors`) | reachable solution next-hop highlighted | hidden |

The engine **never mutates** the graph. It filters the *view* per mode by passing
`include_distractors` into the graph queries, so the same loaded graph serves both
modes.

## Fail-closed posture

The platform's license gate is enforced server-side; the client trusts it. `iter()`
stops the moment a page reports `available=false` (gate refusal or store not built),
so a blocked product yields **zero** records rather than partial/fabricated data. A
puzzle whose start/target node is absent from the loaded graph raises on `HopGame.load`
rather than producing an unwinnable game.
