import assert from "node:assert/strict";
import { test } from "node:test";
import { ensureBaselineDependencies } from "../scripts/gui-baseline-deps.mjs";

function fixture({ complete = false, status = 0, mutate = false, fill = true } = {}) {
  let installed = complete, changed = false;
  const calls = [];
  const io = {
    env: { GATE_SHA: "a".repeat(40), GATE_TREE_SHA256: "b".repeat(64) },
    fs: { existsSync: () => installed, readFileSync: () => Buffer.from(changed ? "changed" : "locked") },
    spawnSync(executable, args, options) {
      calls.push({ executable, args, options });
      installed = fill; changed = mutate;
      return { status, stdout: "", stderr: "" };
    },
  };
  return { io, calls };
}

test("complete dependencies never install or repair existing versions", () => {
  const { io, calls } = fixture({ complete: true });
  ensureBaselineDependencies("/work", io);
  assert.equal(calls.length, 0);
});
test("missing dependencies use one bounded locked install in managed runner", () => {
  const { io, calls } = fixture();
  ensureBaselineDependencies("/work", io);
  assert.equal(calls.length, 1);
  assert.equal(calls[0].executable, "npm");
  assert.deepEqual(calls[0].args, ["ci", "--ignore-scripts", "--include=dev", "--no-audit", "--no-fund"]);
  assert.equal(calls[0].options.cwd, "/work/tools/gui-baseline-quality");
  assert.equal(calls[0].options.timeout, 120000);
});
test("host or unbound installation is refused before npm", () => {
  for (const root of ["/host", "/work"]) {
    const { io, calls } = fixture();
    if (root === "/work") io.env = {};
    assert.throws(() => ensureBaselineDependencies(root, io), /managed Linux runner/);
    assert.equal(calls.length, 0);
  }
});
test("nonzero install, incomplete output and lock mutation remain failures", () => {
  for (const settings of [{ status: 1 }, { fill: false }, { mutate: true }]) {
    const { io } = fixture(settings);
    assert.throws(() => ensureBaselineDependencies("/work", io), /failed|incomplete|changed/);
  }
});
