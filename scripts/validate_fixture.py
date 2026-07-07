#!/usr/bin/env python3
"""Self-contained validator for the bundled KG fixture (kg_sample.json).

This is a COMMITTED gate: it re-derives every puzzle invariant the producer
(``romania_scraper.kg.puzzles.generate_puzzles``) guarantees, plus the
packaging/shape invariants the two bundled fixture copies must hold, using ONLY
the standard library. It deliberately re-implements the generator's
direction-aware BFS and bucket scoping (rather than importing romania_scraper)
so the gate keeps working in the runtime package, which has no romania_scraper
dependency.

Usage as a CI / pre-commit gate::

    python scripts/validate_fixture.py [fixture_path]

Exits 0 (GREEN) when the fixture is clean, 1 on any error, after printing a
per-class summary of how many checks passed / failed.

Public API: :func:`validate(fixture_path) -> list[str]` returns human-readable
error strings (empty list == clean).
"""

from __future__ import annotations

import json
import sys
from collections import Counter, deque
from pathlib import Path

# ---------------------------------------------------------------------------
# Locations of the two byte-identical fixture copies (relative to repo root).
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parent.parent
PACKAGE_FIXTURE = _REPO_ROOT / "cat_de_roman_esti" / "fixtures" / "kg_sample.json"
TESTS_FIXTURE = _REPO_ROOT / "tests" / "fixtures" / "kg_sample.json"
DEFAULT_FIXTURE = PACKAGE_FIXTURE

# ---------------------------------------------------------------------------
# Contract constants (mirror romania_scraper.kg.{models,puzzles}). Kept inline so
# this module is stdlib-only and usable inside the runtime package.
# ---------------------------------------------------------------------------
HOP_BANDS = {"easy": (2, 3), "hard": (4, 7)}
MIXED_CATEGORY = "mixed"
CATEGORIES = (
    "istorie", "literatura", "geografie", "personalitati",
    "arta_cultura", "stiinta", "societate", "limba",
    # Pop-culture shelf (ADR-0011). Mirrors cat_de_roman_esti.wordgames.categories —
    # tests/test_games_pack_invariants.py asserts the two never drift.
    "muzica", "film_tv", "meme_net", "sport", "viata_de_roman", "gastronomie",
)
DIFFICULTY_TIERS = ("easy", "medium", "hard")
GAME_MODES = ("easy", "hard")

# salience -> difficulty_tier bands: >=0.66 easy / 0.33..0.66 medium / <0.33 hard.
TIER_EASY_MIN = 0.66
TIER_MEDIUM_MIN = 0.33

# Exact field sets per record kind (the "field shapes": node 8 / edge 8 / puzzle 11).
NODE_FIELDS = frozenset({
    "id", "node_type", "label_ro", "category", "description",
    "salience", "difficulty_tier", "degree",
})
EDGE_FIELDS = frozenset({
    "id", "src_id", "dst_id", "relation", "label_ro",
    "strength", "is_distractor", "bidirectional",
})
PUZZLE_FIELDS = frozenset({
    "id", "start_id", "target_id", "category", "difficulty", "optimal_hops",
    "par", "solution_path", "hint_neighbors", "start_salience", "target_salience",
})

# The error classes the main() summary groups by. Every error string is prefixed
# with one of these so the per-class summary can be computed without re-checking.
ERROR_CLASSES = (
    "copies_identical",
    "structure",
    "field_shapes",
    "unique_ids",
    "node_tier_bands",
    "alias_unique",
    "label_style",
    "meta_counts",
    "puzzle_par",
    "puzzle_hop_band",
    "puzzle_hints",
    "puzzle_ids_resolve",
    "puzzle_shortest_path",
    "puzzle_category_scope",
    "puzzle_distractor_shortcut",
)

# Concept labels must stay SHORT (playable, typeable): at most this many words.
# Proper titles/official names (work/org/event/...) are exempt — they carry short
# aliases instead. Aliases themselves always obey the cap.
LABEL_MAX_WORDS = 5


def normalize_text(text: str) -> str:
    """Accent-stripped, casefolded, whitespace-collapsed form (mirrors
    ``cat_de_roman_esti.wordgames.service.normalize`` — the resolver's key)."""
    import unicodedata

    decomposed = unicodedata.normalize("NFKD", text)
    no_accents = "".join(c for c in decomposed if not unicodedata.combining(c))
    return " ".join(no_accents.casefold().split())


def tier_for_salience(salience: float) -> str:
    """Band a salience score (0..1) into a difficulty tier (easy|medium|hard)."""
    if salience >= TIER_EASY_MIN:
        return "easy"
    if salience >= TIER_MEDIUM_MIN:
        return "medium"
    return "hard"


def _as_bool(value: object) -> bool:
    """Coerce a served field (1/0, "1"/"0", true/false) to a bool.

    Mirrors ``cat_de_roman_esti.graph._as_bool`` so the validator interprets
    ``is_distractor`` / ``bidirectional`` exactly as the consumer engine does.
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "t"}
    return bool(value)


def build_adjacency(
    edges: list[dict], *, include_distractors: bool = False,
) -> dict[str, set[str]]:
    """Direction-aware adjacency over an edge list (mirrors the generator).

    Forward hop ``src -> dst`` always; reverse hop ``dst -> src`` ONLY when the
    edge is ``bidirectional``. Distractors are excluded unless
    ``include_distractors`` is set. ``is_distractor`` / ``bidirectional`` are
    coerced via :func:`_as_bool` (the fixture stores them as 0/1 ints).
    """
    adj: dict[str, set[str]] = {}
    for e in edges:
        if not include_distractors and _as_bool(e.get("is_distractor", 0)):
            continue
        src, dst = e["src_id"], e["dst_id"]
        adj.setdefault(src, set()).add(dst)
        adj.setdefault(dst, set())  # ensure dst is a known node for BFS
        if _as_bool(e.get("bidirectional", 1)):
            adj[dst].add(src)
    return adj


def bfs_shortest_path(
    adj: dict[str, set[str]], start: str, target: str,
) -> list[str] | None:
    """Shortest path (inclusive of both ends) or None — sorted-neighbour BFS.

    Identical traversal order to ``romania_scraper.kg.puzzles.bfs_shortest_path``
    so a reconstructed path matches the generator's choice when several shortest
    paths of equal length exist.
    """
    if start == target:
        return [start]
    if start not in adj or target not in adj:
        return None
    prev: dict[str, str] = {start: start}
    frontier: deque[str] = deque([start])
    while frontier:
        current = frontier.popleft()
        for nxt in sorted(adj.get(current, ())):
            if nxt in prev:
                continue
            prev[nxt] = current
            if nxt == target:
                path = [target]
                while path[-1] != start:
                    path.append(prev[path[-1]])
                path.reverse()
                return path
            frontier.append(nxt)
    return None


def _bfs_distance(adj: dict[str, set[str]], start: str, target: str) -> int | None:
    """Shortest-path hop count, or None if unreachable.

    Order-independent (used for the distractor-shortcut check, where only the
    LENGTH of the shortest path on the full graph matters).
    """
    path = bfs_shortest_path(adj, start, target)
    return None if path is None else len(path) - 1


def _edges_within_category(edges: list[dict], in_cat: set[str]) -> list[dict]:
    """Edges whose BOTH endpoints are in ``in_cat`` — the in-category subgraph."""
    return [e for e in edges if e["src_id"] in in_cat and e["dst_id"] in in_cat]


# ---------------------------------------------------------------------------
# validate()
# ---------------------------------------------------------------------------
def validate(fixture_path: str | Path = DEFAULT_FIXTURE) -> list[str]:
    """Validate the bundled fixture; return human-readable error strings.

    Empty list == clean. Each error is prefixed ``<class>: `` where ``<class>``
    is one of :data:`ERROR_CLASSES`, so ``main()`` can group a per-class summary.
    """
    errors: list[str] = []
    path = Path(fixture_path)

    # --- copies byte-identical -------------------------------------------------
    # Compare the requested fixture against BOTH canonical copies (whichever it
    # is, the other copy must match it byte-for-byte).
    try:
        primary_bytes = path.read_bytes()
    except OSError as exc:
        return [f"structure: cannot read fixture {path}: {exc}"]

    for other in (PACKAGE_FIXTURE, TESTS_FIXTURE):
        if other.resolve() == path.resolve():
            continue
        try:
            other_bytes = other.read_bytes()
        except OSError as exc:
            errors.append(f"copies_identical: cannot read copy {other}: {exc}")
            continue
        if other_bytes != primary_bytes:
            errors.append(
                f"copies_identical: {path} and {other} are NOT byte-identical "
                f"({len(primary_bytes)} vs {len(other_bytes)} bytes)"
            )

    # --- parse + top-level structure ------------------------------------------
    try:
        data = json.loads(primary_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return errors + [f"structure: fixture is not valid JSON: {exc}"]

    if not isinstance(data, dict):
        return errors + ["structure: top-level fixture is not a JSON object"]
    for key in ("meta", "kg_nodes", "kg_edges", "kg_puzzles"):
        if key not in data:
            errors.append(f"structure: missing top-level key {key!r}")
    if errors and any(e.startswith("structure: missing") for e in errors):
        # Cannot meaningfully continue without the core lists.
        if not all(k in data for k in ("kg_nodes", "kg_edges", "kg_puzzles")):
            return errors

    nodes = data["kg_nodes"]
    edges = data["kg_edges"]
    puzzles = data["kg_puzzles"]
    meta = data.get("meta", {})

    for name, seq in (("kg_nodes", nodes), ("kg_edges", edges), ("kg_puzzles", puzzles)):
        if not isinstance(seq, list):
            errors.append(f"structure: {name} is not a JSON array")
    if any(not isinstance(s, list) for s in (nodes, edges, puzzles)):
        return errors

    # --- field shapes ----------------------------------------------------------
    for i, n in enumerate(nodes):
        if not isinstance(n, dict):
            errors.append(f"field_shapes: kg_nodes[{i}] is not an object")
            continue
        keys = set(n.keys())
        # ``aliases`` is the one OPTIONAL node field (ADR-0012): alternate exact
        # surface forms (inflections/synonyms/short titles) the resolver accepts.
        if keys - {"aliases"} != NODE_FIELDS:
            errors.append(
                f"field_shapes: node {n.get('id', i)!r} has fields {sorted(keys)}, "
                f"expected {sorted(NODE_FIELDS)} (8 fields, plus optional 'aliases')"
            )
        if "aliases" in n and (
            not isinstance(n["aliases"], list)
            or any(not isinstance(a, str) or not a.strip() for a in n["aliases"])
        ):
            errors.append(
                f"field_shapes: node {n.get('id', i)!r} aliases must be a list of "
                "non-empty strings"
            )
        if not isinstance(n.get("id"), str) or not n.get("id"):
            errors.append(f"field_shapes: node at index {i} has non-string/empty id")
        if not isinstance(n.get("salience"), (int, float)):
            errors.append(f"field_shapes: node {n.get('id', i)!r} salience not numeric")
        if n.get("category") not in CATEGORIES:
            errors.append(
                f"field_shapes: node {n.get('id', i)!r} category "
                f"{n.get('category')!r} not in CATEGORIES"
            )
        if n.get("difficulty_tier") not in DIFFICULTY_TIERS:
            errors.append(
                f"field_shapes: node {n.get('id', i)!r} difficulty_tier "
                f"{n.get('difficulty_tier')!r} not a valid tier"
            )

    for i, e in enumerate(edges):
        if not isinstance(e, dict):
            errors.append(f"field_shapes: kg_edges[{i}] is not an object")
            continue
        keys = set(e.keys())
        if keys != EDGE_FIELDS:
            errors.append(
                f"field_shapes: edge {e.get('id', i)!r} has fields {sorted(keys)}, "
                f"expected {sorted(EDGE_FIELDS)} (8 fields)"
            )
        for fld in ("id", "src_id", "dst_id"):
            if not isinstance(e.get(fld), str) or not e.get(fld):
                errors.append(
                    f"field_shapes: edge at index {i} has non-string/empty {fld}"
                )

    for i, p in enumerate(puzzles):
        if not isinstance(p, dict):
            errors.append(f"field_shapes: kg_puzzles[{i}] is not an object")
            continue
        keys = set(p.keys())
        if keys != PUZZLE_FIELDS:
            errors.append(
                f"field_shapes: puzzle {p.get('id', i)!r} has fields {sorted(keys)}, "
                f"expected {sorted(PUZZLE_FIELDS)} (11 fields)"
            )
        for fld in ("optimal_hops", "par"):
            if not isinstance(p.get(fld), int) or isinstance(p.get(fld), bool):
                errors.append(
                    f"field_shapes: puzzle {p.get('id', i)!r} {fld} not an int"
                )
        for fld in ("solution_path", "hint_neighbors"):
            if not isinstance(p.get(fld), list) or not all(
                isinstance(x, str) for x in p.get(fld, [])
            ):
                errors.append(
                    f"field_shapes: puzzle {p.get('id', i)!r} {fld} not a list[str]"
                )
        if p.get("difficulty") not in GAME_MODES:
            errors.append(
                f"field_shapes: puzzle {p.get('id', i)!r} difficulty "
                f"{p.get('difficulty')!r} not a game mode"
            )

    # If any record is structurally broken, the deeper invariants below would
    # raise; bail out reporting the shape errors first.
    if errors and any(e.startswith("field_shapes:") for e in errors):
        # Continue only if the records are at least dict-shaped with the ids we
        # need; otherwise return early to avoid KeyErrors.
        if not (
            all(isinstance(n, dict) and "id" in n for n in nodes)
            and all(isinstance(e, dict) and {"id", "src_id", "dst_id"} <= set(e) for e in edges)
            and all(
                isinstance(p, dict)
                and {"id", "start_id", "target_id", "category", "difficulty",
                     "optimal_hops", "par", "solution_path", "hint_neighbors"} <= set(p)
                for p in puzzles
            )
        ):
            return errors

    # --- unique ids ------------------------------------------------------------
    for name, seq in (("node", nodes), ("edge", edges), ("puzzle", puzzles)):
        counts = Counter(r["id"] for r in seq)
        dupes = sorted(i for i, c in counts.items() if c > 1)
        for dup in dupes:
            errors.append(f"unique_ids: duplicate {name} id {dup!r} ({counts[dup]}x)")

    # --- node difficulty_tier matches salience band ---------------------------
    for n in nodes:
        sal = n["salience"]
        expected = tier_for_salience(float(sal))
        if n["difficulty_tier"] != expected:
            errors.append(
                f"node_tier_bands: node {n['id']!r} salience={sal} -> tier "
                f"{expected!r} but fixture says {n['difficulty_tier']!r}"
            )

    # --- aliases resolve unambiguously (ADR-0012) -------------------------------
    # The resolver keys on the normalized form; an alias must never collide with a
    # node label/id (labels always win) or with another node's alias — a typed word
    # has exactly one meaning.
    label_owner: dict[str, str] = {}
    for n in nodes:
        label_owner.setdefault(normalize_text(str(n["label_ro"])), str(n["id"]))
        label_owner.setdefault(normalize_text(str(n["id"])), str(n["id"]))
    alias_owner: dict[str, str] = {}
    for n in nodes:
        for alias in n.get("aliases", []) or []:
            key = normalize_text(str(alias))
            if not key:
                errors.append(f"alias_unique: node {n['id']!r} has a blank alias")
                continue
            owner = label_owner.get(key)
            if owner is not None and owner != n["id"]:
                errors.append(
                    f"alias_unique: node {n['id']!r} alias {alias!r} collides with "
                    f"the label/id of node {owner!r}"
                )
            elif owner == n["id"]:
                errors.append(
                    f"alias_unique: node {n['id']!r} alias {alias!r} is redundant "
                    "with its own label/id"
                )
            prev = alias_owner.get(key)
            if prev is not None and prev != n["id"]:
                errors.append(
                    f"alias_unique: alias {alias!r} claimed by both {prev!r} "
                    f"and {n['id']!r}"
                )
            alias_owner.setdefault(key, str(n["id"]))

    # --- label style: short, typeable concepts (ADR-0012) -----------------------
    # Concept labels stay <= LABEL_MAX_WORDS words; proper titles/official names
    # (work/org/event/...) are exempt but their aliases obey the cap too.
    for n in nodes:
        if n.get("node_type") == "concept" and len(str(n["label_ro"]).split()) > LABEL_MAX_WORDS:
            errors.append(
                f"label_style: concept {n['id']!r} label {n['label_ro']!r} exceeds "
                f"{LABEL_MAX_WORDS} words"
            )
        for alias in n.get("aliases", []) or []:
            if len(str(alias).split()) > LABEL_MAX_WORDS:
                errors.append(
                    f"label_style: node {n['id']!r} alias {alias!r} exceeds "
                    f"{LABEL_MAX_WORDS} words"
                )

    # --- meta counts match actual ----------------------------------------------
    counts = meta.get("counts", {}) if isinstance(meta, dict) else {}
    for key, actual in (
        ("nodes", len(nodes)), ("edges", len(edges)), ("puzzles", len(puzzles)),
    ):
        declared = counts.get(key)
        if declared != actual:
            errors.append(
                f"meta_counts: meta.counts.{key}={declared!r} != actual {actual}"
            )
    declared_by_cat = counts.get("by_category", {})
    actual_by_cat = dict(sorted(Counter(n["category"] for n in nodes).items()))
    if declared_by_cat and declared_by_cat != actual_by_cat:
        errors.append(
            f"meta_counts: meta.counts.by_category {declared_by_cat} != actual "
            f"{actual_by_cat}"
        )
    declared_pcd = counts.get("puzzles_by_cat_diff", {})
    actual_pcd = dict(sorted(
        Counter(f"{p['category']}/{p['difficulty']}" for p in puzzles).items()
    ))
    if declared_pcd and declared_pcd != actual_pcd:
        errors.append(
            f"meta_counts: meta.counts.puzzles_by_cat_diff {declared_pcd} != actual "
            f"{actual_pcd}"
        )

    # --- per-puzzle invariants -------------------------------------------------
    node_ids = {n["id"] for n in nodes}
    cat_by_id = {n["id"]: n["category"] for n in nodes}

    # Precompute the bucket adjacencies once (mirrors generate_puzzles scoping):
    # full-graph adj (mixed) + per-category in-category adj, with and without
    # distractors.
    full_adj_play = build_adjacency(edges, include_distractors=False)
    full_adj_all = build_adjacency(edges, include_distractors=True)
    cat_adj_play: dict[str, dict[str, set[str]]] = {}
    cat_adj_all: dict[str, dict[str, set[str]]] = {}
    for cat in CATEGORIES:
        in_cat = {nid for nid, c in cat_by_id.items() if c == cat}
        bucket_edges = _edges_within_category(edges, in_cat)
        cat_adj_play[cat] = build_adjacency(bucket_edges, include_distractors=False)
        cat_adj_all[cat] = build_adjacency(bucket_edges, include_distractors=True)

    # Validate every edge endpoint resolves (so adjacency / paths are meaningful).
    for e in edges:
        for fld in ("src_id", "dst_id"):
            if e[fld] not in node_ids:
                errors.append(
                    f"puzzle_ids_resolve: edge {e['id']!r} {fld}={e[fld]!r} "
                    f"is not a known node id"
                )

    for p in puzzles:
        pid = p["id"]
        cat = p["category"]
        diff = p["difficulty"]
        path = p["solution_path"]
        hops = p["optimal_hops"]
        par = p["par"]

        # all solution/edge node ids resolve
        unresolved = [nid for nid in path if nid not in node_ids]
        for nid in unresolved:
            errors.append(
                f"puzzle_ids_resolve: puzzle {pid!r} solution node {nid!r} "
                f"is not a known node id"
            )
        if not path:
            errors.append(f"puzzle_shortest_path: puzzle {pid!r} has empty solution_path")
            continue
        if p["start_id"] != path[0]:
            errors.append(
                f"puzzle_shortest_path: puzzle {pid!r} start_id {p['start_id']!r} "
                f"!= solution_path[0] {path[0]!r}"
            )
        if p["target_id"] != path[-1]:
            errors.append(
                f"puzzle_shortest_path: puzzle {pid!r} target_id {p['target_id']!r} "
                f"!= solution_path[-1] {path[-1]!r}"
            )

        # par == optimal_hops == len(solution_path) - 1
        if not (par == hops == len(path) - 1):
            errors.append(
                f"puzzle_par: puzzle {pid!r} par={par} optimal_hops={hops} "
                f"len(path)-1={len(path) - 1} (must all be equal)"
            )

        # hop band per difficulty (easy [2,3], hard [4,7])
        lo, hi = HOP_BANDS.get(diff, (None, None))
        if lo is not None and not (lo <= hops <= hi):
            errors.append(
                f"puzzle_hop_band: puzzle {pid!r} ({diff}) optimal_hops={hops} "
                f"outside band [{lo},{hi}]"
            )

        # hint_neighbors == solution_path[1:]
        if p["hint_neighbors"] != path[1:]:
            errors.append(
                f"puzzle_hints: puzzle {pid!r} hint_neighbors {p['hint_neighbors']} "
                f"!= solution_path[1:] {path[1:]}"
            )

        # category scope: non-mixed solution stays in-category; mixed crosses >=2
        path_cats = {cat_by_id.get(nid) for nid in path if nid in cat_by_id}
        if cat == MIXED_CATEGORY:
            if len(path_cats) < 2:
                errors.append(
                    f"puzzle_category_scope: mixed puzzle {pid!r} crosses only "
                    f"{len(path_cats)} category ({sorted(c for c in path_cats if c)}); "
                    f"must cross >=2"
                )
        elif path_cats - {cat}:
            offending = sorted(c for c in path_cats if c and c != cat)
            errors.append(
                f"puzzle_category_scope: {cat} puzzle {pid!r} solution leaves "
                f"category via {offending}"
            )

        # Pick the bucket adjacency exactly as generate_puzzles did.
        if cat == MIXED_CATEGORY:
            adj_play, adj_all = full_adj_play, full_adj_all
        elif cat in cat_adj_play:
            adj_play, adj_all = cat_adj_play[cat], cat_adj_all[cat]
        else:
            errors.append(
                f"puzzle_category_scope: puzzle {pid!r} category {cat!r} is "
                f"neither a known category nor {MIXED_CATEGORY!r}"
            )
            continue

        # solution_path is a real shortest path on the NON-distractor bucket graph
        if unresolved:
            # Can't BFS reliably; the resolve error above already records it.
            continue
        gen_dist = _bfs_distance(adj_play, p["start_id"], p["target_id"])
        if gen_dist is None:
            errors.append(
                f"puzzle_shortest_path: puzzle {pid!r} start {p['start_id']!r} "
                f"cannot reach target {p['target_id']!r} on the non-distractor "
                f"{'full' if cat == MIXED_CATEGORY else cat} subgraph"
            )
        elif gen_dist != hops:
            errors.append(
                f"puzzle_shortest_path: puzzle {pid!r} optimal_hops={hops} but real "
                f"shortest path on non-distractor subgraph is {gen_dist}"
            )
        # Verify each consecutive hop is a real edge in the playable adjacency.
        for a, b in zip(path, path[1:], strict=False):
            if b not in adj_play.get(a, set()):
                errors.append(
                    f"puzzle_shortest_path: puzzle {pid!r} hop {a!r}->{b!r} is not "
                    f"a real (direction-aware, non-distractor) edge in its subgraph"
                )

        # NO distractor edge shortcuts below par: shortest path on the FULL bucket
        # graph (INCLUDING distractors, direction-aware) must be >= par.
        full_dist = _bfs_distance(adj_all, p["start_id"], p["target_id"])
        if full_dist is not None and full_dist < par:
            errors.append(
                f"puzzle_distractor_shortcut: puzzle {pid!r} par={par} but a "
                f"distractor path shortens start->target to {full_dist} hops on the "
                f"full (with-distractor) subgraph"
            )

    return errors


# ---------------------------------------------------------------------------
# main() — pre-commit / CI gate
# ---------------------------------------------------------------------------
def _summarize(errors: list[str]) -> dict[str, int]:
    """Group error strings by their ``<class>:`` prefix."""
    by_class: Counter[str] = Counter()
    for e in errors:
        cls = e.split(":", 1)[0].strip()
        by_class[cls] += 1
    return dict(by_class)


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    fixture = Path(argv[0]) if argv else DEFAULT_FIXTURE

    errors = validate(fixture)
    by_class = _summarize(errors)

    print(f"validate_fixture: {fixture}")
    print("-" * 60)
    for cls in ERROR_CLASSES:
        n = by_class.get(cls, 0)
        status = "FAIL" if n else "ok"
        print(f"  [{status:>4}] {cls:<28} {n} error(s)")
    # Any error class not in the known list (defensive).
    for cls in sorted(set(by_class) - set(ERROR_CLASSES)):
        print(f"  [FAIL] {cls:<28} {by_class[cls]} error(s)")
    print("-" * 60)

    if errors:
        print(f"RED: {len(errors)} error(s)")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("GREEN: fixture is valid (0 errors)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
