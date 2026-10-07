import * as fs from "node:fs";
import path from "node:path";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { chromium } from "../frontend/node_modules/playwright/index.mjs";

const root = process.cwd(), output = ".gate/full";
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
  const child = spawnSync("node", args, { cwd: path.join(root, "frontend"), env: process.env, encoding: "utf8", maxBuffer: 64 * 1024 * 1024 });
  fs.writeFileSync(`${output}/playwright-${list ? "list" : "actual"}.json`, child.stdout || "");
  if (child.stderr) process.stderr.write(child.stderr);
  assert.equal(child.status, 0, `Actual Playwright ${list ? "discovery" : "execution"} failed`);
  const report = JSON.parse(child.stdout);
  assert.deepEqual(report.errors || [], []);
  return report;
}
const discovery = collect(playwright(true));
if (process.argv[2] === "inventory") {
  const cases = discovery.map(({ project, file, title }) => ({ lane: "pw-journeys", project, file, title }));
  assert.ok(cases.length > 0); assert.equal(new Set(cases.map(key)).size, cases.length);
  fs.mkdirSync(".gate/gen", { recursive: true });
  fs.writeFileSync(".gate/gen/browser-inventory.json", JSON.stringify({ schema: 1, cases }, null, 2) + "\n");
  process.stdout.write(`Actual discovered cases: ${cases.length}\n`);
  process.exit(0);
}
assert.match(process.env.GATE_APP_IMAGE_ID || "", /^sha256:[a-f0-9]{64}$/);
assert.ok(process.env.GATE_APP_URL, "Full browser qualification needs the actual app image URL");
const inventoryBytes = fs.readFileSync("frontend/e2e/gui-inventory.json"), expected = JSON.parse(inventoryBytes).cases;
assert.ok(expected.length > 0); assert.equal(new Set(expected.map(key)).size, expected.length);
assert.deepEqual(discovery.map(key).sort(), expected.map(key).sort(), "Discovery must equal committed case matrix");
const report = playwright(false), cases = collect(report);
assert.deepEqual(cases.map(key).sort(), expected.map(key).sort(), "Executed matrix changed");
assert.equal(cases.length, expected.length);
for (const item of cases) {
  assert.equal(item.expectedStatus, "passed"); assert.equal(item.status, "expected"); assert.equal(item.ok, true);
  assert.equal(item.results.length, 1); assert.equal(item.results[0].retry, 0); assert.equal(item.results[0].status, "passed");
}
for (const field of ["unexpected", "skipped", "flaky"]) assert.equal(report.stats[field], 0);
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
