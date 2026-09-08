"""Keep useful shortest alternatives in Lanț's existing mixed, private menu."""

from __future__ import annotations

import json
from copy import deepcopy

import pytest
from django.test import Client

from cat_de_roman_esti.graph import Graph
from cat_de_roman_esti.wordgames import lant as L
from cat_de_roman_esti.wordgames.packs import get_pack
from cat_de_roman_esti.wordgames.service import WordGameService, get_service


def _service(shortest_count, reverse=False):
    routes = [(f"short_{i}",) for i in range(shortest_count)]
    routes += [(f"scenic_{i}", f"hidden_scenic_{i}") for i in range(3)]
    routes += [("detour", "hidden_far_1", "hidden_far_2", "hidden_far_3")]
    ids = {"start", "target", "dead", *(node for route in routes for node in route)}
    nodes = [{
        "id": node_id, "label_ro": node_id.replace("_", " ").title(), "category": "test",
        "salience": 1.0 if node_id.startswith("scenic") else 0.4,
    } for node_id in sorted(ids)]
    edges = []
    for index, route in enumerate(routes):
        path = ("start", *route, "target")
        for step, (src, dst) in enumerate(zip(path, path[1:], strict=False)):
            edges.append({
                "id": f"edge_{index}_{step}", "src_id": src, "dst_id": dst,
                "bidirectional": 0, "label_ro": "asociere locală",
                "strength": 0.6 if dst.startswith("short") else 0.9,
            })
    edges.append({
        "id": "dead_edge", "src_id": "start", "dst_id": "dead", "bidirectional": 0,
    })
    if reverse:
        nodes.reverse()
        edges.reverse()
    return WordGameService(Graph.from_records(nodes, edges))


def _session(item=None):
    if item is None:
        return L.LantSession(start="start", target="target", optimal=2, chain=["start"])
    return L.LantSession(
        start=item.payload["start"], target=item.payload["target"],
        optimal=item.payload["optimal"], difficulty=item.difficulty,
        chain=[item.payload["start"]], category=item.category, pack_id=item.id,
    )


def _keys(value):
    if isinstance(value, dict):
        return set(value) | set().union(*(_keys(item) for item in value.values()), set())
    if isinstance(value, list):
        return set().union(*(_keys(item) for item in value), set())
    return set()


@pytest.mark.parametrize("shortest_count", [1, 2, 4])
def test_two_shortest_reserve_keeps_exploration_and_safe_detours(shortest_count, monkeypatch):
    svc = _service(shortest_count)
    monkeypatch.setattr(L, "get_service", lambda: svc)
    session = _session()
    prior = deepcopy(vars(session))
    chosen = L._visible_choice_nodes(session)
    shortest = L._shortest_hops(session)
    assert set(shortest[:2]) <= set(chosen)
    assert len(set(chosen) & set(shortest)) == min(shortest_count, 2)
    assert "scenic_0" in chosen  # Third slot retains semantic-quality exploration.
    assert "detour" in chosen and "dead" not in chosen
    assert len(chosen) == 4
    assert len(set(chosen) & set(L._near_route_hops(session))) == 3
    assert chosen == sorted(chosen, key=lambda node: (L.normalize(svc.label(node)), node))
    assert vars(session) == prior
    payload = L._visible_choices(session)
    assert all(set(choice) == {"label", "relation"} for choice in payload)
    assert "hidden" not in json.dumps(payload)


def test_graph_insertion_order_cannot_change_the_mixed_menu(monkeypatch):
    observed = []
    for reverse in (False, True):
        svc = _service(4, reverse=reverse)
        monkeypatch.setattr(L, "get_service", lambda svc=svc: svc)
        observed.append(L._visible_choices(_session()))
    assert observed[0] == observed[1]


def test_used_shortest_nodes_and_exhausted_corridors_keep_existing_safe_recovery(monkeypatch):
    svc = _service(2)
    monkeypatch.setattr(L, "get_service", lambda: svc)
    # These previously visited nodes cannot be published again as forward choices.
    session = L.LantSession(
        start="short_0", target="target", optimal=2,
        chain=["short_0", "short_1", "start"],
    )
    chosen = L._visible_choice_nodes(session)
    assert set(chosen) == {"scenic_0", "scenic_1", "scenic_2", "detour"}
    assert not {"short_0", "short_1", "dead"} & set(chosen)
    assert L._near_route_hops(session) == []
    session.won = True
    assert L._visible_choices(session) == []


def test_every_eligible_start_preserves_two_available_shortest_continuations_and_caps():
    svc = get_service()
    eligible = [item for item in get_pack().pool("lant") if item._pilot_eligible]
    assert eligible
    for item in eligible:
        session = _session(item)
        shortest = set(L._shortest_hops(session))
        chosen = L._visible_choice_nodes(session)
        assert len(set(chosen) & shortest) >= min(2, len(shortest)), item.id
        assert len(chosen) <= 6
        assert len(set(chosen) & set(L._near_route_hops(session))) <= 3
        assert all(svc.link(session.current, node) is not None for node in chosen)
        assert all(node not in session.chain for node in chosen)
        assert len({L.normalize(svc.label(node)) for node in chosen}) == len(chosen)


@pytest.mark.parametrize("record_id", [
    "lt_gastronomie_221", "lt_arta_cultura_003", "lt_muzica_058",
])
def test_representative_real_rounds_expose_tappable_alternatives_without_route_metadata(record_id):
    item = next(item for item in get_pack().pool("lant") if item.id == record_id)
    assert item._pilot_eligible
    client = Client()
    session = _session(item)
    gid = L.store.create(session)
    url = f"/api/wordgames/lant/games/{gid}"
    try:
        initial = client.get(url).json()
        assert initial["choices"] == client.get(url).json()["choices"]
        assert all(set(choice) == {"label", "relation"} for choice in initial["choices"])
        assert {"corridor", "on_track", "routes", "remaining_distance"}.isdisjoint(_keys(initial))
        assert len(initial["path"]) == 1 and initial["moves"] == 0
        if record_id == "lt_gastronomie_221":
            assert {"Pască", "Poale-n brâu"} <= {
                choice["label"] for choice in initial["choices"]
            }
        labels = {get_service().label(node) for node in L._shortest_hops(session)[:2]}
        assert len(labels) == 2
        assert labels <= {choice["label"] for choice in initial["choices"]}
        for label in labels:
            next_id = L.store.create(_session(item))
            try:
                moved = client.post(
                    f"/api/wordgames/lant/games/{next_id}/move", {"text": label},
                    content_type="application/json",
                ).json()
                assert moved["ok"] and moved["moves"] == 1
                assert moved["progress"]["kind"] == "closer"
            finally:
                L.store.delete(next_id)
    finally:
        L.store.delete(gid)
