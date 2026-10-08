import assert from "node:assert/strict";
import * as fs from "node:fs";
import path from "node:path";
import { createHash } from "node:crypto";
import { fileURLToPath } from "node:url";

export const STYLE_OPERATION = "plan-original-styles";
export const PLANNER_SHA256 = "7d13518cea1173752d54d969c88d2ec899c37887830fd2ef5a7bec2ce469310d";
const MOTION_REGRESSION_INPUTS = {
  "frontend/testdata/motion-layout-shadow/runner.test.mjs": "5f172d65ecdb512a76e24f68fa293ef56a0f07a9bcf0b2f36961492b17b042af",
  "frontend/testdata/motion-layout-shadow/index.html": "4298902a46db2d2e4327577cb3fc542422875f960fd299c39a5f2f8dfe9bb125",
  "frontend/testdata/motion-layout-shadow/entry.tsx": "323e97978e5e2622cb8f17274c34968c5be1460e3751c014f41a4b2398328b3c",
  "frontend/testdata/motion-layout-shadow/fixture.css": "33ac7e864f0ce21bbb83615e6812305eac5f2a215fa438692a4076a0a40681cd"
};
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;
const HASH = /^[0-9a-f]{64}$/;
const IMAGE = /^sha256:[0-9a-f]{64}$/;
const hash = (bytes) => createHash("sha256").update(bytes).digest("hex");
const own = (value, keys) => value !== null && typeof value === "object" && !Array.isArray(value)
  && Object.keys(value).length === keys.length && keys.every((key) => Object.hasOwn(value, key));

export function validGenRequest(request) {
  return own(request, ["schema", "operation", "fixtures"]) && request.schema === 1
    && ["qualify-original-react", "capture-original-baseline", STYLE_OPERATION].includes(request.operation)
    && request.fixtures === "frontend/e2e/original/runtime.spec.mjs";
}
export function sourcePath(root, relative, missing = false) {
  assert.equal(typeof relative, "string");
  assert.ok(relative && !path.isAbsolute(relative) && !/[\\:\x00-\x1f\x7f]/.test(relative), "Literal confined source path required");
  const parts = relative.split("/");
  assert.ok(parts.every((part) => part && ![".", ".."].includes(part) && !/[<>"|?*]|[ .]$/.test(part)
    && !/^(?:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\.|$)/i.test(part)), "Portable source path components required");
  let current = root;
  assert.equal(fs.realpathSync(root), root, "Canonical operation root required");
  for (const part of parts) {
    current = path.join(current, part);
    try { assert.ok(!fs.lstatSync(current).isSymbolicLink(), "Symlink operation ancestor refused"); }
    catch (error) { if (error.code !== "ENOENT" || !missing) throw error; }
  }
  const within = path.relative(root, current);
  assert.ok(within && !path.isAbsolute(within) && within.split(path.sep)[0] !== "..", "Operation path escaped root");
  return current;
}
function read(root, relative, inputs) {
  const file = sourcePath(root, relative); assert.ok(fs.lstatSync(file).isFile(), "Regular operation input required");
  const bytes = fs.readFileSync(file), record = { bytes: bytes.length, sha256: hash(bytes) };
  if (Object.hasOwn(inputs, relative)) assert.deepEqual(inputs[relative], record, "Repeated operation input changed");
  else Object.defineProperty(inputs, relative, { value: record, enumerable: true, writable: false, configurable: false });
  return bytes;
}
function configProjection(config) {
  const keys = ["role", "app", "npm_dir", "vendor_dir", "go_dirs"];
  assert.ok(own(config, keys) || own(config, [...keys, "ui_adoption"]), "Closed complete Cat configuration required");
  assert.equal(config.role, "consumer"); assert.equal(config.app, "cat_de_roman_esti");
  assert.equal(config.vendor_dir, "frontend/vendor"); assert.deepEqual(config.go_dirs, ["go-backend"]);
  assert.equal(typeof config.npm_dir, "string");
  assert.ok(config.npm_dir && !config.npm_dir.startsWith("/") && !/[\\:\x00-\x1f\x7f]/.test(config.npm_dir)
    && config.npm_dir.split("/").every((part) => /^[A-Za-z0-9_@.-]+$/.test(part) && ![".", ".."].includes(part)), "Literal configured kit path required");
  if (Object.hasOwn(config, "ui_adoption")) {
    const phase = config.ui_adoption, legacy = phase?.legacy;
    assert.ok(own(phase, ["mode", "until", "legacy"])); assert.equal(phase.mode, "staged-react"); assert.equal(phase.until, "S1-M2");
    assert.ok(own(legacy, ["version", "archive_sha256", "source_sha", "receipt", "receipt_sha256"]));
    assert.equal(legacy.version, "0.3.0"); assert.equal(legacy.archive_sha256, "1934a81cdfd737a051f591ebcae072f5028943b715456dbb2899b483d399c244");
    assert.match(legacy.source_sha, /^[0-9a-f]{40}(?:[0-9a-f]{24})?$/); assert.match(legacy.receipt_sha256, HASH);
    assert.equal(typeof legacy.receipt, "string");
    const excluded = new Set(["kit", "node_modules", "third_party", "vendor", "dist", "embedfs", "test-results", "TASK_BRIEF.md", "TASK_RESULT.md", "SWARM_RESULT.md"]);
    assert.ok(legacy.receipt && !legacy.receipt.startsWith("/") && !/\.tsbuildinfo(?:\.(?:gz|br))?$/.test(legacy.receipt)
      && legacy.receipt.split("/").every((part) => /^[A-Za-z0-9_@.-]+$/.test(part) && !part.startsWith(".") && !excluded.has(part)), "Source-owned original receipt required");
    for (const directory of [config.npm_dir, config.vendor_dir]) assert.ok(legacy.receipt !== directory && !legacy.receipt.startsWith(directory + "/"));
  }
  return { role: config.role, app: config.app, npm_dir: config.npm_dir, vendor_dir: config.vendor_dir,
    go_dirs: [...config.go_dirs], ...(config.ui_adoption ? { ui_adoption: config.ui_adoption } : {}) };
}

/** Current producer fields: wrapper W and runner/bootstrap I are separate links. */
export function readStyleIdentity(context, configured, request, environment = process.env) {
  assert.ok(validGenRequest(request) && request.operation === STYLE_OPERATION, "Explicit original-style operation required");
  assert.equal(context.target, "gen"); assert.match(context.invocation, UUID);
  assert.match(context.sha, /^[0-9a-f]{40}(?:[0-9a-f]{24})?$/); assert.match(context.tree_sha256, HASH);
  assert.match(context.toolchain_digest, IMAGE); assert.equal(typeof context.dirty, "boolean");
  assert.ok(Number.isInteger(context.parallel) && context.parallel >= 1 && ["report-only", "enforced"].includes(context.stage));
  assert.equal(environment.GATE_VERSIONS_RESOLVE, "0", "Style planning forbids version resolution; use plain owning gen");
  const root = context.root, inputs = {}, config = configProjection(configured);
  assert.deepEqual(JSON.parse(read(root, "scripts/gui-gen-request.json", inputs)), request, "Current source request differs from hook selection");
  const descriptorBytes = read(root, ".gate/wrapper-current.json", inputs), current = JSON.parse(descriptorBytes);
  assert.ok(own(current, ["schema", "invocation", "target", "sha", "tree_sha256", "toolchain_digest", "config_sha256", "config_path", "config_file_sha256"]));
  assert.equal(current.schema, 1); assert.match(current.invocation, UUID); assert.equal(current.target, "gen");
  assert.equal(current.sha, context.sha); assert.equal(current.tree_sha256, context.tree_sha256); assert.equal(current.toolchain_digest, context.toolchain_digest);
  assert.equal(current.config_path, ".gate/gen/wrapper-kit-config.json"); assert.match(current.config_sha256, HASH); assert.match(current.config_file_sha256, HASH);
  assert.deepEqual(read(root, ".gate/gen/wrapper-current.json", inputs), descriptorBytes, "Exact primary descriptor copy required");
  const capturedBytes = read(root, current.config_path, inputs), captured = JSON.parse(capturedBytes);
  assert.equal(hash(capturedBytes), current.config_file_sha256);
  assert.ok(own(captured, ["schema", "target", "sha", "tree_sha256", "toolchain_digest", "config", "config_sha256", "command"]));
  for (const key of ["schema", "target", "sha", "tree_sha256", "toolchain_digest", "config_sha256"]) assert.equal(captured[key], current[key]);
  assert.deepEqual(captured.config, config); assert.equal(JSON.stringify(captured.config), JSON.stringify(config));
  assert.equal(hash(JSON.stringify(config)), current.config_sha256, "Complete current configuration and phase checksum required");
  assert.ok(own(captured.command, ["command", "args", "exit_code", "duration_ms", "stdout_sha256", "stderr_sha256"]));
  assert.equal(captured.command.command, "task"); assert.deepEqual(captured.command.args, ["--silent", "repo:kit-config"]);
  assert.equal(captured.command.exit_code, 0); assert.ok(Number.isInteger(captured.command.duration_ms) && captured.command.duration_ms >= 0);
  assert.match(captured.command.stdout_sha256, HASH); assert.equal(captured.command.stderr_sha256, hash(""));
  const bootstrapBytes = read(root, ".gate/gen/bootstrap-execution.json", inputs), bootstrap = JSON.parse(bootstrapBytes);
  assert.ok(own(bootstrap, ["schema", "target", "invocation", "sha", "tree_sha256", "toolchain_digest", "started", "config", "config_sha256",
    "wrapper_target", "wrapper_config", "wrapper_config_sha256", "wrapper_invocation", "wrapper_descriptor", "wrapper_descriptor_sha256", "actions", "artifacts", "finished"]));
  assert.equal(bootstrap.schema, 1); assert.equal(bootstrap.target, "gen"); assert.equal(bootstrap.invocation, context.invocation);
  for (const key of ["sha", "tree_sha256", "toolchain_digest"]) assert.equal(bootstrap[key], context[key]);
  assert.deepEqual(bootstrap.config, config); assert.equal(bootstrap.config_sha256, current.config_sha256);
  assert.equal(bootstrap.wrapper_target, "gen"); assert.equal(bootstrap.wrapper_invocation, current.invocation);
  assert.equal(bootstrap.wrapper_config, current.config_path); assert.equal(bootstrap.wrapper_config_sha256, hash(capturedBytes));
  assert.equal(bootstrap.wrapper_descriptor, ".gate/wrapper-current.json"); assert.equal(bootstrap.wrapper_descriptor_sha256, hash(descriptorBytes));
  assert.ok(Number.isFinite(Date.parse(bootstrap.started)) && Number.isFinite(Date.parse(bootstrap.finished))
    && Date.parse(bootstrap.finished) >= Date.parse(bootstrap.started) && Date.parse(bootstrap.finished) <= Date.parse(context.started), "Current bootstrap timing required");
  assert.ok(Array.isArray(bootstrap.actions) && bootstrap.actions.length > 0 && Array.isArray(bootstrap.artifacts));
  const listed = new Map();
  for (const artifact of bootstrap.artifacts) {
    const match = /^(.+) sha256:([0-9a-f]{64})$/.exec(artifact); assert.ok(match && !listed.has(match[1]));
    assert.ok(match[1].startsWith(`.gate/gen/logs/${context.invocation}-bootstrap-`));
    assert.equal(hash(read(root, match[1], inputs)), match[2]); listed.set(match[1], match[2]);
  }
  const used = new Set(); let actualConfig = 0;
  for (const [ordinal, action] of bootstrap.actions.entries()) {
    assert.ok(own(action, ["phase", "kind", "command", "argument_count", "args_sha256", "cwd", "exit_code", "duration_ms", "stdout_sha256", "stderr_sha256", "stdout_log", "stderr_log"]));
    assert.equal(action.kind, "command"); assert.equal(action.exit_code, 0);
    assert.ok(typeof action.phase === "string" && /^[A-Za-z][A-Za-z0-9._-]*$/.test(action.phase)); assert.equal(action.cwd, ".");
    assert.ok(typeof action.command === "string" && action.command && Number.isInteger(action.duration_ms) && action.duration_ms >= 0
      && Number.isInteger(action.argument_count) && action.argument_count >= 0); assert.match(action.args_sha256, HASH);
    for (const stream of ["stdout", "stderr"]) { const file = action[`${stream}_log`]; assert.ok(!used.has(file));
      assert.equal(file, `.gate/gen/logs/${context.invocation}-bootstrap-${action.phase}-${ordinal}.${stream}.log`);
      assert.equal(listed.get(file), action[`${stream}_sha256`]); used.add(file); }
    if (action.phase === "config") {
      assert.equal(action.command, "task"); assert.equal(action.argument_count, 2); assert.equal(action.args_sha256, hash(JSON.stringify(["--silent", "repo:kit-config"])));
      assert.equal(action.stdout_sha256, captured.command.stdout_sha256); assert.equal(action.stderr_sha256, hash(""));
      assert.deepEqual(configProjection(JSON.parse(read(root, action.stdout_log, inputs))), config); actualConfig += 1;
    }
  }
  assert.equal(used.size, listed.size); assert.equal(listed.size, bootstrap.actions.length * 2); assert.ok(actualConfig > 0);
  if (config.ui_adoption) assert.equal(hash(read(root, config.ui_adoption.legacy.receipt, inputs)), config.ui_adoption.legacy.receipt_sha256);
  return { operation: STYLE_OPERATION, target: "gen", invocation: context.invocation, wrapper_invocation: current.invocation,
    sha: context.sha, tree_sha256: context.tree_sha256, dirty: context.dirty, toolchain_image_id: context.toolchain_digest,
    toolchain_digest: context.toolchain_digest, app_image_id: null, parallel: context.parallel, csp_stage: context.stage,
    config, config_sha256: current.config_sha256, inputs };
}
export function captureProtected(root, additional = []) {
  const records = {};
  function collect(relative) {
    const file = sourcePath(root, relative, true);
    if (!fs.existsSync(file)) { records[relative] = { absent: true }; return; }
    const stat = fs.lstatSync(file);
    if (stat.isDirectory()) { records[relative] = { directory: true };
      for (const name of fs.readdirSync(file).sort()) collect(`${relative}/${name}`); }
    else { assert.ok(stat.isFile(), "Regular protected source required"); const bytes = fs.readFileSync(file);
      records[relative] = { bytes: bytes.length, sha256: hash(bytes), mode: stat.mode }; }
  }
  for (const relative of new Set(["frontend/src", "frontend/e2e/gui-inventory.json", "frontend/package.json", "frontend/package-lock.json",
    "frontend/tsconfig.json", "frontend/vendor/roedu-ui-0.3.0.tgz", "versions.lock.json", "kit.lock.json", "scripts/gui-gen-request.json",
    "docs/reviews/gui-original-react", "baselines/cat", "legacy", ".gate/gen/original", ".gate/gen/styles/runs", ...additional])) collect(relative);
  return records;
}
export function assertProtectedUnchanged(before, after) {
  // A new planner run may be added; every previously retained path stays exact.
  for (const [file, record] of Object.entries(before)) {
    if (file.startsWith(".gate/gen/styles/runs") && record.absent) continue;
    assert.deepEqual(after[file], record, `Protected input or retained run changed: ${file}`);
  }
  for (const file of Object.keys(after)) if (!file.startsWith(".gate/gen/styles/runs/")) assert.ok(Object.hasOwn(before, file), `Unexpected protected addition: ${file}`);
}
function runFiles(root, relative) {
  const result = [];
  function walk(file) { const full = sourcePath(root, file), stat = fs.lstatSync(full);
    if (stat.isDirectory()) for (const name of fs.readdirSync(full).sort()) walk(`${file}/${name}`);
    else { assert.ok(stat.isFile()); result.push(file); } }
  walk(relative); return result;
}
export function validatePlannerOutput(root, summary, identity, previousRuns = []) {
  assert.ok(summary && summary.schema === 2 && ["pass", "fail"].includes(summary.status));
  assert.equal(summary.mode, "source-plan-only-product-files-unmodified");
  assert.equal(summary.bindings?.sha, identity.sha); assert.equal(summary.bindings?.tree_sha256, identity.tree_sha256);
  assert.equal(summary.bindings?.toolchain_digest, identity.toolchain_digest);
  assert.match(summary.plan_id ?? "", UUID);
  const relative = `.gate/gen/styles/runs/style-plan-${summary.plan_id}`;
  assert.equal(summary.output, relative); assert.ok(!previousRuns.includes(relative), "Fresh planner namespace required");
  assert.ok([`${relative}/report.json`, `${relative}/publication-failure.json`].includes(summary.report_json));
  const bytes = fs.readFileSync(sourcePath(root, summary.report_json)), report = JSON.parse(bytes);
  for (const key of ["schema", "status", "mode", "plan_id", "output", "report_json", "converted", "application_ready", "bindings", "diagnostics", "candidate_diagnostics", "manual"])
    assert.deepEqual(report[key], summary[key], `Planner stdout/disk ${key} differs`);
  assert.ok(Array.isArray(report.files) && Array.isArray(report.sites) && Array.isArray(report.owners));
  assert.ok(Array.isArray(report.diagnostics) && Array.isArray(report.candidate_diagnostics) && Array.isArray(report.manual));
  const analysis = JSON.parse(fs.readFileSync(sourcePath(root, `${relative}/analysis.json`)));
  assert.equal(analysis.application_ready, false); assert.equal(analysis.converted, null);
  for (const key of ["schema", "mode", "plan_id", "output", "bindings"]) assert.deepEqual(analysis[key], report[key]);
  const inputs = report.bindings.inputs; assert.ok(inputs && typeof inputs === "object" && !Array.isArray(inputs));
  for (const [file, record] of Object.entries(inputs)) {
    assert.ok(own(record, ["sha256", "bytes"])); const actual = fs.readFileSync(sourcePath(root, file));
    assert.equal(actual.length, record.bytes); assert.equal(hash(actual), record.sha256, `Actual planner input differs: ${file}`);
  }
  if (report.status === "pass") {
    assert.equal(report.application_ready, true); assert.equal(report.converted, `${relative}/candidate`);
    assert.equal(report.diagnostics.length + report.candidate_diagnostics.length + report.manual.length, 0); assert.ok(report.files.length > 0);
    for (const file of ["scripts/gui-style-plan.mjs", "frontend/package.json", "frontend/package-lock.json", "frontend/tsconfig.json",
      "frontend/src/components/cssUnits.ts", "frontend/src/components/CspStyle.ts", "frontend/src/components/CspElements.tsx", "frontend/src/screens/Alchimie.tsx", "frontend/src/screens/Conexiuni.tsx",
      "frontend/node_modules/react-dom/package.json", "frontend/node_modules/react-dom/cjs/react-dom-client.development.js",
      "frontend/node_modules/typescript/package.json", "frontend/node_modules/typescript/lib/typescript.js",
      "frontend/vendor/roedu-ui-0.3.0.tgz", "cat_de_roman_esti/web/static/assets/index-qYTSE3Vo.js"]) assert.ok(Object.hasOwn(inputs, file), `Required actual planner binding missing: ${file}`);
    assert.equal(inputs["scripts/gui-style-plan.mjs"].sha256, PLANNER_SHA256);
    for (const [file, expected] of Object.entries({
      "frontend/package.json": "efde2d3fbdebc5899dc63ca6b518cab0d60370ef36a7301477da720f4978e2e9",
      "frontend/package-lock.json": "f72661b4bd7ad129a6771037bf900a616a0fdf84bbb41f70c6d118b69fb1b62c",
      "frontend/tsconfig.json": "81dbe0e79cad7363ee3e83e4683cb5f382560608a592b91b5f0f903f2385b963",
      "frontend/src/components/cssUnits.ts": "5681d320b14511757894cff3a850b7f67114d78e9b1eb0d2c36e4d7551c1b873",
      "frontend/src/components/CspStyle.ts": "2ea61764325b4cb9ecd036d106466594d0f32f2f6d83b09a547981c0317fa320",
      "frontend/src/components/CspElements.tsx": "27cf738b5af8a4e4eefab89b513d941261b61d0d41813eca09618ea8a8ef881d",
      "frontend/src/screens/Alchimie.tsx": "d5f299fc3189e887147779c19d39218dc9bd60b717d3f598cdfbbb62760fa53b",
      "frontend/src/screens/Conexiuni.tsx": "7c5d85dda928a7f385be2a31edc8ea217cf381e0d48fa6ddbd5888c1b02e9338",
      "frontend/vendor/roedu-ui-0.3.0.tgz": "1934a81cdfd737a051f591ebcae072f5028943b715456dbb2899b483d399c244",
      "cat_de_roman_esti/web/static/assets/index-qYTSE3Vo.js": "3aeceaed54e6d8614fa85e68bcf2a5c6ab1a7619bf20f7184624d475259be93a",
    })) assert.equal(inputs[file].sha256, expected, `Exact reviewed planner source identity required: ${file}`);
    for (const [name, version] of [["react-dom", "19.2.7"], ["typescript", "5.9.3"]]) {
      assert.equal(report.bindings[name]?.version, version);
      const installed = JSON.parse(fs.readFileSync(sourcePath(root, `frontend/node_modules/${name}/package.json`)));
      assert.equal(installed.name, name); assert.equal(installed.version, version);
      const locked = JSON.parse(fs.readFileSync(sourcePath(root, "frontend/package-lock.json"))).packages[`node_modules/${name}`];
      assert.equal(locked.version, version); assert.equal(locked.resolved, report.bindings[name].resolved); assert.equal(locked.integrity, report.bindings[name].integrity);
    }
    const wanted = new Set([`${relative}/analysis.json`, report.report_json]);
    for (const file of report.files) {
      assert.ok(own(file, ["file", "before_sha256", "after_sha256"]));
      assert.ok(typeof file.file === "string" && file.file.startsWith("frontend/src/") && file.file.endsWith(".tsx"));
      assert.match(file.before_sha256, HASH); assert.match(file.after_sha256, HASH);
      const destination = `${report.converted}/${file.file}`; assert.ok(!wanted.has(destination)); wanted.add(destination);
      assert.equal(hash(fs.readFileSync(sourcePath(root, file.file))), file.before_sha256);
      assert.equal(hash(fs.readFileSync(sourcePath(root, destination))), file.after_sha256);
    }
    assert.deepEqual(runFiles(root, relative).sort(), [...wanted].sort(), "Closed successful planner files required");
  } else { assert.equal(report.application_ready, false); assert.equal(report.converted, null); assert.deepEqual(report.files, []); }
  return { report, artifacts: runFiles(root, relative), report_sha256: hash(bytes) };
}

/** Only the actual owning hook calls this. Unit fixture reports never qualify a product. */
export function runOriginalStyleOperation(hook, configured, request, environment = process.env) {
  const root = hook.context.root; let identity, protectedBefore, attempt, summary, executionError, validated, motionRegression = null;
  const passed = () => hook.checks.every((check) => check.status === "pass");
  const registered = new Set(), artifact = (file) => { if (!registered.has(file)) { hook.artifact(file); registered.add(file); } };
  hook.check("cat-style-current-context", () => hook.assert("Current owning style context and exact reviewed sources", () => {
    identity = readStyleIdentity(hook.context, configured, request, environment);
    const planner = read(root, "scripts/gui-style-plan.mjs", identity.inputs); assert.equal(hash(planner), PLANNER_SHA256);
    assert.equal(fs.realpathSync(sourcePath(root, "scripts/gui-style-operation.mjs")), fs.realpathSync(fileURLToPath(import.meta.url)), "Executing operation must be this repository module");
    read(root, "scripts/gui-style-operation.mjs", identity.inputs); read(root, "scripts/gui-repo-hook.mjs", identity.inputs);
    const units = hash(read(root, "frontend/src/components/cssUnits.ts", identity.inputs));
    const facade = hash(read(root, "frontend/src/components/CspStyle.ts", identity.inputs));
    const components = hash(read(root, "frontend/src/components/CspElements.tsx", identity.inputs));
    assert.equal(units, "5681d320b14511757894cff3a850b7f67114d78e9b1eb0d2c36e4d7551c1b873", "Exact sealed Part A interface overlay required");
    assert.equal(facade, "2ea61764325b4cb9ecd036d106466594d0f32f2f6d83b09a547981c0317fa320");
    assert.equal(components, "27cf738b5af8a4e4eefab89b513d941261b61d0d41813eca09618ea8a8ef881d");
    protectedBefore = captureProtected(root, configReceipt(identity));
    attempt = `.gate/gen/styles/operations/style-operation-${hook.context.invocation}`;
    const directory = sourcePath(root, attempt, true); fs.mkdirSync(path.dirname(directory), { recursive: true }); fs.mkdirSync(directory);
    fs.writeFileSync(sourcePath(root, `${attempt}/request.json`, true), JSON.stringify({ request, identity, manager_approved: false, implementation_ready: false }, null, 2) + "\n", { flag: "wx" });
    artifact(`${attempt}/request.json`); return true;
  }));
  if (!passed()) return;
  hook.check("cat-style-npm-ci", () => hook.run("npm", ["ci", "--no-audit", "--no-fund"], path.join(root, "frontend")));
  if (passed()) hook.check("cat-original-style-planner", () => {
    let stdout;
    try { stdout = hook.run(process.execPath, ["scripts/gui-style-plan.mjs"], root); }
    catch (error) { executionError = error; stdout = error.stdout; }
    if (typeof stdout === "string" && stdout.trim()) summary = JSON.parse(stdout);
    if (summary) validated = validatePlannerOutput(root, summary, identity, Object.keys(protectedBefore).filter((file) => /^\.gate\/gen\/styles\/runs\/style-plan-[^/]+$/.test(file)));
    if (validated) for (const file of validated.artifacts) artifact(file);
    if (executionError) throw executionError;
    hook.assert("Actual reviewed planner returned a successful current proposal", () => validated?.report.status === "pass" && validated.report.application_ready === true);
  });
  if (passed()) hook.check("cat-motion-layout-shadow-regression", () => {
    const inputs = {};
    for (const [file, expected] of Object.entries(MOTION_REGRESSION_INPUTS)) {
      assert.equal(hash(read(root, file, inputs)), expected, `Exact reviewed Motion regression source required: ${file}`);
    }
    const prefix = ".gate/gen/motion-layout-shadow", before = new Map();
    const existing = sourcePath(root, prefix, true);
    if (fs.existsSync(existing)) for (const file of runFiles(root, prefix)) {
      const bytes = fs.readFileSync(sourcePath(root, file)); before.set(file, { bytes: bytes.length, sha256: hash(bytes) });
    }
    let commandError;
    try { hook.run(process.execPath, ["--test", "testdata/motion-layout-shadow/runner.test.mjs"], path.join(root, "frontend")); }
    catch (error) { commandError = error; }
    const all = fs.existsSync(existing) ? runFiles(root, prefix) : [], fresh = all.filter((file) => !before.has(file));
    for (const [file, record] of before) {
      const bytes = fs.readFileSync(sourcePath(root, file)); assert.deepEqual({ bytes: bytes.length, sha256: hash(bytes) }, record, "Earlier actual Motion case changed");
    }
    for (const file of fresh) artifact(file); // Retain actual failures/builds/observations too.
    motionRegression = { scope: "focused-original-layout-shadow-capability-not-full-game", source_inputs: inputs,
      artifacts: fresh, status: commandError ? "fail" : "pending-report" };
    if (commandError) throw commandError;
    const reports = fresh.filter((file) => /^\.gate\/gen\/motion-layout-shadow\/runs\/run-[0-9a-f-]{36}\/report\.json$/.test(file));
    assert.equal(reports.length, 1, "One actual retained Motion regression report required");
    const bytes = fs.readFileSync(sourcePath(root, reports[0])), report = JSON.parse(bytes);
    assert.equal(report.status, "pass"); assert.equal(report.actual_primary.target, "gen");
    assert.equal(report.actual_primary.sha, identity.sha); assert.equal(report.actual_primary.tree_sha256, identity.tree_sha256);
    assert.equal(report.actual_primary.toolchain_digest, identity.toolchain_digest);
    assert.equal(report.actual_primary.invocation, identity.wrapper_invocation);
    assert.equal(report.actual_primary.config_sha256, identity.config_sha256);
    assert.equal(report.qualified_device, false); assert.equal(report.production_or_gameplay_qualified, false);
    assert.deepEqual(report.cases.map((item) => item.owner), ["conexiuni", "caldrece"]);
    for (const [file, record] of Object.entries(inputs)) {
      const current = fs.readFileSync(sourcePath(root, file)); assert.equal(hash(current), record.sha256); assert.equal(current.length, record.bytes);
    }
    motionRegression.status = "pass"; motionRegression.report = { path: reports[0], sha256: hash(bytes) };
  });
  hook.check("cat-style-protected-inputs", () => hook.assert("Product, original receipts, baselines, locks, inventory and retained runs stayed exact", () => {
    assertProtectedUnchanged(protectedBefore, captureProtected(root, configReceipt(identity)));
    for (const [file, record] of Object.entries(identity.inputs)) { const bytes = fs.readFileSync(sourcePath(root, file));
      assert.equal(bytes.length, record.bytes); assert.equal(hash(bytes), record.sha256); }
    return true;
  }));
  hook.check("cat-style-operation-evidence", () => hook.assert("Retained planning-only operation receipt", () => {
    const files = new Set(), newRuns = [];
    const runs = sourcePath(root, ".gate/gen/styles/runs", true);
    if (fs.existsSync(runs)) for (const name of fs.readdirSync(runs)) {
      const relative = `.gate/gen/styles/runs/${name}`;
      if (!Object.hasOwn(protectedBefore, relative)) { assert.match(name, /^style-plan-[0-9a-f-]{36}$/); newRuns.push(relative); for (const file of runFiles(root, relative)) files.add(file); }
    }
    for (const file of files) artifact(file);
    assert.ok(newRuns.length <= 1, "One actual planner call may retain at most one new run");
    if (validated) assert.deepEqual(newRuns, [validated.report.output]);
    const receipt = { schema: 1, operation: STYLE_OPERATION, scope: "original-style-source-planning-only", status: passed() ? "pass" : "fail",
      identity, planner_report: validated ? { path: validated.report.report_json, sha256: validated.report_sha256 } : null,
      planner_proposal_ready: validated?.report.application_ready === true, manager_approved: false, implementation_ready: false,
      release_qualified: false, checks: hook.checks.map((check) => ({ name: check.name, status: check.status, ...(check.reason ? { reason: check.reason } : {}) })),
      retained_planner_artifacts: [...files].sort(), motion_regression: motionRegression };
    fs.writeFileSync(sourcePath(root, `${attempt}/receipt.json`, true), JSON.stringify(receipt, null, 2) + "\n", { flag: "wx" });
    artifact(`${attempt}/receipt.json`); return true;
  }));
}
function configReceipt(identity) { return identity.config.ui_adoption ? [identity.config.ui_adoption.legacy.receipt] : []; }
