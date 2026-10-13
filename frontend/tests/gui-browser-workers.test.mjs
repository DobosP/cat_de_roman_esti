import test from "node:test";
import assert from "node:assert/strict";
import { guiBrowserWorkers } from "../../scripts/gui-browser-workers.mjs";

void test("GUI browser workers use all four permitted workers and honor a lower wrapper limit", () => {
  for (const value of [1, 2, 3, 4]) {
    assert.equal(guiBrowserWorkers({ GOMAXPROCS: String(value) }, "# cap\nGATE_PARALLEL_MAX=4\n"), value);
  }
  assert.equal(guiBrowserWorkers({ GOMAXPROCS: "2" }, "GATE_PARALLEL_MAX=2\n"), 2);
});

void test("GUI browser workers refuse missing, malformed, duplicated or excessive resource limits", () => {
  for (const cap of ["", "GATE_PARALLEL_MAX=0", "GATE_PARALLEL_MAX=5", "GATE_PARALLEL_MAX=4\r",
    "GATE_PARALLEL_MAX=4\nGATE_PARALLEL_MAX=4", "GATE_PARALLEL_MAX=4 # override"]) {
    assert.throws(() => guiBrowserWorkers({ GOMAXPROCS: "4" }, cap));
  }
  for (const value of [undefined, "", "0", "5", "2.5", "04", "4\n"]) {
    assert.throws(() => guiBrowserWorkers({ GOMAXPROCS: value }, "GATE_PARALLEL_MAX=4"));
  }
  assert.throws(() => guiBrowserWorkers({ GOMAXPROCS: "4" }, "GATE_PARALLEL_MAX=2"));
});
