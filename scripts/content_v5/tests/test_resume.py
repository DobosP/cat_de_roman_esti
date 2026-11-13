"""Focused tests for append-only V5 campaign recovery (standard library only)."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "resume.py"
AT = "2026-11-13T10:00:00Z"
SHA = "a" * 40
JOB = {"job_id": "j1", "train_id": None, "item_ids": ["tool1"], "lane": "phase0",
       "game": "shared", "role": "author", "thread_id": "thread1"}
TOKENS = {"tokens_uncached_in": 3, "tokens_out": 5, "tokens_cached": 11}


class ResumeTests(unittest.TestCase):
    def setUp(self):
        # Keep test artifacts under the caller's test scratch, or the tool's own directory.
        test_root = Path(os.environ.get("CAT_V5_TEST_SCRATCH", Path.cwd())).resolve()
        self.temp = tempfile.TemporaryDirectory(prefix=".v5-resume-test-", dir=test_root)
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.contract = {
            "campaign": "test-v5", "base_sha": SHA,
            "ends": {"days": 7, "goal_meter_tokens": 40000000},
            "threads": {"max": 2}, "train": {"max_open": 1}, "start_quota_pct_max": 20,
        }
        self.write_contract()
        self.ledger = self.directory / "ledger.jsonl"

    def write_contract(self):
        (self.directory / "contract.json").write_text(json.dumps(self.contract), encoding="utf-8")

    def call(self, *args, data=None, succeeds=True):
        result = subprocess.run(
            [sys.executable, "-I", str(SCRIPT), "--campaign-dir", str(self.directory), *args],
            input=data, capture_output=True, check=False, text=True,
        )
        if succeeds:
            self.assertEqual(result.returncode, 0, result.stderr)
            return json.loads(result.stdout)
        self.assertEqual(result.returncode, 1, result.stderr)
        return result.stderr

    def append(self, event, *, succeeds=True, **fields):
        return self.call("append", data=json.dumps({"event": event, "at": AT, **fields}),
                         succeeds=succeeds)

    def resume(self, quota=19, meter=100, at=AT, ordinary="yes", *args, succeeds=True):
        return self.call("resume", "--quota-pct", str(quota), "--goal-meter-tokens", str(meter),
                         "--ordinary-usage", ordinary, "--at", at, *args, succeeds=succeeds)

    def test_quota_boundaries(self):
        self.assertEqual(self.resume(20)["mode"], "intake")
        self.assertEqual(self.resume(21)["mode"], "blocked-start")
        self.assertEqual(self.resume(90)["stop_reasons"], ["weekly-quota"])
        self.assertEqual(self.resume(10, ordinary="no")["mode"], "stop")

    def test_owner_override_must_bind_contract_bytes(self):
        import hashlib

        override = {"by": "Paul", "date": "2026-11-13", "quote": "Start below 90%",
                    "start_limit_exclusive": True, "stop_at_pct": 90,
                    "restrict_new_intake_at_pct": 70, "paid_credits": False}
        self.contract.update(start_quota_pct_max=90, quota_override=override)
        self.write_contract()
        self.assertIn("missing contract override",
                      self.append("campaign-start", kit_sha=SHA, quota_pct=38,
                                  goal_meter_tokens=100, ordinary_usage=True, succeeds=False))
        self.assertIn("missing contract override", self.resume(38, succeeds=False))
        self.assertEqual(self.resume(90)["mode"], "stop")
        digest = hashlib.sha256((self.directory / "contract.json").read_bytes()).hexdigest()
        self.append("owner-override", owner="Paul", decision_date=override["date"],
                    quote=override["quote"], contract_sha256=digest, quota_pct=38,
                    previous_start_quota_pct_max=20, start_quota_pct_max=90,
                    start_limit_exclusive=True, stop_at_pct=90, restrict_new_intake_at_pct=70)
        self.assertEqual(self.resume(69)["mode"], "intake")
        self.assertEqual(self.resume(70)["mode"], "finish-judged-only")
        self.assertEqual(self.resume(89)["mode"], "finish-judged-only")
        self.assertEqual(self.resume(90)["mode"], "stop")
        self.append("campaign-start", kit_sha=SHA, quota_pct=38, goal_meter_tokens=100, ordinary_usage=True)
        self.contract["ends"]["days"] = 8
        self.write_contract()
        self.assertIn("override contract digest differs", self.resume(succeeds=False))

    def test_jobs_recovered_by_original_thread_and_metered_once(self):
        self.append("job-dispatch", **JOB)
        self.assertEqual(self.resume()["dispatches_to_poll"][0]["thread_id"], "thread1")
        self.assertEqual(self.resume()["free_slots"], 1)
        self.append("root-meter", **TOKENS)
        self.append("root-meter", **TOKENS)  # Retry after an ambiguous acknowledgement.
        done = {"job_id": "j1", "thread_id": "thread1", "wall_s": 12.5, "verdict": "ready", **TOKENS}
        self.append("job-complete", **done)
        previous = self.ledger.read_bytes()
        self.assertIn("job already completed", self.append("job-complete", **done, succeeds=False))
        self.assertEqual(previous, self.ledger.read_bytes())
        current = self.resume(19, 100, AT, "yes", "--save-state")
        self.assertEqual(current["free_slots"], 2)
        self.assertEqual(current["job_meter"], {**TOKENS, "completed": 1, "wall_s": 12.5})
        self.assertEqual(current["root_meter"], TOKENS)
        state = self.directory / "state.json"
        self.assertLess(state.stat().st_size, 2048)
        state.write_text("corrupt disposable state", encoding="utf-8")
        self.assertEqual(self.resume(), current)

    def test_train_and_clock_advance_only_after_valid_transitions(self):
        self.assertIn("clock must start", self.append("train-open", train_id="t", kind="boards", succeeds=False))
        self.append("campaign-start", kit_sha=SHA, quota_pct=20, goal_meter_tokens=100, ordinary_usage=True)
        self.append("train-open", train_id="t", kind="boards")
        self.assertIn("only one train", self.append("train-open", train_id="other", kind="forms", succeeds=False))
        self.append("train-candidate", train_id="t", sha=SHA)
        self.assertIn("SHA changed", self.append("train-qualified", train_id="t", sha="b" * 40, succeeds=False))
        self.append("train-qualified", train_id="t", sha=SHA)
        self.append("train-landed", train_id="t", sha=SHA)
        expired = "2026-11-20T10:00:00Z"
        snapshot = self.resume(80, 40000100, expired, "yes", "--save-state")
        self.assertEqual(snapshot["stop_reasons"], ["days-spent", "tokens-spent"])
        self.assertEqual(self.resume(80, 40000100, expired)["stop_reasons"], snapshot["stop_reasons"])
        self.assertIsNone(snapshot["active_train"])
        self.assertEqual(snapshot["clock"]["tokens"], 40000000)

    def test_stop_latches_and_prevents_new_work(self):
        current = self.resume(90, 100, AT, "yes", "--save-state")
        self.assertEqual(current["stop_reasons"], ["weekly-quota"])
        self.assertEqual(self.resume(10)["mode"], "stop")
        self.assertIn("campaign stopped", self.append("job-dispatch", succeeds=False, **JOB))

    def test_quota_stop_survives_stale_goal_meter(self):
        self.append("campaign-start", kit_sha=SHA, quota_pct=20, goal_meter_tokens=100, ordinary_usage=True)
        self.assertIn("precedes the campaign", self.resume(90, 99, AT, "yes", "--save-state", succeeds=False))
        self.assertEqual(self.resume(10)["stop_reasons"], ["weekly-quota"])

    def test_elapsed_stop_survives_stale_goal_meter(self):
        self.append("campaign-start", kit_sha=SHA, quota_pct=20, goal_meter_tokens=100, ordinary_usage=True)
        expired = "2026-11-20T10:00:00Z"
        self.assertIn("precedes the campaign", self.resume(19, 99, expired, "yes", "--save-state", succeeds=False))
        self.assertEqual(self.resume(10, 100, expired)["stop_reasons"], ["days-spent"])

    def test_quota_stop_observed_in_turn_survives_reset(self):
        self.append("turn", free_slots=2, queue_len=1, waiting=False, quota_pct=90)
        self.assertEqual(self.resume(1)["stop_reasons"], ["weekly-quota"])
        self.assertIn("campaign stopped", self.append("train-open", train_id="t", kind="boards",
                                                      succeeds=False))

    def test_corrupt_tail_and_duplicate_json_never_written(self):
        duplicate = '{"event":"root-meter","event":"turn","at":"2026-11-13T10:00:00Z"}'
        self.assertIn("duplicate JSON field", self.call("append", data=duplicate, succeeds=False))
        self.assertFalse(self.ledger.exists())
        self.append("job-dispatch", **JOB)
        with self.ledger.open("ab") as handle:
            handle.write(b'{"event":')
        broken = self.ledger.read_bytes()
        self.assertIn("incomplete", self.append("root-meter", **TOKENS, succeeds=False))
        self.assertEqual(self.ledger.read_bytes(), broken)


if __name__ == "__main__":
    unittest.main()
