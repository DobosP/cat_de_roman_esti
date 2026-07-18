"""Offline, deterministic tests for the "Cald sau Rece" (contexto) word game."""

import threading

import pytest

pytest.importorskip("django")

from django.test import Client  # noqa: E402


def make_client() -> Client:
    return Client()


def _post_json(c: Client, url: str, payload: dict) -> dict:
    return c.post(url, payload, content_type="application/json").json()


SEED = 1


def _collect_key_values(obj: object, key_name: str) -> list[object]:
    found: list[object] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key == key_name:
                found.append(value)
            else:
                found.extend(_collect_key_values(value, key_name))
    elif isinstance(obj, list):
        for item in obj:
            found.extend(_collect_key_values(item, key_name))
    return found


def _collect_strings(obj: object) -> set[str]:
    found: set[str] = set()
    if isinstance(obj, str):
        found.add(obj)
    elif isinstance(obj, dict):
        for value in obj.values():
            found |= _collect_strings(value)
    elif isinstance(obj, list):
        for item in obj:
            found |= _collect_strings(item)
    return found


def _assert_secret_hidden(body: dict, target_id: str, target_label: str) -> None:
    assert "target" not in body
    assert "solution" not in body
    assert not _collect_key_values(body, "solution")
    assert target_id not in _collect_key_values(body, "id")
    assert target_label not in _collect_strings(body)


def _target_of(seed: int = SEED, difficulty: str = "normal"):
    """The id + a distance-1 neighbour of the seeded secret, read from the engine.

    Specific labels/distances drift as the bundled KG is regenerated, so tests derive
    them from the engine's own selection rather than pinning to a hand-named id.
    """
    import random

    from cat_de_roman_esti.wordgames.contexto import _pick_target
    from cat_de_roman_esti.wordgames.packs import get_pack
    from cat_de_roman_esti.wordgames.service import get_service

    svc = get_service()
    curated = get_pack().pick_seeded("contexto", random.Random(seed), difficulty=difficulty)
    target = str(curated.payload["target"]) if curated else _pick_target(seed, difficulty).target
    # A genuine incoming distance-1 guess. Contexto distance is directed guess -> target,
    # so an outgoing target neighbour is not necessarily a valid hot guess.
    neighbour = next(nid for nid, distance in svc.distances_to(target).items() if distance == 1)
    return target, svc.label(target), neighbour, svc.label(neighbour)


def _reveal_target_label(client, *, seed: int = SEED, difficulty: str = "normal", daily=None):
    """Reveal the secret label via giveup on a throwaway game with the same instance."""
    if daily is not None:
        url = f"/api/wordgames/contexto/games?difficulty={difficulty}&daily={daily}"
    else:
        url = f"/api/wordgames/contexto/games?difficulty={difficulty}&seed={seed}"
    gid = client.post(url).json()["game_id"]
    return client.post(f"/api/wordgames/contexto/games/{gid}/giveup").json()["target"]["label"]


def test_create_game_hides_target() -> None:
    c = make_client()
    target_id, target_label, _, _ = _target_of()
    res = c.post(f"/api/wordgames/contexto/games?seed={SEED}")
    assert res.status_code == 200
    body = res.json()
    assert body["attempts"] == 0
    assert body["won"] is False
    assert body["guesses"] == []
    assert body["reachable_count"] >= 120
    _assert_secret_hidden(body, target_id, target_label)


def test_unknown_concept_not_counted() -> None:
    c = make_client()
    gid = c.post(f"/api/wordgames/contexto/games?seed={SEED}").json()["game_id"]
    res = c.post(
        f"/api/wordgames/contexto/games/{gid}/guess",
        {"text": "zzz nu exista zzz"},
        content_type="application/json",
    )
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is False
    assert body["message"] == "Nu cunosc acest concept"
    assert body["attempts"] == 0


def test_guess_reports_temperature_and_closeness() -> None:
    c = make_client()
    target_id, _, neighbour_id, neighbour_label = _target_of()
    gid = c.post(f"/api/wordgames/contexto/games?seed={SEED}").json()["game_id"]
    res = c.post(
        f"/api/wordgames/contexto/games/{gid}/guess",
        {"text": neighbour_label},
        content_type="application/json",
    )
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    g = body["guess"]
    # A distance-1 neighbour of the secret reads as "Fierbinte" and is internally
    # consistent: non-zero distance, a real (sub-win) closeness in bounds.
    assert g["id"] == neighbour_id
    assert g["distance"] == 1
    assert 1 < g["rank"] <= body["reachable_count"]
    assert g["temperature"] == "Fierbinte"
    assert 0 <= g["closeness"] <= 100
    assert g["closeness"] < 100  # only the actual target reads 100
    assert body["attempts"] == 1
    assert body["won"] is False
    assert g["attempt_number"] == 1
    assert body["feedback"] == {
        "kind": "first",
        "message": f"Primul reper: #{g['rank']}.",
    }
    assert "target" not in body
    assert body["guesses"][0]["rank"] == g["rank"]


def test_winning_playthrough_reveals_target() -> None:
    c = make_client()
    target_id, _, neighbour_id, neighbour_label = _target_of()
    # Reveal the secret label on a separate (same-seed) game, then play it for real.
    target_label = _reveal_target_label(c)
    gid = c.post(f"/api/wordgames/contexto/games?seed={SEED}").json()["game_id"]
    # one warm guess first, then the exact target (accent-insensitive resolution)
    _post_json(
        c,
        f"/api/wordgames/contexto/games/{gid}/guess",
        {"text": neighbour_label},
    )
    res = c.post(
        f"/api/wordgames/contexto/games/{gid}/guess",
        {"text": target_label},
        content_type="application/json",
    )
    body = res.json()
    assert body["ok"] is True
    assert body["won"] is True
    assert body["guess"]["distance"] == 0
    assert body["guess"]["rank"] == 1
    assert body["guess"]["temperature"] == "Gasit"
    assert body["guess"]["closeness"] == 100
    assert body["guess"]["attempt_number"] == 2
    assert body["feedback"] == {
        "kind": "found",
        "message": "Exact — ai găsit răspunsul!",
    }
    assert body["target"]["id"] == target_id
    # guesses are sorted best-first: the winning guess leads.
    assert body["guesses"][0]["distance"] == 0


def test_duplicate_guess_not_double_counted() -> None:
    c = make_client()
    gid = c.post(f"/api/wordgames/contexto/games?seed={SEED}").json()["game_id"]
    first = _post_json(c, f"/api/wordgames/contexto/games/{gid}/guess", {"text": "Banat"})
    res = _post_json(c, f"/api/wordgames/contexto/games/{gid}/guess", {"text": "Banat"})
    assert res["attempts"] == 1
    assert first["guess"]["attempt_number"] == 1
    assert res["guess"]["attempt_number"] == 1
    assert res["feedback"] == {
        "kind": "repeat",
        "message": f"Deja încercat — rămâne #{res['guess']['rank']}.",
    }
    assert res["guesses"] == first["guesses"]


def test_concurrent_duplicate_guess_is_counted_once() -> None:
    from cat_de_roman_esti.wordgames.contexto import store

    c = make_client()
    gid = c.post(f"/api/wordgames/contexto/games?seed={SEED}").json()["game_id"]
    session = store.get(gid)
    assert session is not None
    rendezvous = threading.Barrier(2)

    class RendezvousGuesses(dict):
        def get(self, key: object, default=None):
            existing = super().get(key, default)
            try:
                rendezvous.wait(timeout=0.15)
            except threading.BrokenBarrierError:
                pass
            return existing

    session.guesses = RendezvousGuesses()
    start = threading.Barrier(3)
    responses: list[dict] = []

    def submit() -> None:
        request_client = make_client()
        start.wait()
        response = request_client.post(
            f"/api/wordgames/contexto/games/{gid}/guess",
            {"text": "Banat"},
            content_type="application/json",
        )
        assert response.status_code == 200, response.content.decode()
        responses.append(response.json())

    threads = [threading.Thread(target=submit) for _ in range(2)]
    for thread in threads:
        thread.start()
    start.wait()
    for thread in threads:
        thread.join(timeout=2)
        assert not thread.is_alive()

    assert sorted(body["feedback"]["kind"] for body in responses) == ["first", "repeat"]
    assert {body["attempts"] for body in responses} == {1}
    assert session.attempts == len(session.guesses) == len(session.order) == 1


def test_comparative_feedback_covers_public_rank_movements_only() -> None:
    from cat_de_roman_esti.wordgames.contexto import (
        GuessRecord,
        _guess_feedback_payload,
        _pick_target,
    )

    session = _pick_target(SEED, "normal")

    def record(node_id: str, rank: int, attempt_number: int) -> GuessRecord:
        return GuessRecord(
            id=node_id,
            label=node_id,
            distance=2,
            temperature="Rece",
            closeness=50,
            rank=rank,
            anchor_id=node_id,
            attempt_number=attempt_number,
        )

    first = record("first", 100, 1)
    assert _guess_feedback_payload(session, first, is_new=True, found=False)["kind"] == "first"
    session.guesses[first.id] = first
    session.order.append(first.id)

    best = record("best", 40, 2)
    best_feedback = _guess_feedback_payload(session, best, is_new=True, found=False)
    assert best_feedback == {
        "kind": "new-best",
        "message": "Cel mai bun: cu 60 locuri mai aproape.",
        "rank_delta": 60,
    }
    session.guesses[best.id] = best
    session.order.append(best.id)

    colder = record("colder", 90, 3)
    assert _guess_feedback_payload(session, colder, is_new=True, found=False) == {
        "kind": "colder",
        "message": "Mai rece cu 50 locuri.",
        "rank_delta": -50,
    }
    session.guesses[colder.id] = colder
    session.order.append(colder.id)

    warmer = record("warmer", 70, 4)
    assert _guess_feedback_payload(session, warmer, is_new=True, found=False) == {
        "kind": "warmer",
        "message": "Mai cald cu 20 locuri.",
        "rank_delta": 20,
    }
    session.guesses[warmer.id] = warmer
    session.order.append(warmer.id)

    same = record("same", 70, 5)
    assert _guess_feedback_payload(session, same, is_new=True, found=False) == {
        "kind": "same",
        "message": "La fel de aproape ca încercarea trecută.",
        "rank_delta": 0,
    }
    assert set(_guess_feedback_payload(session, same, is_new=True, found=False)) == {
        "kind",
        "message",
        "rank_delta",
    }


def test_distinct_attempt_numbers_survive_best_first_resorting_and_get() -> None:
    from cat_de_roman_esti.wordgames.contexto import store
    from cat_de_roman_esti.wordgames.service import get_service

    c = make_client()
    created = c.post(f"/api/wordgames/contexto/games?seed={SEED}").json()
    gid = created["game_id"]
    session = store.get(gid)
    assert session is not None
    svc = get_service()

    accepted: list[dict] = []
    for node_id in svc.all_ids():
        label = svc.label(node_id)
        if node_id == session.target or svc.resolve(label) != node_id:
            continue
        body = _post_json(
            c,
            f"/api/wordgames/contexto/games/{gid}/guess",
            {"text": label},
        )
        if body["ok"] and body["attempts"] > len(accepted):
            accepted.append(body["guess"])
        if len(accepted) == 2:
            break

    assert [guess["attempt_number"] for guess in accepted] == [1, 2]
    fetched = c.get(f"/api/wordgames/contexto/games/{gid}").json()
    by_id = {guess["id"]: guess["attempt_number"] for guess in fetched["guesses"]}
    assert by_id[accepted[0]["id"]] == 1
    assert by_id[accepted[1]["id"]] == 2
    assert {guess["attempt_number"] for guess in fetched["guesses"]} == {1, 2}


def test_giveup_reveals_target() -> None:
    c = make_client()
    gid = c.post(f"/api/wordgames/contexto/games?seed={SEED}").json()["game_id"]
    target_id, _, _, neighbour_label = _target_of()
    res = c.post(f"/api/wordgames/contexto/games/{gid}/giveup")
    assert res.status_code == 200
    body = res.json()
    assert body["gave_up"] is True
    assert body["target"]["id"] == target_id
    # cannot guess after giving up
    after = c.post(
        f"/api/wordgames/contexto/games/{gid}/guess",
        {"text": neighbour_label},
        content_type="application/json",
    )
    assert after.status_code == 400


def test_get_state_keeps_target_hidden() -> None:
    c = make_client()
    target_id, target_label, _, _ = _target_of()
    gid = c.post(f"/api/wordgames/contexto/games?seed={SEED}").json()["game_id"]
    res = c.get(f"/api/wordgames/contexto/games/{gid}")
    assert res.status_code == 200
    _assert_secret_hidden(res.json(), target_id, target_label)


def test_rank_view_model_hides_secret_until_reveal_boundary() -> None:
    c = make_client()
    target_id, target_label, _, _ = _target_of()
    gid = c.post(f"/api/wordgames/contexto/games?seed={SEED}").json()["game_id"]

    before = _make_counted_guesses(c, gid, 3)
    _assert_secret_hidden(before, target_id, target_label)
    assert before["guesses"]
    assert all("rank" in guess for guess in before["guesses"])
    assert all(1 < guess["rank"] <= before["reachable_count"] + 1 for guess in before["guesses"])

    clue = c.post(f"/api/wordgames/contexto/games/{gid}/clue").json()
    _assert_secret_hidden(clue, target_id, target_label)

    over = c.post(f"/api/wordgames/contexto/games/{gid}/giveup").json()
    assert over["gave_up"] is True
    assert over["target"]["id"] == target_id
    assert over["target"]["label"] == target_label


def test_unknown_game_404() -> None:
    c = make_client()
    assert c.get("/api/wordgames/contexto/games/nope").status_code == 404
    assert (
        c.post(
            "/api/wordgames/contexto/games/nope/guess",
            {"text": "Banat"},
            content_type="application/json",
        ).status_code
        == 404
    )
    assert c.post("/api/wordgames/contexto/games/nope/giveup").status_code == 404


# --------------------------------------------------------------------- new: difficulty


def test_create_defaults_to_normal_and_exposes_difficulty() -> None:
    c = make_client()
    body = c.post(f"/api/wordgames/contexto/games?seed={SEED}").json()
    assert body["difficulty"] == "normal"
    assert "daily" not in body  # only present for daily challenges


@pytest.mark.parametrize("difficulty", ["usor", "normal", "greu"])
def test_difficulty_accepted_and_reachable(difficulty: str) -> None:
    c = make_client()
    body = c.post(f"/api/wordgames/contexto/games?seed={SEED}&difficulty={difficulty}").json()
    assert body["difficulty"] == difficulty
    # every tier (incl. obscure "greu") still yields a richly reachable target
    assert body["reachable_count"] >= 120


def test_unknown_difficulty_falls_back_to_normal() -> None:
    c = make_client()
    body = c.post(f"/api/wordgames/contexto/games?seed={SEED}&difficulty=imposibil").json()
    assert body["difficulty"] == "normal"


# ------------------------------------------------------------------------- new: daily


def test_daily_is_deterministic_and_echoed() -> None:
    c = make_client()
    date = "2026-06-21"
    a = c.post(f"/api/wordgames/contexto/games?daily={date}")
    b = c.post(f"/api/wordgames/contexto/games?daily={date}")
    assert a.status_code == 200 and b.status_code == 200
    abody, bbody = a.json(), b.json()
    # same date -> same instance: reveal the secret via giveup and compare.
    ta = c.post(f"/api/wordgames/contexto/games/{abody['game_id']}/giveup").json()
    tb = c.post(f"/api/wordgames/contexto/games/{bbody['game_id']}/giveup").json()
    assert ta["target"]["id"] == tb["target"]["id"]
    assert abody["daily"] == date
    assert ta["daily"] == date


def test_daily_differs_by_date() -> None:
    c = make_client()
    g1 = c.post("/api/wordgames/contexto/games?daily=2026-06-21").json()
    g2 = c.post("/api/wordgames/contexto/games?daily=2026-09-09").json()
    t1 = c.post(f"/api/wordgames/contexto/games/{g1['game_id']}/giveup").json()
    t2 = c.post(f"/api/wordgames/contexto/games/{g2['game_id']}/giveup").json()
    # Overwhelmingly likely to differ across these two unrelated dates.
    assert t1["target"]["id"] != t2["target"]["id"]


# --------------------------------------------------------------- new: score and share


def test_win_includes_score_and_share() -> None:
    c = make_client()
    _, _, _, neighbour_label = _target_of()
    target_label = _reveal_target_label(c)
    gid = c.post(f"/api/wordgames/contexto/games?seed={SEED}").json()["game_id"]
    _post_json(
        c,
        f"/api/wordgames/contexto/games/{gid}/guess",
        {"text": neighbour_label},
    )
    body = _post_json(
        c,
        f"/api/wordgames/contexto/games/{gid}/guess",
        {"text": target_label},
    )
    assert body["won"] is True
    # 2 attempts -> 1000 - 60 = 940
    assert body["score"] == 940
    share = body["share"]
    assert "Cald sau Rece" in share
    assert "2 incercari" in share
    # one emoji square per guess + the bullseye for the win
    assert "🎯" in share
    lines = share.splitlines()
    assert lines[0] == "cat_de_roman_esti · Cald sau Rece"


def test_score_rewards_fewer_attempts() -> None:
    c = make_client()
    target_label = _reveal_target_label(c)
    gid = c.post(f"/api/wordgames/contexto/games?seed={SEED}").json()["game_id"]
    body = _post_json(
        c,
        f"/api/wordgames/contexto/games/{gid}/guess",
        {"text": target_label},
    )
    assert body["won"] is True
    assert body["score"] == 1000  # solved on the first attempt


# --------------------------------------------------------------- category clue


def _make_counted_guesses(client, gid: str, count: int) -> dict:
    """Submit distinct non-target guesses until ``count`` counted attempts exist."""
    from cat_de_roman_esti.wordgames.contexto import store
    from cat_de_roman_esti.wordgames.service import get_service

    svc = get_service()
    session = store.get(gid)
    assert session is not None
    state = {}
    for nid in svc.all_ids():
        if nid == session.target:
            continue
        state = client.post(
            f"/api/wordgames/contexto/games/{gid}/guess",
            {"text": svc.label(nid)},
            content_type="application/json",
        ).json()
        assert state["ok"] is True
        assert "target" not in state
        if state["attempts"] >= count:
            return state
    raise AssertionError("could not build enough counted guesses")


def test_progressive_clues_are_category_then_strictly_warmer_without_target_leak() -> None:
    from cat_de_roman_esti.wordgames.contexto import store
    from cat_de_roman_esti.wordgames.service import get_service

    c = make_client()
    gid = c.post(f"/api/wordgames/contexto/games?seed={SEED}").json()["game_id"]
    early = c.post(f"/api/wordgames/contexto/games/{gid}/clue")
    assert early.status_code == 400

    before = _make_counted_guesses(c, gid, 3)
    assert before["clue_available"] is True
    assert before["next_clue_kind"] == "category"
    assert before["clues_used"] == 0
    assert "target" not in before
    best_before = min(guess["rank"] for guess in before["guesses"])

    clue = c.post(f"/api/wordgames/contexto/games/{gid}/clue")
    assert clue.status_code == 200, clue.content.decode()
    body = clue.json()
    session = store.get(gid)
    assert session is not None
    secret = session.target
    target_node = get_service().node(secret)
    assert body["clues_used"] == 1
    assert body["clue_kind"] == "category"
    assert body["clue"]["category"]["key"] == target_node.category
    assert body["clue"]["category"]["label"]
    assert secret not in str(body)
    assert "target" not in body

    assert body["clue_available"] is True
    assert body["next_clue_kind"] == "warmer"
    warmer = c.post(f"/api/wordgames/contexto/games/{gid}/clue")
    assert warmer.status_code == 200
    again = warmer.json()
    assert again["clue_kind"] == "warmer"
    assert again["clues_used"] == 2
    assert 1 < again["warm_clue"]["rank"] < best_before
    hinted_id = get_service().resolve(again["warm_clue"]["label"])
    assert hinted_id is not None and hinted_id != secret
    assert again["clue_available"] is False
    _assert_secret_hidden(again, secret, get_service().label(secret))

    exhausted = c.post(f"/api/wordgames/contexto/games/{gid}/clue")
    assert exhausted.status_code == 400
    assert c.get(f"/api/wordgames/contexto/games/{gid}").json()["clues_used"] == 2


def test_public_theme_skips_redundant_category_clue_without_penalty() -> None:
    c = make_client()
    created = c.post(
        "/api/wordgames/contexto/games?seed=4&difficulty=usor&category=gastronomie"
    ).json()
    assert created["board_category"] == "gastronomie"
    body = _make_counted_guesses(c, created["game_id"], 3)
    assert body["next_clue_kind"] == "warmer"
    assert body["clues_used"] == 0
    clue = c.post(f"/api/wordgames/contexto/games/{created['game_id']}/clue").json()
    assert clue["clue_kind"] == "warmer"
    assert clue["clues_used"] == 1
    assert "clue" not in clue  # category was already public; no paid duplicate


def test_no_warm_clue_is_offered_when_rank_two_is_already_the_best() -> None:
    from cat_de_roman_esti.wordgames.contexto import rank_for, store
    from cat_de_roman_esti.wordgames.service import get_service

    c = make_client()
    gid = c.post(f"/api/wordgames/contexto/games?seed={SEED}").json()["game_id"]
    session = store.get(gid)
    assert session is not None
    svc = get_service()
    ranked = sorted(
        (
            rank_for(session, distance, session.weighted_dist.get(node_id)),
            node_id,
        )
        for node_id, distance in svc.distances_to(session.target).items()
        if node_id != session.target
    )
    best_rank, best_id = ranked[0]
    assert best_rank == 2
    ids = [best_id, *(node_id for _rank, node_id in reversed(ranked) if node_id != best_id)][:3]
    for node_id in ids:
        body = _post_json(
            c,
            f"/api/wordgames/contexto/games/{gid}/guess",
            {"text": svc.label(node_id)},
        )
        assert body["ok"] is True
    category = c.post(f"/api/wordgames/contexto/games/{gid}/clue").json()
    assert category["clue_kind"] == "category"
    assert category["clue_available"] is False
    assert "next_clue_kind" not in category
    assert c.post(f"/api/wordgames/contexto/games/{gid}/clue").status_code == 400


def test_projected_rank_three_does_not_advertise_an_already_played_warmer_anchor() -> None:
    from cat_de_roman_esti.wordgames.contexto import _build_session, store
    from cat_de_roman_esti.wordgames.service import get_service

    c = make_client()
    svc = get_service()
    target = "n_arta_plastica"
    gid = store.create(_build_session(target, "normal", None))

    for surface in ("joc de masă", "joc video", "jucărie"):
        played = _post_json(
            c,
            f"/api/wordgames/contexto/games/{gid}/guess",
            {"text": surface},
        )
        assert played["ok"] is True
        assert played["guess"]["rank"] == 3
    assert played["attempts"] == 3
    assert played["next_clue_kind"] == "category"

    category = c.post(f"/api/wordgames/contexto/games/{gid}/clue")
    assert category.status_code == 200
    body = category.json()
    assert body["clue_kind"] == "category"
    assert body["clue_available"] is False
    assert "next_clue_kind" not in body
    _assert_secret_hidden(body, target, svc.label(target))

    rejected = c.post(f"/api/wordgames/contexto/games/{gid}/clue")
    assert rejected.status_code == 400
    refreshed = c.get(f"/api/wordgames/contexto/games/{gid}").json()
    assert refreshed["clue_available"] is False
    assert "next_clue_kind" not in refreshed
    _assert_secret_hidden(refreshed, target, svc.label(target))


def test_warmer_clues_prefer_familiar_words_on_approved_easy_targets() -> None:
    from cat_de_roman_esti.wordgames.contexto import (
        WARM_CLUE_MIN_SALIENCE,
        GuessRecord,
        _build_session,
        _warmer_clue_candidate,
    )
    from cat_de_roman_esti.wordgames.packs import get_pack
    from cat_de_roman_esti.wordgames.service import get_service

    svc = get_service()
    for item in get_pack().pool("contexto", difficulty="usor")[:12]:
        session = _build_session(str(item.payload["target"]), "usor", None)
        session.guesses["test-cold"] = GuessRecord(
            id="test-cold",
            label="test-cold",
            distance=999,
            temperature="Inghetat",
            closeness=0,
            rank=session.reachable + 1,
            anchor_id="test-cold",
            attempt_number=1,
        )
        clue = _warmer_clue_candidate(session)
        assert clue is not None
        node_id = svc.resolve(clue.label)
        assert node_id is not None and node_id != session.target
        node = svc.node(node_id)
        assert node is not None and node.salience >= WARM_CLUE_MIN_SALIENCE
        assert 1 < clue.rank < session.reachable + 1


def test_category_clue_penalizes_final_score_and_share() -> None:
    c = make_client()
    target_label = _reveal_target_label(c)
    gid = c.post(f"/api/wordgames/contexto/games?seed={SEED}").json()["game_id"]
    _make_counted_guesses(c, gid, 3)
    c.post(f"/api/wordgames/contexto/games/{gid}/clue")
    body = c.post(
        f"/api/wordgames/contexto/games/{gid}/guess",
        {"text": target_label},
        content_type="application/json",
    ).json()
    assert body["won"] is True
    assert body["clues_used"] == 1
    assert body["score"] == 1000 - 60 * (body["attempts"] - 1) - 120
    assert "indiciu x1" in body["share"]


def test_clue_is_unavailable_after_giveup() -> None:
    c = make_client()
    gid = c.post(f"/api/wordgames/contexto/games?seed={SEED}").json()["game_id"]
    _make_counted_guesses(c, gid, 3)
    c.post(f"/api/wordgames/contexto/games/{gid}/giveup")
    assert c.post(f"/api/wordgames/contexto/games/{gid}/clue").status_code == 400


def test_daily_win_share_includes_date() -> None:
    c = make_client()
    date = "2026-06-21"
    gid = c.post(f"/api/wordgames/contexto/games?daily={date}").json()["game_id"]
    # reveal the secret, then guess it to win cleanly
    target = c.post(f"/api/wordgames/contexto/games/{gid}/giveup")
    # giveup ends the game; start a fresh daily and win it via the revealed label.
    label = target.json()["target"]["label"]
    gid2 = c.post(f"/api/wordgames/contexto/games?daily={date}").json()["game_id"]
    body = _post_json(
        c,
        f"/api/wordgames/contexto/games/{gid2}/guess",
        {"text": label},
    )
    assert body["won"] is True
    assert date in body["share"]


def test_no_score_or_share_before_win() -> None:
    c = make_client()
    body = c.post(f"/api/wordgames/contexto/games?seed={SEED}").json()
    assert "score" not in body
    assert "share" not in body


# ------------------------------------------ Contexto-only broad guess projection (ADR-0042)


def test_projection_is_large_balanced_collision_free_and_legibility_audited() -> None:
    from collections import Counter

    from cat_de_roman_esti.wordgames.contexto_projection import (
        PROJECTION_LEGIBILITY_AUDIT,
        PROJECTION_OVERRIDE_CLUSTERS,
        PROJECTION_TERMS,
        normalize_projection_surface,
        resolve_projection,
    )
    from cat_de_roman_esti.wordgames.service import get_service

    svc = get_service()
    keys = [term.key for term in PROJECTION_TERMS]
    domains = Counter(term.domain for term in PROJECTION_TERMS)
    assert len(PROJECTION_TERMS) == 444
    assert len(domains) == 26
    assert min(domains.values()) >= 14
    assert len(keys) == len(set(keys))
    assert len({term.public_id for term in PROJECTION_TERMS}) == len(PROJECTION_TERMS)
    assert all(term.public_id.startswith("ctxp_") for term in PROJECTION_TERMS)
    assert all(svc.exists(term.anchor_id) for term in PROJECTION_TERMS)
    assert all(svc.resolve(term.surface) is None for term in PROJECTION_TERMS)
    assert all(term.rank_penalty in (0, 1) for term in PROJECTION_TERMS)

    assert {domain for domain, _surface, _anchor in PROJECTION_LEGIBILITY_AUDIT} == set(domains)
    for domain, surface, anchor in PROJECTION_LEGIBILITY_AUDIT:
        term = resolve_projection(surface)
        assert term is not None
        assert term.domain == domain
        assert term.anchor_id == anchor
        assert term.key == normalize_projection_surface(surface)
    # Every explicit semantic cluster is audited, not just its representative.
    for anchor, surfaces in PROJECTION_OVERRIDE_CLUSTERS:
        assert svc.exists(anchor)
        for surface in surfaces:
            term = resolve_projection(surface)
            if term is None:
                assert svc.resolve(surface) is not None  # intentionally screened KG owner
            else:
                assert term.anchor_id == anchor


def test_every_projection_term_uses_an_explicit_cluster_or_named_domain_fallback() -> None:
    from cat_de_roman_esti.wordgames.contexto_projection import (
        PROJECTION_DOMAIN_POLICIES,
        PROJECTION_OVERRIDE_CLUSTERS,
        PROJECTION_TERMS,
        normalize_projection_surface,
    )
    from cat_de_roman_esti.wordgames.service import get_service

    svc = get_service()
    explicit_anchors = {
        normalize_projection_surface(surface): anchor
        for anchor, surfaces in PROJECTION_OVERRIDE_CLUSTERS
        for surface in surfaces
    }
    assert {term.domain for term in PROJECTION_TERMS} == set(PROJECTION_DOMAIN_POLICIES)
    for domain, policy in PROJECTION_DOMAIN_POLICIES.items():
        assert policy.rationale.strip(), domain
        if policy.fallback_anchor_id is not None:
            assert svc.exists(policy.fallback_anchor_id), domain

    for term in PROJECTION_TERMS:
        policy = PROJECTION_DOMAIN_POLICIES[term.domain]
        if term.mapping_kind == "explicit":
            assert term.key in explicit_anchors, term.surface
            assert term.anchor_id == explicit_anchors[term.key], term.surface
        elif term.mapping_kind == "domain_fallback":
            assert term.key not in explicit_anchors, term.surface
            assert policy.fallback_anchor_id is not None, term.surface
            assert term.anchor_id == policy.fallback_anchor_id, term.surface
        else:
            raise AssertionError(f"unknown mapping kind for {term.surface!r}: {term.mapping_kind}")


def test_projection_review_examples_use_honest_semantic_anchors() -> None:
    from cat_de_roman_esti.wordgames.contexto_projection import resolve_projection

    explicit_examples = {
        "a repara": "n_v32_workshop_hand_ciocan",
        "a construi": "n_v32_workshop_hand_ciocan",
        "a aprinde": "n_v4sti_foc",
        "a stinge": "n_v4sti_foc",
        "bancă comercială": "n_v4soc_banca",
        "pinguin": "n_v4sti_pasare",
    }
    for surface, anchor in explicit_examples.items():
        term = resolve_projection(surface)
        assert term is not None
        assert term.anchor_id == anchor
        assert term.mapping_kind == "explicit"

    for surface in ("șarpe", "broască", "șopârlă", "melc", "delfin", "balenă"):
        term = resolve_projection(surface)
        assert term is not None
        assert term.anchor_id == "n_v4sti_animal"
        assert term.mapping_kind == "domain_fallback"

    for surface in (
        "a sta",
        "a opri",
        "a împinge",
        "a trage",
        "a ridica",
        "a pune",
        "a lua",
        "a căra",
        "a lipi",
    ):
        assert resolve_projection(surface) is None


def test_projection_guess_uses_anchor_scale_and_dedupes_normalized_surface() -> None:
    from cat_de_roman_esti.wordgames.contexto import rank_for, store
    from cat_de_roman_esti.wordgames.contexto_projection import resolve_projection
    from cat_de_roman_esti.wordgames.service import get_service

    c = make_client()
    gid = c.post(f"/api/wordgames/contexto/games?seed={SEED}").json()["game_id"]
    session = store.get(gid)
    assert session is not None
    svc = get_service()
    first = resolve_projection("brioșă")
    second = resolve_projection("chec")
    assert first is not None and second is not None
    assert first.anchor_id == second.anchor_id

    played = _post_json(c, f"/api/wordgames/contexto/games/{gid}/guess", {"text": "brioșă"})
    distance = svc.distance(first.anchor_id, session.target)
    expected = rank_for(session, distance, session.weighted_dist.get(first.anchor_id))
    expected = max(2, min(session.reachable + 1, expected + first.rank_penalty))
    assert played["ok"] is True
    assert played["guess"]["id"] == first.public_id
    assert played["guess"]["rank"] == expected
    assert played["attempts"] == 1

    # Accent/case variants are the same canonical surface and therefore free repeats.
    repeated = _post_json(
        c,
        f"/api/wordgames/contexto/games/{gid}/guess",
        {"text": "  BRIOSA  "},
    )
    assert repeated["attempts"] == 1
    # A different authored surface remains a distinct guess even when its anchor matches.
    other = _post_json(c, f"/api/wordgames/contexto/games/{gid}/guess", {"text": "chec"})
    assert other["guess"]["id"] == second.public_id
    assert other["attempts"] == 2


def test_projection_mapped_to_target_anchor_never_wins_even_with_zero_penalty() -> None:
    from cat_de_roman_esti.wordgames.contexto import _build_session, store
    from cat_de_roman_esti.wordgames.contexto_projection import PROJECTION_TERMS
    from cat_de_roman_esti.wordgames.service import get_service

    term = next(item for item in PROJECTION_TERMS if item.rank_penalty == 0)
    svc = get_service()
    c = make_client()
    gid = store.create(_build_session(term.anchor_id, "normal", None))
    projected = _post_json(
        c,
        f"/api/wordgames/contexto/games/{gid}/guess",
        {"text": term.surface},
    )
    assert projected["ok"] is True
    assert projected["won"] is False
    assert projected["guess"]["id"] != term.anchor_id
    assert projected["guess"]["distance"] == 1
    assert projected["guess"]["rank"] >= 2
    assert projected["guess"]["closeness"] < 100
    _assert_secret_hidden(projected, term.anchor_id, svc.label(term.anchor_id))

    exact = _post_json(
        c,
        f"/api/wordgames/contexto/games/{gid}/guess",
        {"text": svc.label(term.anchor_id)},
    )
    assert exact["won"] is True
    assert exact["guess"]["rank"] == 1


def test_projection_typo_suggestions_filter_terms_anchored_on_the_secret() -> None:
    from cat_de_roman_esti.wordgames.contexto import _build_session, store
    from cat_de_roman_esti.wordgames.contexto_projection import resolve_projection
    from cat_de_roman_esti.wordgames.service import get_service

    term = resolve_projection("smoothie")
    assert term is not None
    svc = get_service()
    c = make_client()
    gid = store.create(_build_session(term.anchor_id, "normal", None))
    body = _post_json(
        c,
        f"/api/wordgames/contexto/games/{gid}/guess",
        {"text": "smothie"},
    )
    assert body["ok"] is False
    assert term.label not in body["suggestions"]
    assert body["attempts"] == 0
    _assert_secret_hidden(body, term.anchor_id, svc.label(term.anchor_id))


def test_projection_feedback_spans_rank_and_temperature_buckets_on_easy_pack() -> None:
    from collections import Counter, defaultdict

    from cat_de_roman_esti.wordgames.contexto import _build_session, rank_for, temperature_for
    from cat_de_roman_esti.wordgames.contexto_projection import PROJECTION_TERMS
    from cat_de_roman_esti.wordgames.packs import get_pack
    from cat_de_roman_esti.wordgames.service import get_service

    svc = get_service()
    targets = get_pack().pool("contexto", difficulty="usor")[:12]
    assert len(targets) == 12
    for item in targets:
        session = _build_session(str(item.payload["target"]), "usor", None)
        hop_dist = svc.distances_to(session.target)
        feedback: dict[tuple[str, int], tuple[int, str]] = {}
        by_domain: dict[str, list[int]] = defaultdict(list)
        ranks: list[int] = []
        temperatures: list[str] = []
        for term in PROJECTION_TERMS:
            cache_key = (term.anchor_id, term.rank_penalty)
            if cache_key not in feedback:
                distance = hop_dist.get(term.anchor_id)
                weighted = session.weighted_dist.get(term.anchor_id)
                rank = rank_for(session, distance, weighted)
                rank = max(2, min(session.reachable + 1, rank + term.rank_penalty))
                effective_distance = 1 if distance == 0 else distance
                feedback[cache_key] = (
                    rank,
                    temperature_for(
                        session,
                        effective_distance,
                        weighted,
                        rank_override=rank,
                    ),
                )
            rank, temperature = feedback[cache_key]
            ranks.append(rank)
            temperatures.append(temperature)
            by_domain[term.domain].append(rank)
        assert len(set(ranks)) >= 40
        assert len(set(temperatures)) >= 3
        assert max(Counter(ranks).values()) / len(ranks) <= 0.15
        # At least 24/26 domains have more than one meaningful scoring anchor.
        assert sum(len(set(domain_ranks)) >= 2 for domain_ranks in by_domain.values()) >= 24


def test_contexto_session_keeps_original_bounded_shape_and_store_limits() -> None:
    from cat_de_roman_esti.wordgames.contexto import _pick_target, store

    session = _pick_target(SEED, "normal")
    fields = session.__dataclass_fields__
    assert "hop_dist" not in fields
    assert "clue_candidates" not in fields
    assert not hasattr(session, "projection_feedback")
    assert store._ttl == 7200
    assert store._max == 1000


# ----------------------------------------------- new: instance quality (playtest floor)


@pytest.mark.parametrize("difficulty", ["usor", "normal", "greu"])
def test_every_target_has_a_responsive_warm_band(difficulty: str) -> None:
    """No degenerate "everything is Inghetat" secret ships in any tier.

    Each generated target must clear the responsive-zone floor: a healthy count of
    concepts at distance 1..5 so guesses spread across temperatures. We exercise many
    seeds (deterministic) and assert the floor holds for all of them.
    """
    from cat_de_roman_esti.wordgames.contexto import (
        MIN_RESPONSIVE,
        _pick_target,
        _responsive_count,
    )
    from cat_de_roman_esti.wordgames.service import get_service

    svc = get_service()
    for seed in range(60):
        session = _pick_target(seed, difficulty)
        near = _responsive_count(svc.distances_to(session.target))
        assert near >= MIN_RESPONSIVE, (
            f"{difficulty} seed={seed} target={session.target} responsive={near} < {MIN_RESPONSIVE}"
        )


def test_session_histogram_uses_directed_guess_to_target_distances(monkeypatch) -> None:
    """One-way outbound nodes must not enter Contexto's inbound rank population."""
    from cat_de_roman_esti.graph import Graph
    from cat_de_roman_esti.wordgames import contexto
    from cat_de_roman_esti.wordgames.service import WordGameService

    nodes = [
        {"id": node_id, "label_ro": node_id, "category": "test"}
        for node_id in ("far", "near", "target", "outbound")
    ]
    edges = [
        {
            "id": f"e_{src}_{dst}",
            "src_id": src,
            "dst_id": dst,
            "bidirectional": 0,
            "is_distractor": 0,
        }
        for src, dst in (
            ("far", "near"),
            ("near", "target"),
            ("target", "outbound"),
        )
    ]
    svc = WordGameService(Graph.from_records(nodes, edges))
    monkeypatch.setattr(contexto, "get_service", lambda: svc)

    session = contexto._build_session("target", "normal", None)

    assert svc.distances_from("target") == {"target": 0, "outbound": 1}
    assert svc.distances_to("target") == {"target": 0, "near": 1, "far": 2}
    assert session.reachable == 3
    assert session.dist_hist == {0: 1, 1: 1, 2: 1}
    assert contexto.rank_for(session, svc.distance("near", "target")) == 2
    assert contexto.closeness_for(session, svc.distance("near", "target")) == 50

    # Seed 0 keeps this two-item order. Forward traversal would wrongly accept `far`
    # because it can reach the rest of the graph; inbound traversal correctly skips it.
    monkeypatch.setattr(contexto, "MIN_REACHABLE", 3)
    monkeypatch.setattr(contexto, "MIN_RESPONSIVE", 2)
    monkeypatch.setattr(
        contexto,
        "_difficulty_pool",
        lambda _svc, _difficulty, _category=None: ["far", "target"],
    )
    assert contexto._pick_target(0).target == "target"


def test_seeds_yield_varied_targets() -> None:
    """The seeded selection still produces wide variety, not one repeated target."""
    from cat_de_roman_esti.wordgames.contexto import _pick_target

    targets = {_pick_target(seed, "normal").target for seed in range(40)}
    assert len(targets) >= 15


def test_usor_targets_are_more_famous_than_greu() -> None:
    """'usor' must skew to well-known concepts; 'greu' to obscure ones."""
    from cat_de_roman_esti.wordgames.contexto import _pick_target
    from cat_de_roman_esti.wordgames.service import get_service

    svc = get_service()

    def avg_salience(diff: str) -> float:
        sals = [svc.node(_pick_target(s, diff).target).salience for s in range(40)]
        return sum(sals) / len(sals)

    assert avg_salience("usor") > avg_salience("greu")


# ------------------------------------------------- new: closeness mapping correctness


def test_only_the_win_reads_closeness_100() -> None:
    """A near miss must never report 100 — that is reserved for the actual target.

    Otherwise a distance-1 guess can read 100 and be ambiguous with a win. We pick a
    target, then drive a distance-1 neighbour guess and assert its closeness is < 100.
    """
    from cat_de_roman_esti.wordgames.service import get_service

    svc = get_service()
    _, _, neighbour, _ = _target_of()
    # directed adjacency: pick a neighbour that is truly one BFS hop away (see _target_of).
    c = make_client()
    gid = c.post(f"/api/wordgames/contexto/games?seed={SEED}").json()["game_id"]
    body = c.post(
        f"/api/wordgames/contexto/games/{gid}/guess",
        {"text": svc.label(neighbour)},
        content_type="application/json",
    ).json()
    assert body["ok"] is True
    assert body["guess"]["distance"] == 1
    assert body["guess"]["temperature"] == "Fierbinte"
    assert body["guess"]["closeness"] < 100


def test_closeness_three_way_split_reachable_vs_unreachable() -> None:
    """closeness distinguishes win (100), reachable (1..99), unreachable (0)."""
    from cat_de_roman_esti.wordgames.contexto import _pick_target, closeness_for

    session = _pick_target(SEED, "normal")
    assert closeness_for(session, 0) == 100  # the target
    assert closeness_for(session, None) == 0  # unreachable / disconnected
    # the coldest *reachable* bucket stays >= 1, so it is visibly warmer than unreachable
    coldest = max(session.dist_hist)
    assert 1 <= closeness_for(session, coldest) <= 99


# ----------------------------------------------- new: fuzzy suggestions (ADR-0021)


def _typo(label: str) -> str:
    """Drop an interior character so the text no longer resolves but stays fuzzy-close."""
    mid = len(label) // 2
    return label[:mid] + label[mid + 1 :]


def _heavy_typo(label: str) -> str:
    """Drop two interior characters: still close enough for :meth:`suggest` but below
    the confident auto-accept bar (ADR-0022), so the ADVISORY path stays exercised."""
    mid = len(label) // 2
    return label[:mid] + label[mid + 2 :]


def test_unknown_guess_returns_fuzzy_suggestions_and_stays_uncounted() -> None:
    """A mangled non-target concept yields a "did you mean" hint, no attempt spent.

    Updated for ADR-0022: a single dropped character now usually auto-corrects, so the
    advisory path is driven with a heavier typo that resolve_fuzzy() must NOT accept.
    """
    from cat_de_roman_esti.wordgames.contexto import store
    from cat_de_roman_esti.wordgames.service import get_service

    c = make_client()
    gid = c.post(f"/api/wordgames/contexto/games?seed={SEED}").json()["game_id"]
    svc = get_service()
    target = store.get(gid).target
    # A non-target concept whose two-char-dropped label stays suggestible but is NOT
    # confidently auto-correctable (the advisory path must be the one that answers).
    concept = next(
        nid
        for nid in svc.all_ids()
        if nid != target
        and 6 <= len(svc.label(nid)) <= 10
        and svc.resolve(_heavy_typo(svc.label(nid))) is None
        and svc.resolve_fuzzy(_heavy_typo(svc.label(nid))) is None
        and svc.label(nid) in svc.suggest(_heavy_typo(svc.label(nid)))
    )
    label = svc.label(concept)
    body = c.post(
        f"/api/wordgames/contexto/games/{gid}/guess",
        {"text": _heavy_typo(label)},
        content_type="application/json",
    ).json()
    assert body["ok"] is False
    assert body["attempts"] == 0  # unresolved guesses never count (pinned)
    assert label in body["suggestions"]
    assert "Poate cautai" in body["message"]


def test_fuzzy_suggestions_never_leak_the_target_label() -> None:
    """The secret's own label must never be offered as a suggestion (ADR-0009/0021).

    Updated for ADR-0022: the typo must fall BELOW the auto-accept bar — a confidently
    corrected target typo is now a legitimate win instead (covered separately). The
    session is built directly on a target whose heavy typo stays advisory, so this
    boundary is always exercised instead of depending on the seeded target's label.
    """
    from cat_de_roman_esti.wordgames.contexto import _build_session, store
    from cat_de_roman_esti.wordgames.service import get_service

    c = make_client()
    svc = get_service()
    target = next(
        nid
        for nid in svc.all_ids()
        if 6 <= len(svc.label(nid)) <= 10
        and svc.resolve(_heavy_typo(svc.label(nid))) is None
        and svc.resolve_fuzzy(_heavy_typo(svc.label(nid))) is None
        and svc.label(nid) in svc.suggest(_heavy_typo(svc.label(nid)))
    )
    target_label = svc.label(target)
    typo = _heavy_typo(target_label)
    gid = store.create(_build_session(target, "normal", None))
    # The raw fuzzy matcher WOULD surface the secret; the endpoint must strip it.
    assert target_label in svc.suggest(typo)
    body = c.post(
        f"/api/wordgames/contexto/games/{gid}/guess",
        {"text": typo},
        content_type="application/json",
    ).json()
    assert body["ok"] is False
    assert body["attempts"] == 0
    assert target_label not in body["suggestions"]
    _assert_secret_hidden(body, target, target_label)


def test_service_suggest_dedupes_and_is_deterministic() -> None:
    from cat_de_roman_esti.wordgames.service import get_service

    svc = get_service()
    a = svc.suggest("Bucuresti")
    b = svc.suggest("Bucuresti")
    assert a == b  # deterministic
    assert len(a) == len(set(a))  # each node offered once
    assert svc.suggest("xxqqzznope") == []  # nothing close -> empty


# ----------------------------------------- new: confident auto-accept (ADR-0022)


def _auto_correctable_concept(svc, exclude: str) -> tuple[str, str]:
    """A (node id, typo) pair whose one-char-dropped label confidently auto-corrects."""
    for nid in svc.all_ids():
        if nid == exclude:
            continue
        label = svc.label(nid)
        if len(label) < 7:
            continue
        typo = _typo(label)
        if svc.resolve(typo) is None and svc.resolve_fuzzy(typo) == nid:
            return nid, typo
    raise AssertionError("no auto-correctable label found in the fixture")


def test_resolve_fuzzy_confident_unique_ambiguous_and_below_bar() -> None:
    """The auto-accept resolver fires only on a high-confidence, unambiguous near-miss."""
    from cat_de_roman_esti.graph import Graph
    from cat_de_roman_esti.wordgames.service import WordGameService

    nodes = [
        {"id": "n_u", "label_ro": "strugure", "category": "test"},
        # Two distinct nodes one character apart: any typo between them is ambiguous.
        {"id": "n_a", "label_ro": "portocala", "category": "test"},
        {"id": "n_b", "label_ro": "portocale", "category": "test"},
    ]
    svc = WordGameService(Graph.from_records(nodes, []))
    # High-confidence unique typo (ratio 14/15 ≈ 0.93, nothing else close) -> corrected.
    assert svc.resolve_fuzzy("strugur") == "n_u"
    assert svc.resolve_fuzzy("strugur") == "n_u"  # deterministic
    # Equidistant between two distinct nodes (both 0.94) -> ambiguous -> None.
    assert svc.resolve_fuzzy("portocal") is None
    # Close enough for suggest() but below the 0.90 bar (10/13 ≈ 0.77+) -> None.
    assert svc.resolve_fuzzy("strug") is None
    # Exact input still resolves exactly; empty input never resolves.
    assert svc.resolve_fuzzy("Strugure") == "n_u"
    assert svc.resolve_fuzzy("") is None


def test_typo_auto_accepts_counts_attempt_and_names_correction() -> None:
    """A unique high-confidence typo is played as the corrected concept (ADR-0022)."""
    from cat_de_roman_esti.wordgames.contexto import store
    from cat_de_roman_esti.wordgames.service import get_service

    c = make_client()
    gid = c.post(f"/api/wordgames/contexto/games?seed={SEED}").json()["game_id"]
    svc = get_service()
    target = store.get(gid).target
    concept, typo = _auto_correctable_concept(svc, exclude=target)
    label = svc.label(concept)
    body = c.post(
        f"/api/wordgames/contexto/games/{gid}/guess",
        {"text": typo},
        content_type="application/json",
    ).json()
    assert body["ok"] is True
    assert body["guess"]["id"] == concept
    assert body["guess"]["label"] == label
    assert body["message"] == f"Am înțeles: {label}."
    assert body["attempts"] == 1  # auto-accepted guesses count normally
    assert body["won"] is False
    assert "target" not in body
    # The same typo replayed maps to the same node: deduplicated like any repeat guess.
    again = c.post(
        f"/api/wordgames/contexto/games/{gid}/guess",
        {"text": typo},
        content_type="application/json",
    ).json()
    assert again["attempts"] == 1


def test_typo_of_the_target_is_a_legitimate_win() -> None:
    """A confidently corrected target typo WINS — a typo must not rob the answer."""
    from cat_de_roman_esti.wordgames.service import get_service

    c = make_client()
    svc = get_service()
    target_label = _reveal_target_label(c)
    target = svc.resolve(target_label)
    typo = _typo(target_label)
    if svc.resolve(typo) is not None or svc.resolve_fuzzy(typo) != target:
        pytest.skip("secret label does not confidently auto-correct on this fixture")
    gid = c.post(f"/api/wordgames/contexto/games?seed={SEED}").json()["game_id"]
    body = c.post(
        f"/api/wordgames/contexto/games/{gid}/guess",
        {"text": typo},
        content_type="application/json",
    ).json()
    assert body["ok"] is True
    assert body["won"] is True
    assert body["guess"]["distance"] == 0
    assert body["guess"]["closeness"] == 100
    assert body["message"] == f"Am înțeles: {target_label}."
    assert body["attempts"] == 1
    assert body["target"]["id"] == target
    assert body["score"] == 1000  # solved on the first (auto-accepted) attempt


# ----------------------------------------- new: graded similarity ranking (ADR-0021)


def test_within_bucket_rank_is_finer_when_strengths_differ(monkeypatch) -> None:
    """Two guesses the same hop count away split by path tightness (edge strength)."""
    from cat_de_roman_esti.graph import Graph
    from cat_de_roman_esti.wordgames import contexto
    from cat_de_roman_esti.wordgames.service import WordGameService

    nodes = [
        {"id": n, "label_ro": n, "category": "test"} for n in ("strong", "weak", "far", "target")
    ]
    edges = [
        # both `strong` and `weak` are one hop to target, but via edges of different strength
        {"id": "e_s", "src_id": "strong", "dst_id": "target", "bidirectional": 0, "strength": 0.9},
        {"id": "e_w", "src_id": "weak", "dst_id": "target", "bidirectional": 0, "strength": 0.2},
        # `far` is two hops (through `strong`)
        {"id": "e_f", "src_id": "far", "dst_id": "strong", "bidirectional": 0, "strength": 0.9},
    ]
    svc = WordGameService(Graph.from_records(nodes, edges))
    monkeypatch.setattr(contexto, "get_service", lambda: svc)
    session = contexto._build_session("target", "normal", None)

    r_strong = contexto.rank_for(session, 1, svc.weighted_distances_to("target")["strong"])
    r_weak = contexto.rank_for(session, 1, svc.weighted_distances_to("target")["weak"])
    r_far = contexto.rank_for(session, 2, svc.weighted_distances_to("target")["far"])
    # tighter path ranks strictly better within the bucket...
    assert r_strong < r_weak
    # ...and the whole hop bucket still outranks the next hop bucket (hop ordering kept).
    assert r_weak < r_far


def test_hop_ordering_is_preserved_across_buckets() -> None:
    """Every bucket-d rank is strictly smaller than every bucket-(d+1) rank."""
    from cat_de_roman_esti.wordgames.contexto import _pick_target, rank_for

    session = _pick_target(SEED, "normal")
    prev_max = -1
    for d in sorted(session.sorted_weighted):
        ranks = [rank_for(session, d, w) for w in session.sorted_weighted[d]]
        assert min(ranks) > prev_max
        prev_max = max(ranks)


def test_temperature_is_monotonic_and_pins_found_and_win() -> None:
    """Warmth never rises as rank grows; only d==0 is Gasit and only the win reads 100."""
    from cat_de_roman_esti.wordgames.contexto import (
        _pick_target,
        closeness_for,
        rank_for,
        temperature_for,
    )
    from cat_de_roman_esti.wordgames.service import get_service

    warmth = {"Gasit": 6, "Fierbinte": 5, "Cald": 4, "Caldut": 3, "Rece": 2, "Inghetat": 1}
    svc = get_service()
    session = _pick_target(SEED, "normal")
    dist = svc.distances_to(session.target)
    pairs = sorted(
        (
            rank_for(session, d, session.weighted_dist[nid]),
            warmth[temperature_for(session, d, session.weighted_dist[nid])],
        )
        for nid, d in dist.items()
    )
    assert all(pairs[i][1] >= pairs[i + 1][1] for i in range(len(pairs) - 1))
    # Invariants at the extremes.
    assert temperature_for(session, 0) == "Gasit"
    assert rank_for(session, 0, 0.0) == 1
    assert closeness_for(session, 0) == 100
    # A non-win reachable guess never reads 100.
    assert all(
        closeness_for(session, d, session.weighted_dist[nid]) < 100
        for nid, d in dist.items()
        if d != 0
    )


def test_ranks_are_deterministic_for_the_same_instance() -> None:
    """Two sessions on the same seed produce identical precomputed rank structure."""
    from cat_de_roman_esti.wordgames.contexto import _pick_target

    a = _pick_target(SEED, "normal")
    b = _pick_target(SEED, "normal")
    assert a.target == b.target
    assert a.sorted_weighted == b.sorted_weighted
    assert a.closer_than == b.closer_than
