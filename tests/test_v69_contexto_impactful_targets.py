"""V69 regression guards for impactful Cald sau Rece target selection."""

from __future__ import annotations

import json
import random
from datetime import date, timedelta
from pathlib import Path

import pytest

pytest.importorskip("django")

from django.test import Client  # noqa: E402

from cat_de_roman_esti.wordgames.categories import CATEGORIES  # noqa: E402
from cat_de_roman_esti.wordgames.contexto import (  # noqa: E402
    _build_session,
    _score_feedback,
    store,
)
from cat_de_roman_esti.wordgames.packs import (  # noqa: E402
    CURATED_CATEGORY_DAILY_MIN_POOL,
    load_pack,
)
from cat_de_roman_esti.wordgames.service import get_service, normalize  # noqa: E402

_ROOT = Path(__file__).resolve().parent.parent
_PACKAGE_RESERVE = _ROOT / "cat_de_roman_esti/fixtures/contexto_impact_reserve_v69.json"
_TEST_RESERVE = _ROOT / "tests/fixtures/contexto_impact_reserve_v69.json"
_PACKAGE_RANKINGS = _ROOT / "cat_de_roman_esti/fixtures/board_rankings_v37.json"
_TEST_RANKINGS = _ROOT / "tests/fixtures/board_rankings_v37.json"
_RESERVE_ID = "ct_muzica_163"


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _revealed_target(client: Client, url: str) -> str:
    created = client.post(url)
    assert created.status_code == 200
    game_id = created.json()["game_id"]
    revealed = client.post(f"/api/wordgames/contexto/games/{game_id}/giveup")
    assert revealed.status_code == 200
    return str(revealed.json()["target"]["id"])


def test_refren_rank_two_reproduction_has_two_distinct_exact_owners() -> None:
    svc = get_service()
    target = "n_muz_refren_viral"
    guess = svc.resolve("refren")

    assert guess == "n_v4muz_refren"
    assert svc.resolve("refren viral") == target
    assert guess != target
    assert svc.label(guess) == "Refren"
    assert svc.label(target) == "Refren viral"
    target_node = svc.node(target)
    assert target_node is not None
    assert normalize("refren") not in {normalize(alias) for alias in target_node.aliases}

    session = _build_session(target, "usor", None)
    score = _score_feedback(svc, session, guess)
    assert score.distance == 1
    assert score.rank == 2


def test_v69_impact_reserve_is_mirrored_exact_and_demoted_only_once() -> None:
    assert _PACKAGE_RESERVE.read_bytes() == _TEST_RESERVE.read_bytes()
    reserve = _json(_PACKAGE_RESERVE)
    assert set(reserve) == {"meta", "ids"}
    assert reserve["meta"]["count"] == len(reserve["ids"]) == 1
    assert reserve["ids"] == [_RESERVE_ID]

    assert _PACKAGE_RANKINGS.read_bytes() == _TEST_RANKINGS.read_bytes()
    ranked = {row["id"]: row for row in _json(_PACKAGE_RANKINGS)["boards"]}
    assert ranked[_RESERVE_ID]["status"] == "approved"
    assert ranked[_RESERVE_ID]["pilot_eligible"] is False
    assert ranked[_RESERVE_ID]["selection_weight"] == 1


def test_contexto_retains_201_unique_targets_across_every_category() -> None:
    pack = load_pack()
    eligible = [item for item in pack.pool("contexto") if item._pilot_eligible]

    assert len(eligible) == 203
    assert len({str(item.payload["target"]) for item in eligible}) == 203
    assert {item.category for item in eligible} == set(CATEGORIES)
    assert _RESERVE_ID in {item.id for item in pack.pool("contexto")}
    assert _RESERVE_ID not in {item.id for item in eligible}


def test_muzica_easy_shelf_stays_above_daily_floor_and_never_serves_reserve() -> None:
    pack = load_pack()
    shelf = [
        item
        for item in pack.pool("contexto", category="muzica", difficulty="usor")
        if item._pilot_eligible
    ]
    selectable_ids = {item.id for item in shelf}

    assert len(shelf) == 6
    assert len(shelf) >= CURATED_CATEGORY_DAILY_MIN_POOL
    assert _RESERVE_ID not in selectable_ids
    for seed in range(400):
        picked = pack.pick_seeded(
            "contexto",
            random.Random(seed),
            category="muzica",
            difficulty="usor",
            filtered_shelf_weights=True,
        )
        assert picked is not None and picked.id in selectable_ids
    for offset in range(366):
        day = (date(2026, 1, 1) + timedelta(days=offset)).isoformat()
        picked = pack.pick_daily(
            "contexto",
            day,
            category="muzica",
            difficulty="usor",
            filtered_shelf_weights=True,
        )
        assert picked is not None and picked.id in selectable_ids


def test_contexto_create_opts_into_filtered_shelf_weights_for_seeded_and_daily() -> None:
    pack = load_pack()
    filters = {"category": "muzica", "difficulty": "usor"}

    seeded_case = None
    for seed in range(200):
        legacy = pack.pick_seeded("contexto", random.Random(seed), **filters)
        impact = pack.pick_seeded(
            "contexto",
            random.Random(seed),
            filtered_shelf_weights=True,
            **filters,
        )
        assert legacy is not None and impact is not None
        if legacy.id != impact.id:
            seeded_case = (seed, legacy, impact)
            break
    assert seeded_case is not None
    seed, legacy, impact = seeded_case
    target = _revealed_target(
        Client(),
        f"/api/wordgames/contexto/games?seed={seed}&category=muzica&difficulty=usor",
    )
    assert target == impact.payload["target"]
    assert target != legacy.payload["target"]

    daily_case = None
    for offset in range(366):
        day = (date(2026, 1, 1) + timedelta(days=offset)).isoformat()
        legacy = pack.pick_daily("contexto", day, **filters)
        impact = pack.pick_daily(
            "contexto",
            day,
            filtered_shelf_weights=True,
            **filters,
        )
        assert legacy is not None and impact is not None
        if legacy.id != impact.id:
            daily_case = (day, legacy, impact)
            break
    assert daily_case is not None
    day, legacy, impact = daily_case
    target = _revealed_target(
        Client(),
        f"/api/wordgames/contexto/games?daily={day}&category=muzica&difficulty=usor",
    )
    assert target == impact.payload["target"]
    assert target != legacy.payload["target"]
    assert store._ttl == 7200
    assert store._max == 1000
