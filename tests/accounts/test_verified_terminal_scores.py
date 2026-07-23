"""Six public games update ranking records only from their terminal server action."""

from __future__ import annotations

import pytest

from cat_de_roman_esti.accounts.models import VerifiedBest
from cat_de_roman_esti.wordgames import alchimie, conexiuni, contexto, intrusul, lant, perechi
from cat_de_roman_esti.wordgames.service import get_service

pytestmark = pytest.mark.django_db


def _post(client, url: str, payload: dict):
    return client.post(url, data=payload, content_type="application/json")


def _assert_record(user, game: str, score: int) -> None:
    rows = VerifiedBest.objects.filter(user=user, game=game)
    assert rows.count() == 1
    assert rows.get().score == score


def test_intrusul_terminal_guess_records_server_score(auth_client, give_consent):
    give_consent(auth_client)
    created = auth_client.post("/api/wordgames/intrusul/games?seed=390").json()
    session = intrusul.store.get(created["game_id"])
    assert session is not None

    won = _post(
        auth_client,
        f"/api/wordgames/intrusul/games/{created['game_id']}/guess",
        {"id": session.intruder},
    )
    assert won.status_code == 200 and won.json()["won"] is True
    _assert_record(auth_client.cat_user, "intrusul", won.json()["score"])


def test_perechi_terminal_match_records_server_score(auth_client, give_consent):
    give_consent(auth_client)
    created = auth_client.post("/api/wordgames/perechi/games?seed=391").json()
    session = perechi.store.get(created["game_id"])
    assert session is not None

    result = None
    for pair in session.pairs:
        result = _post(
            auth_client,
            f"/api/wordgames/perechi/games/{created['game_id']}/match",
            {"ids": list(pair.members)},
        )
        assert result.status_code == 200
    assert result is not None and result.json()["won"] is True
    _assert_record(auth_client.cat_user, "perechi", result.json()["score"])


def test_conexiuni_terminal_group_records_server_score(auth_client, give_consent):
    give_consent(auth_client)
    created = auth_client.post("/api/wordgames/conexiuni/games?seed=392").json()
    session = conexiuni.store.get(created["game_id"])
    assert session is not None

    result = None
    for members in session.groups.values():
        result = _post(
            auth_client,
            f"/api/wordgames/conexiuni/games/{created['game_id']}/guess",
            {"ids": list(members)},
        )
        assert result.status_code == 200
    assert result is not None and result.json()["won"] is True
    _assert_record(auth_client.cat_user, "conexiuni", result.json()["score"])


def test_contexto_terminal_guess_records_server_score(auth_client, give_consent):
    give_consent(auth_client)
    created = auth_client.post("/api/wordgames/contexto/games?seed=393").json()
    session = contexto.store.get(created["game_id"])
    assert session is not None

    won = _post(
        auth_client,
        f"/api/wordgames/contexto/games/{created['game_id']}/guess",
        {"text": session.target},
    )
    assert won.status_code == 200 and won.json()["won"] is True
    _assert_record(auth_client.cat_user, "contexto", won.json()["score"])


def test_lant_terminal_move_records_server_score(auth_client, give_consent):
    give_consent(auth_client)
    service = get_service()
    start = next(node_id for node_id in service.all_ids() if service.neighbor_ids(node_id))
    target = service.neighbor_ids(start)[0]
    session = lant.LantSession(
        start=start,
        target=target,
        optimal=1,
        chain=[start],
    )
    game_id = lant.store.create(session)

    won = _post(
        auth_client,
        f"/api/wordgames/lant/games/{game_id}/move",
        {"text": service.label(target)},
    )
    assert won.status_code == 200 and won.json()["won"] is True
    _assert_record(auth_client.cat_user, "lant", won.json()["score"])


def test_alchimie_terminal_combine_records_server_score(auth_client, give_consent):
    give_consent(auth_client)
    created = auth_client.post(
        "/api/wordgames/alchimie/games?seed=394&difficulty=usor"
    ).json()
    session = alchimie.store.get(created["game_id"])
    assert session is not None

    result = None
    for _ in range(alchimie.ALCHIMIE_MAX_ACTIONS):
        useful = alchimie._useful_pair(session)
        assert useful is not None
        result = _post(
            auth_client,
            f"/api/wordgames/alchimie/games/{created['game_id']}/combine",
            {"a": useful[0], "b": useful[1]},
        )
        assert result.status_code == 200
        if result.json()["won"]:
            break
    assert result is not None and result.json()["won"] is True
    _assert_record(auth_client.cat_user, "alchimie", result.json()["score"])
