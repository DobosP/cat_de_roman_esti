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
_V86_RECEIPT = Path(__file__).resolve().parents[1] / (
    "docs/reviews/v86-preparation-and-route-quality/artifact-delta.json"
)
_V87_RECEIPT = Path(__file__).resolve().parents[1] / (
    "docs/reviews/v87-snack-and-action-quality/artifact-delta.json"
)
_V88_RECEIPT = Path(__file__).resolve().parents[1] / (
    "docs/reviews/v88-cross-game-quality/artifact-delta.json"
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


def before_v88_fixture(current: dict) -> dict:
    return _reverse_reviewed_delta(current, "kg_sample.json", _V88_RECEIPT)


def before_v88_pack(current: dict) -> dict:
    return _reverse_reviewed_delta(current, "games_pack.json", _V88_RECEIPT)


def before_v88_rankings(current: dict) -> dict:
    return _reverse_reviewed_delta(current, "board_rankings_v37.json", _V88_RECEIPT)


def before_v88_derived(current: dict) -> dict:
    return _reverse_reviewed_delta(current, "derived_catalog_v38.json", _V88_RECEIPT)


def _before_v87(current: dict, filename: str) -> dict:
    previous = _reverse_reviewed_delta(current, filename, _V88_RECEIPT)
    return _reverse_reviewed_delta(previous, filename, _V87_RECEIPT)


def before_v87_fixture(current: dict) -> dict:
    return _before_v87(current, "kg_sample.json")


def before_v87_pack(current: dict) -> dict:
    return _before_v87(current, "games_pack.json")


def before_v87_rankings(current: dict) -> dict:
    return _before_v87(current, "board_rankings_v37.json")


def before_v87_derived(current: dict) -> dict:
    return _before_v87(current, "derived_catalog_v38.json")


def _before_v86(current: dict, filename: str) -> dict:
    previous = _before_v87(current, filename)
    return _reverse_reviewed_delta(previous, filename, _V86_RECEIPT)


def before_v86_fixture(current: dict) -> dict:
    return _before_v86(current, "kg_sample.json")


def before_v86_pack(current: dict) -> dict:
    return _before_v86(current, "games_pack.json")


def before_v86_rankings(current: dict) -> dict:
    return _before_v86(current, "board_rankings_v37.json")


def before_v86_derived(current: dict) -> dict:
    return _before_v86(current, "derived_catalog_v38.json")


def before_v85_fixture(current: dict) -> dict:
    return _before_v85(current, "kg_sample.json")


def before_v85_pack(current: dict) -> dict:
    return _before_v85(current, "games_pack.json")


def before_v85_rankings(current: dict) -> dict:
    return _before_v85(current, "board_rankings_v37.json")


def before_v85_derived(current: dict) -> dict:
    return _before_v85(current, "derived_catalog_v38.json")


def _before_v85(current: dict, filename: str) -> dict:
    previous = _before_v86(current, filename)
    return _reverse_reviewed_delta(previous, filename, _V85_RECEIPT)


def _before_v84(current: dict, filename: str) -> dict:
    previous = _before_v85(current, filename)
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
    restored = before_v86_projection_rows(current)
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


def before_v86_projection_rows(current: list[tuple]) -> list[tuple]:
    """Restore the exact Congelator projection retired by its V86 native concept."""
    restored = before_v87_projection_rows(current)
    assert not any(row[0] == "congelator" for row in restored)
    assert restored[86][0] == "hotă de bucătărie"
    restored.insert(86, (
        "congelator", "n_v24_home_appliances_frigider", "ustensile de bucătărie",
        0, "explicit", "ctxp_ab9722a1b626f7b1d9ca",
    ))
    return restored


def before_v87_projection_rows(current: list[tuple]) -> list[tuple]:
    """Remove the reviewed Tort cue and restore the two exact V86 pastry rows."""
    restored = before_v88_projection_rows(current)
    added = (
        "tort", "n_v4gas_prajitura", "mâncare gătită", 1, "explicit",
        "ctxp_7de7b40dd74b4b0f44bf",
    )
    assert restored.count(added) == 1
    restored.remove(added)
    for index, row in (
        (14, ("brioșă", "n_v4gas_paine", "mâncare gătită", 1, "explicit",
              "ctxp_48dbb31871219f323569")),
        (15, ("chec", "n_v4gas_paine", "mâncare gătită", 1, "explicit",
              "ctxp_2e50eafd1e160b7bc25a")),
    ):
        assert not any(existing[0] == row[0] for existing in restored)
        assert restored[index][0] == "chiflă"
        restored.insert(index, row)
    return restored


def before_v88_projection_rows(current: list[tuple]) -> list[tuple]:
    """Restore the two exact V87 household cues replaced by native V88 owners."""
    restored = list(current)
    for index, successor, row in (
        (59, "birou de acasă", (
            "taburet", "n_v4soc_casa", "mobilier și casă", 1, "domain_fallback",
            "ctxp_cd04babfc1ac9193f9cf",
        )),
        (106, "cârpă de praf", (
            "mătură", "n_v31_cleaning_floor_aspirator", "curățenie", 1, "explicit",
            "ctxp_14422411a52f6dbbfe68",
        )),
    ):
        assert not any(existing[0] == row[0] for existing in restored)
        assert restored[index][0] == successor
        restored.insert(index, row)
    return restored


def before_v88_feedback_pairs(current: frozenset[tuple[str, str]]) -> frozenset[tuple[str, str]]:
    """Peel only V88's independently reviewed native bread-family cue."""
    added = frozenset({("n_v87_food_briosa", "n_v4gas_paine")})
    assert added <= current
    return current - added


def before_v87_feedback_pairs(current: frozenset[tuple[str, str]]) -> frozenset[tuple[str, str]]:
    """Peel only the three reviewed V87 native exact-target additions."""
    current = before_v88_feedback_pairs(current)
    added = frozenset({
        ("n_v87_food_pandispan", "n_v87_food_chec"),
        ("n_v24_food_snack_biscuit", "n_v87_food_piscot"),
        ("n_v4gas_prajitura", "n_v87_food_cremsnit"),
    })
    assert added <= current
    return current - added


def before_v87_projection_neighborhoods(current: dict) -> dict:
    """Retain exact older policies while checking the two closed V87 cue policies."""
    restored = dict(current)
    for key, anchor, target in (
        ("tort", "n_v4gas_prajitura", "n_v87_food_tort_diplomat"),
        ("ciocolata calda", "n_v24_food_snack_ceai", "n_v85_food_ciocolata"),
    ):
        policy = restored.pop(key)
        assert (policy.anchor_id, policy.min_strength, policy.include_direct_neighbors,
                policy.exact_target_ids) == (anchor, 0.60, False, frozenset({target}))
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
