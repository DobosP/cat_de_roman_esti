"""The repaired V83 food batch is reviewed, selectable and playable through the API."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from tests.content_history import before_v83_derived, before_v83_pack, before_v83_rankings
from tests.content_scenarios import contexto_seed
from tests.current_content import CURRENT_CONTENT

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "cat_de_roman_esti/fixtures"
REVIEW = ROOT / "docs/reviews/v83-food-input-and-feedback"
CASES = [
    ("n_v21gas_cornulete", "normal", ("gem", "nucă"), "cornulețului cu gem"),
    ("n_v17gas_gogosi", "usor", ("gem", "ulei"), "gogoașa prăjită"),
    ("n_gas_telemea", "usor", ("sare", "brânză"), "telemelele"),
    ("n_v3gas_cartofi_prajiti", "usor", ("ulei", "cartof"), "cartofilor prăjiți"),
    ("n_gas_ardei_umpluti", "normal", ("ardei", "orez"), "ardeiului umplut"),
]


def _read(path: Path) -> dict:
    return json.loads(path.read_bytes())


@pytest.mark.parametrize(
    ("filename", "restore", "expected"),
    [
        ("games_pack.json", before_v83_pack,
         "26d61a029a6c706a02a15991730725a3421dfa1f9b36537032291828a44ab070"),
        ("board_rankings_v37.json", before_v83_rankings,
         "fc31646b058bf2caaaf63a90ac172e504fd2bd89c4028102c4570d054f9a40a8"),
        ("derived_catalog_v38.json", before_v83_derived,
         "cf9ed7cba4bc82025297907a5131df7c7f61c06ac43722d22d591790e6facf9a"),
    ],
)
def test_complete_v82_artifacts_reconstruct(filename, restore, expected):
    blob = (FIXTURES / filename).read_bytes()
    assert blob == (ROOT / "tests/fixtures" / filename).read_bytes()
    restored = restore(json.loads(blob))
    encoded = (json.dumps(restored, ensure_ascii=False, indent=1) + "\n").encode()
    assert hashlib.sha256(encoded).hexdigest() == expected


def test_exact_five_new_records_are_approved_and_runtime_selectable():
    from cat_de_roman_esti.wordgames.packs import get_pack

    added = _read(REVIEW / "artifact-delta.json")["new_records"]
    assert len(added) == 5
    assert {r["target"]: r["difficulty"] for r in added} == {
        target: difficulty for target, difficulty, _, _ in CASES
    }
    assert all(r["status"] == "approved" and r["category"] == "gastronomie" for r in added)
    assert {r["id"] for r in added} == {f"ct_gastronomie_{i}" for i in range(329, 334)}
    pack = _read(FIXTURES / "games_pack.json")
    assert pack["meta"]["counts"]["contexto"] == CURRENT_CONTENT.pack_counts["contexto"]
    assert pack["meta"]["id_high_water"]["contexto"] == CURRENT_CONTENT.contexto_id_high_water
    assert get_pack().selectable_count("contexto") == CURRENT_CONTENT.contexto_eligible
    pool = get_pack().pool("contexto", category="gastronomie")
    assert {r.id for r in pool if r._pilot_eligible} >= {r["id"] for r in added}


def test_five_promotions_are_bound_to_independent_complete_reviews():
    candidate = REVIEW / "gastronomie/candidates.json"
    candidate_sha = "sha256:" + hashlib.sha256(candidate.read_bytes()).hexdigest()
    for name in ("verify_factual.json", "verify_quality.json"):
        assert _read(REVIEW / "gastronomie" / name)["candidate_sha256"] == candidate_sha
    ids = [f"ct_gastronomie_{i}" for i in range(329, 334)]
    artifact = _read(REVIEW / "verdicts/contexto_verdicts.json")
    assert artifact["batch"] == {"version": 2, "mode": "gate", "input_ids": ids}
    assert artifact["verdicts"] == dict.fromkeys(ids, "promote")
    assert artifact["coverage"] == {
        "total": 5, "verified": 5, "unverifiedClean": 0, "verifiersLost": 0, "lost": 0,
    }
    reviewers = set()
    for role in ("analyst", "verifier"):
        path = REVIEW / f"{role}-review.json"
        raw = _read(path)
        assert raw["role"] == role and raw["input_ids"] == ids
        reviewers.add(raw["reviewer"])
        assert artifact["provenance"][role]["sha256"] == (
            "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
        )
        for item, final in zip(raw["items"], artifact["perItem"], strict=True):
            assert final[f"{role}_review"] == item
            assert item["review_binding"] == final["review_binding"]
            assert item["verdict"] == final["final"] == "promote"
    assert len(reviewers) == 2


@pytest.mark.parametrize(("target", "difficulty", "openers", "answer"), CASES)
def test_public_round_has_hot_core_guesses_repeat_resume_and_exact_form_win(
    target, difficulty, openers, answer,
):
    pytest.importorskip("django")
    from django.test import Client

    from cat_de_roman_esti.wordgames.contexto import store
    from cat_de_roman_esti.wordgames.service import get_service

    seed = contexto_seed(target, difficulty=difficulty)
    client = Client()
    response = client.post(
        f"/api/wordgames/contexto/games?seed={seed}&category=gastronomie&difficulty={difficulty}"
    )
    assert response.status_code == 200
    initial = response.json()
    gid = initial["game_id"]
    url = f"/api/wordgames/contexto/games/{gid}"
    try:
        assert target not in str(initial) and get_service().label(target) not in str(initial)
        for attempt, word in enumerate(openers, 1):
            body = client.post(
                url + "/guess", {"text": word}, content_type="application/json",
            ).json()
            assert body["ok"] and not body["won"] and body["attempts"] == attempt
            assert body["guess"]["temperature"] == "Fierbinte"
            assert body["guess"]["rank"] == 2 and body["guess"]["distance"] == 1
            assert target not in str(body) and "anchor_id" not in str(body)
        resumed = client.get(url).json()
        assert resumed["guesses"] == body["guesses"] and resumed["attempts"] == 2
        repeat = client.post(
            url + "/guess", {"text": f" {openers[-1].upper()} "},
            content_type="application/json",
        ).json()
        assert repeat["attempts"] == 2 and repeat["feedback"]["kind"] == "repeat"
        control = client.post(
            url + "/guess", {"text": "stilou"}, content_type="application/json",
        ).json()
        assert control["ok"] and not control["won"] and control["guess"]["rank"] > 2
        won = client.post(
            url + "/guess", {"text": answer}, content_type="application/json",
        ).json()
        assert won["won"] and won["guess"]["id"] == target
        assert won["attempts"] == 4 and won["score"] > 0
    finally:
        store.delete(gid)
