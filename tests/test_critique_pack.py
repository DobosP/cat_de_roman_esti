"""Deterministic tests for the content-critique lints (scripts/critique_pack.py, ADR-0023)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

import apply_demotions  # noqa: E402
import critique_pack  # noqa: E402


# --------------------------------------------------------------------- pure helpers
def test_classify_type_mix_homogeneous_is_clean():
    assert critique_pack.classify_type_mix(["event"] * 4) is None


def test_classify_type_mix_flags_three_plus_one_outlier():
    # The reported failure shape: Untold/Neversea/Electric Castle + Bonțida[place].
    assert critique_pack.classify_type_mix(["event", "event", "event", "place"]) == "3+1"


def test_classify_type_mix_flags_two_plus_two_split():
    assert critique_pack.classify_type_mix(["event", "event", "place", "place"]) == "2+2"


def test_classify_type_mix_leaves_diverse_groups_to_judges():
    assert critique_pack.classify_type_mix(["event", "place", "work", "work"]) is None


def test_max_matching_disjoint_pairs():
    pairs = {"untold": {"cluj"}, "neversea": {"constanta"}, "ec": {"bontida"}}
    assert critique_pack.max_matching(pairs) == 3


def test_max_matching_shared_right_node_counts_once():
    pairs = {"a": {"x"}, "b": {"x"}, "c": {"x"}}
    assert critique_pack.max_matching(pairs) == 1


def test_max_matching_uses_augmenting_paths():
    # Greedy a->x would block b; augmenting reassigns a->y for a full matching.
    pairs = {"a": {"x", "y"}, "b": {"x"}}
    assert critique_pack.max_matching(pairs) == 2


def _mini_board():
    groups = {"g1": ["a1", "a2", "a3", "a4"], "g2": ["b1", "b2", "b3", "b4"]}
    node_types = {n: "event" for n in groups["g1"]} | {n: "place" for n in groups["g2"]}
    return groups, node_types


def test_fairness_ignores_type_incompatible_pull():
    # a1's edges all point at the foreign group, but no g2 member shares its type:
    # the raw engine rule would call it unfair; the confusability rule must not.
    groups, node_types = _mini_board()
    neighbors = {"a1": {"b1", "b2"}}
    unfair, contested, engine_unfair = critique_pack.fairness_counts(
        groups, neighbors, node_types
    )
    assert unfair == [] and contested == []
    assert engine_unfair == 1


def test_fairness_flags_type_compatible_pull():
    groups, node_types = _mini_board()
    node_types["a1"] = "place"  # now a1 could visually belong to g2
    neighbors = {"a1": {"b1", "b2"}}
    unfair, _, _ = critique_pack.fairness_counts(groups, neighbors, node_types)
    assert unfair == ["a1"]


def test_fairness_counts_contested_tie():
    groups, node_types = _mini_board()
    node_types["a1"] = "place"
    neighbors = {"a1": {"a2", "b1"}}  # own pull 1, type-compatible foreign pull 1
    unfair, contested, _ = critique_pack.fairness_counts(groups, neighbors, node_types)
    assert unfair == [] and contested == ["a1"]


def test_salience_floors_cover_every_difficulty_band():
    assert set(critique_pack.SALIENCE_FLOORS) == {"usor", "normal", "greu"}
    floors = critique_pack.SALIENCE_FLOORS
    assert floors["usor"] > floors["normal"] > floors["greu"]


def test_generic_region_flags_multi_region_fanout():
    # The reported failure: Sarmale -> Moldova AND Transilvania (true of all Romania).
    reason = critique_pack.classify_generic_region(
        "concept", 0.98,
        [("Moldova", "related_to", 0.52), ("Transilvania", "related_to", 0.50)],
    )
    assert reason and "2 regions" in reason


def test_generic_region_flags_national_concept_single_region():
    # Mămăligă (national staple) claiming Moldova via a generic related_to edge.
    reason = critique_pack.classify_generic_region(
        "concept", 0.97, [("Moldova", "related_to", 0.83)]
    )
    assert reason and "national-salience" in reason


def test_generic_region_leaves_biographic_links_alone():
    # Eminescu -> Moldova is distinctive (born Botoșani); persons are never flagged
    # on a single region link.
    assert critique_pack.classify_generic_region(
        "person", 0.83, [("Moldova", "related_to", 0.80)]
    ) is None


def test_generic_region_ignores_low_salience_single_region():
    assert critique_pack.classify_generic_region(
        "concept", 0.30, [("Bucovina", "related_to", 0.70)]
    ) is None


# --------------------------------------------------------------------- demote path
def _mini_pack():
    return {
        "meta": {"counts": {"conexiuni": 2, "contexto": 1, "lant": 0, "alchimie": 0}},
        "conexiuni": [
            {"id": "cx_a", "status": "approved"},
            {"id": "cx_b", "status": "approved"},
        ],
        "contexto": [{"id": "ct_a", "status": "pending"}],
        "lant": [],
        "alchimie": [],
    }


def test_apply_demotions_moves_approved_to_pending_only():
    pack, stats = apply_demotions.apply(_mini_pack(), {"cx_a": "demote"})
    assert stats["demote"] == 1
    by_id = {it["id"]: it for game in ("conexiuni", "contexto") for it in pack[game]}
    assert by_id["cx_a"]["status"] == "pending"  # demoted, never deleted
    assert by_id["cx_b"]["status"] == "approved"


def test_apply_demotions_never_touches_pending_items():
    # The mirror-image safety of apply_rereview: a stray demote verdict on a pending
    # item is a no-op, so the two scripts can never fight over the same item.
    pack, stats = apply_demotions.apply(_mini_pack(), {"ct_a": "demote"})
    assert stats["demote"] == 0
    assert pack["contexto"][0]["status"] == "pending"


def test_apply_demotions_keep_and_counts():
    pack, stats = apply_demotions.apply(
        _mini_pack(), {"cx_a": "keep", "cx_b": "demote"}
    )
    assert stats["demote"] == 1 and "unknown_verdict" not in stats
    assert pack["meta"]["counts"]["conexiuni"] == 2  # totals unchanged by demotion


# --------------------------------------------------------------------- integration
@pytest.fixture(scope="module")
def loaded():
    return critique_pack.load_all(critique_pack.PACKAGE_PACK, critique_pack.PACKAGE_KG)


def test_run_over_real_pack_is_bounded_and_typed(loaded):
    pack, svc, strong, regions = loaded
    items, pack_findings, selected = critique_pack.run(
        pack, svc, strong, regions, ["contexto"], {"approved"}, None
    )
    assert len(selected) > 0
    for info in items.values():
        assert info["game"] == "contexto"
        for finding in info["findings"]:
            assert finding["check"] in ("salience_floor", "generic_region_link")
            assert finding["level"] == "WARN"


def test_sarmale_region_links_flagged_in_real_kg(loaded):
    _, _, _, regions = loaded
    pack, svc, strong, _ = loaded
    flagged_labels = {
        critique_pack.node_brief(svc, nid)["label"]
        for nid in regions["generic_nodes"]
    }
    assert "Sarmale" in flagged_labels


def test_ids_filter_selects_exactly_the_requested_items(loaded):
    pack, svc, strong, regions = loaded
    target = pack["conexiuni"][0]["id"]
    _, _, selected = critique_pack.run(
        pack, svc, strong, regions, ["conexiuni"], {"approved", "pending"}, {target}
    )
    assert [rec["id"] for _, rec, _ in selected] == [target]


def test_duplicate_groups_flags_exact_and_near_duplicates(loaded):
    pack, svc, strong, _ = loaded
    rec = {**pack["conexiuni"][0], "status": "pending"}
    groups = rec["groups"]
    first_key = sorted(groups)[0]
    quad = groups[first_key]
    exact = {frozenset(quad): ["cx_other_board"]}
    findings = critique_pack.check_conexiuni(rec, svc, strong, exact)
    dups = [f for f in findings if f["check"] == "duplicate_groups"]
    assert dups and dups[0]["level"] == "FAIL"  # pending item reusing an approved quad

    other = next(n for g in groups.values() for n in g if n not in quad)
    near = {frozenset(quad[:3] + [other]): ["cx_near_board"]}
    findings = critique_pack.check_conexiuni(rec, svc, strong, near)
    dups = [f for f in findings if f["check"] == "duplicate_groups"]
    assert dups and dups[0]["level"] == "WARN"
    assert "near-duplicate" in dups[0]["detail"]


def test_null_group_labels_do_not_crash(loaded):
    pack, svc, strong, _ = loaded
    rec = {**pack["conexiuni"][0], "group_labels": None}
    critique_pack.check_conexiuni(rec, svc, strong, {})
    dossier = critique_pack.build_dossier(rec, "conexiuni", svc, strong, [])
    assert len(dossier["groups"]) == 4


def test_dossier_carries_judge_context(loaded):
    pack, svc, strong, _ = loaded
    rec = pack["conexiuni"][0]
    dossier = critique_pack.build_dossier(rec, "conexiuni", svc, strong, [])
    assert dossier["id"] == rec["id"]
    assert len(dossier["groups"]) == 4
    assert all(len(g["members"]) == 4 for g in dossier["groups"])
    assert "fairness" in dossier and "cross_group_strong_edges" in dossier
    ct = pack["contexto"][0]
    ct_dossier = critique_pack.build_dossier(ct, "contexto", svc, strong, [])
    assert ct_dossier["target"]["id"] == ct["target"]
    assert ct_dossier["reachable"] >= 120  # engine floor for approved targets
