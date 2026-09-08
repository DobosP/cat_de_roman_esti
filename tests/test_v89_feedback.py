"""Exact food/dust feedback scopes preserve identity, privacy and prior meanings."""

from __future__ import annotations

import json
from dataclasses import asdict

import pytest
from django.test import Client

from cat_de_roman_esti.graph import Graph
from cat_de_roman_esti.wordgames import contexto as C
from cat_de_roman_esti.wordgames import contexto_projection as P
from cat_de_roman_esti.wordgames.contexto_feedback import EXACT_TARGET_FEEDBACK_PAIRS
from cat_de_roman_esti.wordgames.service import WordGameService, get_service

DIPLOMAT = "n_v87_food_tort_diplomat"
FRISCA = "n_v86_food_frisca"
PAMANT = "n_v24_nature_world_pamant"
DUST_ID = "ctxp_81703160cad7893fa1c9"
CLEANING = {
    "n_v31_cleaning_floor_faras",
    "n_v31_cleaning_floor_mop",
    "n_v31_cleaning_floor_aspirator",
}


def _post(client, path, word):
    response = client.post(path + "/guess", {"text": word}, content_type="application/json")
    assert response.status_code == 200
    return response.json()


def _private(body, target):
    assert "target" not in body and "solution" not in body
    encoded = json.dumps(body, ensure_ascii=False)
    assert target not in encoded and get_service().label(target) not in encoded


@pytest.mark.parametrize("word", [
    "Tort Diplomat", "tortul Diplomat", "tortului Diplomat", "torturi Diplomat",
])
def test_diplomat_is_a_hot_nonwinning_whipped_cream_cue(word):
    client = Client()
    gid = C.store.create(C._build_session(FRISCA, "usor", None))
    path = f"/api/wordgames/contexto/games/{gid}"
    try:
        body = _post(client, path, word)
        assert body["ok"] and not body["won"] and body["attempts"] == 1
        assert (body["guess"]["id"], body["guess"]["label"], body["guess"]["rank"]) == (
            DIPLOMAT, "Tort Diplomat", 2,
        )
        assert body["guess"]["temperature"] == "Fierbinte"
        assert body["guess"]["closeness"] < 100
        _private(body, FRISCA)
        repeat = _post(client, path, "TORT DIPLOMAT")
        assert repeat["attempts"] == 1 and repeat["feedback"]["kind"] == "repeat"
        assert client.get(path).json()["guesses"] == body["guesses"]
        won = _post(client, path, "frișcă")
        assert won["won"] and won["guess"]["rank"] == 1 and won["guess"]["id"] == FRISCA
    finally:
        C.store.delete(gid)


@pytest.mark.parametrize("target", sorted(CLEANING))
def test_projected_dust_is_hot_but_keeps_identity_and_never_wins(target):
    svc = get_service()
    assert svc.resolve("praf") is None
    term = P.resolve_projection("praf")
    assert (term.public_id, term.anchor_id, term.domain, term.rank_penalty) == (
        DUST_ID, PAMANT, "peisaj", 1,
    )
    client = Client()
    gid = C.store.create(C._build_session(target, "usor", None))
    path = f"/api/wordgames/contexto/games/{gid}"
    try:
        body = _post(client, path, "praf")
        assert body["ok"] and not body["won"] and body["attempts"] == 1
        assert (body["guess"]["id"], body["guess"]["label"], body["guess"]["rank"]) == (
            DUST_ID, "Praf", 2,
        )
        assert body["guess"]["temperature"] == "Fierbinte"
        assert body["guess"]["closeness"] < 100
        _private(body, target)
        repeat = _post(client, path, "  PRAF  ")
        assert repeat["attempts"] == 1 and repeat["feedback"]["kind"] == "repeat"
        assert client.get(path).json()["guesses"] == body["guesses"]
        won = _post(client, path, svc.label(target))
        assert won["won"] and won["guess"]["id"] == target and won["guess"]["rank"] == 1
    finally:
        C.store.delete(gid)


def test_dust_scope_is_exact_and_other_earth_terms_keep_their_meanings():
    svc = get_service()
    term = P.resolve_projection("praf")
    policy = P.PROJECTION_NEIGHBORHOODS["praf"]
    assert asdict(policy) == {
        "anchor_id": PAMANT, "min_strength": 0.6, "include_direct_neighbors": False,
        "exact_target_ids": frozenset(CLEANING),
    }
    same_anchor = [other for other in P.PROJECTION_TERMS if other.anchor_id == PAMANT]
    assert len(same_anchor) > 1
    for target in [*svc.graph.nodes, "missing_target"]:
        assert C._projection_anchor_id(svc, term, target) == (
            target if target in CLEANING else PAMANT
        )
    for other in same_anchor:
        if other.key == "praf":
            continue
        for target in CLEANING:
            assert C._projection_anchor_id(svc, other, target) == PAMANT
    for target in CLEANING:
        assert C._feedback_anchor_id(svc, PAMANT, target) == PAMANT


def test_native_diplomat_scope_and_projection_isolation_remain_closed():
    svc = get_service()
    assert (DIPLOMAT, FRISCA) in EXACT_TARGET_FEEDBACK_PAIRS
    for target in [*svc.graph.nodes, "missing_target"]:
        assert C._feedback_anchor_id(svc, DIPLOMAT, target) == (
            FRISCA if target == FRISCA else DIPLOMAT
        )
        assert C._feedback_anchor_id(svc, DIPLOMAT, target, allow_exact_pairs=False) == DIPLOMAT
    assert svc.link(FRISCA, DIPLOMAT) is not None
    assert svc.link(DIPLOMAT, FRISCA) is None
    assert svc.link("n_v20gas_smantana", FRISCA) is None


def test_missing_custom_fixture_anchors_keep_fallback_behavior():
    svc = get_service()
    for kept in [PAMANT, *sorted(CLEANING)]:
        custom = WordGameService(Graph.from_records([
            {"id": kept, "label_ro": svc.label(kept), "category": "viata_de_roman",
             "node_type": "concept", "description": "Custom control", "salience": 0.8},
        ], []))
        for target in CLEANING:
            assert C._projection_anchor_id(custom, P.resolve_projection("praf"), target) == PAMANT
    custom = WordGameService(Graph.from_records([
        {"id": DIPLOMAT, "label_ro": "Tort Diplomat", "category": "gastronomie",
         "node_type": "concept", "description": "Custom control", "salience": 0.8},
    ], []))
    assert C._feedback_anchor_id(custom, DIPLOMAT, FRISCA) == DIPLOMAT


def test_exact_diplomat_target_win_still_bypasses_feedback():
    gid = C.store.create(C._build_session(DIPLOMAT, "usor", None))
    try:
        body = _post(Client(), f"/api/wordgames/contexto/games/{gid}", "Tort Diplomat")
        assert body["won"] and body["guess"]["id"] == DIPLOMAT and body["score"] == 1000
    finally:
        C.store.delete(gid)


@pytest.mark.parametrize(("target", "offered"), [
    ("n_v31_cleaning_floor_faras", False),
    ("n_v31_cleaning_floor_mop", False),
    ("n_v31_cleaning_floor_aspirator", False),
    ("n_v88_cleaning_matura", True),
])
def test_projected_typo_filter_uses_only_the_exact_dust_scope(target, offered):
    svc = get_service()
    assert svc.resolve("prafzz") is None and svc.resolve_fuzzy("prafzz") is None
    assert "Praf" in [term.label for term in P.suggest_projection("prafzz")]
    gid = C.store.create(C._build_session(target, "usor", None))
    path = f"/api/wordgames/contexto/games/{gid}"
    try:
        body = _post(Client(), path, "prafzz")
        assert not body["ok"] and body["attempts"] == 0
        assert ("Praf" in body["suggestions"]) is offered
        _private(body, target)
        assert Client().get(path).json()["guesses"] == []
    finally:
        C.store.delete(gid)
