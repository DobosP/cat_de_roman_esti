"""Deterministic tests for the content-critique lints (scripts/critique_pack.py, ADR-0023)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

import apply_demotions  # noqa: E402
import apply_rereview  # noqa: E402
import critique_pack  # noqa: E402
import import_candidates  # noqa: E402
import validate_games_pack  # noqa: E402


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


def test_apply_demotions_rejects_filename_game_mismatch(tmp_path):
    pack = json.loads(critique_pack.PACKAGE_PACK.read_text(encoding='utf-8'))
    approved = next(item for item in pack['conexiuni'] if item['status'] == 'approved')
    (tmp_path / 'conexiuni_demotions.json').write_text(
        json.dumps({'game': 'contexto', 'verdicts': {approved['id']: 'demote'}}),
        encoding='utf-8',
    )
    with pytest.raises(SystemExit, match='invalid demotion contract'):
        apply_demotions.main(['apply_demotions.py', '--dir', str(tmp_path)])


def test_candidate_imports_are_always_pending_until_critique():
    assert import_candidates.candidate_import_status('keep') == 'pending'
    assert import_candidates.candidate_import_status('fix') == 'pending'
    assert import_candidates.candidate_import_status('drop') is None
    assert import_candidates.candidate_import_status('surprise') is None


def test_candidate_ids_allocate_after_highest_suffix_not_list_length():
    items = [
        {'id': 'lt_stiinta_002'},
        {'id': 'lt_viata_de_roman_205'},
        {'id': 'lt_literatura_099'},
    ]
    assert import_candidates.next_item_number(items, 'lt') == 206


def test_candidate_ids_do_not_reuse_retired_highest_suffix():
    original = {
        game: [] for game in import_candidates.GAME_KINDS
    }
    original['lant'] = [
        {'id': 'lt_stiinta_002'},
        {'id': 'lt_viata_de_roman_209'},
    ]
    survivors_after_rederive = original['lant'][:-1]
    assert import_candidates.next_item_number(survivors_after_rederive, 'lt') == 3
    first_run_marks = import_candidates.item_high_water(original)
    second_run = {
        **original,
        'meta': {'id_high_water': first_run_marks},
        'lant': survivors_after_rederive,
    }
    assert import_candidates.initial_item_numbers(second_run)['lant'] == 210


def test_pack_validator_rejects_lowered_id_high_water(tmp_path):
    pack = json.loads(critique_pack.PACKAGE_PACK.read_text(encoding='utf-8'))
    pack['meta']['id_high_water']['lant'] = 0
    path = tmp_path / 'games_pack.json'
    path.write_text(json.dumps(pack), encoding='utf-8')
    errors = validate_games_pack.validate(path, validate_games_pack.PACKAGE_KG)
    assert any(error.startswith('id_high_water: lant mark 0') for error in errors)


def _write_gate_artifact(
    path, game, verdicts, *, verified=True, batch_ids=None,
    review_binding='sha256:' + ('a' * 64),
):
    ids = list(verdicts) if batch_ids is None else list(batch_ids)
    count = len(verdicts)
    path.write_text(
        json.dumps({
            'game': game,
            'mode': 'gate',
            'batch': {'version': 2, 'mode': 'gate', 'input_ids': sorted(ids)},
            'verdicts': verdicts,
            'perItem': [
                {
                    'id': iid, 'game': game, 'final': verdict,
                    'verified': verified, 'verifier_lost': not verified,
                    'review_binding': review_binding,
                }
                for iid, verdict in verdicts.items()
            ],
            'coverage': {
                'total': count,
                'verified': count if verified else 0,
                'unverifiedClean': 0,
                'verifiersLost': 0 if verified else count,
                'lost': 0,
            },
        }),
        encoding='utf-8',
    )


def test_apply_rereview_blocks_failed_critique_before_writes(tmp_path, monkeypatch):
    pack = json.loads(critique_pack.PACKAGE_PACK.read_text(encoding='utf-8'))
    pending = next(item for item in pack['conexiuni'] if item['status'] == 'pending')
    verdict_path = tmp_path / 'conexiuni_verdicts.json'
    _write_gate_artifact(
        verdict_path, 'conexiuni', {pending['id']: 'promote'},
    )
    originals = {path: path.read_bytes() for path in apply_rereview.PACK_COPIES}
    monkeypatch.setattr(
        apply_rereview, 'current_review_bindings',
        lambda _ids: {pending['id']: 'sha256:' + ('a' * 64)},
    )
    monkeypatch.setattr(apply_rereview, 'critique_promotions', lambda _ids: 1)
    with pytest.raises(SystemExit, match='promotion blocked'):
        apply_rereview.main(['apply_rereview.py', '--dir', str(tmp_path)])
    assert all(path.read_bytes() == blob for path, blob in originals.items())


def test_apply_rereview_rejects_unverified_workflow_artifact(tmp_path, monkeypatch):
    pack = json.loads(critique_pack.PACKAGE_PACK.read_text(encoding='utf-8'))
    pending = next(item for item in pack['conexiuni'] if item['status'] == 'pending')
    _write_gate_artifact(
        tmp_path / 'conexiuni_verdicts.json',
        'conexiuni',
        {pending['id']: 'promote'},
        verified=False,
    )
    monkeypatch.setattr(
        apply_rereview, 'critique_promotions',
        lambda _ids: pytest.fail('critique must not run for an unverified artifact'),
    )
    with pytest.raises(SystemExit, match='not fully verified'):
        apply_rereview.main(['apply_rereview.py', '--dir', str(tmp_path)])


def test_apply_rereview_rejects_hand_combined_gate_batches(tmp_path):
    pack = json.loads(critique_pack.PACKAGE_PACK.read_text(encoding='utf-8'))
    cx = next(item for item in pack['conexiuni'] if item['status'] == 'pending')
    ct = next(item for item in pack['contexto'] if item['status'] == 'pending')
    _write_gate_artifact(
        tmp_path / 'conexiuni_verdicts.json', 'conexiuni', {cx['id']: 'keep'},
    )
    _write_gate_artifact(
        tmp_path / 'contexto_verdicts.json', 'contexto', {ct['id']: 'keep'},
    )
    with pytest.raises(SystemExit, match='same gate batch'):
        apply_rereview.main(['apply_rereview.py', '--dir', str(tmp_path)])


def test_apply_rereview_rejects_stale_artifact_after_content_edit(tmp_path, monkeypatch):
    pack = json.loads(critique_pack.PACKAGE_PACK.read_text(encoding='utf-8'))
    pending = next(item for item in pack['conexiuni'] if item['status'] == 'pending')
    _write_gate_artifact(
        tmp_path / 'conexiuni_verdicts.json',
        'conexiuni',
        {pending['id']: 'promote'},
        review_binding='sha256:' + ('b' * 64),
    )
    monkeypatch.setattr(
        apply_rereview, 'current_review_bindings',
        lambda _ids: {pending['id']: 'sha256:' + ('c' * 64)},
    )
    monkeypatch.setattr(
        apply_rereview, 'critique_promotions',
        lambda _ids: pytest.fail('stale artifacts must fail before deterministic critique'),
    )
    with pytest.raises(SystemExit, match='stale gate artifact'):
        apply_rereview.main(['apply_rereview.py', '--dir', str(tmp_path)])


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


def test_explicit_selection_rejects_unknown_and_filtered_ids(loaded):
    pack, svc, strong, regions = loaded
    target = pack['conexiuni'][0]['id']
    _, _, selected = critique_pack.run(
        pack, svc, strong, regions, ['contexto'], {'approved'}, {target, 'missing_id'}
    )
    errors = critique_pack.selection_errors(
        pack, ['contexto'], {'approved'}, {target, 'missing_id'}, selected
    )
    assert errors == [
        f'{target} belongs to game \'conexiuni\', excluded by --game',
        'unknown item id: missing_id',
    ]


def test_selected_pending_boards_are_compared_with_each_other(loaded):
    pack, svc, strong, regions = loaded
    approved_quads = {
        frozenset(group)
        for rec in pack['conexiuni'] if rec['status'] == 'approved'
        for group in rec['groups'].values()
    }
    base = next(
        rec for rec in pack['conexiuni']
        if rec['status'] == 'pending'
        and all(frozenset(group) not in approved_quads for group in rec['groups'].values())
    )
    first = {**base, 'id': 'cx_batch_duplicate_a'}
    second = {**base, 'id': 'cx_batch_duplicate_b'}
    batch_pack = {**pack, 'conexiuni': [*pack['conexiuni'], first, second]}
    items, _, _ = critique_pack.run(
        batch_pack, svc, strong, regions, ['conexiuni'], {'pending'},
        {first['id'], second['id']},
    )
    for iid in (first['id'], second['id']):
        duplicate_findings = [
            finding for finding in items[iid]['findings']
            if finding['check'] == 'duplicate_groups'
        ]
        assert duplicate_findings
        assert any(finding['level'] == 'FAIL' for finding in duplicate_findings)


def test_selected_batch_reports_projected_member_overuse(loaded):
    pack, svc, strong, regions = loaded
    base = pack['conexiuni'][0]
    approved = [
        {**base, 'id': f'cx_overuse_{index}', 'status': 'approved'}
        for index in range(critique_pack.MEMBER_OVERUSE)
    ]
    candidate = {**base, 'id': 'cx_overuse_candidate', 'status': 'pending'}
    mini_pack = {
        'meta': {}, 'conexiuni': [*approved, candidate],
        'contexto': [], 'lant': [], 'alchimie': [],
    }
    items, _, _ = critique_pack.run(
        mini_pack, svc, strong, regions, ['conexiuni'], {'pending'}, {candidate['id']}
    )
    assert any(
        finding['check'] == 'member_overuse'
        for finding in items[candidate['id']]['findings']
    )


def test_contexto_dossier_neighbors_follow_guess_to_target_direction(loaded):
    pack, svc, strong, _ = loaded
    rec = next(
        item for item in pack['contexto']
        if any(svc.link(nid, item['target']) is None for nid in strong.get(item['target'], {}))
    )
    dossier = critique_pack.build_dossier(rec, 'contexto', svc, strong, [])
    assert dossier['strong_neighbors']
    assert all(svc.link(item['id'], rec['target']) for item in dossier['strong_neighbors'])
    target = dossier['target']
    assert target['degree'] == len(svc.neighbor_ids(rec['target']))
    assert target['incoming_degree'] == len(svc.predecessor_ids(rec['target']))
    assert dossier['review_binding'].startswith('sha256:')


def test_dossier_binding_changes_with_reviewed_content(loaded):
    pack, svc, strong, regions = loaded
    rec = pack['conexiuni'][0]
    dossier = critique_pack.build_dossier(rec, 'conexiuni', svc, strong, [], regions)
    changed_rec = {**rec, 'order': list(reversed(rec['order']))}
    changed = critique_pack.build_dossier(
        changed_rec, 'conexiuni', svc, strong, [], regions,
    )
    assert changed['review_binding'] != dossier['review_binding']


def test_workflow_requires_two_layers_for_gate_promotions():
    workflow = (_REPO_ROOT / '.claude' / 'workflows' / 'critique-games.js').read_text(
        encoding='utf-8'
    )
    assert "MODE === 'sweep' && clean" in workflow
    assert 'critique.id !== id' in workflow
    assert 'verdict.id === id' in workflow
    assert 'verdict.review_binding === critique.review_binding' in workflow
    assert "A.repo || '.'" in workflow
    assert "lant: 'D', alchimie: 'E'" in workflow
    assert 'const batch = { version: 2' in workflow
    assert 'return { mode: MODE, batch, verdicts, perItem, coverage, artifacts }' in workflow


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


def test_lant_and_alchimie_dossiers_expose_choice_profiles(loaded):
    pack, svc, strong, _ = loaded
    lant = next(item for item in pack['lant'] if item['status'] == 'approved')
    lant_dossier = critique_pack.build_dossier(lant, 'lant', svc, strong, [])
    assert lant_dossier['branch_profile']['valid_first_hops'] >= 2
    assert lant_dossier['branch_profile']['narrowest_shortest_path_layer'] >= 2
    paths = lant_dossier['representative_shortest_paths']
    assert paths
    for path in paths:
        assert path['nodes'][0]['id'] == lant['start']
        assert path['nodes'][-1]['id'] == lant['target']
        assert len(path['edges']) == lant['optimal']
        assert all(edge['relation'] for edge in path['edges'])

    alchimie = next(item for item in pack['alchimie'] if item['status'] == 'approved')
    alchimie_dossier = critique_pack.build_dossier(
        alchimie, 'alchimie', svc, strong, [],
    )
    assert alchimie_dossier['craft_profile']['opening_pairs'] >= 2
    assert alchimie_dossier['craft_profile']['target_generation'] is not None
    assert alchimie_dossier['productive_openings']
    recipe = alchimie_dossier['minimum_action_recipe']
    assert recipe and len(recipe) == alchimie['target_depth']
    assert alchimie['target'] in {
        result['id'] for result in recipe[-1]['results']
    }


def test_all_choice_evidence_is_distinct_and_self_contained(loaded):
    pack, svc, strong, _ = loaded
    for item in pack['lant']:
        if item['status'] != 'approved':
            continue
        dossier = critique_pack.build_dossier(item, 'lant', svc, strong, [])
        paths = dossier['representative_shortest_paths']
        first_hops = {path['nodes'][1]['id'] for path in paths}
        expected = min(dossier['branch_profile']['valid_first_hops'], 3)
        assert len(first_hops) == expected

    for item in pack['alchimie']:
        if item['status'] != 'approved':
            continue
        dossier = critique_pack.build_dossier(item, 'alchimie', svc, strong, [])
        owned = set(item['seeds'])
        for step in dossier['minimum_action_recipe']:
            assert {node['id'] for node in step['pair']} <= owned
            owned.update(node['id'] for node in step['results'])
