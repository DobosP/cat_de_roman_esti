"""Private V38 derived-board catalog and source-balanced deterministic selection.

This module is additive: the V37 ``GamesPack`` implementation and its daily hash
namespace remain untouched.  Derived board IDs, source IDs, scores, and ranks are
server-only inputs and must never be copied into API responses.
"""

from __future__ import annotations

import hashlib
import json
import os
import random
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from ..data import DEFAULT_FIXTURE
from .packs import (
    DEFAULT_PACK,
    DEFAULT_RANKINGS,
    DEFAULT_RUBRIC,
    DEFAULT_RUBRIC_SHA256,
    DIFFICULTIES,
    normalized_text_sha256,
)

DERIVED_GAMES = ("intrusul", "perechi")
PACK_DIR = Path(__file__).resolve().parent.parent / "fixtures"
DEFAULT_DERIVED_CATALOG = PACK_DIR / "derived_catalog_v38.json"

SCHEMA_VERSION = 1
FORMULA_VERSION = "v38-derived-1"
MAX_VARIANTS_PER_SOURCE = 3
# Updated only with a reviewed, generator-produced bundled artifact.
DEFAULT_DERIVED_CATALOG_SHA256 = (
    "1072bfe0d0fd7cf1ef88506dd8f190acb2d33e7e1273f29ae7860d8173099331"
)

_META_FIELDS = {
    "schema_version",
    "formula_version",
    "pack_sha256",
    "kg_sha256",
    "rubric_sha256",
    "v37_rankings_sha256",
    "counts",
}
_COUNT_FIELDS = {"total", "by_game", "sources_by_game", "starter_by_game"}
_BOARD_FIELDS = {
    "id",
    "game",
    "source_id",
    "category",
    "difficulty",
    "romanian_familiarity",
    "play_quality",
    "standard_score",
    "starter_score",
    "starter_eligible",
    "standard_rank",
    "starter_rank",
    "payload",
}


@dataclass(frozen=True)
class DerivedBoard:
    """One internally ranked derived puzzle; private fields are never serialized."""

    game: str
    category: str
    difficulty: str
    payload: dict
    _catalog_id: str = field(repr=False, compare=False)
    _source_id: str = field(repr=False, compare=False)
    _romanian_familiarity: int = field(repr=False, compare=False)
    _play_quality: int = field(repr=False, compare=False)
    _standard_score: int = field(repr=False, compare=False)
    _starter_score: int = field(repr=False, compare=False)
    _starter_eligible: bool = field(repr=False, compare=False)
    _standard_rank: int = field(repr=False, compare=False)
    _starter_rank: int | None = field(repr=False, compare=False)


def score_band_weight(score: int) -> int:
    """Return one to five stable integer tickets; equal scores always tie."""

    if isinstance(score, bool) or not isinstance(score, int):
        return 1
    if score >= 85:
        return 5
    if score >= 75:
        return 4
    if score >= 65:
        return 3
    if score >= 55:
        return 2
    return 1


def _rounded_mean(values: list[int]) -> int:
    return (sum(values) + len(values) // 2) // len(values)


def _weighted_choice(items: list, weights: list[int], rng: random.Random):
    total = sum(weights)
    ticket = rng.randrange(total)
    for item, weight in zip(items, weights, strict=True):
        ticket -= weight
        if ticket < 0:
            return item
    raise AssertionError("derived weighted selection exhausted its ticket range")


def _rendezvous(
    items: list,
    weights: list[int],
    key_for,
    *,
    namespace: str,
):
    def rank(pair) -> tuple[bytes, str]:
        item, weight = pair
        base = key_for(item)
        tickets = [hashlib.blake2b(base.encode(), digest_size=8).digest()]
        for ticket in range(1, weight):
            versioned = f"{base}:v38:{namespace}:{ticket}"
            tickets.append(hashlib.blake2b(versioned.encode(), digest_size=8).digest())
        return min(tickets), str(base)

    return min(zip(items, weights, strict=True), key=rank)[0]


class DerivedCatalog:
    """Finite derived boards grouped by private source before candidate selection."""

    def __init__(self, boards: list[DerivedBoard]):
        self._boards = sorted(boards, key=lambda board: board._catalog_id)

    def pool(
        self,
        game: str,
        *,
        category: str | None = None,
        difficulty: str | None = None,
        exclude_source_ids: set[str] | None = None,
        starter: bool = False,
    ) -> list[DerivedBoard]:
        pool = [board for board in self._boards if board.game == game]
        if category is not None:
            pool = [board for board in pool if board.category == category]
        if difficulty is not None:
            pool = [board for board in pool if board.difficulty == difficulty]
        if exclude_source_ids:
            pool = [board for board in pool if board._source_id not in exclude_source_ids]
        if starter:
            pool = [board for board in pool if board._starter_eligible]
        return pool

    def counts(self) -> dict[str, int]:
        return {game: len(self.pool(game)) for game in DERIVED_GAMES}

    @staticmethod
    def _by_source(pool: list[DerivedBoard]) -> list[tuple[str, list[DerivedBoard]]]:
        grouped: dict[str, list[DerivedBoard]] = {}
        for board in pool:
            grouped.setdefault(board._source_id, []).append(board)
        return [(source, grouped[source]) for source in sorted(grouped)]

    @staticmethod
    def _score(board: DerivedBoard, starter: bool) -> int:
        return board._starter_score if starter else board._standard_score

    def pick_seeded(
        self,
        game: str,
        rng: random.Random,
        *,
        category: str | None = None,
        difficulty: str | None = None,
        exclude_source_ids: set[str] | None = None,
        starter: bool = False,
    ) -> DerivedBoard | None:
        pool = self.pool(
            game,
            category=category,
            difficulty=difficulty,
            exclude_source_ids=exclude_source_ids,
            starter=starter,
        )
        sources = self._by_source(pool)
        if not sources:
            return None
        source_scores = [
            _rounded_mean([self._score(board, starter) for board in boards])
            for _, boards in sources
        ]
        source = _weighted_choice(
            sources,
            [score_band_weight(score) for score in source_scores],
            rng,
        )
        candidates = source[1]
        return _weighted_choice(
            candidates,
            [score_band_weight(self._score(board, starter)) for board in candidates],
            rng,
        )

    def pick_daily(
        self,
        game: str,
        daily: str,
        *,
        category: str | None = None,
        difficulty: str | None = None,
    ) -> DerivedBoard | None:
        """Pick a stable source then variant; never widen an empty filtered shelf."""

        pool = self.pool(game, category=category, difficulty=difficulty)
        sources = self._by_source(pool)
        if not sources:
            return None
        source_scores = [
            _rounded_mean([board._standard_score for board in boards])
            for _, boards in sources
        ]
        selected_source = _rendezvous(
            sources,
            [score_band_weight(score) for score in source_scores],
            lambda source: (
                f"{daily}:{game}:{category or ''}:{difficulty or ''}:{source[0]}"
            ),
            namespace="source",
        )
        candidates = selected_source[1]
        return _rendezvous(
            candidates,
            [score_band_weight(board._standard_score) for board in candidates],
            lambda board: (
                f"{daily}:{game}:{category or ''}:{difficulty or ''}:"
                f"{selected_source[0]}:{board._catalog_id}"
            ),
            namespace="candidate",
        )


def _candidate_id(game: str, source_id: str, payload: dict) -> str:
    canonical = json.dumps(
        {"game": game, "source_id": source_id, "payload": payload},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    prefix = "vi" if game == "intrusul" else "vp"
    return f"{prefix}_{hashlib.sha256(canonical).hexdigest()[:20]}"


def _require_score(row: dict, name: str) -> int:
    value = row.get(name)
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 100:
        raise ValueError(f"derived catalog: {row.get('id')} {name} must be 0..100")
    return value


def _validate_payload(row: dict, source: dict) -> None:
    payload = row.get("payload")
    if not isinstance(payload, dict):
        raise ValueError(f"derived catalog: {row.get('id')} payload must be an object")
    groups = source["groups"]
    labels = source["group_labels"]
    if row["game"] == "intrusul":
        if set(payload) != {"members", "intruder", "group_label"}:
            raise ValueError("derived catalog: intrusul payload schema drift")
        members = payload.get("members")
        intruder = payload.get("intruder")
        if (
            not isinstance(members, list)
            or len(members) != 3
            or len(set(members)) != 3
            or not all(isinstance(node_id, str) for node_id in members)
            or not isinstance(intruder, str)
            or intruder in members
        ):
            raise ValueError("derived catalog: invalid intrusul members")
        matching = [key for key, values in groups.items() if set(members) <= set(values)]
        if len(matching) != 1 or any(intruder in groups[key] for key in matching):
            raise ValueError("derived catalog: intrusul source grouping drift")
        if intruder not in {node for values in groups.values() for node in values}:
            raise ValueError("derived catalog: intrusul intruder is outside its source")
        if payload.get("group_label") != labels[matching[0]]:
            raise ValueError("derived catalog: intrusul group label drift")
        return

    if set(payload) != {"pairs"}:
        raise ValueError("derived catalog: perechi payload schema drift")
    pairs = payload.get("pairs")
    if not isinstance(pairs, list) or len(pairs) != 4:
        raise ValueError("derived catalog: perechi requires exactly four pairs")
    used_groups: set[str] = set()
    used_nodes: set[str] = set()
    for pair in pairs:
        if not isinstance(pair, dict) or set(pair) != {"members", "group_label"}:
            raise ValueError("derived catalog: perechi pair schema drift")
        members = pair.get("members")
        if (
            not isinstance(members, list)
            or len(members) != 2
            or len(set(members)) != 2
            or not all(isinstance(node_id, str) for node_id in members)
        ):
            raise ValueError("derived catalog: invalid perechi pair members")
        matching = [key for key, values in groups.items() if set(members) <= set(values)]
        if len(matching) != 1 or matching[0] in used_groups:
            raise ValueError("derived catalog: perechi source grouping drift")
        if pair.get("group_label") != labels[matching[0]]:
            raise ValueError("derived catalog: perechi group label drift")
        if used_nodes & set(members):
            raise ValueError("derived catalog: perechi reuses a visible node")
        used_groups.add(matching[0])
        used_nodes.update(members)


def load_derived_catalog(path: str | Path | None = None) -> DerivedCatalog:
    """Load the exact bundled V38 artifact; any source or schema drift fails closed."""

    if os.environ.get("CAT_GAMES_PACK") or os.environ.get("CAT_KG_FIXTURE"):
        raise ValueError(
            "derived catalog: runtime fixture override requires a matching V38 catalog"
        )
    selected = Path(path or DEFAULT_DERIVED_CATALOG)
    try:
        raw = json.loads(selected.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"derived catalog: cannot read {selected}: {exc}") from exc
    if selected.resolve() == DEFAULT_DERIVED_CATALOG.resolve():
        actual = normalized_text_sha256(selected)
        if actual != DEFAULT_DERIVED_CATALOG_SHA256:
            raise ValueError("derived catalog: bundled artifact digest drift")
    if not isinstance(raw, dict) or set(raw) != {"meta", "boards"}:
        raise ValueError("derived catalog: top level must contain exactly meta and boards")
    meta = raw["meta"]
    rows = raw["boards"]
    if not isinstance(meta, dict) or set(meta) != _META_FIELDS or not isinstance(rows, list):
        raise ValueError("derived catalog: metadata/schema drift")
    if (
        isinstance(meta["schema_version"], bool)
        or not isinstance(meta["schema_version"], int)
        or meta["schema_version"] != SCHEMA_VERSION
    ):
        raise ValueError("derived catalog: unsupported schema version")
    if meta["formula_version"] != FORMULA_VERSION:
        raise ValueError("derived catalog: unsupported formula version")
    bindings = {
        "pack_sha256": DEFAULT_PACK,
        "kg_sha256": DEFAULT_FIXTURE,
        "v37_rankings_sha256": DEFAULT_RANKINGS,
    }
    for name, source_path in bindings.items():
        if meta.get(name) != normalized_text_sha256(source_path):
            raise ValueError(f"derived catalog: {name} source drift")
    expected_rubric = (
        normalized_text_sha256(DEFAULT_RUBRIC)
        if DEFAULT_RUBRIC.exists()
        else DEFAULT_RUBRIC_SHA256
    )
    if meta.get("rubric_sha256") != expected_rubric:
        raise ValueError("derived catalog: rubric_sha256 source drift")

    counts = meta.get("counts")
    if not isinstance(counts, dict) or set(counts) != _COUNT_FIELDS:
        raise ValueError("derived catalog: counts schema drift")
    if any(
        not isinstance(counts.get(name), dict)
        or set(counts[name]) != set(DERIVED_GAMES)
        for name in ("by_game", "sources_by_game", "starter_by_game")
    ):
        raise ValueError("derived catalog: per-game counts schema drift")
    count_values = [
        counts.get("total"),
        *(
            counts[name][game]
            for name in ("by_game", "sources_by_game", "starter_by_game")
            for game in DERIVED_GAMES
        ),
    ]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or value < 0
        for value in count_values
    ):
        raise ValueError("derived catalog: counts must be non-negative integers")

    pack = json.loads(DEFAULT_PACK.read_text(encoding="utf-8"))
    sources = {str(rec["id"]): rec for rec in pack["conexiuni"]}
    ranking = json.loads(DEFAULT_RANKINGS.read_text(encoding="utf-8"))
    eligible_sources = {
        str(row["id"])
        for row in ranking["boards"]
        if row["game"] == "conexiuni" and row["pilot_eligible"] is True
    }
    indexed: dict[str, dict] = {}
    parsed: list[DerivedBoard] = []
    for row in rows:
        if not isinstance(row, dict) or set(row) != _BOARD_FIELDS:
            raise ValueError("derived catalog: board schema drift")
        item_id = row.get("id")
        game = row.get("game")
        source_id = row.get("source_id")
        if not isinstance(item_id, str) or not item_id or item_id in indexed:
            raise ValueError("derived catalog: duplicate/invalid board id")
        if (
            not isinstance(game, str)
            or not isinstance(source_id, str)
            or game not in DERIVED_GAMES
            or source_id not in eligible_sources
        ):
            raise ValueError(f"derived catalog: invalid game/source for {item_id}")
        source = sources[source_id]
        if (
            row.get("category") != source["category"]
            or row.get("difficulty") != source["difficulty"]
        ):
            raise ValueError(f"derived catalog: source metadata drift for {item_id}")
        if row["difficulty"] not in DIFFICULTIES:
            raise ValueError(f"derived catalog: invalid difficulty for {item_id}")
        familiarity = _require_score(row, "romanian_familiarity")
        quality = _require_score(row, "play_quality")
        standard = _require_score(row, "standard_score")
        starter = _require_score(row, "starter_score")
        if standard != (6 * familiarity + 4 * quality + 5) // 10:
            raise ValueError(f"derived catalog: standard formula drift for {item_id}")
        if starter != (75 * familiarity + 25 * quality + 50) // 100:
            raise ValueError(f"derived catalog: starter formula drift for {item_id}")
        eligible = row.get("starter_eligible")
        standard_rank = row.get("standard_rank")
        starter_rank = row.get("starter_rank")
        if not isinstance(eligible, bool):
            raise ValueError(f"derived catalog: invalid starter gate for {item_id}")
        if (
            isinstance(standard_rank, bool)
            or not isinstance(standard_rank, int)
            or standard_rank < 1
        ):
            raise ValueError(f"derived catalog: invalid standard rank for {item_id}")
        if eligible:
            if (
                isinstance(starter_rank, bool)
                or not isinstance(starter_rank, int)
                or starter_rank < 1
            ):
                raise ValueError(f"derived catalog: invalid starter rank for {item_id}")
        elif starter_rank is not None:
            raise ValueError(f"derived catalog: ineligible starter rank for {item_id}")
        _validate_payload(row, source)
        if item_id != _candidate_id(game, source_id, row["payload"]):
            raise ValueError(f"derived catalog: derived id drift for {item_id}")
        indexed[item_id] = row
        parsed.append(
            DerivedBoard(
                game=game,
                category=row["category"],
                difficulty=row["difficulty"],
                payload=row["payload"],
                _catalog_id=item_id,
                _source_id=source_id,
                _romanian_familiarity=familiarity,
                _play_quality=quality,
                _standard_score=standard,
                _starter_score=starter,
                _starter_eligible=eligible,
                _standard_rank=standard_rank,
                _starter_rank=starter_rank,
            )
        )

    expected_counts = {
        "total": len(rows),
        "by_game": {game: sum(row["game"] == game for row in rows) for game in DERIVED_GAMES},
        "sources_by_game": {
            game: len({row["source_id"] for row in rows if row["game"] == game})
            for game in DERIVED_GAMES
        },
        "starter_by_game": {
            game: sum(row["game"] == game and row["starter_eligible"] for row in rows)
            for game in DERIVED_GAMES
        },
    }
    if counts != expected_counts:
        raise ValueError("derived catalog: counts drift")
    for game in DERIVED_GAMES:
        game_rows = [row for row in rows if row["game"] == game]
        standard_order = sorted(game_rows, key=lambda row: (-row["standard_score"], row["id"]))
        if [row["standard_rank"] for row in standard_order] != list(
            range(1, len(standard_order) + 1)
        ):
            raise ValueError(f"derived catalog: {game} standard rank drift")
        starter_order = sorted(
            (row for row in game_rows if row["starter_eligible"]),
            key=lambda row: (-row["starter_score"], row["id"]),
        )
        if [row["starter_rank"] for row in starter_order] != list(
            range(1, len(starter_order) + 1)
        ):
            raise ValueError(f"derived catalog: {game} starter rank drift")
        per_source: dict[str, int] = {}
        for row in game_rows:
            per_source[row["source_id"]] = per_source.get(row["source_id"], 0) + 1
        if any(count > MAX_VARIANTS_PER_SOURCE for count in per_source.values()):
            raise ValueError(f"derived catalog: {game} source cap drift")
    return DerivedCatalog(parsed)


@lru_cache(maxsize=1)
def get_derived_catalog() -> DerivedCatalog:
    return load_derived_catalog()
