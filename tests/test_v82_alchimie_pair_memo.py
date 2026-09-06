"""Pair discovery is invariant across BFS inventories, including after memo capacity."""

from __future__ import annotations

from collections import Counter

import pytest

pytest.importorskip("django")

from cat_de_roman_esti.graph import Graph  # noqa: E402
from cat_de_roman_esti.wordgames import alchimie as A  # noqa: E402
from cat_de_roman_esti.wordgames.service import WordGameService  # noqa: E402


def _branching_service() -> WordGameService:
    # Two independent intermediate crafts create four inventory states. The target
    # requires both intermediates; d introduces empty pairs that are also revisited.
    ids = ("a", "b", "c", "d", "x", "y", "target")
    edges = [
        (parent, output)
        for output, parents in (("x", ("a", "b")), ("y", ("a", "c")),
                                ("target", ("x", "y")))
        for parent in parents
    ]
    return WordGameService(Graph.from_records(
        [{"id": node, "label_ro": node, "category": "test", "salience": 1.0} for node in ids],
        [
            {"id": f"e{index}", "src_id": parent, "dst_id": output,
             "relation": "related_to", "strength": 0.9, "bidirectional": False}
            for index, (parent, output) in enumerate(edges)
        ],
    ))


def _expected_projection() -> A.RecipeProjection:
    return A.RecipeProjection(
        recipes={("a", "b"): ("x",), ("a", "c"): ("y",), ("x", "y"): ("target",)},
        routes=(((('a', 'b'), ('x',)), (('a', 'c'), ('y',)), (('x', 'y'), ('target',))),),
        par=3,
        candidate_quality=((3, 0.9, 0.9),),
    )


def _build_counted(monkeypatch, capacity: int):
    svc = _branching_service()
    calls: Counter[tuple[str, str]] = Counter()
    original = svc.common_neighbors

    def counted(a, b, *, category=None):
        calls[(a, b)] += 1
        return original(a, b, category=category)

    monkeypatch.setattr(A, "get_service", lambda: svc)
    monkeypatch.setattr(A, "MAX_PAIR_RESULT_CACHE", capacity)
    monkeypatch.setattr(svc, "common_neighbors", counted)
    A._build_recipe_projection_cached.cache_clear()
    projection = A._build_recipe_projection(["a", "b", "c", "d"], "target", "test")
    return projection, calls


def test_repeated_pairs_are_discovered_once_including_empty_results(monkeypatch):
    assert A.MAX_PAIR_RESULT_CACHE == 4096
    projection, calls = _build_counted(monkeypatch, A.MAX_PAIR_RESULT_CACHE)
    assert projection == _expected_projection()
    assert len(calls) == 15 and sum(calls.values()) == 15
    assert calls[("a", "b")] == 1  # productive pair revisited in four states
    assert calls[("a", "d")] == 1  # empty pair revisited in four states
    assert set(calls.values()) == {1}


@pytest.mark.parametrize("capacity", [0, 1, 2])
def test_capacity_exhaustion_changes_only_lookup_work_not_projection(monkeypatch, capacity):
    projection, calls = _build_counted(monkeypatch, capacity)
    assert projection == _expected_projection()
    # Sorted a/b and then a/c occupy the first two slots. Every later pair remains
    # uncached when those slots are exhausted, preserving complete graph discovery.
    assert calls[("a", "b")] == (1 if capacity >= 1 else 4)
    assert calls[("a", "c")] == (1 if capacity >= 2 else 4)
    assert calls[("a", "d")] == 4
    assert sum(calls.values()) == 41 - 3 * capacity


def test_pair_results_do_not_escape_a_cold_projection_build(monkeypatch):
    svc = _branching_service()
    calls = []
    original = svc.common_neighbors

    def counted(a, b, *, category=None):
        calls.append((a, b, category))
        return original(a, b, category=category)

    monkeypatch.setattr(A, "get_service", lambda: svc)
    monkeypatch.setattr(svc, "common_neighbors", counted)
    seeds = ["a", "b", "c", "d"]
    A._build_recipe_projection_cached.cache_clear()
    first = A._build_recipe_projection(seeds, "target", "test")
    first_calls = list(calls)
    calls.clear()
    A._build_recipe_projection_cached.cache_clear()
    assert A._build_recipe_projection(seeds, "target", "test") == first
    assert calls == first_calls
    calls.clear()
    assert A._build_recipe_projection(seeds, "target", "other") is None
    assert len(calls) == 6 and all(category == "other" for _, _, category in calls)
