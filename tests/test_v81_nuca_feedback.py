"""V81 walnut input, directed recipe feedback, and projection-boundary contracts."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

pytest.importorskip("django")

from django.test import Client  # noqa: E402

from cat_de_roman_esti.graph import Graph  # noqa: E402
from cat_de_roman_esti.wordgames import contexto  # noqa: E402
from cat_de_roman_esti.wordgames.contexto_feedback import (  # noqa: E402
    COMMON_FEEDBACK_PROXIES,
    INGREDIENT_FEEDBACK_POLICIES,
)
from cat_de_roman_esti.wordgames.contexto_projection import (  # noqa: E402
    PROJECTION_NEIGHBORHOODS,
    PROJECTION_TERMS,
    resolve_projection,
)
from cat_de_roman_esti.wordgames.service import WordGameService, get_service  # noqa: E402
from tests.content_history import before_v84_fixture  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import nuca_feedback_v81_data as DATA  # noqa: E402

NUCA = "n_v81_food_pantry_nuca"
MIERE = "n_v24_food_breakfast_miere"
COZONAC = "n_gas_cozonac"
BACLAVA = "n_gas_baclava_dobrogeana"
TARGETS = {
    COZONAC: 0.97,
    "n_v17gas_coliva": 0.97,
    BACLAVA: 0.95,
    "n_v21gas_cornulete": 0.90,
}
_REMOVED_NUCA_ROW = (
    "nucă",
    MIERE,
    "ingrediente",
    1,
    "explicit",
    "ctxp_92113401f76976ac37f7",
)
_V79_ALL_ROWS_SHA256 = "952933753998d1a7a2a024ab40501d7db655b94481350b1977d582437f4f805f"
_V81_OTHER_ROWS_SHA256 = "a422bf531cfadb66ffe3aacc08db8ac51c3cc06e74bb5e9d762f54353d2088a1"


def _rows() -> list[tuple[str, str, str, int, str, str]]:
    return [
        (
            term.surface,
            term.anchor_id,
            term.domain,
            term.rank_penalty,
            term.mapping_kind,
            term.public_id,
        )
        for term in PROJECTION_TERMS
    ]


def _digest(rows: list[tuple[str, str, str, int, str, str]]) -> str:
    return hashlib.sha256(
        json.dumps(rows, ensure_ascii=False, separators=(",", ":")).encode()
    ).hexdigest()


def _private_game(target: str, *, category: str | None = None) -> tuple[Client, str]:
    game_id = contexto.store.create(
        contexto._build_session(target, "usor", None, category=category)
    )
    return Client(), f"/api/wordgames/contexto/games/{game_id}"


def _guess(client: Client, url: str, text: str) -> dict:
    response = client.post(url + "/guess", {"text": text}, content_type="application/json")
    assert response.status_code == 200
    return response.json()


def _assert_hidden(body: dict, target: str) -> None:
    svc = get_service()
    assert "target" not in body and "solution" not in body and "anchor_id" not in str(body)
    assert target not in str(body) and svc.label(target) not in str(body)


def _node(node_id: str) -> dict[str, str]:
    return {"id": node_id, "label_ro": node_id, "category": "gastronomie"}


def _edge(
    edge_id: str,
    src: str,
    dst: str,
    *,
    strength: float = 0.90,
    relation: str = "part_of",
    label: str = "ingredient pentru",
    distractor: bool = False,
) -> dict:
    return {
        "id": edge_id,
        "src_id": src,
        "dst_id": dst,
        "relation": relation,
        "label_ro": label,
        "strength": strength,
        "bidirectional": False,
        "is_distractor": distractor,
    }


def test_nuca_has_only_the_reviewed_native_surface_and_direct_recipe_edges() -> None:
    svc = get_service()
    fixture = json.loads((ROOT / "cat_de_roman_esti/fixtures/kg_sample.json").read_bytes())
    node = next(item for item in fixture["kg_nodes"] if item["id"] == NUCA)
    assert (node["node_type"], node["label_ro"], node["category"], node["salience"]) == (
        "concept", "Nucă", "gastronomie", 0.90,
    )
    assert node.get("aliases") == ["nucile"]
    assert {svc.resolve(surface) for surface in ("Nucă", "nuca", "nucile")} == {NUCA}
    assert all(svc.resolve(surface) is None for surface in (
        "nuci", "nucii", "nucilor", "nuc", "nucul", "nucului", "miez de nucă", "nucă de cocos",
    ))
    assert all(svc.resolve_fuzzy(surface) is None for surface in (
        "nuci", "nucii", "nucilor", "nuc", "nucul", "nucului", "miez de nucă", "nucă de cocos",
    ))
    assert resolve_projection("nucă") is None

    actual = {target: svc.link(NUCA, target) for target in TARGETS}
    assert set(svc.neighbor_ids(NUCA)) == set(TARGETS)
    assert svc.predecessor_ids(NUCA) == []
    for target, strength in TARGETS.items():
        edge = actual[target]
        assert edge is not None
        assert (
            edge.relation, edge.label_ro, edge.strength, edge.bidirectional, edge.is_distractor
        ) == (
            "part_of", "ingredient pentru", strength, False, False,
        )
        assert svc.link(target, NUCA) is None


def test_nuca_projection_removal_preserves_every_other_v79_row_and_policy() -> None:
    from tests.content_history import before_v84_projection_rows

    rows = before_v84_projection_rows(_rows())
    assert len(rows) == 472
    assert _REMOVED_NUCA_ROW not in rows
    assert _digest(rows) == _V81_OTHER_ROWS_SHA256
    restored = [*rows]
    restored.insert(35, _REMOVED_NUCA_ROW)
    assert _digest(restored) == _V79_ALL_ROWS_SHA256
    assert len(COMMON_FEEDBACK_PROXIES) == 71 and NUCA not in COMMON_FEEDBACK_PROXIES
    assert set(INGREDIENT_FEEDBACK_POLICIES) == {NUCA}
    policy = INGREDIENT_FEEDBACK_POLICIES[NUCA]
    assert (policy.fallback_anchor_id, policy.min_strength) == (MIERE, 0.90)
    assert set(PROJECTION_NEIGHBORHOODS) == {"gem", "burta"}


def test_native_ingredient_policy_requires_direct_direction_strength_relation_and_label() -> None:
    names = (NUCA, MIERE, "good", "weak", "reverse", "decoy", "wrong_relation", "wrong_label")
    graph = Graph.from_records(
        [_node(name) for name in names],
        [
            _edge("e1", NUCA, "good"),
            _edge("e2", NUCA, "weak", strength=0.89),
            _edge("e3", "reverse", NUCA),
            _edge("e4", NUCA, "decoy", distractor=True),
            _edge("e5", NUCA, "wrong_relation", relation="related_to"),
            _edge("e6", NUCA, "wrong_label", label="are nucă"),
        ],
    )
    svc = WordGameService(graph)
    assert contexto._feedback_anchor_id(svc, NUCA, NUCA) == NUCA
    assert contexto._feedback_anchor_id(svc, NUCA, "good") == NUCA
    for target in ("weak", "reverse", "decoy", "wrong_relation", "wrong_label"):
        assert contexto._feedback_anchor_id(svc, NUCA, target) == MIERE


def test_cozonac_nuca_is_hot_private_repeat_safe_and_exact_cozonac_wins() -> None:
    client, url = _private_game(COZONAC)
    try:
        first = _guess(client, url, "nuca")
        assert first["ok"] is True and first["won"] is False and first["attempts"] == 1
        assert first["guess"] == {
            "id": NUCA, "label": "Nucă", "distance": 1, "rank": 2,
            "temperature": "Fierbinte", "closeness": 99, "attempt_number": 1,
        }
        _assert_hidden(first, COZONAC)
        resumed = client.get(url).json()
        assert resumed["attempts"] == 1 and resumed["guesses"] == first["guesses"]
        repeated = _guess(client, url, " NUCILE ")
        assert repeated["attempts"] == 1 and repeated["feedback"]["kind"] == "repeat"
        won = _guess(client, url, "cozonacul")
        assert won["won"] is True and won["guess"]["id"] == COZONAC and won["attempts"] == 2
    finally:
        contexto.store.delete(url.rsplit("/", 1)[-1])


def test_baclava_receives_native_hot_feedback_without_a_win() -> None:
    client, url = _private_game(BACLAVA)
    try:
        response = _guess(client, url, "Nucă")
        assert response["won"] is False
        assert (
            response["guess"]["id"],
            response["guess"]["distance"],
            response["guess"]["rank"],
            response["guess"]["temperature"],
        ) == (
            NUCA, 1, 2, "Fierbinte",
        )
        _assert_hidden(response, BACLAVA)
    finally:
        contexto.store.delete(url.rsplit("/", 1)[-1])


def test_baclava_warm_clue_uses_nuca_without_disclosing_a_hidden_nuca_target() -> None:
    client, url = _private_game(BACLAVA, category="gastronomie")
    try:
        for guess in ("fotbal", "stilou", "curcubeu"):
            response = _guess(client, url, guess)
            assert response["won"] is False
        clue_response = client.post(url + "/clue")
        assert clue_response.status_code == 200
        clue = clue_response.json()
        assert clue["clue_kind"] == "warmer"
        assert clue["word"]["label"] == "Nucă" and clue["word"]["rank"] == 2
        _assert_hidden(clue, BACLAVA)

        replayed = _guess(client, url, clue["word"]["label"])
        assert replayed["won"] is False
        assert (replayed["guess"]["id"], replayed["guess"]["rank"]) == (NUCA, 2)
        _assert_hidden(replayed, BACLAVA)
    finally:
        contexto.store.delete(url.rsplit("/", 1)[-1])

    hidden_nuca = contexto._build_session(NUCA, "usor", None, category="gastronomie")
    own_clue = contexto._warmer_clue_candidate(hidden_nuca)
    assert own_clue is None or get_service().resolve(own_clue.label) != NUCA


@pytest.mark.parametrize(
    ("target", "distance", "rank", "temperature", "closeness"),
    [
        ("n_gas_toba", 4, 246, "Rece", 89),
        ("n_gas_ciorba_radauteana", 5, 1486, "Foarte rece", 35),
        ("n_marea_neagra", 5, 1815, "Inghetat", 21),
    ],
)
@pytest.mark.parametrize("graph_epoch", ("before_v84", "current"))
def test_nuca_keeps_miere_baseline_feedback_outside_its_recipe_zone(
    target: str, distance: int, rank: int, temperature: str, closeness: int,
    graph_epoch: str, monkeypatch,
) -> None:
    if graph_epoch == "before_v84":
        prior = before_v84_fixture(json.loads(
            (ROOT / "cat_de_roman_esti/fixtures/kg_sample.json").read_bytes()
        ))
        svc = WordGameService(Graph.from_records(prior["kg_nodes"], prior["kg_edges"]))
        monkeypatch.setattr(contexto, "get_service", lambda: svc)
    client, url = _private_game(target)
    try:
        response = _guess(client, url, "nucă")
        guess = response["guess"]
        assert response["won"] is False and guess["id"] == NUCA
        if graph_epoch == "before_v84":
            assert (guess["distance"], guess["temperature"], guess["closeness"]) == (
                distance, temperature, closeness,
            )
            assert guess["rank"] in {rank, rank + 1}
        else:
            honey = _guess(client, url, "miere")["guess"]
            assert guess["distance"] == honey["distance"] == distance
            assert guess["temperature"] == honey["temperature"] == temperature
            assert guess["rank"] == honey["rank"] + 1
            assert 0 <= honey["closeness"] - guess["closeness"] <= 1
        _assert_hidden(response, target)
    finally:
        contexto.store.delete(url.rsplit("/", 1)[-1])


def test_miere_target_stays_private_nonwinning_while_exact_nuca_target_wins() -> None:
    client, url = _private_game(MIERE)
    try:
        response = _guess(client, url, "nucă")
        assert response["ok"] is True and response["won"] is False
        assert response["guess"]["id"] == NUCA and response["guess"]["rank"] >= 2
        _assert_hidden(response, MIERE)
    finally:
        contexto.store.delete(url.rsplit("/", 1)[-1])

    client, url = _private_game(NUCA)
    try:
        won = _guess(client, url, "nucile")
        assert won["won"] is True and won["guess"]["id"] == NUCA and won["guess"]["rank"] == 1
    finally:
        contexto.store.delete(url.rsplit("/", 1)[-1])


def test_nuci_suggestion_is_available_only_when_nuca_cannot_be_the_secret() -> None:
    for target, expect_nuca in ((COZONAC, True), (NUCA, False), (MIERE, False)):
        client, url = _private_game(target)
        try:
            response = _guess(client, url, "nuci")
            assert response["ok"] is False and response["attempts"] == 0
            assert ("Nucă" in response["suggestions"]) is expect_nuca
            if not expect_nuca:
                _assert_hidden(response, target)
        finally:
            contexto.store.delete(url.rsplit("/", 1)[-1])


@pytest.mark.parametrize("typo", ("nucilee", "nucilex"))
def test_true_nuca_typos_hide_private_confirmation_but_confirm_for_an_unrelated_target(
    typo: str,
) -> None:
    for target, expect_confirmation in ((NUCA, False), (MIERE, False), (COZONAC, True)):
        client, url = _private_game(target)
        try:
            response = _guess(client, url, typo)
            assert response.get("needs_confirmation", False) is expect_confirmation
            if expect_confirmation:
                assert response["resolved_label"] == "Nucă"
                assert response["attempts"] == 0 and response["won"] is False
                _assert_hidden(response, COZONAC)
            else:
                assert "resolved_label" not in response and "resolved_token" not in response
                if target == NUCA:
                    # A high-confidence typo may complete the real answer, but is never a
                    # confirmation disclosure path.
                    assert response["won"] is True and response["guess"]["id"] == NUCA
                else:
                    assert response["won"] is False and response["attempts"] == 0
                    _assert_hidden(response, MIERE)
        finally:
            contexto.store.delete(url.rsplit("/", 1)[-1])


def test_data_module_stays_bound_to_the_one_node_four_edge_proposal() -> None:
    batch = DATA.build_nodes_and_edges()
    assert DATA.BUILD_VERSION == "fixture-v81-nuca-feedback"
    assert DATA.NEW_NODE_IDS == (NUCA,) and DATA.GAME_ITEM_IDS == ()
    assert [node["id"] for node in batch["nodes"]] == [NUCA]
    assert batch["aliases"] == {}
    assert {(edge["src"], edge["dst"], edge["strength"]) for edge in batch["edges"]} == {
        (NUCA, target, strength) for target, strength in TARGETS.items()
    }
    assert DATA.INTUITIVE_PAIRS == tuple((NUCA, target) for target in TARGETS)
