#!/usr/bin/env python3
"""Generate candidates or a twice-reviewed shared world; dry-run by default."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import quote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import alchimie_discovery_recipe_source as SOURCE  # noqa: E402
from content_file_transaction import atomic_write  # noqa: E402

from cat_de_roman_esti.graph import Node  # noqa: E402
from cat_de_roman_esti.wordgames.recipe_extensions import record_snapshot  # noqa: E402

CATALOG = ROOT / "cat_de_roman_esti/fixtures/alchimie_discovery_world_v92.json"
REVIEW_KIND = "alchimie-discovery-world-review-v1"
FINAL_REVIEW_KIND = "alchimie-discovery-world-final-v1"
RUNTIME_SOURCES = (
    "cat_de_roman_esti/wordgames/discovery_world.py",
    "cat_de_roman_esti/wordgames/alchimie_explore.py",
    "cat_de_roman_esti/wordgames/service.py",
    "cat_de_roman_esti/wordgames/_session_endpoint.py",
    "cat_de_roman_esti/web/urls.py",
    "scripts/build_alchimie_discovery_world.py",
    "scripts/alchimie_discovery_recipe_source.py",
    "scripts/audit_alchimie_discovery_world.py",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2,
                       allow_nan=False) + "\n").encode()


def bindings() -> dict:
    return {
        "kg_sha256": file_sha(ROOT / "cat_de_roman_esti/fixtures/kg_sample.json"),
        "rubric_sha256": file_sha(ROOT / "docs/CRITIQUE_RUBRIC.md"),
        "editorial_source_sha256": file_sha(Path(SOURCE.__file__)),
    }


def candidate() -> dict:
    kg = json.loads((ROOT / "cat_de_roman_esti/fixtures/kg_sample.json").read_bytes())
    by_label: dict[str, list[Node]] = {}
    for record in kg["kg_nodes"]:
        node = Node.from_record(record)
        by_label.setdefault(node.label_ro, []).append(node)

    def node(label: str) -> Node:
        matches = by_label.get(label, [])
        require(len(matches) == 1, f"unknown or ambiguous concept label: {label}")
        return matches[0]

    recipes = []
    for rid, left, right, result, explanation in SOURCE.RECIPES:
        recipes.append({
            "id": rid, "pair": sorted([node(left).id, node(right).id]),
            "result": node(result).id, "explanation": explanation,
            "sources": ["https://dexonline.ro/definitie/" + quote(result.lower())],
        })
    starters = [node(label).id for label in SOURCE.STARTERS]
    unlocks = [{"id": uid, "after_discoveries": threshold, "title": title,
                "concept_ids": [node(label).id for label in labels]}
               for uid, threshold, title, labels in SOURCE.UNLOCKS]
    used = (set(starters) | {nid for tier in unlocks for nid in tier["concept_ids"]}
            | {nid for r in recipes for nid in [*r["pair"], r["result"]]})
    concepts = []
    for n in sorted((Node.from_record(r) for r in kg["kg_nodes"]), key=lambda n: n.id):
        if n.id in used:
            concepts.append({"id": n.id, "label": n.label_ro,
                             "description": SOURCE.DESCRIPTIONS.get(n.label_ro, n.description),
                             "source": n.source, "redistributable": n.redistributable,
                             "snapshot": record_snapshot(n)})
    artifact = {
        "schema_version": 1, "kind": "alchimie-discovery-world-candidates-v1",
        "world": {**SOURCE.WORLD, "starter_ids": starters},
        "bindings": bindings(), "concepts": concepts, "recipes": recipes,
        "unlocks": unlocks,
        "goals": [{"id": gid, "target": node(label).id, "title": title}
                  for gid, label, title in SOURCE.GOALS],
    }
    audit(artifact)
    return artifact


def audit(world: dict) -> dict:
    """Deterministic full closure with supply milestones counted separately."""
    concepts = world["concepts"]
    ids = {c["id"] for c in concepts}
    require(1 <= len(ids) == len(concepts) <= 128, "duplicate or excessive concepts")
    starters = world["world"]["starter_ids"]
    require(2 <= len(set(starters)) == len(starters) <= 12, "invalid starting inventory")
    require(set(starters) <= ids, "unknown starter")
    unlocks = world["unlocks"]
    require(len(unlocks) <= 8 and len({u["id"] for u in unlocks}) == len(unlocks),
            "invalid supply tiers")
    supplies = [nid for u in unlocks for nid in u["concept_ids"]]
    require(len(supplies) <= 48 and len(set(supplies)) == len(supplies)
            and not set(supplies) & set(starters) and set(supplies) <= ids,
            "duplicate, overlapping or unknown supplies")
    require(all(type(u["after_discoveries"]) is int and 0 < u["after_discoveries"] <= 128
                and u["concept_ids"] for u in unlocks), "invalid supply threshold")
    recipes = world["recipes"]
    require(1 <= len(recipes) <= 512 and len({r["id"] for r in recipes}) == len(recipes),
            "invalid recipe inventory")
    pairs = []
    for r in recipes:
        pair = r["pair"]
        require(len(pair) == 2 and pair == sorted(set(pair)) and set(pair) <= ids,
                f"{r['id']}: invalid pair")
        require(r["result"] in ids and r["result"] not in set(pair) | set(starters)
                | set(supplies), f"{r['id']}: result is an ingredient or supplied concept")
        require(isinstance(r["explanation"], str) and r["explanation"].strip(),
                f"{r['id']}: missing explanation")
        pairs.append(tuple(pair))
    require(len(set(pairs)) == len(pairs), "world contains ambiguous duplicate pairs")
    goals = world["goals"]
    require(0 < len(goals) <= 32 and len({g["id"] for g in goals}) == len(goals)
            and all(g["target"] in {r["result"] for r in recipes} for g in goals),
            "invalid optional goals")
    owned = set(starters)
    discoveries: set[str] = set()
    unlocked: set[str] = set()
    rounds = []
    while True:
        gifts = [u for u in unlocks if u["id"] not in unlocked
                 and u["after_discoveries"] <= len(discoveries)]
        for gift in gifts:
            owned.update(gift["concept_ids"])
            unlocked.add(gift["id"])
        new = {r["result"] for r in recipes if set(r["pair"]) <= owned} - owned
        if not new and not gifts:
            break
        discoveries.update(new)
        owned.update(new)
        rounds.append({"step": len(rounds) + 1, "crafted_ids": sorted(new),
                       "unlocked_tiers": [u["id"] for u in gifts],
                       "total_crafted": len(discoveries), "total_owned": len(owned)})
    require(owned == ids, f"unreachable world concepts: {sorted(ids - owned)}")
    require(len(unlocked) == len(unlocks), "unreachable supply milestone")
    used_as_input = {nid for r in recipes for nid in r["pair"]}
    require((set(starters) | set(supplies)) <= used_as_input, "unused starting/supplied concept")
    alternatives = Counter(r["result"] for r in recipes)
    return {
        "concepts": len(ids), "starters": len(starters), "supplies": len(supplies),
        "discoverable_results": len(discoveries), "recipes": len(recipes),
        "opening_recipes": sum(set(r["pair"]) <= set(starters) for r in recipes),
        "all_starting_pairs": len(starters) * (len(starters) - 1) // 2,
        "results_with_alternatives": sum(n > 1 for n in alternatives.values()),
        "terminal_results": len(discoveries - used_as_input), "goals": len(goals),
        "closure_rounds": rounds,
    }


def valid_url(value: object) -> bool:
    if not isinstance(value, str) or any(c.isspace() for c in value):
        return False
    try:
        parsed = urlsplit(value)
        return (parsed.scheme in {"https", "http"} and bool(parsed.hostname)
                and parsed.username is None and parsed.password is None
                and (parsed.port is None or parsed.port > 0))
    except ValueError:
        return False


def read_review(path: Path, role: str, sha: str, ids: set[str]) -> dict:
    value = json.loads(path.read_bytes())
    require(isinstance(value, dict) and value.get("kind") == REVIEW_KIND
            and value.get("role") == role, f"{role}: invalid review")
    require(value.get("candidate_sha256") == sha, f"{role}: stale candidate binding")
    require(isinstance(value.get("reviewer"), str) and value["reviewer"].strip(),
            f"{role}: missing reviewer")
    rows = value.get("items")
    require(isinstance(rows, list) and all(isinstance(r, dict) for r in rows),
            f"{role}: missing judgments")
    actual = [r.get("id") for r in rows]
    require(all(isinstance(i, str) for i in actual) and len(set(actual)) == len(actual)
            and set(actual) == ids, f"{role}: incomplete/unknown/duplicate coverage")
    require(value.get("world_verdict") == "accept" and
            isinstance(value.get("world_rationale"), str) and value["world_rationale"].strip(),
            f"{role}: shared world, supplies and optional goals require acceptance")
    for row in rows:
        require(row.get("verdict") in {"accept", "reject", "hold"}
                and isinstance(row.get("rationale"), str) and row["rationale"].strip(),
                f"{role}: incomplete judgment")
        sources = row.get("sources")
        require(isinstance(sources, list) and all(valid_url(s) for s in sources),
                f"{role}: invalid sources")
        if role == "factual" and row["verdict"] == "accept":
            require(bool(sources), "factual acceptance requires checked source URLs")
    return value


def build_catalog(candidate_path: Path, factual_path: Path, quality_path: Path) -> dict:
    raw = candidate_path.read_bytes()
    value = json.loads(raw)
    require(value.get("kind") == "alchimie-discovery-world-candidates-v1"
            and value.get("schema_version") == 1, "invalid candidate schema")
    require(value.get("bindings") == bindings(), "stale source/KG/rubric bindings")
    require(raw == json_bytes(candidate()), "candidate differs from current editorial generator")
    sha = hashlib.sha256(raw).hexdigest()
    ids = {r["id"] for r in value["recipes"]}
    factual = read_review(factual_path, "factual", sha, ids)
    quality = read_review(quality_path, "quality", sha, ids)
    require(factual["reviewer"] != quality["reviewer"], "reviewers must be independent")
    accepted = set(ids)
    for review in (factual, quality):
        accepted &= {r["id"] for r in review["items"] if r["verdict"] == "accept"}
    require(accepted == ids,
            "revise editorial source and regenerate: every proposed recipe must pass both reviews")
    factual_rows = {r["id"]: r for r in factual["items"]}
    for recipe in value["recipes"]:
        recipe["sources"] = sorted(set(factual_rows[recipe["id"]]["sources"]))
    value.pop("kind")
    value["candidate_sha256"] = sha
    value["reviews"] = [
        {"role": role, "reviewer": review["reviewer"], "candidate_sha256": sha,
         "sha256": file_sha(path)}
        for path, role, review in ((factual_path, "factual", factual),
                                   (quality_path, "quality", quality))
    ]
    audit(value)
    return value


def confirm_final_reviews(catalog: dict, audit_path: Path,
                          factual_path: Path, quality_path: Path) -> None:
    """Bind two final judgments to the exact catalog and current reviewed runtime."""
    audit_sha = file_sha(audit_path)
    live = json.loads(audit_path.read_bytes())
    catalog_sha = hashlib.sha256(json_bytes(catalog)).hexdigest()
    require(isinstance(live, dict) and live.get("catalog_sha256") == catalog_sha,
            "live audit catalog binding differs")
    expected = [{"path": path, "sha256": file_sha(ROOT / path)} for path in RUNTIME_SOURCES]
    actual = live.get("runtime_sources")
    require(isinstance(actual, list) and all(isinstance(v, dict) for v in actual)
            and sorted(actual, key=lambda v: v.get("path", "")) == sorted(
                expected, key=lambda v: v["path"]), "stale or incomplete runtime audit sources")
    require(live.get("verdict") == "accept", "live runtime audit did not accept")
    semantic = {r["role"]: r for r in catalog["reviews"]}
    for role, path in (("factual", factual_path), ("quality", quality_path)):
        review = json.loads(path.read_bytes())
        require(isinstance(review, dict) and review.get("kind") == FINAL_REVIEW_KIND
                and review.get("role") == role, f"{role}: invalid final review")
        require(review.get("reviewer") == semantic[role]["reviewer"],
                f"{role}: final reviewer differs from semantic reviewer")
        require(review.get("catalog_sha256") == catalog_sha
                and review.get("audit_sha256") == audit_sha,
                f"{role}: stale final catalog/audit binding")
        require(review.get("verdict") == "accept" and isinstance(review.get("rationale"), str)
                and review["rationale"].strip(), f"{role}: final acceptance required")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--generate-candidate", action="store_true")
    parser.add_argument("--factual-review", type=Path)
    parser.add_argument("--quality-review", type=Path)
    parser.add_argument("--proposal", type=Path)
    parser.add_argument("--audit", type=Path)
    parser.add_argument("--live-audit", type=Path)
    parser.add_argument("--final-factual-review", type=Path)
    parser.add_argument("--final-quality-review", type=Path)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    if args.audit:
        require(args.audit.resolve() != CATALOG.resolve(), "audit cannot replace package")
    if args.generate_candidate:
        require(not args.write and not args.factual_review and not args.quality_review,
                "candidate generation cannot publish")
        value = candidate()
        require(args.candidate.resolve() != CATALOG.resolve(), "candidate cannot replace package")
        atomic_write(args.candidate, json_bytes(value))
    else:
        require(args.factual_review is not None and args.quality_review is not None,
                "two complete bound reviews required")
        value = build_catalog(args.candidate, args.factual_review, args.quality_review)
        if args.proposal:
            require(args.proposal.resolve() != CATALOG.resolve(), "use --write to publish")
            atomic_write(args.proposal, json_bytes(value))
        if args.write:
            require(args.live_audit is not None and args.final_factual_review is not None
                    and args.final_quality_review is not None,
                    "package write requires live audit and two final reviews")
            confirm_final_reviews(value, args.live_audit, args.final_factual_review,
                                  args.final_quality_review)
            atomic_write(CATALOG, json_bytes(value))
    result = audit(value)
    if args.audit:
        atomic_write(args.audit, json_bytes(result))
    print(json.dumps({k: v for k, v in result.items() if k != "closure_rounds"}))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, KeyError, TypeError) as exc:
        raise SystemExit(f"discovery world rejected: {exc}") from exc
