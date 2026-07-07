"""Curated games pack — loading, selection and item validation (ADR-0011).

The pack (``fixtures/games_pack.json``) carries hand/AI-authored game instances
for the four word games, each tagged with a category from
:mod:`.categories`, a difficulty, a ``source`` (``user`` | ``ai`` | ``ai_corpus``)
and a review ``status``. Only ``approved`` items are ever served; ``pending`` /
``rejected`` items may sit in the file awaiting review but are invisible to
gameplay.

Selection is deterministic where it must be:

* daily picks use rendezvous hashing over item ids, so the day's instance is
  stable for everyone and mostly survives pack growth;
* seeded picks draw from the id-sorted pool via the caller's ``random.Random``.

This module is stdlib-only (no Django) so the offline validator script and the
review tooling can import the exact validation the server applies. A handful of
game constants (difficulty bands, quality floors) are mirrored here from the
game modules — ``tests/test_wordgames_curated.py`` asserts they never drift.
"""

from __future__ import annotations

import hashlib
import json
import os
import random
from dataclasses import dataclass
from functools import lru_cache
from itertools import combinations
from pathlib import Path

from .categories import is_known
from .service import WordGameService, get_service

PACK_DIR = Path(__file__).resolve().parent.parent / "fixtures"
DEFAULT_PACK = PACK_DIR / "games_pack.json"

GAME_KINDS = ("conexiuni", "contexto", "lant", "alchimie")
SOURCES = ("user", "ai", "ai_corpus")
STATUSES = ("approved", "pending", "rejected")
DIFFICULTIES = ("usor", "normal", "greu")

# Mirrored game constants (single-source tests guard the originals against drift).
LANT_BANDS = {"usor": (2, 3), "normal": (3, 4), "greu": (4, 6)}
CONTEXTO_MIN_REACHABLE = 120
CONTEXTO_MIN_RESPONSIVE = 40
CONTEXTO_RESPONSIVE_MAX_HOPS = 5
ALCHIMIE_MIN_OPENING_PAIRS = 2
ALCHIMIE_SEED_RANGE = (5, 7)
CONEXIUNI_GROUPS = 4
CONEXIUNI_GROUP_SIZE = 4

# The shared daily only draws from the curated pool once it is big enough to give
# day-to-day variety; below this floor a curated daily would repeat the same one
# or two instances every day, so the daily stays mined until content lands.
CURATED_DAILY_MIN_POOL = 8


# --------------------------------------------------------------------------- items
@dataclass(frozen=True)
class CuratedItem:
    """Common envelope of one curated game instance."""

    id: str
    game: str
    category: str
    difficulty: str
    source: str
    status: str
    payload: dict

    @property
    def approved(self) -> bool:
        return self.status == "approved"


_COMMON_FIELDS = {"id", "category", "difficulty", "source", "status"}
_PAYLOAD_FIELDS = {
    "conexiuni": {"groups", "group_labels", "order"},
    "contexto": {"target"},
    "lant": {"start", "target", "optimal"},
    "alchimie": {"seeds", "target", "target_depth"},
}


def item_fields(game: str) -> set[str]:
    return _COMMON_FIELDS | _PAYLOAD_FIELDS[game]


# --------------------------------------------------------------------- validation
def _closure_generations(svc: WordGameService, seeds: list[str]) -> dict[str, int]:
    """Combine-closure generation map (mirrors the Alchimie instance builder)."""
    gen: dict[str, int] = {s: 0 for s in seeds}
    owned = set(seeds)
    g = 0
    changed = True
    while changed:
        changed = False
        g += 1
        fresh: set[str] = set()
        for a, b in combinations(sorted(owned), 2):
            for c in svc.common_neighbors(a, b):
                if c not in owned and c not in fresh:
                    fresh.add(c)
                    gen.setdefault(c, g)
        if fresh:
            owned |= fresh
            changed = True
    return gen


def _opening_pairs(svc: WordGameService, seeds: list[str]) -> int:
    owned = set(seeds)
    count = 0
    for a, b in combinations(sorted(owned), 2):
        if any(c not in owned for c in svc.common_neighbors(a, b)):
            count += 1
    return count


def validate_envelope(rec: dict, game: str) -> list[str]:
    """Field-shape + enum errors for one raw item record (no graph access)."""
    errors: list[str] = []
    expected = item_fields(game)
    got = set(rec)
    missing = expected - got
    extra = got - expected
    if missing:
        errors.append(f"missing fields: {sorted(missing)}")
    if extra:
        errors.append(f"unexpected fields: {sorted(extra)}")
    if not isinstance(rec.get("id"), str) or not rec.get("id"):
        errors.append("id must be a non-empty string")
    if rec.get("category") is not None and not is_known(str(rec.get("category"))):
        errors.append(f"unknown category: {rec.get('category')!r}")
    if rec.get("difficulty") not in DIFFICULTIES:
        errors.append(f"difficulty must be one of {DIFFICULTIES}")
    if rec.get("source") not in SOURCES:
        errors.append(f"source must be one of {SOURCES}")
    if rec.get("status") not in STATUSES:
        errors.append(f"status must be one of {STATUSES}")
    return errors


def validate_payload(rec: dict, game: str, svc: WordGameService) -> list[str]:
    """Game-rule errors for one raw item record (playability against the KG)."""
    if game == "conexiuni":
        return _validate_conexiuni(rec, svc)
    if game == "contexto":
        return _validate_contexto(rec, svc)
    if game == "lant":
        return _validate_lant(rec, svc)
    if game == "alchimie":
        return _validate_alchimie(rec, svc)
    return [f"unknown game kind: {game!r}"]


def _validate_conexiuni(rec: dict, svc: WordGameService) -> list[str]:
    errors: list[str] = []
    groups = rec.get("groups")
    labels = rec.get("group_labels")
    order = rec.get("order")
    if not isinstance(groups, dict) or len(groups) != CONEXIUNI_GROUPS:
        return [f"groups must be a dict of exactly {CONEXIUNI_GROUPS} keys"]
    if not isinstance(labels, dict) or set(labels) != set(groups):
        errors.append("group_labels keys must match groups keys exactly")
    elif any(not isinstance(v, str) or not v.strip() for v in labels.values()):
        errors.append("every group label must be a non-empty string")
    tiles: list[str] = []
    for key, ids in groups.items():
        if not isinstance(ids, list) or len(ids) != CONEXIUNI_GROUP_SIZE:
            errors.append(f"group {key!r} must list exactly {CONEXIUNI_GROUP_SIZE} tiles")
            continue
        tiles.extend(str(i) for i in ids)
    if len(set(tiles)) != len(tiles):
        errors.append("boards must not repeat a tile")
    for nid in tiles:
        if not svc.exists(nid):
            errors.append(f"unknown node id: {nid}")
    if not isinstance(order, list) or sorted(map(str, order)) != sorted(tiles):
        errors.append("order must be a permutation of the 16 group tiles")
    return errors


def _validate_contexto(rec: dict, svc: WordGameService) -> list[str]:
    target = str(rec.get("target") or "")
    if not svc.exists(target):
        return [f"unknown target node id: {target}"]
    dist = svc.distances_from(target)
    responsive = sum(
        1 for d in dist.values() if 1 <= d <= CONTEXTO_RESPONSIVE_MAX_HOPS
    )
    errors: list[str] = []
    if len(dist) < CONTEXTO_MIN_REACHABLE:
        errors.append(
            f"target reaches only {len(dist)} nodes (< {CONTEXTO_MIN_REACHABLE})"
        )
    if responsive < CONTEXTO_MIN_RESPONSIVE:
        errors.append(
            f"target has a responsive zone of {responsive} (< {CONTEXTO_MIN_RESPONSIVE})"
        )
    return errors


def _validate_lant(rec: dict, svc: WordGameService) -> list[str]:
    start = str(rec.get("start") or "")
    target = str(rec.get("target") or "")
    optimal = rec.get("optimal")
    errors: list[str] = []
    for nid in (start, target):
        if not svc.exists(nid):
            errors.append(f"unknown node id: {nid}")
    if errors:
        return errors
    if start == target:
        return ["start and target must differ"]
    actual = svc.distance(start, target)
    if actual is None:
        return ["target is unreachable from start on the non-distractor graph"]
    if not isinstance(optimal, int) or optimal != actual:
        errors.append(f"optimal must equal the real BFS distance ({actual})")
    lo, hi = LANT_BANDS[str(rec.get("difficulty"))]
    if not lo <= actual <= hi:
        errors.append(
            f"distance {actual} outside the {rec.get('difficulty')} band [{lo},{hi}]"
        )
    return errors


def _validate_alchimie(rec: dict, svc: WordGameService) -> list[str]:
    seeds = [str(s) for s in rec.get("seeds") or []]
    target = str(rec.get("target") or "")
    depth = rec.get("target_depth")
    errors: list[str] = []
    lo, hi = ALCHIMIE_SEED_RANGE
    if not lo <= len(seeds) <= hi or len(set(seeds)) != len(seeds):
        errors.append(f"seeds must be {lo}-{hi} distinct node ids")
    for nid in [*seeds, target]:
        if not svc.exists(nid):
            errors.append(f"unknown node id: {nid}")
    if errors:
        return errors
    if target in seeds:
        return ["target must not be a seed"]
    gen = _closure_generations(svc, seeds)
    actual = gen.get(target)
    if actual is None:
        return ["target is not craftable from the seeds"]
    if not isinstance(depth, int) or depth != actual:
        errors.append(f"target_depth must equal the closure depth ({actual})")
    if _opening_pairs(svc, seeds) < ALCHIMIE_MIN_OPENING_PAIRS:
        errors.append(
            f"seed set offers fewer than {ALCHIMIE_MIN_OPENING_PAIRS} opening pairs"
        )
    return errors


# --------------------------------------------------------------------------- pack
class GamesPack:
    """All approved curated instances, indexed for deterministic selection."""

    def __init__(self, items: list[CuratedItem]):
        self._items: dict[str, list[CuratedItem]] = {g: [] for g in GAME_KINDS}
        for item in items:
            if item.approved:
                self._items[item.game].append(item)
        for pool in self._items.values():
            pool.sort(key=lambda i: i.id)

    def pool(
        self,
        game: str,
        *,
        category: str | None = None,
        difficulty: str | None = None,
    ) -> list[CuratedItem]:
        out = self._items.get(game, [])
        if category is not None:
            out = [i for i in out if i.category == category]
        if difficulty is not None:
            out = [i for i in out if i.difficulty == difficulty]
        return out

    def counts(self, *, category: str | None = None) -> dict[str, int]:
        return {g: len(self.pool(g, category=category)) for g in GAME_KINDS}

    def pick_seeded(
        self,
        game: str,
        rng: random.Random,
        *,
        category: str | None = None,
        difficulty: str | None = None,
    ) -> CuratedItem | None:
        pool = self.pool(game, category=category, difficulty=difficulty)
        return rng.choice(pool) if pool else None

    def pick_daily(
        self,
        game: str,
        daily: str,
        *,
        category: str | None = None,
        difficulty: str | None = None,
        min_pool: int | None = None,
    ) -> CuratedItem | None:
        """Rendezvous-hash pick: stable per (day, filters) and mostly insensitive
        to pack growth — adding items only re-rolls the day when the new item
        wins the hash, and removing items only affects days they had won.

        The shared (category-less) daily returns None below
        ``CURATED_DAILY_MIN_POOL`` so a thin pool cannot repeat the same instance
        every day; an explicit category request has no floor — the player asked
        for that shelf."""
        if min_pool is None:
            min_pool = 1 if category is not None else CURATED_DAILY_MIN_POOL
        pool = self.pool(game, category=category, difficulty=difficulty)
        if len(pool) < max(1, min_pool):
            return None

        def _weight(item: CuratedItem) -> bytes:
            key = f"{daily}:{game}:{category or ''}:{difficulty or ''}:{item.id}"
            return hashlib.blake2b(key.encode(), digest_size=8).digest()

        return min(pool, key=_weight)


def _parse_items(raw: dict) -> list[CuratedItem]:
    items: list[CuratedItem] = []
    for game in GAME_KINDS:
        for rec in raw.get(game, []) or []:
            if not isinstance(rec, dict):
                raise ValueError(f"games pack: non-object record under {game!r}")
            errors = validate_envelope(rec, game)
            if errors:
                raise ValueError(f"games pack: invalid {game} item {rec.get('id')!r}: {errors}")
            payload = {k: rec[k] for k in _PAYLOAD_FIELDS[game]}
            items.append(
                CuratedItem(
                    id=str(rec["id"]),
                    game=game,
                    category=str(rec["category"]),
                    difficulty=str(rec["difficulty"]),
                    source=str(rec["source"]),
                    status=str(rec["status"]),
                    payload=payload,
                )
            )
    return items


def _resolve_pack(path: str | Path | None) -> Path:
    """Pack path: explicit arg > ``CAT_GAMES_PACK`` env > bundled default."""
    return Path(path or os.environ.get("CAT_GAMES_PACK") or DEFAULT_PACK)


def load_pack(path: str | Path | None = None) -> GamesPack:
    """Parse the pack, envelope-validating every record (fail fast on a broken file).

    Deep playability validation lives in ``scripts/validate_games_pack.py`` (a CI
    gate); at runtime we trust a shipped pack the same way the KG fixture is
    trusted, but refuse to load one whose shape is wrong.
    """
    fpath = _resolve_pack(path)
    raw = json.loads(fpath.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("games pack: top level must be an object")
    return GamesPack(_parse_items(raw))


def _item_node_ids(item: CuratedItem) -> list[str]:
    p = item.payload
    if item.game == "conexiuni":
        return [str(nid) for ids in p["groups"].values() for nid in ids]
    if item.game == "contexto":
        return [str(p["target"])]
    if item.game == "lant":
        return [str(p["start"]), str(p["target"])]
    return [*(str(s) for s in p["seeds"]), str(p["target"])]


def resolvable_items(items: list[CuratedItem], svc: WordGameService) -> list[CuratedItem]:
    """Drop items referencing nodes absent from the LOADED graph.

    The bundled pack is validated against the bundled ``kg_sample.json``, but a
    deployment may swap the graph via ``CAT_KG_FIXTURE`` (e.g. ``kg_real.json``)
    — curated instances that no longer resolve must vanish rather than serve
    boards with phantom tiles or unreachable targets."""
    return [i for i in items if all(svc.exists(nid) for nid in _item_node_ids(i))]


@lru_cache(maxsize=1)
def get_pack() -> GamesPack:
    """The process-wide curated pack (loaded once, pruned to the loaded graph)."""
    pack = load_pack()
    svc = get_service()
    items = [i for pool in pack._items.values() for i in pool]
    return GamesPack(resolvable_items(items, svc))


def validate_pack_item(rec: dict, game: str) -> list[str]:
    """Full validation of one raw item (envelope + playability) — the exact check
    the submissions endpoint and the offline validator share."""
    errors = validate_envelope(rec, game)
    if errors:
        return errors
    return validate_payload(rec, game, get_service())
