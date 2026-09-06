"""V77 ingredient routes: observable feedback and exact preservation boundaries."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path

import pytest

from tests.current_content import CURRENT_CONTENT

pytest.importorskip("django")

from django.test import Client  # noqa: E402

from cat_de_roman_esti.wordgames import contexto, lant  # noqa: E402
from cat_de_roman_esti.wordgames.service import get_service  # noqa: E402
from tests.content_history import (  # noqa: E402
    before_v80_pack,
    before_v80_rankings,
    before_v81_fixture,
)

ROOT = Path(__file__).resolve().parents[1]
FLOUR = "n_v24_food_pantry_faina"
TARGETS = ("n_gas_cozonac", "n_v3gas_clatite")


def test_graph_delta_reconstructs_the_exact_v76_fixture():
    """Pin history independently so refreshing current-artifact tests cannot hide drift."""
    fixture_path = ROOT / "cat_de_roman_esti/fixtures/kg_sample.json"
    fixture = before_v81_fixture(json.loads(fixture_path.read_bytes()))
    receipt = json.loads(
        (ROOT / "docs/reviews/v77-flour-associations/artifact-delta.json").read_bytes()
    )
    assert fixture_path.read_bytes() == (ROOT / "tests/fixtures/kg_sample.json").read_bytes()
    assert fixture["meta"]["build_version"] == "fixture-v77-flour-associations"
    assert len(fixture["kg_nodes"]) == 2364
    assert len(fixture["kg_edges"]) == 9219
    assert len(fixture["kg_puzzles"]) == 180
    edges = receipt["new_edges"]
    assert len(edges) == 2
    assert {e["dst_id"] for e in edges} == set(TARGETS)
    for edge in edges:
        assert edge in fixture["kg_edges"]
        assert {k: v for k, v in edge.items() if k not in ("id", "dst_id")} == {
            "src_id": FLOUR, "relation": "part_of", "label_ro": "ingredient pentru",
            "strength": 0.97, "bidirectional": 0, "is_distractor": 0,
        }
    restored = deepcopy(fixture)
    restored["meta"] = receipt["baseline_meta"]
    added_ids = {e["id"] for e in edges}
    restored["kg_edges"] = [e for e in restored["kg_edges"] if e["id"] not in added_ids]
    for node in restored["kg_nodes"]:
        node["degree"] -= 2 if node["id"] == FLOUR else int(node["id"] in TARGETS)
    restored["kg_puzzles"] = [
        receipt["changed_puzzles"].get(p["id"], {}).get("before", p)
        for p in restored["kg_puzzles"]
    ]
    blob = (json.dumps(restored, ensure_ascii=False, indent=2) + "\n").encode()
    assert hashlib.sha256(blob).hexdigest() == (
        "fa9575db4819fa314e43218a0ad953f52c3e6ee2e34cac105dbc88e2d2247106"
    )


def test_all_pack_records_ranking_rows_and_frozen_boards_remain_exact():
    package = ROOT / "cat_de_roman_esti/fixtures"
    pack = (package / "games_pack.json").read_bytes()
    assert pack == (ROOT / "tests/fixtures/games_pack.json").read_bytes()
    restored_pack = (
        json.dumps(before_v80_pack(json.loads(pack)), ensure_ascii=False, indent=1) + "\n"
    ).encode()
    assert hashlib.sha256(restored_pack).hexdigest() == (
        "9f559e33eac688868dfdf562f62022a3df629c9cb389b957dda0896d7cec70b5"
    )
    rankings = before_v80_rankings(
        json.loads((package / "board_rankings_v37.json").read_bytes())
    )
    assert len(rankings["boards"]) == 620
    ranked_payload = (json.dumps(rankings["boards"], ensure_ascii=False, indent=1) + "\n").encode()
    assert hashlib.sha256(ranked_payload).hexdigest() == (
        "80fc0672c82efa6317ec6e9f0a793efc12cad68a94093d2a8beabc9be34866cf"
    )
    derived = json.loads((package / "derived_catalog_v38.json").read_bytes())
    assert len(derived["boards"]) == CURRENT_CONTENT.derived_counts["total"]
    payload = (json.dumps(derived["boards"], ensure_ascii=False, indent=1) + "\n").encode()
    assert hashlib.sha256(payload).hexdigest() == (
        CURRENT_CONTENT.frozen_boards_sha256
    )


@pytest.mark.parametrize("target", TARGETS)
def test_flour_is_a_direct_ingredient_without_a_reverse_shortcut(target):
    svc = get_service()
    assert svc.distance(FLOUR, target) == 1
    assert svc.link(target, FLOUR) is None
    link = svc.link(FLOUR, target)
    assert link is not None
    assert link.label_ro == "ingredient pentru"


@pytest.mark.parametrize("target", TARGETS)
@pytest.mark.parametrize("surface", ("făină", "FAINA", "făinii"))
def test_flour_feedback_is_hot_private_and_survives_resume(target, surface):
    # Fix both targets here; Clătite is separately promoted and exercised by V80.
    client = Client()
    game_id = contexto.store.create(contexto._build_session(target, "usor", None))
    url = f"/api/wordgames/contexto/games/{game_id}"
    before = client.get(url).json()
    assert "target" not in before
    response = client.post(url + "/guess", {"text": surface}, content_type="application/json")
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["attempts"] == 1
    assert body["won"] is False
    assert "target" not in body
    guess = body["guesses"][0]
    assert guess["id"] == FLOUR
    assert guess["distance"] == 1
    assert guess["temperature"] == "Fierbinte"
    assert guess["rank"] <= 5
    assert target not in response.content.decode()
    resumed = client.get(url).json()
    assert resumed["guesses"] == body["guesses"]
    assert resumed["attempts"] == 1
    repeated = client.post(
        url + "/guess", {"text": surface}, content_type="application/json"
    ).json()
    assert repeated["attempts"] == 1
    won = client.post(
        url + "/guess", {"text": get_service().label(target)}, content_type="application/json"
    ).json()
    assert won["won"] is True
    assert won["attempts"] == 2


@pytest.mark.parametrize("target", TARGETS)
def test_lant_exposes_the_reviewed_ingredient_step(target):
    client = Client()
    session = lant.LantSession(start=FLOUR, target=target, optimal=1, chain=[FLOUR])
    game_id = lant.store.create(session)
    url = f"/api/wordgames/lant/games/{game_id}"
    response = client.post(
        url + "/move", {"text": get_service().label(target)}, content_type="application/json"
    )
    assert response.status_code == 200
    assert response.json()["won"] is True
    assert response.json()["moves"] == 1


def test_no_rejected_food_candidate_was_promoted_by_the_graph_wave():
    pack = before_v80_pack(
        json.loads((ROOT / "cat_de_roman_esti/fixtures/games_pack.json").read_text())
    )
    candidates = {*TARGETS, "n_gas_paine_de_casa"}
    assert not candidates & {row["target"] for row in pack["contexto"]}


def test_deferred_bread_link_does_not_make_flour_warm_for_a_fountain_pen():
    """The rejected third edge caused a misleading flour/bread/school-meal/pen route."""
    assert get_service().link(FLOUR, "n_gas_paine_de_casa") is None
    client = Client()
    game_id = contexto.store.create(contexto._build_session("n_stilou_rezervor", "normal", None))
    response = client.post(
        f"/api/wordgames/contexto/games/{game_id}/guess",
        {"text": "făină"}, content_type="application/json",
    )
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["guesses"][0]["temperature"] not in {"Fierbinte", "Cald", "Caldut"}
