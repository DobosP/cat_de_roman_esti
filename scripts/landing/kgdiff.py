#!/usr/bin/env python3
"""Compare committed nodes, edges, exact aliases and boards at two full SHAs."""
import argparse
import difflib
import json
from pathlib import Path
import sys
import unicodedata

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from report_content_delta import DERIVED_GAMES, PACK_GAMES, inventory, load_documents
from support import exact_commit, require


def fold(text):
    # Advisory neighbours use accent-insensitive word forms. The actual Go
    # resolver is exercised by play.py for each new exact alias.
    return "".join(c for c in unicodedata.normalize("NFD", text.strip().casefold())
                   if not unicodedata.combining(c))


def delta(before, after):
    changed = []
    for key in sorted(before.keys() & after.keys()):
        old, new = before[key], after[key]
        if old != new:
            fields = {field: {"before": old.get(field), "after": new.get(field)}
                      for field in sorted(old.keys() | new.keys())
                      if field not in old or field not in new or old[field] != new[field]}
            changed.append({"id": key, "fields": fields})
    return {
        "before_count": len(before), "after_count": len(after),
        "added": [after[key] for key in sorted(after.keys() - before.keys())],
        "removed": [before[key] for key in sorted(before.keys() - after.keys())],
        "changed": changed,
    }


def aliases(keys, nodes):
    return [{"id": owner, "label": nodes[owner]["label_ro"], "form": form}
            for owner, form in sorted(keys)]


def fold_index(data):
    indexed = {}
    for owner, row in data["concepts"].items():
        label = row["label_ro"]
        require(isinstance(label, str) and label, f"Empty label on {owner}")
        indexed.setdefault(fold(label), set()).add((owner, label))
    for owner, form in data["forms"]:
        indexed.setdefault(fold(form), set()).add((owner, form))
    return indexed


def neighbors(before, after, added_aliases, changed_labels):
    old, new = fold_index(before), fold_index(after)
    changed = [(row["id"], row["form"]) for row in added_aliases] + changed_labels

    def matches(query, owner, index):
        ranked = []
        for key, pairs in index.items():
            # The length ratio bounds SequenceMatcher's possible result.
            if not key or 2 * min(len(query), len(key)) < .85 * (len(query) + len(key)):
                continue
            other = sorted(pair for pair in pairs if pair[0] != owner)
            if other:
                score = difflib.SequenceMatcher(None, query, key, autojunk=False).ratio()
                if score >= .85:
                    ranked.append((-round(score, 4), key, other))
        return [{"fold": key, "similarity": -score, "owners": pairs}
                for score, key, pairs in sorted(ranked)[:8]]

    result = []
    for owner, label in sorted(set(changed)):
        query = fold(label)
        previous, current = matches(query, owner, old), matches(query, owner, new)
        if previous or current:
            result.append({"id": owner, "text": label, "before": previous, "after": current})
    return result


def compare_content(before_documents, after_documents, include_neighbors=True):
    before, after = inventory(before_documents), inventory(after_documents)
    concepts = delta(before["concepts"], after["concepts"])
    added_aliases = aliases(after["forms"].keys() - before["forms"].keys(), after["concepts"])
    removed_aliases = aliases(before["forms"].keys() - after["forms"].keys(), before["concepts"])
    boards = {}
    for game in PACK_GAMES:
        old, new = before["pack"][game], after["pack"][game]
        old_eligible, new_eligible = old["declared_ranked_eligible"], new["declared_ranked_eligible"]
        changes = delta(old["records"], new["records"])
        changes["eligibility"] = (
            {"added": sorted(new_eligible.keys() - old_eligible.keys()),
             "removed": sorted(old_eligible.keys() - new_eligible.keys())}
            if old_eligible is not None and new_eligible is not None else None
        )
        boards[game] = changes
    for game in DERIVED_GAMES:
        boards[game] = delta(before["derived"][game], after["derived"][game])
    report = {
        "schema": 1,
        "concepts": concepts,
        "edges": delta(before["connections"], after["connections"]),
        "legacy_puzzles": delta(before["puzzles"], after["puzzles"]),
        "aliases": {"added": added_aliases, "removed": removed_aliases},
        "boards": boards,
    }
    if include_neighbors:
        changed_labels = [(row["id"], row["label_ro"]) for row in concepts["added"]]
        changed_labels.extend((row["id"], row["fields"]["label_ro"]["after"])
                              for row in concepts["changed"] if "label_ro" in row["fields"])
        report["fuzzy_neighbors"] = neighbors(before, after, added_aliases, changed_labels)
    return report


def committed_delta(repo, baseline, sha, include_neighbors=True):
    exact_commit(repo, baseline)
    exact_commit(repo, sha)
    result = compare_content(load_documents(repo, baseline), load_documents(repo, sha), include_neighbors)
    return {"baseline": baseline, "sha": sha, **result}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--sha", required=True)
    args = parser.parse_args()
    try:
        result = committed_delta(args.repo.resolve(), args.baseline, args.sha)
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"Content diff failed: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
