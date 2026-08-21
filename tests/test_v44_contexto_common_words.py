"""Regression guards for the strict V44 Cald sau Rece common-word repair."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import pytest

pytest.importorskip("django")

from django.test import Client  # noqa: E402

from cat_de_roman_esti.data import load_fixture  # noqa: E402
from cat_de_roman_esti.wordgames.contexto import (  # noqa: E402
    _build_session,
    _score_feedback,
    _warmer_clue_candidate,
    rank_for,
    store,
)
from cat_de_roman_esti.wordgames.contexto_feedback import (  # noqa: E402
    COMMON_FEEDBACK_PROXIES,
)
from cat_de_roman_esti.wordgames.contexto_projection import (  # noqa: E402
    PROJECTION_TERMS,
    resolve_projection,
)
from cat_de_roman_esti.wordgames.service import WordGameService, get_service  # noqa: E402

_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS = _ROOT / "scripts"
sys.path.insert(0, str(_SCRIPTS))

import basic_words_v30_data as V30_DATA  # noqa: E402
import basic_words_v31_data as V31_DATA  # noqa: E402
import basic_words_v32_data as V32_DATA  # noqa: E402
import basic_words_v33_data as V33_DATA  # noqa: E402
import contexto_common_words_v44_data as DATA  # noqa: E402
import critique_pack  # noqa: E402

_PACKAGE_KG = _ROOT / "cat_de_roman_esti" / "fixtures" / "kg_sample.json"
_TEST_KG = _ROOT / "tests" / "fixtures" / "kg_sample.json"
_PACKAGE_PACK = _ROOT / "cat_de_roman_esti" / "fixtures" / "games_pack.json"
_TEST_PACK = _ROOT / "tests" / "fixtures" / "games_pack.json"
_PACKAGE_RANKINGS = (
    _ROOT / "cat_de_roman_esti" / "fixtures" / "board_rankings_v37.json"
)
_PACKAGE_DEMOTIONS = (
    _ROOT / "cat_de_roman_esti" / "fixtures" / "contexto_demotions_v44.json"
)
_TEST_DEMOTIONS = _ROOT / "tests" / "fixtures" / "contexto_demotions_v44.json"
_REVIEW = _ROOT / "docs" / "reviews" / "v44-contexto-vocabulary.json"
_GATE_DIR = _ROOT / "docs" / "reviews" / "v44-final-gate"

_NEW_PROJECTIONS = {
    "bluză": "n_v29_clothing_everyday_haina",
    "blugi": "n_v30_clothing_everyday_pantaloni",
    "jachetă": "n_v30_clothing_outer_geaca",
    "vestă": "n_v29_clothing_everyday_haina",
    "chiflă": "n_v4gas_paine",
    "piure de cartofi": "n_v2lim_cartof",
    "plapumă": "n_v24_home_textiles_patura",
    "garaj": "n_v24_transport_personal_masina",
    "claxon": "n_v24_transport_personal_masina",
    "oglindă retrovizoare": "n_v24_transport_personal_masina",
    "a sosi": "n_v24_action_movement_a_veni",
}


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _post_guess(client: Client, game_id: str, text: str) -> dict:
    return client.post(
        f"/api/wordgames/contexto/games/{game_id}/guess",
        {"text": text},
        content_type="application/json",
    ).json()


def test_v44_alias_source_is_exact_bounded_and_applied_to_both_kg_copies() -> None:
    package_bytes = _PACKAGE_KG.read_bytes()
    assert package_bytes == _TEST_KG.read_bytes()
    fixture = json.loads(package_bytes)
    review = _json(_REVIEW)
    svc = WordGameService(load_fixture(_PACKAGE_KG).graph)

    aliases = {
        alias: node_id
        for node_id, surfaces in DATA.ALIAS_ADDITIONS.items()
        for alias in surfaces
    }
    assert aliases == review["accepted_aliases"]
    assert len(DATA.ALIAS_ADDITIONS) == 11
    assert len(aliases) == 12
    assert all(svc.resolve(alias) == node_id for alias, node_id in aliases.items())
    assert all(
        svc.resolve(surface) is None
        for surface in DATA.BLOCKED_ALIAS_FORMS
        if surface != "a sosi"
    )
    assert resolve_projection("a sosi") is not None

    meta = fixture["meta"]
    assert meta["build_version"] == "fixture-v63-film-and-television-morphology"
    assert meta["counts"]["nodes"] == 2364
    assert meta["counts"]["edges"] == 9217
    assert meta["counts"]["puzzles"] == 180
    assert sum(len(node.get("aliases", ())) for node in fixture["kg_nodes"]) == 8066


def test_v44_projection_funnel_is_explicit_nonwinning_and_collision_safe() -> None:
    review = _json(_REVIEW)
    assert len(PROJECTION_TERMS) == 473
    assert review["accepted_projections"] == _NEW_PROJECTIONS
    for surface, anchor_id in _NEW_PROJECTIONS.items():
        term = resolve_projection(surface)
        assert term is not None
        assert term.anchor_id == anchor_id
        assert term.rank_penalty == 1

    trash = resolve_projection("sac de gunoi")
    assert trash is not None
    assert trash.anchor_id == "n_v4soc_casa"
    assert all(
        resolve_projection(surface) is None
        for surface in review["rejected_projections"]
    )


def test_proxy_inventory_exactly_covers_the_four_shipped_sink_meshes() -> None:
    expected = {
        *V30_DATA.NEW_NODE_IDS,
        *V31_DATA.NEW_NODE_IDS,
        *V32_DATA.NEW_NODE_IDS,
        *V33_DATA.NEW_NODE_IDS,
    }
    svc = get_service()
    assert len(expected) == len(COMMON_FEEDBACK_PROXIES) == 71
    assert set(COMMON_FEEDBACK_PROXIES) == expected
    assert len(set(COMMON_FEEDBACK_PROXIES.values())) == 26
    assert set(COMMON_FEEDBACK_PROXIES).isdisjoint(COMMON_FEEDBACK_PROXIES.values())
    assert all(svc.exists(node_id) for node_id in COMMON_FEEDBACK_PROXIES)
    assert all(svc.exists(anchor_id) for anchor_id in COMMON_FEEDBACK_PROXIES.values())

    support = Counter(
        svc.distance(anchor_id, node_id)
        for node_id, anchor_id in COMMON_FEEDBACK_PROXIES.items()
    )
    assert support == {1: 57, 2: 13, 3: 1}


def test_every_proxy_anchor_reaches_every_selectable_unique_target() -> None:
    pack = _json(_PACKAGE_PACK)
    rankings = _json(_PACKAGE_RANKINGS)
    target_by_id = {row["id"]: row["target"] for row in pack["contexto"]}
    eligible = [
        row
        for row in rankings["boards"]
        if row["game"] == "contexto" and row["pilot_eligible"]
    ]
    targets = {target_by_id[row["id"]] for row in eligible}
    svc = get_service()

    assert len(eligible) == len(targets) == 202
    for anchor_id in set(COMMON_FEEDBACK_PROXIES.values()):
        assert targets <= set(svc.distances_from(anchor_id))
    for node_id in COMMON_FEEDBACK_PROXIES:
        assert targets.isdisjoint(svc.distances_from(node_id))


def test_proxy_feedback_keeps_public_identity_and_never_stacks_penalties() -> None:
    svc = get_service()
    client = Client()
    target = "n_v23lit_capra_cu_trei_iezi"
    sink = "n_v30_clothing_footwear_pantof"
    anchor = "n_v29_clothing_everyday_haina"
    session = _build_session(target, "normal", None)
    distance = svc.distance(anchor, target)
    assert distance is not None
    base_rank = rank_for(session, distance, session.weighted_dist.get(anchor))
    expected_rank = max(2, min(session.reachable + 1, base_rank + 1))
    game_id = store.create(session)

    exact_sink = _post_guess(client, game_id, "Pantof")
    projected_sink = _post_guess(client, game_id, "papuc")
    projected_with_penalty = _post_guess(client, game_id, "blugi")

    assert exact_sink["guess"]["id"] == sink
    assert exact_sink["guess"]["label"] == "Pantof"
    assert "anchor_id" not in exact_sink["guess"]
    assert exact_sink["won"] is False
    assert exact_sink["guess"]["distance"] == distance
    assert exact_sink["guess"]["rank"] == expected_rank
    assert projected_sink["guess"]["rank"] == expected_rank
    assert projected_with_penalty["guess"]["rank"] == expected_rank
    assert projected_with_penalty["attempts"] == 3

    stored = store.get(game_id)
    assert stored is not None
    assert stored.guesses[sink].anchor_id == anchor
    assert stored.guesses[resolve_projection("papuc").public_id].anchor_id == anchor
    assert stored.guesses[resolve_projection("blugi").public_id].anchor_id == anchor


def test_exact_sink_target_still_wins_and_proxy_match_cannot_win() -> None:
    svc = get_service()
    client = Client()
    sink = "n_v30_clothing_footwear_pantof"
    anchor = "n_v29_clothing_everyday_haina"

    exact_game = store.create(_build_session(sink, "normal", None))
    exact = _post_guess(client, exact_game, "Pantof")
    assert exact["won"] is True
    assert exact["guess"]["id"] == sink
    assert exact["guess"]["distance"] == 0
    assert exact["guess"]["rank"] == 1
    assert exact["guess"]["closeness"] == 100

    proxy_game = store.create(_build_session(anchor, "normal", None))
    proxied = _post_guess(client, proxy_game, "Pantof")
    assert proxied["won"] is False
    assert proxied["guess"]["id"] == sink
    assert proxied["guess"]["distance"] == 1
    assert proxied["guess"]["rank"] == 2
    assert proxied["guess"]["closeness"] < 100
    assert "target" not in proxied
    assert svc.label(anchor) not in str(proxied)


def test_projection_typo_cannot_suggest_a_proxy_of_the_secret() -> None:
    client = Client()
    anchor = "n_v29_clothing_everyday_haina"
    game_id = store.create(_build_session(anchor, "normal", None))
    body = _post_guess(client, game_id, "papucc")

    assert body["ok"] is False
    assert body["attempts"] == 0
    assert "Papuc" not in body["suggestions"]
    assert "target" not in body


def test_kg_typo_help_cannot_disclose_a_proxy_of_the_secret() -> None:
    client = Client()
    target = "n_v29_clothing_everyday_haina"
    for typo in ("pantalonx", "pantalno"):
        game_id = store.create(_build_session(target, "normal", None))
        body = _post_guess(client, game_id, typo)
        assert body["ok"] is False
        assert body["attempts"] == 0
        assert body["suggestions"] == []
        assert "needs_confirmation" not in body
        assert "resolved_label" not in body
        assert "Pantaloni" not in str(body)


def test_warmer_clue_uses_playable_proxy_rank_and_never_repeats_its_anchor() -> None:
    client = Client()
    session = _build_session("n_v30_clothing_footwear_pantof", "normal", None)
    game_id = store.create(session)
    played = _post_guess(client, game_id, "Șosetă")
    assert played["guess"]["rank"] == 8

    clue = _warmer_clue_candidate(session)
    assert clue is not None
    assert clue.label != "Șosetă"
    hinted = _post_guess(client, game_id, clue.label)
    assert hinted["guess"]["rank"] == clue.rank

    again = _warmer_clue_candidate(session)
    if again is not None:
        assert again.label not in {"Șosetă", clue.label}
        again_id = get_service().resolve(again.label)
        assert again_id is not None
        again_score = _score_feedback(get_service(), session, again_id)
        assert again_score.anchor_id not in {
            guess.anchor_id for guess in session.guesses.values()
        }


def test_proxy_gracefully_falls_back_when_a_custom_fixture_lacks_the_anchor() -> None:
    from cat_de_roman_esti.graph import Graph
    from cat_de_roman_esti.wordgames.contexto import ContextoSession

    sink = "n_v30_clothing_footwear_pantof"
    target = "custom_target"
    svc = WordGameService(
        Graph.from_records(
            [
                {"id": sink, "label_ro": "Pantof", "category": "test"},
                {"id": target, "label_ro": "Țintă", "category": "test"},
            ],
            [
                {
                    "id": "custom_edge",
                    "src_id": sink,
                    "dst_id": target,
                    "bidirectional": 0,
                    "is_distractor": 0,
                }
            ],
        )
    )
    session = ContextoSession(
        target=target,
        dist_hist={0: 1, 1: 1},
        reachable=2,
        weighted_dist={target: 0.0, sink: 1.0},
        sorted_weighted={0: [0.0], 1: [1.0]},
    )

    score = _score_feedback(svc, session, sink)
    assert score.anchor_id == sink
    assert score.distance == 1
    assert score.rank == 2


def test_bound_promotions_and_duplicate_reserve_cleanup_are_exact() -> None:
    assert _PACKAGE_PACK.read_bytes() == _TEST_PACK.read_bytes()
    assert _PACKAGE_DEMOTIONS.read_bytes() == _TEST_DEMOTIONS.read_bytes()
    pack = _json(_PACKAGE_PACK)
    rankings = _json(_PACKAGE_RANKINGS)
    rows = {row["id"]: row for row in pack["contexto"]}
    ranked = {row["id"]: row for row in rankings["boards"]}
    statuses = Counter(
        row["status"]
        for game in ("conexiuni", "contexto", "lant", "alchimie")
        for row in pack[game]
    )

    assert statuses == {"approved": 610, "pending": 8}
    assert rows["ct_literatura_298"]["status"] == "approved"
    assert rows["ct_viata_de_roman_299"]["status"] == "approved"
    assert ranked["ct_literatura_298"]["pilot_eligible"] is True
    assert ranked["ct_viata_de_roman_299"]["pilot_eligible"] is True
    assert rows["ct_gastronomie_300"]["status"] == "approved"
    assert ranked["ct_gastronomie_300"]["pilot_eligible"] is True

    reserve = _json(_PACKAGE_DEMOTIONS)
    duplicate_to_canonical = {
        "ct_sport_315": "ct_sport_259",
        "ct_sport_316": "ct_sport_262",
        "ct_sport_317": "ct_sport_181",
    }
    assert reserve["meta"]["count"] == 3
    assert set(reserve["ids"]) == set(duplicate_to_canonical)
    for duplicate, canonical in duplicate_to_canonical.items():
        assert rows[duplicate]["status"] == rows[canonical]["status"] == "approved"
        assert rows[duplicate]["target"] == rows[canonical]["target"]
        assert ranked[duplicate]["pilot_eligible"] is False
        assert ranked[canonical]["pilot_eligible"] is True


def test_unanimous_gate_is_complete_and_bound_to_clean_dossiers() -> None:
    gate = _json(_GATE_DIR / "contexto_verdicts.json")
    by_id = {row["id"]: row for row in gate["perItem"]}
    assert gate["batch"]["input_ids"] == [
        "ct_literatura_298",
        "ct_viata_de_roman_299",
    ]
    assert gate["coverage"] == {
        "total": 2,
        "verified": 2,
        "unverifiedClean": 0,
        "verifiersLost": 0,
        "lost": 0,
    }
    assert gate["verdicts"] == {
        "ct_literatura_298": "promote",
        "ct_viata_de_roman_299": "promote",
    }
    for item_id, row in by_id.items():
        dossier = _json(_GATE_DIR / "dossiers" / f"{item_id}.json")
        assert row["analyst"] == row["verifier"] == row["final"] == "promote"
        assert row["verified"] is True
        assert row["failure_modes"] == []
        assert dossier["lint_findings"] == []
        assert dossier["review_binding"] == row["review_binding"]
        assert critique_pack.dossier_review_binding(dossier) == row["review_binding"]
