"""The reviewed Mop round is public; V88 records and rejected candidates stay bounded."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path

import pytest
from django.test import Client

from cat_de_roman_esti.wordgames import contexto as C
from cat_de_roman_esti.wordgames.packs import get_pack
from cat_de_roman_esti.wordgames.service import get_service
from tests import content_history as history
from tests.content_scenarios import contexto_seed
from tests.current_content import CURRENT_CONTENT

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "cat_de_roman_esti/fixtures"
REVIEW = ROOT / "docs/reviews/v89-feedback-and-conexiuni-recovery"
MOP = "n_v31_cleaning_floor_mop"
VERDICTS = {
    "ct_viata_de_roman_352": "reject",
    "ct_viata_de_roman_353": "promote",
    "ct_viata_de_roman_354": "reject",
}
BASELINE = {
    "kg_sample.json": "2964951e3f68be7b49abb7f727b97d700a42d7e3527b117ef8b6c2830103f9fc",
    "games_pack.json": "4c7030bd86e966162f4ac51ef00cf3bb649ff7a9d59c8c34e180cb7ff53e1636",
    "board_rankings_v37.json": "b19a53983a1b4555c700f717033bb61b66aea9ea2dce643a7df0cf1a31e2c764",
    "derived_catalog_v38.json": "1c1613cd4f1e59c2b8d68ded9b071b1f812198f50aca528a3785fef34fad90b8",
}


def _read(path):
    return json.loads(path.read_bytes())


def _sha(blob):
    return hashlib.sha256(blob).hexdigest()


@pytest.mark.parametrize(("filename", "inverse"), [
    ("kg_sample.json", history.before_v89_fixture),
    ("games_pack.json", history.before_v89_pack),
    ("board_rankings_v37.json", history.before_v89_rankings),
    ("derived_catalog_v38.json", history.before_v89_derived),
])
def test_complete_v88_artifacts_reconstruct_and_reject_any_unreviewed_change(filename, inverse):
    path = FIXTURES / filename
    blob = path.read_bytes()
    current = json.loads(blob)
    before = inverse(current)
    indent = 2 if filename == "kg_sample.json" else 1
    assert _sha((json.dumps(before, ensure_ascii=False, indent=indent) + "\n").encode()) == (
        BASELINE[filename]
    )
    assert current == json.loads(blob), "history restoration must not mutate current content"
    assert blob == (ROOT / "tests/fixtures" / filename).read_bytes()
    assert _sha(blob) == CURRENT_CONTENT.artifact_sha256[str(path.relative_to(ROOT))]
    receipt = _read(REVIEW / "artifact-delta.json")
    assert receipt["baseline_commit"] == "b614bfe735a27b9703025420daf603118f6a7f74"
    assert receipt["files"][filename]["baseline_sha256"] == BASELINE[filename]
    for place in ("head", "old_row"):
        modified = deepcopy(current)
        if place == "head":
            modified["meta"]["unreviewed_probe"] = True
        else:
            table = next(key for key, value in modified.items() if isinstance(value, list))
            modified[table][0]["unreviewed_probe"] = True
        with pytest.raises(AssertionError):
            inverse(modified)


def test_all_658_old_pack_records_and_336_derived_boards_survive_exactly():
    live = _read(FIXTURES / "games_pack.json")
    previous = history.before_v89_pack(live)
    games = ("conexiuni", "contexto", "lant", "alchimie")
    assert sum(len(previous[game]) for game in games) == 658
    for game in games:
        old = {row["id"]: row for row in previous[game]}
        current = {row["id"]: row for row in live[game]}
        assert {key: current[key] for key in old} == old
        expected_added = {"ct_viata_de_roman_353"} if game == "contexto" else set()
        assert set(current) - set(old) == expected_added
    assert live["lant"] == previous["lant"] and len(live["lant"]) == 100
    assert live["alchimie"] == previous["alchimie"] and len(live["alchimie"]) == 83
    derived = _read(FIXTURES / "derived_catalog_v38.json")
    assert derived["boards"] == history.before_v89_derived(derived)["boards"]
    assert len(derived["boards"]) == 336
    kg = _read(FIXTURES / "kg_sample.json")
    assert kg == history.before_v89_fixture(kg)
    assert _sha((ROOT / "tests/fixtures/cat_mobile_app_pack_contract.json").read_bytes()) == (
        "d2fbb9f550a05b6b128431ee55787b2b156846887f0bc8ce1908f09e6683b951"
    )


def test_only_reviewed_mop_round_is_approved_and_the_rejected_ids_cannot_be_selected():
    receipt = _read(REVIEW / "artifact-delta.json")["files"]["games_pack.json"]
    new = receipt["tables"]["contexto"]["added"]
    assert len(new) == 1
    assert (new[0]["id"], new[0]["target"], new[0]["category"],
            new[0]["difficulty"], new[0]["status"]) == (
        "ct_viata_de_roman_353", MOP, "viata_de_roman", "usor", "approved",
    )
    live = _read(FIXTURES / "games_pack.json")
    assert live["meta"]["id_high_water"]["contexto"] == 354
    assert all(row["id"] not in {"ct_viata_de_roman_352", "ct_viata_de_roman_354"}
               for row in live["contexto"])
    pool = get_pack().pool("contexto")
    assert {item.id for item in pool if item._pilot_eligible} >= {"ct_viata_de_roman_353"}
    assert not {item.payload["target"] for item in pool} & {
        "n_v31_cleaning_floor_faras", "n_v31_cleaning_floor_aspirator",
    }
    assert get_pack().selectable_count("contexto") == CURRENT_CONTENT.contexto_eligible


def test_all_three_original_candidates_retain_two_independently_bound_final_decisions():
    candidate = REVIEW / "author-candidates/viata_de_roman/candidates.json"
    assert _sha(candidate.read_bytes()) == (
        "a7e22a7d4b1c84f5450e167b0854d5e8a5532f0f8f0b733da10a3b955860cdc4"
    )
    for name in ("verify_factual.json", "verify_quality.json"):
        assert _read(candidate.parent / name)["candidate_sha256"] == (
            "sha256:" + _sha(candidate.read_bytes())
        )
    artifact = _read(REVIEW / "final-gate/contexto_verdicts.json")
    assert artifact["batch"] == {"version": 2, "mode": "gate", "input_ids": list(VERDICTS)}
    assert artifact["verdicts"] == VERDICTS
    assert artifact["coverage"] == {
        "total": 3, "verified": 3, "unverifiedClean": 0, "verifiersLost": 0, "lost": 0,
    }
    reviewers = set()
    for role in ("analyst", "verifier"):
        path = REVIEW / f"{role}.json"
        raw = _read(path)
        reviewers.add(raw["reviewer"])
        assert raw["role"] == role and raw["input_ids"] == list(VERDICTS)
        assert artifact["provenance"][role]["sha256"] == "sha256:" + _sha(path.read_bytes())
        assert {row["id"]: row["verdict"] for row in raw["items"]} == VERDICTS
        for item, verdict in zip(raw["items"], artifact["perItem"], strict=True):
            assert item == verdict[f"{role}_review"]
            assert item["review_binding"] == verdict["review_binding"]
            assert item["verdict"] == verdict["final"] == VERDICTS[item["id"]]
            dossier = _read(REVIEW / "dossiers" / (item["id"] + ".json"))
            assert dossier["review_binding"] == item["review_binding"]
    assert len(reviewers) == 2


def _private(body):
    encoded = json.dumps(body, ensure_ascii=False)
    assert not ({"target", "solution", "source_id", "score"} & body.keys())
    assert MOP not in encoded and "Mop" not in encoded and "anchor_id" not in encoded


def test_public_mop_journey_preserves_clue_privacy_repeat_resume_and_exact_win():
    seed = contexto_seed(MOP, difficulty="usor", category="viata_de_roman")
    client = Client()
    initial = client.post(
        f"/api/wordgames/contexto/games?seed={seed}&category=viata_de_roman&difficulty=usor"
    )
    assert initial.status_code == 200
    body = initial.json()
    game_id = body["game_id"]
    url = f"/api/wordgames/contexto/games/{game_id}"

    def post(action, **payload):
        response = client.post(url + action, payload, content_type="application/json")
        assert response.status_code == 200
        return response.json()

    try:
        assert C.store.get(game_id).pack_id == "ct_viata_de_roman_353"
        _private(body)
        for attempt, word in enumerate(("stilou", "fotbal", "București"), 1):
            body = post("/guess", text=word)
            assert body["ok"] and not body["won"] and body["attempts"] == attempt
            _private(body)
        clue = post("/clue")
        assert clue["clue_kind"] == "warmer" and clue["clues_used"] == 1
        assert clue["word"]["rank"] > 1
        _private(clue)
        resumed = client.get(url).json()
        assert resumed["attempts"] == 3 and resumed["clues_used"] == 1
        assert resumed["warm_clue"]["label"] == clue["word"]["label"]
        _private(resumed)
        body = post("/guess", text="praf")
        assert body["ok"] and not body["won"] and body["attempts"] == 4
        assert body["guess"]["id"] == "ctxp_81703160cad7893fa1c9"
        assert body["guess"]["rank"] == 2 and body["guess"]["temperature"] == "Fierbinte"
        _private(body)
        repeated = post("/guess", text="  PRAF  ")
        assert repeated["attempts"] == 4 and repeated["feedback"]["kind"] == "repeat"
        assert repeated["guesses"] == body["guesses"]
        _private(repeated)
        resumed = client.get(url).json()
        assert resumed["guesses"] == body["guesses"] and resumed["clues_used"] == 1
        _private(resumed)
        won = post("/guess", text=get_service().label(MOP))
        assert won["won"] and won["attempts"] == 5 and won["clues_used"] == 1
        assert won["guess"]["id"] == MOP and won["guess"]["rank"] == 1
        assert won["score"] == C.score_for(5, 1)
        terminal = client.get(url).json()
        assert terminal["won"] and terminal["score"] == won["score"]
    finally:
        C.store.delete(game_id)
