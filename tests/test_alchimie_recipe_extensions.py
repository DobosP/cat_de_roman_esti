"""Reviewed additions preserve cores and reject stale, incomplete or altered evidence."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from types import SimpleNamespace

import pytest

from cat_de_roman_esti.graph import Graph
from cat_de_roman_esti.wordgames import alchimie as A
from cat_de_roman_esti.wordgames import recipe_extensions as R
from cat_de_roman_esti.wordgames.service import WordGameService
from scripts import build_alchimie_recipe_extensions as B


def _write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    return path


@pytest.fixture
def evidence(tmp_path, monkeypatch):
    seeds, target, category = ["a", "b", "c", "d"], "t", "test"
    recipes = {("a", "b"): ("x",), ("b", "c"): ("y",), ("x", "y"): ("t",)}
    routes = (tuple(recipes.items()),)
    projection = A.RecipeProjection(recipes, routes, 3, ((3, 0.8, 0.8),))
    nodes = [{"id": n, "label_ro": n.upper(), "category": category,
              "source": "reviewed local fixture", "redistributable": True,
              "facets": {"license": "CC0"}} for n in (*seeds, "x", "y", target)]
    links = [("a", "x"), ("b", "x"), ("b", "y"), ("c", "y"),
             ("x", "t"), ("y", "t"), ("c", "x"), ("a", "y"), ("d", "x")]
    edges = [{"id": f"e{i}", "src_id": left, "dst_id": right,
              "relation": "related_to", "strength": 0.8, "bidirectional": True,
              "label_ro": "legătură verificată", "source": "reviewed local fixture",
              "redistributable": True, "facets": {"license": "CC0"}}
             for i, (left, right) in enumerate(links)]
    svc = WordGameService(Graph.from_records(nodes, edges))
    record = {"id": "board", "seeds": seeds, "target": target, "target_depth": 3,
              "status": "approved", "category": category, "difficulty": "normal"}
    item = SimpleNamespace(id="board", payload=record, category=category, _pilot_eligible=True)
    monkeypatch.setattr(B, "ROOT", tmp_path)
    monkeypatch.setattr(B, "get_service", lambda: svc)
    monkeypatch.setattr(B, "get_pack", lambda: SimpleNamespace(
        ranked=True, pool=lambda game: [item],
    ))
    monkeypatch.setattr(A, "_build_recipe_projection", lambda *args: projection)
    monkeypatch.setattr(R, "CATALOG_PATH", tmp_path / "package-fixtures/catalog.json")
    R.CATALOG_PATH.parent.mkdir()
    R._load_catalog.cache_clear()
    paths = {
        "pack": "cat_de_roman_esti/fixtures/games_pack.json",
        "kg": "cat_de_roman_esti/fixtures/kg_sample.json",
        "rubric": "docs/CRITIQUE_RUBRIC.md",
    }
    _write(tmp_path / paths["pack"], {"alchimie": [record]})
    _write(tmp_path / paths["kg"], {"kg_nodes": nodes, "kg_edges": edges})
    (tmp_path / "docs").mkdir()
    (tmp_path / paths["rubric"]).write_text("Bounded review rubric\n")
    bindings = {key: {"path": path, "sha256": B.file_sha(tmp_path / path)}
                for key, path in paths.items()}
    labelled = B._labelled_core(svc, projection, seeds, target)
    def concept(n):
        return {"id": n, "label": n.upper(), "category": category}
    candidates = []
    source_edges = {e["id"]: e for e in edges}
    for pair, result in ((["a", "c"], "x"), (["a", "c"], "y"), (["a", "d"], "x")):
        identity = {"board_id": "board", "pair": pair, "result": result}
        cid = f"alrecipe-board-{R.digest(identity)[:16]}"
        edge_rows = []
        for parent in pair:
            edge = svc.link(parent, result)
            raw = source_edges[edge.id]
            edge_rows.append({"runtime_edge": R.record_snapshot(edge), "fixture_edge": raw,
                              "fixture_edge_sha256": R.digest(raw)})
        candidate = {
            "id": cid, "board_id": "board", "category": category, "par": 3,
            "seeds": [concept(n) for n in seeds], "target": concept(target),
            "pair": [concept(n) for n in pair], "result": concept(result),
            "cohorts": ["missing_seed_pair"], "edges": edge_rows,
            "before_core_sha256": R.digest(labelled),
        }
        candidate["candidate_sha256"] = R.digest(candidate)
        candidates.append(candidate)
    artifact = {
        "schema": "alchimie-bounded-completion-candidates-v1", "bindings": bindings,
        "boards": [{"id": "board", "source_record": record,
                    "source_record_sha256": R.digest(record), "before_core": labelled,
                    "before_core_sha256": R.digest(labelled)}], "candidates": candidates,
    }
    candidate_path = _write(tmp_path / "candidates.json", artifact)
    reviews = []
    for role in ("factual", "quality"):
        reviews.append(_write(tmp_path / f"{role}.json", {
            "kind": B.REVIEW_KIND, "reviewer": f"independent-{role}", "role": role,
            "candidate_sha256": B.file_sha(candidate_path),
            "items": [{"id": c["id"], "verdict": "accept", "rationale": "Reviewed pair idea.",
                       "sources": ["https://example.org/reference"] if role == "factual" else []}
                      for c in candidates],
        }))
    yield SimpleNamespace(root=tmp_path, svc=svc, seeds=seeds, target=target, category=category,
                          core=recipes, routes=routes, projection=projection,
                          candidates=candidate_path, reviews=reviews, artifact=artifact)
    R._load_catalog.cache_clear()


def _catalog(e):
    return B.build_catalog(e.candidates, *e.reviews)


def _extend(e):
    return R.extend_recipes(e.svc, e.seeds, e.target, e.category, e.core, e.routes, 3)


def _seal(board):
    board["entry_sha256"] = R.digest({k: v for k, v in board.items() if k != "entry_sha256"})


def _restamp_candidates(e):
    for candidate in e.artifact["candidates"]:
        candidate["candidate_sha256"] = R.digest({k: v for k, v in candidate.items()
                                                   if k != "candidate_sha256"})
    _write(e.candidates, e.artifact)
    for path in e.reviews:
        review = B.read_json(path)
        review["candidate_sha256"] = B.file_sha(e.candidates)
        _write(path, review)


def test_absent_catalog_returns_a_separate_unchanged_core(evidence):
    before = deepcopy(evidence.core)
    result = _extend(evidence)
    assert result == before and result is not evidence.core
    result[("new", "pair")] = ("other",)
    assert evidence.core == before


def test_competing_accepted_outputs_are_dropped_then_safe_addition_applies(evidence):
    catalog = _catalog(evidence)
    assert len(catalog["diagnostics"]) == 1
    assert catalog["diagnostics"][0]["pair"] == ["a", "c"]
    assert len(catalog["boards"][0]["additions"]) == 1
    _write(R.CATALOG_PATH, catalog)
    result = _extend(evidence)
    assert result == {**evidence.core, ("a", "d"): ("x",)}
    assert ("a", "d") not in evidence.core
    assert R._load_catalog.cache_info().maxsize == 1


@pytest.mark.parametrize("verdict", ["reject", "hold"])
def test_one_review_rejection_or_hold_prevents_addition(evidence, verdict):
    review = B.read_json(evidence.reviews[1])
    review["items"][-1]["verdict"] = verdict
    _write(evidence.reviews[1], review)
    assert _catalog(evidence)["boards"] == []


@pytest.mark.parametrize("change", ["missing", "duplicate", "stale", "same_reviewer"])
def test_review_gate_rejects_incomplete_stale_or_nonindependent_evidence(evidence, change):
    path = evidence.reviews[1]
    review = B.read_json(path)
    if change == "missing":
        review["items"].pop()
    elif change == "duplicate":
        review["items"].append(review["items"][0])
    elif change == "stale":
        review["candidate_sha256"] = "0" * 64
    else:
        review["reviewer"] = "independent-factual"
    _write(path, review)
    with pytest.raises(ValueError):
        _catalog(evidence)


@pytest.mark.parametrize("sources", [[], ["bare-domain.ro"], ["https://"], [None],
                                     [{"url": "https://example.org"}], ["https://a.test:bad"],
                                     ["https://a.test/white space"], ["ftp://a.test/source"]])
def test_factual_accept_requires_valid_http_source_urls(evidence, sources):
    review = B.read_json(evidence.reviews[0])
    review["items"][0]["sources"] = sources
    _write(evidence.reviews[0], review)
    with pytest.raises(ValueError, match="source"):
        _catalog(evidence)


def test_rejected_factual_judgment_can_have_no_sources_but_quality_sources_must_be_valid(evidence):
    review = B.read_json(evidence.reviews[0])
    review["items"][0].update(verdict="reject", sources=[])
    _write(evidence.reviews[0], review)
    assert len(_catalog(evidence)["boards"][0]["additions"]) == 2
    review = B.read_json(evidence.reviews[1])
    review["items"][0]["sources"] = ["bad url"]
    _write(evidence.reviews[1], review)
    with pytest.raises(ValueError, match="source"):
        _catalog(evidence)


@pytest.mark.parametrize("change", ["pack", "kg", "rubric", "core", "edge", "label", "overwrite"])
def test_source_and_replayed_core_tampering_fails_even_after_candidate_restamping(evidence, change):
    if change in {"pack", "kg", "rubric"}:
        evidence.artifact["bindings"][change]["sha256"] = "0" * 64
    elif change == "core":
        board = evidence.artifact["boards"][0]
        board["before_core"]["par"] = 2
        board["before_core_sha256"] = R.digest(board["before_core"])
    elif change == "edge":
        evidence.artifact["candidates"][0]["edges"][0]["fixture_edge"]["source"] = "replaced"
    elif change == "label":
        evidence.artifact["candidates"][0]["result"]["label"] = "Different concept"
    else:
        candidate = evidence.artifact["candidates"][0]
        candidate["pair"] = [{"id": n, "label": n.upper(), "category": "test"} for n in ("a", "b")]
    _restamp_candidates(evidence)
    with pytest.raises(ValueError):
        _catalog(evidence)


@pytest.mark.parametrize("field", ["label_ro", "node_type", "source", "redistributable", "facets"])
def test_actual_node_metadata_drift_disables_all_extensions(evidence, field):
    _write(R.CATALOG_PATH, _catalog(evidence))
    from dataclasses import replace

    original = evidence.svc.graph.nodes["x"]
    value = {"redistributable": False, "facets": {"license": "different"}}.get(field, "different")
    evidence.svc.graph.nodes["x"] = replace(original, **{field: value})
    assert _extend(evidence) == evidence.core


def test_actual_edge_metadata_drift_and_wrong_core_disable_all_extensions(evidence, monkeypatch):
    _write(R.CATALOG_PATH, _catalog(evidence))
    assert R.extend_recipes(evidence.svc, evidence.seeds[::-1], evidence.target,
                            evidence.category, evidence.core, evidence.routes, 3) == evidence.core
    from dataclasses import replace

    original = evidence.svc.link
    monkeypatch.setattr(evidence.svc, "link", lambda *args, **kwargs:
                        replace(original(*args, **kwargs), source="different provenance"))
    assert _extend(evidence) == evidence.core


def test_generator_rejects_actual_node_provenance_drift_even_when_labels_match(evidence):
    from dataclasses import replace

    evidence.svc.graph.nodes["x"] = replace(evidence.svc.graph.nodes["x"], source="unreviewed")
    with pytest.raises(ValueError, match="node metadata differs"):
        _catalog(evidence)


@pytest.mark.parametrize(
    "change", ["digest", "overwrite", "weak", "new_concept", "pair_cap", "scope", "core_edge"],
)
def test_corrupt_catalog_fails_closed_including_other_board_scopes(evidence, monkeypatch, change):
    catalog = _catalog(evidence)
    board = catalog["boards"][0]
    addition = board["additions"][0]
    if change == "digest":
        addition["result"] = "y"
    elif change == "overwrite":
        addition["pair"] = ["a", "b"]
    elif change == "weak":
        board["edges"][addition["edge_ids"][0]]["strength"] = 0.69
    elif change == "new_concept":
        addition["result"] = "outside"
    elif change == "pair_cap":
        monkeypatch.setattr(R, "MAX_PAIRS", len(evidence.core))
    elif change == "core_edge":
        board["edges"].pop("e2")
    else:
        board["core"]["target"] = "a"
        board["core_sha256"] = R.digest(board["core"])
    if change != "digest":
        _seal(board)
    _write(R.CATALOG_PATH, catalog)
    with pytest.raises(ValueError):
        _extend(evidence)


def _args(e):
    return ["--candidates", str(e.candidates), "--factual-review", str(e.reviews[0]),
            "--quality-review", str(e.reviews[1])]


def test_default_dry_run_never_writes_package_and_proposal_cannot_overwrite_inputs(evidence):
    R.CATALOG_PATH.write_text("existing package sentinel")
    assert B.main(_args(evidence)) == 0
    assert R.CATALOG_PATH.read_text() == "existing package sentinel"
    before = evidence.candidates.read_bytes()
    assert B.main([*_args(evidence), "--proposal", str(evidence.candidates)]) == 1
    assert evidence.candidates.read_bytes() == before
    assert B.main([*_args(evidence), "--proposal", str(R.CATALOG_PATH)]) == 1
    assert B.main([*_args(evidence), "--write"]) == 1
    assert R.CATALOG_PATH.read_text() == "existing package sentinel"


def _final_evidence(e, catalog):
    runtime = []
    for relative in ("cat_de_roman_esti/wordgames/alchimie.py",
                     "cat_de_roman_esti/wordgames/recipe_extensions.py",
                     "scripts/build_alchimie_recipe_extensions.py"):
        path = e.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# final reviewed runtime\n")
        runtime.append({"path": relative, "sha256": B.file_sha(path)})
    catalog_sha = hashlib.sha256(B.catalog_bytes(catalog)).hexdigest()
    audit = _write(e.root / "audit.json", {"proposed_catalog_sha256": catalog_sha,
                    "candidate_sha256": catalog["candidate_sha256"], "runtime_sources": runtime})
    final = []
    for role in ("factual", "quality"):
        final.append(_write(e.root / f"final-{role}.json", {
            "kind": B.FINAL_REVIEW_KIND, "reviewer": f"independent-{role}", "role": role,
            "catalog_sha256": catalog_sha, "live_audit_sha256": B.file_sha(audit),
            "verdict": "accept", "rationale": "Reviewed this exact live projection audit.",
        }))
    return audit, final


@pytest.mark.parametrize("change", [None, "rejected", "audit", "runtime", "identity", "catalog"])
def test_package_write_requires_two_exact_final_audit_approvals(evidence, change):
    catalog = _catalog(evidence)
    audit, final = _final_evidence(evidence, catalog)
    if change in {"rejected", "identity", "catalog"}:
        review = B.read_json(final[1])
        key, value = {"rejected": ("verdict", "hold"), "identity": ("reviewer", "someone-else"),
                      "catalog": ("catalog_sha256", "0" * 64)}[change]
        review[key] = value
        _write(final[1], review)
    elif change == "audit":
        data = B.read_json(audit)
        data["candidate_sha256"] = "0" * 64
        _write(audit, data)
    elif change == "runtime":
        (evidence.root / "cat_de_roman_esti/wordgames/alchimie.py").write_text("changed\n")
    args = [*_args(evidence), "--live-audit", str(audit),
            "--final-factual-review", str(final[0]),
            "--final-quality-review", str(final[1]), "--write"]
    if change is None:
        assert B.main(args) == 0
        assert R.CATALOG_PATH.read_bytes() == B.catalog_bytes(catalog)
    else:
        assert B.main(args) == 1
        assert not R.CATALOG_PATH.exists()
