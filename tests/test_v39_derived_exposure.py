"""V39 preferred-shelf and beginner exposure contracts."""

from __future__ import annotations

import json
import random
from collections import Counter
from dataclasses import replace

import pytest

pytest.importorskip("django")

from django.test import Client  # noqa: E402

from cat_de_roman_esti.wordgames import intrusul, perechi  # noqa: E402
from cat_de_roman_esti.wordgames.derived_catalog import (  # noqa: E402
    DerivedBoard,
    DerivedCatalog,
    get_derived_catalog,
)
from cat_de_roman_esti.wordgames.service import SessionStore  # noqa: E402

PRIVATE_FIELDS = {
    "source_id",
    "source_ring",
    "catalog_id",
    "romanian_familiarity",
    "play_quality",
    "standard_score",
    "starter_score",
    "starter_eligible",
    "standard_rank",
    "starter_rank",
    "selection_weight",
}


def _board(
    item_id: str,
    source_id: str,
    *,
    score: int,
    game: str = "intrusul",
    category: str = "istorie",
    difficulty: str = "normal",
) -> DerivedBoard:
    return DerivedBoard(
        game=game,
        category=category,
        difficulty=difficulty,
        payload={"members": ["a", "b", "c"], "intruder": "d", "group_label": "G"},
        _catalog_id=item_id,
        _source_id=source_id,
        _romanian_familiarity=score,
        _play_quality=score,
        _standard_score=score,
        _starter_score=score,
        _starter_eligible=True,
        _standard_rank=1,
        _starter_rank=1,
    )


def _all_keys(value: object) -> set[str]:
    if isinstance(value, dict):
        return set(value) | set().union(
            *(_all_keys(item) for item in value.values()),
            set(),
        )
    if isinstance(value, list):
        return set().union(*(_all_keys(item) for item in value), set())
    return set()


def test_runtime_prefers_standard_score_55_for_seeded_starter_and_daily() -> None:
    low = _board("low", "source-low", score=54)
    preferred = _board("preferred", "source-preferred", score=55)
    catalog = DerivedCatalog([low, preferred])

    for seed in range(200):
        standard = catalog.pick_seeded("intrusul", random.Random(seed))
        starter = catalog.pick_seeded(
            "intrusul",
            random.Random(seed),
            starter=True,
            balance_categories=True,
        )
        assert standard is not None and standard._catalog_id == "preferred"
        assert starter is not None and starter._catalog_id == "preferred"

    for day in range(50):
        daily = catalog.pick_daily("intrusul", f"2026-v39-{day}")
        assert daily is not None and daily._catalog_id == "preferred"

    # Inventory/audit access remains complete; only runtime exposure is refined.
    assert {board._catalog_id for board in catalog.pool("intrusul")} == {
        "low",
        "preferred",
    }


def test_sparse_filtered_shelf_falls_back_without_widening_category() -> None:
    low = _board("low", "source-low", score=54, category="istorie")
    preferred = _board("preferred", "source-preferred", score=85, category="istorie")
    other = _board("other", "source-other", score=85, category="muzica")
    catalog = DerivedCatalog([low, preferred, other])

    # Apply exclusions before the quality preference. The remaining strict category
    # stays playable even though its only board is below the preferred threshold.
    seeded = catalog.pick_seeded(
        "intrusul",
        random.Random(7),
        category="istorie",
        exclude_source_ids={"source-preferred"},
        starter=True,
        balance_categories=True,
    )
    assert seeded is not None and seeded._catalog_id == "low"

    daily_catalog = DerivedCatalog([low, other])
    daily = daily_catalog.pick_daily(
        "intrusul",
        "2026-07-23",
        category="istorie",
    )
    assert daily is not None and daily._catalog_id == "low"
    assert (
        daily_catalog.pick_seeded(
            "intrusul",
            random.Random(7),
            category="stiinta",
            starter=True,
            balance_categories=True,
        )
        is None
    )


def test_unscoped_starter_is_category_then_source_balanced_and_order_independent() -> None:
    boards = [_board("history-1", "history-source", score=65, category="istorie")]
    boards.extend(
        _board(
            f"music-{index}",
            f"music-source-{index}",
            score=65,
            category="muzica",
        )
        for index in range(8)
    )
    forward = DerivedCatalog(boards)
    reverse = DerivedCatalog(list(reversed(boards)))
    category_counts: Counter[str] = Counter()
    music_source_counts: Counter[str] = Counter()

    for seed in range(4_000):
        left = forward.pick_seeded(
            "intrusul",
            random.Random(seed),
            starter=True,
            balance_categories=True,
        )
        right = reverse.pick_seeded(
            "intrusul",
            random.Random(seed),
            starter=True,
            balance_categories=True,
        )
        assert left is not None and right is not None
        assert left._catalog_id == right._catalog_id
        category_counts[left.category] += 1
        if left.category == "muzica":
            music_source_counts[left._source_id] += 1

    category_ratio = category_counts["istorie"] / category_counts["muzica"]
    assert 0.90 < category_ratio < 1.10
    assert max(music_source_counts.values()) / min(music_source_counts.values()) < 1.35

    for seed in range(100):
        selected = forward.pick_seeded(
            "intrusul",
            random.Random(seed),
            category="muzica",
            starter=True,
            balance_categories=True,
        )
        assert selected is not None and selected.category == "muzica"


@pytest.mark.parametrize("game", ["intrusul", "perechi"])
def test_unscoped_starter_reserve_keeps_category_first_balance(
    game: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    boards = [
        replace(
            _board(
                "history-1",
                "history-source",
                score=65,
                category="istorie",
            ),
            game=game,
            _starter_eligible=False,
            _starter_rank=None,
        )
    ]
    boards.extend(
        replace(
            _board(
                f"music-{index}",
                f"music-source-{index}",
                score=65,
                category="muzica",
            ),
            game=game,
            _starter_eligible=False,
            _starter_rank=None,
        )
        for index in range(8)
    )
    catalog = DerivedCatalog(boards)
    counts: Counter[str] = Counter()

    if game == "perechi":
        monkeypatch.setattr(perechi, "get_derived_catalog", lambda: catalog)
        monkeypatch.setattr(perechi, "excluded_pack_ids", lambda *_args: set())

    for seed in range(2_000):
        if game == "intrusul":
            selected = intrusul._pick_non_daily(
                catalog,
                random.Random(seed),
                category=None,
                starter=True,
                excluded_sources=set(),
            )
        else:
            selected, _ = perechi._pick_non_daily(
                object(),
                random.Random(seed),
                category=None,
                starter=True,
                previous_game_id=None,
            )
        assert selected is not None and selected._starter_eligible is False
        counts[selected.category] += 1

    ratio = counts["istorie"] / counts["muzica"]
    assert 0.90 < ratio < 1.10


@pytest.mark.parametrize(
    ("game", "module", "base"),
    [
        ("intrusul", intrusul, "/api/wordgames/intrusul"),
        ("perechi", perechi, "/api/wordgames/perechi"),
    ],
)
def test_preferred_board_metadata_stays_private_in_game_api(
    game: str,
    module,
    base: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    real = get_derived_catalog().pool(game)[0]
    low = replace(
        real,
        _catalog_id=f"private-{game}-low",
        _source_id=f"private-{game}-source-low",
        _standard_score=54,
        _starter_score=90,
        _starter_eligible=True,
        _starter_rank=2,
    )
    preferred = replace(
        real,
        _catalog_id=f"private-{game}-preferred",
        _source_id=f"private-{game}-source-preferred",
        _standard_score=55,
        _starter_score=90,
        _starter_eligible=True,
        _starter_rank=1,
    )
    monkeypatch.setattr(
        module,
        "get_derived_catalog",
        lambda: DerivedCatalog([low, preferred]),
    )
    monkeypatch.setattr(module, "store", SessionStore())

    response = Client().post(f"{base}/games?seed=39&starter=1")
    assert response.status_code == 200, response.content
    body = response.json()
    session = module.store.get(body["game_id"])
    assert session is not None and session.catalog_id == preferred._catalog_id
    assert PRIVATE_FIELDS.isdisjoint(_all_keys(body))
    assert "board_category" not in body
    serialized = json.dumps(body, ensure_ascii=False, sort_keys=True)
    assert preferred._catalog_id not in serialized
    assert preferred._source_id not in serialized
