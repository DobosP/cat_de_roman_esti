"""V83 food associations improve six exact rounds while preserving input identity."""

from __future__ import annotations

import hashlib
import json

import pytest

pytest.importorskip("django")

from django.test import Client  # noqa: E402

from cat_de_roman_esti.graph import Graph  # noqa: E402
from cat_de_roman_esti.wordgames import contexto as C  # noqa: E402
from cat_de_roman_esti.wordgames.contexto_feedback import (  # noqa: E402
    COMMON_FEEDBACK_PROXIES,
    EXACT_TARGET_FEEDBACK_PAIRS,
    INGREDIENT_FEEDBACK_POLICIES,
)
from cat_de_roman_esti.wordgames.contexto_projection import (  # noqa: E402
    PROJECTION_NEIGHBORHOODS,
    PROJECTION_TERMS,
    resolve_projection,
)
from cat_de_roman_esti.wordgames.service import WordGameService, get_service  # noqa: E402
from tests.content_history import before_v84_projection_rows  # noqa: E402

ULEI = "n_v24_food_pantry_ulei"
SARE = "n_v4gas_sare"
ARDEI = "n_v24_food_salad_veg_ardei"
GOGOSI = "n_v17gas_gogosi"
CARTOFI = "n_v3gas_cartofi_prajiti"
TELEMEA = "n_gas_telemea"
ARDEI_UMPLUTI = "n_gas_ardei_umpluti"
CORNULETE = "n_v21gas_cornulete"
DULCEATA = "n_v17gas_dulceata"
MIERE = "n_v24_food_breakfast_miere"
GEM_ID = "ctxp_fab0f46e7bcd5932442e"
NATIVE_TARGETS = {ULEI: {GOGOSI, CARTOFI}, SARE: {TELEMEA}, ARDEI: {ARDEI_UMPLUTI}}
ASSOCIATIONS = (
    ("gem", GEM_ID, CORNULETE, "gemm"),
    ("gem", GEM_ID, GOGOSI, "gemm"),
    ("ulei", ULEI, GOGOSI, "uleiu"),
    ("ulei", ULEI, CARTOFI, "uleiu"),
    ("sare", SARE, TELEMEA, "sareee"),
    ("ardei", ARDEI, ARDEI_UMPLUTI, "arrdei"),
)


def _game(target: str) -> tuple[Client, str]:
    session = C._build_session(target, "usor", None, category="gastronomie")
    game_id = C.store.create(session)
    return Client(), f"/api/wordgames/contexto/games/{game_id}"


def _guess(client: Client, url: str, text: str) -> dict:
    response = client.post(url + "/guess", {"text": text}, content_type="application/json")
    assert response.status_code == 200
    return response.json()


def _hidden(response: dict, target: str) -> None:
    assert "target" not in response and "solution" not in response
    assert target not in str(response) and get_service().label(target) not in str(response)
    assert "anchor_id" not in str(response)


def _digest(value) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def test_projection_inventory_and_prior_policies_remain_exact():
    rows = before_v84_projection_rows([
        (term.surface, term.anchor_id, term.domain, term.rank_penalty,
         term.mapping_kind, term.public_id)
        for term in PROJECTION_TERMS
    ])
    assert len(rows) == 472
    assert _digest(rows) == "a422bf531cfadb66ffe3aacc08db8ac51c3cc06e74bb5e9d762f54353d2088a1"
    assert len(COMMON_FEEDBACK_PROXIES) == 71
    assert _digest(COMMON_FEEDBACK_PROXIES) == (
        "def769935fe81552daa94f711ee2b5a3b6e777269fcc3a8c98e30c86db3c9e84"
    )
    assert set(INGREDIENT_FEEDBACK_POLICIES) == {"n_v81_food_pantry_nuca"}
    nuca = INGREDIENT_FEEDBACK_POLICIES["n_v81_food_pantry_nuca"]
    assert (nuca.fallback_anchor_id, nuca.min_strength) == (MIERE, 0.90)
    assert isinstance(EXACT_TARGET_FEEDBACK_PAIRS, frozenset)
    assert EXACT_TARGET_FEEDBACK_PAIRS == frozenset(
        (source, target) for source, targets in NATIVE_TARGETS.items() for target in targets
    )
    assert set(PROJECTION_NEIGHBORHOODS) == {"gem", "burta"}
    gem = PROJECTION_NEIGHBORHOODS["gem"]
    assert (gem.anchor_id, gem.min_strength, gem.include_direct_neighbors) == (DULCEATA, 0.60, True)
    assert gem.exact_target_ids == frozenset({CORNULETE, GOGOSI})
    assert isinstance(gem.exact_target_ids, frozenset)
    burta = PROJECTION_NEIGHBORHOODS["burta"]
    assert (burta.anchor_id, burta.min_strength, burta.include_direct_neighbors,
            burta.exact_target_ids) == ("n_gas_ciorba_burta", 0.60, False, frozenset())


def test_feedback_changes_are_closed_over_every_kg_target():
    svc = get_service()
    for source, expected_targets in NATIVE_TARGETS.items():
        changed = {
            target for target in svc.all_ids()
            if C._feedback_anchor_id(svc, source, target) != source
        }
        assert changed == expected_targets
        assert all(C._feedback_anchor_id(svc, source, target) == target for target in changed)
        assert C._feedback_anchor_id(svc, source, source) == source
    gem = resolve_projection("gem")
    assert gem is not None
    prior_neighborhood = {
        DULCEATA, "n_gas_papanasi", "n_v11gas_magiun_topoloveni",
        "n_v2gas_conserve_iarna", "n_v3gas_clatite", "n_v4gas_fruct",
    }
    for target in svc.all_ids():
        expected = (
            target if target in {CORNULETE, GOGOSI}
            else DULCEATA if target in prior_neighborhood else MIERE
        )
        assert C._projection_anchor_id(svc, gem, target) == expected


@pytest.mark.parametrize("surface,public_id,target,typo", ASSOCIATIONS)
def test_six_associations_are_hot_nonwinning_repeatable_and_resume_exactly(
    surface, public_id, target, typo,
):
    client, url = _game(target)
    try:
        first = _guess(client, url, surface)
        assert first["ok"] is True and first["won"] is False and first["attempts"] == 1
        guess = first["guess"]
        assert (guess["id"], guess["rank"], guess["temperature"], guess["distance"]) == (
            public_id, 2, "Fierbinte", 1,
        )
        assert guess["closeness"] < 100
        _hidden(first, target)
        repeated = _guess(client, url, " " + surface.upper() + " ")
        assert repeated["guess"] == guess and repeated["attempts"] == 1
        assert repeated["feedback"]["kind"] == "repeat"
        resumed = client.get(url).json()
        assert resumed["attempts"] == 1 and resumed["guesses"] == first["guesses"]
        _hidden(resumed, target)
        won = _guess(client, url, get_service().label(target))
        assert won["won"] is True and won["attempts"] == 2
        assert (won["guess"]["id"], won["guess"]["rank"]) == (target, 1)
    finally:
        C.store.delete(url.rsplit("/", 1)[-1])


@pytest.mark.parametrize("surface,public_id,target,typo", ASSOCIATIONS)
def test_unknown_or_fuzzy_input_never_suggests_the_exact_target_proxy(
    surface, public_id, target, typo,
):
    svc = get_service()
    assert svc.resolve(typo) is None
    # Oil and pepper exercise confident fuzzy correction as well as suggestion
    # filtering. Salt and jam exercise the ordinary unknown-input suggestion path.
    if surface in {"ulei", "ardei"}:
        assert svc.resolve_fuzzy(typo) == public_id
    client, url = _game(target)
    try:
        response = _guess(client, url, typo)
        assert response["ok"] is False and response["attempts"] == 0
        assert not response.get("needs_confirmation")
        assert "resolved_label" not in response
        assert surface.capitalize() not in response["suggestions"]
        assert public_id not in str(response)
        _hidden(response, target)
        resumed = client.get(url).json()
        assert resumed["attempts"] == 0 and resumed["guesses"] == []
    finally:
        C.store.delete(url.rsplit("/", 1)[-1])


@pytest.mark.parametrize("target,expected_label", [
    (GOGOSI, "Ulei"), (CARTOFI, "Ulei"), (TELEMEA, "Brânză"), (ARDEI_UMPLUTI, "Ardei"),
])
def test_native_proxy_warmer_clues_are_deterministic_and_reproduce_their_rank(
    target, expected_label,
):
    observed = []
    for _ in range(2):
        client, url = _game(target)
        try:
            for word in ("fotbal", "stilou", "curcubeu"):
                assert _guess(client, url, word)["won"] is False
            clue_response = client.post(url + "/clue")
            assert clue_response.status_code == 200
            clue = clue_response.json()
            assert clue["clue_kind"] == "warmer"
            assert (clue["word"]["label"], clue["word"]["rank"]) == (expected_label, 2)
            _hidden(clue, target)
            observed.append(clue["word"])
            replayed = _guess(client, url, clue["word"]["label"])
            assert replayed["won"] is False and replayed["guess"]["rank"] == clue["word"]["rank"]
            _hidden(replayed, target)
        finally:
            C.store.delete(url.rsplit("/", 1)[-1])
    assert observed[0] == observed[1]


def _service(ids: list[str], edges: list[tuple[str, str]] | None = None) -> WordGameService:
    return WordGameService(Graph.from_records(
        [{"id": node, "label_ro": node, "category": "test"} for node in ids],
        [
            {"id": f"e{index}", "src_id": source, "dst_id": target,
             "relation": "related_to", "strength": 1.0, "bidirectional": True}
            for index, (source, target) in enumerate(edges or [])
        ],
    ))


def test_native_pairs_require_both_nodes_and_do_not_expand_through_neighbors():
    for source, targets in NATIVE_TARGETS.items():
        for target in targets:
            svc = _service([source, target, "neighbor"], [(target, "neighbor")])
            assert C._feedback_anchor_id(svc, source, target) == target
            assert C._feedback_anchor_id(svc, source, "neighbor") == source
            assert C._feedback_anchor_id(svc, target, source) == target
            assert C._feedback_anchor_id(_service([target]), source, target) == source
            assert C._feedback_anchor_id(_service([source]), source, target) == source
            assert C._feedback_anchor_id(svc, source, source) == source


def test_gem_exact_targets_require_existing_dulceata_anchor_and_target():
    gem = resolve_projection("gem")
    assert gem is not None
    for target in (CORNULETE, GOGOSI):
        svc = _service([DULCEATA, MIERE, target, "neighbor"], [(target, "neighbor")])
        assert C._projection_anchor_id(svc, gem, target) == target
        assert C._projection_anchor_id(svc, gem, "neighbor") == MIERE
        assert C._projection_anchor_id(_service([MIERE, target]), gem, target) == MIERE
        assert C._projection_anchor_id(_service([MIERE, DULCEATA]), gem, target) == MIERE
