#!/usr/bin/env python3
"""Report content changes from a Git baseline to a commit or the working tree.

Usage: python scripts/report_content_delta.py --baseline BASE [--head HEAD] [--text]

This inventories authored records, not code churn or semantic-distance changes.
Aliases are exact (owner, form) pairs; their data does not distinguish synonyms
from inflections. Node comparisons exclude aliases, which have their own section.
Ranking eligibility is the sidecar's declaration, not a runtime validation result.

The campaign section compares the Go serving exports and their pinned sources.
It counts separate installed concepts, names, normalized aliases, relationships,
new selectable authored boards, and first explicit board appearances by game.
The forms and links target counters follow ADR-0231. The all_new_forms and
all_new_links summaries preserve the full installed additions.
See campaign_delta for the exact rules. Campaign metrics default to local main.
An explicit --head selects a comparison commit without attesting to landing.

Threat model: a trusted operator supplies the local repository and refs. Git
receives literal arguments and reads named blobs only. Files are treated as
data; no candidate code, receipt paths, or URLs are executed or followed.
Bundle, pin and source digests catch accidental stale exports; a party able to
alter all three can forge consistency. The report cannot prove source evidence,
gate approval, or release. Keep it private: board targets and forms can reveal
answers. A working tree comparison assumes no concurrent content installation.
Use new_forms and new_links for campaign targets. The broader summaries include
additions that could inflate those targets, such as forms on new words or recipes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath

FIXTURES = "cat_de_roman_esti/fixtures/"
FILES = {
    "kg": FIXTURES + "kg_sample.json",
    "pack": FIXTURES + "games_pack.json",
    "derived": FIXTURES + "derived_catalog_v38.json",
    "quick": FIXTURES + "quick_games_v92.json",
    "rankings": FIXTURES + "board_rankings_v37.json",
}
PACK_GAMES = ("conexiuni", "contexto", "lant", "alchimie")
DERIVED_GAMES = ("intrusul", "perechi")
GAMES = PACK_GAMES + DERIVED_GAMES
BUNDLE = "go-backend/internal/content/bundled.json"
BUNDLE_PIN = "go-backend/internal/content/digest.go"
REGISTRY = "docs/content-registry/registry.jsonl"
CAMPAIGN_SOURCES = (
    *FILES.values(),
    FIXTURES + "release_reserve_v1.json",
    FIXTURES + "alchimie_discovery_world_v92.json",
    FIXTURES + "alchimie_recipe_extensions_v92.json",
)
EXAMPLE_LIMIT = 5


class CampaignUnavailable(ValueError):
    """A historical or stale snapshot cannot support installed-content counts."""


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
    quick = index_rows((documents.get("quick") or {}).get("boards", []), "quick")
    if derived.keys() & quick.keys():
        raise ValueError("quick: board ids collide with the frozen catalog")
    derived.update(quick)
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


def git_bytes(repo: Path, *args: str) -> bytes:
    result = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, check=False, timeout=30,
    )
    if result.returncode:
        message = result.stderr.decode("utf-8", errors="replace").strip()
        raise ValueError(f"Git {args[0]} failed: {message}")
    return result.stdout


def git(repo: Path, *args: str) -> str:
    return git_bytes(repo, *args).decode("utf-8")


def read_snapshot(repo: Path, commit: str | None, path: str) -> bytes | None:
    if commit is None:
        try:
            file_path = (repo / path).resolve(strict=True)
            if not file_path.is_relative_to(repo.resolve()):
                raise ValueError(f"Working tree input escapes repository: {path}")
            return file_path.read_bytes()
        except FileNotFoundError:
            return None
    if git(repo, "ls-tree", "--name-only", commit, "--", path).strip():
        return git_bytes(repo, "show", f"{commit}:{path}")
    return None


def load_documents(repo: Path, commit: str | None) -> dict[str, dict | None]:
    documents = {}
    for key, path in FILES.items():
        raw = read_snapshot(repo, commit, path)
        if raw is None and key in ("kg", "pack"):
            raise ValueError(f"Missing required {path} in {commit or 'working tree'}")
        document = json.loads(raw) if raw is not None else None
        if document is not None and not isinstance(document, dict):
            raise ValueError(f"{path}: expected a JSON object")
        documents[key] = document
    return documents


def campaign_bundle(repo: Path, commit: str | None) -> dict:
    where = commit or "working tree"
    raw = read_snapshot(repo, commit, BUNDLE)
    if raw is None:
        raise CampaignUnavailable(f"{where}: serving export missing")
    bundle = json.loads(raw)
    if not isinstance(bundle, dict) or bundle.get("schema_version") != 2:
        raise CampaignUnavailable(f"{where}: unsupported serving export schema")
    sources = bundle.get("sources")
    source_paths = {PurePosixPath(path).name: path for path in CAMPAIGN_SOURCES}
    if not isinstance(sources, dict) or source_paths.keys() - sources.keys():
        raise CampaignUnavailable(f"{where}: serving export predates the V5 source set")
    pin = re.search(
        rb'^const bundledSHA256 = "([0-9a-f]{64})"\r?$',
        read_snapshot(repo, commit, BUNDLE_PIN) or b"",
        re.MULTILINE,
    )
    if pin is None or pin[1].decode("ascii") != hashlib.sha256(raw).hexdigest():
        raise CampaignUnavailable(f"{where}: serving export digest does not match its pin")
    for name, path in source_paths.items():
        source = read_snapshot(repo, commit, path)
        if source is None:
            raise CampaignUnavailable(f"{where}: serving export source missing: {path}")
        # Match native contentbuild.TextSHA256 on both blobs and checkout files.
        source_hash = hashlib.sha256(source.replace(b"\r\n", b"\n").replace(b"\r", b"\n")).hexdigest()
        if sources[name] != source_hash:
            raise CampaignUnavailable(f"{where}: serving export is stale for {path}")
    return bundle


def landed_names(repo: Path, commit: str, new_ids: set[str]) -> set[str]:
    if not new_ids:
        return set()
    raw = read_snapshot(repo, commit, REGISTRY)
    if raw is None:
        return set()
    latest = {}
    for line in raw.splitlines():
        row = json.loads(line)
        if row.get("schema") != "cat-content-candidate-1":
            raise ValueError("Registry: unknown candidate schema")
        if row["type"] == "name":
            latest[row["id"]] = row
    result = set()
    for row in latest.values():
        if row["state"] != "landed":
            continue
        owner = row["identity"].get("owner_id")
        installed = row["payload"].get("node_id")
        if owner and installed and owner != installed:
            raise ValueError(f"Registry: conflicting node IDs for {row['id']}")
        node_id = owner or installed
        if node_id is None:
            continue
        if not isinstance(node_id, str) or not node_id:
            raise ValueError(f"Registry: invalid installed node ID for {row['id']}")
        if node_id in new_ids:
            result.add(node_id)
    return result


def group_ids(rows) -> tuple:
    return tuple(sorted(tuple(sorted(ids)) for ids in rows))


def board_roles(game: str, payload: dict) -> tuple[tuple, set[str]]:
    """Return a player-facing identity and the explicit concept IDs it exposes."""
    if not isinstance(payload, dict):
        raise ValueError(f"Invalid board payload for {game}")
    target = payload.get("target")
    if game == "contexto":
        return (target,), {target}
    if game == "lant":
        return (payload["start"], target), {payload["start"], target}
    if game == "alchimie":
        seeds = tuple(sorted(payload["seeds"]))
        return (seeds, target), {*seeds, target}
    if game == "conexiuni":
        groups = group_ids(payload["groups"].values())
        return groups, {node for group in groups for node in group}
    if game == "intrusul":
        members = tuple(sorted(payload["members"]))
        return (members, payload["intruder"]), {*members, payload["intruder"]}
    pairs = group_ids(row["members"] for row in payload["pairs"])
    return pairs, {node for pair in pairs for node in pair}


def reachable_quick_ids(rows: list[dict]) -> set[str]:
    """Find Quick boards reachable through category, starter or four-source history."""
    regular = {}
    starter = {}
    for row in rows:
        require_fields = (row["game"], row["category"], row["source_id"], row["catalog_id"])
        if (not all(isinstance(field, str) and field for field in require_fields)
                or type(row["overall_score"]) is not int or type(row["starter_safe"]) is not bool):
            raise ValueError("Serving export: invalid Quick selection metadata")
        if row["overall_score"] >= 55:
            shelf = (row["game"], row["category"])
            regular.setdefault(shelf, set()).add(row["source_id"])
            if row["starter_safe"]:
                starter.setdefault(shelf, set()).add(row["source_id"])
    ids = set()
    for row in rows:
        shelf = (row["game"], row["category"])
        source = row["source_id"]
        common = regular.get(shelf, set())
        safe = starter.get(shelf, set())
        if (row["overall_score"] >= 55 or (len(common) <= 4 and source not in common)
                or (row["starter_safe"] and len(safe) <= 4 and source not in safe)):
            ids.add(row["catalog_id"])
    return ids


def selectable_boards(bundle: dict, node_ids: set[str]) -> dict[str, dict]:
    boards = {game: {} for game in GAMES}
    ranked = bundle["pack_ranked"]
    if not isinstance(ranked, bool):
        raise ValueError("Serving export: invalid pack_ranked")
    reachable_quick = reachable_quick_ids(bundle["boards"])
    for field, games, id_field in (
        ("pack_items", PACK_GAMES, "id"), ("boards", DERIVED_GAMES, "catalog_id"),
    ):
        seen = set()
        for row in bundle[field]:
            game, board_id = row["game"], row[id_field]
            if (game not in games or not isinstance(board_id, str)
                    or not board_id or board_id in seen):
                raise ValueError(f"Serving export: invalid or repeated board {board_id!r}")
            seen.add(board_id)
            if field == "pack_items":
                if row["status"] != "approved" or not isinstance(row["pilot_eligible"], bool):
                    raise ValueError(f"Serving export: invalid pack board {board_id!r}")
                if ranked and not row["pilot_eligible"]:
                    continue
            elif board_id not in reachable_quick:
                continue
            signature, words = board_roles(game, row["payload"])
            if not words or not words <= node_ids:
                raise ValueError(f"Serving export: missing board nodes for {board_id!r}")
            boards[game][board_id] = signature, words
    return boards


def authored_boards(inventory: dict, game: str) -> dict:
    if game in PACK_GAMES:
        return inventory["pack"][game]["records"]
    return {key: row["payload"] for key, row in inventory["derived"][game].items()}


def summary(items: list) -> dict:
    return {"count": len(items), "examples": items[:EXAMPLE_LIMIT]}


def transform(text: str, mapping: dict) -> str:
    return " ".join("".join(mapping.get(char, char) for char in text).split())


def reviewed_unresolved(form: str, bundle: dict) -> bool:
    # Matches graph.Service.ReviewedUnresolved's reviewed ambiguous-input exclusions.
    key = transform(form, bundle["accent_normalization_map"]).replace("\u0327", "\u0326")
    return key in ("pas\u0326te", "pas\u0326tele")


def new_forms(before: dict, after: dict, nodes: dict) -> list:
    normalization = after["normalization_map"]
    index = after["normalized_index"]
    old_normalization = before["normalization_map"]
    old_index = before["normalized_index"]
    forms = {}
    for node_id, node in nodes.items():
        label = node["label_ro"]
        primary = {transform(label, normalization), transform(node_id, normalization)}
        for form in sorted(node["aliases"] or []):
            key = transform(form, normalization)
            if key in primary or index.get(key) != node_id or reviewed_unresolved(form, after):
                continue
            old_key = transform(form, old_normalization)
            if old_index.get(old_key) == node_id and not reviewed_unresolved(form, before):
                continue
            forms.setdefault(
                (node_id, key), {"node_id": node_id, "label_ro": label, "form": form},
            )
    return [forms[key] for key in sorted(forms)]


def relationship_links(bundle: dict) -> dict:
    links = {}
    for edge in bundle["edges"]:
        if not edge["is_distractor"]:
            pair = sorted((edge["src_id"], edge["dst_id"]))
            key = (*pair, edge["relation"])
            links[key] = {"kind": "kg", "node_ids": pair, "relation": edge["relation"]}
    return links


def recipe_links(bundle: dict, active_rounds: dict) -> dict:
    links = {}
    recipes = list(bundle["discovery_world"]["recipes"])
    for row in bundle["recipe_extensions"]["boards"]:
        if row["id"] in active_rounds:
            recipes.extend(row["additions"])
    for recipe in recipes:
        pair = sorted(recipe["pair"])
        result = recipe["result"]
        links[(*pair, result)] = {"kind": "alchimie_recipe", "pair": pair, "result": result}
    return links


def additions(before: dict, after: dict) -> list:
    return [after[key] for key in sorted(after.keys() - before.keys())]


def campaign_delta(before: dict, after: dict, before_sources: dict, names: set[str]) -> dict:
    """Count net additions across snapshots, using the shared graph and explicit board roles.

    New words are new concept IDs. Names require the landed registry's explicit
    node binding because entity types also describe generic ideas. Old label or
    alias matches and new non-concept nodes without a name binding are unclassified.
    Forms are unique normalized aliases that now resolve to their owner and did
    not resolve to that owner at baseline. The metric cannot classify morphology
    versus synonymy. The forms target counts only aliases of baseline concepts.

    A board needs a new ID and a new role assignment relative to all authored stock
    at baseline, including ineligible or reserved stock. A changed assignment on an
    existing ID may contribute first exposures of baseline KG IDs, including names.
    First exposures compare the two selectable inventories, not historical plays.
    Count graph links by unordered pair/relation (the installer's key), and
    recipes by unordered ingredients/result. Only graph
    links touching at least one counted new word contribute to the links target.
    Captions, edge directions and metadata have their own diffs. Recipes cover the
    legacy discovery API and declared extensions on selectable rounds; native
    qualification proves the extensions actually apply. Procedurally selected roles and indirect
    exposure through guesses, hops, recipe results and the legacy world are outside
    the board exposure metric.
    """
    old_nodes = index_rows(before["nodes"], "baseline serving nodes")
    nodes = index_rows(after["nodes"], "serving nodes")
    new_words, new_names, unclassified = [], [], []
    norm = after["normalization_map"]
    old_labels = {
        transform(label, norm)
        for row in old_nodes.values()
        for label in [row["label_ro"], *(row["aliases"] or [])]
    }
    for node_id in sorted(nodes.keys() - old_nodes.keys()):
        node = nodes[node_id]
        label = node["label_ro"]
        record = {"id": node_id, "label_ro": label, "node_type": node["node_type"]}
        if transform(label, norm) in old_labels:
            unclassified.append(record)
        elif node_id in names:
            new_names.append(record)
        elif node["node_type"] == "concept":
            new_words.append(record)
        else:
            unclassified.append(record)

    old_boards = selectable_boards(before, old_nodes.keys())
    boards = selectable_boards(after, nodes.keys())
    authored = {game: authored_boards(before_sources, game) for game in GAMES}
    known_ids = {key for game in GAMES for key in authored[game].keys() | old_boards[game].keys()}
    new_boards, first_exposures = {}, {}
    for game in GAMES:
        known_boards = {board_roles(game, row)[0] for row in authored[game].values()}
        known_boards.update(signature for signature, _ in old_boards[game].values())
        added = []
        for board_id, (signature, _) in sorted(boards[game].items()):
            if board_id not in known_ids and signature not in known_boards:
                added.append({"id": board_id})
                known_boards.add(signature)
        new_boards[game] = summary(added)
        old_exposed = {node for _, words in old_boards[game].values() for node in words}
        exposed = {node for _, words in boards[game].values() for node in words}
        first_exposures[game] = summary([
            {"id": node, "label_ro": nodes[node]["label_ro"]}
            for node in sorted((exposed - old_exposed) & old_nodes.keys())
        ])

    baseline_words = {
        node_id for node_id, node in old_nodes.items() if node["node_type"] == "concept"
    }
    new_word_ids = {row["id"] for row in new_words}
    forms = new_forms(before, after, nodes)
    forms_on_baseline_words, forms_on_new_words, other_forms = [], [], []
    for form in forms:
        if form["node_id"] in baseline_words:
            forms_on_baseline_words.append(form)
        elif form["node_id"] in new_word_ids:
            forms_on_new_words.append(form)
        else:
            other_forms.append(form)

    kg_links = additions(relationship_links(before), relationship_links(after))
    links_to_new_words, links_between_existing_words, other_kg_links = [], [], []
    for link in kg_links:
        if not new_word_ids.isdisjoint(link["node_ids"]):
            links_to_new_words.append(link)
        elif baseline_words.issuperset(link["node_ids"]):
            links_between_existing_words.append(link)
        else:
            other_kg_links.append(link)
    recipes = additions(
        recipe_links(before, old_boards["alchimie"]), recipe_links(after, boards["alchimie"]),
    )
    return {
        "new_words": summary(new_words),
        "new_names": summary(new_names),
        "new_forms": summary(forms_on_baseline_words),
        "new_word_forms": summary(forms_on_new_words),
        "other_new_forms": summary(other_forms),
        "all_new_forms": summary(forms),
        "new_links": summary(links_to_new_words),
        "links_between_existing_words": summary(links_between_existing_words),
        "other_new_kg_links": summary(other_kg_links),
        "all_new_links": summary(kg_links + recipes),
        "new_links_by_kind": {"kg": summary(kg_links), "alchimie_recipe": summary(recipes)},
        "new_boards": new_boards,
        "first_exposures": first_exposures,
        "unclassified_new_entities": summary(unclassified),
    }


def resolve_commit(repo: Path, ref: str) -> str:
    if not ref or ref.startswith("-") or "\x00" in ref:
        raise ValueError("Reference must be a Git commit/ref, not an option")
    return git(repo, "rev-parse", "--verify", "--end-of-options", f"{ref}^{{commit}}").strip()


def text_report(report: dict) -> str:
    lines = []
    campaign = report["campaign"]
    if campaign is None:
        lines.append(f"Campaign metrics unavailable ({report['campaign_unavailable']})")
    else:
        def count(label: str, result: dict) -> str:
            examples = ", ".join(
                row.get("form") or row.get("label_ro") or row.get("result")
                or " ↔ ".join(row["node_ids"])
                for row in result["examples"]
            )
            return f"{label} +{result['count']}" + (f" ({examples})" if examples else "")

        lines.append(", ".join((
            count("words", campaign["new_words"]),
            count("forms on existing words", campaign["new_forms"]),
            count("names", campaign["new_names"]),
            count("links with a new word", campaign["new_links"]),
        )))
        lines.append(", ".join((
            count("forms on new words", campaign["new_word_forms"]),
            count("forms on other entities", campaign["other_new_forms"]),
        )))
        lines.append(", ".join((
            count("links between existing words", campaign["links_between_existing_words"]),
            count("other KG links", campaign["other_new_kg_links"]),
            count("Alchimie recipes", campaign["new_links_by_kind"]["alchimie_recipe"]),
        )))
        for key in ("new_boards", "first_exposures"):
            totals = ", ".join(f"{game} +{value['count']}" for game, value in campaign[key].items())
            lines.append(f"{key.replace('_', ' ')}: {totals}")
    destination = report.get("head_commit", "working tree")
    lines.append(f"Content delta: {report['baseline_commit']} -> {destination}")

    def line(label: str, delta: dict | None) -> None:
        if delta is None:
            lines.append(f"{label}: unavailable (ranking sidecar missing in one snapshot)")
        else:
            lines.append(
                f"{label}: {delta['before_count']} -> {delta['after_count']}; "
                f"+{delta['added_count']} -{delta['removed_count']} "
                f"changed {delta['changed_count']}; unchanged {delta['unchanged_count']}"
            )

    if "authored_inventory_unavailable" in report:
        lines.append(f"Authored inventory unavailable ({report['authored_inventory_unavailable']})")
    else:
        for key in ("concepts", "connections", "forms", "puzzles"):
            line(key, report[key])
        for game, sections in report["pack"].items():
            for kind, delta in sections.items():
                line(f"{game} {kind}", delta)
        for game, delta in report["derived"].items():
            line(f"{game} catalog boards", delta)
    lines.extend(report["notes"])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", default="HEAD", help="Git commit/ref (default: HEAD)")
    parser.add_argument("--head", help="Compare a Git commit/ref instead of the working tree")
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    output = parser.add_mutually_exclusive_group()
    output.add_argument("--json", action="store_true", help="JSON output (the default)")
    output.add_argument(
        "--text", action="store_true", help="Concise totals; JSON includes stable IDs"
    )
    args = parser.parse_args(argv)
    try:
        commit = resolve_commit(args.repo, args.baseline)
        head = resolve_commit(args.repo, args.head) if args.head is not None else None
        before_sources = inventory(load_documents(args.repo, commit))
        try:
            after_sources = inventory(load_documents(args.repo, head))
            report = compare(before_sources, after_sources)
        except (OSError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired) as exc:
            if head is not None:
                raise
            report = {"authored_inventory_unavailable": str(exc)}
        try:
            before_bundle = campaign_bundle(args.repo, commit)
            try:
                campaign_head = head or resolve_commit(args.repo, "refs/heads/main")
            except ValueError as exc:
                raise CampaignUnavailable("local main is unavailable") from exc
            report["campaign_head_commit"] = campaign_head
            report["campaign_comparison"] = "local_main" if head is None else "explicit_commit"
            after_bundle = campaign_bundle(args.repo, campaign_head)
            names = landed_names(
                args.repo, campaign_head,
                {node["id"] for node in after_bundle["nodes"]} - before_sources["concepts"].keys(),
            )
            report["campaign"] = campaign_delta(before_bundle, after_bundle, before_sources, names)
        except CampaignUnavailable as exc:
            report["campaign"] = None
            report["campaign_unavailable"] = str(exc)
    except (OSError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired) as exc:
        print(f"Content delta failed: {exc}", file=sys.stderr)
        return 2
    report.update({
        "schema_version": 1,
        "baseline_ref": args.baseline,
        "baseline_commit": commit,
        "comparison": "working_tree" if head is None else "commits",
        "synonyms": {"count": None, "reason": "Alias data does not classify true synonyms."},
        "notes": [
            "Forms are exact [node_id, form] pairs, not necessarily new concepts or synonyms.",
            "Concept changes exclude aliases; other record fields are compared exactly.",
            "Approved additions include new records and promotions of existing records.",
            "Ranked eligibility is declared by the sidecar; run content/runtime gates separately.",
            "Missing historical derived catalogs count as zero; missing rankings are unknown.",
            "Quick-game boards include the frozen V38 catalog and reviewed authored supplements.",
        ],
    })
    if head is not None:
        report["head_commit"] = head
    print(text_report(report) if args.text else json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
