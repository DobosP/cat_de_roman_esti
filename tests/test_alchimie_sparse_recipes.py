"""V34 Alchimie sparse-recipe, inventory, and deterministic-quality contracts."""

from __future__ import annotations

import hashlib
import json
import random
import time
from collections import Counter
from statistics import median

import pytest

pytest.importorskip("django")

from django.test import Client  # noqa: E402

from cat_de_roman_esti.graph import Graph  # noqa: E402
from cat_de_roman_esti.wordgames import alchimie as A  # noqa: E402
from cat_de_roman_esti.wordgames.packs import get_pack  # noqa: E402
from cat_de_roman_esti.wordgames.service import WordGameService  # noqa: E402


def _projection_row(item, projection: A.RecipeProjection) -> dict[str, object]:
    return {
        "id": item.id,
        "par": projection.par,
        "routes": len(projection.routes),
        "recipes": [
            [*pair, *outputs] for pair, outputs in projection.recipes.items()
        ],
    }


@pytest.fixture(scope="module")
def approved_projections() -> tuple[list[tuple[object, A.RecipeProjection]], float]:
    A._build_recipe_projection_cached.cache_clear()
    started = time.perf_counter()
    out = []
    for item in get_pack().pool("alchimie"):
        projection = A._build_recipe_projection(
            item.payload["seeds"], item.payload["target"], item.category
        )
        assert projection is not None
        out.append((item, projection))
    return out, time.perf_counter() - started


def test_all_approved_boards_have_sparse_deterministic_target_routes(
    approved_projections,
) -> None:
    projections, elapsed = approved_projections
    rows = [_projection_row(item, projection) for item, projection in projections]
    digest = hashlib.sha256(
        json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()

    assert len(rows) == 77
    assert digest == "d1daaaab03a5af4d8ba797d38f8968eab24c7f04a154c4e155d86d708a26f4ef"
    assert elapsed < 30.0
    assert Counter(row["routes"] for row in rows) == {1: 5, 2: 6, 3: 7, 4: 59}

    recipe_count = 0
    tied_count = 0
    opening_counts: Counter[int] = Counter()
    for item, projection in projections:
        assert projection.par == item.payload["target_depth"]
        assert 1 <= len(projection.routes) <= A.MAX_TARGET_ROUTES
        assert len(projection.recipes) <= A.MAX_RECIPE_PAIRS
        assert max(map(len, projection.recipes.values())) <= A.MAX_RESULTS_PER_RECIPE
        projected_nodes = set(item.payload["seeds"])
        for pair, outputs in projection.recipes.items():
            projected_nodes.update(pair)
            projected_nodes.update(outputs)
            # A two-result exception must be required together by an actual selected
            # route, never synthesized by merging two unrelated singleton alternatives.
            if len(outputs) == 2:
                assert any(
                    any(
                        step_pair == pair and step_outputs == outputs
                        for step_pair, step_outputs in route
                    )
                    for route in projection.routes
                )
        assert len(projected_nodes) <= A.MAX_PROJECTED_CONCEPTS
        plan = A._minimum_projected_plan(
            set(item.payload["seeds"]), item.payload["target"], projection.recipes
        )
        assert plan is not None and len(plan) == projection.par
        recipe_count += len(projection.recipes)
        tied_count += sum(len(outputs) == 2 for outputs in projection.recipes.values())
        opening_counts[
            A._projected_opening_pair_count(item.payload["seeds"], projection.recipes)
        ] += 1

    assert recipe_count == 536
    assert tied_count == 77
    assert sum(count for openings, count in opening_counts.items() if openings >= 2) == 61
    assert opening_counts[1] == 16


def test_selected_routes_prefer_the_strongest_discovered_shortest_alternative(
    approved_projections,
) -> None:
    projections, _elapsed = approved_projections
    selected_minima: list[float] = []
    weak_fallbacks: list[str] = []
    for item, projection in projections:
        selected = [A._route_quality(route) for route in projection.routes]
        selected_minima.extend(quality[0] for quality in selected)
        available_shortest = [
            (minimum, average)
            for actions, minimum, average in projection.candidate_quality
            if actions == projection.par
        ]
        # Among routes discovered inside the explicit state/candidate bounds, sorting
        # protects the weakest link, then the mean, before deterministic ids.
        assert selected[0][:2] == max(available_shortest)
        for index, quality in enumerate(selected):
            if quality[0] < A.PREFERRED_RECIPE_STRENGTH:
                assert index == 0  # only the mandatory solvability route may be weak
                weak_fallbacks.append(item.id)

    assert min(selected_minima) == pytest.approx(0.40)
    assert median(selected_minima) == pytest.approx(0.66)
    assert weak_fallbacks == [
        "al_gastronomie_027",
        "al_gastronomie_029",
        "al_limba_048",
        "al_meme_net_057",
        "al_viata_de_roman_093",
    ]


def test_projection_identity_survives_a_cold_rebuild() -> None:
    item = get_pack().pool("alchimie")[0]
    A._build_recipe_projection_cached.cache_clear()
    first = A._build_recipe_projection(
        item.payload["seeds"], item.payload["target"], item.category
    )
    A._build_recipe_projection_cached.cache_clear()
    second = A._build_recipe_projection(
        item.payload["seeds"], item.payload["target"], item.category
    )
    assert first == second


def test_projection_cache_invalidates_when_service_identity_changes(monkeypatch) -> None:
    nodes = [
        {
            "id": node_id,
            "label_ro": node_id.upper(),
            "category": "test",
            "salience": 1.0,
        }
        for node_id in ("a", "b", "c", "target")
    ]

    def service_with_parent(parent: str) -> WordGameService:
        edges = [
            {
                "id": f"a-target-{parent}",
                "src_id": "a",
                "dst_id": "target",
                "relation": "related_to",
                "strength": 0.9,
                "bidirectional": False,
            },
            {
                "id": f"{parent}-target",
                "src_id": parent,
                "dst_id": "target",
                "relation": "related_to",
                "strength": 0.9,
                "bidirectional": False,
            },
        ]
        return WordGameService(Graph.from_records(nodes, edges))

    first_service = service_with_parent("b")
    second_service = service_with_parent("c")
    active_service = [first_service]
    monkeypatch.setattr(A, "get_service", lambda: active_service[0])
    A._build_recipe_projection_cached.cache_clear()

    first = A._build_recipe_projection(["a", "b", "c"], "target", "test")
    assert first is not None
    assert first.recipes == {("a", "b"): ("target",)}

    active_service[0] = second_service
    second = A._build_recipe_projection(["a", "b", "c"], "target", "test")
    assert second is not None
    assert second.recipes == {("a", "c"): ("target",)}
    assert A._build_recipe_projection_cached.cache_info().currsize == 1


def test_many_mined_sessions_stay_bounded_solvable_and_fast() -> None:
    A._build_recipe_projection_cached.cache_clear()
    started = time.perf_counter()
    sessions = [
        A._build_session(
            random.Random(seed),
            difficulty=("usor", "normal", "greu")[seed % 3],
        )
        for seed in range(12)
    ]
    elapsed = time.perf_counter() - started

    # Shared CI can be substantially slower under parallel graph-heavy jobs. This stays a
    # coarse regression ceiling; the structural bounds below remain the correctness gate.
    assert elapsed < 45.0
    for session in sessions:
        assert 1 <= len(session.routes) <= A.MAX_TARGET_ROUTES
        assert len(session.recipes) <= A.MAX_RECIPE_PAIRS
        assert max(map(len, session.recipes.values())) <= A.MAX_RESULTS_PER_RECIPE
        plan = A._minimum_projected_plan(
            set(session.seeds), session.target, session.recipes
        )
        assert plan is not None and len(plan) == session.target_depth


def test_inventory_views_are_additive_bounded_and_do_not_expose_recipes() -> None:
    client = Client()
    body = client.post("/api/wordgames/alchimie/games?seed=7").json()
    session = A.store.get(body["game_id"])
    assert session is not None

    assert set(body["inventory_summary"]) == {"active", "depleted", "total"}
    assert body["inventory_summary"]["total"] == len(body["inventory"])
    assert body["inventory_summary"]["active"] <= A.MAX_PROJECTED_CONCEPTS
    assert body["recipe_summary"] == {
        "pairs": len(session.recipes),
        "routes": len(session.routes),
        "max_results": max(map(len, session.recipes.values())),
    }
    assert "recipes" not in body and "routes" not in body
    for item in body["inventory"]:
        assert {"recent", "useful", "ready", "depleted"} <= set(item)
        assert item["depleted"] is (not item["useful"])

    pair = A._useful_pair(session)
    assert pair is not None
    combined = client.post(
        f"/api/wordgames/alchimie/games/{body['game_id']}/combine",
        {"a": pair[0], "b": pair[1]},
        content_type="application/json",
    ).json()
    assert 1 <= len(combined["discovered"]) <= A.MAX_RESULTS_PER_RECIPE
    assert combined["inventory_summary"]["total"] == len(combined["inventory"])
