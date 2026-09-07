"""Reviewed food forms retain their owners and work through real typed-game APIs."""

from __future__ import annotations

import ast
import hashlib
import json
import unicodedata
from pathlib import Path

import pytest

from tests.content_history import before_v83_fixture, before_v84_fixture, v83_added_forms

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "docs/reviews/v83-food-input-and-feedback"
PROPOSAL = json.loads((REVIEW / "morphology-candidates.json").read_bytes())
ALIASES = PROPOSAL["aliases"]


def test_authoring_module_contains_exactly_the_reviewed_aliases():
    tree = ast.parse((ROOT / "scripts/food_input_v83_data.py").read_text())
    assignment = next(
        node for node in tree.body
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)
        and node.target.id == "ALIAS_ADDITIONS"
    )
    assert {owner: list(forms) for owner, forms in ast.literal_eval(assignment.value).items()} == (
        ALIASES
    )


def test_alias_only_kg_delta_reconstructs_complete_v82_fixture():
    blob = (ROOT / "cat_de_roman_esti/fixtures/kg_sample.json").read_bytes()
    assert blob == (ROOT / "tests/fixtures/kg_sample.json").read_bytes()
    current = before_v84_fixture(json.loads(blob))
    before = before_v83_fixture(json.loads(blob))
    encoded = (json.dumps(before, ensure_ascii=False, indent=2) + "\n").encode()
    assert hashlib.sha256(encoded).hexdigest() == (
        "fc3ea5a27e3bcb1da72fb3146316d7709da37012dddc494de0d6d4370862a331"
    )
    assert current["kg_edges"] == before["kg_edges"]
    assert current["kg_puzzles"] == before["kg_puzzles"]
    assert len(current["kg_nodes"]) == len(before["kg_nodes"]) == 2365
    assert sum(len(n.get("aliases", [])) for n in current["kg_nodes"]) == 8475
    assert len(v83_added_forms()) == 24


def test_every_old_authored_surface_retains_its_exact_owner():
    from cat_de_roman_esti.wordgames.service import get_service

    svc = get_service()
    baseline = before_v83_fixture(json.loads(
        (ROOT / "cat_de_roman_esti/fixtures/kg_sample.json").read_bytes()
    ))
    surfaces = sorted({
        text for node in baseline["kg_nodes"]
        for text in (node["id"], node["label_ro"], *node.get("aliases", []))
    })
    rows = [(surface, svc.resolve(surface)) for surface in surfaces]
    assert len(rows) == 13180
    assert hashlib.sha256(
        json.dumps(rows, ensure_ascii=False, separators=(",", ":")).encode()
    ).hexdigest() == "3aa29ea6b44c97be75eade80826545e90d93c44a8c2ca1fd1d3b10f2f6afbb65"


def test_exact_forms_match_the_independent_review_and_preserve_omissions():
    from cat_de_roman_esti.wordgames.service import get_service

    review = json.loads((REVIEW / "morphology-review.json").read_bytes())
    assert review["morphology_candidate_sha256"] == (
        "sha256:" + hashlib.sha256((REVIEW / "morphology-candidates.json").read_bytes()).hexdigest()
    )
    assert {row["owner"]: row["surfaces"] for row in review["items"]} == ALIASES
    assert all(row["verdict"] == "accept" for row in review["items"])
    svc = get_service()
    assert all(svc.resolve(form) == owner for owner, forms in ALIASES.items() for form in forms)
    for form in PROPOSAL["omitted_surfaces"]:
        assert svc.resolve(form) is None


@pytest.mark.parametrize(("owner", "forms"), list(ALIASES.items()))
def test_forms_are_exact_nonwinning_guesses_and_repeat_across_spelling_variants(owner, forms):
    pytest.importorskip("django")
    from django.test import Client

    from cat_de_roman_esti.wordgames import contexto
    from cat_de_roman_esti.wordgames.service import get_service

    target = "n_gas_sarmale"
    client = Client()
    gid = contexto.store.create(contexto._build_session(target, "normal", None))
    url = f"/api/wordgames/contexto/games/{gid}"
    try:
        for form in forms:
            variants = (
                form,
                f"  {form.upper()}  ",
                unicodedata.normalize("NFD", form.replace("ș", "ş").replace("ț", "ţ")),
            )
            for spelling in variants:
                body = client.post(
                    url + "/guess", {"text": spelling}, content_type="application/json",
                ).json()
                assert body["ok"] and not body["won"]
                assert not body.get("needs_confirmation")
                assert body["guess"]["id"] == owner
                assert body["guess"]["label"] == get_service().label(owner)
                assert body["attempts"] == 1
                assert target not in str(body) and "anchor_id" not in str(body)
        resumed = client.get(url).json()
        assert resumed["attempts"] == 1 and len(resumed["guesses"]) == 1
    finally:
        contexto.store.delete(gid)


@pytest.mark.parametrize(("owner", "forms"), list(ALIASES.items()))
def test_every_reviewed_form_can_win_its_own_target(owner, forms):
    pytest.importorskip("django")
    from django.test import Client

    from cat_de_roman_esti.wordgames import contexto

    client = Client()
    for form in forms:
        gid = contexto.store.create(contexto._build_session(owner, "normal", None))
        try:
            result = client.post(
                f"/api/wordgames/contexto/games/{gid}/guess", {"text": form},
                content_type="application/json",
            ).json()
            assert result["won"] and result["guess"]["id"] == owner
            assert result["attempts"] == 1 and result["score"] == 1000
        finally:
            contexto.store.delete(gid)


@pytest.mark.parametrize(("owner", "forms"), list(ALIASES.items()))
def test_forms_are_legal_direct_hops_in_lant(owner, forms):
    pytest.importorskip("django")
    from django.test import Client

    from cat_de_roman_esti.wordgames import lant
    from cat_de_roman_esti.wordgames.service import get_service

    svc = get_service()
    start = next(node for node in svc.predecessor_ids(owner) if node != owner)
    client = Client()
    for form in forms:
        session = lant.LantSession(
            start=start, target=owner, optimal=1, difficulty="usor", chain=[start],
        )
        gid = lant.store.create(session)
        try:
            result = client.post(
                f"/api/wordgames/lant/games/{gid}/move", {"text": form},
                content_type="application/json",
            ).json()
            assert result["ok"] and result["won"] and result["moves"] == 1
        finally:
            lant.store.delete(gid)
