"""Reverse reviewed deltas when checking earlier content-wave history."""

from __future__ import annotations

import json
from collections import Counter
from copy import deepcopy
from pathlib import Path

_RECEIPT = Path(__file__).resolve().parents[1] / (
    "docs/reviews/v80-clatite-target/artifact-delta.json"
)
_V81_RECEIPT = Path(__file__).resolve().parents[1] / (
    "docs/reviews/v81-nuca-feedback/artifact-delta.json"
)
_V82_RECEIPT = Path(__file__).resolve().parents[1] / (
    "docs/reviews/v82-playable-content-batch/artifact-delta.json"
)


def before_v82_pack(current: dict) -> dict:
    receipt = json.loads(_V82_RECEIPT.read_bytes())
    restored = deepcopy(current)
    assert restored["meta"] == receipt["after_pack_meta"]
    for row in receipt["new_records"]:
        assert row in restored["contexto"]
        restored["contexto"].remove(row)
    restored["meta"] = receipt["baseline_pack_meta"]
    return restored


def before_v82_rankings(current: dict) -> dict:
    receipt = json.loads(_V82_RECEIPT.read_bytes())
    restored = deepcopy(current)
    assert restored["meta"] == receipt["after_rankings_meta"]
    new_ids = {row["id"] for row in receipt["new_records"]}
    assert new_ids <= {row["id"] for row in restored["boards"]}
    restored["boards"] = [row for row in restored["boards"] if row["id"] not in new_ids]
    ranks: Counter[str] = Counter()
    for row in restored["boards"]:
        ranks[row["game"]] += 1
        row["rank"] = ranks[row["game"]]
        change = receipt["selection_weight_changes"].get(row["id"])
        if change is not None:
            before, after = change
            assert row["selection_weight"] == after
            row["selection_weight"] = before
    restored["meta"] = receipt["baseline_rankings_meta"]
    return restored


def before_v82_derived(current: dict) -> dict:
    receipt = json.loads(_V82_RECEIPT.read_bytes())
    restored = deepcopy(current)
    assert restored["meta"] == receipt["after_derived_meta"]
    restored["meta"] = receipt["baseline_derived_meta"]
    return restored


def before_v81_fixture(current: dict) -> dict:
    receipt = json.loads(_V81_RECEIPT.read_bytes())
    restored = deepcopy(current)
    assert restored["meta"] == receipt["after_kg_meta"]
    new_node = receipt["new_node"]
    assert new_node in restored["kg_nodes"]
    nodes = []
    for row in restored["kg_nodes"]:
        if row["id"] == new_node["id"]:
            continue
        change = receipt["changed_nodes"].get(row["id"])
        if change:
            assert row == change["after"]
            row = change["before"]
        nodes.append(row)
    restored["kg_nodes"] = nodes
    for edge in receipt["new_edges"]:
        assert edge in restored["kg_edges"]
        restored["kg_edges"].remove(edge)
    for idx, row in enumerate(restored["kg_puzzles"]):
        change = receipt["changed_puzzles"].get(row["id"])
        if change:
            assert row == change["after"]
            restored["kg_puzzles"][idx] = change["before"]
    restored["meta"] = receipt["baseline_kg_meta"]
    return restored


def before_v81_rankings(current: dict) -> dict:
    receipt = json.loads(_V81_RECEIPT.read_bytes())
    restored = before_v82_rankings(current)
    assert restored["meta"] == receipt["after_rankings_meta"]
    rows = {row["id"]: row for row in restored["boards"]}
    assert len(rows) == len(restored["boards"])
    assert set(rows) == set(receipt["baseline_ranking_order"])
    for item_id, change in receipt["changed_ranking_rows"].items():
        assert rows[item_id] == change["after"]
        rows[item_id] = change["before"]
    restored["boards"] = [rows[item_id] for item_id in receipt["baseline_ranking_order"]]
    restored["meta"] = receipt["baseline_rankings_meta"]
    return restored


def before_v81_derived(current: dict) -> dict:
    receipt = json.loads(_V81_RECEIPT.read_bytes())
    restored = before_v82_derived(current)
    assert restored["meta"] == receipt["after_derived_meta"]
    restored["meta"] = receipt["baseline_derived_meta"]
    return restored


def before_v81_projection_rows(current: list[tuple]) -> list[tuple]:
    """Restore the one retired synthetic row for the V79 history fingerprint."""

    restored = list(current)
    assert not any(row[0] == "nucă" for row in restored)
    index = next(i for i, row in enumerate(restored) if row[0] == "alună")
    restored.insert(index, (
        "nucă", "n_v24_food_breakfast_miere", "ingrediente", 1, "explicit",
        "ctxp_92113401f76976ac37f7",
    ))
    return restored


def before_v80_pack(current: dict) -> dict:
    receipt = json.loads(_RECEIPT.read_bytes())
    restored = before_v82_pack(current)
    restored["contexto"] = [
        row for row in restored["contexto"] if row["id"] not in receipt["new_ids"]
    ]
    restored["meta"] = receipt["baseline_pack_meta"]
    return restored


def before_v80_rankings(current: dict) -> dict:
    receipt = json.loads(_RECEIPT.read_bytes())
    restored = before_v81_rankings(current)
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
    restored = before_v81_derived(current)
    restored["meta"] = json.loads(_RECEIPT.read_bytes())["baseline_derived_meta"]
    return restored
