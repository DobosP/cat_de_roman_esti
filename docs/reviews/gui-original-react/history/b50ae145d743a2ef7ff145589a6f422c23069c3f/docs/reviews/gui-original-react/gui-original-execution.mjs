import * as fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { readTarGz } from "../tools/gui-bootstrap-webkit/scripts/kit-sync.mjs";

const root = process.cwd();
const output = path.join(root, ".gate/gen/original");
fs.mkdirSync(output, { recursive: true });
const hash = (bytes) => createHash("sha256").update(bytes).digest("hex");
const bytes = (file) => fs.readFileSync(path.join(root, file));
const manifestBytes = bytes("frontend/package.json"), lockBytes = bytes("frontend/package-lock.json");
const manifest = JSON.parse(manifestBytes), lock = JSON.parse(lockBytes);
if (hash(manifestBytes) !== "efde2d3fbdebc5899dc63ca6b518cab0d60370ef36a7301477da720f4978e2e9" ||
    hash(lockBytes) !== "f72661b4bd7ad129a6771037bf900a616a0fdf84bbb41f70c6d118b69fb1b62c") {
  throw new Error("Original qualification requires the unchanged original manifest and lock bytes");
}
const archive = bytes("frontend/vendor/roedu-ui-0.3.0.tgz");
if (hash(archive) !== "1934a81cdfd737a051f591ebcae072f5028943b715456dbb2899b483d399c244") throw new Error("Original SDK changed");
const entries = readTarGz(archive);
const proofPrefix = "docs/reviews/gui-original-react";
const evidence = path.join(output, "evidence");
fs.mkdirSync(evidence, { recursive: true });
function snapshot(name, data) {
  fs.writeFileSync(path.join(evidence, name), data);
  return { path: `${proofPrefix}/${name}`, sha256: hash(data) };
}
const graph = { manifest: snapshot("original-package.json", manifestBytes), lock: snapshot("original-lock.json", lockBytes) };
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
fs.rmSync(path.join(output, "playwright.json"), { force: true });
const cli = "frontend/node_modules/@playwright/test/cli.js";
const args = [cli, "test", "--config", "frontend/playwright.original.config.mjs"];
const child = spawnSync(process.execPath, args, { cwd: root, env: process.env, encoding: "utf8", maxBuffer: 64 * 1024 * 1024 });
if (child.stdout) process.stderr.write(child.stdout);
if (child.stderr) process.stderr.write(child.stderr);
if (child.error || child.status !== 0) throw new Error(`Actual original Playwright command failed (${child.status ?? "unavailable"})`);
const browser = JSON.parse(fs.readFileSync(path.join(output, "playwright.json")));
const expected = ["intrusul", "perechi"].flatMap((game) => [
  "intro-single-flight", "leaving-actions", "leaving-earned-hint", "leaving-recovery-retry", "held-winning-mutation", "held-winning-read", "held-winning-unmounted", "private-upload-once-after-resume",
].map((name) => `original-${game}-${name}`));
if (browser.status !== "pass" || browser.fixtures.length !== expected.length ||
    JSON.stringify(browser.fixtures.map((item) => item.id).sort()) !== JSON.stringify(expected.sort()) ||
    browser.fixtures.some((item) => item.executed !== true || item.assertions.some((assertion) => assertion.executed !== true || assertion.status !== "pass"))) {
  throw new Error("Original fixture set did not execute completely without skips/retries");
}
const runtime = Object.fromEntries(["react", "react-dom", "framer-motion"].map((name) => [name, lock.packages[`node_modules/${name}`].version]));
if (manifest.dependencies["@roedu/ui"] !== "file:vendor/roedu-ui-0.3.0.tgz" || runtime.react !== "19.2.7" || runtime["react-dom"] !== "19.2.7" || runtime["framer-motion"] !== "12.42.2") throw new Error("Original runtime identity differs");
const report = {
  schema: 1, check: "cat-original-ui-runtime-execution", status: "pass", app: "cat_de_roman_esti",
  sha: process.env.GATE_SHA, tree_sha256: process.env.GATE_TREE_SHA256, toolchain_digest: process.env.TOOLCHAIN_DIGEST,
  runtime_sdk: { name: "@roedu/ui", version: "0.3.0", archive_sha256: hash(archive), manifest_sha256: hash(entries.get("package/package.json").data), entry: "dist/index.js", entry_sha256: hash(entries.get("package/dist/index.js").data) },
  runtime_dependencies: runtime, dependency_graph: graph,
  fixtures: browser.fixtures.map((item) => ({ id: item.id, suite: item.suite, source: fixtureSource, assertions: item.assertions, executed: true })),
};
// Actual command stdout is the native report, retained verbatim by createHook.
process.stdout.write(JSON.stringify(report, null, 2) + "\n");
