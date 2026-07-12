"""Loading layer — turns served records (or a bundled fixture) into a Graph + puzzle.

Two sources, one shape:

  * ``load_from_client`` — pulls ``kg_nodes`` / ``kg_edges`` / ``kg_puzzles`` from a
    live Ro-data-server via the vendored ``RoeduClient`` (fail-closed: an unavailable
    product yields no records, so an empty/blocked product simply yields no puzzles).
  * ``load_fixture`` — reads a bundled JSON snapshot for ``--offline`` play and tests.

Both return the same ``KgBundle`` so the CLI and engine are source-agnostic.
"""

from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .engine import Puzzle, _as_id_list
from .graph import Graph

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"
DEFAULT_FIXTURE = FIXTURE_DIR / "kg_sample.json"


def _resolve_fixture(path: str | Path | None) -> Path:
    """Offline-fixture path: explicit arg > ``CAT_KG_FIXTURE`` env > bundled default.

    The env override lets a deployment swap the offline bundle without touching call
    sites. Caution: the curated ``kg_sample.json`` (the bundled default) is what the
    games pack's node ids reference — pointing at another fixture (e.g. the stale
    ``kg_real.json`` corpus export) silently empties every category's curated games."""
    return Path(path or os.environ.get("CAT_KG_FIXTURE") or DEFAULT_FIXTURE)
DEFAULT_MAX_NODES = 10_000
DEFAULT_MAX_EDGES = 50_000
DEFAULT_MAX_PUZZLES = 5_000
APP_PACK_APP = "cat_de_roman_esti"
APP_PACK_LAYER = "redistributable"
APP_PACK_SCHEMA_VERSION = 1
# Shape version of the manifest dict itself (bump when the manifest keys change, so a
# mobile client can detect a manifest it does not understand without parsing further).
APP_PACK_MANIFEST_VERSION = 1
MOBILE_APP_PACK_CONTRACT = "cat_de_roman_esti.mobile_app_pack.v1"
KG_PRODUCTS = ("kg_nodes", "kg_edges", "kg_puzzles")
APP_PACK_IDS = {
    "roedu:cat_de_roman_esti:kg_nodes:v1": "kg_nodes",
    "roedu:cat_de_roman_esti:kg_edges:v1": "kg_edges",
    "roedu:cat_de_roman_esti:kg_puzzles:v1": "kg_puzzles",
}
PUBLIC_ACCESS_TYPES = {"public_document", "open_license", "public_domain"}


class ClientLike(Protocol):
    """Structural type the loader needs — satisfied by RoeduClient and the fake."""

    def iter(self, product: str, **filters: object): ...


@dataclass
class KgBundle:
    """Everything needed to start games for one category scope."""

    graph: Graph
    puzzles: list[Puzzle]

    def puzzles_for(self, *, category: str | None = None, difficulty: str | None = None):
        """Strict filter: a puzzle belongs to exactly its own ``.category``.

        Return the puzzles where ``category`` is None or ``p.category == category`` AND
        ``difficulty`` is None or ``p.difficulty == difficulty``. The "mixed" bucket is
        not special-cased: ``category="mixed"`` returns only genuinely cross-category
        puzzles (``p.category == "mixed"``), and a single category never surfaces the
        mixed puzzle. A category+difficulty with no matching puzzle legitimately yields
        an empty list (e.g. the bundled fixture has no hard mixed puzzle).
        """
        out = self.puzzles
        if category is not None:
            out = [p for p in out if p.category == category]
        if difficulty is not None:
            out = [p for p in out if p.difficulty == difficulty]
        return out

    def categories(self) -> list[str]:
        cats = {n.category for n in self.graph.nodes.values() if n.category}
        return sorted(cats)


def _bundle_from_records(
    nodes: Sequence[Mapping[str, object]],
    edges: Sequence[Mapping[str, object]],
    puzzles: Sequence[Mapping[str, object]],
) -> KgBundle:
    graph = Graph.from_records(nodes, edges)
    parsed = [Puzzle.from_record(p) for p in puzzles]
    return KgBundle(graph=graph, puzzles=parsed)


def _legal_public_item(rec: Mapping[str, object]) -> bool:
    return (
        bool(rec.get("redistributable") is True)
        and str(rec.get("access_type") or "") in PUBLIC_ACCESS_TYPES
        and bool(str(rec.get("legal_basis") or "").strip())
        and rec.get("gdpr_relevant") is False
    )


def _without_public_unsafe_fields(rec: Mapping[str, object]) -> dict[str, object]:
    """Copy one public app-pack item without internal-only provenance details."""
    out = dict(rec)
    provenance = out.get("provenance")
    if isinstance(provenance, Mapping):
        out["provenance"] = {
            key: value
            for key, value in provenance.items()
            if key not in {"source_url", "sha256", "internal_path", "llms_txt"}
        }
    return out


def records_from_app_packs(raw: Mapping[str, object]) -> dict[str, list[dict[str, object]]]:
    """Normalize tagged app-pack JSON into the legacy per-product record lists.

    The accepted public layer is intentionally narrow: unknown/missing legal metadata,
    GDPR-relevant records, non-redistributable records, and internal layers are withheld
    from the app bundle. The caller gets only redistributable KG records grouped under
    ``kg_nodes`` / ``kg_edges`` / ``kg_puzzles``.
    """
    packs_obj = raw.get("packs", raw)
    packs = packs_obj if isinstance(packs_obj, list) else [packs_obj]
    records: dict[str, list[dict[str, object]]] = {name: [] for name in KG_PRODUCTS}

    for pack_obj in packs:
        if not isinstance(pack_obj, Mapping):
            continue
        if pack_obj.get("app") != APP_PACK_APP:
            continue
        if pack_obj.get("layer") != APP_PACK_LAYER:
            continue
        if pack_obj.get("schema_version") != APP_PACK_SCHEMA_VERSION:
            continue
        pack_product = APP_PACK_IDS.get(str(pack_obj.get("pack_id") or ""))
        if pack_product is None:
            continue
        for item_obj in pack_obj.get("items", []) or []:
            if not isinstance(item_obj, Mapping):
                continue
            kind = str(item_obj.get("kind") or "")
            product = {
                "kg_node": "kg_nodes",
                "kg_edge": "kg_edges",
                "kg_puzzle": "kg_puzzles",
            }.get(kind)
            if product is None or product != pack_product or not _legal_public_item(item_obj):
                continue
            records[product].append(_without_public_unsafe_fields(item_obj))
    return records


def load_app_pack_fixture(path: str | Path) -> KgBundle:
    """Load a synthetic app-pack fixture shaped like ro_data_server app packs."""
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    records = records_from_app_packs(raw)
    return _bundle_from_records(
        records["kg_nodes"],
        records["kg_edges"],
        records["kg_puzzles"],
    )


def load_fixture(path: str | Path | None = None) -> KgBundle:
    """Load a bundled KG snapshot from JSON (offline play / tests)."""
    fpath = _resolve_fixture(path)
    raw = json.loads(fpath.read_text(encoding="utf-8"))
    return _bundle_from_records(
        raw.get("kg_nodes", []),
        raw.get("kg_edges", []),
        raw.get("kg_puzzles", []),
    )


# --------------------------------------------------------------------------- manifest
def _canonical_content_bytes(
    nodes: Sequence[Mapping[str, object]],
    edges: Sequence[Mapping[str, object]],
    puzzles: Sequence[Mapping[str, object]],
) -> bytes:
    """Stable serialization of the KG payload for hashing.

    Records are sorted by ``id`` and each record is serialized with sorted keys, so the
    digest depends only on CONTENT — never on file formatting, key order, or the order
    records happen to appear in. This makes the hash a reliable cache key for a mobile
    client comparing its bundled offline copy against the server's.
    """

    def _by_id(rec: Mapping[str, object]) -> str:
        return str(rec.get("id", ""))

    payload = {
        "kg_nodes": sorted((dict(n) for n in nodes), key=_by_id),
        "kg_edges": sorted((dict(e) for e in edges), key=_by_id),
        "kg_puzzles": sorted((dict(p) for p in puzzles), key=_by_id),
    }
    return json.dumps(
        payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")


def content_hash(
    nodes: Sequence[Mapping[str, object]],
    edges: Sequence[Mapping[str, object]],
    puzzles: Sequence[Mapping[str, object]],
) -> str:
    """Deterministic ``sha256:<hex>`` digest over the canonical KG content."""
    digest = hashlib.sha256(_canonical_content_bytes(nodes, edges, puzzles)).hexdigest()
    return f"sha256:{digest}"


def manifest_from_records(
    nodes: Sequence[Mapping[str, object]],
    edges: Sequence[Mapping[str, object]],
    puzzles: Sequence[Mapping[str, object]],
    *,
    build_version: str = "unknown",
    generated_at: str = "",
) -> dict[str, object]:
    """Build the trust manifest from already-loaded KG records (pure function)."""
    return {
        "app": APP_PACK_APP,
        "schema_version": APP_PACK_SCHEMA_VERSION,
        "manifest_version": APP_PACK_MANIFEST_VERSION,
        "build_version": build_version,
        "generated_at": generated_at,
        "content_hash": content_hash(nodes, edges, puzzles),
        "counts": {
            "nodes": len(nodes),
            "edges": len(edges),
            "puzzles": len(puzzles),
        },
    }


def fixture_manifest(path: str | Path | None = None) -> dict[str, object]:
    """Deterministic trust manifest for the bundled offline fixture.

    A generated mobile client can rely on this to (a) pick the right generated types via
    ``schema_version``, (b) detect a stale cached offline bundle by comparing
    ``content_hash`` against the server's, and (c) surface the human-facing
    ``build_version`` / ``generated_at``. It is a pure function of the fixture content —
    no clock, no env, cheap to recompute — so the same fixture always yields the same
    manifest and a regeneration that changes any record changes the hash.
    """
    fpath = _resolve_fixture(path)
    raw = json.loads(fpath.read_text(encoding="utf-8"))
    meta = raw.get("meta") if isinstance(raw.get("meta"), Mapping) else {}
    return manifest_from_records(
        raw.get("kg_nodes", []),
        raw.get("kg_edges", []),
        raw.get("kg_puzzles", []),
        build_version=str(meta.get("build_version") or "unknown"),
        generated_at=str(meta.get("generated_at") or ""),
    )


# ------------------------------------------------------------- mobile app-pack snapshot
def _mobile_public_records(raw: Mapping[str, object]) -> tuple[
    list[dict[str, object]],
    list[dict[str, object]],
    list[dict[str, object]],
]:
    """Project a KG fixture into the public field names exported to mobile.

    The source KG puzzle records include server-side helper fields such as
    ``solution_path`` and ``hint_neighbors``. They are deliberately excluded here: mobile
    gets the public graph and puzzle endpoints only, then derives gameplay locally.
    """

    nodes = [
        {
            "id": str(rec.get("id") or ""),
            "label_ro": str(rec.get("label_ro") or rec.get("title") or rec.get("id") or ""),
        }
        for rec in raw.get("kg_nodes", [])
        if isinstance(rec, Mapping) and rec.get("id")
    ]
    edges = [
        {
            "id": str(rec.get("id") or ""),
            "src_id": str(rec.get("src_id") or ""),
            "dst_id": str(rec.get("dst_id") or ""),
        }
        for rec in raw.get("kg_edges", [])
        if isinstance(rec, Mapping) and rec.get("src_id") and rec.get("dst_id")
    ]
    puzzles = [
        {
            "id": str(rec.get("id") or ""),
            "start_id": str(rec.get("start_id") or ""),
            "target_id": str(rec.get("target_id") or ""),
            "difficulty": str(rec.get("difficulty") or ""),
        }
        for rec in raw.get("kg_puzzles", [])
        if (
            isinstance(rec, Mapping)
            and rec.get("id")
            and rec.get("start_id")
            and rec.get("target_id")
        )
    ]
    return (
        sorted(nodes, key=lambda rec: str(rec["id"])),
        sorted(edges, key=lambda rec: str(rec["id"])),
        sorted(puzzles, key=lambda rec: str(rec["id"])),
    )


def _mobile_normalized_records(
    nodes: Sequence[Mapping[str, object]],
    edges: Sequence[Mapping[str, object]],
    puzzles: Sequence[Mapping[str, object]],
) -> tuple[list[dict[str, object]], list[list[str]], list[dict[str, object]]]:
    """Normalize cat-exported field names to the mobile verifier's hash projection."""

    mobile_nodes = [
        {
            "id": str(rec.get("id") or ""),
            "label": str(rec.get("label") or rec.get("label_ro") or ""),
        }
        for rec in nodes
    ]
    mobile_edges = [
        sorted([str(rec.get("src_id") or ""), str(rec.get("dst_id") or "")])
        for rec in edges
    ]
    mobile_puzzles = [
        {
            "id": str(rec.get("id") or ""),
            "start": str(rec.get("start") or rec.get("start_id") or ""),
            "target": str(rec.get("target") or rec.get("target_id") or ""),
            "difficulty": str(rec.get("difficulty") or ""),
        }
        for rec in puzzles
    ]
    return mobile_nodes, mobile_edges, mobile_puzzles


def mobile_app_pack_content_hash(
    nodes: Sequence[Mapping[str, object]],
    edges: Sequence[Mapping[str, object]],
    puzzles: Sequence[Mapping[str, object]],
) -> str:
    """Hash the public mobile app-pack projection.

    This intentionally matches ``apps/cat-mobile/src/cat/manifest.ts``: node/puzzle
    records are sorted by id, edge pairs are undirected and sorted, object keys are
    sorted, and no hidden puzzle helper fields participate.
    """

    mobile_nodes, mobile_edges, mobile_puzzles = _mobile_normalized_records(
        nodes, edges, puzzles
    )

    def _by_id(rec: Mapping[str, object]) -> str:
        return str(rec.get("id", ""))

    payload = {
        "kg_nodes": sorted(mobile_nodes, key=_by_id),
        "kg_edges": sorted(mobile_edges, key=lambda edge: "|".join(edge)),
        "kg_puzzles": sorted(mobile_puzzles, key=_by_id),
    }
    canonical = json.dumps(
        payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(canonical).hexdigest()}"


def mobile_app_pack_snapshot(path: str | Path | None = None) -> dict[str, object]:
    """Deterministic public app-pack snapshot consumed by roedu-mobile tests."""

    fpath = _resolve_fixture(path)
    raw = json.loads(fpath.read_text(encoding="utf-8"))
    meta = raw.get("meta") if isinstance(raw.get("meta"), Mapping) else {}
    nodes, edges, puzzles = _mobile_public_records(raw)
    return {
        "contract": MOBILE_APP_PACK_CONTRACT,
        "manifest": {
            "app": APP_PACK_APP,
            "schema_version": APP_PACK_SCHEMA_VERSION,
            "manifest_version": APP_PACK_MANIFEST_VERSION,
            "build_version": str(meta.get("build_version") or "unknown"),
            "generated_at": str(meta.get("generated_at") or ""),
            "content_hash": mobile_app_pack_content_hash(nodes, edges, puzzles),
            "counts": {
                "nodes": len(nodes),
                "edges": len(edges),
                "puzzles": len(puzzles),
            },
        },
        "kg_nodes": nodes,
        "kg_edges": edges,
        "kg_puzzles": puzzles,
    }


def _puzzle_node_ids(puzzles: Sequence[Mapping[str, object]]) -> set[str]:
    """Every node id any puzzle references (endpoints + solution_path + hints)."""
    wanted: set[str] = set()
    for rec in puzzles:
        for key in ("start_id", "target_id"):
            val = rec.get(key)
            if val is not None:
                wanted.add(str(val))
        for key in ("solution_path", "hint_neighbors"):
            for nid in _as_id_list(rec.get(key)):
                wanted.add(nid)
    return wanted


def load_from_client(
    client: ClientLike,
    *,
    category: str | None = None,
    difficulty: str | None = None,
    max_nodes: int | None = DEFAULT_MAX_NODES,
    max_edges: int | None = DEFAULT_MAX_EDGES,
    max_puzzles: int | None = DEFAULT_MAX_PUZZLES,
) -> KgBundle:
    """Pull the KG products from a live server (or fake) into a bundle.

    Fail-closed flows naturally from ``RoeduClient.iter``: if a product reports
    ``available=false`` (gate refusal / store not built) it yields nothing, and the
    resulting bundle simply has fewer records — never fabricated ones.

    Mixed / cross-category puzzles (``category == "mixed"``) and any puzzle whose
    ``solution_path`` strays outside the requested category would otherwise reference
    nodes the single-category node fetch never loaded, leaving a solution node missing
    from the graph (an unwinnable game). To stay robust we fetch puzzles first — the
    requested category *plus* the ``mixed`` bucket — then, if any referenced node is not
    covered by the category node fetch, widen to the UNION of categories by loading the
    full node set. Single-category puzzles whose nodes are all in scope keep loading just
    the requested category. The post-condition: no solution_path node id is ever missing.
    """
    puzzle_filters: list[dict[str, str]] = []
    if category:
        # The requested start-category, and the cross-category "mixed" bucket, which the
        # producer emits separately (its category is literally "mixed", so a plain
        # category filter would exclude it).
        puzzle_filters.append({"category": category})
        if category != "mixed":
            puzzle_filters.append({"category": "mixed"})
    else:
        puzzle_filters.append({})
    if difficulty:
        for pf in puzzle_filters:
            pf["difficulty"] = difficulty

    puzzles: list[Mapping[str, object]] = []
    seen_pids: set[str] = set()
    for pf in puzzle_filters:
        remaining = None if max_puzzles is None else max(0, max_puzzles - len(puzzles))
        if remaining == 0:
            break
        for rec in client.iter("kg_puzzles", max_records=remaining, **pf):
            pid = str(rec.get("id"))
            if pid in seen_pids:
                continue
            seen_pids.add(pid)
            puzzles.append(rec)

    node_filter = {"category": category} if category else {}
    nodes = list(client.iter("kg_nodes", max_records=max_nodes, **node_filter))
    loaded_ids = {str(n.get("id")) for n in nodes}

    # If a (mixed / cross-category) puzzle references a node the category fetch missed,
    # widen to the union: load the full node set so every solution node is present.
    needed = _puzzle_node_ids(puzzles)
    if category and not needed <= loaded_ids:
        nodes = list(client.iter("kg_nodes", max_records=max_nodes))

    # Edges are not category-scoped at the product level; pull all and let the graph
    # index them. Cross-category edges are harmless — neighbours() skips out-of-scope
    # destinations that aren't loaded as nodes.
    edges = list(client.iter("kg_edges", max_records=max_edges))
    return _bundle_from_records(nodes, edges, puzzles)
