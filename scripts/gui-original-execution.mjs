import * as fs from "node:fs";
import assert from "node:assert/strict";
import { fileURLToPath, pathToFileURL } from "node:url";
import { createRequire } from "node:module";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { readTarGz } from "../tools/gui-bootstrap-webkit/scripts/kit-sync.mjs";


// This profile replays the sealed React contracts on the current normalized
// graph. It cannot replace the original SDK adoption receipt.
export async function normalizedReactAdmission() {
  const root = process.cwd(), inputs = new Map();
  const hash = (data) => createHash("sha256").update(data).digest("hex");
  function input(relative) {
    assert.ok(typeof relative === "string" && relative && !path.isAbsolute(relative)
      && !/[\\:\x00-\x1f\x7f]/.test(relative) && relative.split("/").every((part) => part && part !== "." && part !== ".."), "Confined normalized React input required");
    const absolute = path.resolve(root, relative);
    assert.equal(fs.realpathSync(absolute), absolute, "Normalized React input symlink/alias refused");
    assert.ok(fs.lstatSync(absolute).isFile(), "Regular normalized React input required");
    const data = fs.readFileSync(absolute), record = { path: relative, bytes: data.length, sha256: hash(data) };
    if (inputs.has(relative)) assert.deepEqual(inputs.get(relative), record, "Normalized admission input changed");
    inputs.set(relative, record);
    return data;
  }
  const json = (relative) => JSON.parse(input(relative));
  assert.equal(process.env.GATE_APP_URL || "", "", "Normalized React replay starts its owning built server");
  assert.equal(process.env.GATE_APP_IMAGE_ID || "", "", "Normalized React replay has no app image");
  assert.notEqual(process.env.CAT_UI, "legacy", "Normalized replay must serve the current managed dist");
  assert.equal(process.env.GATE_VERSIONS_RESOLVE, "0", "Normalized React replay cannot resolve versions");
  assert.match(process.env.GATE_SHA || "", /^[a-f0-9]{40}(?:[a-f0-9]{24})?$/);
  assert.match(process.env.GATE_TREE_SHA256 || "", /^[a-f0-9]{64}$/);
  assert.match(process.env.TOOLCHAIN_DIGEST || "", /^sha256:[a-f0-9]{64}$/);
  assert.ok(["true", "false"].includes(process.env.GATE_DIRTY));
  const descriptorBytes = input(".gate/wrapper-current.json"), descriptor = JSON.parse(descriptorBytes);
  assert.equal(descriptor.target, "gen");
  for (const [key, value] of [["sha", process.env.GATE_SHA], ["tree_sha256", process.env.GATE_TREE_SHA256], ["toolchain_digest", process.env.TOOLCHAIN_DIGEST]]) assert.equal(descriptor[key], value);
  assert.deepEqual(input(".gate/gen/wrapper-current.json"), descriptorBytes);
  assert.equal(descriptor.config_path, ".gate/gen/wrapper-kit-config.json");
  const configBytes = input(descriptor.config_path), envelope = JSON.parse(configBytes);
  assert.equal(hash(configBytes), descriptor.config_file_sha256);
  for (const key of ["target", "sha", "tree_sha256", "toolchain_digest", "config_sha256"]) assert.equal(envelope[key], descriptor[key]);
  assert.equal(envelope.command.exit_code, 0); assert.equal(envelope.command.stdout_sha256, envelope.config_sha256);
  const bootstrap = json(".gate/gen/bootstrap-execution.json");
  for (const key of ["target", "sha", "tree_sha256", "toolchain_digest", "config_sha256"]) assert.equal(bootstrap[key], descriptor[key]);
  assert.equal(bootstrap.wrapper_target, "gen"); assert.equal(bootstrap.wrapper_invocation, descriptor.invocation);
  assert.equal(bootstrap.wrapper_descriptor, ".gate/wrapper-current.json"); assert.equal(bootstrap.wrapper_descriptor_sha256, hash(descriptorBytes));
  assert.equal(bootstrap.wrapper_config, descriptor.config_path); assert.equal(bootstrap.wrapper_config_sha256, hash(configBytes));
  assert.deepEqual(bootstrap.config, envelope.config);
  const request = json("scripts/gui-gen-request.json");
  assert.equal(request.schema, 1); assert.equal(request.operation, "replay-normalized-react");
  assert.equal(request.fixtures, "frontend/e2e/original/runtime.spec.mjs");
  const config = envelope.config, phase = config.ui_adoption;
  assert.equal(config.role, "consumer"); assert.equal(config.app, "cat_de_roman_esti");
  assert.equal(config.npm_dir, "frontend/node_modules/@roedu/web-kit"); assert.equal(config.vendor_dir, "frontend/vendor");
  assert.deepEqual(config.go_dirs, ["go-backend"]);
  assert.equal(phase.mode, "staged-react"); assert.equal(phase.until, "S1-M2");
  assert.equal(phase.legacy.version, "0.3.0");
  const archive = input("frontend/vendor/roedu-ui-0.3.0.tgz"), archiveHash = hash(archive);
  assert.equal(archiveHash, "1934a81cdfd737a051f591ebcae072f5028943b715456dbb2899b483d399c244");
  assert.equal(phase.legacy.archive_sha256, archiveHash);
  const entries = readTarGz(archive), sdkPackage = entries.get("package/package.json").data;
  const sdkEntry = entries.get("package/dist/index.js").data;
  assert.deepEqual(input("frontend/node_modules/@roedu/ui/package.json"), sdkPackage);
  assert.deepEqual(input("frontend/node_modules/@roedu/ui/dist/index.js"), sdkEntry);
  const receiptBytes = input(phase.legacy.receipt), receipt = JSON.parse(receiptBytes);
  assert.equal(hash(receiptBytes), phase.legacy.receipt_sha256);
  assert.equal(receipt.check, "cat-original-ui-runtime"); assert.equal(receipt.status, "pass");
  assert.equal(receipt.sha, phase.legacy.source_sha); assert.equal(receipt.runtime_sdk.version, "0.3.0");
  assert.equal(receipt.runtime_sdk.archive_sha256, archiveHash);
  assert.equal(receipt.runtime_sdk.manifest_sha256, hash(sdkPackage)); assert.equal(receipt.runtime_sdk.entry_sha256, hash(sdkEntry));
  function bound(record) { assert.equal(hash(input(record.path)), record.sha256, "Preserved original proof binding differs"); }
  bound(receipt.dependency_graph.manifest); bound(receipt.dependency_graph.lock);
  bound(receipt.execution.report); bound(receipt.execution.stdout); bound(receipt.execution.stderr);
  for (const fixture of receipt.fixtures) bound(fixture.source);
  assert.equal(receipt.fixtures.length, 16);
  assert.equal(receipt.fixtures.reduce((n, fixture) => n + fixture.assertions.length, 0), 78);
  const oldManifest = JSON.parse(input(receipt.dependency_graph.manifest.path));
  assert.equal(hash(input(receipt.dependency_graph.manifest.path)), "efde2d3fbdebc5899dc63ca6b518cab0d60370ef36a7301477da720f4978e2e9");
  assert.equal(hash(input(receipt.dependency_graph.lock.path)), "f72661b4bd7ad129a6771037bf900a616a0fdf84bbb41f70c6d118b69fb1b62c");
  for (const [file, expected] of [
    ["frontend/e2e/original/runtime.spec.mjs", "2b06e9274a39d33352d0f5f9856899530911b90e7cdefe264f6fb75398409e2a"],
    ["frontend/playwright.original.config.mjs", "6e05214dbbcb1bb5c2881a0a2a228ca1a3292039d1baea0858787856415ad14f"],
    ["frontend/e2e/original/reporter.mjs", "20f561c1fcd1c0829460fdd4bdf58d51435d8ad5f4c162dfa21441fa5955a3c8"],
    ["frontend/e2e/gui-inventory.json", "763e1e7bfab83f4b469e55b87c1491ae2dff4debdc11412979bf3bdbe28fa278"],
  ]) assert.equal(hash(input(file)), expected, "Sealed fixture/config or exact 900 identities changed");
  const manifest = json("frontend/package.json"), lock = json("frontend/package-lock.json"), versions = json("versions.lock.json");
  assert.equal(lock.lockfileVersion, 3); assert.equal(versions.schema, 2);
  for (const key of ["dependencies", "devDependencies", "optionalDependencies"]) assert.deepEqual(lock.packages[""][key] || {}, manifest[key] || {});
  const declared = { ...manifest.dependencies, ...manifest.devDependencies, ...manifest.optionalDependencies };
  assert.equal(declared["@roedu/ui"], "file:vendor/roedu-ui-0.3.0.tgz");
  const installed = {};
  for (const name of new Set([...Object.keys(declared), "framer-motion", "playwright"])) {
    const locked = lock.packages[`node_modules/${name}`], actual = json(`frontend/node_modules/${name}/package.json`);
    assert.ok(locked, `Normalized installed package lacks lock binding: ${name}`);
    assert.equal(actual.name, name); assert.equal(actual.version, locked.version);
    assert.match(actual.version, /^\d+\.\d+\.\d+$/); installed[name] = actual.version;
  }
  for (const name of ["react", "react-dom"]) {
    assert.equal(installed[name], "19.2.7");
    assert.ok([oldManifest.dependencies[name], "19.2.7"].includes(declared[name]), "Staged React declaration changed");
  }
  assert.equal(installed["@roedu/ui"], "0.3.0");
  function tool(name) {
    const rows = versions.tools.filter((row) => row.kind === "npm" && row.tool === name);
    assert.equal(rows.length, 1); assert.match(rows[0].version || "", /^\d+\.\d+\.\d+$/); return rows[0];
  }
  for (const name of ["motion", "framer-motion", "typescript", "vite", "@playwright/test", "playwright"]) assert.equal(installed[name], tool(name).version, `Actual normalized floor differs: ${name}`);
  assert.equal(declared.motion, tool("motion").version);
  assert.equal(tool("framer-motion").status, "transitive-only"); assert.ok(!Object.hasOwn(declared, "framer-motion"));
  assert.ok(tool("framer-motion").dependants.includes("motion"));
  assert.equal(lock.packages["node_modules/motion"].dependencies["framer-motion"], tool("framer-motion").version);
  for (const row of versions.tools.filter((row) => row.kind === "npm" && installed[row.tool] && row.version)) {
    assert.equal(installed[row.tool], row.version, `Installed normalized tool differs: ${row.tool}`);
    if (Object.hasOwn(declared, row.tool) && ["pinned", "optional", undefined].includes(row.status)) assert.equal(declared[row.tool], row.version, "Normalized tool declaration must be exact");
  }
  assert.ok(installed["@typescript/typescript6"], "The approved parser package is required for the real consumer contracts");
  const apiRow = tool("@typescript/typescript6"); assert.equal(apiRow.status, "optional"); assert.ok(apiRow.exception && apiRow.approved_by);
  input("frontend/scripts/compiler-runtime.mjs");
  const { nativeCompiler, parserBinding } = await import(pathToFileURL(path.join(root, "frontend/scripts/compiler-runtime.mjs")).href);
  const require = createRequire(path.join(root, "frontend/package.json")), apiEntry = require.resolve("@typescript/typescript6");
  const loaded = await import(pathToFileURL(apiEntry).href), api = loaded.default ?? loaded;
  const compiler = nativeCompiler(path.join(root, "frontend")), parser = parserBinding(path.join(root, "frontend"), api);
  assert.equal(hash(input(path.relative(root, compiler.executable))), compiler.executable_sha256);
  input(path.relative(root, apiEntry));
  assert.equal(hash(input(path.relative(root, parser.implementation.path))), parser.implementation.entry_sha256);
  const apiRequire = createRequire(path.join(root, "frontend/node_modules/@typescript/typescript6/package.json"));
  assert.equal(hash(input(path.relative(root, apiRequire.resolve("@typescript/old/package.json")))), parser.implementation.manifest_sha256);
  assert.match(declared["@roedu/web-kit"] || "", /^file:vendor\/roedu-web-kit-\d+\.\d+\.\d+\.tgz$/);
  const kitArchive = input(`frontend/${declared["@roedu/web-kit"].slice(5)}`), kitEntries = readTarGz(kitArchive);
  assert.deepEqual(input(`${config.npm_dir}/package.json`), kitEntries.get("package/package.json").data);
  input(`${config.npm_dir}/scripts/kit-sync.mjs`);
  for (const [key, name] of [["CDR_NATIVE_BINARY", "cat-server"], ["CDR_BROWSER_PLAN_BINARY", "cat-browser-plan"]]) {
    assert.equal(process.env[key], path.join(root, ".gate/gen", name), "Normalized replay requires this owning GEN's binaries"); input(`.gate/gen/${name}`);
  }
  for (const file of ["scripts/gui-original-execution.mjs", "scripts/gui-full-browser.mjs", "scripts/gui-repo-hook.mjs", "tools/gui-bootstrap-webkit/scripts/kit-sync.mjs",
    "frontend/playwright.gui.config.mjs", "frontend/playwright.config.mjs", "frontend/e2e/games.mjs", "frontend/e2e/native-plan.mjs", "frontend/e2e/seeded-starts.json",
    "frontend/e2e/alchimie-111-checkpoint.json", "frontend/e2e/alchimie-221-checkpoint.json", "frontend/e2e/alchimie-221-expanded-checkpoint.json",
    "frontend/node_modules/@playwright/test/cli.js", "scripts/gui-assets.mjs", "scripts/gui-native-preflight.mjs", "scripts/gui-startup-inventory.mjs",
    "frontend/scripts/check-bundle-budget.mjs", "frontend/scripts/gui-lint.mjs", "frontend/tests/bundle-budget.test.mjs",
    "frontend/vite.config.ts", "frontend/tsconfig.json",
    "frontend/tests/gui-api-consumer-contract.test.mjs", "frontend/tests/conexiuni-selection-key.test.mjs",
    "frontend/tests/fixtures/gui-api-consumer-contract.ts", "frontend/tests/fixtures/gui-api-consumer-tsconfig.json"]) input(file);
  function managedFiles(directory, prefix = "") {
    return fs.readdirSync(path.join(root, directory, prefix), { withFileTypes: true }).sort((a, b) => a.name.localeCompare(b.name)).flatMap((entry) => {
      const file = prefix + entry.name;
      if (entry.isDirectory()) return managedFiles(directory, file + "/");
      assert.ok(entry.isFile(), "Nonregular managed build asset refused");
      return [file];
    });
  }
  const distFiles = managedFiles("frontend/dist"), embeddedFiles = managedFiles("go-backend/embedfs/dist").filter((file) => file !== ".keep");
  assert.ok(distFiles.includes("index.html") && distFiles.includes(".vite/manifest.json"), "Actual managed Vite entry and manifest required");
  assert.deepEqual(embeddedFiles, distFiles, "Managed embedded asset set differs from the actual build");
  for (const file of distFiles) assert.deepEqual(input(`go-backend/embedfs/dist/${file}`), input(`frontend/dist/${file}`), "Managed embedded asset bytes differ from the actual build");
  for (const tree of ["dist", "legacy"]) assert.equal(input(`go-backend/embedfs/${tree}/.keep`).length, 0, "Tracked managed scaffold must stay empty");
  const legacy = json("legacy/original-bundle.json");
  assert.equal(hash(input(legacy.archive)), legacy.sha256, "Frozen legacy archive differs");
  assert.equal(input(legacy.archive + ".sha256").toString("utf8"), `${legacy.sha256}  ${path.basename(legacy.archive)}\n`);
  const legacyFiles = managedFiles("go-backend/embedfs/legacy").filter((file) => file !== ".keep");
  assert.deepEqual(legacyFiles, legacy.files.map((item) => item.path), "Embedded legacy asset set differs from its frozen proof");
  assert.ok(legacyFiles.includes("index.html") && legacyFiles.includes(".vite/manifest.json"));
  for (const item of legacy.files) { const data = input(`go-backend/embedfs/legacy/${item.path}`); assert.equal(data.length, item.bytes); assert.equal(hash(data), item.sha256, "Embedded legacy bytes differ from the frozen proof"); }
  assert.equal(input("go-backend/embedfs/build/dist/.keep").length, 0, "Private build scaffold must stay empty");
  const identityPath = "go-backend/embedfs/build/dist/.gui-build.json", identity = json(identityPath);
  assert.deepEqual(Object.keys(identity).sort(), ["manifest_sha256", "sha", "tree_sha256", "versions_lock_sha256"]);
  assert.equal(identity.sha, descriptor.sha); assert.equal(identity.tree_sha256, descriptor.tree_sha256);
  assert.equal(identity.manifest_sha256, hash(input("go-backend/embedfs/dist/.vite/manifest.json")));
  assert.deepEqual(input("go-backend/embedfs/build/dist/versions.lock.json"), input("versions.lock.json"));
  assert.equal(identity.versions_lock_sha256, hash(input("versions.lock.json")));
  for (const file of ["go-backend/cmd/cat-gui-build/main.go", "go-backend/internal/guibuild/generate.go", "go-backend/internal/guibuild/identity.go",
    "go-backend/embedfs/assets.go", "go-backend/internal/httpapi/gui_build.go", "go-backend/internal/httpapi/managed_nonce.go"]) input(file);
  return { inputs: [...inputs.values()], installed_versions: installed, native_compiler: compiler, parser_api: parser,
    managed_build: { source: "frontend/dist", embedded: "go-backend/embedfs/dist", files: distFiles, identity: { path: identityPath, ...identity }, legacy: { proof: "legacy/original-bundle.json", archive: legacy.archive, sha256: legacy.sha256, files: legacyFiles } },
    runtime_dependencies: Object.fromEntries(["react", "react-dom", "motion", "framer-motion"].map((name) => [name, installed[name]])),
    ui_adoption: phase, original_receipt: { path: phase.legacy.receipt, sha256: hash(receiptBytes) },
    sealed_fixtures: receipt.fixtures.map(({ id, suite, assertions }) => ({ id, suite, assertions: assertions.map(({ id }) => id) })) };
}
export function recheckNormalizedReactInputs(admission) {
  for (const item of admission.inputs) {
    const absolute = path.resolve(process.cwd(), item.path);
    assert.equal(fs.realpathSync(absolute), absolute); assert.ok(fs.lstatSync(absolute).isFile());
    const data = fs.readFileSync(absolute);
    assert.equal(data.length, item.bytes); assert.equal(createHash("sha256").update(data).digest("hex"), item.sha256, "Normalized replay changed a bound input");
  }
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
const root = process.cwd();
const normalizedProfile = process.argv[2] === "normalized-react";
if (process.argv[2] !== undefined && !normalizedProfile) throw new Error("Unknown React replay profile");
const admission = normalizedProfile ? await normalizedReactAdmission() : null;
const output = path.join(root, normalizedProfile ? ".gate/gen/normalized-react" : ".gate/gen/original");
fs.mkdirSync(output, { recursive: true });
const hash = (bytes) => createHash("sha256").update(bytes).digest("hex");
const bytes = (file) => fs.readFileSync(path.join(root, file));
const manifestBytes = bytes("frontend/package.json"), lockBytes = bytes("frontend/package-lock.json");
const manifest = JSON.parse(manifestBytes), lock = JSON.parse(lockBytes);
if (!normalizedProfile && (hash(manifestBytes) !== "efde2d3fbdebc5899dc63ca6b518cab0d60370ef36a7301477da720f4978e2e9" ||
    hash(lockBytes) !== "f72661b4bd7ad129a6771037bf900a616a0fdf84bbb41f70c6d118b69fb1b62c")) {
  throw new Error("Original qualification requires the unchanged original manifest and lock bytes");
}
const archive = bytes("frontend/vendor/roedu-ui-0.3.0.tgz");
if (hash(archive) !== "1934a81cdfd737a051f591ebcae072f5028943b715456dbb2899b483d399c244") throw new Error("Original SDK changed");
const entries = readTarGz(archive);
const proofPrefix = normalizedProfile ? ".gate/gen/normalized-react/evidence" : "docs/reviews/gui-original-react";
const evidence = path.join(output, "evidence");
fs.mkdirSync(evidence, { recursive: true });
function snapshot(name, data) {
  fs.writeFileSync(path.join(evidence, name), data);
  return { path: `${proofPrefix}/${name}`, sha256: hash(data) };
}
const graph = { manifest: snapshot(normalizedProfile ? "normalized-package.json" : "original-package.json", manifestBytes), lock: snapshot(normalizedProfile ? "normalized-lock.json" : "original-lock.json", lockBytes) };
snapshot("original-ui-0.3.0.tgz", archive);
const fixtureSource = snapshot("runtime.spec.mjs", bytes("frontend/e2e/original/runtime.spec.mjs"));
snapshot("playwright.original.config.mjs", bytes("frontend/playwright.original.config.mjs"));
snapshot("reporter.mjs", bytes("frontend/e2e/original/reporter.mjs"));
snapshot("games.mjs", bytes("frontend/e2e/games.mjs"));
snapshot("native-plan.mjs", bytes("frontend/e2e/native-plan.mjs"));
snapshot("seeded-starts.json", bytes("frontend/e2e/seeded-starts.json"));
snapshot("gui-original-execution.mjs", bytes("scripts/gui-original-execution.mjs"));
const sourceFiles = [];
function walk(directory) {
  for (const entry of fs.readdirSync(path.join(root, directory), { withFileTypes: true }).sort((a, b) => a.name.localeCompare(b.name))) {
    const file = `${directory}/${entry.name}`;
    if (entry.isDirectory()) walk(file);
    else if (entry.isFile()) sourceFiles.push({ path: file, sha256: hash(bytes(file)) });
    else throw new Error("Original source contains a nonregular path");
  }
}
walk("frontend/src");
snapshot("source-hashes.json", Buffer.from(JSON.stringify({ schema: 1, sha: process.env.GATE_SHA, files: sourceFiles }, null, 2) + "\n"));
const transport = path.join(root, ".gate/gen/original/playwright.json");
fs.rmSync(transport, { force: true });
const cli = "frontend/node_modules/@playwright/test/cli.js";
const args = [cli, "test", "--config", "frontend/playwright.original.config.mjs"];
if (normalizedProfile) args.push("--output", ".gate/gen/normalized-react/browser-output");
const started = new Date().toISOString();
const child = spawnSync(process.execPath, args, { cwd: root, env: process.env, encoding: "utf8", maxBuffer: 64 * 1024 * 1024 });
const finished = new Date().toISOString();
if (normalizedProfile) {
  fs.writeFileSync(path.join(output, "playwright-stdout.log"), child.stdout || "");
  fs.writeFileSync(path.join(output, "playwright-stderr.log"), child.stderr || "");
  fs.writeFileSync(path.join(output, "playwright-command.json"), JSON.stringify({ schema: 1, command: process.execPath, args, cwd: ".", started, finished, exit_code: child.status ?? -1, ...(child.error ? { error: child.error.message } : {}), stdout: { path: ".gate/gen/normalized-react/playwright-stdout.log", sha256: hash(child.stdout || "") }, stderr: { path: ".gate/gen/normalized-react/playwright-stderr.log", sha256: hash(child.stderr || "") } }, null, 2) + "\n");
  if (fs.existsSync(transport)) fs.copyFileSync(transport, path.join(output, "playwright.json"));
}
if (child.stdout) process.stderr.write(child.stdout);
if (child.stderr) process.stderr.write(child.stderr);
if (child.error || child.status !== 0) throw new Error(`Actual original Playwright command failed (${child.status ?? "unavailable"})`);
const browser = JSON.parse(fs.readFileSync(transport));
const expected = ["intrusul", "perechi"].flatMap((game) => [
  "intro-single-flight", "leaving-actions", "leaving-earned-hint", "leaving-recovery-retry", "held-winning-mutation", "held-winning-read", "held-winning-unmounted", "private-upload-once-after-resume",
].map((name) => `original-${game}-${name}`));
if (browser.status !== "pass" || browser.fixtures.length !== expected.length ||
    JSON.stringify(browser.fixtures.map((item) => item.id).sort()) !== JSON.stringify(expected.sort()) ||
    browser.fixtures.some((item) => item.executed !== true || item.assertions.some((assertion) => assertion.executed !== true || assertion.status !== "pass"))) {
  throw new Error("Original fixture set did not execute completely without skips/retries");
}
const runtime = Object.fromEntries(["react", "react-dom", "framer-motion"].map((name) => [name, lock.packages[`node_modules/${name}`].version]));
if (!normalizedProfile && (manifest.dependencies["@roedu/ui"] !== "file:vendor/roedu-ui-0.3.0.tgz" || runtime.react !== "19.2.7" || runtime["react-dom"] !== "19.2.7" || runtime["framer-motion"] !== "12.42.2")) throw new Error("Original runtime identity differs");
if (normalizedProfile) {
  assert.deepEqual(browser.fixtures.map(({ id, suite, assertions }) => ({ id, suite, assertions: assertions.map(({ id }) => id) })).sort((a, b) => a.id.localeCompare(b.id)), [...admission.sealed_fixtures].sort((a, b) => a.id.localeCompare(b.id)), "Unchanged sealed 16/78 assertions required");
  for (const item of sourceFiles) assert.equal(hash(bytes(item.path)), item.sha256, "Normalized source changed during sealed replay");
  recheckNormalizedReactInputs(admission);
}
const report = {
  schema: 1, check: normalizedProfile ? "cat-normalized-react-runtime-execution" : "cat-original-ui-runtime-execution", status: "pass", app: "cat_de_roman_esti",
  ...(normalizedProfile ? { mode: "normalized-react", proof_scope: "owning-gen-built-native-server-sealed-16-78-replay", canonical_full: false, app_image_id: null, admission } : {}),
  sha: process.env.GATE_SHA, tree_sha256: process.env.GATE_TREE_SHA256, toolchain_digest: process.env.TOOLCHAIN_DIGEST,
  runtime_sdk: { name: "@roedu/ui", version: "0.3.0", archive_sha256: hash(archive), manifest_sha256: hash(entries.get("package/package.json").data), entry: "dist/index.js", entry_sha256: hash(entries.get("package/dist/index.js").data) },
  runtime_dependencies: normalizedProfile ? admission.runtime_dependencies : runtime, dependency_graph: graph,
  fixtures: browser.fixtures.map((item) => ({ id: item.id, suite: item.suite, source: fixtureSource, assertions: item.assertions, executed: true })),
};
if (normalizedProfile) fs.writeFileSync(path.join(evidence, "native-report.json"), JSON.stringify(report, null, 2) + "\n");
// Actual command stdout is the native report, retained verbatim by createHook.
process.stdout.write(JSON.stringify(report, null, 2) + "\n");

}
