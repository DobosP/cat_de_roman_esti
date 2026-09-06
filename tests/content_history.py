"""Reverse only V80's allowed delta when checking earlier content-wave history."""

from __future__ import annotations

import json
from collections import Counter
from copy import deepcopy
from pathlib import Path

_RECEIPT = Path(__file__).resolve().parents[1] / (
    "docs/reviews/v80-clatite-target/artifact-delta.json"
)


def before_v80_pack(current: dict) -> dict:
    receipt = json.loads(_RECEIPT.read_bytes())
    restored = deepcopy(current)
    restored["contexto"] = [
        row for row in restored["contexto"] if row["id"] not in receipt["new_ids"]
    ]
    restored["meta"] = receipt["baseline_pack_meta"]
    return restored


def before_v80_rankings(current: dict) -> dict:
    receipt = json.loads(_RECEIPT.read_bytes())
    restored = deepcopy(current)
    restored["boards"] = [
        row for row in restored["boards"] if row["id"] not in receipt["new_ids"]
    ]
    ranks: Counter[str] = Counter()
    for row in restored["boards"]:
        ranks[row["game"]] += 1
        row["rank"] = ranks[row["game"]]
        change = receipt["selection_weight_changes"].get(row["id"])
        if change is not None:
            before, after = change
            assert row["selection_weight"] == after
            row["selection_weight"] = before
    restored["meta"] = receipt["baseline_ranking_meta"]
    return restored


def before_v80_derived(current: dict) -> dict:
    restored = deepcopy(current)
    restored["meta"] = json.loads(_RECEIPT.read_bytes())["baseline_derived_meta"]
    return restored
