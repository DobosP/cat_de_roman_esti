"""A related bread-family input keeps its identity and a closed feedback scope."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from django.test import Client

from cat_de_roman_esti.wordgames import contexto as C
from cat_de_roman_esti.wordgames.contexto_feedback import EXACT_TARGET_FEEDBACK_PAIRS
from cat_de_roman_esti.wordgames.contexto_projection import resolve_projection
from cat_de_roman_esti.wordgames.service import get_service
from tests.content_history import before_v88_feedback_pairs

BRIOSA = "n_v87_food_briosa"
PAINE = "n_v4gas_paine"
ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("word", ["brioșă", "brioșei", "brioșe", "brioșele", "brioșelor"])
def test_native_bread_family_forms_are_hot_distinct_and_free_to_repeat(word):
    svc = get_service()
    assert svc.resolve(word) == BRIOSA and resolve_projection(word) is None
    gid = C.store.create(C._build_session(PAINE, "usor", None))
    url = f"/api/wordgames/contexto/games/{gid}"
    client = Client()
    try:
        response = client.post(url + "/guess", {"text": word}, content_type="application/json")
        assert response.status_code == 200
        body = response.json()
        assert body["ok"] and not body["won"] and body["attempts"] == 1
        assert (body["guess"]["id"], body["guess"]["label"], body["guess"]["rank"]) == (
            BRIOSA, "Brioșă", 2,
        )
        assert body["guess"]["temperature"] == "Fierbinte"
        assert body["guess"]["closeness"] < 100
        encoded = json.dumps(body, ensure_ascii=False)
        assert PAINE not in encoded and '"target"' not in encoded and '"solution"' not in encoded
        assert svc.label(PAINE) not in encoded
        repeat = client.post(
            url + "/guess", {"text": "  BRIOSA  "}, content_type="application/json",
        ).json()
        assert repeat["attempts"] == 1 and repeat["feedback"]["kind"] == "repeat"
        assert repeat["guess"] == body["guess"]
        assert client.get(url).json()["guesses"] == body["guesses"]
        won = client.post(
            url + "/guess", {"text": svc.label(PAINE)}, content_type="application/json",
        ).json()
        assert won["won"] and won["guess"]["id"] == PAINE and won["guess"]["rank"] == 1
    finally:
        C.store.delete(gid)


def test_bread_exception_is_one_closed_scope_and_cannot_be_borrowed_by_projections():
    svc = get_service()
    before = before_v88_feedback_pairs(EXACT_TARGET_FEEDBACK_PAIRS)
    assert len(before) == 9 and EXACT_TARGET_FEEDBACK_PAIRS - before == {(BRIOSA, PAINE)}
    for target in [*svc.graph.nodes, "missing_target"]:
        assert C._feedback_anchor_id(svc, BRIOSA, target) == (PAINE if target == PAINE else BRIOSA)
        assert C._feedback_anchor_id(svc, BRIOSA, target, allow_exact_pairs=False) == BRIOSA
    assert svc.link(BRIOSA, PAINE) is None
    assert C._feedback_anchor_id(svc, "missing_source", PAINE) == "missing_source"


def test_internal_exact_briosa_win_is_preserved_without_promoting_its_hidden_target():
    from cat_de_roman_esti.wordgames.packs import get_pack

    assert all(row.payload["target"] != BRIOSA for row in get_pack().pool("contexto"))
    gid = C.store.create(C._build_session(BRIOSA, "usor", None))
    try:
        body = Client().post(
            f"/api/wordgames/contexto/games/{gid}/guess", {"text": "brioșă"},
            content_type="application/json",
        ).json()
        assert body["won"] and body["score"] == 1000 and body["guess"]["rank"] == 1
    finally:
        C.store.delete(gid)


def test_bread_proposal_has_a_separate_bound_independent_judgment():
    folder = ROOT / "docs/reviews/v88-cross-game-quality/bread-feedback"
    review = json.loads((folder / "independent-review.json").read_bytes())
    assert review["decision"] == "accept_exact_native_pair_with_disclosed_sense_limit"
    assert review["blockers"] == []
    # The independent record must bind the actual authored proposal, not a substitute.
    digest = hashlib.sha256((folder / "proposal.json").read_bytes()).hexdigest()
    assert review["bindings"][str((folder / "proposal.json").relative_to(ROOT))] == digest
