import assert from "node:assert/strict";
import * as fs from "node:fs";
import path from "node:path";
import { createHash } from "node:crypto";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const frontend = fileURLToPath(new URL("../", import.meta.url));
export const EXPECTED_BROWSER_CASES = Object.freeze(JSON.parse(fs.readFileSync(
  new URL("../tests/browser/case-ids.json", import.meta.url), "utf8",
)));

// Validate actual Vitest JSON, including individual outcomes. A forged aggregate
// success/count cannot hide a skipped, missing, duplicated or failed test.
export function checkBrowserReport(report, expected = EXPECTED_BROWSER_CASES) {
  assert.equal(report.success, true, "Vitest must report success");
  assert.equal(report.numTotalTests, expected.length);
  assert.equal(report.numPassedTests, expected.length);
  assert.equal(report.numFailedTests, 0);
  assert.equal(report.numPendingTests, 0);
  assert.equal(report.testResults.length, 1, "The bounded source file must execute");
  assert.equal(report.testResults[0].status, "passed");
  const cases = report.testResults.flatMap((file) => file.assertionResults);
  assert.equal(cases.length, expected.length);
  assert.equal(new Set(cases.map((test) => test.fullName)).size, cases.length);
  const lexical = (left, right) => left < right ? -1 : left > right ? 1 : 0;
  assert.deepEqual(cases.map((test) => test.fullName).sort(lexical), [...expected].sort(lexical));
  for (const test of cases) {
    assert.equal(test.status, "passed", test.fullName);
    assert.deepEqual(test.failureMessages, [], test.fullName);
  }
  return cases.length;
}

function main() {
  assert.equal(fs.realpathSync(process.cwd()), fs.realpathSync(frontend));
  const root = path.dirname(frontend), descriptor = JSON.parse(fs.readFileSync(
    path.join(root, ".gate/wrapper-current.json"), "utf8",
  ));
  assert.equal(descriptor.sha, process.env.GATE_SHA);
  assert.equal(descriptor.tree_sha256, process.env.GATE_TREE_SHA256);
  assert.equal(descriptor.toolchain_digest, process.env.TOOLCHAIN_DIGEST);
  const pins = new Map(JSON.parse(fs.readFileSync(path.join(root, "versions.lock.json"), "utf8"))
    .tools.map((entry) => [entry.tool, entry.version]));
  const manifest = JSON.parse(fs.readFileSync(path.join(frontend, "package.json"), "utf8"));
  const lock = JSON.parse(fs.readFileSync(path.join(frontend, "package-lock.json"), "utf8"));
  const expected = {
    vitest: "5.0.3", "@vitest/browser": "5.0.3", "@vitest/browser-playwright": "5.0.3",
    preact: "11.0.0", vite: "8.3.3", "@playwright/test": "1.63.0", playwright: "1.63.0",
  };
  for (const [name, version] of Object.entries(expected)) {
    assert.equal(pins.get(name), version, name);
    assert.equal(manifest.dependencies?.[name] ?? manifest.devDependencies?.[name], version, name);
    assert.equal(lock.packages[`node_modules/${name}`].version, version, name);
    const installed = JSON.parse(fs.readFileSync(path.join(frontend, "node_modules", name, "package.json"), "utf8"));
    assert.equal(installed.name, name); assert.equal(installed.version, version);
  }
  for (const [name, entry] of Object.entries(lock.packages)) {
    if (/(?:^|\/)node_modules\/(?:playwright|playwright-core)$/.test(name)) assert.equal(entry.version, "1.63.0", name);
    if (/(?:^|\/)node_modules\/vite$/.test(name)) assert.equal(entry.version, "8.3.3", name);
  }
  const run = (args) => {
    const child = spawnSync(process.execPath, args, { cwd: frontend, env: process.env,
      encoding: "utf8", maxBuffer: 16 * 1024 * 1024, timeout: 180000 });
    if (child.stdout) process.stdout.write(child.stdout);
    if (child.stderr) process.stderr.write(child.stderr);
    if (child.error) throw child.error;
    assert.equal(child.status, 0, "Actual pinned source-test command failed");
    return child.stdout;
  };
  run(["scripts/native-tsc.mjs", "--project", "tsconfig.browser.json", "--noEmit"]);
  const vitestPackage = JSON.parse(fs.readFileSync(path.join(frontend, "node_modules/vitest/package.json"), "utf8"));
  const rawCli = typeof vitestPackage.bin === "string" ? vitestPackage.bin : vitestPackage.bin.vitest;
  const cli = rawCli?.startsWith("./") ? rawCli.slice(2) : rawCli;
  assert.ok(typeof cli === "string" && cli && !path.isAbsolute(cli)
    && cli.split("/").every((part) => part && part !== "." && part !== ".."));
  // Vitest5 JSON reporters write files by default. Give this child a fresh
  // private path; never adopt the shared .vitest/json/output.json from an old run.
  assert.ok(["shell", "unit", "full"].includes(descriptor.target));
  assert.match(descriptor.invocation, /^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$/);
  assert.ok(typeof process.getuid === "function", "Unix owner identity required");
  const uid = process.getuid();
  const ownedDirectory = (directory) => {
    const info = fs.lstatSync(directory);
    assert.ok(info.isDirectory() && !info.isSymbolicLink() && fs.realpathSync(directory) === directory
      && info.uid === uid && (info.mode & 0o002) === 0, "Owned no-follow report directory required");
    return info;
  };
  const gateDirectory = path.join(root, ".gate", descriptor.target);
  for (const directory of [root, path.join(root, ".gate"), gateDirectory]) ownedDirectory(directory);
  const reportDirectory = fs.mkdtempSync(path.join(gateDirectory, `vitest-browser-${descriptor.invocation}-`));
  const originalDirectory = ownedDirectory(reportDirectory);
  const reportFile = path.join(reportDirectory, "output.json");
  assert.throws(() => fs.lstatSync(reportFile), { code: "ENOENT" }, "Report target must not already exist");
  run([path.join("node_modules/vitest", cli), "run", "--config", "vitest.browser.config.ts",
    "--reporter=json", "--outputFile", reportFile]);
  const currentDirectory = ownedDirectory(reportDirectory);
  assert.ok(originalDirectory.dev === currentDirectory.dev && originalDirectory.ino === currentDirectory.ino,
    "Fresh report directory changed during child execution");
  const stdout = (() => {
    const before = fs.lstatSync(reportFile, { bigint: true });
    assert.ok(before.isFile() && !before.isSymbolicLink() && before.nlink === 1n
      && before.uid === BigInt(uid) && before.size > 0n && before.size <= 16n * 1024n * 1024n
      && fs.realpathSync(reportFile) === reportFile, "Fresh regular report file required");
    const fd = fs.openSync(reportFile, fs.constants.O_RDONLY | fs.constants.O_NOFOLLOW | fs.constants.O_NONBLOCK);
    try {
      const opened = fs.fstatSync(fd, { bigint: true }), bytes = fs.readFileSync(fd);
      const after = fs.fstatSync(fd, { bigint: true }), current = fs.lstatSync(reportFile, { bigint: true });
      assert.ok(opened.isFile() && ["dev", "ino", "mode", "size", "mtimeNs", "ctimeNs"].every((key) =>
        before[key] === opened[key] && opened[key] === after[key] && after[key] === current[key])
        && BigInt(bytes.length) === after.size, "Report changed while reading actual bytes");
      return bytes;
    } finally { fs.closeSync(fd); }
  })();
  const passed = checkBrowserReport(JSON.parse(stdout.toString("utf8")));
  const hash = (bytes) => createHash("sha256").update(bytes).digest("hex");
  // One tagged JSON line retains the actual complete reporter bytes in the
  // canonical npm-test stdout artifact, including its exact byte hash/length.
  // Base64 is lossless: this is not a summary or a newly invented test receipt.
  process.stdout.write("CAT_VITEST_REPORT " + JSON.stringify({ encoding: "base64",
    bytes: Buffer.byteLength(stdout), sha256: hash(stdout), data: Buffer.from(stdout).toString("base64"),
  }) + "\n");
  // These genuine nested streams are retained by the existing npm-test gate
  // command log. No hand-authored result.json or separate acceptance receipt.
  process.stdout.write("CAT_VITEST_BINDING " + JSON.stringify({ schema: 1, check: "plain-preact-browser-contracts",
    sha: descriptor.sha, tree_sha256: descriptor.tree_sha256,
    wrapper_invocation: descriptor.invocation, versions: expected, passed,
    report_sha256: hash(stdout), inventory_sha256: hash(fs.readFileSync(path.join(frontend, "tests/browser/case-ids.json"))),
  }) + "\n");
}

if (process.argv[1] && fs.realpathSync(process.argv[1]) === fs.realpathSync(fileURLToPath(import.meta.url))) main();
