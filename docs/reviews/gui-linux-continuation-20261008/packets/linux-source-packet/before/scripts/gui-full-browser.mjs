import * as fs from "node:fs";
import path from "node:path";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { chromium } from "../frontend/node_modules/playwright/index.mjs";

const root = process.cwd(), originalProfile = process.argv[2] === "original", normalizedProfile = process.argv[2] === "normalized-react";
const reactProfile = originalProfile || normalizedProfile;
const { normalizedReactAdmission, recheckNormalizedReactInputs } = normalizedProfile ? await import("./gui-original-execution.mjs") : {};
const output = originalProfile ? ".gate/gen/original/complete-browser" : normalizedProfile ? ".gate/gen/normalized-react/complete-browser" : ".gate/full";
fs.mkdirSync(output, { recursive: true });
const hash = (bytes) => createHash("sha256").update(bytes).digest("hex");
function collect(report) {
  const cases = [];
  function visit(suite, parents = []) {
    const titles = [...parents, ...(suite.title ? [suite.title] : [])];
    for (const spec of suite.specs || []) for (const item of spec.tests || []) {
      const file = path.isAbsolute(spec.file) ? path.relative(root, spec.file) : path.relative(root, path.resolve(report.config.rootDir, spec.file));
      cases.push({ id: spec.id, project: item.projectName, file, title: [...titles, spec.title].join(" > "), expectedStatus: item.expectedStatus, status: item.status, results: item.results, ok: spec.ok });
    }
    for (const child of suite.suites || []) visit(child, titles);
  }
  for (const suite of report.suites || []) visit(suite);
  return cases;
}
const key = (item) => `${item.project}:${item.file}:${item.title}`;
function playwright(list) {
  const args = ["node_modules/@playwright/test/cli.js", "test", "--config", "playwright.gui.config.mjs", "--reporter=json", ...(list ? ["--list"] : [])];
  if (reactProfile) args.push("--output", `../${output}/browser-output`);
  const started = new Date().toISOString();
  const child = spawnSync(reactProfile ? process.execPath : "node", args, { cwd: path.join(root, "frontend"), env: process.env, encoding: "utf8", maxBuffer: 64 * 1024 * 1024 });
  fs.writeFileSync(`${output}/playwright-${list ? "list" : "actual"}.json`, child.stdout || "");
  if (reactProfile) {
    const name = list ? "discovery" : "execution";
    const stdout = `${output}/${name}-stdout.log`, stderr = `${output}/${name}-stderr.log`;
    fs.writeFileSync(stdout, child.stdout || ""); fs.writeFileSync(stderr, child.stderr || "");
    fs.writeFileSync(`${output}/${name}-command.json`, JSON.stringify({
      schema: 1, command: process.execPath, args, cwd: "frontend", started,
      finished: new Date().toISOString(), exit_code: child.status ?? -1,
      ...(child.error ? { error: child.error.message } : {}),
      stdout: { path: stdout, sha256: hash(child.stdout || "") }, stderr: { path: stderr, sha256: hash(child.stderr || "") },
    }, null, 2) + "\n");
  }
  if (child.stderr) process.stderr.write(child.stderr);
  assert.equal(child.status, 0, `Actual Playwright ${list ? "discovery" : "execution"} failed`);
  const report = JSON.parse(child.stdout);
  assert.deepEqual(report.errors || [], []);
  return report;
}
// Both profiles execute this same strict discovery/execution validator.
function executeMatrix(discovery) {
  const inventoryBytes = fs.readFileSync("frontend/e2e/gui-inventory.json"), expected = JSON.parse(inventoryBytes).cases;
  assert.ok(expected.length > 0); assert.equal(new Set(expected.map(key)).size, expected.length);
  assert.deepEqual(discovery.map(key).sort(), expected.map(key).sort(), "Discovery must equal committed case matrix");
  const fixtureSources = reactProfile ? [...new Set(expected.map((item) => item.file))].sort().map((file) => {
    assert.ok(file.startsWith("frontend/e2e/"), "Original fixture must stay inside the existing browser suite");
    return originalInput(file);
  }) : null;
  const report = playwright(false), cases = collect(report);
  assert.deepEqual(cases.map(key).sort(), expected.map(key).sort(), "Executed matrix changed");
  assert.equal(cases.length, expected.length);
  for (const item of cases) {
    assert.equal(item.expectedStatus, "passed"); assert.equal(item.status, "expected"); assert.equal(item.ok, true);
    assert.equal(item.results.length, 1); assert.equal(item.results[0].retry, 0); assert.equal(item.results[0].status, "passed");
  }
  for (const field of ["unexpected", "skipped", "flaky"]) assert.equal(report.stats[field], 0);
  return { inventoryBytes, expected, report, cases, fixtureSources };
}
function originalInput(relative) {
  assert.ok(typeof relative === "string" && relative && !path.isAbsolute(relative)
    && !/[\\:\x00-\x1f\x7f]/.test(relative) && relative.split("/").every((part) => part && part !== "." && part !== ".."), "Confined original browser input required");
  const absolute = path.resolve(root, relative);
  assert.equal(fs.realpathSync(absolute), absolute, "Original browser input symlink/alias refused");
  assert.ok(fs.lstatSync(absolute).isFile(), "Regular original browser input required");
  const bytes = fs.readFileSync(absolute);
  return { path: relative, bytes: bytes.length, sha256: hash(bytes) };
}
function originalPrerequisites() {
  assert.equal(process.env.GATE_APP_URL || "", "", "Original browser profile starts its built native server, not an app image");
  assert.equal(process.env.GATE_APP_IMAGE_ID || "", "", "Original browser profile has no app-image qualification");
  assert.match(process.env.GATE_SHA || "", /^[a-f0-9]{40}(?:[a-f0-9]{24})?$/);
  assert.match(process.env.GATE_TREE_SHA256 || "", /^[a-f0-9]{64}$/);
  assert.match(process.env.TOOLCHAIN_DIGEST || "", /^sha256:[a-f0-9]{64}$/);
  assert.ok(["true", "false"].includes(process.env.GATE_DIRTY));
  assert.equal(process.env.GATE_VERSIONS_RESOLVE, "0", "Original browser profile forbids version resolution");
  const descriptorInput = originalInput(".gate/wrapper-current.json"), descriptorBytes = fs.readFileSync(descriptorInput.path);
  const descriptor = JSON.parse(descriptorBytes);
  assert.equal(descriptor.target, "gen"); assert.equal(descriptor.sha, process.env.GATE_SHA);
  assert.equal(descriptor.tree_sha256, process.env.GATE_TREE_SHA256); assert.equal(descriptor.toolchain_digest, process.env.TOOLCHAIN_DIGEST);
  assert.equal(descriptor.config_path, ".gate/gen/wrapper-kit-config.json");
  assert.deepEqual(fs.readFileSync(".gate/gen/wrapper-current.json"), descriptorBytes);
  const configInput = originalInput(descriptor.config_path); assert.equal(configInput.sha256, descriptor.config_file_sha256);
  const request = JSON.parse(fs.readFileSync("scripts/gui-gen-request.json"));
  assert.equal(request.operation, "qualify-original-react", "Owning existing original qualification request required");
  const inputs = ["frontend/package.json", "frontend/package-lock.json", "frontend/vendor/roedu-ui-0.3.0.tgz"].map(originalInput);
  inputs.push(descriptorInput, originalInput(".gate/gen/wrapper-current.json"), configInput, originalInput(".gate/gen/bootstrap-execution.json"), originalInput("versions.lock.json"));
  for (const [index, expected] of [
    "efde2d3fbdebc5899dc63ca6b518cab0d60370ef36a7301477da720f4978e2e9",
    "f72661b4bd7ad129a6771037bf900a616a0fdf84bbb41f70c6d118b69fb1b62c",
    "1934a81cdfd737a051f591ebcae072f5028943b715456dbb2899b483d399c244",
  ].entries()) assert.equal(inputs[index].sha256, expected, "Exact original manifest/lock/SDK required");
  for (const [name, version] of [["react", "19.2.7"], ["react-dom", "19.2.7"], ["framer-motion", "12.42.2"], ["@roedu/ui", "0.3.0"]]) {
    const file = `frontend/node_modules/${name}/package.json`;
    inputs.push(originalInput(file));
    const installed = JSON.parse(fs.readFileSync(file));
    assert.equal(installed.name, name); assert.equal(installed.version, version);
  }
  for (const [key, name] of [["CDR_NATIVE_BINARY", "cat-server"], ["CDR_BROWSER_PLAN_BINARY", "cat-browser-plan"]]) {
    const absolute = process.env[key];
    assert.equal(absolute, path.join(root, ".gate/gen", name), "Original browser binaries must come from this owning gen build");
    inputs.push(originalInput(path.relative(root, absolute)));
  }
  inputs.push(...["scripts/gui-full-browser.mjs", "scripts/gui-gen-request.json", "scripts/gui-repo-hook.mjs",
    "frontend/playwright.gui.config.mjs", "frontend/playwright.config.mjs", "frontend/e2e/gui-inventory.json",
    "frontend/e2e/games.mjs", "frontend/e2e/native-plan.mjs", "frontend/e2e/seeded-starts.json",
    "frontend/e2e/alchimie-111-checkpoint.json", "frontend/e2e/alchimie-221-checkpoint.json", "frontend/e2e/alchimie-221-expanded-checkpoint.json",
    "frontend/node_modules/@roedu/ui/dist/index.js", "frontend/node_modules/@playwright/test/cli.js",
    ".gate/gen/original/evidence/receipt.json", ".gate/gen/original/evidence/source-hashes.json",
    "cat_de_roman_esti/web/static/index.html", "cat_de_roman_esti/web/static/.vite/manifest.json"].map(originalInput));
  const receipt = JSON.parse(fs.readFileSync(".gate/gen/original/evidence/receipt.json"));
  assert.equal(receipt.sha, descriptor.sha); assert.equal(receipt.tree_sha256, descriptor.tree_sha256); assert.equal(receipt.toolchain_digest, descriptor.toolchain_digest);
  assert.equal(inputs.find((item) => item.path === "frontend/node_modules/@roedu/ui/dist/index.js").sha256,
    receipt.runtime_sdk.entry_sha256, "Installed original SDK entry differs from the already verified sealed archive");
  return inputs;
}
async function normalizedPrerequisites() {
  const admission = await normalizedReactAdmission();
  const inputs = [...admission.inputs, ...[".gate/gen/normalized-react/evidence/native-report.json", ".gate/gen/normalized-react/evidence/source-hashes.json",
    ".gate/gen/normalized-react/playwright.json", ".gate/gen/normalized-react/playwright-command.json"].map(originalInput)];
  const native = JSON.parse(fs.readFileSync(".gate/gen/normalized-react/evidence/native-report.json"));
  assert.equal(native.check, "cat-normalized-react-runtime-execution"); assert.equal(native.status, "pass"); assert.equal(native.mode, "normalized-react");
  assert.equal(native.sha, process.env.GATE_SHA); assert.equal(native.tree_sha256, process.env.GATE_TREE_SHA256); assert.equal(native.toolchain_digest, process.env.TOOLCHAIN_DIGEST);
  assert.equal(native.canonical_full, false); assert.equal(native.app_image_id, null);
  assert.deepEqual(native.admission, admission); assert.deepEqual(native.runtime_dependencies, admission.runtime_dependencies);
  const browser = JSON.parse(fs.readFileSync(".gate/gen/normalized-react/playwright.json"));
  assert.equal(browser.status, "pass"); assert.equal(browser.cases.length, 16); assert.equal(browser.fixtures.length, 16);
  for (const item of browser.cases) { assert.equal(item.status, "passed"); assert.equal(item.retry, 0); assert.equal(item.expectedStatus, "passed"); assert.deepEqual(item.errors, []); }
  assert.deepEqual(native.fixtures.map(({ id, suite, assertions, executed }) => ({ id, suite, assertions, executed })), browser.fixtures.map(({ id, suite, assertions, executed }) => ({ id, suite, assertions, executed })));
  assert.deepEqual(native.fixtures.map(({ id, suite, assertions }) => ({ id, suite, assertions: assertions.map(({ id }) => id) })).sort((a, b) => a.id.localeCompare(b.id)), [...admission.sealed_fixtures].sort((a, b) => a.id.localeCompare(b.id)));
  for (const item of native.fixtures) { assert.equal(item.executed, true); for (const assertion of item.assertions) { assert.equal(assertion.executed, true); assert.equal(assertion.status, "pass"); } }
  for (const record of [native.dependency_graph.manifest, native.dependency_graph.lock, ...native.fixtures.map((item) => item.source)]) {
    const input = originalInput(record.path); assert.equal(input.sha256, record.sha256); inputs.push(input);
  }
  assert.equal(native.dependency_graph.manifest.sha256, admission.inputs.find((item) => item.path === "frontend/package.json").sha256);
  assert.equal(native.dependency_graph.lock.sha256, admission.inputs.find((item) => item.path === "frontend/package-lock.json").sha256);
  const sourceHashes = JSON.parse(fs.readFileSync(".gate/gen/normalized-react/evidence/source-hashes.json"));
  assert.equal(sourceHashes.sha, process.env.GATE_SHA);
  for (const record of sourceHashes.files) { const input = originalInput(record.path); assert.equal(input.sha256, record.sha256); inputs.push(input); }
  const command = JSON.parse(fs.readFileSync(".gate/gen/normalized-react/playwright-command.json"));
  assert.equal(command.exit_code, 0); assert.equal(command.command, process.execPath);
  assert.deepEqual(command.args, ["frontend/node_modules/@playwright/test/cli.js", "test", "--config", "frontend/playwright.original.config.mjs", "--output", ".gate/gen/normalized-react/browser-output"]);
  for (const log of [command.stdout, command.stderr]) { const input = originalInput(log.path); assert.equal(input.sha256, log.sha256); inputs.push(input); }
  return { admission, inputs };
}
const normalized = normalizedProfile ? await normalizedPrerequisites() : null;
const originalInputs = originalProfile ? originalPrerequisites() : null;
const discovery = collect(playwright(true));
if (process.argv[2] === "inventory") {
  const cases = discovery.map(({ project, file, title }) => ({ lane: "pw-journeys", project, file, title }));
  assert.ok(cases.length > 0); assert.equal(new Set(cases.map(key)).size, cases.length);
  fs.mkdirSync(".gate/gen", { recursive: true });
  fs.writeFileSync(".gate/gen/browser-inventory.json", JSON.stringify({ schema: 1, cases }, null, 2) + "\n");
  process.stdout.write(`Actual discovered cases: ${cases.length}\n`);
  process.exit(0);
}
if (reactProfile) {
  const { inventoryBytes, expected, report, cases, fixtureSources } = executeMatrix(discovery);
  for (const input of [...(originalInputs || normalized.inputs), ...fixtureSources]) assert.deepEqual(originalInput(input.path), input, "Original execution changed a bound input");
  if (normalizedProfile) recheckNormalizedReactInputs(normalized.admission);
  const commands = ["discovery", "execution"].map((name) => originalInput(`${output}/${name}-command.json`));
  const reports = ["list", "actual"].map((name) => originalInput(`${output}/playwright-${name}.json`));
  const actual = {
    schema: 1, check: normalizedProfile ? "cat-normalized-react-complete-browser" : "cat-original-complete-browser", status: "pass", mode: normalizedProfile ? "normalized-react" : "original-react",
    proof_scope: "owning-gen-built-native-server-complete-browser-matrix", canonical_full: false, app_image_id: null,
    sha: process.env.GATE_SHA, tree_sha256: process.env.GATE_TREE_SHA256,
    toolchain_digest: process.env.TOOLCHAIN_DIGEST, dirty: process.env.GATE_DIRTY === "true",
    inputs: originalInputs || normalized.inputs, ...(normalizedProfile ? { admission: normalized.admission } : {}), fixture_sources: fixtureSources, inventory_sha256: hash(inventoryBytes),
    commands, reports, expected_count: expected.length, stats: report.stats, cases,
  };
  fs.writeFileSync(`${output}/report.json`, JSON.stringify(actual, null, 2) + "\n");
  process.stdout.write(JSON.stringify(actual) + "\n");
  process.exit(0);
}
assert.match(process.env.GATE_APP_IMAGE_ID || "", /^sha256:[a-f0-9]{64}$/);
assert.ok(process.env.GATE_APP_URL, "Full browser qualification needs the actual app image URL");
const { inventoryBytes, expected, report, cases } = executeMatrix(discovery);
fs.writeFileSync(`${output}/browser-pw-journeys.json`, JSON.stringify({ schema: 1, lane: "pw-journeys", sha: process.env.GATE_SHA, tree_sha256: process.env.GATE_TREE_SHA256, app_image_id: process.env.GATE_APP_IMAGE_ID, inventory_sha256: hash(inventoryBytes), expected_count: expected.length, cases }, null, 2) + "\n");

// Independently fetch the actual image identity and every emitted manifest asset.
// The server identity endpoint is implemented by M1 delivery; absence fails full.
const manifestBytes = fs.readFileSync("go-backend/embedfs/dist/.vite/manifest.json"), manifest = JSON.parse(manifestBytes);
const response = await fetch(new URL("/api/gui-build", process.env.GATE_APP_URL));
assert.equal(response.status, 200, "M1 actual embedded build identity required");
const identity = await response.json();
assert.equal(identity.sha, process.env.GATE_SHA); assert.equal(identity.tree_sha256, process.env.GATE_TREE_SHA256);
assert.equal(identity.manifest_sha256, hash(manifestBytes)); assert.equal(identity.versions_lock_sha256, hash(fs.readFileSync("versions.lock.json")));
const files = new Set(), visited = new Set();
function visit(entry) {
  if (visited.has(entry)) return; visited.add(entry);
  const item = manifest[entry]; assert.ok(item);
  files.add(item.file); for (const file of [...item.css || [], ...item.assets || []]) files.add(file);
  for (const imported of [...item.imports || [], ...item.dynamicImports || []]) visit(imported);
}
visit("index.html");
const assets = [];
for (const file of [...files].sort()) {
  const url = new URL(`/${file}`, process.env.GATE_APP_URL).href, actual = await fetch(url);
  assert.equal(actual.status, 200); const data = Buffer.from(await actual.arrayBuffer()), local = fs.readFileSync(`go-backend/embedfs/dist/${file}`);
  assert.deepEqual(data, local); assets.push({ file, url, bytes: data.length, sha256: hash(data) });
}
fs.writeFileSync(`${output}/app-witness.json`, JSON.stringify({ schema: 1, sha: process.env.GATE_SHA, tree_sha256: process.env.GATE_TREE_SHA256, app_image_id: process.env.GATE_APP_IMAGE_ID, identity, entry: "index.html", assets }, null, 2) + "\n");
const browser = await chromium.launch();
try {
  const observations = [], violations = [];
  const routes = ["/", "/intrusul", "/perechi", "/conexiuni", "/alchimie?mode=challenges", "/alchimie?mode=explore", "/cald-rece", "/lant", "/clasament"];
  for (const route of routes) {
    const page = await browser.newPage({ reducedMotion: "no-preference" });
    page.on("console", (message) => { if (/Content Security Policy|Refused to (?:execute|apply|load)/i.test(message.text())) violations.push({ route, message: message.text() }); });
    await page.addInitScript(() => {
      window.__cspViolations = [];
      document.addEventListener("securitypolicyviolation", (event) => window.__cspViolations.push({ directive: event.violatedDirective, blocked: event.blockedURI }));
    });
    const html = await page.goto(new URL(route, process.env.GATE_APP_URL).href);
    const header = process.env.CSP_STAGE === "enforced" ? "content-security-policy" : "content-security-policy-report-only";
    assert.ok(html.headers()[header], `Actual ${header} required`);
    if (process.env.CSP_STAGE === "enforced") assert.equal(html.headers()["content-security-policy-report-only"], undefined);
    await page.locator(".screen").first().waitFor();
    const observation = await page.evaluate(() => {
      const scripts = [...document.querySelectorAll("script")], module = scripts.find((item) => item.type === "module");
      const css = [...document.querySelectorAll('link[rel="stylesheet"]')].map((item) => item.href);
      const preloads = [...document.querySelectorAll('link[rel="modulepreload"]')].map((item) => item.href);
      return { nonces: scripts.map((item) => item.nonce), module: module?.src, css, preloads, json: scripts.filter((item) => item.type === "application/json").length, violations: window.__cspViolations };
    });
    assert.ok(observation.nonces.length > 0 && observation.nonces.every((nonce) => nonce && nonce === observation.nonces[0]));
    assert.ok(observation.module); assert.ok(observation.css.length > 0);
    violations.push(...observation.violations.map((item) => ({ route, ...item })));
    observations.push({ page: route, nonce_sha256: hash(observation.nonces[0]), scripts: observation.nonces.length, json: observation.json,
      assetLinks: observation.css.length + observation.preloads.length, module: new URL(observation.module).pathname, module_url: observation.module,
      css: observation.css.map((url) => new URL(url).pathname), css_urls: observation.css,
      preloads: observation.preloads.map((url) => new URL(url).pathname), preload_urls: observation.preloads });
    await page.close();
  }
  fs.writeFileSync(`${output}/csp-measurement.json`, JSON.stringify({ schema: 1, sha: process.env.GATE_SHA, tree_sha256: process.env.GATE_TREE_SHA256, app_image_id: process.env.GATE_APP_IMAGE_ID, stage: process.env.CSP_STAGE, violations: violations.length, legacy_violations: 0, pages: routes.length, nonceObservations: observations, observedViolations: violations }, null, 2) + "\n");
  assert.equal(violations.length, 0);
} finally { await browser.close(); }
const baseline = spawnSync("node", ["scripts/gui-baseline.mjs", "verify"], { cwd: root, env: process.env, encoding: "utf8", maxBuffer: 64 * 1024 * 1024 });
if (baseline.stderr) process.stderr.write(baseline.stderr);
fs.writeFileSync(`${output}/baseline-stdout.log`, baseline.stdout || "");
assert.equal(baseline.status, 0, "Actual screenshots/axe/vitals must match original baselines");
process.stdout.write(`Actual image ${process.env.GATE_APP_IMAGE_ID}: ${cases.length} browser cases, ${assets.length} fetched assets, CSP/axe/screenshots/vitals passed\n`);
