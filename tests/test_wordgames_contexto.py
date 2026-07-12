"""Offline, deterministic tests for the "Cald sau Rece" (contexto) word game."""

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
    curated = get_pack().pick_seeded(
        "contexto", random.Random(seed), difficulty=difficulty
    )
    target = str(curated.payload["target"]) if curated else _pick_target(seed, difficulty).target
    # A genuine incoming distance-1 guess. Contexto distance is directed guess -> target,
    # so an outgoing target neighbour is not necessarily a valid hot guess.
    neighbour = next(
        nid for nid, distance in svc.distances_to(target).items() if distance == 1
    )
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
    assert body["target"]["id"] == target_id
    # guesses are sorted best-first: the winning guess leads.
    assert body["guesses"][0]["distance"] == 0


def test_duplicate_guess_not_double_counted() -> None:
    c = make_client()
    gid = c.post(f"/api/wordgames/contexto/games?seed={SEED}").json()["game_id"]
    _post_json(c, f"/api/wordgames/contexto/games/{gid}/guess", {"text": "Banat"})
    res = _post_json(c, f"/api/wordgames/contexto/games/{gid}/guess", {"text": "Banat"})
    assert res["attempts"] == 1


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


def test_category_clue_unlocks_after_three_attempts_without_target_leak() -> None:
    from cat_de_roman_esti.wordgames.contexto import store
    from cat_de_roman_esti.wordgames.service import get_service

    c = make_client()
    gid = c.post(f"/api/wordgames/contexto/games?seed={SEED}").json()["game_id"]
    early = c.post(f"/api/wordgames/contexto/games/{gid}/clue")
    assert early.status_code == 400

    before = _make_counted_guesses(c, gid, 3)
    assert before["clue_available"] is True
    assert before["clues_used"] == 0
    assert "target" not in before

    clue = c.post(f"/api/wordgames/contexto/games/{gid}/clue")
    assert clue.status_code == 200, clue.content.decode()
    body = clue.json()
    session = store.get(gid)
    assert session is not None
    secret = session.target
    target_node = get_service().node(secret)
    assert body["clues_used"] == 1
    assert body["clue_available"] is False
    assert body["clue"]["category"]["key"] == target_node.category
    assert body["clue"]["category"]["label"]
    assert secret not in str(body)
    assert "target" not in body

    again = c.post(f"/api/wordgames/contexto/games/{gid}/clue").json()
    assert again["clues_used"] == 1  # repeated reads do not stack penalties


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
            f"{difficulty} seed={seed} target={session.target} "
            f"responsive={near} < {MIN_RESPONSIVE}"
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


def test_unknown_guess_returns_fuzzy_suggestions_and_stays_uncounted() -> None:
    """A typo of a real non-target concept yields a "did you mean" hint, no attempt spent."""
    from cat_de_roman_esti.wordgames.contexto import store
    from cat_de_roman_esti.wordgames.service import get_service

    c = make_client()
    gid = c.post(f"/api/wordgames/contexto/games?seed={SEED}").json()["game_id"]
    svc = get_service()
    target = store.get(gid).target
    # A non-target concept with a long-enough label to survive one dropped character.
    concept = next(
        nid
        for nid in svc.all_ids()
        if nid != target and len(svc.label(nid)) >= 6 and svc.resolve(_typo(svc.label(nid)))
        is None and svc.suggest(_typo(svc.label(nid)))
    )
    label = svc.label(concept)
    body = c.post(
        f"/api/wordgames/contexto/games/{gid}/guess",
        {"text": _typo(label)},
        content_type="application/json",
    ).json()
    assert body["ok"] is False
    assert body["attempts"] == 0  # unresolved guesses never count (pinned)
    assert label in body["suggestions"]
    assert "Poate cautai" in body["message"]


def test_fuzzy_suggestions_never_leak_the_target_label() -> None:
    """The secret's own label must never be offered as a suggestion (ADR-0009/0021)."""
    from cat_de_roman_esti.wordgames.contexto import store
    from cat_de_roman_esti.wordgames.service import get_service

    c = make_client()
    gid = c.post(f"/api/wordgames/contexto/games?seed={SEED}").json()["game_id"]
    svc = get_service()
    target = store.get(gid).target
    target_label = svc.label(target)
    typo = _typo(target_label)
    if svc.resolve(typo) is not None or not svc.suggest(typo):
        pytest.skip("secret label does not produce a fuzzy near-miss on this fixture")
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
    assert all(closeness_for(session, d, session.weighted_dist[nid]) < 100
               for nid, d in dist.items() if d != 0)


def test_ranks_are_deterministic_for_the_same_instance() -> None:
    """Two sessions on the same seed produce identical precomputed rank structure."""
    from cat_de_roman_esti.wordgames.contexto import _pick_target

    a = _pick_target(SEED, "normal")
    b = _pick_target(SEED, "normal")
    assert a.target == b.target
    assert a.sorted_weighted == b.sorted_weighted
    assert a.closer_than == b.closer_than
