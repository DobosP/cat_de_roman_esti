"""Exercise the promoted miner CLIs without writing repository content."""
import hashlib
import itertools
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


TOOLS = Path(__file__).resolve().parents[1] / "scripts" / "miner"
ROOT = Path(os.environ.get("CAT_MINER_REPLAY_ROOT", TOOLS.parents[1])).resolve()
FIXTURES = ROOT / "cat_de_roman_esti" / "fixtures"


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
    return path


def load(path):
    return json.loads(path.read_bytes())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ContentMinerTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.scratch = Path(directory.name).resolve()

    def call(self, name, *arguments, expected=0):
        result = subprocess.run(
            [sys.executable, "-I", "-B", str(TOOLS / (name + ".py")),
             *map(str, arguments), "--scratch-root", str(self.scratch)],
            cwd=self.scratch, text=True, encoding="utf-8", capture_output=True, timeout=180,
        )
        self.assertEqual(result.returncode, expected, result.stderr)
        return result

    def test_need_map_reads_all_six_games(self):
        out = self.scratch / "needs.json"
        self.call("need_map", "--root", ROOT, "--out", out)
        value = load(out)
        self.assertEqual({row["game"] for row in value["cells"]},
                         {"conexiuni", "contexto", "lant", "alchimie", "intrusul", "perechi"})
        self.assertTrue(value["source_bindings"])
        before = digest(out)
        self.call("need_map", "--root", ROOT, "--out", out, expected=2)
        self.assertEqual(digest(out), before)

    def test_index_and_bounded_mine_replay(self):
        index = self.scratch / "index.json"
        out = self.scratch / "mine.json"
        self.call("compat_index", "--root", ROOT, "--out", index)
        value = load(index)
        self.assertFalse(value["complete_static_screen"])
        self.assertTrue(value["unresolved"])
        self.assertTrue(value["tombstones"])
        self.assertTrue(value["native_authorities"]["normalized_index"])
        held = {row.get("owner_label") for row in value["owner_rulings"]
                if row.get("hold") == "explicit_owner_approval_required"}
        self.assertEqual(held, {"Mănăstire", "Sucitor"})
        args = ("--root", ROOT, "--compat", index, "--cell", "cx:gastronomie:normal",
                "--cell", "cx:geografie:normal", "--per-cell", 3, "--budget", 4000, "--max-starts", 10)
        self.call("mine", *args, "--out", out)
        result = load(out)
        self.assertEqual(result["status"], "unapproved_prospects")
        self.assertEqual(result["compat_binding"]["sha256"], digest(index))
        self.assertEqual(len(result["cells"]), 2)
        pack = load(FIXTURES / "games_pack.json")["conexiuni"]
        tombstones = list(load(FIXTURES / "conexiuni_rejection_tombstones.json")["items"].values())
        seen = pack + tombstones
        for cell in result["cells"]:
            self.assertLessEqual(len(cell["candidates"]), 3)
            self.assertGreater(cell["reject_counts"].get("conexiuni_three_tile_quad_overlap", 0), 0)
            for candidate in cell["candidates"]:
                groups = candidate["payload"]["groups"].values()
                tiles = set(itertools.chain.from_iterable(groups))
                for row in seen:
                    old_groups = row["groups"].values()
                    self.assertLess(len(tiles.intersection(itertools.chain.from_iterable(old_groups))), 8)
                    self.assertTrue(all(len(set(group).intersection(other)) < 3
                                        for group in groups for other in old_groups))
                seen.append(candidate["payload"])
        value["source_bindings"][0]["sha256"] = "0" * 64
        save(index, value)
        self.assertIn("stale compat binding", self.call("mine", *args, "--out",
                                                       self.scratch / "stale.json", expected=2).stderr)

    def test_scratch_escape_is_refused(self):
        with tempfile.TemporaryDirectory() as outside:
            target = Path(outside) / "escaped.json"
            result = self.call("need_map", "--root", ROOT, "--out", target, expected=2)
            self.assertIn("outside allowed tree", result.stderr)
            self.assertFalse(target.exists())
            try:
                (self.scratch / "link").symlink_to(outside, target_is_directory=True)
            except (NotImplementedError, OSError):
                return
            self.call("need_map", "--root", ROOT, "--out", self.scratch / "link" / target.name, expected=2)
            self.assertFalse(target.exists())

    def test_edited_compat_index_cannot_remove_canonical_lant_debt(self):
        program = """
import collections
import sys
sys.path.insert(0, sys.argv[1])
from mine import Miner, Repo, FIX
repo = Repo(sys.argv[2])
miner = Miner(repo, {'signatures': [], 'tombstones': []}, 1, 1, 1)
miner.game = 'lant'
miner.results = []
miner.rejects = collections.Counter()
debt = repo.data(FIX + 'lant_rejection_tombstones.json')['items']
assert debt, 'expected canonical rejection debt'
for row in debt.values():
    assert not miner.emit(row, {}, [], [])
assert not miner.results
assert miner.rejects['existing_or_tombstoned_signature'] == len(debt)
"""
        result = subprocess.run([sys.executable, "-IB", "-c", program, str(TOOLS), str(ROOT)],
                                text=True, capture_output=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stderr)

    def critic(self, game, row, *, flags=(), expected=0):
        candidate = save(self.scratch / (game + "-candidate.json"),
                         {**row, "rationale": "AUTHOR_ONLY_SENTINEL", "sources": ["https://source.invalid/private"]})
        public = self.scratch / (game + "-public.json")
        key = self.scratch / (game + "-key.json")
        result = self.call("critic_blind", "build", "--root", ROOT, "--input", candidate,
                           "--game", game, "--public-out", public, "--key-out", key, *flags,
                           expected=expected)
        return public, key, result

    def compare(self, key, response, out, expected=0):
        source = save(self.scratch / "response.json", response)
        return self.call("critic_blind", "compare", "--key", key, "--response", source, "--out", out,
                         expected=expected)

    def test_blind_gameplay_tasks_and_wrong_responses(self):
        pack = load(FIXTURES / "games_pack.json")
        quick = load(FIXTURES / "derived_catalog_v38.json")["boards"]
        rows = {game: pack[game][0] for game in ("conexiuni", "lant", "contexto")}
        rows.update({game: next(row for row in quick if row["game"] == game)
                     for game in ("intrusul", "perechi")})
        for game, row in rows.items():
            with self.subTest(game=game):
                flags = ("--raw-cald-diagnostic",) if game == "contexto" else ()
                public, key, _ = self.critic(game, row, flags=flags)
                value = load(public)
                allowed = {"schema", "challenge_id", "game", "task", "response_schema"}
                if game != "contexto":
                    allowed.add("tiles")
                if game == "lant":
                    allowed.update(("start", "target", "par", "choices"))
                self.assertEqual(set(value), allowed)
                self.assertNotIn("AUTHOR_ONLY_SENTINEL", public.read_text(encoding="utf-8"))
                self.assertNotIn(row["id"], public.read_text(encoding="utf-8"))
                self.assertEqual(load(key)["public_binding"]["sha256"], digest(public))
                response = {"challenge_id": value["challenge_id"], "ambiguous": False}
                if game == "contexto":
                    response["openers"] = ["arbore", "casă", "apă", "câine", "drum"]
                out = self.scratch / (game + "-comparison.json")
                self.compare(key, response, out)
                comparison = load(out)
                self.assertIsNone(comparison["approval"])
                self.assertEqual(comparison["status"], "raw_cald_diagnostic_only" if game == "contexto"
                                 else "critic_filter_failure")

    def test_exact_partition_remains_mechanical_and_hash_bound(self):
        row = load(FIXTURES / "games_pack.json")["conexiuni"][0]
        public, key, _ = self.critic("conexiuni", row)
        groups = load(key)["expected_answer"]["groups"]
        response = {"challenge_id": load(public)["challenge_id"], "ambiguous": False, "groups": groups,
                    "predicates": ["test"] * 4, "recognizable_groups": 4,
                    "tile_explanations": {tile: "test" for group in groups for tile in group}}
        out = self.scratch / "comparison.json"
        self.compare(key, response, out)
        self.assertTrue(load(out)["mechanical_match"])
        self.assertIsNone(load(out)["approval"])
        public.write_bytes(public.read_bytes() + b" ")
        result = self.compare(key, response, self.scratch / "tampered.json", expected=2)
        self.assertIn("public task missing or hash changed", result.stderr)

    def test_unbound_gameplay_modes_refuse(self):
        pack = load(FIXTURES / "games_pack.json")
        cases = (("contexto", pack["contexto"][0], "cap-eight"),
                 ("alchimie", pack["alchimie"][0], "--audit"),
                 ("lant", {**pack["lant"][0], "id": "lt_smoke_prospective"}, "native caption artifact"))
        for game, row, reason in cases:
            with self.subTest(game=game):
                public, key, result = self.critic(game, row, expected=2)
                self.assertIn(reason, result.stderr)
                self.assertFalse(public.exists())
                self.assertFalse(key.exists())

    @unittest.skipUnless(hasattr(os, "mkfifo"), "FIFO unavailable on this platform")
    def test_fifo_refused_without_blocking(self):
        fifo = self.scratch / "pipe.json"
        os.mkfifo(fifo)
        result = self.call("critic_blind", "build", "--root", ROOT, "--input", fifo, "--public-out",
                           self.scratch / "public.json", "--key-out", self.scratch / "key.json", expected=2)
        self.assertIn("not a regular file", result.stderr)

    def test_ambiguous_json_refused(self):
        out = self.scratch / "public.json"
        candidate = self.scratch / "candidate.json"
        for data in (b'{"id":1,"id":2}', b'{"number":1e400}', b'\xef\xbb\xbf{}'):
            with self.subTest(data=data):
                candidate.write_bytes(data)
                result = self.call("critic_blind", "build", "--root", ROOT, "--input", candidate,
                                   "--public-out", out, "--key-out", self.scratch / "key.json", expected=2)
                self.assertNotIn("Traceback", result.stderr)
                self.assertFalse(out.exists())

    def test_forged_alchimie_audit_is_refused(self):
        row = load(FIXTURES / "games_pack.json")["alchimie"][0]
        audit = save(self.scratch / "forged.json", {"schema": "alchimie-live-projection-audit-v1",
                     "game": "alchimie", "mode": "gate", "status": "pending", "input_ids": [row["id"]]})
        # The audit hash is checked before trusting its contents or trying to execute the tool.
        flags = ("--audit", audit, "--audit-sha256", "0" * 64, "--audit-dossier-dir", self.scratch,
                 "--audit-tool", sys.executable, "--audit-tool-sha256", "0" * 64)
        public, key, result = self.critic("alchimie", row, flags=flags, expected=2)
        self.assertIn("audit hash changed", result.stderr)
        self.assertFalse(public.exists())
        self.assertFalse(key.exists())

    def test_review_sidecar_mechanics(self):
        paths = []
        envs = []
        receipts = []
        fetched_at = "2026-11-09T00:07:00Z"
        author = save(self.scratch / "author.json", {"author": "author-test-identity",
                      "sealed_at": "2026-11-09T00:00:00Z", "unsealed_at": "2026-11-09T00:10:00Z",
                      "urls": ["https://source.invalid/author?a=1&b=2"]})
        capture = self.scratch / "capture.txt"
        capture.write_text("synthetic test receipt", encoding="utf-8")
        for role in ("factual", "quality"):
            reviewer = "job-identity-" + role
            url = f"https://source.invalid/{role}"
            raw = save(self.scratch / (role + "-raw.json"),
                       {"reviewer": reviewer, "items": [
                           {"id": "smoke", "sources": [url], "rationale": f"Source sample for {role}"},
                           {"id": "kg-board", "sources": [], "rationale": f"Board sample for {role}"}]})
            path = self.scratch / (role + ".json")
            env = {"reviewer": reviewer, "role": role, "review_path": str(raw), "review_sha256": digest(raw),
                   "signed_at": "2026-11-09T00:09:00Z", "first_peer_read_at": None,
                   "child_safe_by_item": {"smoke": True, "kg-board": True}, "reviewer_chosen_sources": {"smoke": [
                       {"url": url, "chosen_by": reviewer, "fetched_by_role": role, "fetched_at": fetched_at,
                        "capture_path": str(capture), "capture_sha256": digest(capture)}]}}
            receipts.append({"url": url, "fetched_by_role": role, "fetched_at": fetched_at,
                             "capture_sha256": digest(capture)})
            paths.append(save(path, env))
            envs.append(env)
        artifact_rows = []
        for i in range(1, 6):
            path = save(self.scratch / f"artifact-{i}.json", {"stage": i})
            artifact_rows.append({"stage": f"M{i}", "path": str(path), "sha256": digest(path)})
        artifacts = save(self.scratch / "artifacts.json", {"artifacts": artifact_rows})
        manifest = save(self.scratch / "frozen.json", {"items": {"smoke": "source_backed", "kg-board": "kg_only"},
                                                      "receipts": receipts})
        args = ("--author-seal", author, "--reviews", *paths, "--artifacts", artifacts,
                "--manifest", manifest, "--manifest-sha256", digest(manifest))
        out = self.scratch / "independence.json"
        self.call("review_independence", *args, "--out", out)
        self.assertEqual(load(out)["status"], "PASS")
        envs[0]["reviewer_chosen_sources"]["smoke"][0]["fetched_by_role"] = "legacy"
        envs[0]["reviewer_chosen_sources"]["smoke"][0]["fetched_at"] = "2026-11-09T00:10:00Z"
        envs[0]["first_peer_read_at"] = "2026-11-09T00:05:00Z"
        envs[0]["child_safe_by_item"]["smoke"] = False
        save(paths[0], envs[0])
        artifact_rows[1] = {**artifact_rows[0], "stage": "M2"}
        save(artifacts, {"artifacts": artifact_rows})
        out = self.scratch / "invalid-independence.json"
        self.call("review_independence", *args, "--out", out, expected=1)
        errors = "\n".join(load(out)["errors"])
        for reason in ("independently fetched", "first-fetch receipt before signing", "peer read before both signed",
                       "child-safe affirmation", "artifact reused"):
            self.assertIn(reason, errors)


if __name__ == "__main__":
    unittest.main()
