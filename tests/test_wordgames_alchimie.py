"""Offline, deterministic tests for the Alchimie word game router."""

from __future__ import annotations

import random
from itertools import combinations

import pytest

pytest.importorskip("django")

from django.test import Client  # noqa: E402

from cat_de_roman_esti.wordgames import alchimie as A  # noqa: E402

BASE = "/api/wordgames/alchimie"


@pytest.fixture()
def client() -> Client:
    return Client()


def _create(client: Client, seed: int = 7) -> dict:
    res = client.post(f"{BASE}/games?seed={seed}")
    assert res.status_code == 200, res.content.decode()
    return res.json()


def test_create_returns_hidden_target_and_seed_inventory(client: Client) -> None:
    state = _create(client)
    assert state["game_id"]
    assert state["won"] is False
    assert state["moves"] == 0
    assert state["attempted_count"] == 0
    # A recognizable seed inventory of 5-7 concepts.
    assert 5 <= state["seed_count"] <= 7
    assert len(state["inventory"]) == state["seed_count"]
    # Target label is shown, but the secret id stays hidden until won.
    assert state["target"]["label"]
    assert state["target"]["revealed"] is False
    assert state["target"]["id"] is None
    # Seeds have no parents.
    for item in state["inventory"]:
        assert item["parents"] is None


def test_deterministic_for_same_seed(client: Client) -> None:
    a = _create(client, seed=42)
    b = _create(client, seed=42)
    assert a["target"]["label"] == b["target"]["label"]
    assert [i["id"] for i in a["inventory"]] == [i["id"] for i in b["inventory"]]


def test_productive_combine_lineage_is_exact_ordered_and_persistent(client: Client) -> None:
    """The browser journal may use inventory order and exact server-recorded parents."""
    state = _create(client, seed=7)
    seed_ids = [item["id"] for item in state["inventory"]]

    for a, b in combinations(seed_ids, 2):
        gid = state["game_id"]
        before = {item["id"]: item for item in state["inventory"]}
        res = client.post(
            f"{BASE}/games/{gid}/combine",
            {"a": a, "b": b},
            content_type="application/json",
        )
        assert res.status_code == 200, res.content.decode()
        body = res.json()
        if not body["discovered"]:
            state = _create(client, seed=7)
            continue

        assert body["won"] is False
        assert body["already_tried"] is False
        assert body["attempted_count"] == 1
        assert body["target"]["id"] is None
        assert [item["id"] for item in body["inventory"][: body["seed_count"]]] == seed_ids
        assert [item["id"] for item in body["inventory"][-len(body["discovered"]) :]] == [
            item["id"] for item in body["discovered"]
        ]

        inventory = {item["id"]: item for item in body["inventory"]}
        expected_parents = [
            {"id": a, "label": before[a]["label"]},
            {"id": b, "label": before[b]["label"]},
        ]
        for discovered in body["discovered"]:
            assert inventory[discovered["id"]]["parents"] == expected_parents

        resumed = client.get(f"{BASE}/games/{gid}")
        assert resumed.status_code == 200
        assert resumed.json()["inventory"] == body["inventory"]

        reset = client.post(f"{BASE}/games/{gid}/reset")
        assert reset.status_code == 200
        reset_body = reset.json()
        assert [item["id"] for item in reset_body["inventory"]] == seed_ids
        assert all(item["parents"] is None for item in reset_body["inventory"])
        break
    else:
        pytest.fail("seed 7 has no productive seed pair")


def test_combine_is_symmetric_and_lineage_preserves_request_order(client: Client) -> None:
    """Pair results are unordered while recorded parents retain the submitted order."""
    forward_state = _create(client, seed=7)
    reverse_state = _create(client, seed=7)
    assert forward_state["inventory"] == reverse_state["inventory"]

    before = {item["id"]: item for item in forward_state["inventory"]}
    owned = set(before)
    session = A.store.get(forward_state["game_id"])
    assert session is not None
    pair = next(
        (
            recipe_pair
            for recipe_pair, outputs in session.recipes.items()
            if set(recipe_pair) <= owned and any(node_id not in owned for node_id in outputs)
        ),
        None,
    )
    assert pair is not None, "seed 7 has no productive seed pair"
    a, b = pair

    forward_res = client.post(
        f"{BASE}/games/{forward_state['game_id']}/combine",
        {"a": a, "b": b},
        content_type="application/json",
    )
    reverse_res = client.post(
        f"{BASE}/games/{reverse_state['game_id']}/combine",
        {"a": b, "b": a},
        content_type="application/json",
    )
    assert forward_res.status_code == reverse_res.status_code == 200
    forward, reverse = forward_res.json(), reverse_res.json()

    assert forward["discovered"]
    assert reverse["discovered"] == forward["discovered"]
    assert forward["already_tried"] is reverse["already_tried"] is False
    assert forward["attempted_count"] == reverse["attempted_count"] == 1
    assert forward["moves"] == reverse["moves"] == 1
    assert forward["target"]["id"] is reverse["target"]["id"] is None

    forward_inventory = {item["id"]: item for item in forward["inventory"]}
    reverse_inventory = {item["id"]: item for item in reverse["inventory"]}
    forward_parents = [
        {"id": a, "label": before[a]["label"]},
        {"id": b, "label": before[b]["label"]},
    ]
    reverse_parents = list(reversed(forward_parents))
    for discovered in forward["discovered"]:
        node_id = discovered["id"]
        assert forward_inventory[node_id]["parents"] == forward_parents
        assert reverse_inventory[node_id]["parents"] == reverse_parents


def test_winning_play_through(client: Client) -> None:
    """Greedily combine every owned pair until the target is crafted."""
    state = _create(client, seed=7)
    gid = state["game_id"]
    tried: set[tuple[str, str]] = set()

    while not state["won"]:
        ids = [item["id"] for item in state["inventory"]]
        progressed = False
        for a, b in combinations(ids, 2):
            if (a, b) in tried:
                continue
            tried.add((a, b))
            res = client.post(
                f"{BASE}/games/{gid}/combine",
                {"a": a, "b": b},
                content_type="application/json",
            )
            assert res.status_code == 200, res.content.decode()
            state = res.json()
            if state["discovered"] or state["won"]:
                progressed = True
                break
        assert progressed, "ran out of combinations without winning"

    assert state["won"] is True
    # On win the target id + description are revealed.
    assert state["target"]["revealed"] is True
    assert state["target"]["id"] is not None
    assert "tinta" in state["message"].lower()
    # Discovered concepts carry their two parents (the WHY).
    crafted = [i for i in state["inventory"] if i["parents"] is not None]
    assert crafted
    for item in crafted:
        assert len(item["parents"]) == 2


def test_combine_with_no_discovery_counts_move(client: Client) -> None:
    """A combine with no shared neighbour still counts as a move with a clear message."""
    state = _create(client, seed=7)
    gid = state["game_id"]
    ids = [item["id"] for item in state["inventory"]]

    # Find a barren pair (no common neighbours) among the seeds.
    barren: tuple[str, str] | None = None
    for a, b in combinations(ids, 2):
        res = client.post(
            f"{BASE}/games/{gid}/combine",
            {"a": a, "b": b},
            content_type="application/json",
        )
        body = res.json()
        if not body["discovered"]:
            barren = (a, b)
            assert body["message"] == "Nicio combinatie noua."
            assert body["already_tried"] is False
            assert body["moves"] >= 1
            break
        # Re-create to keep a clean inventory for the next probe.
        state = _create(client, seed=7)
        gid = state["game_id"]
    assert barren is not None


def test_combine_unowned_is_400(client: Client) -> None:
    state = _create(client)
    gid = state["game_id"]
    a = state["inventory"][0]["id"]
    res = client.post(
        f"{BASE}/games/{gid}/combine",
        {"a": a, "b": "n_nonexistent_node"},
        content_type="application/json",
    )
    assert res.status_code == 400


def test_combine_same_concept_is_400(client: Client) -> None:
    state = _create(client)
    gid = state["game_id"]
    a = state["inventory"][0]["id"]
    res = client.post(
        f"{BASE}/games/{gid}/combine",
        {"a": a, "b": a},
        content_type="application/json",
    )
    assert res.status_code == 400


def test_reset_restores_seed_inventory(client: Client) -> None:
    state = _create(client, seed=7)
    gid = state["game_id"]
    ids = [item["id"] for item in state["inventory"]]
    # Make some progress.
    client.post(
        f"{BASE}/games/{gid}/combine",
        {"a": ids[0], "b": ids[1]},
        content_type="application/json",
    )

    res = client.post(f"{BASE}/games/{gid}/reset")
    assert res.status_code == 200
    reset = res.json()
    assert reset["moves"] == 0
    assert reset["attempted_count"] == 0
    assert reset["won"] is False
    assert [i["id"] for i in reset["inventory"]] == ids


def test_unknown_game_is_404(client: Client) -> None:
    assert client.get(f"{BASE}/games/does-not-exist").status_code == 404
    res = client.post(
        f"{BASE}/games/does-not-exist/combine",
        {"a": "x", "b": "y"},
        content_type="application/json",
    )
    assert res.status_code == 404


# --------------------------------------------------------------- difficulty + daily + score


def _play_to_win(client: Client, state: dict) -> dict:
    """Greedily combine pairs until the target is crafted; return the won state."""
    gid = state["game_id"]
    tried: set[tuple[str, str]] = set()
    while not state["won"]:
        ids = [item["id"] for item in state["inventory"]]
        progressed = False
        for a, b in combinations(ids, 2):
            if (a, b) in tried:
                continue
            tried.add((a, b))
            res = client.post(
                f"{BASE}/games/{gid}/combine",
                {"a": a, "b": b},
                content_type="application/json",
            )
            assert res.status_code == 200, res.content.decode()
            state = res.json()
            if state["discovered"] or state["won"]:
                progressed = True
                break
        assert progressed, "ran out of combinations without winning"
    return state


@pytest.mark.parametrize("difficulty", ["usor", "normal", "greu"])
def test_difficulty_is_accepted(client: Client, difficulty: str) -> None:
    res = client.post(f"{BASE}/games?seed=7&difficulty={difficulty}")
    assert res.status_code == 200, res.content.decode()
    state = res.json()
    assert state["difficulty"] == difficulty
    assert state["target_depth"] >= 2
    # usor offers a wide inventory; greu is lean.
    if difficulty == "usor":
        assert 6 <= state["seed_count"] <= 7
    if difficulty == "greu":
        assert state["seed_count"] == 5
        assert state["target_depth"] >= 3


def test_unknown_difficulty_falls_back_to_normal(client: Client) -> None:
    res = client.post(f"{BASE}/games?seed=7&difficulty=imposibil")
    assert res.status_code == 200
    assert res.json()["difficulty"] == "normal"


def test_daily_is_deterministic_and_echoed(client: Client) -> None:
    date = "2026-06-21"
    a = client.post(f"{BASE}/games?daily={date}").json()
    b = client.post(f"{BASE}/games?daily={date}").json()
    assert a["daily"] == date
    assert a["target"]["label"] == b["target"]["label"]
    assert [i["id"] for i in a["inventory"]] == [i["id"] for i in b["inventory"]]
    # A different date yields a (very likely) different instance and is echoed.
    other = client.post(f"{BASE}/games?daily=2026-01-01").json()
    assert other["daily"] == "2026-01-01"


def test_in_progress_state_has_no_score_or_share(client: Client) -> None:
    state = _create(client, seed=7)
    assert "score" not in state
    assert "share" not in state


def test_win_includes_score_and_share(client: Client) -> None:
    state = _play_to_win(client, _create(client, seed=7))
    assert state["won"] is True
    assert isinstance(state["score"], int)
    assert 100 <= state["score"] <= 1000
    share = state["share"]
    assert "Alchimie" in share
    assert "combinatii" in share
    assert "⚗️" in share


def test_daily_win_share_includes_date(client: Client) -> None:
    date = "2026-06-21"
    state = _play_to_win(client, client.post(f"{BASE}/games?daily={date}").json())
    assert date in state["share"]
    assert isinstance(state["score"], int)


# ----------------------------------------------------- instance-quality (anti-degenerate)


def _projected_openings(session: A.AlchimieSession) -> int:
    """How many initial pairs are genuinely productive in the live private recipes."""
    owned = set(session.seeds)
    return sum(
        any(
            result not in owned
            for result in session.recipes.get(A._pair_key(a, b), ())
        )
        for a, b in combinations(sorted(owned), 2)
    )


@pytest.mark.parametrize("difficulty", ["usor", "normal", "greu"])
def test_mined_instances_prefer_several_live_projected_openings(
    difficulty: str,
) -> None:
    """A bounded direct-builder sample tests mined, not curated-first API selection."""
    for seed in range(2):
        session = A._build_session(random.Random(seed), difficulty=difficulty)
        assert _projected_openings(session) >= A.MIN_OPENING_PAIRS, (
            f"degenerate instance: seed={seed} diff={difficulty}"
        )


@pytest.mark.parametrize("difficulty", ["usor", "normal", "greu"])
def test_target_is_recognizable(client: Client, difficulty: str) -> None:
    """The hidden target should be a recognizable concept, not an obscure intermediate."""
    from cat_de_roman_esti.wordgames.service import get_service

    svc = get_service()
    session = A._build_session(__import__("random").Random(13), difficulty=difficulty)
    node = svc.node(session.target)
    assert node is not None
    assert node.salience >= A.TARGET_SALIENCE_FLOOR
    # The target is never one of the seeds (it must be crafted).
    assert session.target not in session.seeds


def test_greu_target_depth_is_capped(client: Client) -> None:
    """Greu targets are deep but their exact sequential par stays bounded."""
    import random as _random

    for seed in range(30):
        session = A._build_session(_random.Random(seed), difficulty="greu")
        closure_depth = A._closure_with_generations(
            session.seeds, session.category
        )[session.target]
        assert 3 <= closure_depth <= A.GREU_MAX_GENERATION
        assert closure_depth <= session.target_depth <= A.ALCHIMIE_MAX_ACTIONS


def test_curated_par_makes_the_perfect_score_achievable() -> None:
    """A former closure-depth undercount now prices the real six-action optimum."""
    from cat_de_roman_esti.wordgames.packs import get_pack, minimum_alchimie_actions
    from cat_de_roman_esti.wordgames.service import get_service

    item = next(i for i in get_pack().pool("alchimie") if i.id == "al_film_tv_023")
    par = minimum_alchimie_actions(
        get_service(),
        item.payload["seeds"],
        item.payload["target"],
        item.category,
    )
    assert par == item.payload["target_depth"] == 6
    session = A.AlchimieSession(
        seeds=item.payload["seeds"],
        target=item.payload["target"],
        target_depth=par,
    )
    session.moves = par
    assert session.score == 1000
    assert "✨" in A._share_line(session)


# ----------------------------------------------------------------- nudges + edge cases


def _barren_owned_pairs(
    session: A.AlchimieSession, ids: list[str]
) -> list[tuple[str, str]]:
    """Untried owned pairs with no fresh result in the private recipe projection.

    Each pair can grow the fruitless streak exactly once: experiment memory makes later
    submissions free and inert, so hint tests deliberately use distinct barren pairs.
    """
    owned = set(ids)
    return [
        (a, b)
        for a, b in combinations(sorted(owned), 2)
        if A._pair_key(a, b) not in session.attempted_pairs
        and not [
            result
            for result in session.recipes.get(A._pair_key(a, b), ())
            if result not in owned
        ]
    ]


def _force_fruitless(client: Client, state: dict) -> dict:
    """Drive a game into the "stuck" state with distinct barren owned pairs.

    Experiment memory prevents a retry from inflating the dry-spell counter, so every
    accepted fruitless combine here represents a genuinely new experiment.
    """
    gid = state["game_id"]
    session = A.store.get(gid)
    assert session is not None
    ids = [i["id"] for i in state["inventory"]]
    pairs = _barren_owned_pairs(session, ids)
    assert len(pairs) >= A.NUDGE_AFTER_FRUITLESS, (
        "expected enough distinct barren pairs to force fruitless combines"
    )
    for a, b in pairs:
        if state["hint_available"]:
            break
        state = client.post(
            f"{BASE}/games/{gid}/combine",
            {"a": a, "b": b},
            content_type="application/json",
        ).json()
        assert state["discovered"] == [], "barren pair unexpectedly discovered a concept"
        assert state["already_tried"] is False
    assert state["hint_available"] is True
    return state


def test_repeated_barren_pair_is_authoritative_free_and_resettable(
    client: Client,
) -> None:
    """One unordered barren experiment costs once; reset intentionally forgets it."""
    state = _create(client, seed=7)
    gid = state["game_id"]
    inventory = state["inventory"]
    ids = [item["id"] for item in inventory]
    session = A.store.get(gid)
    assert session is not None
    pairs = _barren_owned_pairs(session, ids)
    assert pairs, "expected seed 7 to expose a barren owned pair"
    a, b = pairs[0]

    first_res = client.post(
        f"{BASE}/games/{gid}/combine",
        {"a": a, "b": b},
        content_type="application/json",
    )
    assert first_res.status_code == 200, first_res.content.decode()
    first = first_res.json()
    assert first["discovered"] == []
    assert first["inventory"] == inventory
    assert first["message"] == "Nicio combinatie noua."
    assert first["already_tried"] is False
    assert first["moves"] == first["attempted_count"] == 1
    assert first["hint_available"] is False

    score = session.score
    fruitless = session.fruitless_streak
    hints_used = session.hints_used
    retry_res = client.post(
        f"{BASE}/games/{gid}/combine",
        {"a": b, "b": a},
        content_type="application/json",
    )
    assert retry_res.status_code == 200, retry_res.content.decode()
    retry = retry_res.json()
    assert retry["discovered"] == []
    assert retry["inventory"] == inventory
    assert retry["message"] == "Deja încercată · fără cost. Schimbă un ingredient."
    assert retry["already_tried"] is True
    assert retry["moves"] == retry["attempted_count"] == 1
    assert retry["hint_available"] is False
    assert retry["hints_used"] == hints_used
    assert session.fruitless_streak == fruitless
    assert session.score == score

    resumed = client.get(f"{BASE}/games/{gid}").json()
    assert resumed["attempted_count"] == 1
    assert "attempted_pairs" not in resumed

    reset = client.post(f"{BASE}/games/{gid}/reset").json()
    assert reset["moves"] == reset["attempted_count"] == 0
    assert session.attempted_pairs == set()
    after_reset = client.post(
        f"{BASE}/games/{gid}/combine",
        {"a": b, "b": a},
        content_type="application/json",
    ).json()
    assert after_reset["already_tried"] is False
    assert after_reset["moves"] == after_reset["attempted_count"] == 1


def test_repeated_productive_pair_is_free_and_does_not_replay_discovery(
    client: Client,
) -> None:
    """A formerly productive experiment is remembered after its output is owned."""
    state = _create(client, seed=7)
    gid = state["game_id"]
    session = A.store.get(gid)
    assert session is not None
    pair = A._useful_pair(session)
    assert pair is not None
    a, b = pair

    first = client.post(
        f"{BASE}/games/{gid}/combine",
        {"a": a, "b": b},
        content_type="application/json",
    ).json()
    assert first["discovered"]
    assert first["already_tried"] is False
    assert first["attempted_count"] == first["moves"] == 1
    snapshot = {
        "inventory": first["inventory"],
        "moves": first["moves"],
        "attempted_count": first["attempted_count"],
        "hints_used": first["hints_used"],
        "hint_available": first["hint_available"],
        "fruitless_streak": session.fruitless_streak,
        "score": session.score,
    }

    retry = client.post(
        f"{BASE}/games/{gid}/combine",
        {"a": b, "b": a},
        content_type="application/json",
    ).json()
    assert retry["discovered"] == []
    assert retry["already_tried"] is True
    assert retry["message"] == "Deja încercată · fără cost. Schimbă un ingredient."
    for key in ("inventory", "moves", "attempted_count", "hints_used", "hint_available"):
        assert retry[key] == snapshot[key]
    assert session.fruitless_streak == snapshot["fruitless_streak"]
    assert session.score == snapshot["score"]


def test_attempt_memory_is_exactly_bounded_to_all_32_concept_pairs(
    client: Client,
) -> None:
    """The private set has a structural 496-pair ceiling and leaks only its count."""
    from cat_de_roman_esti.wordgames.service import get_service

    ids = list(get_service().all_ids())[:34]
    assert len(ids) == 34
    owned, extra, target = ids[:32], ids[32], ids[33]
    session = A.AlchimieSession(seeds=owned, target=target, recipes={})
    for node_id in owned:
        session.add(node_id, None)
    gid = A.store.create(session)
    pairs = list(combinations(owned, 2))
    assert len(pairs) == A.MAX_ATTEMPTED_PAIRS == 496

    last: dict | None = None
    for expected, (a, b) in enumerate(pairs, start=1):
        response = client.post(
            f"{BASE}/games/{gid}/combine",
            {"a": a, "b": b},
            content_type="application/json",
        )
        assert response.status_code == 200, response.content.decode()
        last = response.json()
        assert last["already_tried"] is False
        assert last["attempted_count"] == expected

    assert last is not None
    assert last["moves"] == last["attempted_count"] == A.MAX_ATTEMPTED_PAIRS
    assert len(session.attempted_pairs) == A.MAX_ATTEMPTED_PAIRS
    assert not {"attempted_pairs", "experiments", "recipes", "routes"} & set(last)

    # A malformed 33-concept session still fails closed instead of growing the set.
    session.add(extra, None)
    overflow = client.post(
        f"{BASE}/games/{gid}/combine",
        {"a": owned[0], "b": extra},
        content_type="application/json",
    )
    assert overflow.status_code == 409
    assert len(session.attempted_pairs) == A.MAX_ATTEMPTED_PAIRS
    assert session.moves == A.MAX_ATTEMPTED_PAIRS


def _projected_distance_to_target(gid: str, owned: set[str]) -> int | None:
    """Exact remaining private-recipe actions to the in-process secret target."""
    from cat_de_roman_esti.wordgames import alchimie as _A

    session = _A.store.get(gid)
    assert session is not None
    plan = _A._minimum_projected_plan(owned, session.target, session.recipes)
    return len(plan) if plan is not None else None


def test_hint_unavailable_until_stuck(client: Client) -> None:
    state = _create(client, seed=7)
    assert state["hint_available"] is False
    assert state["hints_used"] == 0
    # Asking too early is a friendly 400, not a server error.
    res = client.post(f"{BASE}/games/{state['game_id']}/hint")
    assert res.status_code == 400


def _seed_with_useful_and_barren(client: Client) -> dict:
    """Find a game whose seed inventory has BOTH a forward-progress pair and a barren one.

    On the dense graph most seeds qualify, but a few degenerate instances have no single
    owned pair that strictly shortens the path to the target (the engine correctly returns
    no hint there). We scan a handful of seeds and pick one where a hint must materialise,
    so the test exercises the real nudge path without hard-coding a magic seed.
    """
    from cat_de_roman_esti.wordgames import alchimie as _A
    for seed in range(40):
        state = _create(client, seed=seed)
        ids = [i["id"] for i in state["inventory"]]
        session = _A.store.get(state["game_id"])
        if (
            session is None
            or len(_barren_owned_pairs(session, ids))
            < 2 * _A.NUDGE_AFTER_FRUITLESS
        ):
            continue
        if _A._useful_pair(session) is not None:
            return state
    raise AssertionError("no seed offered both a barren and a forward-progress pair")


def test_hints_progress_from_output_orientation_to_useful_pair(client: Client) -> None:
    state = _force_fruitless(client, _seed_with_useful_and_barren(client))
    assert state["hint_available"] is True
    gid = state["game_id"]
    session = A.store.get(gid)
    assert session is not None
    secret = session.target

    first = client.post(f"{BASE}/games/{gid}/hint").json()
    assert first["hints_used"] == 1
    assert first["hint"] is None
    assert first["hint_kind"] in {"output", "category"}
    assert secret not in str(first)
    if first["hint_kind"] == "output":
        assert set(first["hint_output"]) == {"label"}

    state = _force_fruitless(client, first)
    res = client.post(f"{BASE}/games/{gid}/hint").json()
    assert res["hints_used"] == 2
    assert res["hint_kind"] == "pair"
    assert res["hint"] is not None
    a_id, b_id = res["hint"][0]["id"], res["hint"][1]["id"]
    # The suggested pair must be owned and actually productive (a real forward move).
    owned = {i["id"] for i in res["inventory"]}
    assert a_id in owned and b_id in owned
    fresh = [
        c
        for c in session.recipes[A._pair_key(a_id, b_id)]
        if c not in owned
    ]
    assert fresh, "hint pointed at a barren pair"
    # ...and it must STRICTLY reduce exact projected actions, not just discover noise.
    base_distance = _projected_distance_to_target(gid, owned)
    new_distance = _projected_distance_to_target(gid, owned | set(fresh))
    assert (
        new_distance is not None
        and base_distance is not None
        and new_distance < base_distance
    ), (
        "hint did not shorten the path to the target"
    )
    # The nudge resets the dry spell so it can't be spammed.
    assert res["hint_available"] is False


def test_hint_penalizes_score() -> None:
    """Each revealed hint subtracts from the score and breaks a "perfect" share."""
    base = A.AlchimieSession(seeds=["a"], target="t", target_depth=2)
    base.moves = 2  # optimal solve
    assert base.score == 1000
    assert "✨" in A._share_line(base)  # perfect medal

    base.hints_used = 1
    assert base.score == 1000 - 150
    line = A._share_line(base)
    assert "✨" not in line and "💡 x1" in line

    base.hints_used = 100  # never below the floor
    assert base.score == 100


def test_combine_after_win_is_readonly(client: Client) -> None:
    """Combining a finished game must not advance moves or corrupt the score."""
    state = _play_to_win(client, _create(client, seed=7))
    gid = state["game_id"]
    moves_at_win = state["moves"]
    score_at_win = state["score"]
    ids = [i["id"] for i in state["inventory"]]
    res = client.post(
        f"{BASE}/games/{gid}/combine",
        {"a": ids[0], "b": ids[1]},
        content_type="application/json",
    ).json()
    assert res["won"] is True
    assert res["moves"] == moves_at_win
    assert res["score"] == score_at_win
    assert res["discovered"] == []
    assert isinstance(res["already_tried"], bool)


def test_hint_on_won_game_is_400(client: Client) -> None:
    state = _play_to_win(client, _create(client, seed=7))
    res = client.post(f"{BASE}/games/{state['game_id']}/hint")
    assert res.status_code == 400


def test_combine_trims_whitespace_inputs(client: Client) -> None:
    """Padded ids resolve to owned concepts rather than spuriously 400-ing."""
    state = _create(client, seed=7)
    gid = state["game_id"]
    a, b = state["inventory"][0]["id"], state["inventory"][1]["id"]
    res = client.post(
        f"{BASE}/games/{gid}/combine",
        {"a": f"  {a} ", "b": f" {b}  "},
        content_type="application/json",
    )
    assert res.status_code == 200, res.content.decode()


def test_empty_input_is_400(client: Client) -> None:
    state = _create(client, seed=7)
    gid = state["game_id"]
    a = state["inventory"][0]["id"]
    res = client.post(
        f"{BASE}/games/{gid}/combine",
        {"a": a, "b": ""},
        content_type="application/json",
    )
    assert res.status_code == 400


def test_reset_clears_hints_and_streak(client: Client) -> None:
    state = _force_fruitless(client, _create(client, seed=7))
    gid = state["game_id"]
    client.post(f"{BASE}/games/{gid}/hint")
    reset = client.post(f"{BASE}/games/{gid}/reset").json()
    assert reset["hints_used"] == 0
    assert reset["hint_available"] is False
    assert reset["moves"] == 0
    assert reset["attempted_count"] == 0
