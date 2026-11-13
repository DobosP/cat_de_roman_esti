"""Synthetic, offline regression tests for the exact corpus and replay."""

import argparse
import bz2
from collections import Counter
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
from types import ModuleType
import unittest
from unittest.mock import patch
from xml.sax.saxutils import escape

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import build_form_probes as probes
import wiktionary_dump as reader


def exact_parser():
    spec = importlib.util.find_spec("wiktionary_dump")
    code = Path(spec.origin).read_bytes()
    module = ModuleType("test_isolated_dump_parser")
    exec(compile(code, spec.origin, "exec"), module.__dict__)
    return module


def page(title, body="", redirect=False):
    return (f"<page><title>{escape(title)}</title><ns>0</ns>"
            + ('<redirect title="alt" />' if redirect else "")
            + f"<revision><id>100</id><model>wikitext</model><format>text/x-wiki</format>"
              f"<text bytes=\"{len(body.encode('utf-8'))}\">{escape(body)}</text></revision></page>")


def dump(pages):
    raw = (f'<mediawiki xmlns="{reader.XMLNS}0.11/"><siteinfo><dbname>rowiktionary</dbname></siteinfo>'
           + "".join(pages) + "</mediawiki>").encode()
    return bz2.compress(raw)


class TestFormProbes(unittest.TestCase):
    def test_only_exact_romanian_title_and_literal_forms(self):
        noun = """== {{limba|ron}} ==
{{-substantiv-|ron}}
{{substantiv-ron
|gen={{f}}
|nom-sg=masă
|nom-pl=mese
|art-sg=masa
|art-pl=mesele
|dat-sg=mesei
|dat-pl=meselor
|voc-sg=-
|voc-pl=-
}}
"""
        adj = """== {{limba|ron}} ==
{{-adjectiv-|ron}}
{{adjectiv-ron
|m-sg=alb
|m-pl=[[albi]]
|f-sg=[[albă]]
|f-pl=[[albe]]
}}
"""
        actual = [
            page("masă", noun), page("alb", adj), page("mase", redirect=True),
            page("măsură", "== {{limba|ron}} ==\n{{-substantiv-|ron}}\n{{substantiv-ron|broken}}\n"),
            page("mesî", "<nowiki>\n== {{limba|ron}} ==\n</nowiki>\n"),
            page("mea", "== {{limba|eng}} ==\n# X\n"), page("mers", "== {{limba|ron}} ==\n{{-verb-|ron}}\n"),
            page("ședere", "== {{limba|ron}} ==\n"), page("şedere", "== {{limba|ron}} ==\n"),
            page("sedere", "== {{limba|ron}} ==\n"),
        ]
        compressed = dump(actual)
        receipt = {"url": "https://example.invalid/rowiktionary.dump",
                   "sha256": probes.digest(compressed), "bytes": len(compressed),
                   "dump_checksum": {"sha1": hashlib.sha1(compressed, usedforsecurity=False).hexdigest()}}
        binding = {"archive_url": receipt["url"], "archive_sha256": receipt["sha256"],
                   "archive_receipt_sha256": "b" * 64}
        parser = exact_parser()
        original = parser.RevisionScan
        with tempfile.TemporaryDirectory(dir=os.environ.get("FORM_PROBES_TEST_SCRATCH")) as name, \
                patch.object(parser, "archive_receipt", return_value=(receipt, "b" * 64)):
            cache = Path(name)
            (cache / (receipt["sha256"] + ".dump")).write_bytes(compressed)
            raw, uncovered, coverage = probes.collect_corpus(parser, cache, "20261101", binding)
            self.assertEqual(json.loads(raw), sorted({
                "alb", "albi", "albă", "albe", "masă", "masa", "mese", "mesele", "mesei", "meselor",
                "măsură", "mers", "ședere", "şedere", "sedere",
            }))
            self.assertEqual(uncovered, {
                "măsură": ["unsupported noun table"], "mers": ["ungated verb paradigm"],
                "mesî": ["Romanian heading marker outside a confirmed section"],
            })
            self.assertEqual(coverage["unsupported_noun_table_pages"], 1)
            self.assertEqual(coverage["ungated_verb_pages"], 1)
            self.assertEqual(coverage["main_namespace_redirects_without_language_proof"], 1)
            self.assertEqual(coverage["supported_adjective_tables"], 1)
            self.assertEqual(coverage["exact_title_surfaces"], 7)
            self.assertIs(parser.RevisionScan, original)
            self.assertIsNot(parser.RevisionScan, reader.RevisionScan)
            (cache / (receipt["sha256"] + ".dump")).write_bytes(compressed[:-1] + b"x")
            with self.assertRaises((reader.DumpError, parser.DumpError, OSError)):
                probes.collect_corpus(parser, cache, "20261101", binding)
            self.assertIs(parser.RevisionScan, original)

    def test_shards_budget_accounts_for_automatic_probe_inputs(self):
        automatic = [{"surface": f"alias {i:03}"} for i in range(100)]
        neighbors = [{"surface": f"neighbor {i:04}"} for i in range(1800)]
        neighbors.extend([automatic[0], {"surface": "folded probe"}, {"surface": "țară"}, {"surface": "tara"}])
        groups = probes.shards(automatic, neighbors, ["folded probe"])
        self.assertEqual([len(group) for group in groups], [900, 900, 3])
        self.assertTrue(all(group == sorted(set(group)) for group in groups))
        self.assertEqual(Counter(item for group in groups for item in group),
                         Counter({row["surface"]: 1 for row in neighbors if row != automatic[0]}))
        self.assertIn("folded probe", groups[0])
        self.assertEqual(groups, probes.shards(automatic, list(reversed(neighbors)), ["folded probe"]))

    def test_proposal_packet_keeps_accented_spellings(self):
        row = {"schema": "cat-v5-form-probe-input-1", "items": [
            {"id": "form-1", "owner_id": "n_mare", "forms": ["țări", "tari", "ţări"]},
        ]}
        self.assertEqual([item["surface"] for item in probes.proposals(probes.json_bytes(row))],
                         ["tari", "ţări", "țări"])
        row["items"][0]["forms"].append("tari")
        with self.assertRaisesRegex(ValueError, "repeated literal"):
            probes.proposals(probes.json_bytes(row))

    def test_resolver_replay_requires_exact_proposals(self):
        first = {"nodes": [{"id": "owner", "aliases": ["existing"]}]}
        next_ = {"nodes": [{"id": "owner", "aliases": ["existing", "nouă"]}]}
        self.assertEqual(probes.effective_additions(probes.json_bytes(first), probes.json_bytes(next_)),
                         {("owner", "nouă")})
        next_["nodes"][0]["aliases"].remove("existing")
        with self.assertRaisesRegex(ValueError, "additive aliases"):
            probes.effective_additions(probes.json_bytes(first), probes.json_bytes(next_))
        self.assertEqual(probes.answered_owner({"mode": "unknown"}), "")
        self.assertEqual(probes.answered_owner({"mode": "confirm", "guess": {"id": "owner"}}), "owner")

    def test_missing_parser_gate_does_not_build_or_write(self):
        args = argparse.Namespace(
            sha="a" * 40, baseline="b" * 40, gate="no-go", gate_sha256="c" * 64,
        )
        output = HERE / "test-gate-denied-must-not-exist"
        self.assertFalse(output.exists())
        with patch.object(probes, "exact_commit", side_effect=lambda _root, sha: sha), \
                patch.object(probes, "reviewed_parser_gate", side_effect=ValueError("missing gate")), \
                patch.object(probes, "collect_corpus") as scan:
            with self.assertRaisesRegex(ValueError, "missing gate"):
                probes.candidate_probes(args, HERE, HERE, output)
            scan.assert_not_called()
        self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
