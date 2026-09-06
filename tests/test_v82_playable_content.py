"""V82 adds a reviewed food shelf with real public, recoverable game journeys."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from tests.content_history import before_v82_derived, before_v82_pack, before_v82_rankings

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "cat_de_roman_esti/fixtures"
REVIEW = ROOT / "docs/reviews/v82-playable-content-batch"
CASES = [
    ("n_gas_cozonac", "Cozonac", "usor", ("făină", "nucă")),
    ("n_v17gas_pasca", "Pască", "normal", ("brânză", "desert")),
    ("n_gas_mustar", "Muștar", "usor", ("mici", "grătar")),
    ("n_gas_mujdei", "Mujdei", "usor", ("usturoi", "grătar")),
    ("n_gas_ciorba_burta", "Ciorbă de burtă", "normal", ("burtă", "smântână")),
    ("n_gas_urda", "Urdă", "normal", ("brânză", "lapte")),
    ("n_v3gas_friptura", "Friptură", "usor", ("carne", "grătar")),
    ("n_gas_bulz", "Bulz", "normal", ("mămăligă", "brânză")),
]


def _read(path: Path) -> dict:
    return json.loads(path.read_bytes())


def _digest(value: dict) -> str:
    return hashlib.sha256(
        (json.dumps(value, ensure_ascii=False, indent=1) + "\n").encode()
    ).hexdigest()


@pytest.mark.parametrize(
    ("filename", "restore", "expected"),
    [
        ("games_pack.json", before_v82_pack,
         "27ce95294b7a8ea39aedc3f22e125650d0f06d9ecbcf0fb7af4bc6966d59cb29"),
        ("board_rankings_v37.json", before_v82_rankings,
         "fa1094a6c51e6d51cdafc5fecd302ef43bd3f44ff0e5aa7b36b7397a8ef7b546"),
        ("derived_catalog_v38.json", before_v82_derived,
         "f66624bfe2e5ef434c9d47eb21b128d569637ac941b85834b2c0a5a196de7a6a"),
    ],
)
def test_complete_v81_content_reconstructs(filename, restore, expected):
    blob = (FIXTURES / filename).read_bytes()
    assert blob == (ROOT / "tests/fixtures" / filename).read_bytes()
    assert _digest(restore(json.loads(blob))) == expected


def test_all_eight_reviewed_targets_are_approved_and_runtime_selectable():
    from cat_de_roman_esti.wordgames.packs import get_pack

    receipt = _read(REVIEW / "artifact-delta.json")
    expected = {target: difficulty for target, _, difficulty, _ in CASES}
    new = receipt["new_records"]
    assert len(new) == len(expected) == 8
    assert {row["target"]: row["difficulty"] for row in new} == expected
    assert all(row["status"] == "approved" and row["category"] == "gastronomie" for row in new)
    new_ids = {row["id"] for row in new}
    old_ids = {row["id"] for row in before_v82_pack(_read(FIXTURES / "games_pack.json"))[
        "contexto"
    ]}
    assert not old_ids & new_ids
    pool = get_pack().pool("contexto", category="gastronomie")
    assert {row.id for row in pool if row._pilot_eligible} >= new_ids
    assert get_pack().selectable_count("contexto") == 212
    # This content batch changes neither the KG vocabulary nor the shared graph.
    assert hashlib.sha256((FIXTURES / "kg_sample.json").read_bytes()).hexdigest() == (
        "fc3ea5a27e3bcb1da72fb3146316d7709da37012dddc494de0d6d4370862a331"
    )


def test_complete_candidate_has_two_independently_bound_promotions():
    candidate = REVIEW / "gastronomie/candidates.json"
    binding = "sha256:" + hashlib.sha256(candidate.read_bytes()).hexdigest()
    for name in ("verify_factual.json", "verify_quality.json"):
        assert _read(REVIEW / "gastronomie" / name)["candidate_sha256"] == binding
    ids = [row["id"] for row in _read(REVIEW / "artifact-delta.json")["new_records"]]
    artifact = _read(REVIEW / "verdicts/contexto_verdicts.json")
    assert artifact["batch"] == {"version": 2, "mode": "gate", "input_ids": ids}
    assert artifact["verdicts"] == dict.fromkeys(ids, "promote")
    assert artifact["coverage"] == {
        "total": 8, "verified": 8, "unverifiedClean": 0, "verifiersLost": 0, "lost": 0,
    }
    reviewers = set()
    for role in ("analyst", "verifier"):
        path = REVIEW / f"{role}-review.json"
        raw = _read(path)
        reviewers.add(raw["reviewer"])
        assert raw["role"] == role and raw["input_ids"] == ids
        assert artifact["provenance"][role]["sha256"] == (
            "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
        )
        for item, verdict in zip(raw["items"], artifact["perItem"], strict=True):
            assert item == verdict[f"{role}_review"]
            assert item["review_binding"] == verdict["review_binding"]
            assert item["verdict"] == verdict["final"] == "promote"
    assert len(reviewers) == 2


@pytest.mark.parametrize(("target", "answer", "difficulty", "openers"), CASES)
def test_public_food_round_has_useful_guesses_resume_repeats_and_exact_win(
    target, answer, difficulty, openers,
):
    pytest.importorskip("django")
    from django.test import Client

    from cat_de_roman_esti.wordgames.contexto import store

    seed = _read(REVIEW / "public-seeds.json")[target]
    client = Client()
    response = client.post(
        f"/api/wordgames/contexto/games?seed={seed}&category=gastronomie&difficulty={difficulty}"
    )
    assert response.status_code == 200
    initial = response.json()
    game_id = initial["game_id"]
    url = f"/api/wordgames/contexto/games/{game_id}"
    try:
        assert not ({"target", "solution", "source_id", "score"} & initial.keys())
        assert target not in str(initial) and answer not in str(initial)
        for number, opener in enumerate(openers, 1):
            response = client.post(
                url + "/guess", {"text": opener}, content_type="application/json"
            )
            assert response.status_code == 200
            body = response.json()
            assert body["ok"] and not body["won"] and body["attempts"] == number
            assert body["guess"]["distance"] <= 2
            assert body["guess"]["temperature"] in {"Cald", "Fierbinte"}
            assert target not in str(body) and answer not in str(body)
            assert "anchor_id" not in str(body)
        resumed = client.get(url).json()
        assert resumed["guesses"] == body["guesses"] and resumed["attempts"] == 2
        repeated = client.post(
            url + "/guess", {"text": f" {openers[-1].upper()} "},
            content_type="application/json",
        ).json()
        assert repeated["attempts"] == 2 and repeated["feedback"]["kind"] == "repeat"
        cold = client.post(
            url + "/guess", {"text": "stilou"}, content_type="application/json",
        ).json()
        assert cold["ok"] and not cold["won"]
        assert cold["guess"]["rank"] > body["guess"]["rank"]
        assert cold["guess"]["temperature"] not in {"Cald", "Fierbinte"}
        won = client.post(
            url + "/guess", {"text": answer}, content_type="application/json",
        ).json()
        assert won["won"] and won["guess"]["id"] == target
        assert won["attempts"] == 4 and won["score"] > 0
    finally:
        store.delete(game_id)
