"""Content progress is distinct from metadata churn, promotions, and word forms."""

from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import report_content_delta as delta  # noqa: E402


def documents() -> dict:
    return {
        "kg": {
            "meta": {"build_version": "before"},
            "kg_nodes": [
                {"id": "nut", "label_ro": "Nucă", "aliases": ["nucile"]},
                {"id": "cake", "label_ro": "Cozonac", "aliases": []},
            ],
            "kg_edges": [{"id": "e1", "src_id": "nut", "dst_id": "cake"}],
            "kg_puzzles": [{"id": "pz1", "start_id": "nut", "target_id": "cake"}],
        },
        "pack": {"contexto": [
            {"id": "ct1", "target": "cake", "status": "pending"},
            {"id": "ct2", "target": "nut", "status": "approved"},
        ]},
        "derived": {"boards": [{"id": "vi1", "game": "intrusul", "payload": [1, 2]}]},
        "quick": None,
        "rankings": {"boards": [
            {"id": "ct1", "game": "contexto", "status": "pending", "pilot_eligible": False},
            {"id": "ct2", "game": "contexto", "status": "approved", "pilot_eligible": True},
        ]},
    }


def test_reports_growth_removals_and_promotions_separately():
    before = documents()
    after = copy.deepcopy(before)
    after["kg"]["kg_nodes"].append({"id": "jam", "label_ro": "Gem", "aliases": ["gemul"]})
    after["kg"]["kg_nodes"][0]["aliases"] = ["nucilor"]
    after["kg"]["kg_edges"][0]["dst_id"] = "jam"
    after["kg"]["kg_edges"].append({"id": "e2", "src_id": "jam", "dst_id": "cake"})
    after["kg"]["kg_puzzles"] = []
    after["pack"]["contexto"][0]["status"] = "approved"
    after["pack"]["contexto"][1]["status"] = "pending"
    after["pack"]["contexto"].append({"id": "ct3", "target": "jam", "status": "approved"})
    for row in after["rankings"]["boards"]:
        row["status"] = "approved" if row["id"] == "ct1" else "pending"
        row["pilot_eligible"] = row["id"] == "ct1"
    after["rankings"]["boards"].append(
        {"id": "ct3", "game": "contexto", "status": "approved", "pilot_eligible": False}
    )
    after["derived"]["boards"][0]["game"] = "perechi"
    report = delta.compare(delta.inventory(before), delta.inventory(after))

    assert report["concepts"]["added_ids"] == ["jam"]
    assert report["concepts"]["changed_count"] == 0
    assert report["forms"]["added_ids"] == [("jam", "gemul"), ("nut", "nucilor")]
    assert report["forms"]["removed_ids"] == [("nut", "nucile")]
    assert report["connections"]["changed_ids"] == ["e1"]
    assert report["connections"]["added_ids"] == ["e2"]
    assert report["puzzles"]["removed_ids"] == ["pz1"]
    assert not report["puzzles"]["all_baseline_ids_retained"]
    contexto = report["pack"]["contexto"]
    assert contexto["records"]["added_ids"] == ["ct3"]
    assert contexto["records"]["changed_ids"] == ["ct1", "ct2"]
    assert contexto["approved"]["added_ids"] == ["ct1", "ct3"]
    assert contexto["approved"]["removed_ids"] == ["ct2"]
    assert contexto["declared_ranked_eligible"]["added_ids"] == ["ct1"]
    assert contexto["declared_ranked_eligible"]["removed_ids"] == ["ct2"]
    assert report["derived"]["intrusul"]["removed_ids"] == ["vi1"]
    assert report["derived"]["perechi"]["added_ids"] == ["vi1"]


def test_reordering_and_build_metadata_do_not_create_content():
    before = documents()
    after = copy.deepcopy(before)
    after["kg"]["meta"]["build_version"] = "after"
    after["kg"]["kg_nodes"].reverse()
    report = delta.compare(delta.inventory(before), delta.inventory(after))
    assert report["concepts"]["unchanged_count"] == 2
    assert report["concepts"]["all_baseline_records_unchanged"]
    assert report["connections"]["unchanged_count"] == 1
    assert report["pack"]["contexto"]["records"]["unchanged_count"] == 2
    assert report["derived"]["intrusul"]["unchanged_count"] == 1


def test_missing_historical_sidecars_are_not_false_zero_eligibility():
    before = documents()
    before["rankings"] = None
    before["derived"] = None
    report = delta.compare(delta.inventory(before), delta.inventory(documents()))
    assert report["pack"]["contexto"]["declared_ranked_eligible"] is None
    assert report["derived"]["intrusul"]["added_ids"] == ["vi1"]


def test_authored_supplement_counts_as_growth_without_changing_frozen_boards():
    before = documents()
    after = copy.deepcopy(before)
    after["quick"] = {"boards": [
        {"id": "iq1", "game": "intrusul", "payload": [3, 4]},
        {"id": "pq1", "game": "perechi", "payload": [5, 6]},
    ]}
    report = delta.compare(delta.inventory(before), delta.inventory(after))
    assert report["derived"]["intrusul"]["added_ids"] == ["iq1"]
    assert report["derived"]["intrusul"]["unchanged_count"] == 1
    assert report["derived"]["perechi"]["added_ids"] == ["pq1"]
    after["quick"]["boards"].append(after["derived"]["boards"][0])
    with pytest.raises(ValueError, match="collide with the frozen catalog"):
        delta.inventory(after)


@pytest.mark.parametrize("invalid", ["duplicate_node", "duplicate_form", "stale_rank_status"])
def test_ambiguous_inventories_fail_instead_of_undercounting(invalid):
    docs = documents()
    if invalid == "duplicate_node":
        docs["kg"]["kg_nodes"].append(docs["kg"]["kg_nodes"][0])
    elif invalid == "duplicate_form":
        docs["kg"]["kg_nodes"][0]["aliases"].append("nucile")
    else:
        docs["rankings"]["boards"][0]["status"] = "approved"
    with pytest.raises(ValueError):
        delta.inventory(docs)


def test_cli_reads_baseline_git_content_and_uncommitted_workspace(tmp_path, capsys):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    docs = documents()
    for key, path in delta.FILES.items():
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(docs[key]), encoding="utf-8")
    subprocess.run(["git", "-C", str(tmp_path), "add", "."], check=True)
    subprocess.run(
        ["git", "-C", str(tmp_path), "-c", "user.name=Test", "-c", "user.email=test@example.test",
         "-c", "commit.gpgsign=false", "commit", "-qm", "baseline"], check=True,
    )
    docs["kg"]["kg_nodes"][0]["aliases"].append("nuci")
    (tmp_path / delta.FILES["kg"]).write_text(json.dumps(docs["kg"]), encoding="utf-8")

    assert delta.main(["--repo", str(tmp_path), "--baseline", "HEAD", "--json"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["forms"]["added_ids"] == [["nut", "nuci"]]
    assert report["concepts"]["changed_count"] == 0
    assert report["synonyms"]["count"] is None
    assert report["campaign"] is None
    assert "serving export missing" in report["campaign_unavailable"]
    assert len(report["baseline_commit"]) == 40
    assert delta.main(["--repo", str(tmp_path), "--text"]) == 0
    assert "forms: 1 -> 2; +1 -0" in capsys.readouterr().out
    assert delta.main(["--repo", str(tmp_path), "--head", "HEAD"]) == 0
    committed = json.loads(capsys.readouterr().out)
    assert committed["comparison"] == "commits"
    assert committed["head_commit"] == report["baseline_commit"]
    assert committed["forms"]["added_count"] == 0
    assert delta.main(["--repo", str(tmp_path), "--baseline", "missing-ref"]) == 2
    output = capsys.readouterr()
    assert not output.out
    assert "Content delta failed" in output.err


def test_option_like_baseline_is_rejected_before_git(tmp_path, capsys):
    assert delta.main(["--repo", str(tmp_path), "--baseline=--all"]) == 2
    assert "not an option" in capsys.readouterr().err


def serving_bundle(docs):
    return {
        "schema_version": 2,
        "nodes": [
            {"node_type": "concept", **node} for node in docs["kg"]["kg_nodes"]
        ],
        "edges": [],
        "pack_ranked": True,
        "pack_items": [],
        "boards": [],
        "normalization_map": {"I": "i", "N": "n", "Î": "i", "Ș": "s", "ș": "s"},
        "accent_normalization_map": {"ș": "s\u0326"},
        "normalized_index": {"nucile": "nut"},
        "discovery_world": {"recipes": []},
        "recipe_extensions": {"boards": []},
    }


def board(game, key, payload, eligible=True):
    if game in delta.PACK_GAMES:
        return {"game": game, "id": key, "status": "approved", "pilot_eligible": eligible,
                "payload": payload}
    return {"game": game, "catalog_id": key, "payload": payload, "category": "limba",
            "source_id": key, "overall_score": 55, "starter_safe": True}


def test_campaign_splits_target_forms_and_links_from_other_installed_additions():
    docs = documents()
    docs["derived"] = None
    before = serving_bundle(docs)
    before["nodes"].append({
        "id": "elder", "node_type": "person", "label_ro": "Bunic", "aliases": [],
    })
    before["edges"] = [
        {"src_id": "nut", "dst_id": "cake", "relation": "recipe", "is_distractor": False},
    ]
    before["discovery_world"]["recipes"] = [{"pair": ["nut", "cake"], "result": "cake"}]
    after = copy.deepcopy(before)
    after["nodes"][0]["aliases"] = ["Nucile", "nucilor", "nucă", "paște"]
    before["normalized_index"]["nuca veche"] = "nut"
    after["nodes"][0]["aliases"].append("nuca veche")
    after["normalized_index"]["nuca veche"] = "nut"
    after["nodes"][2]["aliases"].append("bunicul")
    after["nodes"].extend([
        {"id": "jam", "node_type": "concept", "label_ro": "Gem", "aliases": ["gemul"]},
        {"id": "juice", "node_type": "concept", "label_ro": "Suc", "aliases": []},
        {"id": "person", "node_type": "person", "label_ro": "Ion Creangă", "aliases": []},
        {"id": "place", "node_type": "concept", "label_ro": "Iași", "aliases": ["Iașului"]},
        {"id": "event", "node_type": "event", "label_ro": "Serbarea școlară", "aliases": []},
        {"id": "nut_rekey", "node_type": "concept", "label_ro": "Nucă", "aliases": ["nuco"]},
    ])
    after["normalized_index"].update(
        nucilor="nut", gemul="jam", bunicul="elder", iasului="place", nuco="nut_rekey",
        **{"nucă": "nut", "paste": "nut"},
    )
    after["edges"][0].update(src_id="cake", dst_id="nut", label_ro="reworded", bidirectional=True)
    after["edges"].extend([
        {"src_id": "jam", "dst_id": "cake", "relation": "ingredient", "is_distractor": False},
        {"src_id": "cake", "dst_id": "jam", "relation": "ingredient", "is_distractor": False},
        {"src_id": "jam", "dst_id": "juice", "relation": "ingredient", "is_distractor": False},
        {"src_id": "jam", "dst_id": "place", "relation": "part_of", "is_distractor": False},
        {"src_id": "cake", "dst_id": "nut", "relation": "ingredient", "is_distractor": False},
        {"src_id": "elder", "dst_id": "place", "relation": "part_of", "is_distractor": False},
        {"src_id": "nut", "dst_id": "nut_rekey", "relation": "kind_of", "is_distractor": False},
        {"src_id": "jam", "dst_id": "nut", "relation": "decoy", "is_distractor": True},
    ])
    after["discovery_world"]["recipes"].append({"pair": ["cake", "nut"], "result": "cake"})
    after["discovery_world"]["recipes"].append({"pair": ["cake", "nut"], "result": "jam"})
    after["recipe_extensions"]["boards"].append(
        {"id": "not_selectable", "additions": [{"pair": ["cake", "nut"], "result": "nut"}]},
    )

    report = delta.campaign_delta(before, after, delta.inventory(docs), {"place"})
    assert [row["id"] for row in report["new_words"]["examples"]] == ["jam", "juice"]
    assert [row["id"] for row in report["new_names"]["examples"]] == ["place"]
    assert [row["id"] for row in report["unclassified_new_entities"]["examples"]] == [
        "event", "nut_rekey", "person",
    ]
    assert [row["form"] for row in report["new_forms"]["examples"]] == ["nucilor"]
    assert [row["form"] for row in report["new_word_forms"]["examples"]] == ["gemul"]
    assert [row["form"] for row in report["other_new_forms"]["examples"]] == [
        "bunicul", "nuco", "Iașului",
    ]
    assert report["all_new_forms"]["count"] == 5
    assert [row["form"] for row in report["all_new_forms"]["examples"]] == [
        "bunicul", "gemul", "nucilor", "nuco", "Iașului",
    ]
    assert report["new_links"]["count"] == 3
    assert [row["node_ids"] for row in report["new_links"]["examples"]] == [
        ["cake", "jam"], ["jam", "juice"], ["jam", "place"],
    ]
    assert report["links_between_existing_words"]["examples"] == [
        {"kind": "kg", "node_ids": ["cake", "nut"], "relation": "ingredient"},
    ]
    assert [row["node_ids"] for row in report["other_new_kg_links"]["examples"]] == [
        ["elder", "place"], ["nut", "nut_rekey"],
    ]
    assert report["all_new_links"]["count"] == 7
    assert report["new_links_by_kind"]["kg"]["count"] == 6
    assert report["all_new_links"]["examples"] == report["new_links_by_kind"]["kg"]["examples"]
    assert report["new_links_by_kind"]["alchimie_recipe"]["examples"] == [
        {"kind": "alchimie_recipe", "pair": ["cake", "nut"], "result": "jam"},
    ]


def test_campaign_separates_new_boards_from_first_exposures():
    docs = documents()
    docs["derived"] = None
    old_nodes = docs["kg"]["kg_nodes"]
    old_nodes.extend([
        {"id": key, "label_ro": key, "aliases": []} for key in ("butter", "pear", "salt")
    ])
    before = serving_bundle(docs)
    before["pack_items"] = [board("contexto", "ct2", {"target": "nut"})]
    after = copy.deepcopy(before)
    after["nodes"].append(
        {"id": "jam", "node_type": "concept", "label_ro": "Gem", "aliases": []},
    )
    after["pack_items"].extend([
        board("contexto", "ct1", {"target": "cake"}),  # promotion
        board("contexto", "ct_rekey", {"target": "cake"}),  # copies old pending target
        board("contexto", "ct_pending", {"target": "salt"}, eligible=False),
        board("contexto", "ct_fresh", {"target": "pear"}),
        board("contexto", "ct_fresh_duplicate", {"target": "pear"}),
        board("contexto", "ct_new_word", {"target": "jam"}),
        board("lant", "lt1", {"start": "nut", "target": "cake"}),
        board("conexiuni", "cx1", {"groups": {"g1": ["nut", "cake"], "g2": ["pear", "salt"]}}),
        board("alchimie", "al1", {"seeds": ["nut", "cake"], "target": "pear"}),
    ])
    after["boards"] = [
        board("intrusul", "vi1", {"members": ["nut", "cake", "salt"], "intruder": "pear"}),
        board("perechi", "vp1", {
            "pairs": [{"members": ["nut", "cake"]}, {"members": ["pear", "salt"]}],
        }),
    ]
    after["recipe_extensions"]["boards"].append(
        {"id": "al1", "additions": [{"pair": ["cake", "nut"], "result": "butter"}]},
    )

    report = delta.campaign_delta(before, after, delta.inventory(docs), set())
    assert set(report["new_boards"]) == set(delta.GAMES)
    boards = report["new_boards"]
    assert boards["contexto"]["examples"] == [{"id": "ct_fresh"}, {"id": "ct_new_word"}]
    assert all(boards[game]["count"] == 1 for game in delta.GAMES if game != "contexto")
    exposures = report["first_exposures"]
    assert [x["id"] for x in exposures["contexto"]["examples"]] == ["cake", "pear"]
    assert [x["id"] for x in exposures["lant"]["examples"]] == ["cake", "nut"]
    assert [x["id"] for x in exposures["alchimie"]["examples"]] == ["cake", "nut", "pear"]
    assert report["new_links_by_kind"]["alchimie_recipe"]["count"] == 1


def test_campaign_authored_reserve_and_rekeyed_quick_board_do_not_count():
    docs = documents()
    original = {"members": ["cake"], "intruder": "nut", "group_label": "Initial label"}
    docs["derived"]["boards"][0]["payload"] = original
    before = serving_bundle(docs)
    after = copy.deepcopy(before)
    after["boards"] = [
        board("intrusul", "vi1", original),
        board("intrusul", "vi2", {**original, "group_label": "New label"}),
    ]

    report = delta.campaign_delta(before, after, delta.inventory(docs), set())
    assert report["new_boards"]["intrusul"]["count"] == 0
    assert report["first_exposures"]["intrusul"]["count"] == 2


def test_campaign_uses_only_current_landed_name_classification(tmp_path):
    registry = tmp_path / delta.REGISTRY
    registry.parent.mkdir(parents=True)
    rows = [
        {"id": "n1", "type": "name", "state": "landed", "identity": {"owner_id": "known"}},
        {"id": "n2", "type": "name", "state": "landed", "identity": {}},
        {"id": "n3", "type": "name", "state": "landed", "identity": {"owner_id": "withdrawn"}},
        {
            "id": "n3", "type": "name", "state": "retracted(reason)",
            "identity": {"owner_id": "withdrawn"},
        },
        {"id": "n4", "type": "name", "state": "qualified", "identity": {"owner_id": "pending"}},
        {"id": "n5", "type": "concept", "state": "landed", "identity": {"owner_id": "word"}},
    ]
    for row in rows:
        row["schema"] = "cat-content-candidate-1"
        row["payload"] = {"node_id": "declared"} if row["id"] == "n2" else {}
    registry.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")

    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "add", "."], check=True)
    subprocess.run(
        ["git", "-C", str(tmp_path), "-c", "user.name=Test", "-c", "user.email=test@example.test",
         "-c", "commit.gpgsign=false", "commit", "-qm", "registry"], check=True,
    )
    head = delta.resolve_commit(tmp_path, "HEAD")
    registry.write_text("", encoding="utf-8")  # Ignore unpublished registry edits.
    assert delta.landed_names(
        tmp_path, head, {"known", "declared", "withdrawn", "pending", "word"},
    ) == {"known", "declared"}


def test_campaign_checks_bundle_pin_sources_and_checkout_line_endings(tmp_path):
    def write(path, data):
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)

    source_bytes = b'{"fixture": true}\n'
    digest = hashlib.sha256(source_bytes).hexdigest()
    bundle = serving_bundle(documents())
    bundle["sources"] = {Path(path).name: digest for path in delta.CAMPAIGN_SOURCES}
    for path in delta.CAMPAIGN_SOURCES:
        write(path, source_bytes.replace(b"\n", b"\r\n"))
    raw = json.dumps(bundle).encode("utf-8")
    pin = f'const bundledSHA256 = "{hashlib.sha256(raw).hexdigest()}"\n'.encode("ascii")
    write(delta.BUNDLE, raw)
    write(delta.BUNDLE_PIN, pin)

    assert delta.campaign_bundle(tmp_path, None) == bundle
    write(delta.BUNDLE_PIN, b'invalid')
    with pytest.raises(delta.CampaignUnavailable, match="does not match its pin"):
        delta.campaign_bundle(tmp_path, None)
    write(delta.BUNDLE_PIN, pin)
    write(delta.FILES["kg"], b'{"fixture": false}\n')
    with pytest.raises(delta.CampaignUnavailable, match="stale for .*kg_sample"):
        delta.campaign_bundle(tmp_path, None)



def test_quick_roles_require_a_reachable_shelf():
    base = board("intrusul", "base", {"members": ["cake"], "intruder": "nut"})
    competitors = [{**base, "catalog_id": str(i), "source_id": str(i), "starter_safe": False}
                   for i in range(5)]
    hidden = {**base, "catalog_id": "hidden", "source_id": "0", "overall_score": 54,
              "starter_safe": False}
    starter = {**hidden, "catalog_id": "starter", "starter_safe": True}
    fallback = {**hidden, "catalog_id": "fallback", "source_id": "outside"}
    assert delta.reachable_quick_ids([*competitors, hidden, starter, fallback]) == {
        "0", "1", "2", "3", "4", "starter",
    }
    assert "fallback" in delta.reachable_quick_ids([*competitors[:4], fallback])


def test_implicit_campaign_counts_local_main_from_unlanded_branch(tmp_path, capsys):
    subprocess.run(["git", "init", "-q", "-b", "main", str(tmp_path)], check=True)

    def git_run(*args):
        subprocess.run(["git", "-C", str(tmp_path), *args], check=True)

    docs = documents()
    docs["derived"] = {"boards": []}
    bundle = serving_bundle(docs)

    def save():
        for key, name in delta.FILES.items():
            target = tmp_path / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps(docs[key]), encoding="utf-8")
        bundle["sources"] = {}
        import hashlib
        for name in delta.CAMPAIGN_SOURCES:
            target = tmp_path / name
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists():
                target.write_bytes(b"{}\n")
            bundle["sources"][target.name] = hashlib.sha256(target.read_bytes()).hexdigest()
        raw = json.dumps(bundle).encode()
        target = tmp_path / delta.BUNDLE
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        (tmp_path / delta.BUNDLE_PIN).write_text(
            'const bundledSHA256 = "' + hashlib.sha256(raw).hexdigest() + '"\n', encoding="utf-8",
        )

    def commit(message):
        git_run("add", ".")
        git_run("-c", "user.name=Test", "-c", "user.email=test@example.test",
                "-c", "commit.gpgsign=false", "commit", "-qm", message)

    save()
    commit("baseline")
    git_run("checkout", "-qb", "candidate")
    docs["kg"]["kg_nodes"][0]["aliases"].append("nuci")
    bundle["normalized_index"]["nuci"] = "nut"
    save()
    commit("unlanded addition")
    assert delta.main(["--repo", str(tmp_path), "--baseline", "main", "--json"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["forms"]["added_count"] == 1
    assert report["campaign"]["new_forms"]["count"] == 0
    assert report["campaign_comparison"] == "local_main"
    assert delta.main(["--repo", str(tmp_path), "--baseline", "main", "--head", "candidate"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["campaign"]["new_forms"]["count"] == 1
    assert report["campaign_comparison"] == "explicit_commit"
    assert delta.main([
        "--repo", str(tmp_path), "--baseline", "main", "--head", "candidate", "--text",
    ]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert lines[0] == (
        "words +0, forms on existing words +1 (nuci), names +0, links with a new word +0"
    )
    assert lines[1] == "forms on new words +0, forms on other entities +0"
    assert lines[2] == "links between existing words +0, other KG links +0, Alchimie recipes +0"
    (tmp_path / delta.FILES["rankings"]).write_text("{}", encoding="utf-8")
    assert delta.main(["--repo", str(tmp_path), "--baseline", "main", "--json"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert "authored_inventory_unavailable" in report
    assert report["campaign"]["new_forms"]["count"] == 0
