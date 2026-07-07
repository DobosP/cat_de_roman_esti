#!/usr/bin/env python3
"""Review queued user submissions and promote accepted ones into the games pack.

The submissions endpoint (``/api/submissions``) appends pending items to
``$CAT_SUBMISSIONS_DIR/submissions.jsonl``; nothing a player sends is ever served
directly. This tool is the human/AI review step of the pipeline (ADR-0011):

    python scripts/review_submissions.py list   [--dir DIR]
    python scripts/review_submissions.py promote ID [ID...] [--dir DIR]
    python scripts/review_submissions.py reject  ID [ID...] [--dir DIR]

``promote`` re-validates each item (same rules as the server), writes it —
``status: approved``, ``source: user`` — into BOTH bundled pack copies, refreshes
``meta.counts``, then runs the full pack validator and ROLLS BACK both copies if
it fails (the densify_content.py idiom). ``reject`` moves items to
``submissions-rejected.jsonl`` for the audit trail.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))

import validate_games_pack  # noqa: E402  (sibling script)

from cat_de_roman_esti.wordgames.packs import GAME_KINDS, validate_pack_item  # noqa: E402

QUEUE_NAME = "submissions.jsonl"
REJECTED_NAME = "submissions-rejected.jsonl"
PACK_COPIES = (validate_games_pack.PACKAGE_PACK, validate_games_pack.TESTS_PACK)


def _queue_dir(arg: str | None) -> Path:
    raw = arg or os.environ.get("CAT_SUBMISSIONS_DIR")
    if not raw:
        raise SystemExit("no submissions dir: pass --dir or set CAT_SUBMISSIONS_DIR")
    return Path(raw)


def _read_queue(qdir: Path) -> list[dict]:
    qfile = qdir / QUEUE_NAME
    if not qfile.exists():
        return []
    entries = []
    for line in qfile.read_text(encoding="utf-8").splitlines():
        if line.strip():
            entries.append(json.loads(line))
    return entries


def _write_queue(qdir: Path, entries: list[dict]) -> None:
    text = "".join(json.dumps(e, ensure_ascii=False) + "\n" for e in entries)
    (qdir / QUEUE_NAME).write_text(text, encoding="utf-8")


def cmd_list(qdir: Path) -> int:
    entries = _read_queue(qdir)
    if not entries:
        print("queue empty")
        return 0
    for entry in entries:
        item = entry["item"]
        errors = validate_pack_item(dict(item), entry["game"])
        verdict = "VALID" if not errors else f"INVALID ({'; '.join(errors)})"
        author = entry.get("author") or "-"
        print(f"{item['id']}  {entry['game']:<9} {item['category']:<15} "
              f"{item['difficulty']:<6} by {author:<12} {verdict}")
    return 0


def cmd_promote(qdir: Path, ids: list[str]) -> int:
    entries = _read_queue(qdir)
    chosen = [e for e in entries if e["item"]["id"] in ids]
    missing = set(ids) - {e["item"]["id"] for e in chosen}
    if missing:
        raise SystemExit(f"not in queue: {sorted(missing)}")

    accepted: list[tuple[str, dict]] = []
    for entry in chosen:
        item = dict(entry["item"])
        item["status"] = "approved"
        item["source"] = "user"
        errors = validate_pack_item(item, entry["game"])
        if errors:
            raise SystemExit(f"{item['id']} fails validation: {errors}")
        accepted.append((entry["game"], item))

    originals = {copy: copy.read_bytes() for copy in PACK_COPIES}
    for copy in PACK_COPIES:
        pack = json.loads(originals[copy].decode("utf-8"))
        for game, item in accepted:
            pack[game].append(item)
        pack["meta"]["counts"] = {g: len(pack[g]) for g in GAME_KINDS}
        copy.write_text(json.dumps(pack, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    if validate_games_pack.main(["validate_games_pack.py"]) != 0:
        for copy, blob in originals.items():
            copy.write_bytes(blob)
        raise SystemExit("pack validation failed after merge — ROLLED BACK both copies")

    promoted_ids = {item["id"] for _game, item in accepted}
    _write_queue(qdir, [e for e in entries if e["item"]["id"] not in promoted_ids])
    print(f"promoted {sorted(promoted_ids)} into both pack copies (validator green)")
    return 0


def cmd_reject(qdir: Path, ids: list[str]) -> int:
    entries = _read_queue(qdir)
    keep, rejected = [], []
    for entry in entries:
        (rejected if entry["item"]["id"] in ids else keep).append(entry)
    if not rejected:
        raise SystemExit(f"not in queue: {sorted(ids)}")
    with (qdir / REJECTED_NAME).open("a", encoding="utf-8") as fh:
        for entry in rejected:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    _write_queue(qdir, keep)
    print(f"rejected {[e['item']['id'] for e in rejected]} (kept in {REJECTED_NAME})")
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("list", "promote", "reject"))
    parser.add_argument("ids", nargs="*")
    parser.add_argument("--dir", dest="dir", default=None)
    args = parser.parse_args(argv[1:])
    qdir = _queue_dir(args.dir)
    if args.command == "list":
        return cmd_list(qdir)
    if not args.ids:
        raise SystemExit(f"{args.command} needs at least one submission id")
    if args.command == "promote":
        return cmd_promote(qdir, args.ids)
    return cmd_reject(qdir, args.ids)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
