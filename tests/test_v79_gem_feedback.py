"""V79: Gem has dessert-local Contexto feedback without becoming a global synonym."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from tests.current_content import CURRENT_CONTENT

pytest.importorskip("django")

from django.test import Client  # noqa: E402

from cat_de_roman_esti.graph import Graph  # noqa: E402
from cat_de_roman_esti.wordgames import contexto, lant  # noqa: E402
from cat_de_roman_esti.wordgames.contexto_projection import (  # noqa: E402
    PROJECTION_NEIGHBORHOODS,
    PROJECTION_TERMS,
    resolve_projection,
    suggest_projection,
)
from cat_de_roman_esti.wordgames.service import WordGameService, get_service  # noqa: E402
from tests.content_history import before_v81_projection_rows  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CLATITE = "n_v3gas_clatite"
DULCEATA = "n_v17gas_dulceata"
MIERE = "n_v24_food_breakfast_miere"
UNT = "n_v24_food_breakfast_unt"
SOCATA = "n_v18gas_socata"
GEM_PUBLIC_ID = "ctxp_fab0f46e7bcd5932442e"
_ALL_BASELINE_PROJECTIONS_SHA256 = (
    "952933753998d1a7a2a024ab40501d7db655b94481350b1977d582437f4f805f"
)
ARTIFACT_SHA256 = {
    "cat_de_roman_esti/fixtures/kg_sample.json": (
        CURRENT_CONTENT.kg_sha256
    ),
    "cat_de_roman_esti/fixtures/games_pack.json": (
        CURRENT_CONTENT.pack_sha256
    ),
    "cat_de_roman_esti/fixtures/board_rankings_v37.json": (
        CURRENT_CONTENT.rankings_sha256
    ),
    "cat_de_roman_esti/fixtures/derived_catalog_v38.json": (
        CURRENT_CONTENT.derived_sha256
    ),
    "tests/fixtures/cat_mobile_app_pack_contract.json": (
        CURRENT_CONTENT.mobile_sha256
    ),
}


def _projection_rows() -> list[tuple[str, str, str, int, str, str]]:
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


def _assert_secret_hidden(body: dict, target: str) -> None:
    svc = get_service()
    assert "target" not in body and "solution" not in body
    assert target not in str(body)
    assert svc.label(target) not in str(body)


def _contexto_game(target: str) -> tuple[Client, str]:
    game_id = contexto.store.create(contexto._build_session(target, "usor", None))
    return Client(), f"/api/wordgames/contexto/games/{game_id}"


def _guess(client: Client, url: str, text: str) -> dict:
    return client.post(
        url + "/guess", {"text": text}, content_type="application/json"
    ).json()


def _node(node_id: str) -> dict[str, str]:
    return {"id": node_id, "label_ro": node_id, "category": "test"}


def _edge(edge_id: str, src: str, dst: str, strength: float, *, distractor=False) -> dict:
    return {
        "id": edge_id,
        "src_id": src,
        "dst_id": dst,
        "relation": "related_to",
        "strength": strength,
        "bidirectional": False,
        "is_distractor": distractor,
    }


def test_gem_preserves_all_baseline_fields_and_has_one_local_policy() -> None:
    gem = resolve_projection("gem")
    nuca = resolve_projection("nucă")
    aluna = resolve_projection("alună")
    assert gem is not None and nuca is None and aluna is not None
    assert get_service().resolve("nucă") == "n_v81_food_pantry_nuca"
    assert (
        gem.surface,
        gem.key,
        gem.domain,
        gem.anchor_id,
        gem.rank_penalty,
        gem.mapping_kind,
        gem.public_id,
    ) == (
        "gem",
        "gem",
        "ingrediente",
        MIERE,
        1,
        "explicit",
        GEM_PUBLIC_ID,
    )
    assert aluna.anchor_id == MIERE
    blob = json.dumps(
        before_v81_projection_rows(_projection_rows()), ensure_ascii=False, separators=(",", ":")
    ).encode()
    assert hashlib.sha256(blob).hexdigest() == _ALL_BASELINE_PROJECTIONS_SHA256
    assert set(PROJECTION_NEIGHBORHOODS) == {"gem", "burta"}
    policy = PROJECTION_NEIGHBORHOODS["gem"]
    assert (policy.anchor_id, policy.min_strength) == (DULCEATA, 0.60)
    assert policy.include_direct_neighbors is True


def test_gem_neighborhood_requires_strong_direct_non_distractor_edge() -> None:
    gem = resolve_projection("gem")
    assert gem is not None
    nodes = [_node(node_id) for node_id in (MIERE, DULCEATA, "strong", "weak", "reverse", "decoy")]
    graph = Graph.from_records(
        nodes,
        [
            _edge("e1", DULCEATA, "strong", 0.60),
            _edge("e2", DULCEATA, "weak", 0.59),
            _edge("e3", "reverse", DULCEATA, 1.0),
            _edge("e4", DULCEATA, "decoy", 1.0, distractor=True),
        ],
    )
    svc = WordGameService(graph)
    assert contexto._projection_anchor_id(svc, gem, DULCEATA) == DULCEATA
    assert contexto._projection_anchor_id(svc, gem, "strong") == DULCEATA
    assert contexto._projection_anchor_id(svc, gem, "weak") == MIERE
    assert contexto._projection_anchor_id(svc, gem, "reverse") == MIERE
    assert contexto._projection_anchor_id(svc, gem, "decoy") == MIERE
    missing_anchor = WordGameService(Graph.from_records([_node(MIERE), _node("target")], []))
    assert contexto._projection_anchor_id(missing_anchor, gem, "target") == MIERE


def test_gem_effective_dulceata_neighborhood_is_exactly_the_reviewed_six() -> None:
    gem = resolve_projection("gem")
    assert gem is not None
    svc = get_service()
    effective_targets = {
        node_id
        for node_id in svc.all_ids()
        if contexto._projection_anchor_id(svc, gem, node_id) == DULCEATA
    }
    assert effective_targets == {
        DULCEATA,
        "n_gas_papanasi",
        "n_v11gas_magiun_topoloveni",
        "n_v2gas_conserve_iarna",
        CLATITE,
        "n_v4gas_fruct",
    }
    assert SOCATA not in effective_targets


def test_gem_is_hot_for_clatite_and_repeats_survive_resume() -> None:
    client, url = _contexto_game(CLATITE)
    try:
        first = _guess(client, url, "gem")
        assert first["ok"] is True and first["won"] is False and first["attempts"] == 1
        assert first["guess"] == {
            "id": GEM_PUBLIC_ID,
            "label": "Gem",
            "distance": 1,
            "rank": 8,
            "temperature": "Fierbinte",
            "closeness": 99,
            "attempt_number": 1,
        }
        _assert_secret_hidden(first, CLATITE)
        assert "anchor_id" not in str(first)
        assert DULCEATA not in str(first)
        assert get_service().label(DULCEATA) not in str(first)
        resumed = client.get(url).json()
        assert resumed["attempts"] == 1 and resumed["guesses"] == first["guesses"]
        repeated = _guess(client, url, " GEM ")
        assert repeated["attempts"] == 1
        assert repeated["feedback"]["kind"] == "repeat"
    finally:
        contexto.store.delete(url.rsplit("/", 1)[-1])


def test_gem_never_wins_when_its_private_anchor_is_the_target() -> None:
    client, url = _contexto_game(DULCEATA)
    try:
        projected = _guess(client, url, "gem")
        assert projected["ok"] is True
        assert projected["won"] is False and projected["attempts"] == 1
        assert projected["guess"]["id"] == GEM_PUBLIC_ID
        assert projected["guess"]["rank"] >= 2
        assert projected["guess"]["closeness"] < 100
        _assert_secret_hidden(projected, DULCEATA)
        exact = _guess(client, url, "dulceață")
        assert exact["won"] is True
        assert exact["guess"]["id"] == DULCEATA
        assert exact["guess"]["rank"] == 1
    finally:
        contexto.store.delete(url.rsplit("/", 1)[-1])


def test_gem_typo_suggestion_follows_the_effective_anchor_privacy() -> None:
    terms = suggest_projection("gemm")
    assert [term.label for term in terms] == ["Gem"]

    for target, expect_gem in ((CLATITE, True), (MIERE, False), (DULCEATA, False)):
        client, url = _contexto_game(target)
        try:
            response = _guess(client, url, "gemm")
            assert response["ok"] is False and response["attempts"] == 0
            assert ("Gem" in response["suggestions"]) is expect_gem
            if not expect_gem:
                assert "Dulceață" not in response["suggestions"]
                _assert_secret_hidden(response, target)
        finally:
            contexto.store.delete(url.rsplit("/", 1)[-1])


@pytest.mark.parametrize(
    ("target", "distance", "rank", "temperature", "closeness"),
    [
        ("n_gas_muraturi", 4, 623, "Rece", 73),
        ("n_gas_gratar_1_mai", 5, 1619, "Inghetat", 29),
        ("n_gas_ciorba_radauteana", 5, 1487, "Foarte rece", 35),
        ("n_gas_salata_boeuf", 5, 1041, "Foarte rece", 55),
    ],
)
def test_gem_keeps_cold_feedback_for_unrelated_food_targets(
    target: str, distance: int, rank: int, temperature: str, closeness: int
) -> None:
    client, url = _contexto_game(target)
    try:
        response = _guess(client, url, "gem")
        assert response["ok"] is True and response["won"] is False
        assert response["guess"] == {
            "id": GEM_PUBLIC_ID,
            "label": "Gem",
            "distance": distance,
            "rank": rank,
            "temperature": temperature,
            "closeness": closeness,
            "attempt_number": 1,
        }
    finally:
        contexto.store.delete(url.rsplit("/", 1)[-1])


def test_gem_falls_back_to_miere_for_weak_socata_link() -> None:
    gem = resolve_projection("gem")
    assert gem is not None
    svc = get_service()
    assert svc.exists(SOCATA)
    assert contexto._projection_anchor_id(svc, gem, SOCATA) == MIERE


def test_exact_miere_and_unt_stay_kg_words_and_lant_rejects_gem() -> None:
    svc = get_service()
    assert svc.resolve("miere") == MIERE and svc.resolve("unt") == UNT
    assert resolve_projection("miere") is None and resolve_projection("unt") is None
    start = svc.predecessor_ids(DULCEATA)[0]
    game_id = lant.store.create(
        lant.LantSession(start=start, target=DULCEATA, optimal=1, chain=[start])
    )
    try:
        client = Client()
        before = client.get(f"/api/wordgames/lant/games/{game_id}").json()
        response = client.post(
            f"/api/wordgames/lant/games/{game_id}/move",
            {"text": "gem"},
            content_type="application/json",
        ).json()
        assert response["ok"] is False
        assert lant._resolve_neighbor("gem", start, DULCEATA) is None
        assert client.get(f"/api/wordgames/lant/games/{game_id}").json() == before
    finally:
        lant.store.delete(game_id)


def test_v79_keeps_all_served_artifact_bytes_pinned() -> None:
    actual = {
        relative: hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
        for relative in ARTIFACT_SHA256
    }
    assert actual == ARTIFACT_SHA256
