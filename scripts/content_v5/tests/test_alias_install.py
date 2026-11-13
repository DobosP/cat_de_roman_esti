"""Focused alias preparation tests using synthetic candidate and review data."""

import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import quote

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import alias_install as aliases
import test_wiktionary_dump as dump_fixtures


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


class DumpAliasInstallTests(unittest.TestCase):
    """Synthetic sources and reviews, replayed by the real parser and comparator."""

    def setUp(self):
        scratch = Path(os.environ.get("CAT_V5_TEST_SCRATCH", Path.cwd()))
        directory = tempfile.TemporaryDirectory(prefix="alias-dump-", dir=scratch)
        self.addCleanup(directory.cleanup)
        self.scratch = Path(directory.name)
        self.cache = self.scratch / "cache"
        self.cache.mkdir()
        self.repo = aliases.V5.parents[1]
        self.commit = "a" * 40
        self.archived_title = "mentă"
        self.archived_revision = 901
        self.archived_text = dump_fixtures.NOUN
        cached = [{"title": "istoric" + chr(97 + i), "dump_revision": 1 + i} for i in range(20)]
        fresh = [{"title": "proaspat" + chr(97 + i), "dump_revision": i + 100, "category": category}
                 for i, category in enumerate(list(aliases.SAMPLE_KINDS) * 2)]
        archived_pages = [dump_fixtures.page(
            self.archived_title, raw=self.archived_text, revision=self.archived_revision,
        )]
        self.cached_html = {}
        for row in [*cached, *fresh]:
            category = row.get("category")
            kind = aliases.SAMPLE_KINDS[category] if category else "noun"
            archived_pages.append(self.archive_sample(row, kind, fresh=category is not None))
        self.receipt, self.archive_path = dump_fixtures.archive(
            self.cache, dump_fixtures.START + "".join(archived_pages) + dump_fixtures.END,
        )
        self.archive = {"archive_url": self.receipt["url"], "archive_sha256": self.receipt["sha256"],
                        "archive_receipt_sha256": aliases.sha256(self.archive_path.read_bytes())}
        self.source = {**self.archive, "title": self.archived_title, "revision_id": self.archived_revision,
                       "text_sha256": aliases.sha256(self.archived_text.encode())}
        self.git_files = {path: (self.repo / path).read_bytes()
                          for path in (aliases.PARSER_PATH, aliases.COMPARATOR_PATH)}
        prefix = f"scripts/content_v5/dump_samples/{dump_fixtures.DAY}"
        baseline = raw({"archive": {**self.archive, "missing_titles": []}, "cached_comparison": cached})
        sample = raw({"archive_date": dump_fixtures.DAY, "archive_sha256": self.receipt["sha256"],
                      "cached_comparison_sha256": aliases.sha256(baseline), "pages": fresh})
        comparator = dump_fixtures.comparator
        sample_hash = aliases.sha256(sample)
        # Synthetic Git fixtures pin the synthetic manifest in otherwise unchanged comparator code.
        comparator_code = self.git_files[aliases.COMPARATOR_PATH]
        self.assertEqual(comparator_code.count(comparator.SAMPLE_SHA256.encode()), 1)
        comparator_code = comparator_code.replace(comparator.SAMPLE_SHA256.encode(), sample_hash.encode())
        self.git_files.update({f"{prefix}-cached.json": baseline, f"{prefix}-sample.json": sample,
                               aliases.COMPARATOR_PATH: comparator_code})
        hashes = {"parser_sha256": aliases.sha256(self.git_files[aliases.PARSER_PATH]),
                  "comparator_sha256": aliases.sha256(comparator_code), "sample_sha256": sample_hash}
        archived_sha = self.archive["archive_sha256"]
        with patch.object(comparator, "SAMPLE_SHA256", sample_hash):
            self.historical = comparator.compare(self.cache, dump_fixtures.DAY, archived_sha, [
                (row["title"], row["dump_revision"], "noun") for row in cached
            ], cached_baseline_sha256=aliases.sha256(baseline))
            self.fresh = comparator.compare(self.cache, dump_fixtures.DAY, archived_sha, [
                (row["title"], row["dump_revision"], aliases.SAMPLE_KINDS[row["category"]]) for row in fresh
            ])
        for report in (self.historical, self.fresh):
            self.assertTrue(report["equal"], report["pages"])
            report.update(hashes)
        self.gate = {**hashes, "schema": "cat-v5-wiktionary-parser-gate-1", "archive": self.archive,
                     "verdict": "GO", "reviewer_thread": "mock-parser-review"}
        self.selected = {}
        self.registry = {}
        self.judgments = {"schema": "cat-v5-alias-judgments-1", "input_sha256": "input", "items": {}}
        self.families = {}
        self.add_family("mint", "mentei", "Genitiv-Dativ")

    def archive_sample(self, row, kind, *, fresh):
        title, revision = row["title"], row["dump_revision"]
        url = dump_fixtures.comparator.WIKI + quote(title, safe="")
        if kind == "noun":
            text = dump_fixtures.NOUN.replace("mentă", title)
            fixture = dump_fixtures.ComparatorTests()
            fixture.title, fixture.revision, fixture.url = title, revision, url
            html = fixture.rendered().replace("mentă", title)
        else:
            text = dump_fixtures.AdjectiveTests.RAW.replace("luminos", title)
            config = json.dumps({"wgTitle": title, "wgPageName": title, "wgRevisionId": revision,
                                 "wgNamespaceNumber": 0, "wgIsRedirect": False})
            html = (
                f'<html><head><link rel="canonical" href="{url}"><script>RLCONF={config};</script></head>'
                '<body><table class="adjectiv-ron"><tbody>'
                f'<tr><td colspan="3">Declinarea adjectivului <br/>{title}</td></tr>'
                '<tr><td>Gen</td><td>Singular</td><td>Plural</td></tr>'
                f'<tr><td>Masculin</td><td>{title}</td><td>luminoși</td></tr>'
                '<tr><td>Feminin</td><td>luminoasă</td><td>luminoase</td></tr>'
                f'<tr><td>Neutru</td><td>{title}</td><td>luminoase</td></tr>'
                '</tbody></table></body></html>'
            )
        fetcher = dump_fixtures.comparator.FRESH_FETCHER if fresh else "mock-historical-fetch"
        receipt, path = dump_fixtures.write_receipt(
            self.cache, url, html.encode(), ".body", first_fetcher=fetcher, attempt_fetcher=fetcher,
            headers={"content-type": "text/html; charset=UTF-8"},
        )
        self.cached_html[title] = (path, self.cache / (receipt["sha256"] + ".body"))
        return dump_fixtures.page(title, raw=text, revision=revision)

    def add_family(self, item_id, form, label):
        selected = {"id": item_id, "kind": "form", "owner_id": "owner", "forms": [form]}
        identity = {"lemma": "Mentă", "sense": "plant", "owner_id": "owner"}
        frozen = {**selected, "identity": identity}
        view = "f" * 64
        proposal = {"schema": "cat-v5-dump-proposed-cells-1", "item_id": item_id,
                    "author_thread": "mock-author", "payload": frozen,
                    "payload_sha256": aliases.sha256(aliases.canonical(frozen)), "derived_view_sha256": view,
                    "source": self.source.copy(), "proposed_cells": [[label, "Singular", form]]}
        threads = {role: "mock-" + role for role in aliases.ROLE_NAMES}
        reviews = {
            role: {"role": role, "item_id": item_id, "verdict": "accept", "child_safe": True,
                   "thread_id": thread, "payload_sha256": proposal["payload_sha256"], "derived_view_sha256": view,
                   "sources": [{"kind": "dump-inflection-table", "source": self.source.copy(), "table_kind": "noun"}]}
            for role, thread in threads.items()
        }
        transcripts = {
            role: {"schema": "cat-v5-dump-transcription-1", "role": role, "thread_id": thread,
                   "source": self.source.copy(), "cells": [[label, "Singular", form]]}
            for role, thread in threads.items()
        }
        self.families[item_id] = proposal, reviews, transcripts
        self.selected[item_id] = selected
        self.registry[item_id] = {
            "identity": identity, "v5_derived_view_sha256": view,
            "provenance": [{**self.source, "first_fetcher": "fixture", "first_fetch_origin": "v5",
                            "fetched_by_role": "script"}],
            "v5_independence_checks": {"signed_reviews": True, "rationale_overlap_ok": True,
                                       "reviewer_identity_leaks_checked": True, "source_reuse_checked": True},
        }

    def save(self, path, value):
        data = raw(value)
        (self.scratch / path).write_bytes(data)
        return {"path": path, "sha256": aliases.sha256(data)}

    def seal(self):
        self.gate["historical"] = self.save("historical.json", self.historical)
        self.gate["fresh"] = self.save("fresh.json", self.fresh)
        gate_ref = self.save("gate.json", self.gate)
        for item_id, (proposal, reviews, transcripts) in self.families.items():
            binding = {
                "author_thread": proposal["author_thread"], "payload_sha256": proposal["payload_sha256"],
                "reviews": {role: self.save(f"{item_id}-{role}-review.json", review)
                            for role, review in reviews.items()},
                "dump": {"gate": gate_ref, "table_kind": "noun",
                         "proposal": self.save(f"{item_id}-proposal.json", proposal),
                         "transcriptions": {role: self.save(f"{item_id}-{role}-transcript.json", transcript)
                                            for role, transcript in transcripts.items()}},
            }
            self.registry[item_id]["v5_review_binding"] = binding
            self.judgments["items"][item_id] = binding
        return gate_ref

    def verify(self):
        def git_blob(repo, *args):
            self.assertEqual(repo, self.repo)
            self.assertEqual(args[:2], ("--no-replace-objects", "show"))
            commit, path = args[2].split(":", 1)
            self.assertEqual(commit, self.commit)
            return self.git_files[path]

        with patch.object(aliases, "git", side_effect=git_blob):
            return aliases.acceptance(self.judgments, self.selected, "input", self.scratch, self.registry,
                                      repo=self.repo, sha=self.commit)

    def test_recomputes_dump_proof_and_batches_shared_titles(self):
        self.add_family("mint-two", "menta", "Articulat")
        gate = self.seal()
        with (
            patch.object(aliases, "verify_dump_pages", wraps=aliases.verify_dump_pages) as verify,
            patch.object(aliases, "replay_parser_gate", wraps=aliases.replay_parser_gate) as replay,
        ):
            self.assertEqual(self.verify(), {"mint": gate["sha256"], "mint-two": gate["sha256"]})
            verify.assert_called_once()
            replay.assert_called_once()
            self.assertEqual(len(verify.call_args.args[-1]), 2)

    def test_failed_gate_blocks_before_opening_proposal_or_archive(self):
        for problem in ("verdict", "fresh count", "live revision", "parser hash", "sample bytes"):
            with self.subTest(problem=problem):
                self.gate["verdict"] = "HOLD" if problem == "verdict" else "GO"
                with patch.dict(self.fresh):
                    if problem == "fresh count":
                        self.fresh["pages"] = self.fresh["pages"][:9]
                    if problem == "live revision":
                        first, *others = self.fresh["pages"]
                        self.fresh["pages"] = [{**first, "cached_revision": first["expected_revision"] + 1}, *others]
                    with patch.dict(self.git_files):
                        if problem == "parser hash":
                            self.git_files[aliases.PARSER_PATH] += b"\n# changed"
                        if problem == "sample bytes":
                            path = f"scripts/content_v5/dump_samples/{dump_fixtures.DAY}-sample.json"
                            self.git_files[path] += b"\n"
                        self.seal()
                        (self.scratch / "mint-proposal.json").unlink()
                        with patch.object(aliases, "verify_dump_pages") as verify:
                            with self.assertRaisesRegex(ValueError, "(GO receipt|sample|replay differs|committed parser)"):
                                self.verify()
                            verify.assert_not_called()

    def test_rejects_fabricated_green_report_with_exact_title_and_revision(self):
        first = self.fresh["pages"][0]
        first.update(rendered_pair_count=0, parsed_pair_count=0, cached_body_sha256="a" * 64,
                     cached_receipt_sha256="a" * 64, dump_text_sha256="a" * 64)
        self.seal()
        with self.assertRaisesRegex(ValueError, "additional live replay differs"):
            self.verify()

    def test_requires_retained_historical_and_fresh_cache_evidence(self):
        self.seal()
        historical_title = self.historical["pages"][0]["title"]
        fresh_title = self.fresh["pages"][0]["title"]
        for path, description in ((self.cached_html[historical_title][0], "historical"),
                                  (self.cached_html[fresh_title][1], "additional live")):
            original = path.read_bytes()
            path.unlink()
            with self.subTest(description=description):
                with self.assertRaisesRegex(ValueError, f"{description} replay failed"):
                    self.verify()
            path.write_bytes(original)

    def test_refuses_matching_but_ineligible_registry_provenance(self):
        self.seal()
        provenance = self.registry["mint"]["provenance"]
        original, = provenance
        for extra in ({"scope": "legacy"}, {"scope": "model"}, {"scope": "kg-only"}, {"scope": []},
                      {"origin": "legacy"}, {"status": 429}, {"status": 200.0},
                      {"body_problem": "truncated"}, {"dump_failure": None}):
            with self.subTest(extra=extra):
                provenance[:] = [{**original, **extra}]
                with self.assertRaisesRegex(ValueError, "differs from eligible reviewed registry provenance"):
                    self.verify()
        provenance.append(original)
        self.verify()

    def test_refuses_changed_or_mismatched_transcriptions(self):
        self.seal()
        path = self.scratch / "mint-quality-transcript.json"
        path.write_bytes(path.read_bytes() + b"\n")
        with self.assertRaisesRegex(ValueError, "Artifact SHA-256 differs"):
            self.verify()
        _, _, transcripts = self.families["mint"]
        transcripts["quality"]["cells"] = []
        self.seal()
        with self.assertRaisesRegex(ValueError, "Independent dump transcriptions differ"):
            self.verify()
        transcripts["quality"]["thread_id"] = "a-different-reader"
        self.seal()
        with self.assertRaisesRegex(ValueError, "does not bind the quality S5 reviewer"):
            self.verify()

    def test_refuses_s5_reject_wrong_table_and_shared_gate_reviewer(self):
        _, reviews, _ = self.families["mint"]
        reviews["quality"]["child_safe"] = False
        self.seal()
        with self.assertRaisesRegex(ValueError, "quality judgment did not accept"):
            self.verify()
        reviews["quality"]["child_safe"] = True
        reviews["quality"]["sources"][0]["table_kind"] = "adjective"
        self.seal()
        with self.assertRaisesRegex(ValueError, "quality does not cite the exact dump table"):
            self.verify()
        reviews["quality"]["sources"][0]["table_kind"] = "noun"
        self.gate["reviewer_thread"] = reviews["quality"]["thread_id"]
        self.seal()
        with self.assertRaisesRegex(ValueError, "gate reviewer must be distinct"):
            self.verify()

    def test_refuses_raw_revision_registry_provenance_and_wrong_parser_cell(self):
        self.seal()
        self.registry["mint"]["provenance"][0]["first_fetcher"] = "a-different-fetcher"
        with self.assertRaisesRegex(ValueError, "differs from eligible reviewed registry provenance"):
            self.verify()
        self.registry["mint"]["provenance"][0]["first_fetcher"] = "fixture"
        proposal, reviews, transcripts = self.families["mint"]
        for source in [proposal["source"], *(doc["source"] for doc in transcripts.values()),
                       *(doc["sources"][0]["source"] for doc in reviews.values())]:
            source["revision_id"] += 1
        self.seal()
        with self.assertRaisesRegex(ValueError, "Raw dump page differs"):
            self.verify()
        for source in [proposal["source"], *(doc["source"] for doc in transcripts.values()),
                       *(doc["sources"][0]["source"] for doc in reviews.values())]:
            source["revision_id"] -= 1
        for doc, key in [(proposal, "proposed_cells"), *((doc, "cells") for doc in transcripts.values())]:
            doc[key][0][0] = "Articulat"
        self.seal()
        with self.assertRaisesRegex(ValueError, "Proposed cells differ from the gated parser"):
            self.verify()

    def test_refuses_proposer_as_archive_first_fetcher_and_tampered_archive(self):
        proposal, _, _ = self.families["mint"]
        proposal["author_thread"] = "fixture"
        self.seal()
        with self.assertRaisesRegex(ValueError, "archive first fetcher is the author"):
            self.verify()
        dump = self.cache / (self.receipt["sha256"] + ".dump")
        dump.write_bytes(dump.read_bytes() + b"\n")
        with self.assertRaisesRegex(ValueError, "historical replay failed.*archive byte count differs"):
            self.verify()


if __name__ == "__main__":
    unittest.main()
