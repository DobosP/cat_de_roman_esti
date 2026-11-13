"""Receipt closeout validations with synthetic gate and registry evidence."""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import close_landing as close


SHA = "b" * 40
BASE = "a" * 40


class CloseLandingTests(unittest.TestCase):
    def test_write_preserves_native_evidence_and_rolls_back_owned_outputs(self):
        scratch = Path(os.environ.get("CAT_V5_TEST_SCRATCH", Path.cwd())).resolve()
        receipt = "docs/reviews/v5-forms-1/landing.json"
        saved = {close.REGISTRY: b"", close.STATUS: b"previous status", close.QUEUE: b"previous queue"}
        outputs = {**dict.fromkeys(saved, b"updated"), receipt: b"landing receipt"}
        outputs[close.REGISTRY] = b""
        for existing_parent in (True, False):
            with self.subTest(existing_parent=existing_parent), tempfile.TemporaryDirectory(
                prefix="closeout-rollback-", dir=scratch,
            ) as name:
                repo = Path(name)
                (repo / "docs/reviews").mkdir(parents=True)
                (repo / close.REGISTRY).parent.mkdir()
                for relative, data in saved.items():
                    (repo / relative).write_bytes(data)
                path = repo / receipt
                evidence = path.parent / "native" / "review.json"
                if existing_parent:
                    evidence.parent.mkdir(parents=True)
                    evidence.write_bytes(b"native evidence")

                def fail_docs(*args, **kwargs):
                    self.assertEqual(path.read_bytes(), outputs[receipt])
                    raise subprocess.CalledProcessError(1, "cat-doc-check")

                with patch.object(close, "git"), patch.object(close.subprocess, "run") as docs:
                    docs.side_effect = fail_docs
                    with self.assertRaises(subprocess.CalledProcessError):
                        close.write(repo, outputs, Path("cat-doc-check"))
                    for relative, data in saved.items():
                        self.assertEqual((repo / relative).read_bytes(), data)
                    self.assertFalse(path.exists())
                    self.assertEqual(path.parent.is_dir(), existing_parent)
                    if existing_parent:
                        self.assertEqual(evidence.read_bytes(), b"native evidence")

                    if existing_parent:
                        path.symlink_to(path.parent / "missing.json")
                        with self.assertRaisesRegex(ValueError, "Landing receipt already exists"):
                            close.write(repo, outputs, Path("cat-doc-check"))
                        path.unlink()
                    else:
                        path.parent.symlink_to(repo / "docs/reviews/missing", target_is_directory=True)
                        with self.assertRaisesRegex(ValueError, "Landing directory must be a real directory"):
                            close.write(repo, outputs, Path("cat-doc-check"))
                        path.parent.unlink()

                    docs.side_effect = None
                    close.write(repo, outputs, Path("cat-doc-check"))
                    with self.assertRaisesRegex(ValueError, "Landing receipt already exists"):
                        close.write(repo, outputs, Path("cat-doc-check"))
                self.assertEqual(path.read_bytes(), outputs[receipt])
                if existing_parent:
                    self.assertEqual(evidence.read_bytes(), b"native evidence")

    def test_transitions_preserve_history_and_bind_receipt(self):
        item = {"id": "a", "state": "reviewed", "holds": [], "dependencies": [],
                "co_landing_group": None, "payload": {"forms": ["nuci"]}}
        receipt = {"path": "docs/reviews/v5-t/landing.json", "sha256": "a" * 64, "bytes": 7}
        qualified, landed = close.transitions({"a": item}, ["a"], receipt, SHA, "2026-11-13")
        self.assertEqual(qualified["state"], "qualified")
        self.assertEqual(landed["state"], "landed")
        self.assertEqual(landed["previous_sha256"],
                         hashlib.sha256(close.registry_encode(qualified).encode()).hexdigest())
        self.assertEqual(landed["v5_landing"], {"candidate": SHA, "receipt": receipt})
        self.assertEqual(item["state"], "reviewed")

    def test_partial_group_missing_dependency_and_holds_are_rejected(self):
        first = {"id": "a", "state": "reviewed", "holds": [], "dependencies": ["b"],
                 "co_landing_group": "pair"}
        second = {"id": "b", "state": "reviewed", "holds": [], "dependencies": [],
                  "co_landing_group": "pair"}
        with self.assertRaisesRegex(ValueError, "Partial co-landing"):
            close.transitions({"a": first, "b": second}, ["a"], {}, SHA, "2026-11-13")
        first["co_landing_group"] = None
        with self.assertRaisesRegex(ValueError, "Unlanded dependency"):
            close.transitions({"a": first, "b": second}, ["a"], {}, SHA, "2026-11-13")
        second["holds"] = [{"kind": "owner"}]
        with self.assertRaisesRegex(ValueError, "has a hold"):
            close.transitions({"a": first, "b": second}, ["a", "b"], {}, SHA, "2026-11-13")

    def test_scope_requires_landed_alias_and_http_play(self):
        alias = {"id": "nut", "form": "nuci", "label": "Nucă"}
        row = {"type": "form", "identity": {"owner_id": "nut"}, "payload": {"forms": ["nuci"]}}
        payload_sha = hashlib.sha256(close.registry_encode(row["payload"]).encode()).hexdigest()
        delta = {"aliases": {"added": [alias]}, "boards": {},
                 "concepts": {"added": []}, "edges": {"added": []}}
        bundle = {"manifest": {"content_hash": "hash"}, "pack_items": []}
        transcript = b"\n".join(json.dumps(item).encode() for item in (
            {"sha": SHA, "baseline": BASE, "content_hash": "hash"},
            {"id": "nut", "alias": "nuci", "label": "Nucă", "repeat_seed": 0, "wins": {}},
            {"boards": 0, "aliases": 1, "failures": 0},
        )) + b"\n"
        docs = {
            "assembly": {"item_ids": ["a"], "installed": {"a": {"owner_id": "nut"}},
                         "frozen_payload_sha256": {"a": payload_sha}, "touched_boards": []},
            "landing-review": {"item_ids": ["a"]},
            "http-play": {"sha": SHA, "baseline": BASE, "transcript": {
                "path": "play.jsonl", "sha256": hashlib.sha256(transcript).hexdigest()}},
        }
        with patch.object(close, "read_artifact", return_value=transcript):
            close.check_scope(Path("."), docs, delta, ["a"], {"a": row}, bundle)
            with self.assertRaisesRegex(ValueError, "item sets differ"):
                close.check_scope(Path("."), docs, delta, ["other"], {"a": row}, bundle)
            delta["aliases"]["added"] = []
            with self.assertRaisesRegex(ValueError, "Installed aliases differ"):
                close.check_scope(Path("."), docs, delta, ["a"], {"a": row}, bundle)

    def test_pack_payload_excludes_generated_record_fields(self):
        installed = {"id": "cx1", "status": "approved", "source": "v5",
                     "groups": {"a": ["x"]}, "order": ["x"],
                     "category": "limba", "difficulty": "normal"}
        self.assertEqual(close.board_payload("conexiuni", installed),
                         {"groups": {"a": ["x"]}, "order": ["x"],
                          "category": "limba", "difficulty": "normal"})

    def test_gui_trigger_uses_content_not_rail_filename(self):
        empty = {"added": [], "removed": [], "changed": []}
        delta = {"boards": {"conexiuni": {**empty}}, "edges": {**empty}}
        bundle = {"lant_captions": {}, "discovery_world": {"recipes": []},
                  "recipe_extensions": {"boards": []}}
        paths = [b"cat_de_roman_esti/fixtures/board_rankings_v37.json",
                 b"cat_de_roman_esti/fixtures/alchimie_recipe_extensions_v92.json"]
        self.assertFalse(close.needs_gui(delta, bundle, bundle, paths))
        delta["boards"]["conexiuni"]["eligibility"] = {"added": ["cx1"], "removed": []}
        self.assertTrue(close.needs_gui(delta, bundle, bundle, paths))

    def test_exact_receipts_require_green_independent_quorum(self):
        lock = {"toolchain_image": {"image_id": "image"}}
        packets = {
            "assembly": {"sha": SHA, "baseline": BASE, "status": "pass"},
            "build": {"sha": SHA, "status": "pass", "target": "build", "dirty": False,
                      "schema": 1, "versions_lock_sha256": "lock", "toolchain_digest": "image",
                      "tree_sha256": "c" * 64,
                      "checks": [{"name": name, "status": "pass"} for name in sorted(close.BUILD_CHECKS)]},
            "4i": {"sha": SHA, "status": "pass", "baseline": BASE, "source_tree_sha256": "c" * 64,
                   "checks": [{"name": name, "exit_code": 0} for name in sorted(close.CHECKS_4I)]},
            "reference": {"sha": SHA, "status": "pass", "case_count": 1206},
            "pin-review": {"sha": SHA, "verdict": "GO", "thread_id": "pin", "case_count": 1206},
            "http-play": {"sha": SHA, "baseline": BASE, "status": "pass"},
            "landing-review": {"sha": SHA, "verdict": "GO", "thread_id": "landing"},
        }

        def verify():
            packets["4i"]["build_receipt_sha256"] = hashlib.sha256(json.dumps(packets["build"]).encode()).hexdigest()
            for role in ("assembly", "http-play", "reference", "pin-review"):
                packets["landing-review"][role.replace("-", "_") + "_sha256"] = (
                    hashlib.sha256(json.dumps(packets[role]).encode()).hexdigest()
                )
            raw = {role: json.dumps(packet).encode() for role, packet in packets.items()}
            refs = {role: {"path": role, "sha256": hashlib.sha256(data).hexdigest()}
                    for role, data in raw.items()}
            with patch.object(close, "read_artifact", side_effect=lambda _, path, limit=0: raw[path]):
                return close.read_receipts(Path("."), refs, SHA, BASE, False, lock, "lock")[0]

        self.assertEqual(set(verify()), set(packets))
        packets["4i"]["source_tree_sha256"] = "e" * 64
        with self.assertRaisesRegex(ValueError, "exact build receipt and tree"):
            verify()
        packets["4i"]["source_tree_sha256"] = "c" * 64
        packets["landing-review"]["thread_id"] = "pin"
        with self.assertRaisesRegex(ValueError, "must be distinct"):
            verify()
        packets["http-play"]["status"] = "fail"
        with self.assertRaisesRegex(ValueError, "not green"):
            verify()


if __name__ == "__main__":
    unittest.main()
