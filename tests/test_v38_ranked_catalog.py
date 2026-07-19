"""V38 private catalog loading and source-balanced selector contracts."""

from __future__ import annotations

import json
import random
from collections import Counter
from pathlib import Path

import pytest

from cat_de_roman_esti.wordgames.derived_catalog import (
    DEFAULT_DERIVED_CATALOG,
    DERIVED_GAMES,
    DerivedBoard,
    DerivedCatalog,
    load_derived_catalog,
    score_band_weight,
)
from cat_de_roman_esti.wordgames.packs import load_pack


def _board(
    item_id: str,
    source_id: str,
    *,
    score: int = 65,
    starter: bool = True,
    category: str = "istorie",
    difficulty: str = "normal",
) -> DerivedBoard:
    return DerivedBoard(
        game="intrusul",
        category=category,
        difficulty=difficulty,
        payload={"members": ["a", "b", "c"], "intruder": "d", "group_label": "G"},
        _catalog_id=item_id,
        _source_id=source_id,
        _romanian_familiarity=score,
        _play_quality=score,
        _standard_score=score,
        _starter_score=score,
        _starter_eligible=starter,
        _standard_rank=1,
        _starter_rank=1 if starter else None,
    )


def test_bundled_catalog_loads_exact_private_inventory() -> None:
    catalog = load_derived_catalog()
    assert catalog.counts() == {"intrusul": 183, "perechi": 153}
    assert {board._source_id for board in catalog.pool("intrusul")}.__len__() == 66
    assert {board._source_id for board in catalog.pool("perechi")}.__len__() == 51
    first = catalog.pool("intrusul")[0]
    assert not hasattr(first, "id") and not hasattr(first, "source_id")
    assert first._source_id not in repr(first)
    assert "standard_score" not in repr(first)


def test_bundled_artifact_digest_drift_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    modified = json.loads(DEFAULT_DERIVED_CATALOG.read_text(encoding="utf-8"))
    modified["boards"][0]["romanian_familiarity"] -= 1
    path = tmp_path / "derived_catalog_v38.json"
    path.write_text(json.dumps(modified, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(
        "cat_de_roman_esti.wordgames.derived_catalog.DEFAULT_DERIVED_CATALOG", path
    )
    with pytest.raises(ValueError, match="bundled artifact digest drift"):
        load_derived_catalog()


@pytest.mark.parametrize("schema", [True, 1.0, "1"])
def test_schema_version_requires_exact_integer(
    schema: object, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    document = json.loads(DEFAULT_DERIVED_CATALOG.read_text(encoding="utf-8"))
    document["meta"]["schema_version"] = schema
    path = tmp_path / "catalog.json"
    path.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(ValueError, match="unsupported schema version"):
        load_derived_catalog(path)


def test_runtime_fixture_overrides_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CAT_KG_FIXTURE", "/tmp/other-graph.json")
    with pytest.raises(ValueError, match="runtime fixture override"):
        load_derived_catalog()


def test_equal_scores_receive_equal_stable_ticket_bands() -> None:
    assert score_band_weight(54) == 1
    assert score_band_weight(55) == 2
    assert score_band_weight(65) == 3
    assert score_band_weight(75) == 4
    assert score_band_weight(85) == 5
    assert score_band_weight(75) == score_band_weight(75)
    assert score_band_weight(True) == 1


def test_seeded_selection_is_source_balanced_not_candidate_balanced() -> None:
    boards = [
        _board("a1", "source-a"),
        _board("b1", "source-b"),
        _board("b2", "source-b"),
        _board("b3", "source-b"),
    ]
    forward = DerivedCatalog(boards)
    reverse = DerivedCatalog(list(reversed(boards)))
    counts: Counter[str] = Counter()
    for seed in range(2_000):
        left = forward.pick_seeded("intrusul", random.Random(seed))
        right = reverse.pick_seeded("intrusul", random.Random(seed))
        assert left is not None and right is not None
        assert left._catalog_id == right._catalog_id
        counts[left._source_id] += 1
    ratio = counts["source-a"] / counts["source-b"]
    assert 0.80 < ratio < 1.25


def test_starter_exclusions_and_empty_filters_never_widen() -> None:
    eligible = _board("a", "source-a", starter=True)
    reserve = _board("b", "source-b", starter=False, category="muzica")
    catalog = DerivedCatalog([eligible, reserve])
    picked = catalog.pick_seeded("intrusul", random.Random(1), starter=True)
    assert picked is not None and picked._catalog_id == "a"
    assert (
        catalog.pick_seeded(
            "intrusul",
            random.Random(1),
            starter=True,
            exclude_source_ids={"source-a"},
        )
        is None
    )
    assert catalog.pick_seeded("intrusul", random.Random(1), category="stiinta") is None
    assert catalog.pick_daily("intrusul", "2026-07-19", category="stiinta") is None


def test_daily_selection_is_stable_and_order_independent() -> None:
    boards = [
        _board("a1", "source-a", score=55),
        _board("a2", "source-a", score=85),
        _board("b1", "source-b", score=75),
    ]
    forward = DerivedCatalog(boards)
    reverse = DerivedCatalog(list(reversed(boards)))
    for day in range(200):
        key = f"2026-v38-{day}"
        left = forward.pick_daily("intrusul", key)
        right = reverse.pick_daily("intrusul", key)
        assert left is not None and right is not None
        assert left._catalog_id == right._catalog_id


def test_v37_daily_assignments_remain_unchanged() -> None:
    pack = load_pack()
    expected = {
        ("conexiuni", "2026-07-19"): "cx_film_tv_169",
        ("conexiuni", "2026-12-31"): "cx_societate_290",
        ("contexto", "2026-07-19"): "ct_viata_de_roman_273",
        ("contexto", "2026-12-31"): "ct_muzica_243",
        ("lant", "2026-07-19"): "lt_viata_de_roman_094",
        ("lant", "2026-12-31"): "lt_film_tv_011",
        ("alchimie", "2026-07-19"): "al_muzica_066",
        ("alchimie", "2026-12-31"): "al_muzica_064",
    }
    assert {
        (game, day): pack.pick_daily(game, day, difficulty="normal").id
        for game, day in expected
    } == expected


def test_catalog_constructor_does_not_mutate_v37_pack_behavior() -> None:
    original = load_pack().pick_daily("contexto", "2026-08-08", difficulty="normal")
    catalog = load_derived_catalog()
    assert catalog.counts()[DERIVED_GAMES[0]] > 0
    after = load_pack().pick_daily("contexto", "2026-08-08", difficulty="normal")
    assert original is not None and after is not None and original.id == after.id
