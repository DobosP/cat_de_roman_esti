"""Check frequency folding, summing, statuses and input refusals."""

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
import frequency

FIXTURE = "\n".join([
    "de 100",
    "ţară 20",          # cedilla
    "țară 5",           # comma
    "tara 14",          # no diacritics
    "Țară 1",           # case
    "ŞCOALĂ 3",         # uppercase cedilla
    "școală 4",
    "scoala 9",
    "tata 7",           # plain word, no diacritic variant
    "olar",             # malformed: no count
    "bad x1",           # malformed: count not digits
    "",
])


def sha(data):
    return hashlib.sha256(data).hexdigest()


class FrequencyTests(unittest.TestCase):
    def setUp(self):
        base = Path(os.environ.get("CAT_V5_TEST_SCRATCH", Path.cwd()))
        self.dir = tempfile.TemporaryDirectory(prefix="frequency-", dir=base)
        self.root = Path(self.dir.name)
        self.data = FIXTURE.encode("utf-8")
        self.list = self.root / "list.txt"
        self.list.write_bytes(self.data)
        self.freq = frequency.load(self.list, sha(self.data))

    def tearDown(self):
        self.dir.cleanup()

    def test_cedilla_comma_case_sum_to_one_spelling(self):
        row = self.freq.lookup("țară")
        self.assertEqual((row["exact"], row["variants"], row["status"]), (26, 3, "exact"))
        self.assertEqual(self.freq.lookup("Ţară")["exact"], 26)
        self.assertEqual(self.freq.lookup("ŞCOALĂ")["exact"], 7)
        self.assertEqual(row["undiacritised"], 40)

    def test_undiacritised_only_is_flagged_fallback(self):
        row = self.freq.lookup("școală")
        self.assertEqual(row["status"], "exact")
        row = self.freq.lookup("tară")
        self.assertEqual(row["exact"], 0)
        self.assertEqual((row["undiacritised"], row["status"]), (40, "undiacritised_only"))

    def test_minority_spelling_is_flagged(self):
        # tara (14) is the plain writing of țară (26): its exact count is real but
        # most of the plain letters belong to the diacritic spelling.
        row = self.freq.lookup("tara")
        self.assertEqual((row["exact"], row["dominant_spelling"], row["minority_spelling"]),
                         (14, "țară", True))
        row = self.freq.lookup("țară")
        self.assertEqual((row["dominant_spelling"], row["minority_spelling"]), ("țară", False))
        row = self.freq.lookup("școală")
        self.assertEqual((row["dominant_spelling"], row["minority_spelling"]), ("scoala", False))
        self.assertIs(self.freq.lookup("libelulă")["minority_spelling"], False)
        self.assertIsNone(self.freq.lookup("cal de mare")["minority_spelling"])

    def test_plain_spelling_and_absent_and_multiword(self):
        self.assertEqual(self.freq.lookup("tata")["status"], "exact")
        self.assertEqual(self.freq.lookup("tată")["status"], "undiacritised_only")
        absent = self.freq.lookup("libelulă")
        self.assertEqual((absent["exact"], absent["undiacritised"], absent["status"]),
                         (0, 0, "absent"))
        multi = self.freq.lookup("  cal  de mare ")
        self.assertEqual((multi["status"], multi["exact"], multi["label"]),
                         ("multiword", None, "cal  de mare"))
        for bad in ("", "   ", 5, "x" * 200):
            with self.assertRaises(ValueError):
                self.freq.lookup(bad)

    def test_malformed_lines_skipped_and_counted(self):
        self.assertEqual(self.freq.skipped, 2)
        self.assertEqual(self.freq.lookup("de")["exact"], 100)

    def test_hash_mismatch_and_oversize_refused(self):
        with self.assertRaisesRegex(ValueError, "SHA-256 differs"):
            frequency.load(self.list, sha(b"other"))
        with self.assertRaisesRegex(ValueError, "64 lowercase"):
            frequency.load(self.list, "ABC")
        with self.assertRaisesRegex(ValueError, "exceeds"):
            frequency.load(self.list, sha(self.data), max_bytes=len(self.data) - 1)
        frequency.load(self.list, sha(self.data), max_bytes=len(self.data))

    def test_cli_json_and_txt_labels_and_failures(self):
        labels = self.root / "labels.json"
        labels.write_text(json.dumps(["țară", "cal de mare", "libelulă"]), encoding="utf-8")
        out = self.root / "out.json"
        command = [sys.executable, "-I", frequency.__file__, "--list", str(self.list),
                   "--sha256", sha(self.data), "--labels", str(labels), "--out", str(out)]
        result = subprocess.run(command, capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr.decode())
        report = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual(report["list_sha256"], sha(self.data))
        self.assertEqual([row["status"] for row in report["rows"]],
                         ["exact", "multiword", "absent"])
        self.assertEqual(set(report["rows"][0]),
                         {"label", "exact", "variants", "undiacritised", "status",
                          "dominant_spelling", "minority_spelling"})
        text = self.root / "labels.txt"
        text.write_text("tată\n\nșcoală\n", encoding="utf-8")
        command[command.index("--labels") + 1] = str(text)
        subprocess.run(command, capture_output=True, check=True)
        report = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual([row["status"] for row in report["rows"]],
                         ["undiacritised_only", "exact"])
        command[command.index("--sha256") + 1] = sha(b"other")
        failed = subprocess.run(command, capture_output=True, check=False)
        self.assertEqual(failed.returncode, 2)
        self.assertIn(b"SHA-256 differs", failed.stderr)

    def test_labels_bounds(self):
        big = self.root / "big.txt"
        big.write_bytes(b"a\n" * (frequency.MAX_LABELS_BYTES // 2 + 1))
        with self.assertRaisesRegex(ValueError, "exceeds"):
            frequency.read_labels(big)
        bad = self.root / "bad.json"
        bad.write_text('["a", 1]')
        with self.assertRaisesRegex(ValueError, "list of strings"):
            frequency.read_labels(bad)


if __name__ == "__main__":
    unittest.main()
