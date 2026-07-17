#!/usr/bin/env python3
"""Apply a common-word graph wave as one rollback-protected transaction.

The default authored data stays in :mod:`common_words_v24_data`; later audited waves may
select another local data module with ``--data-module``. This entry point is the only
writer: it rejects duplicate/ambiguous concepts before calling the established
``densify_content`` puzzle rebuild, proves that existing approved pack records keep
their exact payload and status, refreshes the public mobile snapshot, validates both
fixture/pack mirrors, and restores all five files if any step fails.

New game items are intentionally optional.  They are staged only when the data module
exports explicit, full pack records through ``GAME_ITEMS`` or the builder's
``game_items`` key; such records are always forced through the pending critique gate.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
import tempfile
from collections import Counter, defaultdict
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import NoReturn

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

import densify_content  # noqa: E402
import import_candidates  # noqa: E402
import validate_games_pack  # noqa: E402
from validate_fixture import (  # noqa: E402
    CATEGORIES,
    normalize_text,
)
from validate_fixture import (  # noqa: E402
    validate as validate_fixture,
)

from cat_de_roman_esti.data import (  # noqa: E402
    content_hash,
    load_fixture,
    mobile_app_pack_snapshot,
)
from cat_de_roman_esti.wordgames.packs import (  # noqa: E402
    GAME_KINDS,
    validate_envelope,
    validate_payload,
)
from cat_de_roman_esti.wordgames.service import WordGameService  # noqa: E402

FIXTURE_COPIES = (densify_content.PACKAGE_FIXTURE, densify_content.TESTS_FIXTURE)
PACK_COPIES = (validate_games_pack.PACKAGE_PACK, validate_games_pack.TESTS_PACK)
MOBILE_CONTRACT = _REPO_ROOT / "tests" / "fixtures" / "cat_mobile_app_pack_contract.json"
TRANSACTION_FILES = (*FIXTURE_COPIES, *PACK_COPIES, MOBILE_CONTRACT)
DEFAULT_BUILD_VERSION = "fixture-v24-common-words"
DEFAULT_NOTE = (
    "v24 common-word graph wave: beginner-recognizable Romanian vocabulary, "
    "deterministic dense-graph rebuild, with curated game items kept behind review."
)


class ApplyError(RuntimeError):
    """A fail-closed authoring or transaction error."""


@dataclass(frozen=True)
class Batch:
    nodes: tuple[dict, ...]
    edges: tuple[dict, ...]
    aliases: dict[str, tuple[str, ...]]
    game_items: object
    expected_game_item_ids: tuple[str, ...]
    expected_node_ids: tuple[str, ...]
    beginner_benchmark: tuple[str, ...]
    deferred_terms: tuple[str, ...]
    intuitive_pairs: tuple[tuple[str, str], ...]
    build_version: str
    note: str


@dataclass(frozen=True)
class ProbePlan:
    baseline_node_count: int
    baseline_edge_count: int
    expected_degrees: dict[str, int]
    expected_edge_keys: frozenset[tuple[str, str, str]]
    expected_edge_records: dict[tuple[str, str, str], tuple[object, ...]]
    intuitive_pairs: tuple[tuple[str, str], ...]
    eligible_benchmark: tuple[str, ...]
    benchmark_owners: dict[str, str]


def fail(message: str) -> NoReturn:
    raise ApplyError(message)


def _load_json(blob: bytes, label: str) -> dict:
    try:
        value = json.loads(blob.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        fail(f"{label} is not valid UTF-8 JSON: {exc}")
    if not isinstance(value, dict):
        fail(f"{label} must contain a JSON object")
    return value


def _atomic_write(path: Path, blob: bytes) -> None:
    """Replace one mirror without exposing a partially written JSON document."""
    temp_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as handle:
            temp_name = handle.name
            handle.write(blob)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
        temp_name = None
    finally:
        if temp_name is not None:
            try:
                os.unlink(temp_name)
            except FileNotFoundError:
                pass


def _snapshot() -> dict[Path, bytes]:
    snapshots: dict[Path, bytes] = {}
    for path in TRANSACTION_FILES:
        try:
            snapshots[path] = path.read_bytes()
        except OSError as exc:
            fail(f"cannot snapshot {path}: {exc}")
    return snapshots


def _restore(snapshots: dict[Path, bytes]) -> None:
    errors: list[str] = []
    for path, blob in snapshots.items():
        try:
            if path.read_bytes() != blob:
                _atomic_write(path, blob)
        except OSError as exc:
            errors.append(f"{path}: {exc}")
    mismatches: list[str] = []
    for path, blob in snapshots.items():
        try:
            if path.read_bytes() != blob:
                mismatches.append(str(path))
        except OSError as exc:
            errors.append(f"{path}: cannot verify restored bytes: {exc}")
    if errors or mismatches:
        detail = "; ".join([*errors, *(f"restore mismatch: {p}" for p in mismatches)])
        raise ApplyError(f"transaction rollback was incomplete: {detail}")


def _assert_mirrors_identical() -> None:
    if FIXTURE_COPIES[0].read_bytes() != FIXTURE_COPIES[1].read_bytes():
        fail("fixture mirrors are not byte-identical")
    if PACK_COPIES[0].read_bytes() != PACK_COPIES[1].read_bytes():
        fail("games-pack mirrors are not byte-identical")


def _refresh_mobile_contract() -> None:
    payload = mobile_app_pack_snapshot(FIXTURE_COPIES[0])
    blob = (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    _atomic_write(MOBILE_CONTRACT, blob)


def _assert_mobile_contract_current() -> None:
    checked_in = _load_json(MOBILE_CONTRACT.read_bytes(), "mobile app-pack contract")
    expected = mobile_app_pack_snapshot(FIXTURE_COPIES[0])
    if checked_in != expected:
        fail("mobile app-pack contract does not match the merged fixture")


def _module_constant(module: ModuleType, *names: str, default: object = None) -> object:
    for name in names:
        if hasattr(module, name):
            return getattr(module, name)
    return default


def _as_string_tuple(value: object, label: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, (str, bytes)) or not isinstance(value, (list, tuple, set)):
        fail(f"{label} must be a sequence of strings")
    ordered = sorted(value, key=str) if isinstance(value, set) else value
    result = tuple(str(item).strip() for item in ordered)
    if any(not item for item in result):
        fail(f"{label} must not contain blank values")
    if len(result) != len(set(result)):
        fail(f"{label} contains duplicate values")
    return result


def _game_item_id_tuple(value: object) -> tuple[str, ...]:
    """Accept the flat or game-keyed ID declarations used by pack regressions."""
    if not isinstance(value, dict):
        return _as_string_tuple(value, "GAME_ITEM_IDS")
    item_ids: list[str] = []
    if set(value) <= set(GAME_KINDS):
        for game in GAME_KINDS:
            declared = value.get(game, ())
            if isinstance(declared, str):
                declared = (declared,)
            item_ids.extend(_as_string_tuple(declared, f"GAME_ITEM_IDS[{game!r}]"))
    else:
        for item_id, game in value.items():
            if game not in GAME_KINDS:
                fail(f"GAME_ITEM_IDS maps {item_id!r} to unknown game {game!r}")
            item_ids.append(str(item_id).strip())
    if any(not item_id for item_id in item_ids) or len(item_ids) != len(set(item_ids)):
        fail("GAME_ITEM_IDS contains blank or duplicate IDs")
    return tuple(item_ids)


def _normalize_node(raw: object, index: int) -> dict:
    if not isinstance(raw, dict):
        fail(f"nodes[{index}] must be an object")
    required = ("id", "node_type", "label_ro", "category", "description", "salience")
    missing = [key for key in required if key not in raw]
    if missing:
        fail(f"nodes[{index}] is missing {missing}")
    node = deepcopy(raw)
    for key in required[:-1]:
        if not isinstance(node[key], str) or not node[key].strip():
            fail(f"nodes[{index}].{key} must be a non-empty string")
        node[key] = node[key].strip()
    if node["category"] not in CATEGORIES:
        fail(f"node {node['id']!r} has unknown category {node['category']!r}")
    try:
        salience = float(node["salience"])
    except (TypeError, ValueError):
        fail(f"node {node['id']!r} has a non-numeric salience")
    if not 0.0 <= salience <= 1.0:
        fail(f"node {node['id']!r} salience must be in [0, 1]")
    node["salience"] = salience
    aliases = node.get("aliases", []) or []
    if isinstance(aliases, (str, bytes)) or not isinstance(aliases, (list, tuple)):
        fail(f"node {node['id']!r} aliases must be a sequence")
    node["aliases"] = [str(alias).strip() for alias in aliases]
    if any(not alias for alias in node["aliases"]):
        fail(f"node {node['id']!r} carries a blank alias")
    return node


def _binary_flag(value: object, label: str) -> int:
    if isinstance(value, bool):
        return int(value)
    if value in (0, 1, "0", "1"):
        return int(value)
    fail(f"{label} must be 0/1 or false/true")


def _normalize_edge(raw: object, index: int) -> dict:
    if not isinstance(raw, dict):
        fail(f"edges[{index}] must be an object")
    src = raw.get("src", raw.get("src_id"))
    dst = raw.get("dst", raw.get("dst_id"))
    relation = raw.get("relation")
    if not all(isinstance(value, str) and value.strip() for value in (src, dst, relation)):
        fail(f"edges[{index}] needs non-empty src/dst/relation strings")
    try:
        strength = float(raw.get("strength", 0.5))
    except (TypeError, ValueError):
        fail(f"edges[{index}] has a non-numeric strength")
    if not 0.0 <= strength <= 1.0:
        fail(f"edges[{index}] strength must be in [0, 1]")
    edge = {
        "src": str(src).strip(),
        "dst": str(dst).strip(),
        "relation": str(relation).strip(),
        "label_ro": str(raw.get("label_ro", "")).strip(),
        "strength": strength,
        "is_distractor": _binary_flag(
            raw.get("is_distractor", 0), f"edges[{index}].is_distractor"
        ),
        "bidirectional": _binary_flag(
            raw.get("bidirectional", 1), f"edges[{index}].bidirectional"
        ),
    }
    if "id" in raw:
        if not isinstance(raw["id"], str) or not raw["id"].strip():
            fail(f"edges[{index}].id must be a non-empty string when supplied")
        edge["id"] = raw["id"].strip()
    return edge


def _unpack_builder_result(result: object) -> tuple[object, object, object, object]:
    if isinstance(result, dict):
        nodes = result.get("nodes", result.get("kg_nodes"))
        edges = result.get("edges", result.get("kg_edges"))
        return nodes, edges, result.get("aliases", {}), result.get("game_items")
    if isinstance(result, (tuple, list)) and len(result) in (2, 3):
        game_items = result[2] if len(result) == 3 else None
        return result[0], result[1], {}, game_items
    fail("build_nodes_and_edges() must return a mapping or a two/three-item sequence")


def _load_batch(module_name: str = "common_words_v24_data") -> Batch:
    try:
        module = importlib.import_module(module_name)
    except (ImportError, SyntaxError) as exc:
        fail(f"cannot import {module_name}: {exc}")
    builder = getattr(module, "build_nodes_and_edges", None)
    if not callable(builder):
        fail(f"{module_name} must export build_nodes_and_edges()")
    nodes_raw, edges_raw, aliases_raw, built_game_items = _unpack_builder_result(builder())
    if not isinstance(nodes_raw, (list, tuple)) or not isinstance(edges_raw, (list, tuple)):
        fail("builder nodes and edges must be sequences")
    if not isinstance(aliases_raw, dict):
        fail("builder aliases must be an object keyed by node id")

    nodes = tuple(_normalize_node(raw, index) for index, raw in enumerate(nodes_raw))
    edges = tuple(_normalize_edge(raw, index) for index, raw in enumerate(edges_raw))
    aliases: dict[str, tuple[str, ...]] = {}
    for raw_id, raw_aliases in aliases_raw.items():
        node_id = str(raw_id).strip()
        aliases[node_id] = _as_string_tuple(raw_aliases, f"aliases[{node_id!r}]")

    raw_pairs = _module_constant(module, "INTUITIVE_PAIRS", "LINK_PROBES", default=())
    if isinstance(raw_pairs, (str, bytes)) or not isinstance(raw_pairs, (list, tuple, set)):
        fail("INTUITIVE_PAIRS must be a sequence of two-item pairs")
    pairs: list[tuple[str, str]] = []
    ordered_pairs = sorted(raw_pairs, key=str) if isinstance(raw_pairs, set) else raw_pairs
    for index, pair in enumerate(ordered_pairs):
        if not isinstance(pair, (list, tuple)) or len(pair) != 2:
            fail(f"INTUITIVE_PAIRS[{index}] must contain exactly two values")
        left, right = (str(value).strip() for value in pair)
        if not left or not right or left == right:
            fail(f"INTUITIVE_PAIRS[{index}] must contain two distinct non-empty values")
        pairs.append((left, right))

    build_version = str(
        _module_constant(
            module, "BUILD_VERSION", "V24_BUILD_VERSION", default=DEFAULT_BUILD_VERSION
        )
    ).strip()
    note = str(_module_constant(module, "NOTE", "BUILD_NOTE", default=DEFAULT_NOTE)).strip()
    if not build_version or not note:
        fail("BUILD_VERSION and NOTE must be non-empty")

    game_items = built_game_items
    if game_items is None:
        game_items = _module_constant(module, "GAME_ITEMS", default=None)
    return Batch(
        nodes=nodes,
        edges=edges,
        aliases=aliases,
        game_items=game_items,
        expected_game_item_ids=_game_item_id_tuple(
            _module_constant(module, "GAME_ITEM_IDS", default=())
        ),
        expected_node_ids=_as_string_tuple(
            _module_constant(module, "NEW_NODE_IDS", default=()), "NEW_NODE_IDS"
        ),
        beginner_benchmark=_as_string_tuple(
            _module_constant(module, "BEGINNER_BENCHMARK", default=()),
            "BEGINNER_BENCHMARK",
        ),
        deferred_terms=_as_string_tuple(
            _module_constant(module, "DEFERRED_AMBIGUOUS_TERMS", default=()),
            "DEFERRED_AMBIGUOUS_TERMS",
        ),
        intuitive_pairs=tuple(pairs),
        build_version=build_version,
        note=note,
    )


def _edge_key(src: str, dst: str, relation: str) -> tuple[str, str, str]:
    left, right = sorted((src, dst))
    return left, right, relation


def _fixture_edge_key(edge: dict) -> tuple[str, str, str]:
    return _edge_key(str(edge["src_id"]), str(edge["dst_id"]), str(edge["relation"]))


def _batch_edge_key(edge: dict) -> tuple[str, str, str]:
    return _edge_key(str(edge["src"]), str(edge["dst"]), str(edge["relation"]))


def _edge_signature(edge: dict) -> tuple[object, ...]:
    return (
        str(edge.get("src_id", edge.get("src"))),
        str(edge.get("dst_id", edge.get("dst"))),
        str(edge["relation"]),
        str(edge.get("label_ro", "")),
        round(float(edge.get("strength", 0.5)), 3),
        int(edge.get("is_distractor", 0)),
        int(edge.get("bidirectional", 1)),
    )


def _surface_index(nodes: list[dict] | tuple[dict, ...]) -> dict[str, set[str]]:
    owners: dict[str, set[str]] = defaultdict(set)
    for node in nodes:
        node_id = str(node["id"])
        for surface in (node_id, str(node["label_ro"]), *(node.get("aliases", []) or [])):
            key = normalize_text(str(surface))
            if key:
                owners[key].add(node_id)
    return dict(owners)


def _resolve_probe(value: str, node_ids: set[str], owners: dict[str, set[str]]) -> str:
    if value in node_ids:
        return value
    matches = owners.get(normalize_text(value), set())
    if len(matches) != 1:
        fail(f"probe {value!r} resolves to {sorted(matches)}, expected exactly one node")
    return next(iter(matches))


def _play_link_exists(edges: list[dict], src: str, dst: str) -> bool:
    """Whether the pair has a direct non-distractor edge in either authored direction."""
    for edge in edges:
        if int(edge.get("is_distractor", 0)):
            continue
        left = str(edge.get("src_id", edge.get("src")))
        right = str(edge.get("dst_id", edge.get("dst")))
        if (left == src and right == dst) or (left == dst and right == src):
            return True
    return False


def _detect_already_applied(batch: Batch, fixture: dict) -> None:
    existing_ids = {str(node["id"]) for node in fixture["kg_nodes"]}
    incoming_ids = {str(node["id"]) for node in batch.nodes}
    existing_edges = {_fixture_edge_key(edge) for edge in fixture["kg_edges"]}
    incoming_edges = {_batch_edge_key(edge) for edge in batch.edges}
    aliases_by_id = {
        str(node["id"]): {normalize_text(str(alias)) for alias in node.get("aliases", []) or []}
        for node in fixture["kg_nodes"]
    }
    aliases_applied = all(
        node_id in aliases_by_id
        and all(normalize_text(alias) in aliases_by_id[node_id] for alias in aliases)
        for node_id, aliases in batch.aliases.items()
    )
    has_authored_content = bool(incoming_ids or incoming_edges or any(batch.aliases.values()))
    content_applied = has_authored_content and (
        (not incoming_ids or incoming_ids <= existing_ids)
        and (not incoming_edges or incoming_edges <= existing_edges)
        and aliases_applied
    )
    if fixture.get("meta", {}).get("build_version") == batch.build_version or content_applied:
        fail(f"common-word wave is already applied ({batch.build_version})")


def _preflight(batch: Batch, fixture: dict) -> ProbePlan:
    if not batch.nodes and not batch.edges and not batch.aliases:
        fail("the common-word wave is empty")
    existing_nodes = list(fixture["kg_nodes"])
    existing_edges = list(fixture["kg_edges"])
    existing_node_ids = {str(node["id"]) for node in existing_nodes}
    incoming_ids = [str(node["id"]) for node in batch.nodes]
    duplicate_ids = sorted(node_id for node_id, count in Counter(incoming_ids).items() if count > 1)
    if duplicate_ids:
        fail(f"duplicate incoming node ids: {duplicate_ids}")
    collisions = sorted(set(incoming_ids) & existing_node_ids)
    if collisions:
        fail(f"incoming node ids already exist (partial/replayed wave): {collisions[:12]}")
    if batch.expected_node_ids and set(batch.expected_node_ids) != set(incoming_ids):
        missing = sorted(set(batch.expected_node_ids) - set(incoming_ids))
        extra = sorted(set(incoming_ids) - set(batch.expected_node_ids))
        fail(f"NEW_NODE_IDS differs from builder output; missing={missing}, extra={extra}")

    prospective_ids = existing_node_ids | set(incoming_ids)
    unknown_alias_targets = sorted(set(batch.aliases) - prospective_ids)
    if unknown_alias_targets:
        fail(f"alias targets do not exist in the prospective graph: {unknown_alias_targets}")

    owners = _surface_index(existing_nodes)
    incoming_surfaces: dict[str, tuple[str, str]] = {}

    def claim(surface: str, node_id: str, origin: str) -> None:
        key = normalize_text(surface)
        if not key:
            fail(f"{origin} for {node_id!r} normalizes to blank")
        if origin in {"node alias", "alias map"} and owners.get(key) == {node_id}:
            fail(f"{origin} {surface!r} is redundant for {node_id!r}")
        foreign = owners.get(key, set()) - {node_id}
        if foreign:
            fail(
                f"normalized surface collision: {surface!r} for {node_id!r} "
                f"already belongs to {sorted(foreign)}"
            )
        previous = incoming_surfaces.get(key)
        if previous is not None:
            prev_owner, prev_origin = previous
            fail(
                f"incoming normalized surface {surface!r} ({origin}/{node_id}) duplicates "
                f"{prev_origin}/{prev_owner}"
            )
        incoming_surfaces[key] = (node_id, origin)
        owners.setdefault(key, set()).add(node_id)

    for node in batch.nodes:
        node_id = str(node["id"])
        claim(node_id, node_id, "id")
        claim(str(node["label_ro"]), node_id, "label")
        for alias in node.get("aliases", []) or []:
            claim(str(alias), node_id, "node alias")
    for node_id, aliases in batch.aliases.items():
        for alias in aliases:
            claim(alias, node_id, "alias map")

    deferred_keys = {normalize_text(term) for term in batch.deferred_terms}
    incoming_word_keys = {
        key for key, (_, origin) in incoming_surfaces.items() if origin != "id"
    }
    accidentally_authored = sorted(deferred_keys & incoming_word_keys)
    if accidentally_authored:
        fail(f"deferred ambiguous terms were authored into the resolver: {accidentally_authored}")

    benchmark_keys = [normalize_text(term) for term in batch.beginner_benchmark]
    if len(benchmark_keys) != len(set(benchmark_keys)):
        fail("BEGINNER_BENCHMARK contains duplicate normalized surfaces")
    eligible_benchmark = tuple(
        term
        for term in batch.beginner_benchmark
        if normalize_text(term) not in deferred_keys
    )
    if not eligible_benchmark:
        fail("all beginner benchmark terms were marked deferred")
    benchmark_owners: dict[str, str] = {}
    unresolved_benchmark: list[str] = []
    for term in eligible_benchmark:
        matches = owners.get(normalize_text(term), set())
        if len(matches) == 1:
            benchmark_owners[term] = next(iter(matches))
        else:
            unresolved_benchmark.append(f"{term} -> {sorted(matches)}")
    if len(benchmark_owners) * 10 < len(eligible_benchmark) * 9:
        fail(
            "beginner semantic coverage is below 90%: "
            f"{len(benchmark_owners)}/{len(eligible_benchmark)}; "
            f"unresolved={unresolved_benchmark}"
        )

    existing_edge_ids = {str(edge["id"]) for edge in existing_edges}
    supplied_edge_ids = [str(edge["id"]) for edge in batch.edges if "id" in edge]
    duplicate_edge_ids = sorted(
        edge_id for edge_id, count in Counter(supplied_edge_ids).items() if count > 1
    )
    if duplicate_edge_ids:
        fail(f"duplicate incoming edge ids: {duplicate_edge_ids}")
    edge_id_collisions = sorted(set(supplied_edge_ids) & existing_edge_ids)
    if edge_id_collisions:
        fail(f"incoming edge ids already exist: {edge_id_collisions[:12]}")

    existing_edge_keys = {_fixture_edge_key(edge) for edge in existing_edges}
    incoming_edge_keys: set[tuple[str, str, str]] = set()
    for edge in batch.edges:
        src, dst = str(edge["src"]), str(edge["dst"])
        if src not in prospective_ids or dst not in prospective_ids:
            fail(f"edge endpoint does not resolve: {src!r} -> {dst!r}")
        if src == dst:
            fail(f"self-loop is not allowed: {src!r}")
        key = _batch_edge_key(edge)
        if key in existing_edge_keys:
            fail(f"incoming edge duplicates an existing edge: {key}")
        if key in incoming_edge_keys:
            fail(f"duplicate incoming edge: {key}")
        incoming_edge_keys.add(key)

    prospective_edges = [*existing_edges, *batch.edges]
    degrees: Counter[str] = Counter()
    playable_neighbors: dict[str, set[str]] = defaultdict(set)
    touched = set(incoming_ids)
    for edge in prospective_edges:
        src = str(edge.get("src_id", edge.get("src")))
        dst = str(edge.get("dst_id", edge.get("dst")))
        degrees[src] += 1
        degrees[dst] += 1
        if not int(edge.get("is_distractor", 0)):
            playable_neighbors[src].add(dst)
            playable_neighbors[dst].add(src)
    for edge in batch.edges:
        touched.update((str(edge["src"]), str(edge["dst"])))
    isolated = sorted(node_id for node_id in incoming_ids if degrees[node_id] == 0)
    if isolated:
        fail(f"new common-word nodes must not be isolated: {isolated}")
    category_by_id = {
        str(node["id"]): str(node["category"]) for node in [*existing_nodes, *batch.nodes]
    }
    low_incident = sorted(
        node_id for node_id in incoming_ids if len(playable_neighbors[node_id]) < 4
    )
    low_same_category = sorted(
        node_id
        for node_id in incoming_ids
        if sum(
            category_by_id.get(neighbor) == category_by_id[node_id]
            for neighbor in playable_neighbors[node_id]
        )
        < 2
    )
    if low_incident or low_same_category:
        fail(
            "new-node link probes failed: "
            f"incident<4={low_incident}, same-category<2={low_same_category}"
        )

    intuitive: list[tuple[str, str]] = []
    for left, right in batch.intuitive_pairs:
        src = _resolve_probe(left, prospective_ids, owners)
        dst = _resolve_probe(right, prospective_ids, owners)
        if not _play_link_exists(prospective_edges, src, dst):
            fail(f"intuitive pair lacks a direct playable link: {left!r} -> {right!r}")
        intuitive.append((src, dst))

    return ProbePlan(
        baseline_node_count=len(existing_nodes),
        baseline_edge_count=len(existing_edges),
        expected_degrees={node_id: degrees[node_id] for node_id in sorted(touched)},
        expected_edge_keys=frozenset(incoming_edge_keys),
        expected_edge_records={
            _batch_edge_key(edge): _edge_signature(edge) for edge in batch.edges
        },
        intuitive_pairs=tuple(intuitive),
        eligible_benchmark=eligible_benchmark,
        benchmark_owners=benchmark_owners,
    )


def _verify_merged_graph(batch: Batch, plan: ProbePlan, fixture: dict) -> None:
    nodes = list(fixture["kg_nodes"])
    edges = list(fixture["kg_edges"])
    if len(nodes) != plan.baseline_node_count + len(batch.nodes):
        fail("merged node count does not equal baseline plus the authored wave")
    if len(edges) != plan.baseline_edge_count + len(batch.edges):
        fail("merged edge count does not equal baseline plus the authored wave")
    if fixture.get("meta", {}).get("build_version") != batch.build_version:
        fail("densify pipeline did not persist the requested build version")

    by_id = {str(node["id"]): node for node in nodes}
    authored_node_ids = {str(node["id"]) for node in batch.nodes}
    missing_nodes = sorted((set(batch.expected_node_ids) | authored_node_ids) - set(by_id))
    if missing_nodes:
        fail(f"expected v24 nodes are absent after merge: {missing_nodes}")
    authored_aliases: dict[str, set[str]] = defaultdict(set)
    for node in batch.nodes:
        authored_aliases[str(node["id"])].update(str(alias) for alias in node["aliases"])
    for node_id, aliases in batch.aliases.items():
        authored_aliases[node_id].update(aliases)
    for node_id, aliases in authored_aliases.items():
        actual_aliases = {str(alias) for alias in by_id[node_id].get("aliases", []) or []}
        missing = sorted(aliases - actual_aliases)
        if missing:
            fail(f"authored aliases missing after merge for {node_id}: {missing}")
    actual_keys = {_fixture_edge_key(edge) for edge in edges}
    missing_edges = sorted(plan.expected_edge_keys - actual_keys)
    if missing_edges:
        fail(f"authored links are absent after merge: {missing_edges[:12]}")
    actual_edges = {_fixture_edge_key(edge): edge for edge in edges}
    changed_edges = sorted(
        key
        for key, expected in plan.expected_edge_records.items()
        if _edge_signature(actual_edges[key]) != expected
    )
    if changed_edges:
        fail(f"authored link direction/fields changed after merge: {changed_edges[:12]}")
    for node_id, expected in plan.expected_degrees.items():
        actual = by_id.get(node_id, {}).get("degree")
        if actual != expected:
            fail(f"degree probe failed for {node_id}: expected {expected}, got {actual}")

    owners = _surface_index(nodes)
    resolved_after = {
        term: next(iter(matches))
        for term in plan.eligible_benchmark
        if len(matches := owners.get(normalize_text(term), set())) == 1
    }
    if len(resolved_after) * 10 < len(plan.eligible_benchmark) * 9:
        unresolved = [
            f"{term} -> {sorted(owners.get(normalize_text(term), set()))}"
            for term in plan.eligible_benchmark
            if term not in resolved_after
        ]
        fail(
            "post-merge beginner semantic coverage is below 90%: "
            f"{len(resolved_after)}/{len(plan.eligible_benchmark)}; unresolved={unresolved}"
        )
    for term, expected_owner in plan.benchmark_owners.items():
        actual = resolved_after.get(term)
        if actual != expected_owner:
            fail(
                f"benchmark probe changed for {term!r}: "
                f"expected {expected_owner}, got {actual}"
            )
    for src, dst in plan.intuitive_pairs:
        if not _play_link_exists(edges, src, dst):
            fail(f"intuitive link probe failed after merge: {src!r} -> {dst!r}")


def _approved_projection(pack: dict) -> dict[str, list[dict]]:
    return {
        game: [deepcopy(item) for item in pack.get(game, []) if item.get("status") == "approved"]
        for game in GAME_KINDS
    }


def _assert_approved_stable(pack: dict, svc: WordGameService) -> None:
    report: list[str] = []
    survivors = import_candidates.rederive_existing_items(deepcopy(pack), svc, report)
    before = _approved_projection(pack)
    after = {
        game: [item for item in survivors[game] if item.get("status") == "approved"]
        for game in GAME_KINDS
    }
    if before != after:
        before_by_id = {item["id"]: item for records in before.values() for item in records}
        after_by_id = {item["id"]: item for records in after.values() for item in records}
        changed = sorted(
            item_id
            for item_id in set(before_by_id) | set(after_by_id)
            if before_by_id.get(item_id) != after_by_id.get(item_id)
        )
        detail = "; ".join(report[:8])
        fail(f"graph wave would alter approved pack records {changed[:20]}; {detail}")


def _records_by_game(raw_items: object) -> dict[str, list[dict]]:
    result = {game: [] for game in GAME_KINDS}
    if raw_items is None:
        return result
    if isinstance(raw_items, dict):
        extra = sorted(set(raw_items) - set(GAME_KINDS))
        if extra:
            fail(f"GAME_ITEMS contains unknown game keys: {extra}")
        for game in GAME_KINDS:
            records = raw_items.get(game, []) or []
            if not isinstance(records, (list, tuple)):
                fail(f"GAME_ITEMS[{game!r}] must be a sequence")
            for record in records:
                if not isinstance(record, dict):
                    fail(f"GAME_ITEMS[{game!r}] contains a non-object")
                result[game].append(deepcopy(record))
        return result
    if isinstance(raw_items, (list, tuple)):
        for record in raw_items:
            if not isinstance(record, dict) or record.get("game") not in GAME_KINDS:
                fail("list-form GAME_ITEMS records need a valid 'game' field")
            copied = deepcopy(record)
            game = str(copied.pop("game"))
            result[game].append(copied)
        return result
    fail("GAME_ITEMS must be a game-keyed object or a sequence of records")


def _stage_explicit_game_items(
    batch: Batch, baseline_pack: dict, svc: WordGameService
) -> tuple[bytes, tuple[str, ...]]:
    records = _records_by_game(batch.game_items)
    if not any(records.values()):
        if batch.expected_game_item_ids:
            fail("GAME_ITEM_IDS is non-empty but no explicit GAME_ITEMS were supplied")
        return PACK_COPIES[0].read_bytes(), ()

    pack = deepcopy(baseline_pack)
    existing_ids = {
        str(item["id"]) for game in GAME_KINDS for item in pack.get(game, [])
    }
    high_water = import_candidates.item_high_water(pack)
    staged_ids: list[str] = []
    for game in GAME_KINDS:
        for record in records[game]:
            if record.get("status", "pending") != "pending":
                fail(f"new game item for {game} must be pending")
            record["status"] = "pending"
            record.setdefault("source", "ai")
            if not record.get("id"):
                category = str(record.get("category", "")).strip()
                if not category:
                    fail(f"new {game} item needs a category for deterministic ID allocation")
                number = high_water[game] + 1
                record["id"] = f"{import_candidates.PREFIX[game]}_{category}_{number:03d}"
            item_id = str(record["id"])
            if item_id in existing_ids or item_id in staged_ids:
                fail(f"duplicate game item id: {item_id}")
            head, separator, suffix = item_id.rpartition("_")
            if not separator or not head.startswith(f"{import_candidates.PREFIX[game]}_"):
                fail(f"new {game} item has invalid id prefix: {item_id}")
            if not suffix.isdigit() or int(suffix) <= high_water[game]:
                fail(f"new {game} item id must allocate above high-water {high_water[game]}")
            high_water[game] = int(suffix)
            errors = validate_envelope(record, game) or validate_payload(record, game, svc)
            if errors:
                fail(f"new {game} item {item_id} is invalid: {errors[:3]}")
            pack[game].append(record)
            staged_ids.append(item_id)
    if batch.expected_game_item_ids and set(staged_ids) != set(batch.expected_game_item_ids):
        fail(
            "GAME_ITEM_IDS differs from staged records: "
            f"expected={sorted(batch.expected_game_item_ids)}, actual={sorted(staged_ids)}"
        )
    pack["meta"]["counts"] = {game: len(pack[game]) for game in GAME_KINDS}
    pack["meta"]["id_high_water"] = high_water
    if _approved_projection(pack) != _approved_projection(baseline_pack):
        fail("staging pending records changed an approved pack payload/status")
    return (json.dumps(pack, ensure_ascii=False, indent=1) + "\n").encode(), tuple(staged_ids)


def _validate_repository() -> None:
    fixture_errors = validate_fixture(FIXTURE_COPIES[0])
    pack_errors = validate_games_pack.validate(PACK_COPIES[0], FIXTURE_COPIES[0])
    pack_errors.extend(validate_games_pack.validate(PACK_COPIES[1], FIXTURE_COPIES[1]))
    if fixture_errors or pack_errors:
        detail = "; ".join([*fixture_errors[:8], *pack_errors[:8]])
        fail(f"post-write validation failed: {detail}")
    _assert_mirrors_identical()


def _fixture_content_hash(fixture: dict) -> str:
    return content_hash(fixture["kg_nodes"], fixture["kg_edges"], fixture["kg_puzzles"])


def apply(*, dry_run: bool = False, module_name: str = "common_words_v24_data") -> None:
    snapshots = _snapshot()
    try:
        _assert_mirrors_identical()
        baseline_fixture = _load_json(snapshots[FIXTURE_COPIES[0]], "package fixture")
        baseline_pack = _load_json(snapshots[PACK_COPIES[0]], "package games pack")
        batch = _load_batch(module_name)
        _detect_already_applied(batch, baseline_fixture)
        plan = _preflight(batch, baseline_fixture)
        print(
            f"apply_common_words_v24[{module_name}]: preflight GREEN — "
            f"{len(batch.nodes)} nodes, {len(batch.edges)} edges, "
            f"{len(batch.beginner_benchmark)} beginner probes, "
            f"{len(batch.intuitive_pairs)} intuitive-link probes"
        )
        if dry_run:
            print(
                f"apply_common_words_v24[{module_name}]: dry-run complete; "
                "no repository files changed"
            )
            return

        rc = densify_content.run(
            {"nodes": list(batch.nodes), "edges": list(batch.edges), "aliases": batch.aliases},
            batch.build_version,
            batch.note,
        )
        if rc != 0:
            fail("densify_content rejected the graph wave")
        merged_fixture = _load_json(FIXTURE_COPIES[0].read_bytes(), "merged package fixture")
        _verify_merged_graph(batch, plan, merged_fixture)

        svc = WordGameService(graph=load_fixture(FIXTURE_COPIES[0]).graph)
        _assert_approved_stable(baseline_pack, svc)
        pack_blob, staged_ids = _stage_explicit_game_items(batch, baseline_pack, svc)
        if staged_ids:
            for path in PACK_COPIES:
                _atomic_write(path, pack_blob)
        elif any(path.read_bytes() != snapshots[path] for path in PACK_COPIES):
            fail("games pack changed even though the data module supplied no game items")

        _refresh_mobile_contract()
        _validate_repository()
        _assert_mobile_contract_current()
        final_pack = _load_json(PACK_COPIES[0].read_bytes(), "final games pack")
        if _approved_projection(final_pack) != _approved_projection(baseline_pack):
            fail("approved pack payload/status semantics changed after final validation")
        before_hash = _fixture_content_hash(baseline_fixture)
        after_hash = _fixture_content_hash(merged_fixture)
        if before_hash == after_hash:
            fail("fixture content checksum did not change after applying a non-empty wave")
        print(
            f"apply_common_words_v24[{module_name}]: GREEN — "
            f"build={batch.build_version}, content_hash={after_hash}, "
            f"staged_items={list(staged_ids)}"
        )
    except BaseException as exc:
        try:
            _restore(snapshots)
        except BaseException as restore_exc:
            raise ApplyError(f"{exc}; additionally, rollback failed: {restore_exc}") from exc
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-module",
        default="common_words_v24_data",
        help="importable local wave module (default: common_words_v24_data)",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="run all non-mutating preflight checks only"
    )
    args = parser.parse_args(argv)
    try:
        apply(dry_run=args.dry_run, module_name=args.data_module)
    except KeyboardInterrupt:
        print("apply_common_words_v24: interrupted; transaction restored", file=sys.stderr)
        return 130
    except BaseException as exc:
        print(f"apply_common_words_v24: ERROR — {exc}; transaction restored", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
