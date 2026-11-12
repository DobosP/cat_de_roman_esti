import test from "node:test";
import assert from "node:assert/strict";
import * as fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createHash } from "node:crypto";
import { loadUnitReuse, validateUnitReuse, UNIT_REUSE_LANES } from "../../scripts/gui-unit-reuse.mjs";
import { PRODUCER_BUILD_ASSERT, PRODUCER_BUILD_CHECK, PRODUCER_DESCRIPTOR,
  PRODUCER_RACE_ASSERT, producerBuildArgs } from "../../scripts/gui-pending-producer.mjs";

// Synthetic hostile-input contracts, never release or gate qualification evidence.
const hash = (bytes) => createHash("sha256").update(bytes).digest("hex");
const encode = (value) => Buffer.from(JSON.stringify(value) + "\n");
const inner = "12345678-1234-4234-8234-123456789abc";
const outer = "87654321-4321-4321-8321-cba987654321";
const prerequisiteNames = ["bootstrap-evidence", "cat-setup-npm-ci", "versions-check", "toolchain-versions", "lint-scope", "kit:check",
  "cat-active-ui", "cat-doccheck-source-contracts", "cat-doc-check", "cat-content-validate", "cat-content-export", "cat-docs-gate",
  "cat-unit-fresh-build-output", "cat-unit-frontend-build", "cat-unit-emitted-inventory", "cat-unit-assets", "cat-unit-gui-identity",
  "cat-route-budgets", "cat-frozen-legacy-integrity"];
function fixture() {
  const config = { role: "consumer", app: "cat_de_roman_esti", npm_dir: "frontend/node_modules/@roedu/web-kit", vendor_dir: "frontend/vendor", go_dirs: ["go-backend", "shared-go/authcore"] };
  const binding = { sha: "a".repeat(40), tree_sha256: "b".repeat(64), toolchain_digest: `sha256:${"c".repeat(64)}` };
  const context = { target: "full", dirty: false, ...binding, parallel: 4, stage: "enforced", config_sha256: hash(JSON.stringify(config)), started: "2026-10-13T03:00:00.000Z" };
  const captured = { schema: 1, target: "unit", ...binding, config, config_sha256: context.config_sha256,
    command: { command: "task", args: ["--silent", "repo:kit-config"], exit_code: 0, duration_ms: 1, stdout_sha256: hash(encode(config)), stderr_sha256: hash("") } };
  const wrapper = { schema: 1, invocation: outer, target: "unit", ...binding, config_sha256: context.config_sha256,
    config_path: ".gate/unit/wrapper-kit-config.json", config_file_sha256: hash(encode(captured)), operator: "agent:codex" };
  const logs = new Map(), bootstrapArtifacts = [];
  function command(check, executable, args, cwd, prefix = `${inner}-${check}`, bootstrap = false) {
    const action = { [bootstrap ? "phase" : "check"]: check, kind: "command", command: executable, argument_count: args.length,
      args_sha256: hash(JSON.stringify(args)), cwd, exit_code: 0, duration_ms: 5 };
    for (const stream of ["stdout", "stderr"]) {
      const relative = `.gate/unit/logs/${prefix}-0.${stream}.log`, bytes = Buffer.from(stream === "stdout" ? "synthetic command output\n" : "");
      logs.set(relative, bytes); action[`${stream}_sha256`] = hash(bytes); action[`${stream}_log`] = relative;
      if (bootstrap) bootstrapArtifacts.push(`${relative} sha256:${hash(bytes)}`);
    }
    return action;
  }
  const bootstrap = { schema: 1, target: "unit", invocation: inner, ...binding, started: "2026-10-13T02:00:00.000Z", config, config_sha256: context.config_sha256,
    wrapper_target: "unit", wrapper_config: wrapper.config_path, wrapper_config_sha256: hash(encode(captured)), wrapper_invocation: outer,
    wrapper_descriptor: ".gate/wrapper-current.json", wrapper_descriptor_sha256: hash(encode(wrapper)),
    actions: [command("config", "task", ["--silent", "repo:kit-config"], ".", `${inner}-bootstrap-config`, true)],
    artifacts: bootstrapArtifacts, finished: "2026-10-13T02:00:02.000Z" };
  const execution = { schema: 1, invocation: inner, sha: binding.sha, tree_sha256: binding.tree_sha256, actions: [] };
  const commands = [
    ["npm", ["test"], "frontend"], ["npm", ["run", "lint"], "frontend"], ["npm", ["run", "typecheck"], "frontend"],
    ["go", ["test", "-race", "-timeout=30m", "-count=1", "-json", "./..."], "go-backend"],
    ["go", ["vet", "./..."], "go-backend"], ["go", ["test", "-race", "-json", "./..."], "shared-go/authcore"], ["go", ["vet", "./..."], "shared-go/authcore"],
  ];
  for (const [index, name] of UNIT_REUSE_LANES.entries()) {
    execution.actions.push(command(name, ...commands[index]));
    const labels = name === "cat-backend-race" ? ["Backend race requires fresh synced assets and compiled identity inputs", "Only explicit native PG tests may skip without DSN"]
      : name === "cat-backend-vet" ? ["Backend vet requires fresh synced assets and compiled identity inputs"]
        : name === "cat-authcore-race" ? ["Only explicit native PG tests may skip without DSN"] : [];
    execution.actions.push(...labels.map((label) => ({ check: name, kind: "assertion", label, passed: true, duration_ms: 0 })));
  }
  const result = { schema: 1, target: "unit", status: "pass", ...binding, dirty: false, versions_lock_sha256: hash("synthetic versions\n"), parallel: 4,
    started: bootstrap.started, finished: "2026-10-13T02:30:00.000Z",
    checks: [...prerequisiteNames, ...UNIT_REUSE_LANES].map((name) => ({ name, status: "pass", duration_ms: 5 })),
    csp: { stage: "enforced", violations: 0, legacy_violations: 0 }, budgets: {}, artifacts: [] };
  function materialize() {
    // Rebind hashes after semantic mutations, so rejection proves validation of
    // the semantics rather than merely detecting an incidental stale hash.
    wrapper.config_file_sha256 = hash(encode(captured));
    bootstrap.wrapper_config_sha256 = hash(encode(captured));
    bootstrap.wrapper_descriptor_sha256 = hash(encode(wrapper));
    const files = new Map(logs);
    files.set(".gate/unit/execution.json", encode(execution));
    files.set(".gate/unit/bootstrap-execution.json", encode(bootstrap));
    result.artifacts = [...files].map(([name, bytes]) => `${name} sha256:${hash(bytes)}`);
    files.set(".gate/unit/wrapper-current.json", encode(wrapper));
    files.set(".gate/unit/wrapper-kit-config.json", encode(captured));
    files.set(".gate/unit/result.json", encode(result));
    files.set("versions.lock.json", Buffer.from("synthetic versions\n"));
    return files;
  }
  return { context, result, execution, wrapper, captured, bootstrap, logs, command, materialize };
}
function validate(value, files = value.materialize()) {
  return validateUnitReuse(value.context, (name) => { assert.ok(files.has(name), `fixture file missing: ${name}`); return files.get(name); });
}
void test("complete same-SHA unit binds distinct invocations and returns only required evidence", () => {
  const value = fixture(), files = value.materialize(), before = [...files].map(([name, bytes]) => [name, hash(bytes)]);
  const actual = validate(value, files);
  assert.equal(actual.status, "hit"); assert.equal(actual.proof.invocation, inner); assert.equal(actual.proof.wrapper_invocation, outer);
  assert.equal(actual.proof.result_sha256, hash(files.get(".gate/unit/result.json")));
  assert.equal(actual.proof.execution_sha256, hash(files.get(".gate/unit/execution.json")));
  assert.deepEqual(actual.proof.lanes.map((lane) => lane.name), UNIT_REUSE_LANES);
  assert.equal(actual.files.size, 21); assert.equal(actual.files.has("versions.lock.json"), false);
  assert.deepEqual([...files].map(([name, bytes]) => [name, hash(bytes)]), before);
});
const refusals = [
  ["current dirty tree", (v) => { v.context.dirty = true; }],
  ["prior dirty tree", (v) => { v.result.dirty = true; }],
  ["wrong SHA", (v) => { v.result.sha = "d".repeat(40); }],
  ["wrong tree", (v) => { v.result.tree_sha256 = "d".repeat(64); }],
  ["wrong toolchain", (v) => { v.result.toolchain_digest = `sha256:${"d".repeat(64)}`; }],
  ["wrong versions", (v) => { v.result.versions_lock_sha256 = "d".repeat(64); }],
  ["wrong parallel", (v) => { v.result.parallel = 2; }],
  ["wrong CSP stage", (v) => { v.result.csp.stage = "report-only"; }],
  ["CSP violation", (v) => { v.result.csp.violations = 1; }],
  ["legacy CSP violation", (v) => { v.result.csp.legacy_violations = 1; }],
  ["failed overall result", (v) => { v.result.status = "fail"; }],
  ["missing required lane", (v) => { v.result.checks.pop(); }],
  ["missing prerequisite", (v) => { v.result.checks.shift(); }],
  ["duplicate lane", (v) => { v.result.checks.push({ ...v.result.checks.at(-1) }); }],
  ["failed lane", (v) => { v.result.checks.at(-1).status = "fail"; }],
  ["skipped lane", (v) => { v.result.checks.at(-1).status = "skipped"; }],
  ["future result", (v) => { v.result.finished = "2026-10-13T04:00:00.000Z"; }],
  ["wrong execution UUID", (v) => { v.execution.invocation = outer; }],
  ["wrapper UUID equals inner UUID", (v) => { v.wrapper.invocation = inner; v.bootstrap.wrapper_invocation = inner; }],
  ["wrapper target mismatch", (v) => { v.wrapper.target = "full"; }],
  ["unknown wrapper key", (v) => { v.wrapper.extra = true; }],
  ["wrapper operator mismatch", (v) => { v.wrapper.operator = "other"; }],
  ["current config differs", (v) => { v.context.config_sha256 = "d".repeat(64); }],
  ["bootstrap wrong wrapper", (v) => { v.bootstrap.wrapper_invocation = inner; }],
  ["bootstrap missing command", (v) => { v.bootstrap.actions = []; }],
  ["bootstrap failed command", (v) => { v.bootstrap.actions[0].exit_code = 1; }],
  ["bootstrap duplicate stream", (v) => { v.bootstrap.actions[0].stderr_log = v.bootstrap.actions[0].stdout_log; }],
  ["wrong command", (v) => { v.execution.actions[0].command = "true"; }],
  ["wrong command arguments", (v) => { v.execution.actions[0].args_sha256 = hash('["--help"]'); }],
  ["wrong working directory", (v) => { v.execution.actions[0].cwd = "."; }],
  ["failed command", (v) => { v.execution.actions[0].exit_code = 2; }],
  ["duplicate command", (v) => { v.execution.actions.push({ ...v.execution.actions[0] }); }],
  ["missing command", (v) => { v.execution.actions.shift(); }],
  ["failed original assertion", (v) => { v.execution.actions.find((a) => a.kind === "assertion").passed = false; }],
  ["removed original assertion", (v) => { v.execution.actions = v.execution.actions.filter((a) => a.label !== "Only explicit native PG tests may skip without DSN"); }],
  ["substituted assertion", (v) => { v.execution.actions.find((a) => a.kind === "assertion").label = "invented success"; }],
  ["stream traversal", (v) => { v.execution.actions[0].stdout_log = ".gate/unit/../../outside"; }],
];
for (const [name, mutate] of refusals) void test(`reuse refuses ${String(name)}`, () => { const value = fixture(); mutate(value); assert.throws(() => validate(value)); });
for (const filename of [".gate/unit/execution.json", ".gate/unit/bootstrap-execution.json", ".gate/unit/wrapper-current.json", ".gate/unit/wrapper-kit-config.json"]) {
  void test(`reuse refuses missing or corrupt ${filename}`, () => {
    const value = fixture(), files = value.materialize(); files.set(filename, Buffer.from("{}")); assert.throws(() => validate(value, files));
    files.delete(filename); assert.throws(() => validate(value, files));
  });
}
void test("reuse refuses corrupted stdout and stderr, duplicate artifacts and unsafe unused artifacts", () => {
  for (const stream of ["stdout", "stderr"]) {
    const value = fixture(), files = value.materialize(); files.set(value.execution.actions[0][`${stream}_log`], Buffer.from("tampered"));
    assert.throws(() => validate(value, files), /hash differs/);
  }
  for (const artifact of ["duplicate", ".gate/unit/../full/secret sha256:" + "a".repeat(64)]) {
    const value = fixture(), files = value.materialize(); value.result.artifacts.push(artifact === "duplicate" ? value.result.artifacts[0] : artifact);
    files.set(".gate/unit/result.json", encode(value.result)); assert.throws(() => validate(value, files));
  }
});
void test("optional native proof retains only result-bound fixed graph artifacts", () => {
  const value = fixture();
  for (const name of ["native-inputs.json", "native-reuse/graph.stdout.json", "native-reuse/graph.stderr.log", "native-reuse/graph-command.json", "native-reuse/graph.json"]) {
    value.logs.set(`.gate/unit/${name}`, Buffer.from("synthetic native proof"));
  }
  value.logs.set(".gate/unit/unrelated-big-build.bin", Buffer.from("not retained"));
  const files = value.materialize(), actual = validate(value, files);
  assert.equal(actual.files.size, 26); assert.equal(actual.files.has(".gate/unit/unrelated-big-build.bin"), false);
  files.set(".gate/unit/native-inputs.json", Buffer.from("tampered")); assert.throws(() => validate(value, files), /hash differs/);
});
void test("production loader returns miss for absent evidence, refuses symlinks, and reads a confined complete fixture", (t) => {
  const base = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../../.gate"); fs.mkdirSync(base, { recursive: true });
  const root = fs.mkdtempSync(path.join(base, "synthetic-unit-reuse-")); t.after(() => fs.rmSync(root, { force: true, recursive: true }));
  const value = fixture(); assert.equal(loadUnitReuse(root, value.context).status, "miss");
  for (const [name, bytes] of value.materialize()) { fs.mkdirSync(path.dirname(path.join(root, name)), { recursive: true }); fs.writeFileSync(path.join(root, name), bytes); }
  assert.equal(loadUnitReuse(root, value.context).status, "hit");
  const result = path.join(root, ".gate/unit/result.json"), saved = path.join(root, "saved-result.json"); fs.renameSync(result, saved); fs.symlinkSync(saved, result);
  assert.match(loadUnitReuse(root, value.context).reason, /nonregular/);
  fs.unlinkSync(result); fs.renameSync(saved, result);
  const alias = path.join(root, "alias"); fs.symlinkSync(root, alias);
  assert.match(loadUnitReuse(alias, value.context).reason, /root/);
  const logs = path.join(root, ".gate/unit/logs"), savedLogs = path.join(root, "saved-logs"); fs.renameSync(logs, savedLogs); fs.symlinkSync(savedLogs, logs);
  assert.match(loadUnitReuse(root, value.context).reason, /nonregular/);
});
void test("capsule reads current versions and every wrapper-failure marker forces real execution", (t) => {
  const base = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../../.gate"); fs.mkdirSync(base, { recursive: true });
  const directory = fs.mkdtempSync(path.join(base, "synthetic-unit-capsule-")); t.after(() => fs.rmSync(directory, { force: true, recursive: true }));
  const root = path.join(directory, "live"), capsule = path.join(directory, "capsule"); fs.mkdirSync(root); fs.mkdirSync(capsule);
  const value = fixture();
  for (const [name, bytes] of value.materialize()) { fs.mkdirSync(path.dirname(path.join(capsule, name)), { recursive: true }); fs.writeFileSync(path.join(capsule, name), bytes); }
  fs.writeFileSync(path.join(root, "versions.lock.json"), "synthetic versions\n");
  assert.equal(loadUnitReuse(root, value.context, capsule).status, "hit");
  fs.writeFileSync(path.join(root, "versions.lock.json"), "different current versions\n");
  assert.equal(loadUnitReuse(root, value.context, capsule).status, "miss");
  fs.writeFileSync(path.join(root, "versions.lock.json"), "synthetic versions\n");
  const marker = path.join(capsule, ".gate/unit/wrapper-fail.json");
  for (const make of [() => fs.writeFileSync(marker, ""), () => fs.mkdirSync(marker), () => fs.symlinkSync(path.join(directory, "absent"), marker)]) {
    make(); assert.match(loadUnitReuse(root, value.context, capsule).reason, /wrapper failure marker/); fs.rmSync(marker, { recursive: true, force: true });
  }
});

const optInPackage = "github.com/DobosP/cat_de_roman_esti/go-backend/internal/contentops";
const optInTest = "TestQuickPendingActualCompiledProducerReadset";
const producerFile = `.gate/unit/${PRODUCER_DESCRIPTOR}`;

function registeredFixture() {
  const value = fixture();
  value.context.actualPendingProducer = true;
  const descriptor = { schema: 1, target: "unit", invocation: inner, sha: value.result.sha,
    tree_sha256: value.result.tree_sha256, toolchain_digest: value.result.toolchain_digest,
    output: `/tmp/cat-pending-review-producer-${inner}-a123Z9/cat-content-rail`,
    bytes: 40 * 1024 * 1024, sha256: "d".repeat(64) };
  const build = value.command(PRODUCER_BUILD_CHECK, "go", producerBuildArgs(descriptor.output), "go-backend");
  const race = value.execution.actions.find((action) => action.check === "cat-backend-race" && action.kind === "command");
  const assertion = (check, label) => ({ check, kind: "assertion", label, passed: true, duration_ms: 0 });
  value.result.checks.push({ name: PRODUCER_BUILD_CHECK, status: "pass", duration_ms: 5 });
  value.execution.actions.unshift(assertion(PRODUCER_BUILD_CHECK, PRODUCER_BUILD_ASSERT), build);
  value.execution.actions.push(assertion("cat-backend-race", PRODUCER_RACE_ASSERT));
  const base = { Package: optInPackage, Test: optInTest };
  const events = [
    { ...base, Action: "run" },
    { ...base, Action: "output", Output: `    readset_producer_test.go:240: actual unstripped producer ${descriptor.bytes} bytes sha256=${descriptor.sha256}; source executable remained read-only\n` },
    { ...base, Action: "pass" },
    { Package: optInPackage, Action: "pass" },
  ];
  const materialize = (eventBytes = Buffer.concat(events.map(encode)),
    descriptorBytes = Buffer.from(JSON.stringify(descriptor, null, 2) + "\n")) => {
    value.logs.set(producerFile, descriptorBytes);
    value.logs.set(race.stdout_log, eventBytes);
    race.stdout_sha256 = hash(eventBytes);
    return value.materialize();
  };
  return { value, descriptor, build, events, materialize };
}

void test("registered reuse binds the actual producer build, its streams and exact race events", () => {
  const { value, descriptor, build, materialize } = registeredFixture();
  const files = materialize(), actual = validate(value, files);
  assert.deepEqual(actual.proof.lanes.map((lane) => lane.name), UNIT_REUSE_LANES);
  assert.deepEqual(actual.proof.pending_review_producer, {
    descriptor: producerFile, descriptor_sha256: hash(files.get(producerFile)), build_action_sha256: hash(JSON.stringify(build)),
    executable_bytes: descriptor.bytes, executable_sha256: descriptor.sha256,
  });
  assert.equal(actual.files.size, 24);
  assert.equal(actual.files.has(descriptor.output), false);
  const historical = fixture(); historical.context.actualPendingProducer = true;
  assert.throws(() => validate(historical), /build check missing/);
  value.context.actualPendingProducer = false;
  assert.throws(() => validate(value, files), /unexpected pending producer/);
});

void test("registered reuse refuses stale build identities and incomplete or malformed exact race output", () => {
  const variants = [
    (v) => { v.value.result.checks.pop(); },
    (v) => { v.descriptor.invocation = outer; },
    (v) => { v.descriptor.output = "/tmp/unowned/cat-content-rail"; },
    (v) => { v.descriptor.bytes = 32 * 1024 * 1024; },
    (v) => { v.build.args_sha256 = hash('["build","-ldflags=-s -w"]'); },
    (v) => { v.value.execution.actions.push(...v.value.execution.actions.splice(0, 2)); },
    (v) => { v.value.execution.actions.pop(); },
    (v) => { v.events.splice(0, 1); },
    (v) => { v.events.splice(1, 0, v.events[0]); },
    (v) => { v.events[2].Action = "skip"; },
    (v) => { v.events[2].Package = "other"; },
    (v) => { v.events[1].Output = v.events[1].Output.replace(/^.*actual /, "actual "); },
    (v) => { v.events[1].Output = v.events[1].Output.replace("41943040", "41943041"); },
    (v) => { v.events[1].Output = v.events[1].Output.replace("d".repeat(64), "e".repeat(64)); },
    (v) => { v.events.push({ Package: optInPackage, Action: "output", Output: "(cached)" }); },
  ];
  for (const mutate of variants) {
    const value = registeredFixture(); mutate(value);
    assert.throws(() => validate(value.value, value.materialize()), /pending producer|cat-backend-race/);
  }
  const value = registeredFixture();
  assert.throws(() => validate(value.value, value.materialize(Buffer.from("{malformed\n"))), /exact pending producer events/);
  const files = value.materialize();
  files.delete(producerFile);
  assert.throws(() => validate(value.value, files), /fixture file missing/);
});

void test("the production loader derives registration from the live projection and treats stale proofs as misses", (t) => {
  const base = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../../.gate"); fs.mkdirSync(base, { recursive: true });
  const root = fs.mkdtempSync(path.join(base, "synthetic-producer-reuse-")); t.after(() => fs.rmSync(root, { force: true, recursive: true }));
  function install(files) {
    for (const [name, bytes] of files) {
      fs.mkdirSync(path.dirname(path.join(root, name)), { recursive: true });
      fs.writeFileSync(path.join(root, name), bytes);
    }
  }
  const historical = fixture();
  install(historical.materialize());
  assert.equal(loadUnitReuse(root, historical.context).status, "hit");
  const registration = path.join(root, "go-backend/internal/contentops/readset_producer_test.go");
  fs.mkdirSync(path.dirname(registration), { recursive: true }); fs.writeFileSync(registration, "synthetic registration");
  assert.match(loadUnitReuse(root, historical.context).reason, /build check missing/);
  const registered = registeredFixture();
  install(registered.materialize());
  assert.equal(loadUnitReuse(root, historical.context).status, "hit");
  fs.writeFileSync(path.join(root, producerFile), Buffer.alloc(4097, 32));
  assert.match(loadUnitReuse(root, historical.context).reason, /size exceeds bound/);
});
