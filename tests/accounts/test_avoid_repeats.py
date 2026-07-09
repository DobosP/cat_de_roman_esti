"""Avoid-repeats: signed-in players don't get a curated puzzle they've finished (accounts ON)."""

from __future__ import annotations

import random

import pytest

from cat_de_roman_esti.accounts.models import PlayedPuzzle
from cat_de_roman_esti.accounts.progress import finished_pack_ids, record_played
from cat_de_roman_esti.wordgames.packs import get_pack

pytestmark = pytest.mark.django_db


def _contexto_category_with_curated():
    pack = get_pack()
    cats = sorted({i.category for i in pack.pool("contexto") if i.category})
    for c in cats:
        ids = [i.id for i in pack.pool("contexto", category=c)]
        if ids:
            return c, ids
    return None, []


def test_pick_seeded_excludes_finished():
    pack = get_pack()
    cat, ids = _contexto_category_with_curated()
    assert ids, "fixture must have curated contexto instances"
    excluded = {ids[0]}
    picked = set()
    for s in range(80):
        item = pack.pick_seeded("contexto", random.Random(s), category=cat, exclude_ids=excluded)
        if item is not None:
            picked.add(item.id)
    assert ids[0] not in picked


def test_record_and_finished_roundtrip(make_google_user):
    user = make_google_user()
    record_played(user, "contexto", "X1")
    record_played(user, "contexto", "X1")  # idempotent
    record_played(user, "lant", "Y1")
    assert finished_pack_ids(user, "contexto") == {"X1"}
    assert finished_pack_ids(user, "lant") == {"Y1"}
    assert PlayedPuzzle.objects.filter(user=user).count() == 2


def test_giveup_records_finished_curated(auth_client):
    cat, ids = _contexto_category_with_curated()
    assert ids
    created = auth_client.post(
        f"/api/wordgames/contexto/games?category={cat}", content_type="application/json"
    )
    assert created.status_code == 200
    game_id = created.json()["game_id"]

    gave_up = auth_client.post(
        f"/api/wordgames/contexto/games/{game_id}/giveup", content_type="application/json"
    )
    assert gave_up.status_code == 200

    recorded = finished_pack_ids(auth_client.cat_user, "contexto")
    assert len(recorded) == 1
    assert recorded.issubset(set(ids))  # a real curated instance from that category


def test_anonymous_play_records_nothing(client):
    cat, _ = _contexto_category_with_curated()
    created = client.post(
        f"/api/wordgames/contexto/games?category={cat}", content_type="application/json"
    )
    assert created.status_code == 200
    game_id = created.json()["game_id"]
    client.post(
        f"/api/wordgames/contexto/games/{game_id}/giveup", content_type="application/json"
    )
    # Anonymous players are never tracked.
    assert PlayedPuzzle.objects.count() == 0
