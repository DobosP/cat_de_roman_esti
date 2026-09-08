"""Native dust replaces one approximation without changing other meanings or leaking answers."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import Path

import pytest
from django.test import Client

from cat_de_roman_esti.graph import Graph
from cat_de_roman_esti.wordgames import contexto as C
from cat_de_roman_esti.wordgames import contexto_feedback as F
from cat_de_roman_esti.wordgames import contexto_projection as P
from cat_de_roman_esti.wordgames.packs import get_pack
from cat_de_roman_esti.wordgames.service import WordGameService, get_service, normalize
from tests.content_history import before_v90_projection_neighborhoods, before_v90_projection_rows
from tests.current_content import CURRENT_CONTENT
from tests.v89_contexto_snapshot import v89_contexto_snapshot

DUST = "n_v90_household_praf"
EARTH = "n_v24_nature_world_pamant"
RETIRED = "ctxp_81703160cad7893fa1c9"
TOOLS = (
    "n_v31_cleaning_floor_faras", "n_v31_cleaning_floor_mop",
    "n_v31_cleaning_floor_aspirator", "n_v88_cleaning_matura",
)
ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "docs/reviews/v90-household-discovery-and-critique-gates"


def _sha(value):
    return hashlib.sha256(json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ).encode()).hexdigest()


def _private(body, target):
    encoded = json.dumps(body, ensure_ascii=False)
    assert "target" not in body and "solution" not in body and "anchor_id" not in encoded
    assert target not in encoded
    # A player-entered qualified label such as Praf de copt may contain "Praf";
    # none of the unearned scalar labels may be the exact hidden dust answer.
    def leaves(value):
        if isinstance(value, dict):
            for item in value.values():
                yield from leaves(item)
        elif isinstance(value, list):
            for item in value:
                yield from leaves(item)
        elif isinstance(value, str):
            yield value
    assert all(normalize(value) != normalize(get_service().label(target)) for value in leaves(body))


def _post(client, url, **payload):
    response = client.post(url, payload, content_type="application/json")
    assert response.status_code == 200, response.content
    return response.json()


def test_exact_retired_dust_payload_is_the_only_projection_row_change():
    live = [(t.surface, t.anchor_id, t.domain, t.rank_penalty, t.mapping_kind, t.public_id)
            for t in P.PROJECTION_TERMS]
    historical = before_v90_projection_rows(live)
    assert len(live) == CURRENT_CONTENT.projection_terms == 464
    assert len(historical) == 465 and len({row[2] for row in live}) == 26
    assert [row for row in historical if row[0] != "praf"] == live
    assert historical[314] == ("praf", EARTH, "peisaj", 1, "explicit", RETIRED)
    assert P.resolve_projection("praf") is None and "praf" not in P.PROJECTION_INDEX
    assert all(term.public_id != RETIRED for term in P.suggest_projection("prafzz"))
    assert get_service().resolve("praf") == DUST
    assert "praf" in P._EXISTING_KG_SURFACES and "praf" not in P.PROJECTION_NEIGHBORHOODS
    old_policies = before_v90_projection_neighborhoods(P.PROJECTION_NEIGHBORHOODS)
    assert {key: value for key, value in old_policies.items() if key != "praf"} == (
        P.PROJECTION_NEIGHBORHOODS
    )
    assert asdict(old_policies["praf"]) == {
        "anchor_id": EARTH, "min_strength": 0.6, "include_direct_neighbors": False,
        "exact_target_ids": frozenset(TOOLS[:3]),
    }
    assert len(F.EXACT_TARGET_FEEDBACK_PAIRS) == 11
    assert len(F.COMMON_FEEDBACK_PROXIES) == 71
    assert _sha(F.COMMON_FEEDBACK_PROXIES) == (
        "def769935fe81552daa94f711ee2b5a3b6e777269fcc3a8c98e30c86db3c9e84"
    )
    assert P.NATIVE_PROJECTION_REPLACEMENTS == (
        ("nucă", "ingrediente", "n_v81_food_pantry_nuca"),
        ("drojdie", "ingrediente", "n_v84_food_drojdie"),
        ("scorțișoară", "ingrediente", "n_v85_food_scortisoara"),
        ("cacao", "băuturi", "n_v85_food_cacao"),
    )


@pytest.mark.parametrize("target", TOOLS)
def test_native_dust_forms_are_direct_nonwinning_guesses_and_share_one_attempt(target):
    svc, client = get_service(), Client()
    gid = C.store.create(C._build_session(target, "usor", None))
    url = f"/api/wordgames/contexto/games/{gid}"
    try:
        for word in ("praf", "praful", "  PRAFULUI  "):
            assert svc.resolve(word) == DUST and P.resolve_projection(word) is None
            body = _post(client, url + "/guess", text=word)
            assert body["ok"] and not body["won"] and body["attempts"] == 1
            assert body["guess"]["id"] == DUST and body["guess"]["label"] == "Praf"
            assert body["guess"]["distance"] == 1 and body["guess"]["rank"] > 1
            assert body["guess"]["temperature"] in {"Cald", "Fierbinte"}
            assert body["guess"]["closeness"] < 100
            _private(body, target)
        assert body["feedback"]["kind"] == "repeat"
        assert client.get(url).json()["guesses"] == body["guesses"]
        won = _post(client, url + "/guess", text=svc.label(target))
        assert won["won"] and won["guess"]["id"] == target and won["guess"]["rank"] == 1
    finally:
        C.store.delete(gid)


@pytest.mark.parametrize(("word", "owner"), [
    ("praf de copt", "n_v87_food_praf_copt"),
    ("prafului de copt", "n_v87_food_praf_copt"),
    ("lapte praf", "n_v86_food_lapte_praf"),
    ("laptelui praf", "n_v86_food_lapte_praf"),
    ("pământ", EARTH),
])
def test_named_powders_and_earth_keep_distinct_owners_and_cannot_win_dust(word, owner):
    svc = get_service()
    assert svc.resolve(word) == owner != DUST
    gid = C.store.create(C._build_session(DUST, "usor", None))
    url = f"/api/wordgames/contexto/games/{gid}"
    try:
        body = _post(Client(), url + "/guess", text=word)
        assert body["ok"] and not body["won"] and body["guess"]["id"] == owner
        _private(body, DUST)
    finally:
        C.store.delete(gid)


def test_other_earth_projections_and_unaccepted_powder_senses_are_unchanged():
    for word in ("noroi", "bolovan"):
        term = P.resolve_projection(word)
        assert term is not None and term.anchor_id == EARTH
        for target in (DUST, *TOOLS):
            assert C._projection_anchor_id(get_service(), term, target) == EARTH
    assert get_service().resolve("prafuri") is None
    assert all(node.payload["target"] not in {
        DUST, "n_v90_food_firimitura", "n_v90_textile_scama",
    } for node in get_pack().pool("contexto"))


@pytest.mark.parametrize("target", (*TOOLS, DUST, EARTH))
def test_advisory_dust_typo_keeps_attempts_free_and_never_reveals_the_hidden_answer(target):
    svc = get_service()
    assert svc.resolve("prafzz") is None and svc.resolve_fuzzy("prafzz") is None
    assert "Praf" in svc.suggest("prafzz")
    gid = C.store.create(C._build_session(target, "usor", None))
    url = f"/api/wordgames/contexto/games/{gid}"
    try:
        body = _post(Client(), url + "/guess", text="prafzz")
        assert not body["ok"] and body["attempts"] == 0
        assert ("Praf" in body["suggestions"]) is (target != DUST)
        _private(body, target)
        assert Client().get(url).json()["guesses"] == []
    finally:
        C.store.delete(gid)


def test_confident_dust_typo_requires_confirmation_for_tools_and_wins_its_actual_owner():
    svc, client = get_service(), Client()
    assert svc.resolve_fuzzy("prafuluix") == DUST
    for target in (TOOLS[0], DUST):
        gid = C.store.create(C._build_session(target, "usor", None))
        url = f"/api/wordgames/contexto/games/{gid}"
        try:
            body = _post(client, url + "/guess", text="prafuluix")
            if target != DUST:
                assert body["needs_confirmation"] and body["attempts"] == 0
                assert body["resolved_label"] == "Praf"
                _private(body, target)
                body = _post(client, url + "/guess", text="prafuluix",
                             confirm=body["resolved_token"])
                assert body["ok"] and not body["won"] and body["attempts"] == 1
                assert body["guess"]["id"] == DUST
                _private(body, target)
            else:
                assert body["won"] and body["guess"]["id"] == DUST and body["attempts"] == 1
                assert not body.get("needs_confirmation")
        finally:
            C.store.delete(gid)


def test_custom_graph_without_native_dust_has_no_retired_synthetic_fallback(monkeypatch):
    target = TOOLS[1]
    svc = get_service()
    custom = WordGameService(Graph.from_records([
        {"id": node, "label_ro": svc.label(node), "node_type": "concept",
         "category": "viata_de_roman", "description": "Custom fixture", "salience": 0.8}
        for node in (EARTH, target)
    ], []))
    monkeypatch.setattr(C, "get_service", lambda: custom)
    assert custom.resolve("praf") is None and P.resolve_projection("praf") is None
    gid = C.store.create(C._build_session(target, "usor", None))
    url = f"/api/wordgames/contexto/games/{gid}"
    try:
        body = _post(Client(), url + "/guess", text="praf")
        assert not body["ok"] and not body["won"] and body["attempts"] == 0
        assert body["guesses"] == [] and "Praf" not in body.get("suggestions", [])
        _private(body, target)
    finally:
        C.store.delete(gid)


def test_historical_v89_fixture_restores_native_praf_and_actual_pack_after_teardown(monkeypatch):
    current_ids = {item.id for item in get_pack().pool("contexto")}
    with v89_contexto_snapshot(monkeypatch) as (old_service, old_pack):
        assert old_service.resolve("praf") is None
        assert P.resolve_projection("praf").public_id == RETIRED
        assert old_pack.selectable_count("contexto") == 236
        assert C.get_service() is old_service and C.get_pack() is old_pack
    assert C.get_service().resolve("praf") == DUST and P.resolve_projection("praf") is None
    assert {item.id for item in get_pack().pool("contexto")} == current_ids
    assert C.get_pack().selectable_count("contexto") == CURRENT_CONTENT.contexto_eligible
