"""Focused alias preparation tests using synthetic candidate and review data."""

import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import alias_install as aliases


def raw(value):
    return json.dumps(value, ensure_ascii=False).encode()


class AliasInstallTests(unittest.TestCase):
    def test_generation_changes_only_exact_bound_aliases(self):
        before = {"meta": {"note": "keep"}, "kg_nodes": [
            {"id": "nut", "label_ro": "Nucă", "aliases": ["nuca"]},
            {"id": "pear", "label_ro": "Pară"},
        ], "kg_edges": [{"id": "e1"}], "kg_puzzles": [{"id": "p1"}]}
        candidate = {"a": {"owner_id": "nut", "forms": ["nuci", "nucilor"]}}
        after = json.loads(aliases.generate(raw(before), candidate))
        before["kg_nodes"][0]["aliases"].extend(["nuci", "nucilor"])
        self.assertEqual(after, before)
        with self.assertRaisesRegex(ValueError, "Duplicate accepted alias"):
            aliases.generate(raw(before), candidate)

    def test_screen_binding_and_atomic_family(self):
        receipt = {
            "schema": "cat-form-screen-result-1",
            "bindings": {"input_sha256": "a", "kg_sha256": "b", "executable_sha256": "c"},
            "items": [{"id": "a", "owner_id": "nut", "kind": "form", "state": "screened",
                       "reason_code": "screened", "accepted_forms": ["nuci"]}],
        }
        selected = aliases.selected_rows(receipt, "a", "b", "c")
        self.assertEqual(selected["a"]["forms"], ["nuci"])
        self.assertEqual(aliases.entry_key("https://ro.wiktionary.org/wiki/nuc%C4%83"), "nucă")
        self.assertEqual(aliases.entry_key("https://ro.wiktionary.org/wiki/nucă"), "nucă")
        with self.assertRaisesRegex(ValueError, "Screen kg binding differs"):
            aliases.selected_rows(receipt, "a", "other", "c")
        receipt["items"][0]["state"] = "held_owner"
        with self.assertRaisesRegex(ValueError, "refused item"):
            aliases.selected_rows(receipt, "a", "b", "c")

    def test_s7_rejects_unreviewed_items_and_incomplete_registry_group(self):
        selected = {"a": {"id": "a", "owner_id": "nut", "kind": "form", "forms": ["nuci"]}}
        row = {"state": "idea", "holds": [], "type": "form", "identity": {"owner_id": "nut"},
               "payload": {"forms": ["nuci"]}, "co_landing_group": "family"}
        with self.assertRaisesRegex(ValueError, "outside the unheld reviewed pool"):
            aliases.require_reviewed_pool({"a": row}, selected)
        row["state"] = "reviewed"
        with self.assertRaisesRegex(ValueError, "Partial reviewed co-landing group"):
            aliases.require_reviewed_pool({"a": row, "b": row}, selected)
        aliases.require_reviewed_pool({"a": row}, selected)

    def test_second_mirror_failure_restores_first_and_releases_lock(self):
        scratch = Path(os.environ.get("CAT_V5_TEST_SCRATCH", Path.cwd()))
        with tempfile.TemporaryDirectory(prefix="alias-rollback-", dir=scratch) as name:
            repo = Path(name)
            for relative in (aliases.KG, aliases.MIRROR):
                path = repo / relative
                path.parent.mkdir(parents=True)
                path.write_bytes(b"before")
            original = aliases.atomic_write

            def write(path, data):
                if path == repo / aliases.MIRROR:
                    raise OSError("injected second mirror failure")
                original(path, data)

            with patch.object(aliases, "atomic_write", side_effect=write):
                with self.assertRaisesRegex(OSError, "injected second mirror failure"):
                    aliases.install_mirrors(repo, b"before", b"after")
            self.assertEqual((repo / aliases.KG).read_bytes(), b"before")
            self.assertEqual((repo / aliases.MIRROR).read_bytes(), b"before")
            self.assertFalse((repo / ".cat-content-ops.lock").exists())

    def test_dual_acceptance_rejects_shared_thread_and_legacy_source(self):
        selected = {"a": {"id": "a", "owner_id": "nut", "kind": "form", "forms": ["nuci"]}}
        identity = {"owner_id": "nut", "sense": "fruit", "lemma": "nucă"}
        view = "a" * 64
        payload = hashlib.sha256(aliases.canonical({**selected["a"], "identity": identity})).hexdigest()
        docs = {
            role: {"role": role, "item_id": "a", "payload_sha256": payload,
                   "derived_view_sha256": view, "verdict": "accept",
                   "child_safe": True, "thread_id": role, "sources": [{
                       "url": "https://ro.wiktionary.org/wiki/nuc%C4%83",
                       "kind": "inflection-table",
                   }]}
            for role in aliases.ROLE_NAMES
        }

        body = b"Mock inflection evidence"
        body_sha = hashlib.sha256(body).hexdigest()
        receipt = {"url": docs["factual"]["sources"][0]["url"], "origin": "v5",
                   "first_fetch_origin": "v5", "status": 200, "fetched_by_role": "script",
                   "first_fetcher": "intake", "sha256": body_sha, "bytes": len(body)}
        receipt_path = "cache/" + "b" * 64 + ".response.json"

        def verify():
            receipt_bytes = raw(receipt)
            for doc in docs.values():
                doc["sources"][0]["receipt"] = {
                    "path": receipt_path, "sha256": hashlib.sha256(receipt_bytes).hexdigest(),
                }
            refs = {role: {"path": role, "sha256": hashlib.sha256(raw(doc)).hexdigest()}
                    for role, doc in docs.items()}
            envelope = {"schema": "cat-v5-alias-judgments-1", "input_sha256": "input",
                        "items": {"a": {"author_thread": "author", "payload_sha256": payload, "reviews": refs}}}
            files = {**{role: raw(doc) for role, doc in docs.items()}, receipt_path: receipt_bytes,
                     f"cache/{body_sha}.body": body}
            with patch.object(aliases, "owned_file", side_effect=lambda _, key, limit: files[key]):
                registry = {"a": {"v5_review_binding": envelope["items"]["a"], "identity": identity,
                                  "v5_derived_view_sha256": view,
                                  "v5_independence_checks": {"signed_reviews": True, "rationale_overlap_ok": True,
                                     "reviewer_identity_leaks_checked": True, "source_reuse_checked": True}}}
                aliases.acceptance(envelope, selected, "input", Path("."), registry)
                registry["a"]["v5_review_binding"] = {**envelope["items"]["a"], "author_thread": "different"}
                with self.assertRaisesRegex(ValueError, "reviewed registry evidence"):
                    aliases.acceptance(envelope, selected, "input", Path("."), registry)

        verify()
        docs["quality"]["thread_id"] = "factual"
        with self.assertRaisesRegex(ValueError, "threads must be distinct"):
            verify()
        docs["quality"]["thread_id"] = "quality"
        receipt["first_fetch_origin"] = "legacy"
        with self.assertRaisesRegex(ValueError, "lacks eligible Wiktionary"):
            verify()


if __name__ == "__main__":
    unittest.main()
