import assert from "node:assert/strict";
import * as fs from "node:fs";
import path from "node:path";
import { createHash, randomUUID } from "node:crypto";
import { fileURLToPath } from "node:url";
import test from "node:test";
import { STYLE_OPERATION, NORMALIZED_STYLE_OPERATION, validGenRequest, sourcePath, readStyleIdentity, captureProtected, assertProtectedUnchanged, validatePlannerOutput } from "../../scripts/gui-style-operation.mjs";

// These are protocol/data fixtures, never actual wrapper/bootstrap/planner receipts.
// Only a separately authorized native owning gen may earn planning evidence.
// Actual owning unit/full must authorize physical fixture writes before the first
// write. Compose mounts retained /work; /tmp would vanish when its --rm runner exits.
// Synthetic NON-RELEASE fixtures stay outside the target subtree in .gate/_temp.
const repository = fs.realpathSync(fileURLToPath(new URL("../../", import.meta.url)));
const sha = (bytes) => createHash("sha256").update(bytes).digest("hex");
const request = { schema: 1, operation: STYLE_OPERATION, fixtures: "frontend/e2e/original/runtime.spec.mjs" };
const configuration = { role: "consumer", app: "cat_de_roman_esti", npm_dir: "tools/gui-bootstrap-webkit", vendor_dir: "frontend/vendor", go_dirs: ["go-backend"] };
function write(root, relative, value) {
  const file = sourcePath(root, relative, true); fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, value); return file;
}
function json(root, relative, value) { return write(root, relative, JSON.stringify(value, null, 2) + "\n"); }
function nativeStaging() {
  assert.equal(process.platform, "linux", "Actual native Compose runner required before fixture writes");
  assert.equal(repository, "/work", "Actual retained /work repository required");
  let ancestor = repository;
  while (true) {
    const stat = fs.lstatSync(ancestor);
    assert.ok(stat.isDirectory() && !stat.isSymbolicLink(), "Regular native repository ancestors required");
    const parent = path.dirname(ancestor); if (parent === ancestor) break; ancestor = parent;
  }
  assert.equal(fs.realpathSync.native(repository), repository);
  const gate = sourcePath(repository, ".gate"), gateStat = fs.lstatSync(gate);
  assert.ok(gateStat.isDirectory() && !gateStat.isSymbolicLink()); assert.equal(fs.realpathSync.native(gate), gate);
  const file = sourcePath(repository, ".gate/wrapper-current.json"), stat = fs.lstatSync(file);
  assert.ok(stat.isFile() && !stat.isSymbolicLink()); assert.equal(fs.realpathSync.native(file), file);
  const descriptorBytes = fs.readFileSync(file), actual = JSON.parse(descriptorBytes);
  const fields = ["schema", "invocation", "target", "sha", "tree_sha256", "toolchain_digest", "config_sha256", "config_path", "config_file_sha256"];
  // `operator` is the one optional key the core-v1.8+ wrapper records (core ADR-0024).
  const keys = Object.hasOwn(actual ?? {}, "operator") ? [...fields, "operator"] : fields;
  assert.ok(actual && !Array.isArray(actual) && Object.keys(actual).length === keys.length && keys.every((key) => Object.hasOwn(actual, key)));
  assert.ok(actual.operator === undefined || actual.operator === null || (typeof actual.operator === "string" && /^(paul|agent:[a-z0-9][a-z0-9-]{1,39})$/.test(actual.operator)));
  assert.equal(actual.schema, 1); assert.ok(["unit", "full"].includes(actual.target), "Actual current unit/full descriptor required");
  assert.match(actual.invocation, /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/);
  assert.match(actual.sha, /^[0-9a-f]{40}$/); assert.match(actual.tree_sha256, /^[0-9a-f]{64}$/);
  assert.match(actual.toolchain_digest, /^sha256:[0-9a-f]{64}$/);
  assert.equal(actual.sha, process.env.GATE_SHA); assert.equal(actual.tree_sha256, process.env.GATE_TREE_SHA256);
  assert.equal(actual.toolchain_digest, process.env.TOOLCHAIN_DIGEST, "Actual source/tree/image environment binding required");
  assert.match(actual.config_sha256, /^[0-9a-f]{64}$/); assert.match(actual.config_file_sha256, /^[0-9a-f]{64}$/);
  assert.equal(actual.config_path, `.gate/${actual.target}/wrapper-kit-config.json`);
  assert.deepEqual(fs.readFileSync(sourcePath(repository, `.gate/${actual.target}/wrapper-current.json`)), descriptorBytes);
  const configBytes = fs.readFileSync(sourcePath(repository, actual.config_path)); assert.equal(sha(configBytes), actual.config_file_sha256);
  let current = repository;
  for (const part of [".gate", "_temp", "gui-style-operation-synthetic"]) {
    current = path.join(current, part);
    try { fs.lstatSync(current); } catch (error) { if (error.code !== "ENOENT") throw error; fs.mkdirSync(current, { mode: 0o700 }); }
    const directoryStat = fs.lstatSync(current);
    assert.ok(directoryStat.isDirectory() && !directoryStat.isSymbolicLink(), "Regular private retained staging required");
    assert.equal(fs.realpathSync.native(current), current);
  }
  return { directory: current, descriptor_sha256: sha(descriptorBytes), target: actual.target,
    wrapper_invocation: actual.invocation, sha: actual.sha, tree_sha256: actual.tree_sha256, toolchain_digest: actual.toolchain_digest };
}
function fixture(t, { selectedRequest = request, configured = configuration } = {}) {
  const native = nativeStaging(); // No physical fixture write precedes this actual guard.
  const stagingRoot = fs.mkdtempSync(path.join(native.directory, "NON-RELEASE-")); fs.chmodSync(stagingRoot, 0o700);
  const root = path.join(stagingRoot, "fixture");
  t.after(() => {
    // Inventory literal physical paths after success or failure; never follow
    // symlink probes, clean up, or turn synthetic data into qualification.
    const rows = [];
    function inventory(directory) {
      for (const name of fs.readdirSync(directory).sort()) {
        const file = path.join(directory, name), stat = fs.lstatSync(file);
        const relative = path.relative(stagingRoot, file).split(path.sep).join("/");
        if (stat.isSymbolicLink()) rows.push({ path: relative, kind: "literal-symlink", target: fs.readlinkSync(file), followed: false });
        else if (stat.isDirectory()) { rows.push({ path: relative, kind: "directory", mode: stat.mode }); inventory(file); }
        else if (stat.isFile()) { const bytes = fs.readFileSync(file); rows.push({ path: relative, kind: "regular", bytes: bytes.length, sha256: sha(bytes), mode: stat.mode }); }
        else rows.push({ path: relative, kind: "other", mode: stat.mode, followed: false });
      }
    }
    try {
      inventory(stagingRoot);
      fs.writeFileSync(path.join(stagingRoot, "retained-inventory.json"), JSON.stringify({ schema: 1, scope: "NON-RELEASE-SYNTHETIC",
        physical_staging_root: stagingRoot, physical_fixture_root: root, native_staging_authority: native,
        cleanup_performed: false, manager_approved: false, release_qualified: false, rows }, null, 2) + "\n", { flag: "wx", mode: 0o600 });
    } finally { t.diagnostic(`Retained NON-RELEASE style-operation physical fixture: ${root}; owned staging: ${stagingRoot}`); }
  });
  fs.mkdirSync(root, { mode: 0o700 });
  write(root, "NON-RELEASE-FIXTURE.txt", "Synthetic operation protocol evidence only. Never an actual gate or release receipt.\n");
  const context = { root, target: "gen", invocation: randomUUID(), sha: "a".repeat(40), tree_sha256: "b".repeat(64), dirty: true,
    toolchain_digest: "sha256:" + "c".repeat(64), parallel: 2, stage: "report-only", started: "2000-01-01T00:00:02.000Z" };
  const rawConfig = JSON.stringify(configured) + "\n", stdout = `.gate/gen/logs/${context.invocation}-bootstrap-config-0.stdout.log`;
  const stderr = `.gate/gen/logs/${context.invocation}-bootstrap-config-0.stderr.log`;
  write(root, stdout, rawConfig); write(root, stderr, ""); json(root, "scripts/gui-gen-request.json", selectedRequest);
  const captured = { schema: 1, target: "gen", sha: context.sha, tree_sha256: context.tree_sha256, toolchain_digest: context.toolchain_digest,
    config: structuredClone(configured), config_sha256: sha(JSON.stringify(configured)),
    command: { command: "task", args: ["--silent", "repo:kit-config"], exit_code: 0, duration_ms: 0,
      stdout_sha256: sha(rawConfig), stderr_sha256: sha("") } };
  const configPath = ".gate/gen/wrapper-kit-config.json"; json(root, configPath, captured);
  const current = { schema: 1, invocation: randomUUID(), target: "gen", sha: context.sha, tree_sha256: context.tree_sha256,
    toolchain_digest: context.toolchain_digest, config_sha256: captured.config_sha256, config_path: configPath,
    config_file_sha256: sha(fs.readFileSync(sourcePath(root, configPath))) };
  json(root, ".gate/wrapper-current.json", current); json(root, ".gate/gen/wrapper-current.json", current);
  const bootstrap = { schema: 1, target: "gen", invocation: context.invocation, sha: context.sha, tree_sha256: context.tree_sha256,
    toolchain_digest: context.toolchain_digest, started: "2000-01-01T00:00:00.000Z", config: structuredClone(configured),
    config_sha256: current.config_sha256, wrapper_target: "gen", wrapper_config: configPath, wrapper_config_sha256: current.config_file_sha256,
    wrapper_invocation: current.invocation, wrapper_descriptor: ".gate/wrapper-current.json",
    wrapper_descriptor_sha256: sha(fs.readFileSync(sourcePath(root, ".gate/wrapper-current.json"))),
    actions: [{ phase: "config", kind: "command", command: "task", argument_count: 2,
      args_sha256: sha(JSON.stringify(["--silent", "repo:kit-config"])), cwd: ".", exit_code: 0, duration_ms: 0,
      stdout_sha256: sha(rawConfig), stderr_sha256: sha(""), stdout_log: stdout, stderr_log: stderr }],
    artifacts: [`${stdout} sha256:${sha(rawConfig)}`, `${stderr} sha256:${sha("")}`], finished: "2000-01-01T00:00:01.000Z" };
  json(root, ".gate/gen/bootstrap-execution.json", bootstrap);
  if (configured.ui_adoption) write(root, configured.ui_adoption.legacy.receipt, fs.readFileSync(sourcePath(repository, configured.ui_adoption.legacy.receipt)));
  return { root, stagingRoot, context, current, captured, bootstrap, stdout, stderr, configured, selectedRequest };
}
const identity = (item, env = { GATE_VERSIONS_RESOLVE: "0" }) => readStyleIdentity(item.context, item.configured, item.selectedRequest, env);
for (const operation of ["qualify-original-react", "capture-original-baseline", "replay-normalized-react", STYLE_OPERATION, NORMALIZED_STYLE_OPERATION]) void test(`exact gen request admits ${operation}`, () => {
  assert.equal(validGenRequest({ ...request, operation }), true);
});
const badRequests = [
  ["absent", undefined], ["null", null], ["array", []], ["wrong schema", { ...request, schema: 2 }],
  ["unknown operation", { ...request, operation: "apply-styles" }], ["wrong fixture", { ...request, fixtures: "other.spec.mjs" }],
  ["extra field", { ...request, apply: true }], ["missing field", { schema: 1, operation: STYLE_OPERATION }],
  ["inherited fields", Object.assign(Object.create({ fixtures: request.fixtures }), { schema: 1, operation: STYLE_OPERATION })],
];
for (const [name, value] of badRequests) void test(`gen request refuses ${name}`, () => assert.equal(validGenRequest(value), false));

void test("data fixture binds separate wrapper W and runner I without app-image qualification", (t) => {
  const item = fixture(t), bound = identity(item);
  assert.equal(bound.wrapper_invocation, item.current.invocation); assert.equal(bound.invocation, item.context.invocation);
  assert.notEqual(bound.wrapper_invocation, bound.invocation); assert.equal(bound.app_image_id, null);
  assert.equal(bound.toolchain_image_id, item.context.toolchain_digest);
  assert.ok(Object.hasOwn(bound.inputs, ".gate/gen/bootstrap-execution.json"));
  assert.ok(Object.hasOwn(bound.inputs, "scripts/gui-gen-request.json"));
});
const contextMutations = [
  ["different target", (item) => { item.context.target = "full"; }],
  ["source SHA mismatch", (item) => { item.context.sha = "d".repeat(40); }],
  ["source tree mismatch", (item) => { item.context.tree_sha256 = "d".repeat(64); }],
  ["image identity mismatch", (item) => { item.context.toolchain_digest = "sha256:" + "d".repeat(64); }],
  ["runner I mismatch", (item) => { item.context.invocation = randomUUID(); }],
  ["descriptor copy mismatch", (item) => { json(item.root, ".gate/gen/wrapper-current.json", { ...item.current, invocation: randomUUID() }); }],
  ["descriptor extra field", (item) => { json(item.root, ".gate/wrapper-current.json", { ...item.current, permit_apply: true }); }],
  ["config bytes mismatch", (item) => { write(item.root, item.current.config_path, "{}\n"); }],
  ["bootstrap wrapper W mismatch", (item) => { json(item.root, ".gate/gen/bootstrap-execution.json", { ...item.bootstrap, wrapper_invocation: randomUUID() }); }],
  ["bootstrap descriptor hash mismatch", (item) => { json(item.root, ".gate/gen/bootstrap-execution.json", { ...item.bootstrap, wrapper_descriptor_sha256: "d".repeat(64) }); }],
  ["bootstrap config object mismatch", (item) => { json(item.root, ".gate/gen/bootstrap-execution.json", { ...item.bootstrap, config: { ...configuration, vendor_dir: "elsewhere" } }); }],
  ["bootstrap failed command", (item) => { const value = structuredClone(item.bootstrap); value.actions[0].exit_code = 1; json(item.root, ".gate/gen/bootstrap-execution.json", value); }],
  ["bootstrap wrong actual args", (item) => { const value = structuredClone(item.bootstrap); value.actions[0].args_sha256 = sha(JSON.stringify(["--silent", "another-task"])); json(item.root, ".gate/gen/bootstrap-execution.json", value); }],
  ["bootstrap modified stdout", (item) => { write(item.root, item.stdout, "{}\n"); }],
  ["bootstrap omitted config action", (item) => { json(item.root, ".gate/gen/bootstrap-execution.json", { ...item.bootstrap, actions: [], artifacts: [] }); }],
  ["bootstrap duplicate stream", (item) => { const value = structuredClone(item.bootstrap); value.actions[0].stderr_log = value.actions[0].stdout_log; json(item.root, ".gate/gen/bootstrap-execution.json", value); }],
  ["bootstrap extra field", (item) => { json(item.root, ".gate/gen/bootstrap-execution.json", { ...item.bootstrap, ignore_failed: true }); }],
  ["source request mismatch", (item) => { json(item.root, "scripts/gui-gen-request.json", { ...request, operation: "capture-original-baseline" }); }],
];
for (const [name, mutate] of contextMutations) void test(`current style binding refuses ${String(name)}`, (t) => {
  const item = fixture(t); mutate(item); assert.throws(() => identity(item));
});
for (const value of ["1", undefined]) void test(`style planning refuses resolver state ${String(value)}`, (t) => {
  assert.throws(() => identity(fixture(t), { GATE_VERSIONS_RESOLVE: value }));
});
void test("a caller cannot substitute an app, locator or source phase into frozen configuration", (t) => {
  for (const config of [{ ...configuration, app: "other" }, { ...configuration, npm_dir: "../escape" },
    { ...configuration, ui_adoption: { mode: "staged-react", until: "later", legacy: {} } }, { ...configuration, unexpected: true }]) {
    assert.throws(() => readStyleIdentity(fixture(t).context, config, request, { GATE_VERSIONS_RESOLVE: "0" }));
  }
});

void test("source paths refuse streams, escapes and reserved components", (t) => {
  const item = fixture(t);
  for (const name of ["../outside", "scripts/x:stream", "scripts/NUL", "scripts/COM1.txt", "scripts/trailing.", "scripts/a\\b", "/tmp/outside"]) {
    assert.throws(() => sourcePath(item.root, name, true));
  }
});
void test("a symlink ancestor cannot select or publish an artifact outside the fixture", (t) => {
  const item = fixture(t), outside = path.join(item.stagingRoot, "private-owned-outside-probe"); fs.mkdirSync(outside, { mode: 0o700 });
  fs.symlinkSync(outside, path.join(item.root, "linked"), "dir");
  assert.throws(() => sourcePath(item.root, "linked/evidence.json", true));
  assert.deepEqual(fs.readdirSync(outside), []);
});
void test("protected source additions and byte mutations refuse while old failure evidence stays exact", (t) => {
  const item = fixture(t); write(item.root, "frontend/src/keep.ts", "old\n");
  write(item.root, ".gate/gen/styles/runs/style-plan-old/analysis.json", "retained failure\n");
  const before = captureProtected(item.root);
  write(item.root, "frontend/src/keep.ts", "changed\n");
  assert.throws(() => assertProtectedUnchanged(before, captureProtected(item.root)));
  write(item.root, "frontend/src/keep.ts", "old\n"); write(item.root, "frontend/src/added.ts", "new\n");
  assert.throws(() => assertProtectedUnchanged(before, captureProtected(item.root)));
  assert.equal(fs.readFileSync(path.join(item.root, ".gate/gen/styles/runs/style-plan-old/analysis.json"), "utf8"), "retained failure\n");
});
void test("the exact protected map permits only fresh planner runs", (t) => {
  const item = fixture(t), before = captureProtected(item.root);
  write(item.root, ".gate/gen/styles/runs/style-plan-unit/analysis.json", "unit fixture\n");
  assertProtectedUnchanged(before, captureProtected(item.root));
  write(item.root, "frontend/e2e/gui-inventory.json", "{}\n");
  assert.throws(() => assertProtectedUnchanged(before, captureProtected(item.root)));
});

for (const mutation of ["sibling bytes", "nested bytes", "nested addition"]) void test(`actual original proof directory refuses ${mutation} without a staged phase`, (t) => {
  const item = fixture(t), directory = "docs/reviews/gui-original-react";
  assert.equal(Object.hasOwn(configuration, "ui_adoption"), false);
  const evidence = [
    ["receipt.json", "NON-RELEASE receipt before\n"],
    ["stdout.log", "NON-RELEASE sibling before\n"],
    ["evidence/proof.json", "NON-RELEASE nested before\n"],
  ];
  for (const [relative, bytes] of evidence) write(item.root, `${directory}/${relative}`, bytes);
  // No phase-specific/additional paths: the operation's default map must cover
  // the actual complete directory, not only a receipt or a nonexistent alias.
  const before = captureProtected(item.root);
  assert.deepEqual(before[directory], { directory: true });
  for (const [relative, bytes] of evidence) {
    const record = before[`${directory}/${relative}`];
    assert.equal(record.bytes, Buffer.byteLength(bytes)); assert.equal(record.sha256, sha(bytes));
  }
  assertProtectedUnchanged(before, captureProtected(item.root));
  const changed = mutation === "sibling bytes" ? "stdout.log" : mutation === "nested bytes" ? "evidence/proof.json" : "evidence/added-proof.json";
  if (mutation === "nested addition") write(item.root, `${directory}/${changed}`, "NON-RELEASE added proof\n");
  else {
    const previous = evidence.find(([relative]) => relative === changed)[1];
    const replacement = previous.replace("before", "after!");
    assert.equal(Buffer.byteLength(replacement), Buffer.byteLength(previous));
    write(item.root, `${directory}/${changed}`, replacement);
  }
  assert.throws(() => assertProtectedUnchanged(before, captureProtected(item.root)), (error) => {
    assert.ok(error instanceof Error);
    assert.ok(error.message.includes(`${directory}/${changed}`));
    assert.match(error.message, mutation === "nested addition" ? /Unexpected protected addition:/ : /Protected input or retained run changed:/);
    return true;
  });
  assert.equal(fs.readFileSync(sourcePath(item.root, `${directory}/receipt.json`), "utf8"), evidence[0][1]);
  // Keep each refused physical fixture intact; no restoring/deleting it here.
});

function failedProposal(item) {
  const bound = identity(item), id = randomUUID(), relative = `.gate/gen/styles/runs/style-plan-${id}`;
  const report = { schema: 2, status: "fail", application_ready: false, diagnostics: [], candidate_diagnostics: [], sites: [], manual: [{ reason: "UNIT FIXTURE: planner refusal" }],
    owners: [], proposals: [], files: [], bindings: { sha: bound.sha, tree_sha256: bound.tree_sha256, toolchain_digest: bound.toolchain_digest, inputs: {} },
    plan_id: id, output: relative, converted: null, report_json: `${relative}/report.json`, mode: "source-plan-only-product-files-unmodified" };
  json(item.root, `${relative}/analysis.json`, report); json(item.root, report.report_json, report);
  return { bound, report, summary: structuredClone(report), relative };
}
void test("a data-only refusal retains its actual fresh files without a converted path", (t) => {
  const item = fixture(t), proposal = failedProposal(item);
  const checked = validatePlannerOutput(item.root, proposal.summary, proposal.bound);
  assert.equal(checked.report.status, "fail"); assert.equal(checked.report.converted, null);
  assert.deepEqual(checked.artifacts.sort((left, right) => left < right ? -1 : left > right ? 1 : 0), [`${proposal.relative}/analysis.json`, proposal.report.report_json].sort((left, right) => left < right ? -1 : left > right ? 1 : 0));
});
const outputMutations = [
  ["stdout identity", (proposal) => { proposal.summary.bindings.sha = "d".repeat(40); }],
  ["stdout versus disk", (proposal) => { proposal.summary.manual = []; }],
  ["old namespace", () => {}, true],
  ["outside report", (proposal) => { proposal.summary.report_json = "frontend/other.json"; }],
  ["failure selects candidate", (proposal) => { proposal.summary.converted = `${proposal.relative}/candidate`; }],
  ["failure says ready", (proposal) => { proposal.summary.application_ready = true; }],
];
for (const [name, mutate, old] of outputMutations) void test(`planner report refuses ${String(name)}`, (t) => {
  const item = fixture(t), proposal = failedProposal(item); mutate(proposal);
  assert.throws(() => validatePlannerOutput(item.root, proposal.summary, proposal.bound, old ? [proposal.relative] : []));
});
void test("modified planner input bytes refuse even on a failure report", (t) => {
  const item = fixture(t), proposal = failedProposal(item); write(item.root, "frontend/src/fixture.ts", "original\n");
  proposal.report.bindings.inputs["frontend/src/fixture.ts"] = { bytes: 9, sha256: sha("original\n") };
  json(item.root, proposal.report.report_json, proposal.report); json(item.root, `${proposal.relative}/analysis.json`, proposal.report);
  proposal.summary = structuredClone(proposal.report); write(item.root, "frontend/src/fixture.ts", "changed\n");
  assert.throws(() => validatePlannerOutput(item.root, proposal.summary, proposal.bound));
});

// The React-era proposal protocol tests (normalized/original planner proposals,
// byte guards, native candidate graphs and the controlled planner refusal)
// modelled the React 19 normalized tree: Alchimie/Perechi screens, the vendored
// UI 0.3.0 archive, the React SDK allocation plugin and installed react-dom. The
// M2 Preact port removed that tree, so they retired with it (Decision Log
// 2026-10-12; docs/reviews/gui-m2-activation/bindings.md). The explicit-unit
// contract they served is held by scripts/gui-style-audit.mjs and its test.
