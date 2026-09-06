"""V76: a correctly accented unsupported sense must not play the pasta concept."""

from __future__ import annotations

import hashlib
import json
import unicodedata

import pytest

pytest.importorskip("django")

from django.test import Client  # noqa: E402

from cat_de_roman_esti.graph import Graph  # noqa: E402
from cat_de_roman_esti.wordgames import contexto, lant  # noqa: E402
from cat_de_roman_esti.wordgames.service import WordGameService, get_service  # noqa: E402

PASTA = "n_v3gas_paste"
HOLIDAY_FORMS = ("Paște", "Paștele")


@pytest.mark.parametrize("surface", HOLIDAY_FORMS)
@pytest.mark.parametrize("variant", ("plain", "case-space", "decomposed", "legacy-cedilla"))
def test_explicit_accented_senses_are_neither_resolved_nor_suggested(surface, variant):
    if variant == "case-space":
        surface = f" \t{surface.upper()}\n"
    elif variant == "decomposed":
        surface = unicodedata.normalize("NFD", surface)
    elif variant == "legacy-cedilla":
        surface = unicodedata.normalize("NFD", surface.replace("ș", "ş"))
    svc = get_service()
    assert svc.resolve(surface) is None
    assert svc.resolve_fuzzy(surface) is None
    assert svc.suggest(surface) == []


def test_every_existing_label_id_and_alias_keeps_its_resolution():
    """Snapshot all 13,177 authored surfaces before the V76 behavior change."""
    svc = get_service()
    surfaces = sorted({
        text
        for node in svc.graph.nodes.values()
        for text in (node.id, node.label_ro, *node.aliases)
    })
    rows = [(surface, svc.resolve(surface)) for surface in surfaces]
    assert len(rows) == 13177
    digest = hashlib.sha256(
        json.dumps(rows, ensure_ascii=False, separators=(",", ":")).encode()
    ).hexdigest()
    assert digest == "12affbd7c5cad237a200e64264ff0ee77e544f8016d3f66412ed92d677c6fc00"
    for surface in ("Paste", "pastele", "PASTE FAINOASE", "paste făinoase"):
        assert svc.resolve(surface) == PASTA
    assert svc.resolve("Masa de Paste") == svc.resolve("Masa de Paște")
    assert svc.resolve("sarmaluțe") == svc.resolve("sărmăluțe")


@pytest.mark.parametrize("surface", HOLIDAY_FORMS)
@pytest.mark.parametrize("target", (PASTA, "n_gas_cozonac"))
def test_contexto_rejects_the_wrong_sense_without_changing_or_revealing_the_game(surface, target):
    client = Client()
    game_id = contexto.store.create(contexto._build_session(target, "usor", None))
    url = f"/api/wordgames/contexto/games/{game_id}"
    before = client.get(url).json()
    response = client.post(url + "/guess", {"text": surface}, content_type="application/json")
    assert response.status_code == 200
    rejected = response.json()
    assert rejected["ok"] is False
    assert rejected["attempts"] == 0
    assert rejected["guesses"] == []
    assert rejected["suggestions"] == []
    assert not rejected.get("needs_confirmation")
    assert "resolved_label" not in rejected
    assert "target" not in rejected
    assert target not in response.content.decode()
    assert client.get(url).json() == before

    won = client.post(
        url + "/guess", {"text": get_service().label(target)}, content_type="application/json"
    ).json()
    assert won["ok"] is True
    assert won["won"] is True
    assert won["attempts"] == 1


@pytest.mark.parametrize("surface", HOLIDAY_FORMS)
def test_lant_cannot_win_by_folding_a_holiday_to_a_legal_pasta_hop(surface):
    client = Client()
    start = "n_v2gas_branza"
    assert get_service().link(start, PASTA) is not None
    session = lant.LantSession(
        start=start, target=PASTA, optimal=1, difficulty="usor", chain=[start]
    )
    game_id = lant.store.create(session)
    url = f"/api/wordgames/lant/games/{game_id}"
    before = client.get(url).json()
    assert lant._resolve_neighbor(surface, start, PASTA) is None
    response = client.post(url + "/move", {"text": surface}, content_type="application/json")
    assert response.status_code == 200
    assert response.json()["ok"] is False
    assert response.json()["suggestions"] == []
    assert client.get(url).json() == before
    won = client.post(url + "/move", {"text": "Paste"}, content_type="application/json").json()
    assert won["ok"] is True
    assert won["won"] is True
    assert won["moves"] == 1


@pytest.mark.parametrize("surface", HOLIDAY_FORMS)
def test_lant_visible_label_matching_cannot_bypass_the_sense_guard(monkeypatch, surface):
    graph = Graph.from_records(
        [
            {"id": "n_start", "label_ro": "Brânză", "category": "gastronomie"},
            {"id": PASTA, "label_ro": "Paste", "category": "gastronomie",
             "aliases": ["pastele"]},
        ],
        [{"id": "edge", "src_id": "n_start", "dst_id": PASTA,
          "relation": "related_to", "label_ro": "se servește cu", "strength": 1.0,
          "is_distractor": 0, "bidirectional": 0}],
    )
    svc = WordGameService(graph)
    monkeypatch.setattr(lant, "get_service", lambda: svc)
    client = Client()
    session = lant.LantSession(
        start="n_start", target=PASTA, optimal=1, difficulty="usor", chain=["n_start"]
    )
    game_id = lant.store.create(session)
    url = f"/api/wordgames/lant/games/{game_id}"
    before = client.get(url).json()
    assert [choice["label"] for choice in before["choices"]] == ["Paste"]
    rejected = client.post(url + "/move", {"text": surface}, content_type="application/json")
    assert rejected.status_code == 200
    assert rejected.json()["ok"] is False
    assert rejected.json()["suggestions"] == []
    assert client.get(url).json() == before
    won = client.post(
        url + "/move", {"text": before["choices"][0]["label"]}, content_type="application/json"
    ).json()
    assert won["won"] is True
    assert won["moves"] == 1
