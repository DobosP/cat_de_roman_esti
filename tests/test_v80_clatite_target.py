"""A reviewed Clătite round is selectable without changing earlier content."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from tests.content_history import before_v80_derived, before_v80_pack, before_v80_rankings

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "cat_de_roman_esti/fixtures"
REVIEW = ROOT / "docs/reviews/v80-clatite-target"
NEW_ID = "ct_gastronomie_320"
TARGET = "n_v3gas_clatite"
PUBLIC_SEED = 20


def _read(path: Path) -> dict:
    return json.loads(path.read_bytes())


def _digest(payload: dict) -> str:
    return hashlib.sha256(
        (json.dumps(payload, ensure_ascii=False, indent=1) + "\n").encode()
    ).hexdigest()


def test_only_the_reviewed_row_is_added_and_earlier_pack_is_exact() -> None:
    from cat_de_roman_esti.wordgames.packs import get_pack

    blob = (FIXTURES / "games_pack.json").read_bytes()
    assert blob == (ROOT / "tests/fixtures/games_pack.json").read_bytes()
    pack = json.loads(blob)
    assert [row for row in pack["contexto"] if row["id"] == NEW_ID] == [{
        "id": NEW_ID, "target": TARGET, "difficulty": "usor",
        "category": "gastronomie", "source": "ai", "status": "approved",
    }]
    assert pack["meta"]["counts"]["contexto"] == 210
    assert pack["meta"]["id_high_water"]["contexto"] == 320
    assert _digest(before_v80_pack(pack)) == (
        "9f559e33eac688868dfdf562f62022a3df629c9cb389b957dda0896d7cec70b5"
    )
    assert get_pack().selectable_count("contexto") == 204
    pool = get_pack().pool("contexto", category="gastronomie", difficulty="usor")
    assert any(row.id == NEW_ID and row._pilot_eligible for row in pool)


def test_existing_rankings_and_frozen_boards_reconstruct_exact_baseline() -> None:
    rankings = _read(FIXTURES / "board_rankings_v37.json")
    derived = _read(FIXTURES / "derived_catalog_v38.json")
    assert len(rankings["boards"]) == 621
    assert len(derived["boards"]) == 336
    assert _read(REVIEW / "artifact-delta.json")["selection_weight_changes"] == {
        "ct_meme_net_064": [4, 3],
    }
    assert _digest(before_v80_rankings(rankings)) == (
        "53c2542b845d2560a900712381ab4c28cb1b9789beaae9690639647871e905d3"
    )
    assert _digest(before_v80_derived(derived)) == (
        "84aaa772746dac0eb4e1366738f467afad86c543c7430cb67810475d5a296878"
    )


def test_exact_candidate_has_two_independently_bound_promotions() -> None:
    candidate = REVIEW / "gastronomie/candidates.json"
    binding = "sha256:" + hashlib.sha256(candidate.read_bytes()).hexdigest()
    assert binding == "sha256:87e8b3b4133a82c83542070f6f3228d7482b8e775d66fed660574148220e67dd"
    for name in ("verify_factual.json", "verify_quality.json"):
        assert _read(REVIEW / "gastronomie" / name)["candidate_sha256"] == binding
    artifact = _read(REVIEW / "verdicts/contexto_verdicts.json")
    assert artifact["batch"] == {
        "version": 2, "mode": "gate", "input_ids": [NEW_ID],
    }
    assert artifact["verdicts"] == {NEW_ID: "promote"}
    assert artifact["coverage"] == {
        "total": 1, "verified": 1, "unverifiedClean": 0, "verifiersLost": 0, "lost": 0,
    }
    assert len(artifact["perItem"]) == 1
    row = artifact["perItem"][0]
    assert row["id"] == NEW_ID and row["verified"] is True
    assert row["policy"] == "unanimous-promote" and row["verifier_lost"] is False
    reviewers = set()
    for role in ("analyst", "verifier"):
        path = REVIEW / f"{role}-review.json"
        raw = _read(path)
        reviewers.add(raw["reviewer"])
        assert raw["role"] == role and raw["input_ids"] == [NEW_ID]
        assert len(raw["items"]) == 1
        assert row[f"{role}_review"] == raw["items"][0]
        assert row[role] == row["final"] == "promote"
        assert raw["items"][0]["review_binding"] == row["review_binding"]
        assert artifact["provenance"][role]["sha256"] == (
            "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
        )
    assert len(reviewers) == 2


@pytest.mark.parametrize(
    ("opener", "distance", "rank", "temperature"),
    [("făină", 1, 2, "Fierbinte"), ("ou", 1, 5, "Fierbinte"),
     ("gem", 1, 8, "Fierbinte"), ("dulceață", 1, 7, "Fierbinte"),
     ("lapte", 2, 40, "Cald"), ("brânză", 2, 30, "Cald"),
     ("smântână", 2, 22, "Cald")],
)
def test_public_clatite_round_has_warm_openers_resume_repeats_and_exact_win(
    opener: str, distance: int, rank: int, temperature: str,
) -> None:
    pytest.importorskip("django")
    from django.test import Client

    from cat_de_roman_esti.wordgames.contexto import store

    client = Client()
    response = client.post(
        f"/api/wordgames/contexto/games?seed={PUBLIC_SEED}&category=gastronomie&difficulty=usor"
    )
    assert response.status_code == 200
    initial = response.json()
    game_id = initial["game_id"]
    url = f"/api/wordgames/contexto/games/{game_id}"
    try:
        assert not ({"target", "solution", "source_id", "score"} & initial.keys())
        warm = client.post(url + "/guess", {"text": opener}, content_type="application/json")
        assert warm.status_code == 200
        body = warm.json()
        assert body["won"] is False and body["attempts"] == 1
        assert (body["guess"]["distance"], body["guess"]["rank"],
                body["guess"]["temperature"]) == (distance, rank, temperature)
        assert TARGET not in str(body) and "anchor_id" not in str(body)
        resumed = client.get(url).json()
        assert resumed["guesses"] == body["guesses"] and resumed["attempts"] == 1
        repeated = client.post(
            url + "/guess", {"text": f" {opener.upper()} "}, content_type="application/json"
        ).json()
        assert repeated["attempts"] == 1 and repeated["feedback"]["kind"] == "repeat"
        won = client.post(
            url + "/guess", {"text": "clătitele"}, content_type="application/json"
        ).json()
        assert won["won"] is True and won["guess"]["id"] == TARGET
        assert won["attempts"] == 2 and won["score"] == 940
    finally:
        store.delete(game_id)
