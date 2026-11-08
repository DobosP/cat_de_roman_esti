"""Portable stdlib tests for the V4 landing tools."""
from contextlib import redirect_stdout
import hashlib
import copy
import io
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

sys.dont_write_bytecode = True
LANDING = Path(__file__).resolve().parents[1] / "scripts" / "landing"
sys.path.insert(0, str(LANDING))
from kgdiff import compare_content
from play import LocalHTTP, check_alias, check_contexto_win, find_contexto, planned_board, play, scope, verify_server
from run_4i import gate_tree_entry, go_environment, prepare_source, run_checks, stage_assets
from support import BUILD, DESCRIPTOR, EMBED, LOCK, LOCK_COPY, SYNC, digest, relative_parts


def docs():
    return {
        "kg": {
            "kg_nodes": [{"id": "n1", "label_ro": "Cireș", "aliases": ["cireșii"]}],
            "kg_edges": [{"id": "e1", "label_ro": "produce"}],
            "kg_puzzles": [],
        },
        "pack": {"conexiuni": [{"id": "cx1", "status": "approved"}]},
        "quick": None,
        "derived": None,
        "rankings": {"boards": [{"id": "cx1", "game": "conexiuni", "status": "approved", "pilot_eligible": False}]},
    }


def packed(directory, name, data):
    path = directory / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return digest(data)


class Diffs(unittest.TestCase):
    def test_added_concept_edges_forms_boards_and_neighbor(self):
        before = docs()
        after = copy.deepcopy(before)
        after["kg"]["kg_nodes"].append({"id": "n2", "label_ro": "Cireșică", "aliases": ["ciresii"]})
        after["kg"]["kg_edges"][0]["label_ro"] = "crește"
        after["kg"]["kg_edges"].append({"id": "e2", "src_id": "n2", "dst_id": "n1"})
        after["pack"]["conexiuni"].append({"id": "cx2", "status": "approved", "order": ["n2"]})
        after["rankings"]["boards"].append({"id": "cx2", "game": "conexiuni", "status": "approved", "pilot_eligible": True})
        result = compare_content(before, after)
        self.assertEqual([row["id"] for row in result["concepts"]["added"]], ["n2"])
        self.assertEqual(result["concepts"]["changed"], [])
        self.assertEqual(result["edges"]["changed"][0]["fields"]["label_ro"], {"before": "produce", "after": "crește"})
        self.assertEqual(result["edges"]["added"][0]["id"], "e2")
        self.assertEqual(result["boards"]["conexiuni"]["added"][0]["id"], "cx2")
        self.assertEqual(result["boards"]["conexiuni"]["eligibility"]["added"], ["cx2"])
        self.assertEqual(result["aliases"]["added"], [{"id": "n2", "label": "Cireșică", "form": "ciresii"}])
        collision = next(row for row in result["fuzzy_neighbors"] if row["text"] == "ciresii")
        self.assertEqual(collision["before"][0]["owners"], [("n1", "cireșii")])

    def test_alias_removal_is_separate_from_concept_change(self):
        before = docs()
        after = copy.deepcopy(before)
        after["kg"]["kg_nodes"][0]["aliases"] = []
        after["pack"]["conexiuni"][0]["order"] = ["n1"]
        result = compare_content(before, after)
        self.assertEqual(result["aliases"]["removed"][0]["form"], "cireșii")
        self.assertEqual(result["concepts"]["changed"], [])
        self.assertEqual(result["boards"]["conexiuni"]["changed"][0]["id"], "cx1")

    def test_duplicate_identity_fails_closed(self):
        after = docs()
        after["kg"]["kg_nodes"] *= 2
        with self.assertRaisesRegex(ValueError, "duplicate"):
            compare_content(docs(), after)


class BuildAndChecks(unittest.TestCase):
    def test_go_forces_offline_defaults_and_ignores_inherited_app_environment(self):
        with patch.dict(os.environ, {"GOFLAGS": "-skip .*", "CAT_ACCOUNTS_ENABLED": "1",
                                     "GOENV": "/outside", "GOPROXY": "https://example.invalid"}):
            env = go_environment()
        self.assertEqual(env["GOPROXY"], "off")
        self.assertEqual(env["GOENV"], "off")
        self.assertEqual(env["GOTOOLCHAIN"], "local")
        self.assertEqual(env["GOFLAGS"], "-mod=readonly -buildvcs=false")
        self.assertNotIn("CAT_ACCOUNTS_ENABLED", env)

    def test_wrapper_tree_uses_portable_paths_modes_and_exclusions(self):
        content = hashlib.sha256(b"sample").digest()
        self.assertEqual(gate_tree_entry("scripts/example.sh", 0o755, content),
                         b"scripts/example.sh\0x\0" + content)
        self.assertEqual(gate_tree_entry(".gate.env", 0o644, content), b".gate.env\0-\0" + content)
        for path in ("frontend/dist/file", "nested/.env.local", ".gate/result.json", "TASK_BRIEF.md"):
            with self.subTest(path=path):
                self.assertIsNone(gate_tree_entry(path, 0o644, content))

    def test_wrong_projected_tree_fails_before_staging_assets(self):
        with patch("run_4i.extract_source", return_value="a" * 64), patch("run_4i.stage_assets") as stage:
            with self.assertRaisesRegex(ValueError, "Git-projected source tree differs"):
                prepare_source(Path("repo"), "b" * 40, Path("mirror"), Path("source"), b"receipt",
                               {"tree_sha256": "c" * 64}, {})
            stage.assert_not_called()

    def test_confined_asset_paths_on_all_hosts(self):
        for path in ("../asset", "assets//file", "C:/outside", "assets\\escape", "/outside", "a/./b", "assets/.. /escape", "assets/NUL.txt"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                relative_parts(path)
        self.assertEqual(relative_parts("dist/.vite/manifest.json"), ["dist", ".vite", "manifest.json"])

    def test_receipt_bound_generated_assets_and_tamper(self):
        with tempfile.TemporaryDirectory(prefix="cat landing ") as path:
            root = Path(path)
            mirror, target = root / "mirror", root / "snapshot"
            asset_receipt = {
                "schema": 1, "sha": "a"*40, "tree_sha256": "b"*64, "toolchain_digest": "sha256:" + "c"*64,
                "legacy_sha256": "d"*64,
            }
            artifacts = {}
            for tree in ("dist", "legacy"):
                rows = []
                for name, body in (("index.html", b"asset"), (".vite/manifest.json", b"{}")):
                    sha = packed(mirror, f"{EMBED}/{tree}/{name}", body)
                    rows.append({"path": name, "bytes": len(body), "sha256": sha})
                asset_receipt[tree], asset_receipt[f"{tree}_files"] = rows, len(rows)
            asset_receipt["manifest_sha256"] = asset_receipt["dist"][1]["sha256"]
            receipt = {key: asset_receipt[key] for key in ("sha", "tree_sha256", "toolchain_digest")}
            receipt["versions_lock_sha256"] = packed(target, LOCK, b"{}")
            packed(target, f"{EMBED}/build/dist/.keep", b"")
            identity = {key: receipt[key] for key in ("sha", "tree_sha256", "versions_lock_sha256")}
            identity["manifest_sha256"] = asset_receipt["manifest_sha256"]
            artifacts[DESCRIPTOR] = packed(mirror, DESCRIPTOR, json.dumps(identity).encode())
            artifacts[LOCK_COPY] = packed(mirror, LOCK_COPY, b"{}")
            artifacts[SYNC] = packed(mirror, SYNC, json.dumps(asset_receipt).encode())
            packed(target, "legacy/original-bundle.json",
                   json.dumps({"sha256": asset_receipt["legacy_sha256"], "files": asset_receipt["legacy"]}).encode())
            packed(mirror, BUILD, b"build receipt")
            packed(mirror, f"{EMBED}/dist/unlisted.js", b"bad")
            stage_assets(mirror, target, b"build receipt", receipt, artifacts)
            self.assertEqual((target / EMBED / "dist/index.html").read_bytes(), b"asset")
            self.assertFalse((target / EMBED / "dist/unlisted.js").exists())
            (target / EMBED / "dist/index.html").unlink()
            packed(mirror, f"{EMBED}/dist/index.html", b"other")
            with self.assertRaisesRegex(ValueError, "Managed asset differs"):
                stage_assets(mirror, target, b"build receipt", receipt, artifacts)

    def test_all_ten_checks_run_after_a_failure(self):
        with tempfile.TemporaryDirectory(prefix="cat landing ") as path:
            root = Path(path)
            with patch("run_4i.subprocess.run") as runner, redirect_stdout(io.StringIO()):
                runner.side_effect = [Mock(returncode=1)] + [Mock(returncode=0) for _ in range(9)]
                results = run_checks("go", root, root, root, "a"*40, "b"*40, {})
            self.assertEqual([row["exit_code"] for row in results], [1] + [0]*9)
            calls = [call.args[0] for call in runner.call_args_list]
            self.assertEqual(len(calls), 10)
            self.assertIn("-count=1", calls[5])
            self.assertIn("-count=1", calls[7])
            self.assertEqual(calls[9][-3:], ["a"*40, "b"*40, "--"])
            self.assertEqual(len(list(root.glob("*.log"))), 10)


class Playback(unittest.TestCase):
    def test_url_only_accepts_literal_local_ipv4_and_explicit_port(self):
        self.assertEqual(LocalHTTP("http://127.0.0.1:8000").port, 8000)
        for url in ("http://localhost:80", "https://127.0.0.1:80", "http://127.0.0.1",
                    "http://local@127.0.0.1:80", "http://127.0.0.1:80/api", "http://127.0.0.1:80?redirect=1"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                LocalHTTP(url)

    def test_local_request_refuses_redirect_without_second_connection(self):
        with patch("play.HTTPConnection") as connection:
            response = connection.return_value.getresponse.return_value
            response.status = 302
            response.headers = {"Location": "https://example.invalid/"}
            with self.assertRaisesRegex(ValueError, "HTTP 302"):
                LocalHTTP("http://127.0.0.1:8000").request("GET", "/api/gui-build")
            connection.assert_called_once_with("127.0.0.1", 8000, timeout=30)
            response.read.assert_not_called()

    def test_server_manifest_digest_is_required_before_gameplay(self):
        identity = {"sha": "a"*40, "tree_sha256": "b"*64, "manifest_sha256": "c"*64,
                    "versions_lock_sha256": "d"*64}
        http = Mock()
        http.request.return_value = {**identity, "manifest_sha256": "e"*64}
        with self.assertRaisesRegex(ValueError, "build identity differs"):
            verify_server(http, identity, {})
        http.request.assert_called_once_with("GET", "/api/gui-build")

    def test_content_manifest_version_is_type_strict(self):
        identity = {"sha": "a"*40}
        manifest = {"schema_version": 1, "manifest_version": 1}
        for version in manifest:
            with self.subTest(version=version):
                http = Mock()
                http.request.side_effect = [identity, {**manifest, version: True}]
                with self.assertRaisesRegex(ValueError, "content identity differs"):
                    verify_server(http, identity, manifest)

    def test_cald_seed_and_win_require_the_exact_board_shelf(self):
        query = {"category": "istorie", "difficulty": "normal", "seed": 1}
        shelf = {"board_category": "istorie", "difficulty": "normal"}
        initial = {**shelf, "won": False, "attempts": 0}
        guess = {"id": "owner"}
        won = {"ok": True, "won": True, "attempts": 1, "guess": guess, "guesses": [guess]}
        http = Mock()
        http.create.return_value = ("/cald", {**initial, "board_category": "geografie"})
        with self.assertRaisesRegex(ValueError, "wrong shelf"):
            find_contexto(http)(1, "normal", "istorie")
        with self.assertRaisesRegex(ValueError, "Invalid initial Cald game"):
            check_contexto_win(http, query, "alias", "owner", "label")
        http.create.return_value = ("/cald", initial)
        http.request.side_effect = [won, {**won, **shelf, "target": guess, "difficulty": "greu"}]
        with self.assertRaisesRegex(ValueError, "did not survive reload"):
            check_contexto_win(http, query, "alias", "owner", "label")
        http.request.side_effect = [won, {**won, **shelf, "target": guess}, {}]
        check_contexto_win(http, query, "alias", "owner", "label")

    def test_lant_uses_exact_directed_caption_for_the_actual_move(self):
        board = {"id": "lt1", "game": "lant", "category": "history", "difficulty": "normal",
                 "payload": {"start": "n1", "target": "n2", "optimal": 1}}
        initial = {"board_category": "history", "difficulty": "normal", "start": {"id": "n1"},
                   "target": {"id": "n2"}, "optimal": 1, "won": False}
        plan = {"pack_id": "lt1", "query": {"category": "history", "difficulty": "normal", "seed": "0"},
                "initial": initial, "steps": [{"action": "move", "payload": {"text": "Word"}}]}
        move = {"ok": True, "current": {"id": "n2"}, "relation": "a scris", "moves": 1, "won": True,
                "path": [{"id": "n1"}, {"id": "n2", "relation": "a scris"}]}
        http = Mock()
        http.create.return_value = ("/lant", initial)
        with patch("play.subprocess.run", return_value=Mock(stdout=json.dumps(plan).encode())):
            http.request.side_effect = [move, {**move, "target": {"id": "n2"}}]
            self.assertEqual(planned_board(http, board, Path("planner"), 10, {"n1\0n2": "a scris"}), 0)
            http.request.side_effect = [move]
            with self.assertRaisesRegex(ValueError, "caption differs"):
                planned_board(http, board, Path("planner"), 10, {"n1\0n2": "a publicat", "n2\0n1": "a scris"})

    def test_alias_is_checked_in_both_orders_and_reloaded(self):
        row = {"id": "n1", "label": "Cireș", "form": "cireșii"}
        record = {"id": "n1"}
        http = Mock()
        http.create.return_value = ("/contexto", {})
        http.request.return_value = {"guess": record, "guesses": [record], "won": False, "ok": True, "attempts": 1}
        result = check_alias(http, lambda *args: "other", row, [], 3)
        self.assertEqual(result["repeat_seed"], 0)
        self.assertEqual([call.args[2]["text"] for call in http.request.call_args_list if call.args[0] == "POST"],
                         ["Cireș", "cireșii", "cireșii", "Cireș"])
        self.assertEqual(sum(call.args[0] == "GET" for call in http.request.call_args_list), 2)
        http.request.return_value["attempts"] = 2
        with self.assertRaisesRegex(ValueError, "single expected slot"):
            check_alias(http, lambda *args: "other", row, [], 3)

    def test_changed_and_touched_rounds_are_deduplicated_and_invalid_ids_fail(self):
        change = {"boards": {"conexiuni": {"added": [], "changed": [{"id": "cx1"}, {"id": "cx3"}]}},
                  "aliases": {"added": []}}
        bundled = {"pack_items": [
            {"id": board_id, "game": "conexiuni", "status": "approved", "pilot_eligible": eligible}
            for board_id, eligible in (("cx1", True), ("cx2", True), ("cx3", False))
        ]}
        boards, blocked, _ = scope(change, bundled, ("cx1", "cx2", "cx2", "cx3", "missing"))
        self.assertEqual([board["id"] for board in boards], ["cx1", "cx2"])
        self.assertEqual(blocked, [("conexiuni", "cx3"), ("unknown", "missing")])
        _, blocked_without_touched, _ = scope(change, bundled)
        self.assertEqual(blocked_without_touched, [])

    def test_quick_and_unselectable_rounds_fail_aggregate(self):
        change = {"aliases": {"added": []}, "boards": {
            "intrusul": {"added": [{"id": "i1"}]}, "conexiuni": {"added": [{"id": "cx1"}]},
        }}
        bundled = {"pack_items": [{"id": "cx1", "game": "conexiuni", "status": "approved", "pilot_eligible": False}]}
        boards, blocked, _ = scope(change, bundled)
        self.assertEqual(boards, [])
        self.assertEqual(len(blocked), 2)
        with redirect_stdout(io.StringIO()) as lines:
            self.assertEqual(play(Mock(), change, bundled, None, 10), 1)
        self.assertEqual(json.loads(lines.getvalue().splitlines()[-1])["failures"], 2)


@unittest.skipUnless(shutil.which("bash") and os.name == "posix" and hasattr(socket, "AF_UNIX"), "POSIX preflight")
class Preflight(unittest.TestCase):
    def test_only_two_read_only_docker_commands_on_local_socket(self):
        with tempfile.TemporaryDirectory() as path, socket.socket(socket.AF_UNIX) as sock:
            root = Path(path)
            sock.bind(str(root / "docker.sock"))
            pin = "sha256:" + "a"*64
            fake_bin = root / "bin"
            fake_bin.mkdir()
            fake_git = fake_bin / "git"
            fake_git.write_text(f'#!/bin/sh\ncase "$3" in\nrev-parse) printf "%s\\n" "$2" ;;\nshow) printf "%s\\n" TOOLCHAIN_IMAGE=roedu-toolchain:fixture TOOLCHAIN_DIGEST={pin} ;;\n*) exit 33 ;;\nesac\n')
            fake_docker = fake_bin / "docker"
            fake_docker.write_text(f'#!/bin/sh\nprintf "%s\\n" "$*" >> "$OBSERVED"\ncase "$3 $4" in\n"image inspect") echo {pin} ;;\n"network ls") echo gate-example_default ;;\n*) exit 34 ;;\nesac\n')
            fake_git.chmod(0o700)
            fake_docker.chmod(0o700)
            log = root / "docker.log"
            environment = {**os.environ, "PATH": f"{fake_bin}{os.pathsep}{os.environ['PATH']}",
                           "CAT_LANDING_DOCKER_SOCKET": str(root / "docker.sock"),
                           "DOCKER_HOST": "tcp://example.invalid", "DOCKER_CONTEXT": "remote", "OBSERVED": str(log)}
            result = subprocess.run(["bash", str(LANDING / "preflight.sh"), str(root)], capture_output=True,
                                    text=True, timeout=15, env=environment)
            self.assertEqual(result.returncode, 0, result.stderr)
            commands = log.read_text().splitlines()
            self.assertEqual(len(commands), 2)
            self.assertIn(f"--host unix://{root}/docker.sock image inspect", commands[0])
            physical = root.resolve()
            suffix = hashlib.sha256(os.fsencode(physical)).hexdigest()[:12]
            project = f"gate-{physical.parent.name}-{physical.name}-{suffix}"
            self.assertIn(f"network ls --filter label=com.docker.compose.project={project} ", commands[1])


if __name__ == "__main__":
    unittest.main()
