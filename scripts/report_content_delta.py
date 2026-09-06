#!/usr/bin/env python3
"""Report content changes from a Git baseline to the working tree, using only stdlib.

Usage: python scripts/report_content_delta.py --baseline HEAD [--text]

This inventories authored records, not code churn or semantic-distance changes.
Aliases are exact (owner, form) pairs; their data does not distinguish synonyms
from inflections. Node comparisons exclude aliases, which have their own section.
Ranking eligibility is the sidecar's declaration, not a runtime validation result.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

FIXTURES = "cat_de_roman_esti/fixtures/"
FILES = {
    "kg": FIXTURES + "kg_sample.json",
    "pack": FIXTURES + "games_pack.json",
    "derived": FIXTURES + "derived_catalog_v38.json",
    "rankings": FIXTURES + "board_rankings_v37.json",
}
PACK_GAMES = ("conexiuni", "contexto", "lant", "alchimie")
DERIVED_GAMES = ("intrusul", "perechi")


def index_rows(rows: list, label: str) -> dict[str, dict]:
    """Reject ambiguous IDs rather than silently undercounting a malformed file."""
    if not isinstance(rows, list):
        raise ValueError(f"{label}: expected a list")
    indexed = {}
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("id"), str) or not row["id"]:
            raise ValueError(f"{label}: every record needs a nonempty string id")
        if row["id"] in indexed:
            raise ValueError(f"{label}: duplicate id {row['id']!r}")
        indexed[row["id"]] = row
    return indexed


def inventory(documents: dict[str, dict | None]) -> dict:
    """Build stable-identity inventories without importing either version's runtime."""
    kg, pack = documents["kg"], documents["pack"]
    if kg is None or pack is None:
        raise ValueError("KG and games pack are required")
    nodes = index_rows(kg["kg_nodes"], "nodes")
    forms = {}
    for node_id, node in nodes.items():
        aliases = node.get("aliases", [])
        if not isinstance(aliases, list) or any(not isinstance(form, str) for form in aliases):
            raise ValueError(f"nodes: {node_id!r} aliases must be a list of strings")
        for form in aliases:
            key = (node_id, form)
            if key in forms:
                raise ValueError(f"nodes: duplicate form {key!r}")
            forms[key] = form
    derived = index_rows((documents.get("derived") or {}).get("boards", []), "derived")
    if any(row.get("game") not in DERIVED_GAMES for row in derived.values()):
        raise ValueError("derived: unknown game")
    ranking_doc = documents.get("rankings")
    rankings = (
        index_rows(ranking_doc["boards"], "rankings") if ranking_doc is not None else None
    )
    result = {
        "concepts": {
            node_id: {key: value for key, value in node.items() if key != "aliases"}
            for node_id, node in nodes.items()
        },
        "connections": index_rows(kg["kg_edges"], "connections"),
        "forms": forms,
        "puzzles": index_rows(kg["kg_puzzles"], "puzzles"),
        "pack": {},
        "derived": {},
    }
    pack_ids = set()
    for game in PACK_GAMES:
        records = index_rows(pack.get(game, []), game)
        if pack_ids & records.keys():
            raise ValueError("pack: record ids must be unique across games")
        pack_ids.update(records)
        approved = {key: True for key, row in records.items() if row.get("status") == "approved"}
        eligible = None
        if rankings is not None:
            eligible = {}
            for key, row in records.items():
                rank = rankings.get(key, {})
                if (rank.get("game"), rank.get("status")) != (game, row.get("status")):
                    raise ValueError(f"rankings: missing or mismatched identity/status for {key!r}")
                if not isinstance(rank.get("pilot_eligible"), bool):
                    raise ValueError(f"rankings: invalid eligibility for {key!r}")
                if rank["pilot_eligible"]:
                    if key not in approved:
                        raise ValueError(f"rankings: non-approved eligible record {key!r}")
                    eligible[key] = True
        result["pack"][game] = {
            "records": records, "approved": approved, "declared_ranked_eligible": eligible,
        }
    if rankings is not None and pack_ids != rankings.keys():
        raise ValueError("rankings: ids must cover exactly the games pack")
    for game in DERIVED_GAMES:
        result["derived"][game] = {
            key: row for key, row in derived.items() if row["game"] == game
        }
    return result


def record_delta(before: dict, after: dict) -> dict:
    """Keep reports compact: IDs for differences, counts and flags for preservation."""
    retained = before.keys() & after.keys()
    changed = sorted(key for key in retained if before[key] != after[key])
    added, removed = sorted(after.keys() - before.keys()), sorted(before.keys() - after.keys())
    return {
        "before_count": len(before), "after_count": len(after),
        "added_count": len(added), "removed_count": len(removed),
        "changed_count": len(changed), "retained_count": len(retained),
        "unchanged_count": len(retained) - len(changed),
        "all_baseline_ids_retained": not removed,
        "all_baseline_records_unchanged": not removed and not changed,
        "added_ids": added, "removed_ids": removed, "changed_ids": changed,
    }


def compare(before: dict, after: dict) -> dict:
    report = {
        key: record_delta(before[key], after[key])
        for key in ("concepts", "connections", "forms", "puzzles")
    }
    report["pack"] = {}
    for game in PACK_GAMES:
        report["pack"][game] = {}
        for kind in ("records", "approved", "declared_ranked_eligible"):
            old, new = before["pack"][game][kind], after["pack"][game][kind]
            report["pack"][game][kind] = (
                record_delta(old, new) if old is not None and new is not None else None
            )
    report["derived"] = {
        game: record_delta(before["derived"][game], after["derived"][game])
        for game in DERIVED_GAMES
    }
    return report


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True,
        encoding="utf-8", check=False, timeout=30,
    )
    if result.returncode:
        raise ValueError(f"Git {args[0]} failed: {result.stderr.strip()}")
    return result.stdout


def load_documents(repo: Path, commit: str | None) -> dict[str, dict | None]:
    documents = {}
    for key, path in FILES.items():
        if commit is None:
            text = (repo / path).read_text(encoding="utf-8") if (repo / path).exists() else None
        elif git(repo, "ls-tree", "--name-only", commit, "--", path).strip():
            text = git(repo, "show", f"{commit}:{path}")
        else:
            text = None
        if text is None and key in ("kg", "pack"):
            raise ValueError(f"Missing required {path} in {commit or 'working tree'}")
        document = json.loads(text) if text is not None else None
        if document is not None and not isinstance(document, dict):
            raise ValueError(f"{path}: expected a JSON object")
        documents[key] = document
    return documents


def text_report(report: dict) -> str:
    lines = [f"Content delta: {report['baseline_commit']} -> working tree"]

    def line(label: str, delta: dict | None) -> None:
        if delta is None:
            lines.append(f"{label}: unavailable (ranking sidecar missing in one snapshot)")
        else:
            lines.append(
                f"{label}: {delta['before_count']} -> {delta['after_count']}; "
                f"+{delta['added_count']} -{delta['removed_count']} "
                f"changed {delta['changed_count']}; unchanged {delta['unchanged_count']}"
            )

    for key in ("concepts", "connections", "forms", "puzzles"):
        line(key, report[key])
    for game, sections in report["pack"].items():
        for kind, delta in sections.items():
            line(f"{game} {kind}", delta)
    for game, delta in report["derived"].items():
        line(f"{game} frozen boards", delta)
    lines.extend(report["notes"])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", default="HEAD", help="Git commit/ref (default: HEAD)")
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    output = parser.add_mutually_exclusive_group()
    output.add_argument("--json", action="store_true", help="JSON output (the default)")
    output.add_argument(
        "--text", action="store_true", help="Concise totals; JSON includes stable IDs"
    )
    args = parser.parse_args(argv)
    try:
        if not args.baseline or args.baseline.startswith("-") or "\x00" in args.baseline:
            raise ValueError("Baseline must be a Git commit/ref, not an option")
        commit = git(
            args.repo, "rev-parse", "--verify", "--end-of-options", f"{args.baseline}^{{commit}}"
        ).strip()
        report = compare(
            inventory(load_documents(args.repo, commit)),
            inventory(load_documents(args.repo, None)),
        )
    except (OSError, ValueError, KeyError, subprocess.TimeoutExpired) as exc:
        print(f"Content delta failed: {exc}", file=sys.stderr)
        return 2
    report.update({
        "schema_version": 1,
        "baseline_ref": args.baseline,
        "baseline_commit": commit,
        "comparison": "working_tree",
        "synonyms": {"count": None, "reason": "Alias data does not classify true synonyms."},
        "notes": [
            "Forms are exact [node_id, form] pairs, not necessarily new concepts or synonyms.",
            "Concept changes exclude aliases; other record fields are compared exactly.",
            "Approved additions include new records and promotions of existing records.",
            "Ranked eligibility is declared by the sidecar; run content/runtime gates separately.",
            "Missing historical derived catalogs count as zero; missing rankings are unknown.",
        ],
    })
    print(text_report(report) if args.text else json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
