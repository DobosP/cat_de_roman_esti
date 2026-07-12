"""Pytest guard over the curated games pack (ADR-0011).

Imports the committed validator (``scripts/validate_games_pack.py``) and asserts
the shipped pack passes every shape/enum/playability invariant with zero errors,
that both bundled copies are byte-identical, and that the taxonomy mirrors
(``validate_fixture.CATEGORIES`` vs ``wordgames.categories``) and the game-rule
constants mirrored into ``wordgames.packs`` never drift from the game modules.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent


def _load_script(name: str):
    spec = importlib.util.spec_from_file_location(name, _REPO_ROOT / "scripts" / f"{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


pack_validator = _load_script("validate_games_pack")
kg_validator = _load_script("validate_fixture")


@pytest.mark.parametrize(
    ("pack_path", "kg_path"),
    [
        (pack_validator.PACKAGE_PACK, pack_validator.PACKAGE_KG),
        (pack_validator.TESTS_PACK, pack_validator.TESTS_KG),
    ],
    ids=["package_copy", "tests_copy"],
)
def test_pack_has_zero_invariant_errors(pack_path, kg_path):
    errors = pack_validator.validate(pack_path, kg_path)
    assert errors == [], (
        f"{len(errors)} pack invariant error(s):\n" + "\n".join(f"  - {e}" for e in errors)
    )


def test_pack_copies_are_byte_identical():
    pkg = pack_validator.PACKAGE_PACK.read_bytes()
    tst = pack_validator.TESTS_PACK.read_bytes()
    assert pkg == tst


def test_pack_validator_main_exits_zero():
    assert pack_validator.main(["validate_games_pack.py"]) == 0


def test_category_taxonomy_mirrors_do_not_drift():
    from cat_de_roman_esti.wordgames.categories import known_keys

    assert set(kg_validator.CATEGORIES) == set(known_keys())


def test_game_constant_mirrors_do_not_drift():
    pytest.importorskip("django")
    from cat_de_roman_esti.wordgames import alchimie, contexto, lant, packs

    assert packs.LANT_BANDS == lant._DIFFICULTY_BANDS
    assert packs.LANT_MIN_FIRST_HOP_CHOICES == lant._MIN_FIRST_HOP_CHOICES == 2
    assert packs.LANT_MIN_LAYER_WIDTH == lant._MIN_LAYER_WIDTH == 2
    assert packs.CONTEXTO_MIN_REACHABLE == contexto.MIN_REACHABLE
    assert packs.CONTEXTO_MIN_RESPONSIVE == contexto.MIN_RESPONSIVE
    assert packs.CONTEXTO_RESPONSIVE_MAX_HOPS == contexto.RESPONSIVE_MAX_HOPS
    assert packs.ALCHIMIE_MIN_OPENING_PAIRS == alchimie.MIN_OPENING_PAIRS
    assert packs.ALCHIMIE_SEED_RANGE == (alchimie.SEED_MIN, alchimie.SEED_MAX)
    assert packs.ALCHIMIE_MAX_ACTIONS == 6
    assert packs.ALCHIMIE_MAX_SEARCH_STATES == 50_000
    assert packs.CONEXIUNI_GROUPS == 4 and packs.CONEXIUNI_GROUP_SIZE == 4


def test_contexto_validator_uses_directed_guess_to_target_distances(monkeypatch):
    from cat_de_roman_esti.graph import Graph
    from cat_de_roman_esti.wordgames import packs
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
    monkeypatch.setattr(packs, "CONTEXTO_MIN_REACHABLE", 3)
    monkeypatch.setattr(packs, "CONTEXTO_MIN_RESPONSIVE", 2)

    assert len(svc.distances_from("target")) == 2  # wrong direction would fail the floor
    assert packs._validate_contexto({"target": "target"}, svc) == []


def test_alchimie_par_counts_sequential_actions_not_parallel_rounds():
    from cat_de_roman_esti.wordgames import packs

    class RecipeService:
        nodes = {"a", "b", "c", "d", "e", "x", "y", "target"}
        recipes = {
            frozenset(("a", "b")): ["x"],
            frozenset(("c", "d")): ["y"],
            frozenset(("x", "y")): ["target"],
        }

        def exists(self, node_id):
            return node_id in self.nodes

        def common_neighbors(self, a, b, *, category=None):
            assert category == "societate"
            return self.recipes.get(frozenset((a, b)), [])

    svc = RecipeService()
    seeds = ["a", "b", "c", "d", "e"]
    assert packs._closure_generations(svc, seeds, "societate")["target"] == 2
    assert packs.minimum_alchimie_actions(
        svc, seeds, "target", "societate", max_actions=2
    ) is None
    assert packs.minimum_alchimie_actions(
        svc, seeds, "target", "societate", max_actions=3
    ) == 3

    errors = packs._validate_alchimie(
        {
            "seeds": seeds,
            "target": "target",
            "target_depth": 2,
            "category": "societate",
        },
        svc,
    )
    assert errors == ["target_depth must equal the exact action par (3)"]


def test_every_approved_lant_has_real_shortest_path_choices():
    pytest.importorskip("django")
    from cat_de_roman_esti.wordgames.packs import (
        LANT_MIN_FIRST_HOP_CHOICES,
        LANT_MIN_LAYER_WIDTH,
        get_pack,
        lant_branch_profile,
    )
    from cat_de_roman_esti.wordgames.service import get_service

    svc = get_service()
    items = get_pack().pool("lant")
    # v14-era boards + 5 promoted, minus re-derivation retirements (v16, v18, 2× v20).
    assert len(items) == 90
    assert "lt_stiinta_200" not in {item.id for item in items}
    for item in items:
        first_hop, min_width, _ = lant_branch_profile(
            svc,
            item.payload["start"],
            item.payload["target"],
            item.payload["optimal"],
        )
        assert first_hop >= LANT_MIN_FIRST_HOP_CHOICES, item.id
        assert min_width >= LANT_MIN_LAYER_WIDTH, item.id


def test_unresolvable_items_are_pruned_at_load():
    pytest.importorskip("django")
    from cat_de_roman_esti.wordgames.packs import (
        CuratedItem,
        resolvable_items,
    )
    from cat_de_roman_esti.wordgames.service import get_service

    good = CuratedItem(
        id="ct_ok", game="contexto", category="istorie", difficulty="normal",
        source="ai", status="approved", payload={"target": "n_dacia"},
    )
    ghost = CuratedItem(
        id="ct_ghost", game="contexto", category="istorie", difficulty="normal",
        source="ai", status="approved", payload={"target": "n_nu_exista"},
    )
    kept = resolvable_items([good, ghost], get_service())
    assert [i.id for i in kept] == ["ct_ok"]


def test_rendezvous_daily_pick_is_stable_and_order_independent():
    from cat_de_roman_esti.wordgames.packs import CuratedItem, GamesPack

    def item(iid: str) -> CuratedItem:
        return CuratedItem(
            id=iid, game="contexto", category="istorie", difficulty="normal",
            source="ai", status="approved", payload={"target": "n_dacia"},
        )

    a, b, c = item("ct_a"), item("ct_b"), item("ct_c")
    pack1 = GamesPack([a, b, c])
    pack2 = GamesPack([c, a, b])  # same items, different insertion order
    day = "2026-07-07"
    pick1 = pack1.pick_daily("contexto", day, min_pool=1)
    pick2 = pack2.pick_daily("contexto", day, min_pool=1)
    assert pick1 is not None and pick1.id == pick2.id
    # A different day may pick differently, but stays deterministic per day.
    assert pack1.pick_daily("contexto", "2026-07-08", min_pool=1).id == pack2.pick_daily(
        "contexto", "2026-07-08", min_pool=1
    ).id
    # Below the variety floor, the shared (category-less) daily declines to pick.
    assert pack1.pick_daily("contexto", day) is None
