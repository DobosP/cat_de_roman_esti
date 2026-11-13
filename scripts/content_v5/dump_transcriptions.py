#!/usr/bin/env python3
"""Compare two sealed raw-table transcriptions to proposed dump forms."""

import argparse
from datetime import date
import json
from pathlib import Path
import re
import sys
import unicodedata

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "landing"))
from support import digest, read_artifact, read_json, require

SHA = re.compile(r"[a-f0-9]{64}")
THREAD = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9_.:-]{0,127}")
ARCHIVE_URL = re.compile(
    r"https://dumps\.wikimedia\.org/rowiktionary/([0-9]{8})/"
    r"rowiktionary-\1-pages-articles\.xml\.bz2"
)
SOURCE_KEYS = {"archive_url", "archive_sha256", "archive_receipt_sha256",
               "title", "revision_id", "text_sha256"}
ROLES = {"factual", "quality"}
MAX_JSON = 128 * 1024
MAX_CELLS = 512


def valid_digest(value):
    return isinstance(value, str) and SHA.fullmatch(value) and value != "0" * 64


def literal(value):
    return (isinstance(value, str) and value and value == value.strip()
            and len(value.encode("utf-8")) <= 1024
            and all(ord(char) >= 32 and ord(char) != 127 for char in value))


def valid_source(source):
    if not isinstance(source, dict) or set(source) != SOURCE_KEYS:
        return False
    url = source["archive_url"]
    archive = ARCHIVE_URL.fullmatch(url) if isinstance(url, str) else None
    if archive is None:
        return False
    try:
        if date.fromisoformat(archive[1]).year < 2001:
            return False
    except ValueError:
        return False
    return (all(valid_digest(source[key]) for key in
                ("archive_sha256", "archive_receipt_sha256", "text_sha256"))
            and literal(source["title"]) and type(source["revision_id"]) is int
            and source["revision_id"] > 0)


def table_cells(raw):
    require(isinstance(raw, list) and len(raw) <= MAX_CELLS, "Invalid cell inventory")
    result = set()
    for cell in raw:
        require(isinstance(cell, list) and len(cell) == 3 and all(literal(value) for value in cell),
                "Cells must be [row label, column label, literal form]")
        key = tuple(cell)
        require(key not in result, "Duplicate table cell")
        result.add(key)
    return result


def verified_document(scratch, path, expected):
    require(valid_digest(expected), "Invalid artifact SHA-256")
    data = read_artifact(scratch, path, MAX_JSON)
    require(digest(data) == expected, f"Artifact SHA-256 differs for {path}")
    return read_json(data)


def lemma_key(value):
    return " ".join(unicodedata.normalize("NFC", value).replace("_", " ").split()).casefold()


def frozen_forms(proposal):
    payload = proposal["payload"]
    require(isinstance(payload, dict) and set(payload) == {"id", "kind", "owner_id", "forms", "identity"}
            and payload["kind"] == "form" and payload["id"] == proposal["item_id"]
            and literal(payload["owner_id"]) and isinstance(payload["identity"], dict)
            and payload["identity"].get("owner_id") == payload["owner_id"]
            and literal(payload["identity"].get("lemma"))
            and literal(payload["identity"].get("sense")), "Invalid frozen form payload")
    require(lemma_key(payload["identity"]["lemma"]) == lemma_key(proposal["source"]["title"]),
            "Dump source title differs from the frozen lemma")
    data = json.dumps(payload, sort_keys=True, ensure_ascii=False, allow_nan=False,
                      separators=(",", ":")).encode("utf-8")
    require(digest(data) == proposal["payload_sha256"], "Frozen form payload hash differs")
    forms = payload["forms"]
    require(isinstance(forms, list) and all(literal(form) for form in forms)
            and len(forms) == len(set(forms)), "Invalid frozen forms")
    return set(forms)


def compare(proposal, transcripts):
    require(set(proposal) == {"schema", "item_id", "author_thread", "payload_sha256",
                              "derived_view_sha256", "payload", "source", "proposed_cells"}
            and proposal["schema"] == "cat-v5-dump-proposed-cells-1", "Invalid proposal envelope")
    author = proposal["author_thread"]
    require(isinstance(author, str) and THREAD.fullmatch(author) and literal(proposal["item_id"])
            and valid_digest(proposal["payload_sha256"]) and valid_digest(proposal["derived_view_sha256"])
            and valid_source(proposal["source"]), "Invalid proposal binding")
    expected = table_cells(proposal["proposed_cells"])
    require(expected and {cell[2] for cell in expected} == frozen_forms(proposal),
            "Proposed cells must cover the exact frozen forms")
    require(len(transcripts) == 2, "Exactly two transcriptions required")
    by_role = {}
    threads = {author}
    for transcript in transcripts:
        require(set(transcript) == {"schema", "role", "thread_id", "source", "cells"}
                and transcript["schema"] == "cat-v5-dump-transcription-1",
                "Invalid proposal-blind transcription envelope")
        role, thread = transcript["role"], transcript["thread_id"]
        require(isinstance(role, str) and role in ROLES and role not in by_role,
                "One factual and one quality transcription required")
        require(isinstance(thread, str) and THREAD.fullmatch(thread) and thread not in threads,
                "Author and transcribers must be distinct")
        require(valid_source(transcript["source"]) and transcript["source"] == proposal["source"],
                f"{role} transcription binds a different archive or page")
        threads.add(thread)
        actual = table_cells(transcript["cells"])
        by_role[role] = {"thread_id": thread, "cell_count": len(actual),
                         "missing_proposed_cells": sorted(expected - actual)}

    forms = {}
    for form in sorted({cell[2] for cell in expected}):
        missing_roles = [
            role for role in sorted(ROLES)
            if any(cell[2] == form for cell in by_role[role]["missing_proposed_cells"])
        ]
        forms[form] = {"pass": not missing_roles, "missing_roles": missing_roles}
    return {"schema": "cat-v5-dump-transcription-diff-1", "item_id": proposal["item_id"],
            "author_thread": author, "payload_sha256": proposal["payload_sha256"],
            "derived_view_sha256": proposal["derived_view_sha256"], "source": proposal["source"],
            "transcribers": by_role, "forms": forms,
            "pass": all(row["pass"] for row in forms.values())}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scratch", type=Path, required=True)
    parser.add_argument("--proposal", nargs=2, required=True, metavar=("PATH", "SHA256"))
    parser.add_argument("--transcription", nargs=2, action="append", required=True,
                        metavar=("PATH", "SHA256"))
    args = parser.parse_args()
    try:
        scratch = args.scratch.absolute()
        require(scratch.is_dir() and scratch.resolve() == scratch, "Canonical scratch directory required")
        refs = [args.proposal, *args.transcription]
        require(len(refs) == 3 and len({path for path, _ in refs}) == len(refs),
                "Three distinct artifact paths required")
        proposal = verified_document(scratch, *args.proposal)
        transcripts = [verified_document(scratch, *ref) for ref in args.transcription]
        report = compare(proposal, transcripts)
        report["proposal"] = dict(zip(("path", "sha256"), args.proposal, strict=True))
        for transcript, ref in zip(transcripts, args.transcription, strict=True):
            report["transcribers"][transcript["role"]]["transcription"] = dict(
                zip(("path", "sha256"), ref, strict=True))
        print(json.dumps(report, sort_keys=True, ensure_ascii=True, allow_nan=False))
        return 0 if report["pass"] else 1
    except (TypeError, KeyError, OSError, ValueError) as exc:
        parser.exit(2, f"dump transcriptions: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
