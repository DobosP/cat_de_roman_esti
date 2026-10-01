"""Regenerate independent CPython reference vectors, from the repository root.

PYTHONPATH=. <repo-venv>/bin/python go-backend/internal/catalog/testdata/generate_vectors.py
This reads the canonical Python selector; it does not reimplement it.
"""

from __future__ import annotations

import hashlib
import json
import random
import sys
from pathlib import Path

from cat_de_roman_esti.wordgames.derived_catalog import (
    DerivedBoard,
    DerivedCatalog,
    get_derived_catalog,
)

HERE = Path(__file__).resolve().parent
RNG_DATA = HERE.parent.parent / "pyrandom" / "testdata"
RNG_DATA.mkdir(parents=True, exist_ok=True)
sys.set_int_max_str_digits(10000)


def write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def rng_vectors() -> None:
    vectors = []
    for seed in [0, 1, -1, 42, 2**64 + 12345, -(2**200 + 123456789), 2**2500 + 47, 2**21000 + 89]:
        rng = random.Random(seed)
        outputs = [rng.getrandbits(32) for _ in range(1250)]
        widths = [0, 1, 5, 31, 32, 33, 63, 64, 65, 127, 256]
        rng = random.Random(seed)
        bit_values = [str(rng.getrandbits(k)) for k in widths]
        ranges = [1, 2, 3, 4, 5, 7, 16, 17, 256, 1000, 2**40 + 9, 2**62]
        rng = random.Random(seed)
        below = [rng.randrange(n) for n in ranges]
        rng = random.Random(seed)
        order = list(range(20))
        rng.shuffle(order)
        vectors.append(
            {
                "seed": str(seed),
                "outputs": [
                    {"index": i, "value": outputs[i]}
                    for i in [0, 1, 2, 3, 4, 10, 623, 624, 625, 626, 1247, 1248, 1249]
                ],
                "bits": widths,
                "bit_values": bit_values,
                "ranges": ranges,
                "below": below,
                "shuffle": order,
            }
        )
    write(
        RNG_DATA / "python_random.json",
        {
            "source": "CPython random.Random integer seed / getrandbits / randrange / shuffle",
            "vectors": vectors,
        },
    )


def board(
    item_id, source, category, overall, starter_score, starter, difficulty="normal", game="intrusul"
):
    return DerivedBoard(
        game=game,
        category=category,
        difficulty=difficulty,
        payload={},
        _catalog_id=item_id,
        _source_id=source,
        _romanian_familiarity=overall,
        _play_quality=overall,
        _standard_score=overall,
        _starter_score=starter_score,
        _starter_eligible=starter,
        _standard_rank=1,
        _starter_rank=1 if starter else None,
    )


def selector_vectors() -> None:
    synthetic = [
        board("a1", "a", "istorie", 54, 95, True, "usor"),
        board("a2", "a", "istorie", 55, 85, True),
        board("a3", "a", "istorie", 85, 15, True),
        board("b1", "b", "muzica", 65, 75, True),
        board("b2", "b", "muzica", 75, 65, False),
        board("c1", "c", "muzica", 95, 35, False),
        board("d1", "d", "stiinta", 40, 90, True),
        board("e1", "e", "stiinta", 45, 30, True),
        board("f1", "f", "istorie", 100, 10, False, "greu"),
        board("g1", "g", "gastronomie", 53, 53, True),
        board("h1", "h", "știință", 65, 66, True),
        board("p1", "p", "istorie", 99, 99, True, game="perechi"),
    ]
    write(
        HERE / "synthetic_boards.json",
        [
            {
                "game": b.game,
                "catalog_id": b._catalog_id,
                "source_id": b._source_id,
                "category": b.category,
                "difficulty": b.difficulty,
                "overall_score": b._standard_score,
                "starter_score": b._starter_score,
                "starter_safe": b._starter_eligible,
            }
            for b in synthetic
        ],
    )
    bundled = get_derived_catalog()
    options = [
        {},
        {"starter": True},
        {"balance_categories": True},
        {"starter": True, "balance_categories": True},
        {"category": "istorie"},
        {"category": "muzica", "starter": True},
        {"category": "stiinta"},
        {"category": "gastronomie"},
        {"category": "necunoscuta"},
        {"difficulty": "greu"},
        {"difficulty": "usor"},
        {"difficulty": "invalid"},
        {"exclude_source_ids": {"a", "b", "c"}},
        {"category": "istorie", "exclude_source_ids": {"a", "f"}},
        {"category": "istorie", "starter": True, "exclude_source_ids": {"a"}},
        {"category": "știință", "balance_categories": True},
    ]
    seeded, daily = [], []
    for inventory, catalog in [("synthetic", DerivedCatalog(synthetic)), ("bundled", bundled)]:
        opts = list(options)
        if inventory == "bundled":
            sources = sorted({b._source_id for b in catalog.pool("intrusul")})
            opts += [
                {
                    "exclude_source_ids": set(sources[:40]),
                    "starter": True,
                    "balance_categories": True,
                }
            ]
            opts += [
                {"category": c} for c in sorted({b.category for b in catalog.pool("intrusul")})
            ]
        for settings in opts:
            normalized = {k: sorted(v) if isinstance(v, set) else v for k, v in settings.items()}
            for seed in list(range(24)) + [-42, 2**64 + 12345, -(2**200 + 123456789)]:
                rng = random.Random(seed)
                selected = catalog.pick_seeded("intrusul", rng, **settings)
                seeded.append(
                    {
                        "inventory": inventory,
                        "seed": str(seed),
                        "options": normalized,
                        "id": selected._catalog_id if selected else "",
                        "next_bits": str(rng.getrandbits(64)),
                    }
                )
            daily_settings = {k: v for k, v in settings.items() if k in {"category", "difficulty"}}
            for day in ["2026-10-01", "2026-10-02", "2026-12-31", "2027-01-01", "arbitrary-șț-key"]:
                selected = catalog.pick_daily("intrusul", day, **daily_settings)
                daily.append(
                    {
                        "inventory": inventory,
                        "day": day,
                        "options": normalized,
                        "id": selected._catalog_id if selected else "",
                    }
                )
    write(
        HERE / "python_selector.json",
        {"source": "Canonical derived_catalog.DerivedCatalog", "seeded": seeded, "daily": daily},
    )


if __name__ == "__main__":
    rng_vectors()
    inputs = [
        "",
        "abc",
        "2026-10-01:intrusul",
        "șțîâă",
        *("a" * n for n in [127, 128, 129, 256, 1025]),
    ]
    write(
        HERE / "blake2b8.json",
        [
            {"input": value, "digest": hashlib.blake2b(value.encode(), digest_size=8).hexdigest()}
            for value in inputs
        ],
    )
    selector_vectors()
