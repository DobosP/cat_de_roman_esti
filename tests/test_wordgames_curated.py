"""Curated-games serving: category param, curated-first selection, submissions.

Exercises the starter pack bundled in ``fixtures/games_pack.json`` end-to-end
through the four create endpoints, the ``/api/categories`` taxonomy endpoint and
the ``/api/submissions`` intake — including the hidden-answer guarantees curated
boards must keep (authored group labels stay reveal-gated, curated Contexto
targets stay hidden, curated dailies stay themeless).
"""

from __future__ import annotations

import importlib
import json

import pytest

pytest.importorskip("django")

from django.test import Client

from cat_de_roman_esti.wordgames.packs import get_pack


def _strings(obj: object) -> set[str]:
    found: set[str] = set()
    if isinstance(obj, str):
        found.add(obj)
    elif isinstance(obj, dict):
        for value in obj.values():
            found |= _strings(value)
    elif isinstance(obj, list):
        for item in obj:
            found |= _strings(item)
    return found


# --------------------------------------------------------------------------- pack
def test_pack_loads_and_pools_filter():
    pack = get_pack()
    counts = pack.counts()
    # The bundled pack always carries at least the istorie/geografie starters.
    assert counts["conexiuni"] >= 1 and counts["contexto"] >= 1
    assert all(i.approved for game in counts for i in pack.pool(game))
    istorie = pack.pool("conexiuni", category="istorie")
    assert istorie and all(i.category == "istorie" for i in istorie)
    assert "cx_istorie_001" in {i.id for i in istorie}
    for i in pack.pool("contexto", difficulty="usor"):
        assert i.difficulty == "usor"


# ---------------------------------------------------------------------- conexiuni
def _pack_item(game: str, item_id: str):
    matches = [i for i in get_pack().pool(game) if i.id == item_id]
    assert matches, f"pack item {item_id} not found"
    return matches[0]


@pytest.mark.parametrize("game", ("conexiuni", "contexto", "lant", "alchimie"))
def test_default_play_prefers_curated_pack_deterministically(game: str):
    """Ordinary play must benefit from the reviewed v12 pack, not bypass it."""
    module = importlib.import_module(f"cat_de_roman_esti.wordgames.{game}")
    url = f"/api/wordgames/{game}/games?seed=131&difficulty=normal"

    first = Client().post(url)
    second = Client().post(url)
    assert first.status_code == second.status_code == 200

    first_session = module.store.get(first.json()["game_id"])
    second_session = module.store.get(second.json()["game_id"])
    assert first_session is not None and second_session is not None
    assert first_session.pack_id is not None
    assert first_session.pack_id == second_session.pack_id
    assert first_session.pack_id in {
        item.id for item in get_pack().pool(game, difficulty="normal")
    }


@pytest.mark.parametrize("game", ("conexiuni", "contexto", "lant", "alchimie"))
def test_default_play_mines_only_when_curated_pool_is_empty(game: str, monkeypatch):
    """The deterministic generators remain a fail-soft fallback for a thin pack."""
    from cat_de_roman_esti.wordgames.packs import GamesPack

    module = importlib.import_module(f"cat_de_roman_esti.wordgames.{game}")
    monkeypatch.setattr(module, "get_pack", lambda: GamesPack([]))

    response = Client().post(
        f"/api/wordgames/{game}/games?seed=137&difficulty=normal"
    )
    assert response.status_code == 200
    session = module.store.get(response.json()["game_id"])
    assert session is not None
    assert session.pack_id is None


def test_conexiuni_curated_board_by_category():
    from cat_de_roman_esti.wordgames.conexiuni import store

    c = Client()
    body = c.post("/api/wordgames/conexiuni/games?seed=5&category=istorie").json()
    assert body["board_category"] == "istorie"
    assert len(body["tiles"]) == 16
    session = store.get(body["game_id"])
    item = _pack_item("conexiuni", session.pack_id)
    assert item.category == "istorie"
    assert session.group_labels == item.payload["group_labels"]
    # Authored labels and group keys stay reveal-gated pre-terminal.
    public = _strings(body)
    for hidden in [*session.group_labels.values(), *session.groups.keys()]:
        assert hidden not in public


def test_conexiuni_curated_solution_reveals_authored_labels():
    from cat_de_roman_esti.wordgames.conexiuni import store

    c = Client()
    body = c.post("/api/wordgames/conexiuni/games?seed=5&category=istorie").json()
    gid = body["game_id"]
    session = store.get(gid)
    authored = set(session.group_labels.values())
    for ids in session.groups.values():
        body = c.post(
            f"/api/wordgames/conexiuni/games/{gid}/guess",
            {"ids": list(ids)},
            content_type="application/json",
        ).json()
    assert body["won"] is True
    labels = {group["label"] for group in body["solution"]}
    assert labels == authored
    assert "Istorie" in body["share"]


def test_conexiuni_unknown_category_400_and_empty_category_503():
    c = Client()
    assert c.post("/api/wordgames/conexiuni/games?category=nope").status_code == 400
    # A known category with no approved boards fails closed with a clear message.
    empty = next(
        (
            key
            for key in ("muzica", "film_tv", "meme_net", "sport", "societate", "limba")
            if not get_pack().pool("conexiuni", category=key)
        ),
        None,
    )
    if empty is not None:
        assert c.post(f"/api/wordgames/conexiuni/games?category={empty}").status_code == 503


def test_daily_curated_floor_matches_pool_size():
    from cat_de_roman_esti.wordgames.conexiuni import store
    from cat_de_roman_esti.wordgames.packs import CURATED_DAILY_MIN_POOL

    c = Client()
    body = c.post("/api/wordgames/conexiuni/games?daily=2026-07-07&difficulty=normal").json()
    session = store.get(body["game_id"])
    pool = get_pack().pool("conexiuni", difficulty="normal")
    if len(pool) >= CURATED_DAILY_MIN_POOL:
        assert session.pack_id is not None  # deep pool -> curated daily
    else:
        assert session.pack_id is None  # thin pool -> historical mined daily


def test_daily_prefers_curated_once_the_pool_is_deep(monkeypatch):
    from cat_de_roman_esti.wordgames import conexiuni
    from cat_de_roman_esti.wordgames.packs import (
        CURATED_DAILY_MIN_POOL,
        CuratedItem,
        GamesPack,
        get_pack,
    )

    base = get_pack().pool("conexiuni", category="istorie")[0]
    items = [
        CuratedItem(
            id=f"cx_synth_{i:03d}", game="conexiuni", category="istorie",
            difficulty="normal", source="ai", status="approved",
            payload=base.payload,
        )
        for i in range(CURATED_DAILY_MIN_POOL)
    ]
    monkeypatch.setattr(conexiuni, "get_pack", lambda: GamesPack(items))

    c = Client()
    day = "2026-07-07"
    first = c.post(f"/api/wordgames/conexiuni/games?daily={day}").json()
    second = c.post(f"/api/wordgames/conexiuni/games?daily={day}").json()
    s1 = conexiuni.store.get(first["game_id"])
    s2 = conexiuni.store.get(second["game_id"])
    assert s1.pack_id is not None
    assert s1.pack_id == s2.pack_id  # stable within the day
    # A curated daily stays themeless (the theme is a paid/earned reveal).
    assert "board_category" not in first


# ----------------------------------------------------------------------- contexto
def test_contexto_curated_target_by_category_stays_hidden():
    from cat_de_roman_esti.wordgames.contexto import store

    c = Client()
    body = c.post("/api/wordgames/contexto/games?seed=1&category=istorie").json()
    assert body["board_category"] == "istorie"
    session = store.get(body["game_id"])
    item = _pack_item("contexto", session.pack_id)
    assert session.target == item.payload["target"]
    assert session.target not in _strings(body)


def test_contexto_mined_fallback_stays_inside_category(monkeypatch):
    from cat_de_roman_esti.wordgames import contexto
    from cat_de_roman_esti.wordgames.packs import GamesPack
    from cat_de_roman_esti.wordgames.service import get_service

    monkeypatch.setattr(contexto, "get_pack", lambda: GamesPack([]))  # force mining
    c = Client()
    body = c.post("/api/wordgames/contexto/games?seed=7&category=literatura").json()
    session = contexto.store.get(body["game_id"])
    assert session.pack_id is None
    assert session.target in set(get_service().by_category("literatura"))


# --------------------------------------------------------------------------- lant
def test_lant_curated_pair_by_category():
    from cat_de_roman_esti.wordgames.lant import store

    c = Client()
    body = c.post("/api/wordgames/lant/games?seed=3&category=istorie").json()
    assert body["board_category"] == "istorie"
    session = store.get(body["game_id"])
    item = _pack_item("lant", session.pack_id)
    assert session.start == item.payload["start"]
    assert session.target == item.payload["target"]
    assert session.optimal == item.payload["optimal"]


def test_lant_mined_fallback_keeps_endpoints_in_category(monkeypatch):
    from cat_de_roman_esti.wordgames import lant
    from cat_de_roman_esti.wordgames.packs import GamesPack
    from cat_de_roman_esti.wordgames.service import get_service

    monkeypatch.setattr(lant, "get_pack", lambda: GamesPack([]))  # force mining
    c = Client()
    body = c.post("/api/wordgames/lant/games?seed=9&category=stiinta").json()
    session = lant.store.get(body["game_id"])
    members = set(get_service().by_category("stiinta"))
    assert session.pack_id is None
    assert session.start in members and session.target in members


# ----------------------------------------------------------------------- alchimie
def test_alchimie_curated_instance_by_category():
    from cat_de_roman_esti.wordgames.alchimie import store

    c = Client()
    body = c.post("/api/wordgames/alchimie/games?seed=2&category=istorie").json()
    assert body["board_category"] == "istorie"
    assert body["target"]["id"] is None  # still hidden pre-win
    session = store.get(body["game_id"])
    item = _pack_item("alchimie", session.pack_id)
    assert session.seeds == item.payload["seeds"]
    assert session.target_depth == item.payload["target_depth"]


# -------------------------------------------------------------------- /api/categories
def test_categories_endpoint_reports_taxonomy_and_availability():
    c = Client()
    body = c.get("/api/categories").json()
    by_key = {entry["key"]: entry for entry in body["categories"]}
    assert len(by_key) == 14
    assert by_key["muzica"]["kind"] == "pop"
    assert by_key["istorie"]["kind"] == "serious"
    # istorie: curated everywhere -> every game available.
    assert all(by_key["istorie"]["available"].values())
    assert by_key["istorie"]["curated"]["conexiuni"] >= 1
    # The serving rule itself: Conexiuni availability == an approved curated board
    # exists (it cannot be mined per-category); counts mirror the loaded pack.
    pack = get_pack()
    for key, entry in by_key.items():
        assert entry["available"]["conexiuni"] == (entry["curated"]["conexiuni"] > 0)
        assert entry["curated"]["conexiuni"] == len(pack.pool("conexiuni", category=key))


# ------------------------------------------------------------------- /api/submissions
VALID_SUBMISSION = {
    "game": "lant",
    "category": "istorie",
    "difficulty": "normal",
    "payload": {"start": None, "target": None, "optimal": None},  # filled per-test
}


def _fresh_submission() -> dict:
    item = get_pack().pool("lant", category="istorie")[0]
    body = json.loads(json.dumps(VALID_SUBMISSION))
    body["payload"] = dict(item.payload)
    return body


@pytest.fixture(autouse=True)
def _reset_rate_limit():
    from cat_de_roman_esti.wordgames import submissions

    submissions._rate_hits.clear()
    yield
    submissions._rate_hits.clear()


def test_submissions_disabled_without_env(monkeypatch):
    monkeypatch.delenv("CAT_SUBMISSIONS_DIR", raising=False)
    resp = Client().post(
        "/api/submissions", _fresh_submission(), content_type="application/json"
    )
    assert resp.status_code == 503


def test_submissions_accepted_lands_pending_in_queue(tmp_path, monkeypatch):
    monkeypatch.setenv("CAT_SUBMISSIONS_DIR", str(tmp_path))
    resp = Client().post(
        "/api/submissions", _fresh_submission(), content_type="application/json"
    )
    assert resp.status_code == 202
    body = resp.json()
    assert body["status"] == "pending"
    lines = (tmp_path / "submissions.jsonl").read_text(encoding="utf-8").splitlines()
    entry = json.loads(lines[0])
    assert entry["game"] == "lant"
    assert entry["item"]["status"] == "pending"
    assert entry["item"]["source"] == "user"
    assert entry["item"]["id"] == body["id"]


def test_submissions_invalid_payload_rejected(tmp_path, monkeypatch):
    monkeypatch.setenv("CAT_SUBMISSIONS_DIR", str(tmp_path))
    bad = _fresh_submission()
    bad["payload"]["target"] = "n_nu_exista"
    resp = Client().post("/api/submissions", bad, content_type="application/json")
    assert resp.status_code == 400
    assert not (tmp_path / "submissions.jsonl").exists()


def test_submissions_rate_limited(tmp_path, monkeypatch):
    from cat_de_roman_esti.wordgames import submissions

    monkeypatch.setenv("CAT_SUBMISSIONS_DIR", str(tmp_path))
    c = Client()
    good = _fresh_submission()
    for _ in range(submissions.RATE_LIMIT_MAX):
        assert c.post("/api/submissions", good, content_type="application/json").status_code == 202
    resp = c.post("/api/submissions", good, content_type="application/json")
    assert resp.status_code == 429
