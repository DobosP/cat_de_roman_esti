"""Casual easy selection exposes reviewed narrow rounds while favoring wider routes."""
from __future__ import annotations

import random
from dataclasses import replace

import pytest
from django.test import Client

from cat_de_roman_esti.wordgames import lant as L
from cat_de_roman_esti.wordgames.packs import CuratedItem, GamesPack
from cat_de_roman_esti.wordgames.service import SessionStore


def item(name, *, eligible=True, difficulty="usor"):
    return CuratedItem(
        id=name, game="lant", category="gastronomie", difficulty=difficulty,
        source="ai", status="approved",
        payload={"start": name, "target": "target", "optimal": 2},
        _pilot_eligible=eligible,
    )


def pick(seed, *, daily=None, category="gastronomie", difficulty="usor", excluded=()):
    return L._pick_curated(
        random.Random(seed), daily=daily, category=category, difficulty=difficulty,
        exclude_ids=set(excluded),
    )


@pytest.fixture
def mixed_pool(monkeypatch):
    # Equal ranked weights isolate corridor preference from content popularity.
    rows = [item(f"{kind}-{i}") for kind in ("narrow", "wide") for i in range(8)]
    pack = GamesPack(rows, ranked=True)
    monkeypatch.setattr(L, "get_pack", lambda: pack)
    monkeypatch.setattr(L, "_corridor_profile", lambda start, _target, _optimal:
                        (3, 3, 3) if start.startswith("wide") else (2, 2, 2))
    return pack


def test_casual_easy_selection_is_repeatable_and_favors_wide_without_starving_narrow(mixed_pool):
    first = [pick(seed).id for seed in range(2048)]
    assert first == [pick(seed).id for seed in range(2048)]
    assert set(first) == {row.id for row in mixed_pool.pool("lant")}
    wide = sum(name.startswith("wide") for name in first)
    assert 0.80 < wide / len(first) < 0.95
    initial_narrow = [seed for seed in range(2048)
                      if mixed_pool.pick_seeded("lant", random.Random(seed),
                                                category="gastronomie",
                                                difficulty="usor").id.startswith("narrow")]
    retained = sum(first[seed].startswith("narrow") for seed in initial_narrow)
    # The retained fraction is near one quarter, conditional on a narrow first pick.
    assert 0.20 < retained / len(initial_narrow) < 0.30


@pytest.mark.parametrize("category", [None, "gastronomie"])
def test_daily_keeps_the_same_wide_rendezvous_pick_without_using_rng(mixed_pool, category):
    class NoRandom:
        def __getattr__(self, name):
            pytest.fail(f"Daily selection must not draw random values: {name}")

    wide = GamesPack([r for r in mixed_pool.pool("lant") if r.id.startswith("wide")],
                     ranked=True)
    for day in range(1, 29):
        daily = f"2026-09-{day:02d}"
        initial = mixed_pool.pick_daily("lant", daily, category=category, difficulty="usor")
        expected = initial if initial.id.startswith("wide") else wide.pick_daily(
            "lant", daily, category=category, difficulty="usor",
        )
        selected = L._pick_curated(NoRandom(), daily=daily, category=category,
                                  difficulty="usor", exclude_ids={expected.id})
        assert selected == expected


def test_casual_selection_respects_exclusions_in_both_preference_paths(mixed_pool):
    excluded = {"narrow-0", "wide-0", "wide-1"}
    results = {pick(seed, excluded=excluded).id for seed in range(512)}
    assert not results & excluded
    assert any(name.startswith("narrow") for name in results)
    assert any(name.startswith("wide") for name in results)


def test_thin_pool_still_exposes_its_narrow_approved_board(mixed_pool, monkeypatch):
    thin = GamesPack([item("narrow-0"), item("wide-0")], ranked=True)
    monkeypatch.setattr(L, "get_pack", lambda: thin)
    assert {pick(seed).id for seed in range(128)} == {"narrow-0", "wide-0"}
    # Below the category daily variety floor, the caller still gets its mined fallback.
    assert pick(3, daily="2026-09-15") is None


def test_exhausted_eligible_pool_repeats_safe_content_without_using_reserves(
    mixed_pool, monkeypatch,
):
    safe = item("narrow-safe")
    pool = GamesPack([safe, item("wide-reserve", eligible=False)], ranked=True)
    monkeypatch.setattr(L, "get_pack", lambda: pool)
    assert {pick(seed, excluded={safe.id}).id for seed in range(128)} == {safe.id}


def test_normal_selection_preserves_original_seed_and_rng_state(mixed_pool, monkeypatch):
    normal = GamesPack([replace(row, difficulty="normal") for row in mixed_pool.pool("lant")],
                       ranked=True)
    monkeypatch.setattr(L, "get_pack", lambda: normal)
    for seed in range(32):
        expected_rng, actual_rng = random.Random(seed), random.Random(seed)
        expected = normal.pick_seeded("lant", expected_rng, category="gastronomie",
                                      difficulty="normal")
        actual = L._pick_curated(actual_rng, daily=None, category="gastronomie",
                                difficulty="normal", exclude_ids=set())
        assert actual == expected and actual_rng.getstate() == expected_rng.getstate()


@pytest.mark.parametrize("board_id", ["lt_gastronomie_243", "lt_gastronomie_244"])
def test_new_two_route_rounds_naturally_serve_anonymously_without_exclusions(monkeypatch, board_id):
    monkeypatch.setattr(L, "store", SessionStore())
    seed = next(seed for seed in range(2048) if pick(seed).id == board_id)
    client = Client()
    states = []
    for _ in range(2):
        response = client.post(
            f"/api/wordgames/lant/games?category=gastronomie&difficulty=usor&seed={seed}",
        )
        assert response.status_code == 200, response.content
        state = response.json()
        session = L.store.get(state["game_id"])
        assert session.pack_id == board_id
        assert L._route_profiles(session.start, session.target, session.optimal)[0][:2] == (2, 2)
        assert not L._is_wide_beginner_item(pick(seed))
        states.append(state)
    for field in ("start", "target", "optimal", "choices", "board_category", "difficulty"):
        assert states[0][field] == states[1][field]
