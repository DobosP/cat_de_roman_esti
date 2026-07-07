"""Curated-games serving: category param, curated-first selection, submissions.

Exercises the starter pack bundled in ``fixtures/games_pack.json`` end-to-end
through the four create endpoints, the ``/api/categories`` taxonomy endpoint and
the ``/api/submissions`` intake — including the hidden-answer guarantees curated
boards must keep (authored group labels stay reveal-gated, curated Contexto
targets stay hidden, curated dailies stay themeless).
"""

from __future__ import annotations

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
def test_starter_pack_loads_and_pools_filter():
    pack = get_pack()
    assert pack.counts() == {"conexiuni": 2, "contexto": 2, "lant": 2, "alchimie": 1}
    assert [i.id for i in pack.pool("conexiuni", category="istorie")] == ["cx_istorie_001"]
    assert pack.pool("conexiuni", category="muzica") == []
    assert pack.pool("contexto", category="istorie", difficulty="greu") == []


# ---------------------------------------------------------------------- conexiuni
def test_conexiuni_curated_board_by_category():
    from cat_de_roman_esti.wordgames.conexiuni import store

    c = Client()
    body = c.post("/api/wordgames/conexiuni/games?seed=5&category=istorie").json()
    assert body["board_category"] == "istorie"
    assert len(body["tiles"]) == 16
    session = store.get(body["game_id"])
    assert session.pack_id == "cx_istorie_001"
    assert session.group_labels["voievozi"] == "Voievozi medievali"
    # Authored labels and group keys stay reveal-gated pre-terminal.
    public = _strings(body)
    for hidden in ("Voievozi medievali", "Lumea dacica", "voievozi", "dacia"):
        assert hidden not in public


def test_conexiuni_curated_solution_reveals_authored_labels():
    from cat_de_roman_esti.wordgames.conexiuni import store

    c = Client()
    body = c.post("/api/wordgames/conexiuni/games?seed=5&category=istorie").json()
    gid = body["game_id"]
    session = store.get(gid)
    for ids in session.groups.values():
        body = c.post(
            f"/api/wordgames/conexiuni/games/{gid}/guess",
            {"ids": list(ids)},
            content_type="application/json",
        ).json()
    assert body["won"] is True
    labels = {group["label"] for group in body["solution"]}
    assert labels == {
        "Voievozi medievali",
        "Conducatori ai Romaniei moderne",
        "Lumea dacica",
        "Momente ale Unirii",
    }
    assert "Istorie" in body["share"]


def test_conexiuni_unknown_category_400_and_empty_category_503():
    c = Client()
    assert c.post("/api/wordgames/conexiuni/games?category=nope").status_code == 400
    assert c.post("/api/wordgames/conexiuni/games?category=muzica").status_code == 503


def test_daily_stays_mined_while_curated_pool_is_thin():
    from cat_de_roman_esti.wordgames.conexiuni import store

    c = Client()
    body = c.post("/api/wordgames/conexiuni/games?daily=2026-07-07").json()
    # Starter pack has 1 board per category — far below CURATED_DAILY_MIN_POOL,
    # so the shared daily keeps the historical mined behavior (variety guard).
    assert store.get(body["game_id"]).pack_id is None


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
    assert session.pack_id == "ct_istorie_001"
    assert session.target == "n_stefan_cel_mare"
    assert "n_stefan_cel_mare" not in _strings(body)


def test_contexto_mined_fallback_stays_inside_category():
    from cat_de_roman_esti.wordgames.contexto import store
    from cat_de_roman_esti.wordgames.service import get_service

    c = Client()
    body = c.post("/api/wordgames/contexto/games?seed=7&category=literatura").json()
    session = store.get(body["game_id"])
    assert session.pack_id is None
    assert session.target in set(get_service().by_category("literatura"))


# --------------------------------------------------------------------------- lant
def test_lant_curated_pair_by_category():
    from cat_de_roman_esti.wordgames.lant import store

    c = Client()
    body = c.post("/api/wordgames/lant/games?seed=3&category=istorie").json()
    assert body["board_category"] == "istorie"
    session = store.get(body["game_id"])
    assert session.pack_id == "lt_istorie_001"
    pack_item = get_pack().pool("lant", category="istorie")[0]
    assert session.start == pack_item.payload["start"]
    assert session.target == pack_item.payload["target"]
    assert session.optimal == pack_item.payload["optimal"]


def test_lant_mined_fallback_keeps_endpoints_in_category():
    from cat_de_roman_esti.wordgames.lant import store
    from cat_de_roman_esti.wordgames.service import get_service

    c = Client()
    body = c.post("/api/wordgames/lant/games?seed=9&category=stiinta").json()
    session = store.get(body["game_id"])
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
    pack_item = get_pack().pool("alchimie", category="istorie")[0]
    assert session.pack_id == "al_istorie_001"
    assert session.seeds == pack_item.payload["seeds"]
    assert session.target_depth == pack_item.payload["target_depth"]


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
    assert by_key["istorie"]["curated"]["conexiuni"] == 1
    # muzica: no nodes, no curated content yet -> nothing available.
    assert not any(by_key["muzica"]["available"].values())
    assert by_key["muzica"]["node_count"] == 0
    # literatura: no curated boards, but minable for the three minable games.
    assert by_key["literatura"]["available"]["conexiuni"] is False
    assert by_key["literatura"]["available"]["contexto"] is True


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
