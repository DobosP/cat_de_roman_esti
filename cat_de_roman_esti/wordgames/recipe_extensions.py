"""Apply independently reviewed additions to an exact, unchanged Alchimie core.

This module never derives recipes from graph similarity. A missing catalog or an
unmatched board/graph leaves the core intact; a malformed catalog fails closed.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from functools import lru_cache
from pathlib import Path

from ..graph import Edge, Node

CATALOG_PATH = Path(__file__).resolve().parents[1] / "fixtures/alchimie_recipe_extensions_v92.json"
SCHEMA = "alchimie-recipe-extensions-v1"
MAX_PAIRS = 24
MAX_CONCEPTS = 32
MAX_RESULTS = 2
MIN_STRENGTH = 0.70
MAX_CATALOG_BYTES = 4 * 1024 * 1024


def canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def digest(value: object) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def record_snapshot(value) -> dict:
    """JSON-normalized actual Node/Edge fields, including provenance and facets."""
    return json.loads(canonical_bytes(asdict(value)))


def core_record(seeds, target, category, recipes, routes, par) -> dict:
    return {
        "seeds": list(seeds), "target": target, "category": category, "par": par,
        "recipes": [
            {"pair": list(pair), "results": list(outputs)}
            for pair, outputs in sorted(recipes.items())
        ],
        "routes": [
            [{"pair": list(pair), "results": list(outputs)} for pair, outputs in route]
            for route in routes
        ],
    }


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(f"Alchimie recipe extensions: {message}")


def _sha(value: object) -> bool:
    return (
        isinstance(value, str) and len(value) == 64
        and all(char in "0123456789abcdef" for char in value)
    )


def validate_catalog(catalog: dict) -> dict[str, dict]:
    """Validate the complete catalog, including scopes not used by this request."""
    _require(isinstance(catalog, dict) and catalog.get("schema") == SCHEMA, "invalid schema")
    _require(_sha(catalog.get("candidate_sha256")), "invalid candidate binding")
    bindings = catalog.get("bindings")
    _require(isinstance(bindings, dict), "missing source bindings")
    for name in ("pack", "kg", "rubric"):
        _require(isinstance(bindings.get(name), dict) and _sha(bindings[name].get("sha256")),
                 f"invalid {name} binding")
    reviews = catalog.get("semantic_reviews")
    _require(isinstance(reviews, list) and len(reviews) == 2, "two reviews required")
    _require(all(isinstance(r, dict) for r in reviews), "invalid review records")
    _require({r.get("role") for r in reviews} == {"factual", "quality"}, "review roles differ")
    _require(all(isinstance(r.get("reviewer"), str) and r["reviewer"].strip()
                 and _sha(r.get("sha256")) for r in reviews), "invalid review binding")
    _require(len({r["reviewer"] for r in reviews}) == 2, "reviewers must differ")
    boards = catalog.get("boards")
    _require(isinstance(boards, list) and len(boards) <= 512, "invalid board inventory")
    indexed: dict[str, dict] = {}
    board_ids: set[str] = set()
    candidate_ids: set[str] = set()
    for board in boards:
        _require(isinstance(board, dict), "invalid board")
        _require(isinstance(board.get("id"), str) and board["id"] not in board_ids,
                 "duplicate or invalid board id")
        board_ids.add(board["id"])
        fingerprint = board.get("core_sha256")
        core = board.get("core")
        _require(isinstance(core, dict) and _sha(fingerprint) and digest(core) == fingerprint,
                 "invalid core fingerprint")
        _require(fingerprint not in indexed, "duplicate core scope")
        _require(board.get("entry_sha256") == digest({k: v for k, v in board.items()
                                                     if k != "entry_sha256"}),
                 "altered board entry")
        seeds = core.get("seeds")
        _require(isinstance(seeds, list) and all(isinstance(s, str) for s in seeds)
                 and len(set(seeds)) == len(seeds) and 2 <= len(seeds) <= MAX_CONCEPTS,
                 "invalid seeds")
        _require(isinstance(core.get("target"), str) and core["target"] not in seeds,
                 "invalid target")
        _require(isinstance(core.get("category"), str) and bool(core["category"]),
                 "invalid category")
        _require(type(core.get("par")) is int and 1 <= core["par"] <= 6, "invalid par")
        recipes = core.get("recipes")
        _require(isinstance(recipes, list) and 1 <= len(recipes) <= MAX_PAIRS,
                 "invalid core recipes")
        concepts = set(seeds)
        pairs: set[tuple[str, str]] = set()
        for row in recipes:
            _require(isinstance(row, dict), "invalid recipe")
            pair, outputs = row.get("pair"), row.get("results")
            _require(isinstance(pair, list) and len(pair) == 2
                     and all(isinstance(n, str) for n in pair)
                     and pair == sorted(set(pair)), "invalid core pair")
            _require(tuple(pair) not in pairs, "duplicate core pair")
            pairs.add(tuple(pair))
            _require(isinstance(outputs, list) and 1 <= len(outputs) <= MAX_RESULTS
                     and all(isinstance(n, str) for n in outputs)
                     and len(set(outputs)) == len(outputs), "invalid core outputs")
            concepts.update(pair)
            concepts.update(outputs)
        _require(core["target"] in concepts and len(concepts) <= MAX_CONCEPTS,
                 "invalid concept bound")
        routes = core.get("routes")
        _require(isinstance(routes, list) and 1 <= len(routes) <= 4, "invalid core routes")
        by_pair = {tuple(r["pair"]): set(r["results"]) for r in recipes}
        for route in routes:
            _require(isinstance(route, list) and 1 <= len(route) <= 6, "invalid route")
            owned = set(seeds)
            for step in route:
                _require(isinstance(step, dict) and isinstance(step.get("pair"), list)
                         and isinstance(step.get("results"), list), "invalid route step")
                pair = tuple(step["pair"])
                _require(pair in by_pair and set(pair) <= owned
                         and bool(step["results"])
                         and set(step["results"]) <= by_pair[pair], "route differs from core")
                owned.update(step["results"])
            _require(core["target"] in owned, "route cannot reach target")
        nodes, edges = board.get("nodes"), board.get("edges")
        _require(isinstance(nodes, dict) and set(nodes) == concepts, "node scope mismatch")
        _require(all(isinstance(row, dict) and set(row) == set(Node.__dataclass_fields__)
                     and row.get("id") == nid
                     for nid, row in nodes.items()), "invalid node snapshots")
        _require(isinstance(edges, dict) and len(edges) <= MAX_PAIRS * 4,
                 "invalid edge snapshots")
        _require(all(isinstance(row, dict) and set(row) == set(Edge.__dataclass_fields__)
                     and row.get("id") == eid
                     for eid, row in edges.items()), "invalid edge snapshots")
        edge_directions = set()
        for edge in edges.values():
            edge_directions.add((edge["src_id"], edge["dst_id"]))
            if edge["bidirectional"]:
                edge_directions.add((edge["dst_id"], edge["src_id"]))
        _require(all((parent, output) in edge_directions for row in recipes
                     for parent in row["pair"] for output in row["results"]),
                 "missing core edge snapshots")
        additions = board.get("additions")
        _require(isinstance(additions, list) and bool(additions), "empty extension board")
        _require(len(pairs) + len(additions) <= MAX_PAIRS, "recipe pair bound exceeded")
        for addition in additions:
            _require(isinstance(addition, dict), "invalid addition")
            pair, result = addition.get("pair"), addition.get("result")
            cid = addition.get("candidate_id")
            _require(isinstance(cid, str) and cid not in candidate_ids
                     and _sha(addition.get("candidate_sha256")), "invalid candidate identity")
            candidate_ids.add(cid)
            _require(isinstance(pair, list) and len(pair) == 2
                     and all(isinstance(n, str) for n in pair)
                     and pair == sorted(set(pair)), "invalid added pair")
            _require(tuple(pair) not in pairs, "existing pair overwrite or duplicate addition")
            pairs.add(tuple(pair))
            _require(isinstance(result, str) and set(pair) | {result} <= concepts
                     and result not in pair and result not in seeds
                     and core["target"] not in pair, "addition escapes reviewed concepts")
            _require(set(pair) <= set(seeds) or result == core["target"],
                     "addition escapes reviewed cohorts")
            edge_ids = addition.get("edge_ids")
            _require(isinstance(edge_ids, list) and len(edge_ids) == 2
                     and all(eid in edges for eid in edge_ids), "missing recipe edges")
            for parent, eid in zip(pair, edge_ids, strict=True):
                edge = edges[eid]
                _require({edge.get("src_id"), edge.get("dst_id")} == {parent, result}
                         and (edge.get("src_id") == parent or edge.get("bidirectional") is True),
                         "edge endpoints or direction differ")
                strength = edge.get("strength")
                _require(type(strength) in (int, float) and MIN_STRENGTH <= strength <= 1
                         and edge.get("is_distractor") is False, "weak or distractor edge")
        indexed[fingerprint] = board
    return indexed


@lru_cache(maxsize=1)
def _load_catalog(path: str, modified_ns: int, size: int) -> dict[str, dict]:
    _require(size <= MAX_CATALOG_BYTES, "catalog size bound exceeded")
    raw = Path(path).read_bytes()
    _require(len(raw) <= MAX_CATALOG_BYTES, "catalog size bound exceeded")
    try:
        return validate_catalog(json.loads(raw))
    except (KeyError, TypeError, json.JSONDecodeError) as exc:
        raise ValueError("Alchimie recipe extensions: malformed catalog") from exc


def extend_recipes(service, seeds, target, category, core_recipes, core_routes, core_par):
    """Return a new book; mismatched scopes/actual graph metadata get no additions."""
    merged = {pair: tuple(outputs) for pair, outputs in core_recipes.items()}
    try:
        stat = CATALOG_PATH.stat()
    except FileNotFoundError:
        return merged
    catalog = _load_catalog(str(CATALOG_PATH), stat.st_mtime_ns, stat.st_size)
    core = core_record(seeds, target, category, core_recipes, core_routes, core_par)
    board = catalog.get(digest(core))
    if board is None:
        return merged
    for nid, expected in board["nodes"].items():
        node = service.node(nid)
        if node is None or record_snapshot(node) != expected:
            return merged
    for expected in board["edges"].values():
        edge = service.link(expected["src_id"], expected["dst_id"])
        if edge is None or record_snapshot(edge) != expected:
            return merged
    for addition in board["additions"]:
        pair, result = tuple(addition["pair"]), addition["result"]
        if result not in service.common_neighbors(*pair, category=category):
            return {pair: tuple(outputs) for pair, outputs in core_recipes.items()}
        merged[pair] = (result,)
    return merged
