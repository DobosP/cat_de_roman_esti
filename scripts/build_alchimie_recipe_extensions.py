#!/usr/bin/env python3
"""Build reviewed Alchimie additions; package writes require final audit approval."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cat_de_roman_esti.web.settings")

import django  # noqa: E402

django.setup()

from content_file_transaction import atomic_write  # noqa: E402

from cat_de_roman_esti.graph import Edge, Node  # noqa: E402
from cat_de_roman_esti.wordgames import alchimie as A  # noqa: E402
from cat_de_roman_esti.wordgames import recipe_extensions as R  # noqa: E402
from cat_de_roman_esti.wordgames.packs import get_pack  # noqa: E402
from cat_de_roman_esti.wordgames.service import get_service  # noqa: E402

REVIEW_KIND = "alchimie-recipe-extension-review-v1"
FINAL_REVIEW_KIND = "alchimie-recipe-extension-final-review-v1"


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def read_json(path: Path) -> dict:
    value = json.loads(path.read_bytes())
    require(isinstance(value, dict), f"{path}: object required")
    return value


def catalog_bytes(catalog: dict) -> bytes:
    return (json.dumps(catalog, ensure_ascii=False, sort_keys=True, indent=2,
                       allow_nan=False) + "\n").encode("utf-8")


def _valid_source_url(value: object) -> bool:
    if not isinstance(value, str) or not value or any(c.isspace() for c in value):
        return False
    try:
        parsed = urlsplit(value)
        return (parsed.scheme in {"http", "https"} and bool(parsed.hostname)
                and bool(parsed.netloc) and parsed.username is None
                and parsed.password is None and (parsed.port is None or parsed.port > 0))
    except ValueError:
        return False


def read_review(path: Path, role: str, candidate_sha: str, candidate_ids: set[str]) -> dict:
    raw = path.read_bytes()
    review = json.loads(raw)
    require(isinstance(review, dict), f"{role}: review object required")
    require(review.get("kind") == REVIEW_KIND and review.get("role") == role,
            f"{role}: invalid review kind/role")
    require(isinstance(review.get("reviewer"), str) and bool(review["reviewer"].strip()),
            f"{role}: reviewer identity required")
    require(review.get("candidate_sha256") == candidate_sha, f"{role}: stale candidate binding")
    items = review.get("items")
    require(isinstance(items, list) and all(isinstance(i, dict) for i in items),
            f"{role}: review items required")
    ids = [item.get("id") for item in items]
    require(all(isinstance(i, str) for i in ids) and len(ids) == len(set(ids))
            and set(ids) == candidate_ids, f"{role}: incomplete or duplicate candidate coverage")
    for item in items:
        require(item.get("verdict") in {"accept", "reject", "hold"}
                and isinstance(item.get("rationale"), str) and bool(item["rationale"].strip())
                and isinstance(item.get("sources"), list), f"{role}: incomplete judgment")
        require(all(_valid_source_url(source) for source in item["sources"]),
                f"{role}: every source must be a valid HTTP(S) URL")
        if role == "factual" and item["verdict"] == "accept":
            require(bool(item["sources"]), "factual: accepted candidates need source URLs")
    review["_source_sha256"] = hashlib.sha256(raw).hexdigest()
    return review


def _labelled_core(service, projection, seeds, target) -> dict:
    def concept(nid):
        node = service.node(nid)
        return {"id": nid, "label": node.label_ro, "category": node.category}

    def recipe(pair, outputs):
        return {"pair": [concept(n) for n in pair], "results": [concept(n) for n in outputs]}

    concepts = set(seeds) | {
        n for pair, outputs in projection.recipes.items() for n in (*pair, *outputs)
    }
    return {
        "par": projection.par,
        "recipes": [recipe(pair, outs) for pair, outs in projection.recipes.items()],
        "routes": [[recipe(pair, outs) for pair, outs in route] for route in projection.routes],
        "concepts": [concept(n) for n in sorted(concepts)],
        "seed_pair_total": len(seeds) * (len(seeds) - 1) // 2,
        "productive_seed_pairs": A._projected_opening_pair_count(list(seeds), projection.recipes),
        "target_producing_pairs": sum(
            target in outs for outs in projection.recipes.values()
        ),
    }


def build_catalog(candidate_path: Path, factual_path: Path, quality_path: Path) -> dict:
    """Replay exact current cores and intersect two complete independent judgments."""
    candidate_sha = file_sha(candidate_path)
    artifact = read_json(candidate_path)
    require(artifact.get("schema") == "alchimie-bounded-completion-candidates-v1",
            "invalid candidate schema")
    bindings = artifact.get("bindings", {})
    expected_paths = {
        "pack": "cat_de_roman_esti/fixtures/games_pack.json",
        "kg": "cat_de_roman_esti/fixtures/kg_sample.json",
        "rubric": "docs/CRITIQUE_RUBRIC.md",
    }
    for name, relative in expected_paths.items():
        require(isinstance(bindings.get(name), dict)
                and bindings[name].get("path") == relative
                and bindings[name].get("sha256") == file_sha(ROOT / relative),
                f"stale or invalid {name} binding")
    candidates = artifact.get("candidates")
    require(isinstance(candidates, list) and all(isinstance(c, dict) for c in candidates),
            "invalid candidates")
    ids = [c.get("id") for c in candidates]
    require(all(isinstance(i, str) for i in ids) and len(ids) == len(set(ids)),
            "duplicate candidate ids")
    reviews = [read_review(path, role, candidate_sha, set(ids)) for path, role in
               ((factual_path, "factual"), (quality_path, "quality"))]
    require(reviews[0]["reviewer"] != reviews[1]["reviewer"], "reviewers must differ")
    accepted = set(ids)
    for review in reviews:
        accepted &= {i["id"] for i in review["items"] if i["verdict"] == "accept"}

    service = get_service()
    pack = get_pack()
    eligible = {item.id: item for item in pack.pool("alchimie")
                if not pack.ranked or item._pilot_eligible}
    archived = artifact.get("boards")
    require(isinstance(archived, list) and all(isinstance(b, dict) for b in archived),
            "invalid archived cores")
    archived_ids = [b.get("id") for b in archived]
    require(all(isinstance(i, str) for i in archived_ids)
            and len(archived_ids) == len(set(archived_ids))
            and set(archived_ids) == set(eligible), "incomplete current board coverage")
    raw_kg = read_json(ROOT / expected_paths["kg"])
    source_edges = {e["id"]: e for e in raw_kg["kg_edges"]}
    source_nodes = {n["id"]: n for n in raw_kg["kg_nodes"]}
    raw_pack = read_json(ROOT / expected_paths["pack"])
    source_records = {r["id"]: r for r in raw_pack["alchimie"]}
    cores = {}
    for board in archived:
        item = eligible[board["id"]]
        seeds, target = item.payload["seeds"], item.payload["target"]
        require(board.get("source_record") == source_records[item.id]
                and board.get("source_record_sha256") == R.digest(source_records[item.id]),
                f"{item.id}: stale source record")
        projection = A._build_recipe_projection(seeds, target, item.category)
        require(projection is not None, f"{item.id}: unavailable current core")
        labelled = _labelled_core(service, projection, seeds, target)
        require(board.get("before_core") == labelled
                and board.get("before_core_sha256") == R.digest(labelled),
                f"{item.id}: stale core books/routes/labels")
        for concept in labelled["concepts"]:
            nid = concept["id"]
            require(R.record_snapshot(service.node(nid))
                    == R.record_snapshot(Node.from_record(source_nodes[nid])),
                    f"{item.id}: actual node metadata differs from reviewed KG")
        for pair, outputs in projection.recipes.items():
            for parent in pair:
                for output in outputs:
                    edge = service.link(parent, output)
                    require(edge is not None and edge.id in source_edges
                            and R.record_snapshot(edge)
                            == R.record_snapshot(Edge.from_record(source_edges[edge.id])),
                            f"{item.id}: actual core edge metadata differs from reviewed KG")
        core = R.core_record(seeds, target, item.category, projection.recipes,
                             projection.routes, projection.par)
        cores[item.id] = (board, core, projection)

    chosen: dict[tuple[str, tuple[str, str]], list[dict]] = {}
    for candidate in candidates:
        cid = candidate["id"]
        require(candidate.get("candidate_sha256") == R.digest({
            k: v for k, v in candidate.items() if k != "candidate_sha256"
        }), f"{cid}: altered candidate")
        bid = candidate.get("board_id")
        require(bid in cores, f"{cid}: unknown board")
        archived_board, core, projection = cores[bid]
        require(candidate.get("before_core_sha256") == archived_board["before_core_sha256"],
                f"{cid}: stale core binding")
        pair = tuple(n["id"] for n in candidate["pair"])
        result = candidate["result"]["id"]
        identity = {"board_id": bid, "pair": list(pair), "result": result}
        require(cid == f"alrecipe-{bid}-{R.digest(identity)[:16]}", f"{cid}: unstable identity")
        concepts = {n["id"] for n in archived_board["before_core"]["concepts"]}
        require(len(pair) == 2 and list(pair) == sorted(set(pair))
                and pair not in projection.recipes and set(pair) | {result} <= concepts
                and result not in set(pair) | set(core["seeds"])
                and core["target"] not in pair, f"{cid}: invalid absent-pair extension")
        expected_cohorts = []
        if set(pair) <= set(core["seeds"]):
            expected_cohorts.append("missing_seed_pair")
        if result == core["target"]:
            expected_cohorts.append("missing_target_pair")
        require(bool(expected_cohorts) and candidate.get("cohorts") == expected_cohorts,
                f"{cid}: invalid candidate cohort")
        require(candidate.get("category") == core["category"]
                and candidate.get("par") == core["par"]
                and [n["id"] for n in candidate.get("seeds", [])] == core["seeds"]
                and candidate.get("target", {}).get("id") == core["target"],
                f"{cid}: board context differs")
        for concept in [*candidate["pair"], candidate["result"], candidate["target"],
                        *candidate["seeds"]]:
            node = service.node(concept["id"])
            require(node is not None and concept == {
                "id": node.id, "label": node.label_ro, "category": node.category,
            }, f"{cid}: concept labels differ")
        require(result in service.common_neighbors(*pair, category=core["category"]),
                f"{cid}: result absent from scoped graph")
        require(isinstance(candidate.get("edges"), list) and len(candidate["edges"]) == 2,
                f"{cid}: exactly two edges required")
        for parent, archived_edge in zip(pair, candidate["edges"], strict=True):
            edge = service.link(parent, result)
            require(edge is not None and not edge.is_distractor
                    and edge.strength >= R.MIN_STRENGTH, f"{cid}: edge strength differs")
            require(archived_edge.get("runtime_edge") == R.record_snapshot(edge)
                    and archived_edge.get("fixture_edge") == source_edges[edge.id]
                    and archived_edge.get("fixture_edge_sha256") == R.digest(source_edges[edge.id]),
                    f"{cid}: edge metadata/provenance differs")
        if cid in accepted:
            chosen.setdefault((bid, pair), []).append(candidate)

    diagnostics = []
    additions_by_board: dict[str, list[dict]] = {}
    for (bid, pair), options in sorted(chosen.items()):
        if len(options) != 1:
            diagnostics.append({"board_id": bid, "pair": list(pair),
                                "reason": "competing accepted outputs; all dropped",
                                "candidate_ids": sorted(c["id"] for c in options)})
            continue
        candidate = options[0]
        additions_by_board.setdefault(bid, []).append({
            "candidate_id": candidate["id"], "candidate_sha256": candidate["candidate_sha256"],
            "pair": list(pair), "result": candidate["result"]["id"],
            "edge_ids": [e["runtime_edge"]["id"] for e in candidate["edges"]],
        })
    boards = []
    for bid, additions in sorted(additions_by_board.items()):
        archived_board, core, projection = cores[bid]
        nodes = {n["id"]: R.record_snapshot(service.node(n["id"]))
                 for n in archived_board["before_core"]["concepts"]}
        edges = {}
        for pair, outputs in projection.recipes.items():
            for parent in pair:
                for output in outputs:
                    edge = service.link(parent, output)
                    edges[edge.id] = R.record_snapshot(edge)
        for addition in additions:
            for parent in addition["pair"]:
                edge = service.link(parent, addition["result"])
                edges[edge.id] = R.record_snapshot(edge)
        board = {"id": bid, "core": core, "core_sha256": R.digest(core),
                 "nodes": nodes, "edges": edges, "additions": additions}
        board["entry_sha256"] = R.digest(board)
        boards.append(board)
    catalog = {
        "schema": R.SCHEMA, "candidate_sha256": candidate_sha,
        "bindings": {name: bindings[name] for name in expected_paths},
        "semantic_reviews": [
            {"reviewer": review["reviewer"], "role": review["role"],
             "sha256": review["_source_sha256"]}
            for review in reviews
        ],
        "boards": boards, "diagnostics": diagnostics,
    }
    require(file_sha(candidate_path) == candidate_sha, "candidates changed during generation")
    for review, path in zip(reviews, (factual_path, quality_path), strict=True):
        require(file_sha(path) == review["_source_sha256"], "review changed during generation")
    for name, relative in expected_paths.items():
        require(file_sha(ROOT / relative) == bindings[name]["sha256"],
                f"{name} changed during generation")
    R.validate_catalog(catalog)
    return catalog


def confirm_final_reviews(catalog: dict, live_audit: Path, factual: Path, quality: Path) -> None:
    """Final judgments bind exact proposal bytes and an audit of the final runtime."""
    proposed_sha = hashlib.sha256(catalog_bytes(catalog)).hexdigest()
    audit_sha = file_sha(live_audit)
    audit = read_json(live_audit)
    require(audit.get("proposed_catalog_sha256") == proposed_sha
            and audit.get("candidate_sha256") == catalog["candidate_sha256"],
            "final live audit does not bind this proposal/candidate artifact")
    sources = audit.get("runtime_sources")
    require(isinstance(sources, list) and all(isinstance(s, dict) for s in sources),
            "final live audit runtime sources required")
    paths = [s.get("path") for s in sources]
    require(all(isinstance(p, str) for p in paths) and len(set(paths)) == len(paths)
            and {"cat_de_roman_esti/wordgames/alchimie.py",
                 "cat_de_roman_esti/wordgames/recipe_extensions.py",
                 "scripts/build_alchimie_recipe_extensions.py"} <= set(paths),
            "final live audit must bind the crafting runtime, extension loader and generator")
    for source in sources:
        path = (ROOT / source["path"]).resolve()
        require(path.is_relative_to(ROOT) and path.is_file()
                and file_sha(path) == source.get("sha256"), "stale final runtime audit")
    initial = {r["role"]: r for r in catalog["semantic_reviews"]}
    for role, path in (("factual", factual), ("quality", quality)):
        review = read_json(path)
        require(review.get("kind") == FINAL_REVIEW_KIND and review.get("role") == role
                and review.get("reviewer") == initial[role]["reviewer"],
                f"{role}: final reviewer identity/role differs")
        require(review.get("catalog_sha256") == proposed_sha
                and review.get("live_audit_sha256") == audit_sha,
                f"{role}: stale final proposal/audit binding")
        require(review.get("verdict") == "accept" and isinstance(review.get("rationale"), str)
                and bool(review["rationale"].strip()), f"{role}: final approval required")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates", type=Path, required=True)
    parser.add_argument("--factual-review", type=Path, required=True)
    parser.add_argument("--quality-review", type=Path, required=True)
    parser.add_argument("--proposal", type=Path,
                        help="optional staged proposal; never a package fixture")
    parser.add_argument("--live-audit", type=Path)
    parser.add_argument("--final-factual-review", type=Path)
    parser.add_argument("--final-quality-review", type=Path)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.proposal:
            inputs = [args.candidates, args.factual_review, args.quality_review,
                      args.live_audit, args.final_factual_review, args.final_quality_review]
            require(args.proposal.resolve() not in {p.resolve() for p in inputs if p},
                    "proposal must not overwrite an input")
            require(not args.proposal.resolve().is_relative_to(R.CATALOG_PATH.parent.resolve()),
                    "proposal must not write package fixtures")
        if args.write:
            require(all((args.live_audit, args.final_factual_review, args.final_quality_review)),
                    "--write requires a live audit and both final reviews")
        catalog = build_catalog(args.candidates, args.factual_review, args.quality_review)
        if args.write:
            confirm_final_reviews(catalog, args.live_audit,
                                  args.final_factual_review, args.final_quality_review)
        blob = catalog_bytes(catalog)
        if args.proposal:
            atomic_write(args.proposal, blob)
        if args.write:
            atomic_write(R.CATALOG_PATH, blob)
        print(json.dumps({"mode": "write" if args.write else "dry-run",
                          "catalog_sha256": hashlib.sha256(blob).hexdigest(),
                          "boards": len(catalog["boards"]),
                          "additions": sum(len(b["additions"]) for b in catalog["boards"]),
                          "diagnostics": catalog["diagnostics"]}, ensure_ascii=False))
        return 0
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(f"Alchimie extensions: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
