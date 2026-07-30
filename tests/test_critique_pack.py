"""Deterministic tests for the content-critique lints (scripts/critique_pack.py, ADR-0023)."""

from __future__ import annotations

import hashlib
import json
import sys
from copy import deepcopy
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


def test_board_type_shortcut_requires_four_homogeneous_groups():
    groups = {
        "g1": ["a1", "a2", "a3", "a4"],
        "g2": ["b1", "b2", "b3", "b4"],
        "g3": ["c1", "c2", "c3", "c4"],
        "g4": ["d1", "d2", "d3", "d4"],
    }
    four_types = {
        node_id: group_id
        for group_id, members in groups.items()
        for node_id in members
    }
    assert critique_pack.board_type_shortcut(groups, four_types) == 4
    four_types["d4"] = "g3"
    assert critique_pack.board_type_shortcut(groups, four_types) is None


@pytest.mark.parametrize(
    ("label", "member", "foreign"),
    [
        ("Cuvinte care încep cu litera P", "Primar", "Document"),
        ("Cuvinte care se termină în ȚIE", "Justiție", "Document"),
        ("Denumirea afișată conține o cratimă", "O-Zone", "Aferim!"),
        (
            "Etichete afișate formate din exact trei litere majuscule",
            "CNP",
            "Document",
        ),
        ("Evenimente istorice cu anul în denumire", "Revoluția 1848", "Primar"),
        ("Încep cu S sau Ș", "Șnițel", "Ceai"),
        ("Încep cu șirul „Sala”", "Salată", "Muștar"),
        ("Se termină cu litera R", "Muștar", "Mărarul"),
        ("Au cuvântul „cu” în denumire", "Fasole cu ciolan", "Cuvânt"),
        ("Numele afișat are exact trei cuvinte", "Ana Maria Brânză", "Ana Blandiana"),
        ("Prenume din exact patru litere", "Radu Drăgușin", "Dan Petrescu"),
        (
            "Primul cuvânt al numelui începe cu R",
            "Radu Jude",
            "Andrei Pleșu",
        ),
    ],
)
def test_surface_rule_parser_is_literal_and_auditable(label, member, foreign):
    rule = critique_pack.parse_surface_rule(label)
    assert rule is not None
    assert critique_pack.matches_surface_rule(rule, member)
    assert not critique_pack.matches_surface_rule(rule, foreign)


def test_surface_rule_crossfit_is_a_pending_failure():
    groups = {
        "g1": ["p1", "p2", "p3", "p4"],
        "g2": ["x1", "x2", "x3", "x4"],
        "g3": ["y1", "y2", "y3", "y4"],
        "g4": ["z1", "z2", "z3", "z4"],
    }
    labels = {"g1": "Cuvinte care încep cu litera P"}
    displayed = {
        "p1": "Primar",
        "p2": "Prefect",
        "p3": "Port",
        "p4": "Parc",
        "x1": "Populație",
        **{node_id: node_id for node_id in groups["g2"][1:]},
        **{node_id: node_id for node_id in groups["g3"]},
        **{node_id: node_id for node_id in groups["g4"]},
    }
    node_types = {node_id: "concept" for node_id in displayed}
    findings = critique_pack.surface_rule_findings(
        groups, labels, displayed, node_types, approved=False
    )
    assert findings == [{
        "check": "surface_predicate_crossfit",
        "level": "FAIL",
        "detail": (
            'group "Cuvinte care încep cu litera P" also matches '
            "foreign tile(s): Populație"
        ),
    }]


@pytest.mark.parametrize(
    "label",
    [
        "Țin de viața la bloc",
        "Repere ale unei seri de film",
        "Apar în situația locuirii",
        "Practici și obiecte legate de Paște",
        "Programe sau măsuri publice cu impact direct",
        "Din lumea teatrului",
        "Concepte asociate cu un inventator",
    ],
)
def test_vague_predicate_wording_catches_association_bundle_labels(label):
    assert critique_pack.vague_predicate_wording(label) is not None


@pytest.mark.parametrize(
    "label",
    [
        "Romane publicate între cele două războaie",
        "Nume de familie care încep cu S",
        "Au câștigat titlul olimpic la canotaj",
    ],
)
def test_vague_predicate_wording_leaves_testable_labels_alone(label):
    assert critique_pack.vague_predicate_wording(label) is None


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
    assert import_candidates.candidate_import_status('fix') is None
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
    analyst_verdicts=None, verifier_verdicts=None,
):
    ids = list(verdicts) if batch_ids is None else list(batch_ids)
    count = len(verdicts)
    analyst_verdicts = analyst_verdicts or verdicts
    verifier_verdicts = verifier_verdicts or verdicts
    path.write_text(
        json.dumps({
            'game': game,
            'mode': 'gate',
            'batch': {'version': 2, 'mode': 'gate', 'input_ids': sorted(ids)},
            'verdicts': verdicts,
            'perItem': [
                {
                    'id': iid, 'game': game, 'final': verdict,
                    'proposed': analyst_verdicts[iid],
                    'analyst': analyst_verdicts[iid],
                    'verifier': verifier_verdicts[iid],
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
    monkeypatch.setattr(
        apply_rereview, 'critique_promotions', lambda _ids, _rejects: 1
    )
    with pytest.raises(SystemExit, match='promotion blocked'):
        apply_rereview.main(['apply_rereview.py', '--dir', str(tmp_path)])
    assert all(path.read_bytes() == blob for path, blob in originals.items())


@pytest.mark.parametrize("validator_mode", ["return", "raise"])
def test_apply_rereview_restores_both_mirrors_when_validation_fails(
    tmp_path,
    monkeypatch,
    validator_mode,
):
    original = critique_pack.PACKAGE_PACK.read_bytes()
    copies = (tmp_path / "package-pack.json", tmp_path / "tests-pack.json")
    for copy in copies:
        copy.write_bytes(original)
    pack = json.loads(original.decode("utf-8"))
    pending = next(item for item in pack["conexiuni"] if item["status"] == "pending")
    _write_gate_artifact(
        tmp_path / "conexiuni_verdicts.json",
        "conexiuni",
        {pending["id"]: "promote"},
    )

    monkeypatch.setattr(apply_rereview, "PACK_COPIES", copies)
    monkeypatch.setattr(
        apply_rereview,
        "current_review_bindings",
        lambda _ids: {pending["id"]: "sha256:" + ("a" * 64)},
    )
    monkeypatch.setattr(
        apply_rereview,
        "critique_promotions",
        lambda _ids, _rejects: 0,
    )
    if validator_mode == "return":
        monkeypatch.setattr(
            apply_rereview.validate_games_pack,
            "main",
            lambda _argv: 1,
        )
        expected_exception = SystemExit
    else:
        def raise_validator_error(_argv):
            raise RuntimeError("injected validator exception")

        monkeypatch.setattr(
            apply_rereview.validate_games_pack,
            "main",
            raise_validator_error,
        )
        expected_exception = RuntimeError

    with pytest.raises(expected_exception):
        apply_rereview.main(["apply_rereview.py", "--dir", str(tmp_path)])

    assert [copy.read_bytes() for copy in copies] == [original, original]


def test_apply_rereview_restores_first_mirror_after_second_write_fails(
    tmp_path,
    monkeypatch,
):
    original = critique_pack.PACKAGE_PACK.read_bytes()
    copies = (tmp_path / "package-pack.json", tmp_path / "tests-pack.json")
    for copy in copies:
        copy.write_bytes(original)
    pack = json.loads(original.decode("utf-8"))
    pending = next(item for item in pack["conexiuni"] if item["status"] == "pending")
    _write_gate_artifact(
        tmp_path / "conexiuni_verdicts.json",
        "conexiuni",
        {pending["id"]: "promote"},
    )

    monkeypatch.setattr(apply_rereview, "PACK_COPIES", copies)
    monkeypatch.setattr(
        apply_rereview,
        "current_review_bindings",
        lambda _ids: {pending["id"]: "sha256:" + ("a" * 64)},
    )
    monkeypatch.setattr(
        apply_rereview,
        "critique_promotions",
        lambda _ids, _rejects: 0,
    )
    monkeypatch.setattr(
        apply_rereview.validate_games_pack,
        "main",
        lambda _argv: pytest.fail("validator must not run after a write failure"),
    )
    real_atomic_write = apply_rereview.atomic_write
    writes = 0

    def fail_second_write(path, blob):
        nonlocal writes
        writes += 1
        if writes == 2:
            raise OSError("injected second mirror failure")
        real_atomic_write(path, blob)

    monkeypatch.setattr(apply_rereview, "atomic_write", fail_second_write)
    with pytest.raises(OSError, match="injected second mirror failure"):
        apply_rereview.main(["apply_rereview.py", "--dir", str(tmp_path)])

    assert [copy.read_bytes() for copy in copies] == [original, original]


@pytest.mark.parametrize("validator_result", [0, 1])
def test_apply_rereview_records_rejections_transactionally(
    tmp_path,
    monkeypatch,
    validator_result,
):
    original = critique_pack.PACKAGE_PACK.read_bytes()
    copies = (tmp_path / "package-pack.json", tmp_path / "tests-pack.json")
    for copy in copies:
        copy.write_bytes(original)
    pack = json.loads(original.decode("utf-8"))
    pending = next(
        item for item in pack["conexiuni"] if item["status"] == "pending"
    )
    binding = "sha256:" + ("a" * 64)
    _write_gate_artifact(
        tmp_path / "conexiuni_verdicts.json",
        "conexiuni",
        {pending["id"]: "reject"},
        review_binding=binding,
    )
    tombstone_path = tmp_path / "tombstones.json"
    empty_tombstones = (
        json.dumps({
            "schema_version": 1,
            "meta": {
                "note": "test",
                "count": 0,
                "group_count": 0,
                "initial_seed_gate_sha256": "0" * 64,
            },
            "items": {},
        }) + "\n"
    ).encode()
    tombstone_path.write_bytes(empty_tombstones)

    monkeypatch.setattr(apply_rereview, "PACK_COPIES", copies)
    monkeypatch.setattr(
        apply_rereview.critique_pack,
        "REJECTION_TOMBSTONES",
        tombstone_path,
    )
    monkeypatch.setattr(
        apply_rereview,
        "current_review_bindings",
        lambda _ids: {pending["id"]: binding},
    )
    monkeypatch.setattr(
        apply_rereview,
        "critique_promotions",
        lambda _ids, _rejects: 0,
    )
    monkeypatch.setattr(
        apply_rereview.validate_games_pack,
        "main",
        lambda _argv: validator_result,
    )

    if validator_result:
        with pytest.raises(SystemExit, match="pack validation failed"):
            apply_rereview.main(
                ["apply_rereview.py", "--dir", str(tmp_path)]
            )
        assert [copy.read_bytes() for copy in copies] == [original, original]
        assert tombstone_path.read_bytes() == empty_tombstones
        return

    assert apply_rereview.main(
        ["apply_rereview.py", "--dir", str(tmp_path)]
    ) == 0
    for copy in copies:
        updated_pack = json.loads(copy.read_text())
        assert pending["id"] not in {
            item["id"] for item in updated_pack["conexiuni"]
        }
    tombstones = json.loads(tombstone_path.read_text())
    entry = tombstones["items"][pending["id"]]
    assert entry["record_sha256"] == critique_pack.canonical_json_sha256(pending)
    assert entry["groups_sha256"] == critique_pack.canonical_json_sha256(
        pending["groups"]
    )
    assert entry["review_binding"] == binding
    assert entry["source_gate_sha256"] == hashlib.sha256(
        (tmp_path / "conexiuni_verdicts.json").read_bytes()
    ).hexdigest()
    assert entry["groups"] == pending["groups"]


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
        lambda _ids, _rejects: pytest.fail(
            'critique must not run for an unverified artifact'
        ),
    )
    with pytest.raises(SystemExit, match='not fully verified'):
        apply_rereview.main(['apply_rereview.py', '--dir', str(tmp_path)])


@pytest.mark.parametrize(
    ("analyst", "verifier", "unsafe_final"),
    [
        ("reject", "promote", "promote"),
        ("keep", "promote", "promote"),
        ("promote", "keep", "promote"),
        ("promote", "reject", "promote"),
    ],
)
def test_apply_rereview_rejects_non_unanimous_promotion(
    tmp_path, monkeypatch, analyst, verifier, unsafe_final,
):
    pack = json.loads(critique_pack.PACKAGE_PACK.read_text(encoding="utf-8"))
    pending = next(item for item in pack["conexiuni"] if item["status"] == "pending")
    _write_gate_artifact(
        tmp_path / "conexiuni_verdicts.json",
        "conexiuni",
        {pending["id"]: unsafe_final},
        analyst_verdicts={pending["id"]: analyst},
        verifier_verdicts={pending["id"]: verifier},
    )
    monkeypatch.setattr(
        apply_rereview,
        "critique_promotions",
        lambda _ids, _rejects: pytest.fail(
            "non-unanimous promotion must fail before deterministic critique"
        ),
    )
    with pytest.raises(SystemExit, match="not fully verified"):
        apply_rereview.main(["apply_rereview.py", "--dir", str(tmp_path)])


def test_apply_rereview_accepts_conservative_disagreement_rejection(tmp_path):
    pack = json.loads(critique_pack.PACKAGE_PACK.read_text(encoding="utf-8"))
    pending = next(item for item in pack["conexiuni"] if item["status"] == "pending")
    path = tmp_path / "conexiuni_verdicts.json"
    _write_gate_artifact(
        path,
        "conexiuni",
        {pending["id"]: "reject"},
        analyst_verdicts={pending["id"]: "reject"},
        verifier_verdicts={pending["id"]: "promote"},
    )
    verdicts, batch, bindings = apply_rereview.validated_artifact(
        json.loads(path.read_text(encoding="utf-8")),
        "conexiuni",
        path,
    )
    assert verdicts == {pending["id"]: "reject"}
    assert batch["input_ids"] == [pending["id"]]
    assert bindings[pending["id"]] == "sha256:" + ("a" * 64)


def test_tracked_v43_gate_satisfies_conservative_two_reviewer_contract():
    path = (
        _REPO_ROOT
        / "docs"
        / "reviews"
        / "v43-final-gate"
        / "conexiuni_verdicts.json"
    )
    verdicts, batch, bindings = apply_rereview.validated_artifact(
        json.loads(path.read_text(encoding="utf-8")),
        "conexiuni",
        path,
    )
    assert verdicts == {
        "cx_personalitati_360": "reject",
        "cx_sport_361": "reject",
    }
    assert set(batch["input_ids"]) == set(verdicts)
    assert set(bindings) == set(verdicts)


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
        lambda _ids, _rejects: pytest.fail(
            'stale artifacts must fail before deterministic critique'
        ),
    )
    with pytest.raises(SystemExit, match='stale gate artifact'):
        apply_rereview.main(['apply_rereview.py', '--dir', str(tmp_path)])


# --------------------------------------------------------------------- integration
@pytest.fixture(scope="module")
def loaded():
    return critique_pack.load_all(critique_pack.PACKAGE_PACK, critique_pack.PACKAGE_KG)


def test_real_rejection_tombstones_are_valid_and_not_runtime_boards(loaded):
    pack, _, _, _ = loaded
    tombstones = critique_pack.load_rejection_tombstones()
    runtime_ids = {item["id"] for item in pack["conexiuni"]}
    assert len(tombstones) == 43
    assert sum(len(item["groups"]) for item in tombstones) == 172
    assert {"cx_personalitati_360", "cx_sport_361"} <= {
        item["id"] for item in tombstones
    }
    assert not ({item["id"] for item in tombstones} & runtime_ids)


def test_pending_lant_runtime_failures_are_critique_gate_failures(loaded):
    pack, svc, strong, regions = loaded
    valid = next(item for item in pack["lant"] if item["id"] == "lt_viata_de_roman_211")
    invalid = {
        **valid,
        "id": "lt_pending_invalid",
        "category": "arta_cultura",
        "difficulty": "greu",
        "start": "n_gas_masa_craciun",
        "target": "n_masa_tacerii",
        "optimal": 5,
    }
    pack = {**pack, "lant": [*pack["lant"], invalid]}

    items, _, selected = critique_pack.run(
        pack,
        svc,
        strong,
        regions,
        ["lant"],
        {"pending"},
        {invalid["id"], valid["id"]},
    )

    assert {record["id"] for _, record, _ in selected} == {
        invalid["id"],
        valid["id"],
    }
    assert {
        finding["detail"]
        for finding in items[invalid["id"]]["findings"]
        if finding["check"] == "lant_playability"
    } == {
        "only 1 valid first-hop choice(s) (< 2)",
        "narrowest shortest-path layer has width 1 (< 2)",
    }
    assert not any(
        finding["check"] == "lant_playability"
        for finding in items.get(valid["id"], {}).get("findings", [])
    )


def test_rejection_tombstone_group_mutation_fails_integrity_check():
    data = json.loads(critique_pack.REJECTION_TOMBSTONES.read_text(encoding="utf-8"))
    item_id = next(iter(data["items"]))
    data["items"][item_id]["groups"]["g1"][0] = "n_tampered"
    with pytest.raises(ValueError, match="groups digest drift"):
        critique_pack.validate_rejection_tombstones(data)


def test_four_type_board_shortcut_blocks_pending_but_only_warns_on_stock(loaded):
    pack, svc, strong, _ = loaded
    by_type: dict[str, list[str]] = {}
    for rec in pack["conexiuni"]:
        for members in rec["groups"].values():
            for node_id in members:
                node_type = svc.node(node_id).node_type
                bucket = by_type.setdefault(node_type, [])
                if node_id not in bucket:
                    bucket.append(node_id)
    chosen = [
        members[:4]
        for _, members in sorted(by_type.items())
        if len(members) >= 4
    ][:4]
    assert len(chosen) == 4
    base = deepcopy(pack["conexiuni"][0])
    base["groups"] = {
        f"g{index}": members for index, members in enumerate(chosen, 1)
    }
    base["group_labels"] = {
        f"g{index}": f"Predicatul {index}" for index in range(1, 5)
    }
    base["order"] = [node_id for members in chosen for node_id in members]

    for status, expected in (("pending", "FAIL"), ("approved", "WARN")):
        findings = critique_pack.check_conexiuni(
            {**base, "status": status}, svc, strong, {}
        )
        shortcut = [
            finding
            for finding in findings
            if finding["check"] == "board_type_shortcut"
        ]
        assert [finding["level"] for finding in shortcut] == [expected]


def test_vague_predicate_wording_blocks_pending_but_only_warns_on_stock(loaded):
    pack, svc, strong, _ = loaded
    base = deepcopy(pack["conexiuni"][0])
    group_id = sorted(base["groups"])[0]
    base["group_labels"][group_id] = "Repere ale unei teme"
    for status, expected in (("pending", "FAIL"), ("approved", "WARN")):
        findings = critique_pack.check_conexiuni(
            {**base, "status": status}, svc, strong, {}
        )
        wording = [
            finding
            for finding in findings
            if finding["check"] == "vague_predicate_wording"
        ]
        assert [finding["level"] for finding in wording] == [expected]


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


def test_default_status_filter_does_not_expand_approved_review_to_pending(loaded):
    pack, svc, strong, regions = loaded
    base = pack["conexiuni"][0]
    approved = {**base, "id": "cx_scope_approved", "status": "approved"}
    pending = {**base, "id": "cx_scope_pending", "status": "pending"}
    mini_pack = {
        "meta": {},
        "conexiuni": [approved, pending],
        "contexto": [],
        "lant": [],
        "alchimie": [],
    }

    _, _, selected = critique_pack.run(
        mini_pack,
        svc,
        strong,
        regions,
        ["conexiuni"],
        {"approved", "pending"},
        {approved["id"]},
    )

    findings = selected[0][2]
    assert not any(
        finding["check"] in {"duplicate_groups", "board_reskin"}
        for finding in findings
    )


def test_prospective_promotion_gate_keeps_same_batch_rejects_as_novelty_debt(
    loaded, monkeypatch
):
    pack, svc, strong, regions = loaded
    base = next(
        {**rec, "status": "pending"}
        for rec in pack["conexiuni"]
        if not any(
            finding["level"] == "FAIL"
            for finding in critique_pack.check_conexiuni(
                {**rec, "status": "pending"}, svc, strong, {}
            )
        )
    )
    promoted = {**base, "id": "cx_prospective_promote"}
    duplicate = {**base, "id": "cx_prospective_duplicate"}
    mini_pack = {
        "meta": {},
        "conexiuni": [promoted, duplicate],
        "contexto": [],
        "lant": [],
        "alchimie": [],
    }
    monkeypatch.setattr(
        apply_rereview.critique_pack,
        "load_all",
        lambda *_args: (deepcopy(mini_pack), svc, strong, regions),
    )

    assert apply_rereview.critique_promotions(
        {promoted["id"]}, {duplicate["id"]}
    ) == 1
    assert apply_rereview.critique_promotions({promoted["id"]}, set()) == 1
    assert apply_rereview.critique_promotions(
        {promoted["id"], duplicate["id"]}, set()
    ) == 1


def test_rejection_tombstones_block_future_exact_and_board_reskins(
    loaded, tmp_path, monkeypatch
):
    pack, svc, strong, regions = loaded
    base = deepcopy(pack["conexiuni"][0])
    base["id"] = "cx_rejected_source"
    base["status"] = "pending"
    binding = "sha256:" + ("a" * 64)
    empty = {
        "schema_version": 1,
        "meta": {
            "note": "test",
            "count": 0,
            "group_count": 0,
            "initial_seed_gate_sha256": "0" * 64,
        },
        "items": {},
    }
    path = tmp_path / "tombstones.json"
    path.write_bytes(
        apply_rereview.updated_rejection_tombstones(
            (json.dumps(empty) + "\n").encode(),
            [base],
            {base["id"]: binding},
            {base["id"]: "b" * 64},
        )
    )
    monkeypatch.setattr(critique_pack, "REJECTION_TOMBSTONES", path)

    candidate = {**base, "id": "cx_future_candidate"}
    mini_pack = {
        "meta": {},
        "conexiuni": [candidate],
        "contexto": [],
        "lant": [],
        "alchimie": [],
    }
    _, _, selected = critique_pack.run(
        mini_pack,
        svc,
        strong,
        regions,
        ["conexiuni"],
        {"pending"},
        {candidate["id"]},
    )
    findings = selected[0][2]
    assert any(
        finding["check"] == "duplicate_groups"
        and "rejected:cx_rejected_source" in finding["detail"]
        for finding in findings
    )
    assert any(
        finding["check"] == "board_reskin"
        and "rejected:cx_rejected_source" in finding["detail"]
        for finding in findings
    )

    replacement = next(
        node_id
        for rec in pack["conexiuni"]
        for members in rec["groups"].values()
        for node_id in members
        if node_id not in {
            tile for members in base["groups"].values() for tile in members
        }
    )
    near_candidate = deepcopy(candidate)
    near_candidate["id"] = "cx_future_near_candidate"
    first_group = sorted(near_candidate["groups"])[0]
    near_candidate["groups"][first_group][0] = replacement
    near_candidate["order"] = [
        node_id
        for members in near_candidate["groups"].values()
        for node_id in members
    ]
    mini_pack["conexiuni"] = [near_candidate]
    _, _, selected = critique_pack.run(
        mini_pack,
        svc,
        strong,
        regions,
        ["conexiuni"],
        {"pending"},
        {near_candidate["id"]},
    )
    near_findings = selected[0][2]
    assert any(
        finding["check"] == "duplicate_groups"
        and "near-duplicate" in finding["detail"]
        and "rejected:cx_rejected_source" in finding["detail"]
        for finding in near_findings
    )


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
        other_id = second['id'] if iid == first['id'] else first['id']
        duplicate_findings = [
            finding for finding in items[iid]['findings']
            if finding['check'] == 'duplicate_groups'
        ]
        assert duplicate_findings
        assert any(finding['level'] == 'FAIL' for finding in duplicate_findings)
        assert any(other_id in finding['detail'] for finding in duplicate_findings)


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
    findings = items[candidate['id']]['findings']
    assert any(
        finding['check'] == 'member_overuse' and finding['level'] == 'FAIL'
        for finding in findings
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
    assert "analyst === 'promote' && verifier === 'promote'" in workflow
    assert "return `${gateVerdict(analyst, verifier)}-without-unanimity`" in workflow
    assert 'analyst, verifier, policy' in workflow
    assert 'return { mode: MODE, batch, verdicts, perItem, coverage, artifacts }' in workflow


def test_authored_workflow_censuses_full_inventory_for_reskins():
    workflow = (
        _REPO_ROOT / ".claude" / "workflows" / "verify-authored-content.js"
    ).read_text(encoding="utf-8")
    assert "including reserves and pending stock" in workflow
    assert "conexiuni_rejection_tombstones.json" in workflow
    assert "exact or 3-of-4 quads plus >=8/16 whole-board overlap" in workflow
    assert "Treat those freshness matches as drop" in workflow
    assert "candidate_sha256" in workflow


def test_audit_and_gate_workflows_retain_rejected_pattern_evidence():
    audit = (
        _REPO_ROOT / ".claude" / "workflows" / "game-audit-recon.js"
    ).read_text(encoding="utf-8")
    gate = (
        _REPO_ROOT / ".claude" / "workflows" / "critique-games.js"
    ).read_text(encoding="utf-8")
    assert "demotion/rejection artifact" in audit
    assert "rejection tombstones" in audit
    assert "conexiuni_rejection_tombstones.json" in gate
    assert "four-type sorting" in gate


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
    assert dups and dups[0]["level"] == "FAIL"
    assert "near-duplicate" in dups[0]["detail"]


def test_pending_conexiuni_label_self_leak_is_a_fail(loaded):
    pack, svc, strong, _ = loaded
    rec = {**pack["conexiuni"][0], "status": "pending"}
    group = sorted(rec["groups"])[0]
    member = critique_pack.node_brief(svc, rec["groups"][group][0])["label"]
    rec = {
        **rec,
        "group_labels": {**rec["group_labels"], group: f"Din lumea {member}"},
    }

    findings = critique_pack.check_conexiuni(rec, svc, strong, {})

    leaks = [f for f in findings if f["check"] == "label_self_leak"]
    assert leaks and leaks[0]["level"] == "FAIL"
    assert member in leaks[0]["detail"]


@pytest.mark.parametrize(
    ("label", "member"),
    [
        ("Posturi ale T.V.R.", "TVR"),
        ("Posturi ale TVR", "T.V.R."),
        ("Scrieri de MIHAI EMINESCU", "Mihai Eminescu"),
        ("Personaje din Ion-Luca Caragiale", "Ion Luca Caragiale"),
    ],
)
def test_label_leak_normalization_catches_real_answer_forms(label, member):
    assert critique_pack.label_leaks_member(label, member)


@pytest.mark.parametrize(
    ("label", "member"),
    [
        ("Posturi TV", "TV"),
        ("Festival teatral", "Teatru"),
        ("Opere de Marin Preda", "Marina"),
        ("Formula 1", "Formula 10"),
    ],
)
def test_label_leak_normalization_preserves_noise_and_word_boundaries(label, member):
    assert not critique_pack.label_leaks_member(label, member)


def test_pending_conexiuni_mirrored_groups_are_a_fail(loaded):
    pack, svc, strong, _ = loaded
    rec = next(
        {**item, "status": "pending"}
        for item in pack["conexiuni"]
        if any(
            finding["check"] == "mirrored_groups"
            for finding in critique_pack.check_conexiuni(item, svc, strong, {})
        )
    )

    findings = critique_pack.check_conexiuni(rec, svc, strong, {})

    mirrors = [f for f in findings if f["check"] == "mirrored_groups"]
    assert mirrors and all(f["level"] == "FAIL" for f in mirrors)


def test_pending_conexiuni_half_board_reskin_is_a_fail(loaded):
    pack, svc, strong, _ = loaded
    rec = {**pack["conexiuni"][0], "status": "pending"}
    board = frozenset(nid for group in rec["groups"].values() for nid in group)

    findings = critique_pack.check_conexiuni(
        rec,
        svc,
        strong,
        {},
        {"cx_other_board": board},
    )

    reskins = [f for f in findings if f["check"] == "board_reskin"]
    assert reskins and reskins[0]["level"] == "FAIL"
    assert "cx_other_board (16)" in reskins[0]["detail"]


def test_approved_stock_freshness_checks_remain_warnings(loaded):
    pack, svc, strong, _ = loaded
    rec = pack["conexiuni"][0]
    group = sorted(rec["groups"])[0]
    member = critique_pack.node_brief(svc, rec["groups"][group][0])["label"]
    rec = {
        **rec,
        "group_labels": {**rec["group_labels"], group: f"Din lumea {member}"},
    }
    quad = frozenset(rec["groups"][group])
    board = frozenset(nid for ids in rec["groups"].values() for nid in ids)

    findings = critique_pack.check_conexiuni(
        rec,
        svc,
        strong,
        {quad: ["cx_other_board"]},
        {"cx_other_board": board},
    )

    freshness = [
        finding
        for finding in findings
        if finding["check"] in {
            "duplicate_groups",
            "board_reskin",
            "label_self_leak",
        }
    ]
    assert {finding["check"] for finding in freshness} == {
        "duplicate_groups",
        "board_reskin",
        "label_self_leak",
    }
    assert all(finding["level"] == "WARN" for finding in freshness)


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
