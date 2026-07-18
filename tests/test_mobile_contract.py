"""Mobile API-contract guards for the word-game BFF.

These tests pin the contract a *generated mobile client* depends on, independently of
the per-game behaviour tests in ``test_wordgames_*.py``:

* **Hidden-answer exposure** — no game's public responses may leak its secret answer
  (contexto's target, alchimie's target id, lant's full route corridor, or an unsolved
  Conexiuni group). Each test also asserts the positive reveal boundary.
* **Stable OpenAPI operationIds** — the generated TypeScript client's method names come
  from ``operationId``s; these must stay ``<game>_<action>`` and never bake in the HTTP
  path (which would churn on any route refactor).
* **Trust manifest endpoint** — ``/api/manifest`` serves the deterministic fixture
  manifest a mobile app uses to detect a stale offline bundle.
"""

from __future__ import annotations

import pytest

pytest.importorskip("django")

from django.test import Client  # noqa: E402

from cat_de_roman_esti.data import (  # noqa: E402
    APP_PACK_SCHEMA_VERSION,
    fixture_manifest,
)
from cat_de_roman_esti.wordgames.service import get_service  # noqa: E402

SEED = 1


def client() -> Client:
    return Client()


def _post_json(c: Client, url: str, payload: dict) -> dict:
    return c.post(url, payload, content_type="application/json").json()


def _collect_ids(obj: object) -> set[str]:
    """Every value that appears under an ``"id"`` key, anywhere in a response body.

    This is how we prove a *concept id* (a game's hidden answer) does not leak: a secret
    must not surface as any concept id in the serialized response. ``game_id`` and other
    non-``id`` keys are intentionally ignored, and a ``None`` id (alchimie's withheld
    target) is never collected.
    """
    found: set[str] = set()
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key == "id" and isinstance(value, str):
                found.add(value)
            else:
                found |= _collect_ids(value)
    elif isinstance(obj, list):
        for item in obj:
            found |= _collect_ids(item)
    return found


def _collect_strings(obj: object) -> set[str]:
    """Every string value in a response body, for exact hidden-label checks."""
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


def _collect_keys(obj: object) -> set[str]:
    """Every object key in a response body."""
    found: set[str] = set()
    if isinstance(obj, dict):
        found |= set(obj)
        for value in obj.values():
            found |= _collect_keys(value)
    elif isinstance(obj, list):
        for item in obj:
            found |= _collect_keys(item)
    return found


def _cross_group_guess(groups: dict[str, list[str]], index: int) -> list[str]:
    """Build one of four distinct Conexiuni mistakes (one tile from each group)."""
    return [members[index % len(members)] for members in groups.values()]


# --------------------------------------------------------------- hidden-answer guards
def test_contexto_does_not_leak_target_before_win() -> None:
    from cat_de_roman_esti.wordgames.contexto import store

    c = client()
    created = c.post(f"/api/wordgames/contexto/games?seed={SEED}").json()
    gid = created["game_id"]
    session = store.get(gid)
    assert session is not None
    secret = session.target
    svc = get_service()
    secret_label = svc.label(secret)
    fetched = c.get(f"/api/wordgames/contexto/games/{gid}").json()

    # Public rank metadata describes the directed population of guesses that can reach
    # the target. The map itself remains server-side and does not expose the answer.
    assert session.reachable == len(svc.distances_to(secret))
    assert created["reachable_count"] == session.reachable

    for body in (created, fetched):
        assert "target" not in body  # dedicated reveal key absent pre-win
        assert "solution" not in body
        assert secret not in _collect_ids(body)  # ...and the id leaks nowhere else
        assert secret_label not in _collect_strings(body)

    # Boundary for the optional category clue: it may reveal the broad category, but not
    # the secret concept id/label/description.
    last_guess = None
    for nid in svc.all_ids():
        if nid == secret:
            continue
        last_guess = _post_json(
            c,
            f"/api/wordgames/contexto/games/{gid}/guess",
            {"text": svc.label(nid)},
        )
        assert last_guess["ok"] is True
        assert "target" not in last_guess
        assert "solution" not in last_guess
        assert secret not in _collect_ids(last_guess)
        assert secret_label not in _collect_strings(last_guess)
        assert "rank" in last_guess["guess"]
        if c.get(f"/api/wordgames/contexto/games/{gid}").json()["attempts"] >= 3:
            break
    assert last_guess is not None
    clue = c.post(f"/api/wordgames/contexto/games/{gid}/clue").json()
    assert "target" not in clue
    assert "solution" not in clue
    assert secret not in _collect_ids(clue)
    assert secret_label not in _collect_strings(clue)
    assert set(clue["clue"]) == {"category", "message"}

    # Boundary: giving up reveals the secret target id and label.
    over = c.post(f"/api/wordgames/contexto/games/{gid}/giveup").json()
    assert over["target"]["id"] == secret
    assert over["target"]["label"] == secret_label


def _alchimie_play_to_win(c: Client, state: dict) -> dict:
    """Greedily combine every owned pair until the target is crafted; return won state."""
    gid = state["game_id"]
    while not state["won"]:
        ids = [item["id"] for item in state["inventory"]]
        progressed = False
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                res = _post_json(
                    c,
                    f"/api/wordgames/alchimie/games/{gid}/combine",
                    {"a": ids[i], "b": ids[j]},
                )
                if res["discovered"] or res["won"]:
                    state = res
                    progressed = True
                    break
            if progressed:
                break
        assert progressed, "no productive combine found — instance should be solvable"
    return state


def test_alchimie_hides_target_id_until_win() -> None:
    from cat_de_roman_esti.wordgames.alchimie import store

    c = client()
    created = c.post(f"/api/wordgames/alchimie/games?seed={SEED}").json()
    gid = created["game_id"]
    session = store.get(gid)
    assert session is not None
    secret = session.target
    fetched = c.get(f"/api/wordgames/alchimie/games/{gid}").json()

    for body in (created, fetched):
        # The target LABEL is shown as the goal by design, but the id is withheld and
        # the secret never appears among the owned-concept ids until it is crafted.
        assert body["target"]["revealed"] is False
        assert body["target"]["id"] is None
        assert body["target"]["label"]  # goal is still shown to the player
        assert secret not in _collect_ids(body)

    # Boundary: crafting the target flips revealed and exposes the real id.
    won = _alchimie_play_to_win(c, created)
    assert won["target"]["revealed"] is True
    assert won["target"]["id"] == secret


def test_lant_exposes_id_free_local_choices_not_the_route_corridor() -> None:
    from cat_de_roman_esti.wordgames import lant

    c = client()
    created = c.post(f"/api/wordgames/lant/games?seed={SEED}").json()
    start, target, optimal = created["start"]["id"], created["target"]["id"], created["optimal"]
    svc = get_service()

    # Only the endpoints carry concept IDs. Local choices are label/relation actions;
    # corridor membership and route IDs remain server-only.
    assert _collect_ids(created) == {start, target}
    assert 1 <= len(created["choices"]) <= 6
    assert all(set(choice) == {"label", "relation"} for choice in created["choices"])
    assert all(
        lant._resolve_neighbor(choice["label"], start, target) in svc.neighbor_ids(start)
        for choice in created["choices"]
    )
    assert not {"corridor", "on_track", "route_budget"} & _collect_keys(created)

    # There genuinely is a hidden middle to protect. A local label may name one useful
    # neighbour, but no intermediate concept ID or complete route is serialized.
    ds, dt = svc.distances_from(start), svc.distances_to(target)
    on_path = [
        nid
        for nid in svc.all_ids()
        if nid not in (start, target)
        and ds.get(nid) is not None
        and dt.get(nid) is not None
        and ds[nid] + dt[nid] == optimal
    ]
    assert on_path, "expected solution-path intermediates for a normal-difficulty game"
    assert not (set(on_path) & _collect_ids(created))


def test_conexiuni_hides_solution_until_over() -> None:
    from cat_de_roman_esti.wordgames.conexiuni import (
        MAX_LIVES,
        MIN_CLUE_MISTAKES,
        NUM_GROUPS,
        _category_label,
        _group_label,
        store,
    )

    c = client()
    created = c.post(f"/api/wordgames/conexiuni/games?seed={SEED}").json()
    gid = created["game_id"]
    session = store.get(gid)
    assert session is not None
    groups = session.groups
    fetched = c.get(f"/api/wordgames/conexiuni/games/{gid}").json()

    for body in (created, fetched):
        assert "solution" not in body  # full grouping withheld pre-finish
        assert body["solved"] == []
        # Tiles carry only id + label; the category that would give the grouping away
        # is never attached to a tile.
        for tile in body["tiles"]:
            assert set(tile) == {"id", "label"}

    # A correct group becomes public because the player earned it; every unsolved group
    # and the full solution remain hidden.
    first_cat, first_members = next(iter(groups.items()))
    correct_body = _post_json(
        c, f"/api/wordgames/conexiuni/games/{gid}/guess", {"ids": first_members}
    )
    assert correct_body["correct"] is True
    assert correct_body["won"] is False
    assert correct_body["category"] == {
        "key": first_cat,
        "label": _group_label(session, first_cat),
    }
    assert "solution" not in correct_body
    assert [group["key"] for group in correct_body["solved"]] == [first_cat]
    assert {tile["id"] for tile in correct_body["solved"][0]["tiles"]} == set(first_members)
    assert correct_body["solved_count"] == 1
    assert {tile["id"] for tile in correct_body["tiles"]}.isdisjoint(first_members)
    strings = _collect_strings(correct_body)
    hidden = set(groups) - {first_cat}
    assert all(cat not in strings for cat in hidden)
    assert all(_category_label(cat) not in strings for cat in hidden)
    assert all(_group_label(session, cat) not in strings for cat in hidden)

    # Boundary for the optional clue: after enough mistakes it may reveal a redacted
    # label pattern, but never category keys, exact category labels, or tile membership.
    created = c.post(f"/api/wordgames/conexiuni/games?seed={SEED + 1}").json()
    gid = created["game_id"]
    session = store.get(gid)
    assert session is not None
    groups = session.groups
    for index in range(MIN_CLUE_MISTAKES):
        _post_json(
            c,
            f"/api/wordgames/conexiuni/games/{gid}/guess",
            {"ids": _cross_group_guess(groups, index)},
        )
    clue = c.post(f"/api/wordgames/conexiuni/games/{gid}/clue").json()
    assert "solution" not in clue
    assert set(clue["clue"]) == {"pattern", "message"}
    clue_text = f"{clue['clue']['pattern']} {clue['clue']['message']}"
    assert all(cat not in clue_text for cat in groups)
    assert all(_category_label(cat) not in clue_text for cat in groups)
    assert all(nid not in clue_text for ids in groups.values() for nid in ids)

    # Boundary: exhausting lives (4 wrong guesses) reveals the full solution.
    last = clue
    for index in range(MIN_CLUE_MISTAKES, MAX_LIVES):
        last = _post_json(
            c,
            f"/api/wordgames/conexiuni/games/{gid}/guess",
            {"ids": _cross_group_guess(groups, index)},
        )
    assert last["lost"] is True
    assert len(last["solution"]) == NUM_GROUPS


# ------------------------------------------------------------- openapi / manifest surface
EXPECTED_OPERATION_IDS = {
    "meta_health",
    "meta_manifest",
    # Additive (ADR-0011): category taxonomy + user-submitted-game intake.
    "meta_categories",
    "submissions_create",
    "alchimie_create_game",
    "alchimie_get_game",
    "alchimie_combine",
    "alchimie_hint_game",
    "alchimie_reset_game",
    "contexto_create_game",
    "contexto_get_game",
    "contexto_guess",
    "contexto_clue",
    "contexto_give_up",
    "lant_create_game",
    "lant_get_game",
    "lant_move",
    "lant_undo",
    "lant_hint",
    "conexiuni_create_game",
    "conexiuni_get_game",
    "conexiuni_guess",
    "conexiuni_clue",
}


def test_openapi_operation_ids_are_stable() -> None:
    from drf_spectacular.generators import SchemaGenerator

    schema = SchemaGenerator().get_schema(request=None, public=True)
    ops = {
        op["operationId"]
        for methods in schema["paths"].values()
        for op in methods.values()
        if isinstance(op, dict) and "operationId" in op
    }
    assert ops == EXPECTED_OPERATION_IDS
    # The HTTP path must NOT be baked into the operationId (the churny default we
    # replaced) — so a generated client's method names survive a route refactor.
    assert not any("wordgames" in op for op in ops)


def test_manifest_endpoint_matches_fixture_manifest() -> None:
    body = client().get("/api/manifest").json()
    assert body == fixture_manifest()
    assert body["schema_version"] == APP_PACK_SCHEMA_VERSION
    assert body["content_hash"].startswith("sha256:")
