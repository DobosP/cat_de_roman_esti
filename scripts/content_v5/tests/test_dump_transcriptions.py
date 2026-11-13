"""Check that independent dump transcriptions bind exact cells and reviewers."""

from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import dump_transcriptions as transcriptions


def sha(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


class DumpTranscriptionTests(unittest.TestCase):
    def setUp(self):
        source = {
            "archive_url": "https://dumps.wikimedia.org/rowiktionary/20261101/"
                           "rowiktionary-20261101-pages-articles.xml.bz2",
            "archive_sha256": sha("archive"), "archive_receipt_sha256": sha("receipt"),
            "title": "nucă", "revision_id": 5, "text_sha256": sha("source"),
        }
        cells = [["Nominativ-Acuzativ", "Plural", "nuci"],
                 ["Articulat", "Plural", "nucile"]]
        payload = {"id": "forms:nucă", "kind": "form", "owner_id": "nucă",
                   "forms": ["nuci", "nucile"],
                   "identity": {"owner_id": "nucă", "lemma": "Nucă", "sense": "fruit"}}
        payload_sha = sha(json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")))
        self.proposal = {
            "schema": "cat-v5-dump-proposed-cells-1", "item_id": "forms:nucă",
            "author_thread": "author", "payload_sha256": payload_sha, "payload": payload,
            "derived_view_sha256": sha("view"), "source": source, "proposed_cells": cells,
        }
        self.transcripts = [
            {"schema": "cat-v5-dump-transcription-1", "role": role, "thread_id": role,
             "source": deepcopy(source),
             "cells": [*deepcopy(cells), ["Nominativ-Acuzativ", "Singular", "nucă"]]}
            for role in ("factual", "quality")
        ]

    def test_full_transcripts_can_contain_unproposed_cells(self):
        report = transcriptions.compare(self.proposal, self.transcripts)
        self.assertTrue(report["pass"])
        self.assertEqual(set(report["forms"]), {"nuci", "nucile"})

    def test_drop_only_form_with_a_cell_discrepancy(self):
        self.transcripts[1]["cells"][1][0] = "Genitiv-Dativ"
        report = transcriptions.compare(self.proposal, self.transcripts)
        self.assertFalse(report["pass"])
        self.assertTrue(report["forms"]["nuci"]["pass"])
        self.assertEqual(report["forms"]["nucile"]["missing_roles"], ["quality"])
        self.assertEqual(report["transcribers"]["quality"]["missing_proposed_cells"],
                         [("Articulat", "Plural", "nucile")])

    def test_rejects_a_changed_page_binding_or_reused_actor(self):
        for key, value in (("revision_id", 6), ("text_sha256", sha("other")),
                           ("archive_receipt_sha256", sha("other"))):
            with self.subTest(key=key):
                transcripts = deepcopy(self.transcripts)
                transcripts[0]["source"][key] = value
                with self.assertRaisesRegex(ValueError, "different archive or page"):
                    transcriptions.compare(self.proposal, transcripts)
        self.transcripts[0]["thread_id"] = self.proposal["author_thread"]
        with self.assertRaisesRegex(ValueError, "must be distinct"):
            transcriptions.compare(self.proposal, self.transcripts)

    def test_rejects_reused_table_from_another_lemma(self):
        self.proposal["source"]["title"] = "alună"
        for transcript in self.transcripts:
            transcript["source"]["title"] = "alună"
        with self.assertRaisesRegex(ValueError, "title differs"):
            transcriptions.compare(self.proposal, self.transcripts)

    def test_rejects_omitted_frozen_form_and_changed_payload(self):
        proposed_cells = self.proposal["proposed_cells"]
        omitted = proposed_cells.pop()
        with self.assertRaisesRegex(ValueError, "cover the exact frozen forms"):
            transcriptions.compare(self.proposal, self.transcripts)
        proposed_cells.append(omitted)
        self.proposal["payload"]["forms"].pop()
        with self.assertRaisesRegex(ValueError, "payload hash differs"):
            transcriptions.compare(self.proposal, self.transcripts)

    def test_rejects_duplicate_cells_and_disclosed_proposal_fields(self):
        self.transcripts[0]["cells"].append(self.transcripts[0]["cells"][0])
        with self.assertRaisesRegex(ValueError, "Duplicate table cell"):
            transcriptions.compare(self.proposal, self.transcripts)
        self.transcripts[0]["cells"].pop()
        self.transcripts[0]["payload_sha256"] = self.proposal["payload_sha256"]
        with self.assertRaisesRegex(ValueError, "proposal-blind"):
            transcriptions.compare(self.proposal, self.transcripts)

    def test_cli_hash_failure_and_nonzero_per_form_discrepancy(self):
        base = Path(os.environ.get("CAT_V5_TEST_SCRATCH", Path.cwd()))
        with tempfile.TemporaryDirectory(prefix="dump-transcriptions-", dir=base) as name:
            root = Path(name)
            self.transcripts[1]["cells"].pop(1)
            flags = []
            for label, value, flag in (("proposal", self.proposal, "--proposal"),
                                       ("factual", self.transcripts[0], "--transcription"),
                                       ("quality", self.transcripts[1], "--transcription")):
                raw = json.dumps(value, ensure_ascii=False)
                (root / label).write_text(raw, encoding="utf-8")
                flags.extend((flag, label, sha(raw)))
            command = [sys.executable, "-I", transcriptions.__file__, "--scratch", str(root), *flags]
            result = subprocess.run(command, capture_output=True, check=False)
            self.assertEqual(result.returncode, 1, result.stderr.decode())
            report = json.loads(result.stdout)
            self.assertEqual(report["forms"]["nucile"]["missing_roles"], ["quality"])
            (root / "quality").write_text("{}")
            failed = subprocess.run(command, capture_output=True, check=False)
            self.assertEqual(failed.returncode, 2)
            self.assertIn(b"SHA-256 differs", failed.stderr)


if __name__ == "__main__":
    unittest.main()
