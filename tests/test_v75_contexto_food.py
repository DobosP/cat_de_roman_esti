"""V75 promotes exactly the reviewed targets and preserves prior content."""

from __future__ import annotations

import copy
import hashlib
import json
from collections import Counter
from pathlib import Path

import pytest

from cat_de_roman_esti.wordgames.packs import get_pack
from tests.content_history import before_v80_derived, before_v80_pack, before_v80_rankings
from tests.content_scenarios import contexto_seed
from tests.current_content import CURRENT_CONTENT

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "cat_de_roman_esti/fixtures"
REVIEW = ROOT / "docs/reviews/v75-contexto-food"
NEW_TARGETS = {
    "ct_gastronomie_318": "n_gas_mici",
    "ct_gastronomie_319": "n_gas_salata_boeuf",
}
OLD_PACK_SHA = "05e80ab2ffb8ec185ad445305a728c784a93e683474d5ec645c10aa1247184ed"
OLD_RANKINGS_SHA = "45dfd81444dec14b4b639122fe30dea58f05ca76440003eb5280cc01bfcdc3e9"
OLD_DERIVED_SHA = "8cff438c25deb5084c0311e808941bfef23e3c7bdbf93242a7a53348a6d2ef57"
# V75 reconstruction uses its original KG binding; V77 changes only that wrapper.
V75_KG_SHA = "fa9575db4819fa314e43218a0ad953f52c3e6ee2e34cac105dbc88e2d2247106"
WEIGHT_CHANGES = {
    "ct_sport_094": (5, 4),
    "ct_gastronomie_127": (5, 4),
    "ct_meme_net_160": (4, 3),
    "ct_societate_087": (3, 2),
}


def read(path: Path) -> dict:
    return json.loads(path.read_text())


def digest(value: dict) -> str:
    blob = (json.dumps(value, ensure_ascii=False, indent=1) + "\n").encode()
    return hashlib.sha256(blob).hexdigest()


def test_only_two_reviewed_records_are_added_to_the_previous_pack() -> None:
    pack = before_v80_pack(read(FIXTURES / "games_pack.json"))
    new = {row["id"]: row for row in pack["contexto"] if row["id"] in NEW_TARGETS}
    assert {key: row["target"] for key, row in new.items()} == NEW_TARGETS
    assert all(
        row["status"] == "approved" and row["category"] == "gastronomie"
        and row["difficulty"] == "usor" and row["source"] == "ai"
        for row in new.values()
    )
    assert pack["meta"]["counts"]["contexto"] == 209
    assert pack["meta"]["id_high_water"]["contexto"] == 319
    previous = copy.deepcopy(pack)
    previous["contexto"] = [row for row in pack["contexto"] if row["id"] not in NEW_TARGETS]
    previous["meta"]["counts"]["contexto"] = 207
    previous["meta"]["id_high_water"]["contexto"] = 317
    # Reconstruct the entire prior artifact: old records, holds and ordering are exact.
    assert digest(previous) == OLD_PACK_SHA
    pool = get_pack().pool("contexto", category="gastronomie", difficulty="usor")
    assert {row.id for row in pool if row._pilot_eligible} >= NEW_TARGETS.keys()
    assert get_pack().selectable_count("contexto") >= 204


def test_rank_changes_are_limited_to_new_targets_ordinals_and_four_weight_bands() -> None:
    ranking = before_v80_rankings(read(FIXTURES / "board_rankings_v37.json"))
    previous = copy.deepcopy(ranking)
    new_rows = [row for row in ranking["boards"] if row["id"] in NEW_TARGETS]
    assert len(new_rows) == 2 and all(row["pilot_eligible"] for row in new_rows)
    assert ranking["meta"]["counts"]["pilot_eligible"] == 450
    previous["boards"] = [row for row in previous["boards"] if row["id"] not in NEW_TARGETS]
    ranks: Counter[str] = Counter()
    for row in previous["boards"]:
        ranks[row["game"]] += 1
        row["rank"] = ranks[row["game"]]
        if row["id"] in WEIGHT_CHANGES:
            before, after = WEIGHT_CHANGES[row["id"]]
            assert row["selection_weight"] == after
            row["selection_weight"] = before
    previous["meta"]["kg_sha256"] = V75_KG_SHA
    previous["meta"]["pack_sha256"] = OLD_PACK_SHA
    counts = previous["meta"]["counts"]
    counts.update(total=618, approved=610, pilot_eligible=448)
    counts["by_game"]["contexto"] = 207
    counts["eligible_by_game"]["contexto"] = 201
    # In particular, all old quality scores, eligibility and status remain byte-exact.
    assert digest(previous) == OLD_RANKINGS_SHA


def test_derived_boards_kg_and_mobile_payloads_are_preserved() -> None:
    derived = before_v80_derived(read(FIXTURES / "derived_catalog_v38.json"))
    derived["meta"]["kg_sha256"] = V75_KG_SHA
    derived["meta"]["pack_sha256"] = OLD_PACK_SHA
    derived["meta"]["v37_rankings_sha256"] = OLD_RANKINGS_SHA
    assert digest(derived) == OLD_DERIVED_SHA
    # Current-artifact pins; V77 separately reconstructs the complete V75/V76 KG.
    expected = {
        FIXTURES / "kg_sample.json":
            CURRENT_CONTENT.kg_sha256,
        ROOT / "tests/fixtures/cat_mobile_app_pack_contract.json":
            CURRENT_CONTENT.mobile_sha256,
        FIXTURES / "lant_rejection_tombstones.json":
            "e3d8166aa5c59c2ff1e7cba06be4fcd505d02a8c98224ab2fe6126d6c826cc29",
    }
    assert all(
        hashlib.sha256(path.read_bytes()).hexdigest() == sha for path, sha in expected.items()
    )


def test_five_candidate_dispositions_and_two_independent_promotions_are_bound() -> None:
    candidate = REVIEW / "gastronomie/candidates.json"
    sha = "sha256:" + hashlib.sha256(candidate.read_bytes()).hexdigest()
    assert sha == "sha256:baef6c35007d7da7982058f0bbb220b3fbf95f91377247412368f63898e38431"
    factual = read(REVIEW / "gastronomie/verify_factual.json")
    quality = read(REVIEW / "gastronomie/verify_quality.json")
    assert factual["candidate_sha256"] == quality["candidate_sha256"] == sha
    assert {row["ref"]: row["verdict"] for row in quality["instances"]} == {
        "contexto[0]": "keep", "contexto[1]": "drop", "contexto[2]": "keep",
        "contexto[3]": "drop", "contexto[4]": "drop",
    }
    artifact = read(REVIEW / "verdicts/contexto_verdicts.json")
    assert artifact["batch"]["version"] == 2
    assert artifact["batch"]["input_ids"] == list(NEW_TARGETS)
    assert artifact["verdicts"] == dict.fromkeys(NEW_TARGETS, "promote")
    reviewer_ids = set()
    for role in ("analyst", "verifier"):
        raw_path = REVIEW / f"{role}-review.json"
        raw = read(raw_path)
        reviewer_ids.add(raw["reviewer"].casefold())
        assert artifact["provenance"][role]["sha256"] == (
            "sha256:" + hashlib.sha256(raw_path.read_bytes()).hexdigest()
        )
        assert raw["input_ids"] == list(NEW_TARGETS)
        assert raw["role"] == role
        for row, final in zip(raw["items"], artifact["perItem"], strict=True):
            assert final[f"{role}_review"] == row
            assert row["verdict"] == final[role] == final["final"] == "promote"
            assert row["review_binding"] == final["review_binding"]
    assert len(reviewer_ids) == 2


@pytest.mark.parametrize(
    ("opener", "answer", "target"),
    [("grătar", "mici", "n_gas_mici"),
     ("salată", "salata de boeuf", "n_gas_salata_boeuf")],
)
def test_new_targets_are_publicly_selectable_warm_and_winnable(
    opener: str, answer: str, target: str,
) -> None:
    pytest.importorskip("django")
    from django.test import Client

    seed = contexto_seed(target, difficulty="usor")
    client = Client()
    response = client.post(
        f"/api/wordgames/contexto/games?seed={seed}&category=gastronomie&difficulty=usor"
    )
    assert response.status_code == 200
    initial = response.json()
    assert not ({"target", "solution", "score", "source_id"} & initial.keys())
    url = f"/api/wordgames/contexto/games/{initial['game_id']}/guess"
    warm = client.post(url, {"text": opener}, content_type="application/json")
    assert warm.status_code == 200
    assert warm.json()["guess"]["distance"] == 1
    assert warm.json()["guess"]["rank"] == 2
    assert warm.json()["guess"]["temperature"] == "Fierbinte"
    assert warm.json()["won"] is False
    win = client.post(url, {"text": answer}, content_type="application/json")
    assert win.status_code == 200
    assert win.json()["won"] is True
    assert win.json()["guess"]["id"] == target
    assert win.json()["attempts"] == 2
    assert win.json()["score"] == 940
