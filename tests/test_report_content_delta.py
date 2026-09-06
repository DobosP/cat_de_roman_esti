"""Content progress is distinct from metadata churn, promotions, and word forms."""

from __future__ import annotations

import copy
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
    assert len(report["baseline_commit"]) == 40
    assert delta.main(["--repo", str(tmp_path), "--text"]) == 0
    assert "forms: 1 -> 2; +1 -0" in capsys.readouterr().out
    assert delta.main(["--repo", str(tmp_path), "--baseline", "missing-ref"]) == 2
    output = capsys.readouterr()
    assert not output.out
    assert "Content delta failed" in output.err


def test_option_like_baseline_is_rejected_before_git(tmp_path, capsys):
    assert delta.main(["--repo", str(tmp_path), "--baseline=--all"]) == 2
    assert "not an option" in capsys.readouterr().err
