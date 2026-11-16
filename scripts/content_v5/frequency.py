#!/usr/bin/env python3
"""Diacritic-folded word frequency lookup over a FrequencyWords list."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import unicodedata

sys.dont_write_bytecode = True

SHA = re.compile(r"[a-f0-9]{64}")
MAX_LIST_BYTES = 64 * 1024 * 1024
MAX_LINE_BYTES = 256
MAX_LABELS_BYTES = 1024 * 1024
MAX_LABELS = 100_000
MAX_LABEL_CHARS = 128
SCHEMA = "cat-v5-frequency-1"
CEDILLA = str.maketrans({"ş": "ș", "ţ": "ț", "Ş": "Ș", "Ţ": "Ț"})


def fold(text):
    """NFC, cedilla to comma, lowercase: one spelling per Romanian word."""
    text = unicodedata.normalize("NFC", text).translate(CEDILLA)
    return unicodedata.normalize("NFC", text.lower()).translate(CEDILLA)


def plain(folded):
    """Remove every combining mark (ă â î ș ț and any other diacritic)."""
    decomposed = unicodedata.normalize("NFD", folded)
    return "".join(char for char in decomposed if not unicodedata.combining(char))


class Frequencies:
    def __init__(self, counts, plain_counts, variants, sha256, skipped):
        self.counts = counts
        self.plain_counts = plain_counts
        self.variants = variants
        self.sha256 = sha256
        self.skipped = skipped

    def lookup(self, label):
        if not isinstance(label, str) or not label.strip() or len(label) > MAX_LABEL_CHARS:
            raise ValueError("Label must be a non-empty string of bounded length")
        label = label.strip()
        if any(char.isspace() for char in label):
            return {"label": label, "exact": None, "variants": None,
                    "undiacritised": None, "status": "multiword"}
        key = fold(label)
        exact = self.counts.get(key, 0)
        undiacritised = self.plain_counts.get(plain(key), 0)
        status = ("exact" if exact else
                  "undiacritised_only" if undiacritised else "absent")
        return {"label": label, "exact": exact, "variants": self.variants.get(key, 0),
                "undiacritised": undiacritised, "status": status}


def load(list_path, expected_sha256, max_bytes=MAX_LIST_BYTES):
    """Verify the list hash, then sum counts of spellings that fold together.

    `variants` counts the raw lines merged into a folded spelling. Lines that do
    not match "word count" are skipped and counted in `skipped`.
    """
    if not isinstance(expected_sha256, str) or not SHA.fullmatch(expected_sha256):
        raise ValueError("Expected SHA-256 must be 64 lowercase hex characters")
    path = Path(list_path)
    with path.open("rb") as handle:
        data = handle.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise ValueError(f"Frequency list exceeds {max_bytes} bytes")
    digest = hashlib.sha256(data).hexdigest()
    if digest != expected_sha256:
        raise ValueError(f"Frequency list SHA-256 differs: {digest}")
    text = data.decode("utf-8")
    counts, variants, skipped = {}, {}, 0
    for line in text.split("\n"):
        line = line.rstrip("\r")
        if not line:
            continue
        word, _, number = line.rpartition(" ")
        if (not word or not number.isascii() or not number.isdigit()
                or len(line.encode("utf-8")) > MAX_LINE_BYTES or word != word.strip()
                or any(char.isspace() for char in word)):
            skipped += 1
            continue
        key = fold(word)
        counts[key] = counts.get(key, 0) + int(number)
        variants[key] = variants.get(key, 0) + 1
    plain_counts = {}
    for key, count in counts.items():
        flat = plain(key)
        plain_counts[flat] = plain_counts.get(flat, 0) + count
    return Frequencies(counts, plain_counts, variants, digest, skipped)


def read_labels(path):
    path = Path(path)
    with path.open("rb") as handle:
        data = handle.read(MAX_LABELS_BYTES + 1)
    if len(data) > MAX_LABELS_BYTES:
        raise ValueError(f"Labels file exceeds {MAX_LABELS_BYTES} bytes")
    text = data.decode("utf-8")
    if path.suffix == ".json":
        labels = json.loads(text)
        if not isinstance(labels, list) or not all(isinstance(item, str) for item in labels):
            raise ValueError("Labels JSON must be a list of strings")
    else:
        labels = [line for line in text.splitlines() if line.strip()]
    if not labels or len(labels) > MAX_LABELS:
        raise ValueError(f"Labels must number between 1 and {MAX_LABELS}")
    return labels


def report(frequencies, labels):
    return {"schema": SCHEMA, "list_sha256": frequencies.sha256,
            "skipped_lines": frequencies.skipped,
            "rows": [frequencies.lookup(label) for label in labels]}


def write_json(path, value):
    path = Path(path)
    raw = json.dumps(value, ensure_ascii=False, indent=1, sort_keys=True, allow_nan=False) + "\n"
    descriptor, temp = tempfile.mkstemp(dir=path.parent, prefix=".frequency-")
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(raw)
        os.replace(temp, path)
    except BaseException:
        os.unlink(temp)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", type=Path, required=True)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--labels", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        frequencies = load(args.list, args.sha256)
        result = report(frequencies, read_labels(args.labels))
        write_json(args.out, result)
        counts = {}
        for row in result["rows"]:
            counts[row["status"]] = counts.get(row["status"], 0) + 1
        print(json.dumps(counts, sort_keys=True))
        return 0
    except (TypeError, KeyError, OSError, ValueError) as exc:
        parser.exit(2, f"frequency: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
