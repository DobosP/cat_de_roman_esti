"""Select bounded public fixtures for named-round journeys as content pools grow."""

from __future__ import annotations

import random


def contexto_seed(target: str, *, difficulty: str, category: str = "gastronomie") -> int:
    """Find a current public seed; actual journey tests still exercise the real API.

    Historical seed/date receipts are separate evidence. This helper never injects a
    target into the API or skips a journey if the target is no longer selectable.
    """
    from cat_de_roman_esti.wordgames.packs import get_pack

    pack = get_pack()
    for seed in range(1000):
        item = pack.pick_seeded(
            "contexto", random.Random(seed), category=category, difficulty=difficulty,
            filtered_shelf_weights=True,
        )
        if item is not None and item.payload["target"] == target:
            return seed
    raise AssertionError(f"No public seed found for selectable target {target!r}")
