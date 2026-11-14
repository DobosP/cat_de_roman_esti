"""Focused tests for Pilot 2 additive link preparation and rollback."""

from copy import deepcopy
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import link_install as install


SCRATCH = Path(os.environ.get("CAT_V5_TEST_SCRATCH", Path.cwd()))
REPO = Path(__file__).resolve().parents[3]


def make_item():
    return {
        "id": "word:custom", "source": {},
        "node": {"id": "n_custom", "node_type": "concept", "label_ro": "Testword",
                 "category": "stiinta", "description": "Only a synthetic test definition.", "salience": .5101},
        "links": [
            {"src_id": "n_custom", "dst_id": f"n_{i}", "relation": "related_to",
             "bidirectional": i % 2 == 0, "label_ro": f"relation {i}", "strength": .72}
            for i in range(4)
        ],
    }


def mini():
    return {
        "kg_nodes": [
            {"id": f"n_{i}", "label_ro": label, "category": "stiinta", "node_type": "concept",
             "description": label, "salience": .5, "difficulty_tier": "medium", "degree": 1}
            for i, label in enumerate(("Stea", "Planetă", "Galaxie", "Cometă"))
        ],
        "kg_edges": [
            {"id": "e01", "src_id": "n_0", "dst_id": "n_1", "relation": "related_to",
             "label_ro": "pair", "strength": .55, "is_distractor": 0, "bidirectional": 1}
        ],
        "meta": {},
    }


class LinkInstallTests(unittest.TestCase):
    def test_exact_generation_reuses_existing_graph_operator(self):
        before = mini()
        item = make_item()
        nodes, links = install.merge_input([item], before, before)
        self.assertEqual((nodes, links), ([item["node"]], item["links"]))
        data = deepcopy(before)
        merged_nodes, merged_edges = install.merge_records(data, {
            "nodes": nodes,
            "edges": [{**link, "src": link["src_id"], "dst": link["dst_id"]} for link in links],
        })
        result = install.rebuild_document(data, merged_nodes, merged_edges, "test", "synthetic")
        after = json.loads(result)
        install.exact_additions(before, after, nodes, links)
        self.assertEqual(len(after["kg_nodes"]), 5)
        self.assertEqual(len(after["kg_edges"]), 5)
        self.assertEqual(after["kg_nodes"][-1]["degree"], 4)
        after["kg_edges"][-1]["strength"] = .5
        with self.assertRaisesRegex(ValueError, "altered a frozen link"):
            install.exact_additions(before, after, nodes, links)

    def test_rejects_duplicate_rounding_wrong_owner_and_missing_baseline_neighbors(self):
        graph = mini()
        for issue in ("duplicate", "strength", "no new endpoint", "no baseline words", "same category"):
            with self.subTest(issue=issue):
                candidate, baseline = make_item(), deepcopy(graph)
                if issue == "duplicate":
                    candidate["links"][1] = candidate["links"][0]
                elif issue == "strength":
                    candidate["links"][0]["strength"] = .7284
                elif issue == "no new endpoint":
                    candidate["links"][0]["src_id"] = "n_1"
                elif issue == "no baseline words":
                    baseline["kg_nodes"] = baseline["kg_nodes"][:1]
                else:
                    candidate["node"]["category"] = "limba"
                with self.assertRaises(ValueError):
                    install.merge_input([candidate], graph, baseline)

    def test_shared_new_word_link_must_appear_in_both_frozen_lists(self):
        graph = mini()
        first = make_item()
        second = make_item()
        second["id"] = "word:second"
        second["node"].update(id="n_second", label_ro="Other")
        for link in second["links"]:
            link["src_id"] = "n_second"
        shared = {**first["links"][0], "dst_id": "n_second"}
        first["links"].append(shared)
        with self.assertRaisesRegex(ValueError, "both frozen word reviews"):
            install.merge_input([first, second], graph, graph)
        second["links"].append(shared)
        _, links = install.merge_input([first, second], graph, graph)
        self.assertEqual(links.count(shared), 1)

    def test_dry_run_preserves_backlog_registry_order_and_rejects_other_lane(self):
        def word(id_, state, lane="L2"):
            return {"id": id_, "state": state, "type": "concept", "lane": lane,
                    "origin": {"state": "ACTIVE_UNASSESSED", "source": {"scope": "v3-seed"}}}
        registry = {row["id"]: row for row in (
            word("first-idea", "idea"), word("not-backlog", "sourced", "W"),
            word("z-first-sourced", "sourced"), word("a-second-sourced", "sourced"),
        )}
        self.assertEqual(install.dry_backlog(registry)["id"], "z-first-sourced")

    def test_span_coverage_must_equal_all_additive_links(self):
        link = {k: v for k, v in make_item()["links"][0].items() if k in install.EDGE_KEYS}
        other = {**link, "dst_id": "n_other"}
        body = install.canonical({
            "schema": "cat-v5-link-spans-1",
            "links": [{"link": link, "url": "https://ro.wikipedia.org/wiki/Test",
                       "receipt_sha256": install.digest(b"r"), "body_sha256": install.digest(b"b"),
                       "quote": "A synthetic source span."}],
        })
        ref = {"path": "claims.json", "sha256": install.digest(body)}
        with patch.object(install, "read_artifact", return_value=body):
            with self.assertRaisesRegex(ValueError, "Quote coverage differs"):
                install.verify_span_evidence(SCRATCH, ref, [link, other])
            with patch.object(install, "check_batch", return_value={"status": "fail"}):
                with self.assertRaisesRegex(ValueError, "span check failed"):
                    install.verify_span_evidence(SCRATCH, ref, [link])

    def test_wiktionary_direct_definitions_can_start_immediately_after_marker(self):
        for line in ("#(''bot.'') (''Asparagus officinalis'')", "# Ordinary definition"):
            with self.subTest(line=line):
                self.assertIsNotNone(install.WIKI_DEFINITION.match(line))
        for line in ("## Subdefinition", "#: Example", "#* Citation", "#  : Example", "# \t"):
            with self.subTest(line=line):
                self.assertIsNone(install.WIKI_DEFINITION.match(line))

    def test_frequency_positive_row_cannot_override_source_refusal(self):
        body = b"miner 503\n"
        sha = install.digest(body)
        path = "legacy-cache/" + install.digest(install.FREQUENCY_URL.encode("ascii")) + ".receipt.json"
        for headers in ({}, {"content-signal": "ai-input=no"}, {"content-signal-present": "true"},
                        {"x-robots-tag": "noai"}, {"location": "/other"}):
            with self.subTest(headers=headers):
                receipt = install.canonical({"url": install.FREQUENCY_URL, "status": 200, "sha256": sha,
                                             "bytes": len(body), "headers": headers})
                ref = {"receipt": {"path": path, "sha256": install.digest(receipt)}, "body_sha256": sha}
                with patch.object(install, "read_artifact", side_effect=[receipt, body]):
                    if headers:
                        with self.assertRaisesRegex(ValueError, "ineligible source header"):
                            install.frequency_rows(SCRATCH, ref)
                    else:
                        self.assertEqual(install.frequency_rows(SCRATCH, ref), {"miner": 503})

    def test_item_span_hash_does_not_change_with_train_membership(self):
        item = make_item()
        results = {
            install.link_key(link): {"link": {k: link[k] for k in install.EDGE_KEYS},
                                    "url": "https://ro.wikipedia.org/wiki/Example",
                                    "status": "pass", "quote_sha256": install.digest(b"quote")}
            for link in item["links"]
        }
        before, urls = install.item_span_evidence(item, results)
        self.assertEqual(urls, {"https://ro.wikipedia.org/wiki/Example"})
        results[("n_neighbor", "n_0", "related_to", True)] = {
            "url": "https://ro.wikipedia.org/wiki/Other", "status": "pass"}
        self.assertEqual(install.item_span_evidence(item, results), (before, urls))
        results[install.link_key(item["links"][0])]["quote_sha256"] = install.digest(b"other")
        self.assertNotEqual(install.item_span_evidence(item, results)[0], before)

    def test_publish_rollback_restores_all_four_mirrors(self):
        with tempfile.TemporaryDirectory(prefix="link-rollback-", dir=SCRATCH) as name:
            repo = Path(name)
            pairs = {repo / install.KG: b"kg", repo / install.PACK: b"pack",
                     repo / "tests/fixtures/kg_sample.json": b"kg",
                     repo / "tests/fixtures/games_pack.json": b"pack"}
            for file, value in pairs.items():
                file.parent.mkdir(parents=True, exist_ok=True)
                file.write_bytes(value)
            def inject(path, data):
                if path == repo / install.PACK:
                    raise OSError("injected failure")
                path.write_bytes(data)
            with patch.object(install, "atomic_write", side_effect=inject):
                with self.assertRaisesRegex(OSError, "injected failure"):
                    install.published_outputs(repo, b"kg", b"pack", b"new kg", b"new pack")
            self.assertTrue(all(path.read_bytes() == value for path, value in pairs.items()))
            self.assertFalse((repo / ".cat-content-ops.lock").exists())

    def test_reviewer_binding_refuses_shared_role_or_wrong_span_report(self):
        item = make_item()
        payload_sha = install.digest(install.canonical(item))
        binding = {"author_thread": "author", "payload_sha256": payload_sha,
                   "derived_view_sha256": install.digest(b"view"),
                   "reviews": {role: {"path": role} for role in ("critic", "factual", "quality")}}
        registry = {"v5_word_review_binding": binding, "v5_derived_view_sha256": binding["derived_view_sha256"],
                    "v5_independence_checks": {name: True for name in (
                        "signed_reviews", "rationale_overlap_ok", "reviewer_identity_leaks_checked",
                        "source_reuse_checked")}}
        span = install.digest(b"spans")
        transcript = b"synthetic retained transcript"
        def document(root, reference, label):
            role = reference["path"]
            if role == "critic":
                return {**binding, "role": role, "thread_id": "critic-thread", "verdict": "pass",
                        "item_id": item["id"], "transcript_path": "transcript",
                        "transcript_sha256": install.digest(transcript)}
            return {**binding, "role": role, "thread_id": "shared",
                    "verdict": "accept", "child_safe": True, "item_id": item["id"],
                    "span_result_sha256": span}
        allowed = {"https://ro.wikipedia.org/wiki/Example"}
        with patch.object(install, "verified_json", side_effect=document), patch.object(
            install, "cited_live_sources", return_value=allowed,
        ), patch.object(install, "read_artifact", return_value=transcript):
            with self.assertRaisesRegex(ValueError, "independent quality"):
                install.verify_review(SCRATCH, item, registry, binding, "gate", span, allowed)
            with self.assertRaisesRegex(ValueError, "independent factual"):
                install.verify_review(SCRATCH, item, registry, binding, "gate", "wrong span", allowed)


if __name__ == "__main__":
    unittest.main()
