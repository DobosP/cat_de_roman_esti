"""Reviewed authored quick-game boards, additive to the frozen V38 collection."""

from __future__ import annotations

import hashlib
import itertools
import json
import math
from collections import Counter
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from ..data import DEFAULT_FIXTURE
from .categories import is_known
from .derived_catalog import (
    DEFAULT_DERIVED_CATALOG,
    DerivedBoard,
    DerivedCatalog,
    _candidate_id,
    _competition_ranks,
)
from .discovery_world import Identifier, Text, valid_reference
from .packs import (
    DEFAULT_PACK,
    DEFAULT_RUBRIC,
    DEFAULT_RUBRIC_SHA256,
    DIFFICULTIES,
    normalized_text_sha256,
)
from .recipe_extensions import record_snapshot
from .service import get_service

CATALOG_PATH = Path(__file__).resolve().parents[1] / "fixtures/quick_games_v92.json"
CATALOG_SHA256 = "85c89ec82d27a19ba619604ed3c47b09e3bb18e1718343db6d56c03b0999761c"
MAX_BOARDS = 256
MAX_BYTES = 2 * 1024 * 1024


class AuthoredBoard(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    id: Identifier
    game: Identifier
    source_id: Identifier
    category: Identifier
    difficulty: Identifier
    payload: dict
    sources: list[Text] = Field(min_length=1, max_length=16)
    rationale: Text


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2,
                       allow_nan=False) + "\n").encode()


def digest(value: object) -> str:
    return hashlib.sha256(json_bytes(value)).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(f"quick catalog: {message}")


def core_payload_hash() -> str:
    return digest(json.loads(DEFAULT_DERIVED_CATALOG.read_bytes())["boards"])


def bindings(*, live: bool) -> dict:
    result = {"kg_sha256": normalized_text_sha256(DEFAULT_FIXTURE),
              "rubric_sha256": (normalized_text_sha256(DEFAULT_RUBRIC)
                                if DEFAULT_RUBRIC.exists() else DEFAULT_RUBRIC_SHA256),
              "core_payload_sha256": core_payload_hash()}
    if live:
        result["pack_sha256"] = normalized_text_sha256(DEFAULT_PACK)
        result["core_catalog_sha256"] = normalized_text_sha256(DEFAULT_DERIVED_CATALOG)
    return result


def graph_strengths(service) -> dict[frozenset[str], float]:
    strengths = {}
    for edge in service.graph.edges:
        if not edge.is_distractor:
            pair = frozenset((edge.src_id, edge.dst_id))
            strengths[pair] = max(strengths.get(pair, 0.0), min(1.0, max(0.0, edge.strength)))
    return strengths


def visible_ids(row: dict) -> list[str]:
    p = row["payload"]
    return ([*p["members"], p["intruder"]] if row["game"] == "intrusul"
            else [n for pair in p["pairs"] for n in pair["members"]])


def _score(value: float) -> int:
    return int(math.floor(min(100.0, max(0.0, value)) + 0.5))


def _mean(values) -> float:
    return sum(values) / len(values)


def rate_board(raw: dict, service, strengths: dict) -> dict:
    """Use the established V38 structural gates and score formulas, never author scores."""
    row = AuthoredBoard.model_validate(raw).model_dump()
    game = row["game"]
    require(game in {"intrusul", "perechi"}, "unknown game")
    require(row["id"].startswith("iq92_" if game == "intrusul" else "pq92_"), "id namespace")
    require(row["source_id"].startswith("aq92_"), "source namespace")
    require(is_known(row["category"]) and row["difficulty"] in DIFFICULTIES, "category/difficulty")
    require(all(valid_reference(url) for url in row["sources"]), "source references")
    payload = row["payload"]
    if game == "intrusul":
        require(set(payload) == {"members", "intruder", "group_label"}, "intrusul shape")
        require(isinstance(payload["members"], list) and len(payload["members"]) == 3
                and isinstance(payload["intruder"], str)
                and isinstance(payload["group_label"], str) and payload["group_label"].strip(),
                "intrusul payload")
    else:
        require(set(payload) == {"pairs"} and isinstance(payload["pairs"], list)
                and len(payload["pairs"]) == 4, "perechi shape")
        require(all(isinstance(p, dict) and set(p) == {"members", "group_label"}
                    and isinstance(p["members"], list) and len(p["members"]) == 2
                    and isinstance(p["group_label"], str) and p["group_label"].strip()
                    for p in payload["pairs"]), "perechi payload")
    ids = visible_ids(row)
    require(all(isinstance(n, str) and service.exists(n) for n in ids), "unknown concept")
    require(len(set(ids)) == len(ids), "duplicate visible concept")
    saliences = [service.node(n).salience for n in ids]
    def strength(a, b):
        return strengths.get(frozenset((a, b)), 0.0)
    if game == "intrusul":
        members = payload["members"]
        require(len({service.node(n).node_type for n in ids}) == 1, "intrusul type shortcut")
        inside = [strength(a, b) for a, b in itertools.combinations(members, 2)]
        positive = [value for value in inside if value >= .60]
        require(len(positive) >= 2, "weak trio")
        require(all(frozenset((n, payload["intruder"])) not in strengths for n in members),
                "intruder has an inlier link")
        familiarity = _score(100 * (.65 * _mean(saliences) + .35 * min(saliences)))
        cohesion = 100 * (.60 * _mean(positive) + .40 * min(positive))
        quality = _score(.55 * cohesion + .25 * (100 * len(positive) / 3) + 20)
        starter = min(saliences) >= .35 and min(inside) >= .70
    else:
        pairs = [frozenset(p["members"]) for p in payload["pairs"]]
        intended = [strength(*p["members"]) for p in payload["pairs"]]
        cross = [strength(a, b) for a, b in itertools.combinations(ids, 2)
                 if frozenset((a, b)) not in pairs]
        require(min(intended) >= .60 and max(cross) < .60, "ambiguous or weak matching")
        ordered = sorted(saliences)
        familiarity = _score(100 * (.50 * _mean(saliences)
                                   + .30 * ordered[(len(ordered) - 1) // 4]
                                   + .20 * min(saliences)))
        association = 100 * (.60 * _mean(intended) + .40 * min(intended))
        separation = 100 * max(0.0, 1 - max(cross) / .60)
        quality = _score(.75 * association + .25 * separation)
        starter = min(saliences) >= .35 and min(intended) >= .70 and max(cross) == 0
    standard = _score(.60 * familiarity + .40 * quality)
    require(standard >= 55, "below preferred quality shelf")
    return {"id": _candidate_id(game, row["source_id"], payload), "game": game,
            "source_id": row["source_id"], "category": row["category"],
            "difficulty": row["difficulty"], "payload": payload,
            "romanian_familiarity": familiarity, "play_quality": quality,
            "standard_score": standard, "starter_score": _score(.75 * familiarity + .25 * quality),
            "starter_eligible": starter, "standard_rank": 0, "starter_rank": None}


def rated_boards(rows: list[dict], base: DerivedCatalog, service) -> list[dict]:
    require(isinstance(rows, list) and 0 < len(rows) <= MAX_BOARDS
            and all(isinstance(r, dict) and isinstance(r.get("id"), str) for r in rows),
            "board bound/shape")
    require(len({r["id"] for r in rows}) == len(rows), "duplicate authored id")
    strengths = graph_strengths(service)
    rated = [rate_board(r, service, strengths) for r in rows]
    visible = {(r.game, frozenset(visible_ids({"game": r.game, "payload": r.payload})))
               for r in base._boards}
    trios = {frozenset(r.payload["members"]) for r in base._boards if r.game == "intrusul"}
    for row in rated:
        key = row["game"], frozenset(visible_ids(row))
        require(key not in visible, "reused visible board")
        visible.add(key)
        if row["game"] == "intrusul":
            trio = frozenset(row["payload"]["members"])
            require(trio not in trios, "reused inlier trio")
            trios.add(trio)
    require(max(Counter((r["game"], r["source_id"]) for r in rated).values()) <= 3,
            "source family cap")
    for game in ("intrusul", "perechi"):
        rows_for_game = [r for r in rated if r["game"] == game]
        for field, rank_field in (("standard_score", "standard_rank"),
                                  ("starter_score", "starter_rank")):
            selected = rows_for_game if field == "standard_score" else [
                r for r in rows_for_game if r["starter_eligible"]]
            ordered, ranks = _competition_ranks(selected, field)
            for row, rank in zip(ordered, ranks, strict=True):
                row[rank_field] = rank
    return rated


def validate_catalog(raw: dict, base: DerivedCatalog, service=None) -> list[DerivedBoard]:
    service = service or get_service()
    require(isinstance(raw, dict) and raw.get("kind") == "quick-content-catalog-v1", "schema")
    require(raw.get("bindings") == bindings(live=True), "source drift")
    reviews = raw.get("reviews", [])
    require(isinstance(reviews, list) and len(reviews) == 2
            and all(isinstance(r, dict) and isinstance(r.get("reviewer"), str)
                    and r["reviewer"].strip() for r in reviews), "review records")
    require({r.get("role") for r in reviews} == {"factual", "quality"}
            and len({r["reviewer"].strip().casefold() for r in reviews}) == 2,
            "independent reviews")
    for value in [raw.get("candidate_sha256"), *(r.get("sha256") for r in reviews)]:
        require(isinstance(value, str) and len(value) == 64
                and all(c in "0123456789abcdef" for c in value), "review digest")
    rows = raw.get("authored")
    require(isinstance(rows, list), "missing authored rows")
    rated = rated_boards(rows, base, service)
    require(raw.get("boards") == rated, "rating or payload drift")
    ids = {n for row in rows for n in visible_ids(row)}
    require(raw.get("nodes") == {n: record_snapshot(service.node(n)) for n in sorted(ids)},
            "concept provenance drift")
    return [DerivedBoard(
        game=r["game"], category=r["category"], difficulty=r["difficulty"], payload=r["payload"],
        _catalog_id=r["id"], _source_id=r["source_id"],
        _romanian_familiarity=r["romanian_familiarity"],
        _play_quality=r["play_quality"], _standard_score=r["standard_score"],
        _starter_score=r["starter_score"], _starter_eligible=r["starter_eligible"],
        _standard_rank=r["standard_rank"], _starter_rank=r["starter_rank"],
    ) for r in rated]


def extend_catalog(base: DerivedCatalog) -> DerivedCatalog:
    if not CATALOG_SHA256:
        return base
    try:
        require(CATALOG_PATH.stat().st_size <= MAX_BYTES, "catalog too large")
        require(normalized_text_sha256(CATALOG_PATH) == CATALOG_SHA256, "artifact digest drift")
        extra = validate_catalog(json.loads(CATALOG_PATH.read_bytes()), base)
    except (OSError, UnicodeError) as exc:
        raise ValueError("quick catalog: cannot read bound catalog or sources") from exc
    return DerivedCatalog([*base._boards, *extra])
