"""Directed numeric C3 gate and its review/ranking boundaries (ADR-0134)."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from cat_de_roman_esti.graph import Edge, Graph, Node
from cat_de_roman_esti.wordgames.service import WordGameService
from scripts import apply_rereview, critique_pack, rank_games_pack


def _service(count: int, *, outgoing: int = 0) -> WordGameService:
    graph = Graph()
    for node_id in ["target", *(f"in_{i:02}" for i in range(count)),
                    *(f"out_{i:02}" for i in range(outgoing))]:
        graph.add_node(Node(node_id, "object", node_id, "viata_de_roman", salience=1.0))
    for index in range(count):
        graph.add_edge(Edge(f"in_{index}", f"in_{index:02}", "target", "related_to",
                            strength=0.1, bidirectional=False))
    for index in range(outgoing):
        graph.add_edge(Edge(f"out_{index}", "target", f"out_{index:02}", "related_to",
                            strength=1.0, bidirectional=False))
    return WordGameService(graph)


def _record(status: str = "pending") -> dict:
    return {"id": "ct_numeric", "target": "target", "status": status,
            "difficulty": "usor", "category": "viata_de_roman", "source": "ai"}


def _pack(record: dict) -> dict:
    return {"meta": {}, "conexiuni": [], "contexto": [record], "lant": [], "alchimie": []}


@pytest.mark.parametrize("count", [0, 4, 5, 11])
@pytest.mark.parametrize("status", ["pending", "approved"])
def test_numeric_floor_is_necessary_and_status_sensitive(count: int, status: str) -> None:
    svc = _service(count, outgoing=20)
    record = _record(status)
    original = deepcopy(record)
    findings = critique_pack.check_contexto_incoming_floor(record, svc)
    if count < 5:
        assert len(findings) == 1
        assert findings[0]["check"] == "contexto_incoming_floor"
        assert findings[0]["level"] == ("WARN" if status == "approved" else "FAIL")
        assert f"{count} unique existing" in findings[0]["detail"]
    else:
        assert findings == []
    assert record == original
    assert len(svc.neighbor_ids("target")) == 20
    # Strength and salience are not a substitute for the distinct-neighbor count.
    assert all(svc.link(n, "target").strength < 0.6 for n in svc.predecessor_ids("target"))


def test_runtime_direction_deduplication_and_invalid_nodes_are_respected() -> None:
    graph = _service(2, outgoing=20).graph
    for node_id in ["bidirectional", "reverse_bidirectional", "distractor"]:
        graph.add_node(Node(node_id, "object", node_id, "viata_de_roman"))
    graph.add_edge(Edge("bidir", "target", "bidirectional", "related_to"))
    graph.add_edge(Edge("reverse", "reverse_bidirectional", "target", "related_to"))
    graph.add_edge(Edge("parallel", "in_00", "target", "related_to", strength=1.0))
    graph.add_edge(Edge("self", "target", "target", "related_to"))
    graph.add_edge(Edge("decoy", "distractor", "target", "related_to", is_distractor=True))
    graph.add_edge(Edge("missing_source", "missing", "target", "related_to"))
    graph.add_edge(Edge("missing_target", "target", "missing", "related_to"))
    svc = WordGameService(graph)
    expected = ["bidirectional", "in_00", "in_01", "reverse_bidirectional"]
    assert critique_pack.contexto_incoming_ids(svc, "target") == expected
    assert critique_pack.contexto_incoming_ids(svc, "missing") == []
    assert critique_pack.check_contexto_incoming_floor(_record(), svc)[0]["level"] == "FAIL"
    assert critique_pack.check_contexto_incoming_floor(
        {**_record(), "target": "missing"}, svc
    )[0]["detail"].startswith("0 unique existing")
    graph.edges.reverse()
    reordered = Graph()
    for node in reversed(list(graph.nodes.values())):
        reordered.add_node(node)
    for edge in graph.edges:
        reordered.add_edge(edge)
    assert critique_pack.contexto_incoming_ids(WordGameService(reordered), "target") == expected


def test_new_dossier_evidence_is_bounded_and_does_not_claim_recognition() -> None:
    svc = _service(100)
    dossier = critique_pack.build_dossier(_record(), "contexto", svc, {}, [])
    evidence = dossier["incoming_neighbor_floor"]
    assert evidence == {
        "minimum": 5, "count": 100,
        "sample": [{"id": f"in_{index:02}", "label": f"in_{index:02}"}
                   for index in range(10)],
        "sample_truncated": True, "recognition_assessed": False,
    }
    assert dossier["review_binding"] == critique_pack.dossier_review_binding(dossier)
    changed = deepcopy(dossier)
    changed["incoming_neighbor_floor"]["count"] -= 1
    assert critique_pack.dossier_review_binding(changed) != dossier["review_binding"]
    complete = critique_pack.build_dossier(_record(), "contexto", _service(4), {}, [])
    assert complete["incoming_neighbor_floor"]["sample_truncated"] is False
    assert len(complete["incoming_neighbor_floor"]["sample"]) == 4


@pytest.mark.parametrize("status, expected", [("pending", 1), ("approved", 0)])
def test_strict_cli_blocks_pending_and_only_reports_approved(
    monkeypatch, tmp_path, status: str, expected: int,
) -> None:
    record = _record(status)
    pack = _pack(record)
    monkeypatch.setattr(critique_pack, "load_all", lambda *_: (
        pack, _service(4, outgoing=20), {}, {"generic_nodes": {}, "region_ids": set()},
    ))
    report = tmp_path / "report.json"
    assert critique_pack.main([
        "critique_pack.py", "--status", status, "--ids", record["id"],
        "--strict", "--json", str(report),
    ]) == expected
    raw = json.loads(report.read_text())
    assert raw["thresholds"]["contexto_incoming_floor"] == 5
    assert raw["items"][record["id"]]["findings"][0]["check"] == "contexto_incoming_floor"
    assert pack == _pack(record)


def test_promotion_recheck_blocks_numerically_impossible_pending_target(monkeypatch) -> None:
    record = _record()
    pack = _pack(record)
    monkeypatch.setattr(apply_rereview.critique_pack, "load_all", lambda *_: (
        pack, _service(4, outgoing=20), {}, {"generic_nodes": {}, "region_ids": set()},
    ))
    assert apply_rereview.critique_promotions({record["id"]}) == 1
    assert pack == _pack(record)


def test_existing_pending_holds_pass_only_the_numeric_floor() -> None:
    pack, svc, strong, regions = critique_pack.load_all(
        critique_pack.PACKAGE_PACK, critique_pack.PACKAGE_KG,
    )
    ids = {"ct_meme_net_238", "ct_societate_257"}
    _, _, selected = critique_pack.run(pack, svc, strong, regions, ["contexto"], {"pending"}, ids)
    assert {record["id"] for _, record, _ in selected} == ids
    for game, record, findings in selected:
        assert record["status"] == "pending"
        assert all(finding["check"] != "contexto_incoming_floor" for finding in findings)
        evidence = critique_pack.build_dossier(record, game, svc, strong, findings)[
            "incoming_neighbor_floor"
        ]
        assert evidence["count"] >= 5
        assert evidence["recognition_assessed"] is False


def test_archived_dossier_keeps_its_embedded_rubric_and_binding() -> None:
    archive = Path(__file__).resolve().parents[1] / (
        "docs/reviews/v89-feedback-and-conexiuni-recovery/dossiers/ct_viata_de_roman_353.json"
    )
    original = archive.read_bytes()
    dossier = json.loads(original)
    assert dossier["rubric_sha256"] != critique_pack.rubric_sha256()
    assert "incoming_neighbor_floor" not in dossier
    assert critique_pack.dossier_review_binding(dossier) == dossier["review_binding"]
    assert archive.read_bytes() == original


def test_new_stock_warning_does_not_change_any_contexto_score_or_eligibility() -> None:
    pack, svc, strong, regions = critique_pack.load_all(
        critique_pack.PACKAGE_PACK, critique_pack.PACKAGE_KG,
    )
    _, _, selected = critique_pack.run(
        pack, svc, strong, regions, ["contexto"], {"approved", "pending"}, None,
    )
    demoted = rank_games_pack._owner_demotions()

    def salience(node_id: str) -> float:
        return rank_games_pack._service_salience(svc, node_id)

    def strength(a: str, b: str) -> float:
        return rank_games_pack._service_edge_strength(svc, a, b)

    warnings = 0
    for game, record, findings in selected:
        dossier = critique_pack.build_dossier(record, game, svc, strong, findings)
        baseline = deepcopy(dossier)
        baseline.pop("incoming_neighbor_floor")
        baseline["lint_findings"] = [finding for finding in findings
                                     if finding["check"] != "contexto_incoming_floor"]
        if record["status"] != "approved":
            continue
        warnings += sum(f["check"] == "contexto_incoming_floor" for f in findings)
        assert rank_games_pack.romanian_familiarity(game, dossier, salience) == (
            rank_games_pack.romanian_familiarity(game, baseline, salience)
        )
        assert rank_games_pack.play_quality(game, record, dossier, strength) == (
            rank_games_pack.play_quality(game, record, baseline, strength)
        )
        assert rank_games_pack._pilot_eligible(record, game, dossier, svc, demoted) == (
            rank_games_pack._pilot_eligible(record, game, baseline, svc, demoted)
        )
    assert warnings > 0
