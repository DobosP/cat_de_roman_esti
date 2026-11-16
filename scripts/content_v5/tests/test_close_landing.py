"""Receipt closeout validations with synthetic gate and registry evidence."""

from copy import deepcopy
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

    def word_fixture(self):
        def node(owner, label):
            return {"id": owner, "label_ro": label, "node_type": "concept",
                    "description": label, "category": "stiinta", "salience": .6}

        def edge(src, dst):
            return {"src_id": src, "dst_id": dst, "relation": "related_to",
                    "label_ro": "related", "bidirectional": False, "strength": .7}

        common = edge("n_one", "n_two")
        links = [common, *(edge("n_one", f"n_{i}") for i in range(3)),
                 *(edge("n_two", f"n_{i}") for i in range(3))]
        items = [{"id": "one", "node": node("n_one", "One"), "links": links[:4]},
                 {"id": "two", "node": node("n_two", "Two"), "links": [common, *links[4:]]}]
        delta = {"concepts": {"added": [{**item["node"], "degree": len(item["links"]),
                                      "difficulty_tier": close.link_install.tier_for_salience(.6)} for item in items]},
                 "edges": {"added": [{**row, "id": f"e{i}", "is_distractor": 0, "bidirectional": 0}
                                     for i, row in enumerate(links)]},
                 "aliases": {"added": []}, "boards": {}}
        return items, links, delta

    def test_shared_word_edge_has_one_committed_effect_and_exact_fields(self):
        items, links, delta = self.word_fixture()
        self.assertEqual(close.word_artifacts(items, links, delta), {
            "one": {"node_id": "n_one", "edge_ids": ["e0", "e1", "e2", "e3"]},
            "two": {"node_id": "n_two", "edge_ids": ["e0", "e4", "e5", "e6"]},
        })
        for field, value in (("relation", "is_a"), ("label_ro", "other"), ("bidirectional", 1),
                             ("src_id", "n_two"), ("strength", .6), ("is_distractor", 1)):
            with self.subTest(field=field):
                changed = deepcopy(delta)
                changed["edges"]["added"][0][field] = value
                with self.assertRaisesRegex(ValueError, "incident link"):
                    close.word_artifacts(items, links, changed)
        for duplicate in (True, False):
            with self.subTest(duplicate=duplicate):
                changed = deepcopy(delta)
                extra = {**changed["edges"]["added"][0], "id": "extra"}
                if not duplicate:
                    extra["dst_id"] = "n_extra"
                changed["edges"]["added"].append(extra)
                with self.assertRaisesRegex(ValueError, "incident link"):
                    close.word_artifacts(items, links, changed)

    def test_word_scope_requires_exact_disturbed_board_http_play(self):
        items, links, delta = self.word_fixture()
        words = close.word_artifacts(items, links, delta)
        for item, word in words.items():
            word["payload_sha256"] = close.sha256(item.encode())
        registry = {item: {"type": "concept", "payload": {"forms": [], "node_id": word["node_id"]}}
                    for item, word in words.items()}
        docs = {
            "assembly": {"item_ids": sorted(words), "installed": {
                item: {key: row[key] for key in ("node_id", "edge_ids")} for item, row in words.items()},
                "frozen_payload_sha256": {item: row["payload_sha256"] for item, row in words.items()},
                "touched_boards": [["contexto", "board"]]},
            "landing-review": {"item_ids": sorted(words)},
            "http-play": {"sha": SHA, "baseline": BASE, "transcript": {"path": "play.jsonl"}},
        }
        delta["boards"]["contexto"] = {"added": [], "removed": [], "changed": []}
        bundle = {"manifest": {"content_hash": "hash"}, "pack_items": [
            {"id": "board", "pilot_eligible": True, "status": "approved", "game": "contexto",
             "payload": {"target": "n_0"}}]}
        header = {"sha": SHA, "baseline": BASE, "content_hash": "hash"}
        views = {("contexto", "board")}

        def play_receipt(rows):
            raw = b"".join((json.dumps(row) + "\n").encode() for row in rows)
            docs["http-play"]["transcript"]["sha256"] = close.sha256(raw)
            return raw

        raw = play_receipt([header, {"game": "contexto", "id": "board", "won": True, "seed": 1},
                            {"boards": 1, "aliases": 0, "failures": 0}])
        with patch.object(close, "read_artifact", return_value=raw):
            close.check_scope(Path("."), docs, delta, sorted(words), registry, bundle, words, views)
            docs["assembly"]["touched_boards"] = []
            with self.assertRaisesRegex(ValueError, "disturbed board"):
                close.check_scope(Path("."), docs, delta, sorted(words), registry, bundle, words, views)
        docs["assembly"]["touched_boards"] = [["contexto", "board"]]
        raw = play_receipt([header, {"boards": 0, "aliases": 0, "failures": 0}])
        with patch.object(close, "read_artifact", return_value=raw):
            with self.assertRaisesRegex(ValueError, "HTTP play scope differs"):
                close.check_scope(Path("."), docs, delta, sorted(words), registry, bundle, words, views)

    def test_word_board_reblind_requires_exact_bundle_and_every_changed_view(self):
        before, after = "a" * 64, "b" * 64
        first = {"game": "contexto", "id": "board", "kind": "changed",
                 "before_sha256": "c" * 64, "after_sha256": "d" * 64}
        shifted = {**first, "id": "count-only", "before_sha256": "1" * 64, "after_sha256": "2" * 64}
        diff = {"schema": "cat-board-view-diff-2", "baseline_bundle_sha256": before,
                "candidate_bundle_sha256": after, "disturbed_total": 2,
                "games": {game: {"disturbed": 2 if game == "contexto" else 0} for game in close.BOARD_GAMES},
                "disturbed": [first, {**first, "id": "board-2"}],
                "diagnostic_changes": [{**shifted, "id": "board"}, shifted]}
        diff_ref = {"path": "diff", "sha256": "e" * 64}
        reblind_ref = {"path": "blind", "sha256": "f" * 64}
        assembly = {"sha": SHA, "board_view_diff": diff_ref, "board_reblind": reblind_ref}
        opening = {"game": "contexto", "id": "board", "view_sha256": "d" * 64,
                   "thread_id": "fresh-blind-thread", "verdict": "pass"}
        reblind = {"schema": "cat-v5-board-reblind-1", "sha": SHA, "board_view_diff_sha256": diff_ref["sha256"],
                   "boards": [{**opening, "transcript": {"path": "play-1", "sha256": "1" * 64}},
                              {**opening, "id": "board-2",
                               "transcript": {"path": "play-2", "sha256": "2" * 64}}]}
        plays = {"play-1": {**opening, "play": [{"guess": "Câmpie"}]},
                 "play-2": {**opening, "id": "board-2", "play": [{"guess": "Munte"}]}}

        def evidence(_scratch, ref, _limit):
            document = {"diff": diff, "blind": reblind, **plays}[ref["path"]]
            return close.json_bytes(document)

        def check(candidate=after, other_roles=frozenset()):
            recorder = close.Evidence(Path("."), {})
            result = close.word_board_scope(recorder, assembly, before, candidate, other_roles)
            self.assertEqual(set(recorder.attachments), {
                "board-view-diff", "board-reblind", "board-reblind-transcript-1", "board-reblind-transcript-2",
            })
            return result

        with patch.object(close, "evidence_file", side_effect=evidence):
            # A count-only change is replayed over HTTP and needs no reblind.
            self.assertEqual(check(), (
                {("contexto", "board"): "d" * 64, ("contexto", "board-2"): "d" * 64},
                {("contexto", "board"), ("contexto", "board-2"), ("contexto", "count-only")}))
            with self.assertRaisesRegex(ValueError, "Exact full"):
                check("0" * 64)
            for stale in ({"schema": "cat-board-view-diff-1"}, {"one_word_dry_run": {}}):
                with self.subTest(stale=stale), patch.dict(diff, stale):
                    with self.assertRaisesRegex(ValueError, "Exact full"):
                        check()
            with patch.dict(diff, {"diagnostic_changes": [shifted, shifted]}):
                with self.assertRaisesRegex(ValueError, "Duplicate diagnostic"):
                    check()
            with self.assertRaisesRegex(ValueError, "Independent reblind"):
                check(other_roles={"fresh-blind-thread"})
            reblind["boards"][0]["view_sha256"] = "c" * 64
            with self.assertRaisesRegex(ValueError, "reblind pass differs"):
                check()
            reblind["boards"][0]["view_sha256"] = "d" * 64
            for invalid in ([], [{}], [{"guess": "   "}], [{"won": True}]):
                with self.subTest(play=invalid):
                    plays["play-2"]["play"] = invalid
                    with self.assertRaisesRegex(ValueError, "exact binding or play"):
                        check()
            plays["play-2"]["play"] = plays["play-1"]["play"]
            with self.assertRaisesRegex(ValueError, "Reused disturbed-board reblind play"):
                check()
            reblind["boards"][1]["transcript"]["sha256"] = "1" * 64
            with self.assertRaisesRegex(ValueError, "Reused disturbed-board reblind transcript"):
                check()
            reblind["boards"] = reblind["boards"][:1]
            with self.assertRaisesRegex(ValueError, "every disturbed board"):
                check()

    def test_evidence_aggregates_old_and_word_attachments_under_one_budget(self):
        data = b"three"
        ref = {"path": "nested", "sha256": close.sha256(data)}
        tracker = close.Evidence(Path("."), {"assembly": {
            "path": "assembly", "sha256": "a" * 64, "bytes": close.MAX_EVIDENCE - len(data),
        }})

        def bounded_read(_scratch, path, limit):
            self.assertIn(path, {"nested", "later"})
            if len(data) > limit:
                raise ValueError("Artifact exceeds size bound")
            return data

        with patch.object(close, "read_artifact", side_effect=bounded_read):
            tracker.add("word-link-claims", ref)
            tracker.add("shared-claims", ref, shared=True)
            self.assertEqual(tracker.used, close.MAX_EVIDENCE)
            self.assertEqual(set(tracker.attachments), {"assembly", "word-link-claims"})
            with self.assertRaisesRegex(ValueError, "Conflicting digest"):
                tracker.add("conflict", {**ref, "sha256": "b" * 64}, shared=True)
            with self.assertRaisesRegex(ValueError, "reused across"):
                tracker.add("http-transcript", ref)
            with self.assertRaisesRegex(ValueError, "size bound"):
                tracker.add("reference-corpus", {**ref, "path": "later"})

    def test_reblind_independence_includes_all_relevant_known_roles(self):
        tracker = close.Evidence(Path("."), {})
        docs = {"landing-review": {"thread_id": "landing"}, "pin-review": {"thread_id": "pins"}}
        rows = [{"id": "word", "checks": {}, "reviews": []},
                {"id": "board", "checks": {"v5_author": {"thread_id": "board-author"},
                                             "v5_blind": {"thread_id": "board-critic"}},
                 "reviews": [{"role": "quality", "thread_id": "board-quality"}]},
                {"id": "form", "checks": {}, "reviews": [], "v5_author_thread": "form-author",
                 "v5_review_binding": {"reviews": {"factual": {"path": "form-factual"}}}}]
        judgments = {"word": {"author_thread": "word-author", "reviews": {
            "factual": {"path": "word-factual"}, "critic": {"path": "word-critic"},
        }}}
        def attachment(_name, ref, *_args, **_kwargs):
            return close.json_bytes({"thread_id": ref["path"], "transcript_path": "word-critic-play",
                                     "transcript_sha256": "a" * 64})
        with patch.object(tracker, "add", side_effect=attachment):
            self.assertEqual(close.other_reblind_roles(tracker, docs, rows, judgments), {
                "landing", "pins", "board-author", "board-critic", "board-quality", "form-author",
                "form-factual", "word-author", "word-factual", "word-critic",
            })

    def test_qualified_word_replays_unchanged_exact_reviewed_predecessor(self):
        item = "one"
        prior = {"id": item, "state": "reviewed", "holds": [], "reviews": [],
                 "checks": {"v5_word_source_sha256": "a" * 64}, "frozen_payload": {"sha256": "a" * 64}}
        qualified = {**prior, "state": "qualified",
                     "previous_sha256": close.sha256(close.registry_encode(prior).encode())}
        self.assertEqual(close.reviewed_word_rows({item: qualified}, [prior, qualified], {item}), {item: prior})
        qualified["checks"] = {"v5_word_source_sha256": "b" * 64}
        with self.assertRaisesRegex(ValueError, "changed exact reviewed evidence"):
            close.reviewed_word_rows({item: qualified}, [prior, qualified], {item})

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
