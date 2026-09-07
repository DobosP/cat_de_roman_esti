"""V82 keeps the body meaning of burtă except for its defining soup target."""

from __future__ import annotations

import hashlib
import json

import pytest

pytest.importorskip("django")

from django.test import Client  # noqa: E402

from cat_de_roman_esti.graph import Graph  # noqa: E402
from cat_de_roman_esti.wordgames import contexto  # noqa: E402
from cat_de_roman_esti.wordgames.contexto_projection import (  # noqa: E402
    PROJECTION_NEIGHBORHOODS,
    PROJECTION_TERMS,
    resolve_projection,
    suggest_projection,
)
from cat_de_roman_esti.wordgames.service import WordGameService, get_service  # noqa: E402
from tests.content_history import before_v84_projection_rows  # noqa: E402

SOUP = "n_gas_ciorba_burta"
BODY = "n_v4sti_corp"
PUBLIC_ID = "ctxp_b32f1b5e793a06a4c804"
V81_PROJECTION_SHA256 = "a422bf531cfadb66ffe3aacc08db8ac51c3cc06e74bb5e9d762f54353d2088a1"


def _game(target: str) -> tuple[Client, str]:
    game_id = contexto.store.create(contexto._build_session(target, "usor", None))
    return Client(), f"/api/wordgames/contexto/games/{game_id}"


def _guess(client: Client, url: str, text: str) -> dict:
    response = client.post(url + "/guess", {"text": text}, content_type="application/json")
    assert response.status_code == 200
    return response.json()


def _assert_secret_hidden(body: dict, target: str) -> None:
    assert "target" not in body and "solution" not in body
    assert target not in str(body) and get_service().label(target) not in str(body)
    assert "anchor_id" not in str(body)


def _node(node_id: str) -> dict:
    return {"id": node_id, "label_ro": node_id, "category": "test"}


def _edge(edge_id: str, src: str, dst: str, *, bidirectional: bool = False) -> dict:
    return {
        "id": edge_id, "src_id": src, "dst_id": dst, "relation": "related_to",
        "strength": 1.0, "bidirectional": bidirectional, "is_distractor": False,
    }


def test_all_projection_rows_and_body_meaning_remain_exactly_v81():
    rows = before_v84_projection_rows([
        (term.surface, term.anchor_id, term.domain, term.rank_penalty,
         term.mapping_kind, term.public_id)
        for term in PROJECTION_TERMS
    ])
    assert len(rows) == 472
    blob = json.dumps(rows, ensure_ascii=False, separators=(",", ":")).encode()
    assert hashlib.sha256(blob).hexdigest() == V81_PROJECTION_SHA256
    term = resolve_projection("burtă")
    assert term is not None
    assert (term.key, term.domain, term.anchor_id, term.rank_penalty,
            term.mapping_kind, term.public_id) == (
        "burta", "corp", BODY, 1, "domain_fallback", PUBLIC_ID,
    )
    assert get_service().resolve("burtă") is None
    assert set(PROJECTION_NEIGHBORHOODS) == {"gem", "burta"}
    assert PROJECTION_NEIGHBORHOODS["burta"].include_direct_neighbors is False
    gem = PROJECTION_NEIGHBORHOODS["gem"]
    assert (gem.anchor_id, gem.min_strength, gem.include_direct_neighbors) == (
        "n_v17gas_dulceata", 0.60, True,
    )


def test_burta_feedback_changes_for_exactly_one_target_in_the_entire_graph():
    svc = get_service()
    term = resolve_projection("burtă")
    assert term is not None
    changed = {
        target for target in svc.all_ids()
        if contexto._projection_anchor_id(svc, term, target) != BODY
    }
    assert changed == {SOUP}
    assert contexto._projection_anchor_id(svc, term, SOUP) == SOUP


def test_exact_target_mode_does_not_expand_to_strong_or_bidirectional_neighbors():
    term = resolve_projection("burtă")
    assert term is not None
    ids = [SOUP, BODY, "strong", "reverse", "bidirectional", "unconnected"]
    svc = WordGameService(Graph.from_records(
        [_node(node_id) for node_id in ids],
        [_edge("e1", SOUP, "strong"), _edge("e2", "reverse", SOUP),
         _edge("e3", SOUP, "bidirectional", bidirectional=True)],
    ))
    assert contexto._projection_anchor_id(svc, term, SOUP) == SOUP
    for target in ids[1:]:
        assert contexto._projection_anchor_id(svc, term, target) == BODY
    missing_soup = WordGameService(Graph.from_records([_node(BODY), _node("other")], []))
    assert contexto._projection_anchor_id(missing_soup, term, SOUP) == BODY
    assert contexto._projection_anchor_id(missing_soup, term, "other") == BODY


def test_burta_is_hot_nonwinning_and_repeat_resume_preserve_the_round():
    client, url = _game(SOUP)
    try:
        first = _guess(client, url, "burtă")
        assert first["ok"] is True and first["won"] is False and first["attempts"] == 1
        guess = first["guess"]
        assert (guess["id"], guess["label"], guess["temperature"], guess["rank"]) == (
            PUBLIC_ID, "Burtă", "Fierbinte", 2,
        )
        assert guess["closeness"] < 100
        _assert_secret_hidden(first, SOUP)
        for spelling in (" BURTĂ ", "burta"):
            repeated = _guess(client, url, spelling)
            assert repeated["attempts"] == 1 and repeated["won"] is False
            assert repeated["feedback"]["kind"] == "repeat"
            assert repeated["guess"] == guess
            _assert_secret_hidden(repeated, SOUP)
        resumed = client.get(url).json()
        assert resumed["attempts"] == 1 and resumed["guesses"] == first["guesses"]
        _assert_secret_hidden(resumed, SOUP)
        exact = _guess(client, url, get_service().label(SOUP))
        assert exact["won"] is True and exact["attempts"] == 2
        assert exact["guess"]["id"] == SOUP and exact["guess"]["rank"] == 1
    finally:
        contexto.store.delete(url.rsplit("/", 1)[-1])


@pytest.mark.parametrize("target", [SOUP, BODY])
def test_unknown_suggestions_hide_burta_when_its_effective_anchor_is_the_secret(target):
    assert [term.surface for term in suggest_projection("burttă")] == ["burtă"]
    client, url = _game(target)
    try:
        response = _guess(client, url, "burttă")
        assert response["ok"] is False and response["attempts"] == 0
        assert "Burtă" not in response["suggestions"]
        assert PUBLIC_ID not in str(response)
        _assert_secret_hidden(response, target)
        resumed = client.get(url).json()
        assert resumed["attempts"] == 0 and resumed["guesses"] == []
    finally:
        contexto.store.delete(url.rsplit("/", 1)[-1])


def test_burta_typo_can_still_be_suggested_for_an_unrelated_target():
    client, url = _game("n_gas_muraturi")
    try:
        response = _guess(client, url, "burttă")
        assert response["ok"] is False and response["attempts"] == 0
        assert "Burtă" in response["suggestions"]
        _assert_secret_hidden(response, "n_gas_muraturi")
    finally:
        contexto.store.delete(url.rsplit("/", 1)[-1])
