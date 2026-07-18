"""Alchimie category-scoped projection input (ADR-0044) stays within one theme."""

from __future__ import annotations

import pytest

pytest.importorskip("django")

from django.test import Client

from cat_de_roman_esti.wordgames.service import get_service


def test_common_neighbors_category_scope_restricts_results():
    svc = get_service()
    # find a pair with common neighbours that span >1 category
    ids = svc.all_ids()
    for a in ids[:200]:
        for b in svc.neighbor_ids(a)[:10]:
            unscoped = svc.common_neighbors(a, b)
            if len(unscoped) < 3:
                continue
            cat = svc.node(a).category
            scoped = svc.common_neighbors(a, b, category=cat)
            # scoped is a subset, and every scoped result really is in-category
            assert set(scoped) <= set(unscoped)
            assert all(svc.node(c).category == cat for c in scoped)
            if len(scoped) < len(unscoped):
                return  # found a genuine narrowing — the point is proven
    pytest.skip("no pair with a cross-category common-neighbour narrowing found")


def test_mined_alchimie_is_always_themed_and_bounded():
    from cat_de_roman_esti.wordgames.alchimie import _closure_with_generations, store
    from cat_de_roman_esti.wordgames.packs import minimum_alchimie_actions

    c = Client()
    # No category requested -> the builder must still pick one (ADR-0044).
    body = c.post("/api/wordgames/alchimie/games?seed=7").json()
    assert body["board_category"], "mined Alchimie must be themed"
    session = store.get(body["game_id"])
    # The closure is bounded to the theme, not the whole graph.
    closure = _closure_with_generations(session.seeds, session.category)
    svc = get_service()
    assert len(closure) <= len(svc.by_category(session.category)) + len(session.seeds)
    assert session.target in closure
    # target_depth is the exact sequential-action par; closure depth is only its
    # parallel-round lower bound and may be smaller.
    assert closure[session.target] <= session.target_depth
    assert (
        minimum_alchimie_actions(
            svc, session.seeds, session.target, session.category
        )
        == session.target_depth
    )


def test_category_scoped_alchimie_is_winnable():
    from cat_de_roman_esti.wordgames.alchimie import _pair_key, store

    c = Client()
    body = c.post("/api/wordgames/alchimie/games?seed=2&category=istorie").json()
    gid = body["game_id"]
    session = store.get(gid)
    target = session.target
    # Greedily craft toward the target following the in-category closure.
    for _ in range(30):
        fresh = c.get(f"/api/wordgames/alchimie/games/{gid}").json()
        if fresh["won"]:
            break
        owned = [i["id"] for i in fresh["inventory"]]
        made = False
        for i in range(len(owned)):
            for j in range(i + 1, len(owned)):
                cn = session.recipes.get(_pair_key(owned[i], owned[j]), ())
                if any(x not in owned for x in cn):
                    c.post(
                        f"/api/wordgames/alchimie/games/{gid}/combine",
                        {"a": owned[i], "b": owned[j]},
                        content_type="application/json",
                    )
                    made = True
                    break
            if made:
                break
        if not made:
            break
    assert store.get(gid).won or target in store.get(gid).owned
