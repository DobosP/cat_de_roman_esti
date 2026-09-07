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
_V83_REVIEW = Path(__file__).resolve().parents[1] / "docs/reviews/v83-food-input-and-feedback"
_V84_RECEIPT = Path(__file__).resolve().parents[1] / (
    "docs/reviews/v84-six-game-graph-quality/artifact-delta.json"
)
_V85_RECEIPT = Path(__file__).resolve().parents[1] / (
    "docs/reviews/v85-ingredient-feedback-and-board-clarity/artifact-delta.json"
)


def _reverse_reviewed_delta(current: dict, filename: str, receipt_path: Path) -> dict:
    """Peel only exact reviewed additions/corrections before checking old wave pins."""
    receipt = json.loads(receipt_path.read_bytes())["files"][filename]
    restored = deepcopy(current)
    head = {key: value for key, value in restored.items() if not isinstance(value, list)}
    assert head == receipt["head_after"]
    for table, changes in receipt["tables"].items():
        rows = restored[table]
        assert isinstance(rows, list)
        for added in changes["added"]:
            assert rows.count(added) == 1
            rows.remove(added)
        by_id = {row["id"]: row for row in rows}
        assert len(by_id) == len(rows)
        for row_id, change in changes["changed"].items():
            assert by_id[row_id] == change["after"]
            by_id[row_id] = change["before"]
        rows = [by_id[row["id"]] for row in rows]
        for removal in sorted(changes["removed"], key=lambda record: record["index"]):
            row = removal["row"]
            assert row["id"] not in by_id
            assert 0 <= removal["index"] <= len(rows)
            rows.insert(removal["index"], row)
            by_id[row["id"]] = row
        if (order := changes["baseline_order"]) is not None:
            assert len(order) == len(set(order)) == len(rows)
            assert set(order) == set(by_id)
            rows = [by_id[row_id] for row_id in order]
        restored[table] = rows
    for key in head:
        if key not in receipt["head_before"]:
            del restored[key]
    restored.update(receipt["head_before"])
    return restored


def before_v85_fixture(current: dict) -> dict:
    return _reverse_reviewed_delta(current, "kg_sample.json", _V85_RECEIPT)


def before_v85_pack(current: dict) -> dict:
    return _reverse_reviewed_delta(current, "games_pack.json", _V85_RECEIPT)


def before_v85_rankings(current: dict) -> dict:
    return _reverse_reviewed_delta(current, "board_rankings_v37.json", _V85_RECEIPT)


def before_v85_derived(current: dict) -> dict:
    return _reverse_reviewed_delta(current, "derived_catalog_v38.json", _V85_RECEIPT)


def _before_v84(current: dict, filename: str) -> dict:
    previous = _reverse_reviewed_delta(current, filename, _V85_RECEIPT)
    return _reverse_reviewed_delta(previous, filename, _V84_RECEIPT)


def before_v84_fixture(current: dict) -> dict:
    return _before_v84(current, "kg_sample.json")


def before_v84_pack(current: dict) -> dict:
    return _before_v84(current, "games_pack.json")


def before_v84_rankings(current: dict) -> dict:
    return _before_v84(current, "board_rankings_v37.json")


def before_v84_derived(current: dict) -> dict:
    return _before_v84(current, "derived_catalog_v38.json")


def before_v84_projection_rows(current: list[tuple]) -> list[tuple]:
    """Restore the exact retired Drojdie row from the committed V83 module."""
    restored = before_v85_projection_rows(current)
    assert not any(row[0] == "drojdie" for row in restored)
    index = next(i for i, row in enumerate(restored) if row[0] == "gem")
    restored.insert(index, (
        "drojdie", "n_v4gas_mancare", "ingrediente", 1, "domain_fallback",
        "ctxp_3218ea40b036e40101f5",
    ))
    return restored


def before_v85_projection_rows(current: list[tuple]) -> list[tuple]:
    """Restore only V85's two native replacements to their exact V84 positions."""
    restored = list(current)
    for index, successor, row in (
        (29, "piper", (
            "scorțișoară", "n_v4gas_mancare", "ingrediente", 1, "domain_fallback",
            "ctxp_ed454bb254e529d7508c",
        )),
        (38, "cappuccino", (
            "cacao", "n_v3gas_cafea", "băuturi", 1, "explicit",
            "ctxp_73226150ba2fe847d20e",
        )),
    ):
        assert not any(existing[0] == row[0] for existing in restored)
        assert restored[index][0] == successor
        restored.insert(index, row)
    return restored


def v83_added_forms() -> set[str]:
    receipt = json.loads((_V83_REVIEW / "morphology-delta.json").read_bytes())
    return {
        form for change in receipt["alias_changes"].values()
        for form in change["after"] if form not in change["before"]
    }


def before_v83_fixture(current: dict) -> dict:
    receipt = json.loads((_V83_REVIEW / "morphology-delta.json").read_bytes())
    restored = before_v84_fixture(current)
    assert restored["meta"] == receipt["after_kg_meta"]
    for row in restored["kg_nodes"]:
        change = receipt["alias_changes"].get(row["id"])
        if change is not None:
            assert row["aliases"] == change["after"]
            row["aliases"] = change["before"]
    restored["meta"] = receipt["baseline_kg_meta"]
    return restored


def before_v83_pack(current: dict) -> dict:
    receipt = json.loads((_V83_REVIEW / "artifact-delta.json").read_bytes())
    restored = before_v84_pack(current)
    assert restored["meta"] == receipt["after_pack_meta"]
    for row in receipt["new_records"]:
        assert row in restored["contexto"]
        restored["contexto"].remove(row)
    restored["meta"] = receipt["baseline_pack_meta"]
    return restored


def before_v83_rankings(current: dict) -> dict:
    receipt = json.loads((_V83_REVIEW / "artifact-delta.json").read_bytes())
    restored = before_v84_rankings(current)
    assert restored["meta"] == receipt["after_rankings_meta"]
    added = {row["id"] for row in receipt["new_records"]}
    assert added <= {row["id"] for row in restored["boards"]}
    restored["boards"] = [row for row in restored["boards"] if row["id"] not in added]
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


def before_v83_derived(current: dict) -> dict:
    receipt = json.loads((_V83_REVIEW / "artifact-delta.json").read_bytes())
    restored = before_v84_derived(current)
    assert restored["meta"] == receipt["after_derived_meta"]
    restored["meta"] = receipt["baseline_derived_meta"]
    return restored


def before_v82_pack(current: dict) -> dict:
    receipt = json.loads(_V82_RECEIPT.read_bytes())
    restored = before_v83_pack(current)
    assert restored["meta"] == receipt["after_pack_meta"]
    for row in receipt["new_records"]:
        assert row in restored["contexto"]
        restored["contexto"].remove(row)
    restored["meta"] = receipt["baseline_pack_meta"]
    return restored


def before_v82_rankings(current: dict) -> dict:
    receipt = json.loads(_V82_RECEIPT.read_bytes())
    restored = before_v83_rankings(current)
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
    restored = before_v83_derived(current)
    assert restored["meta"] == receipt["after_derived_meta"]
    restored["meta"] = receipt["baseline_derived_meta"]
    return restored


def before_v81_fixture(current: dict) -> dict:
    receipt = json.loads(_V81_RECEIPT.read_bytes())
    restored = before_v83_fixture(current)
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

    restored = before_v84_projection_rows(current)
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
