"""Focused tests for the V4 seed and current journal boundaries."""

import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
from collections import Counter
from copy import deepcopy
from itertools import islice
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "docs/content-registry"
SPEC = importlib.util.spec_from_file_location(
    "content_registry", ROOT / "scripts/content_registry.py"
)
assert SPEC and SPEC.loader
registry = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(registry)


class FakeLanded:
    def __init__(self, paths):
        self.blobs = paths

    def read(self, path):
        return registry.Input(path, self.blobs[path], "landed")


def transition(row, new_state, **kwargs):
    return {
        **deepcopy(row),
        **kwargs,
        "state": new_state,
        "event": "transition",
        "previous_sha256": registry.digest(registry.encode(row).encode("utf-8")),
    }


class RegistryTest(unittest.TestCase):
    def setUp(self):
        self.ref = {"scope": "v3-seed", "path": "input.jsonl", "line": 4, "sha256": "a" * 64}

    def row(self, raw_state="ACTIVE_UNASSESSED", **kwargs):
        return registry.candidate("test", "1", "form", "Frunză", raw_state, self.ref, **kwargs)

    def test_v3_states_preserve_dispositions(self):
        expected = {
            "ACTIVE_UNASSESSED": "idea",
            "SOURCE_NEEDED": "parked(source)",
            "COMPATIBILITY_UNRESOLVED": "parked(screen)",
            "ALREADY_SERVED": "already_served",
            "INACTIVE_HELD": "held_recorded",
            "INACTIVE_REJECTED": "rejected",
        }
        for old, new in expected.items():
            with self.subTest(state=old):
                row = self.row(old)
                self.assertEqual(new, row["state"])
                self.assertTrue(row["retry_when"]["predicate"])
                self.assertEqual("legacy", row["provenance"][0]["fetched_by_role"])
        self.assertEqual(
            [{"kind": "recorded", "ref": "input.jsonl:4"}], self.row("INACTIVE_HELD")["holds"]
        )

    def test_round_trip_and_read_only_replay(self):
        first = self.row()
        next_row = transition(first, "screened")
        with tempfile.TemporaryDirectory() as root:
            output = Path(root) / "output"
            registry.write_seed(output, [first], {})
            journal = output / "registry.jsonl"
            expected = (registry.encode(first) + "\n").encode("utf-8")
            self.assertEqual(expected, journal.read_bytes())
            self.assertEqual(
                {"test:1": first}, registry.current_rows(registry.read_journal(journal))
            )
            with self.assertRaisesRegex(ValueError, "already exists"):
                registry.write_seed(output, [next_row], {})
            self.assertEqual(expected, journal.read_bytes())
            self.assertEqual({"test:1": next_row}, registry.current_rows([first, next_row]))

    def test_invalid_events_and_legacy_approvals_are_rejected(self):
        row = self.row()
        with self.assertRaisesRegex(ValueError, "Duplicate candidate"):
            registry.current_rows([row, row])
        with self.assertRaisesRegex(ValueError, "predecessor mismatch"):
            registry.current_rows([row, {**transition(row, "screened"), "previous_sha256": "0"}])
        with self.assertRaisesRegex(ValueError, "skipped a gate"):
            registry.current_rows([row, transition(row, "qualified")])
        with self.assertRaisesRegex(ValueError, "changed lane"):
            registry.current_rows([row, transition(row, "screened", lane="B")])
        for origin in ("v3-seed", "v4"):
            create = deepcopy(row)
            create["origin"]["source"]["scope"] = origin
            for state in ("screened", "qualified", "landed", "retracted(reason)"):
                with (
                    self.subTest(origin=origin, state=state),
                    self.assertRaisesRegex(
                        ValueError,
                        "cannot start in an advanced state",
                    ),
                ):
                    registry.current_rows([{**create, "state": state}])
        with self.assertRaisesRegex(ValueError, "cannot confer approval"):
            registry.current_rows(
                [
                    {
                        **row,
                        "provenance": [
                            {**row["provenance"][0], "fetched_by_role": "quality"},
                        ],
                    }
                ]
            )

    def test_provenance_is_append_only(self):
        row = self.row()
        legacy = row["provenance"][0]
        for bad in (
            [],
            [{**legacy, "fetched_by_role": "factual"}],
            [{**legacy, "sha256": "b" * 64}],
        ):
            with (
                self.subTest(provenance=bad),
                self.assertRaisesRegex(
                    ValueError,
                    "rewrote provenance",
                ),
            ):
                registry.current_rows([row, transition(row, "screened", provenance=bad)])
        next_ = transition(row, "screened", provenance=[legacy, {**legacy, "path": "other.json"}])
        self.assertEqual(next_, registry.current_rows([row, next_])["test:1"])

    def source_rows(self, receipt, *, row=None, on_screened=False):
        row = self.row() if row is None else row
        screened = transition(row, "screened")
        if on_screened:
            screened["provenance"].append(receipt)
        sourced = transition(screened, "sourced")
        if receipt is not None and not on_screened:
            sourced["provenance"].append(receipt)
        return [row, screened, sourced]

    def test_source_client_receipt_binds_receipt_body_and_first_fetch(self):
        url = "https://ro.wiktionary.org/wiki/frunz%C4%83"
        receipt_name = f"{registry.digest(url.encode('ascii'))}.receipt.json"
        receipt = {
            "path": f"cache/{receipt_name}",
            "url": url,
            "sha256": registry.digest(b"immutable cache receipt"),
            "body_sha256": registry.digest(b"captured body"),
            "fetched_by_role": "script",
            "first_fetch_origin": "v5",
            "first_fetcher": "test-script",
        }
        rows = self.source_rows(receipt)
        self.assertEqual(rows[-1], registry.current_rows(rows)[rows[-1]["id"]])
        for changes in (
            {"path": "model-proposal.json"},
            {"path": f"cache/{receipt_name.replace('.receipt.', '.response.')}"},
            # A redirect's initial URL does not name its final receipt.
            {"path": f"cache/{registry.digest(b'https://ro.wiktionary.org/wiki/frunza')}.receipt.json"},
            {"body_sha256": receipt["sha256"]},
            {"body_sha256": "bogus"},
            {"first_fetch_origin": "legacy"},
            {"first_fetcher": " "},
            {"fetched_by_role": "author"},
            {"fetched_by_role": "model"},
            {"scope": "model"},
            {"status": 404},
            {"body_problem": "incomplete"},
            {"body_problem": []},
            {"scope": []},
            {"scope": None},
            {"status": 200.0},
            {"dump_failure": False},
        ):
            with (
                self.subTest(changes=changes),
                self.assertRaisesRegex(ValueError, "needs a source"),
            ):
                registry.current_rows(self.source_rows({**receipt, **changes}))
        wiki = "https://ro.wiktionary.org"
        raw = "https://raw.githubusercontent.com"
        for url in (
            "https://ro.wiktionary.org@other.example/wiki/a",
            f"{wiki}/robots.txt",
            f"{wiki}/%72obots.txt",
            f"{wiki}/wiki/a%Z1",
            f"{wiki}/wiki/a?q=%Q0",
            f"{wiki}/wiki/a%ff",
            f"{wiki}/wiki/a%c4%83",
            f"{wiki}/wiki/%61",
            f"{wiki}/wiki/a?",
            f"{wiki}/wiki/a{{b",
            f"{wiki}/terms",
            f"{wiki}/wiki/Wik%C8%9Bionar:Termeni_de_utilizare",
            "https://ro.wikipedia.org/wiki/Wikipedia:Termeni_de_utilizare",
            "https://ro.wikipedia.org/wiki/W%C4%B0K%C4%B0PEDIA:Termeni_de_utilizare",
            "https://www.wikidata.org/wiki/Wikidata:Terms_of_use",
            f"{wiki}/wiki/a%00",
            f"{wiki}/wiki/%2e%2e/a",
            f"{wiki}/wiki/./a",
            f"{wiki}/wiki//a",
            f"{wiki}/wiki/a%2fb",
            f"{wiki}/wiki/a%5cb",
            f"{wiki}/wiki/a%252fb",
            f"{raw}/other/FrequencyWords/master/ro.txt",
            f"{raw}/hermitdave/FrequencyWords/master",
            f"{raw}/hermitdave/FrequencyWords/master/",
            f"{raw}/hermitdave/FrequencyWords/master/ro.txt?ignored=1",
            f"{raw}/hermitdave/FrequencyWords/master/r%20o.txt",
        ):
            with self.subTest(url=url), self.assertRaisesRegex(ValueError, "needs a source"):
                name = f"{registry.digest(url.encode('ascii'))}.receipt.json"
                registry.current_rows(self.source_rows({**receipt, "url": url, "path": name}))
        frequency_url = f"{raw}/hermitdave/FrequencyWords/master/content/2018/ro/ro_50k.txt"
        name = f"{registry.digest(frequency_url.encode('ascii'))}.receipt.json"
        frequency_rows = self.source_rows({**receipt, "url": frequency_url, "path": name})
        self.assertEqual(frequency_rows[-1], registry.current_rows(frequency_rows)[rows[-1]["id"]])
        for bad in (
            None, False, "0" * 64, "f" * 64, "deadbeef" * 8, registry.EMPTY_SHA256,
            receipt["sha256"].upper(),
        ):
            with self.subTest(sha=bad), self.assertRaisesRegex(ValueError, "needs a source"):
                registry.current_rows(self.source_rows({**receipt, "sha256": bad}))
        with self.assertRaisesRegex(ValueError, "needs a source"):
            registry.current_rows(self.source_rows(receipt, on_screened=True))

    def test_dump_receipt_requires_a_specific_romanian_wiktionary_revision(self):
        url = "https://dumps.wikimedia.org/rowiktionary/20261101/rowiktionary-20261101"
        receipt = {
            "archive_url": url + "-pages-articles.xml.bz2",
            "archive_receipt_sha256": registry.digest(b"archive receipt"),
            "archive_sha256": registry.digest(b"archive bytes"),
            "title": "frunză",
            "revision_id": 123,
            "text_sha256": registry.digest(b"revision bytes"),
            "first_fetch_origin": "v5",
            "first_fetcher": "dump-fetch-script",
            "fetched_by_role": "script",
        }
        rows = self.source_rows(receipt)
        self.assertEqual(rows[-1], registry.current_rows(rows)[rows[-1]["id"]])
        for changes in (
            {"archive_url": url + "-sha1sums.txt"},
            {"archive_url": receipt["archive_url"].replace("rowiktionary", "rowiki")},
            {"archive_url": receipt["archive_url"].replace("20261101", "20261131")},
            {"archive_url": receipt["archive_url"].replace("-20261101-", "-20261102-")},
            {"archive_receipt_sha256": receipt["archive_sha256"]},
            {"archive_sha256": None},
            {"text_sha256": "f" * 64},
            {"title": ""},
            {"revision_id": True},
            {"revision_id": 0},
            {"fetched_by_role": "factual"},
            {"dump_failure": "checksum failed"},
        ):
            with (
                self.subTest(changes=changes),
                self.assertRaisesRegex(ValueError, "needs a source"),
            ):
                registry.current_rows(self.source_rows({**receipt, **changes}))

    def test_kg_board_receipt_pins_a_tracked_blob_and_excludes_other_lanes(self):
        # Use the repo's real tracked fixture and ignore the working tree copy.
        commit = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True)
        commit = commit.strip()
        data = subprocess.check_output(
            ["git", "-C", str(ROOT), "show", f"{commit}:{registry.KG_PATH}"]
        )
        receipt = {
            "scope": "kg-only",
            "fetched_by_role": "script",
            "path": registry.KG_PATH,
            "commit": commit,
            "sha256": registry.digest(data),
        }
        board = {**self.row(), "type": "board.contexto", "class": "P", "lane": "B"}
        rows = self.source_rows(receipt, row=board)
        self.assertEqual(rows[-1], registry.current_rows(rows, ROOT)[board["id"]])
        with self.assertRaisesRegex(ValueError, "needs a source"):
            registry.current_rows(rows)
        with self.assertRaisesRegex(ValueError, "needs a source"):
            registry.current_rows(rows, ROOT / "docs")
        git_dir = subprocess.check_output(
            ["git", "-C", str(ROOT), "rev-parse", "--absolute-git-dir"], text=True
        ).strip()
        with tempfile.TemporaryDirectory() as outside:
            with patch.dict(os.environ, GIT_DIR=git_dir, GIT_WORK_TREE=outside):
                with self.assertRaisesRegex(ValueError, "needs a source"):
                    registry.current_rows(rows, Path(outside))
                self.assertEqual(rows[-1], registry.current_rows(rows, ROOT)[board["id"]])
        for changes in (
            {"sha256": registry.digest(b"wrong bytes")},
            {"commit": "HEAD"},
            {"commit": "1" * 40},
            {"path": "../kg_sample.json"},
            {"scope": "model"},
            {"fetched_by_role": "author"},
        ):
            with (
                self.subTest(changes=changes),
                self.assertRaisesRegex(ValueError, "needs a source"),
            ):
                registry.current_rows(self.source_rows({**receipt, **changes}, row=board), ROOT)
        for row in (
            self.row(),
            {**board, "type": "board.perechi", "lane": "Q"},
            {**board, "lane": "G"},
            {**board, "origin": {**board["origin"], "kind": "model"}},
        ):
            with self.subTest(row=row["type"]):
                with self.assertRaisesRegex(ValueError, "needs a source"):
                    registry.current_rows(self.source_rows(receipt, row=row), ROOT)

    def test_exact_legacy_sourced_exception_does_not_cover_new_events(self):
        for old_id in ("v5-b2:prospect_contexto_f2331b7b66dc1171", "v5-f1:frunza"):
            with self.subTest(id=old_id):
                events = registry.read_journal(REGISTRY / "registry.jsonl")
                historical = list(islice((row for row in events if row["id"] == old_id), 3))
                self.assertEqual("sourced", historical[-1]["state"])
                self.assertEqual(historical[-1], registry.current_rows(historical)[old_id])
                edited = {**historical[-1], "label_ro": "Edited"}
                with self.assertRaisesRegex(ValueError, "needs a source"):
                    registry.current_rows([*historical[:-1], edited])
        with self.assertRaisesRegex(ValueError, "needs a source"):
            registry.current_rows(self.source_rows(None))

    def test_side_state_releases_require_bound_retry_evidence(self):
        for raw in ("INACTIVE_HELD", "SOURCE_NEEDED", "COMPATIBILITY_UNRESOLVED", "ALREADY_SERVED"):
            with self.subTest(raw_state=raw), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                first = self.row(raw)
                proof = {
                    "candidate_id": first["id"],
                    "prerequisite": first["retry_when"],
                    "previous_sha256": registry.digest(registry.encode(first).encode("utf-8")),
                    "verdict": "resolved",
                }
                data = ("{}\n" + registry.encode(proof) + "\n").encode("utf-8")
                (root / "proof.jsonl").write_bytes(data)
                evidence = {
                    "prerequisite": first["retry_when"],
                    "ref": "proof.jsonl:2",
                    "sha256": registry.digest(data),
                }
                for bad in (
                    True,
                    {**evidence, "sha256": "0" * 64},
                    {**evidence, "sha256": "a" * 64},
                    {**evidence, "prerequisite": {"predicate": "wrong"}},
                    {**evidence, "ref": "missing.jsonl:2"},
                    {**evidence, "ref": "proof.jsonl:1"},
                    {**evidence, "ref": "proof.jsonl:3"},
                    {**evidence, "ref": "../proof.jsonl:2"},
                    {**evidence, "ref": f"{root / 'proof.jsonl'}:2"},
                ):
                    with self.assertRaisesRegex(ValueError, "exact retry evidence"):
                        registry.current_rows(
                            [first, transition(first, "idea", retry_evidence=bad)],
                            root,
                        )
                with self.assertRaisesRegex(ValueError, "rewrote a retry prerequisite"):
                    registry.current_rows(
                        [
                            first,
                            transition(
                                first,
                                first["state"],
                                retry_when={"predicate": "changed"},
                            ),
                        ],
                    )
                next_ = transition(first, "idea", holds=[], retry_evidence=evidence)
                with self.assertRaisesRegex(ValueError, "exact retry evidence"):
                    registry.current_rows([first, next_])
                self.assertEqual(next_, registry.current_rows([first, next_], root)["test:1"])

                for field in ("candidate_id", "previous_sha256", "prerequisite", "verdict"):
                    wrong = (registry.encode({**proof, field: "wrong"}) + "\n").encode("utf-8")
                    (root / "proof.jsonl").write_bytes(wrong)
                    wrong_evidence = {
                        **evidence,
                        "ref": "proof.jsonl:1",
                        "sha256": registry.digest(wrong),
                    }
                    with self.assertRaisesRegex(ValueError, "exact retry evidence"):
                        registry.current_rows(
                            [first, transition(first, "idea", retry_evidence=wrong_evidence)],
                            root,
                        )

        locked = self.row("INACTIVE_HELD", state="held_owner", rule="owner.md:4")
        with self.assertRaisesRegex(ValueError, "Owner hold is locked"):
            registry.current_rows([locked, transition(locked, "idea")])

    def test_adr_0210_sofa_cannot_reopen_with_retry_receipt(self):
        sofa = next(
            row
            for row in registry.read_journal(REGISTRY / "registry.jsonl")
            if row["origin"].get("record_id") == "v115-sofa"
        )
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            evidence = {
                "prerequisite": sofa["retry_when"],
                "ref": "fabricated.jsonl:1",
                "sha256": "0" * 64,
            }
            with self.assertRaisesRegex(ValueError, "exact retry evidence"):
                registry.current_rows(
                    [sofa, transition(sofa, "idea", retry_evidence=evidence)], root
                )

            proof = {
                "candidate_id": sofa["id"],
                "prerequisite": sofa["retry_when"],
                "previous_sha256": registry.digest(registry.encode(sofa).encode("utf-8")),
                "verdict": "resolved",
            }
            data = (registry.encode(proof) + "\n").encode("utf-8")
            (root / "fabricated.jsonl").write_bytes(data)
            evidence["sha256"] = registry.digest(data)
            with self.assertRaisesRegex(ValueError, "exact retry evidence"):
                registry.current_rows(
                    [sofa, transition(sofa, "idea", retry_evidence=evidence)], root
                )

    def test_exclusions_are_direct_literals_in_landed_script_tree(self):
        landed = FakeLanded(
            {
                "scripts/active_data.py": b"raise RuntimeError('never run')\n"
                b"BLOCKED_ALIAS_FORMS: tuple[str, ...] = ('hold',)\n"
                b"DEFERRED_TEST = (*OLD, 'other')\n",
                "docs/content-stock/archive/archived_data.py": b"DEFERRED_TEST = ('archive',)\n",
                "scripts/active_helper.py": b"DEFERRED_TEST = ('helper',)\n",
            }
        )
        rows = registry.lexical_exclusions(landed)
        self.assertEqual(["hold", "other"], [r["literal"] for r in rows])
        self.assertEqual([2, 3], [r["source"]["line"] for r in rows])

    def test_exact_lexical_owner_rules(self):
        self.assertEqual("ie", registry.owner_rule("a", "n_v1_33_ie", "Ie", ["II"]))
        self.assertEqual("family", registry.owner_rule("b", "n_v84_food_sucitor", "Făcăleț", []))
        self.assertEqual("sucitoare", registry.owner_rule("c", "other", "other", ["sucitoare"]))
        self.assertIsNone(registry.owner_rule("d", "other", "other", ["iei", "sucitoarele"]))

    def test_committed_seed_has_exact_owner_membership(self):
        # Milestone 0 is the first 2,683 rows of the append-only live journal.
        events = registry.read_journal(REGISTRY / "registry.jsonl")
        rows = registry.current_rows(islice(events, 2683))
        exclusions = json.loads((REGISTRY / "exclusions.json").read_bytes())
        owners = {
            row["origin"]["id"]
            for row in rows.values()
            if row["state"] == "held_owner" and row["type"] == "board.conexiuni"
        }
        self.assertEqual(79, len(owners))
        self.assertEqual(owners, set(exclusions["owner_held_conexiuni"]))
        self.assertEqual(87, Counter(row["state"] for row in rows.values())["held_owner"])
        self.assertEqual(2683, len(rows))
        self.assertEqual(
            1741,
            sum(
                any(ref["path"].startswith(f"{registry.ARCHIVE}/") for ref in row["provenance"])
                for row in rows.values()
            ),
        )
        bulk = {
            row["origin"]["record_id"]: row
            for row in rows.values()
            if row["id"].startswith("bulk-001:")
        }
        for id_ in ("v141-vesela", "v142-fosila", "v142-felie", "v115-dus"):
            self.assertEqual("held_recorded", bulk[id_]["state"])
        scoped_holds = {
            key for key, row in bulk.items() if row["retry_when"]["predicate"] == "owner_answer"
        }
        self.assertEqual(
            {
                "v115-sofa",
                "v117-bol",
                "v138-iepuras",
                "v126-lavoar",
                "v122-covoras_de_baie",
                "v139-ursoaica",
                "v140-patent",
                "v122-prelungitor",
                "v139-lupoaica",
                "v139-vulpoi",
            },
            scoped_holds,
        )
        self.assertEqual(62, sum(len(bulk[id_]["payload"]["forms"]) for id_ in scoped_holds))
        self.assertTrue(all(bulk[id_]["state"] == "held_recorded" for id_ in scoped_holds))
        primary_refs = {
            "v115-sofa": ("scripts/contexto_common_words_v44_data.py", 39),
            "v117-bol": ("scripts/basic_words_v30_data.py", 250),
            "v138-iepuras": ("scripts/basic_words_v30_data.py", 243),
        }
        for key, pair in primary_refs.items():
            self.assertIn(pair, {(ref["path"], ref["line"]) for ref in bulk[key]["provenance"]})
        v133 = [
            row
            for id_, row in bulk.items()
            if id_.startswith("v133-") and row["state"] == "parked(source)"
        ]
        self.assertEqual(29, len(v133))
        self.assertTrue(all(row["origin"]["state"] == "ACTIVE_UNASSESSED" for row in v133))
        for id_ in ("v121-eticheta", "v121-punga"):
            self.assertEqual("parked(source)", bulk[id_]["state"])
            self.assertEqual("continuous/ledger.jsonl:350", bulk[id_]["retry_when"]["ref"])

    def test_live_journal_replays_with_repository_evidence_root(self):
        events = list(registry.read_journal(REGISTRY / "registry.jsonl"))
        rows = registry.current_rows(events, ROOT)
        self.assertEqual({event["id"] for event in events}, set(rows))
        self.assertIn("v5-p2-f2:grindina", rows)


if __name__ == "__main__":
    unittest.main()
