"""Digest-bound V1 reservations; archived records remain unchanged."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

RESERVE_PATH = Path(__file__).resolve().parent.parent / "fixtures/release_reserve_v1.json"
MANIFEST_SHA256 = "fd522b637ab87681d0e890ffb38de44fc57480bf37c302746a328d71a9219fb7"
MAX_MANIFEST_BYTES = 64 * 1024
PACK_GAMES = frozenset({"conexiuni", "contexto", "lant", "alchimie"})
QUICK_GAMES = frozenset({"intrusul", "perechi"})


def record_digest(value: object) -> str:
    return hashlib.sha256(json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")).hexdigest()


def _plain(value: object) -> object:
    if isinstance(value, Mapping):
        return {key: _plain(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [_plain(item) for item in value]
    return value


def quick_definition(record: Mapping) -> dict:
    """Bind gameplay identity, not mutable ranking estimates or other variants."""
    return {key: _plain(record[key]) for key in (
        "id", "game", "source_id", "category", "difficulty", "payload",
    )}


@dataclass(frozen=True)
class ReleaseReserve:
    pack: tuple[tuple[str, str, str], ...]
    quick: tuple[tuple[str, str], ...]

    @property
    def pack_ids(self) -> frozenset[str]:
        return frozenset(row[0] for row in self.pack)


def _require(test: bool, message: str) -> None:
    if not test:
        raise ValueError("release reserve: " + message)


def _sha(value: object) -> bool:
    return (isinstance(value, str) and len(value) == 64
            and all(c in "0123456789abcdef" for c in value))


def load_reserve(path: Path = RESERVE_PATH) -> ReleaseReserve:
    """Bounded, fail-closed loading also works in a wheel without review docs."""
    try:
        _require(path.stat().st_size <= MAX_MANIFEST_BYTES, "manifest too large")
        blob = path.read_bytes().replace(b"\r\n", b"\n")
        _require(hashlib.sha256(blob).hexdigest() == MANIFEST_SHA256, "digest drift")
        data = json.loads(blob)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("release reserve: unreadable manifest") from exc
    _require(isinstance(data, dict) and set(data) == {"meta", "ids", "pack", "quick"},
             "schema")
    meta = data["meta"]
    _require(isinstance(meta, dict) and meta.get("kind") == "v1-release-reserve-v1",
             "metadata")
    _require(meta.get("count") == 20 and meta.get("quick_count") == 3, "counts")
    _require(isinstance(meta.get("reviewer"), str)
             and meta["reviewer"].strip()
             and meta["reviewer"].strip().casefold() != str(meta.get("author")).casefold(),
             "reviewer independence")
    _require(all(_sha(meta.get(key)) for key in (
        "proposal_sha256", "alchimie_proposal_sha256", "quality_review_sha256",
    )), "review bindings")
    pack, quick = data["pack"], data["quick"]
    _require(isinstance(pack, list) and len(pack) == 20
             and isinstance(quick, list) and len(quick) == 3, "rows")
    _require(all(isinstance(r, dict) and set(r) == {"id", "game", "record_sha256"}
                 and isinstance(r["id"], str) and r["game"] in PACK_GAMES
                 and _sha(r["record_sha256"]) for r in pack), "pack rows")
    _require(all(isinstance(r, dict) and set(r) == {
        "id", "game", "source_id", "record_sha256", "definition_sha256",
    } and isinstance(r["id"], str) and r["game"] in QUICK_GAMES
                 and isinstance(r["source_id"], str)
                 and _sha(r["record_sha256"]) and _sha(r["definition_sha256"])
                 for r in quick), "quick rows")
    ids = [r["id"] for r in pack]
    quick_ids = [r["id"] for r in quick]
    _require(ids == sorted(set(ids)) and data["ids"] == ids, "pack identity/count drift")
    _require(quick_ids == sorted(set(quick_ids)) and not set(ids) & set(quick_ids),
             "quick identity/count drift")
    return ReleaseReserve(
        tuple((r["id"], r["game"], r["record_sha256"]) for r in pack),
        tuple((r["id"], r["definition_sha256"]) for r in quick),
    )


@lru_cache(maxsize=1)
def get_reserve() -> ReleaseReserve:
    return load_reserve()


def validate_pack_reserve(pack: dict) -> frozenset[str]:
    """Ranking rebuilds must recheck every archived record before applying a hold."""
    reserve = load_reserve()
    for item_id, game, expected in reserve.pack:
        matches = [r for r in pack.get(game, []) if r.get("id") == item_id]
        _require(len(matches) == 1 and record_digest(matches[0]) == expected,
                 f"reviewed pack record drift: {item_id}")
    return reserve.pack_ids


def quick_is_reserved(board) -> bool:
    """A custom board reusing only an ID is not the reviewed archived definition."""
    expected = next((sha for item_id, sha in get_reserve().quick
                     if item_id == board._catalog_id), None)
    if expected is None:
        return False
    definition = quick_definition({
        "id": board._catalog_id, "game": board.game, "source_id": board._source_id,
        "category": board.category, "difficulty": board.difficulty, "payload": board.payload,
    })
    return record_digest(definition) == expected
