// Consumer quality rules use native Oxlint, not an ESLint compatibility layer.
// The immutable kit AST checker remains the mandatory import/compat/transitive,
// inline-style/handler and v11 policy owner, including its closed legacy scopes.
// Its core-only Oxlint preset has unscoped React bans: duplicating those here
// would reject the explicitly staged React source instead of reporting pending.
// No source/component path is exempted, including CspElements.tsx.
// Native compiler config/gating use fixed valid/no-gating engine options; the
// old 7.1 hook-factory rule is a deprecated noop. Actual engine probing is required
// before asserting equivalence. References: https://oxc.rs/blog/2026-08-18-react-compiler-support
import assert from "node:assert/strict";
import * as fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { createHash, randomUUID } from "node:crypto";
import { fileURLToPath, pathToFileURL } from "node:url";

const frontend = fs.realpathSync(fileURLToPath(new URL("../", import.meta.url)));
const root = path.dirname(frontend);
assert.equal(process.cwd(), frontend, "Run the owning frontend lint script from its package");
const descriptor = JSON.parse(fs.readFileSync(path.join(root, ".gate/wrapper-current.json")));
assert.equal(descriptor.sha, process.env.GATE_SHA);
assert.equal(descriptor.tree_sha256, process.env.GATE_TREE_SHA256);
assert.equal(descriptor.toolchain_digest, process.env.TOOLCHAIN_DIGEST);
const configured = spawnSync("task", ["--silent", "repo:kit-config"], { cwd: root, env: process.env, encoding: "utf8" });
assert.equal(configured.status, 0, "Actual repo kit configuration required");
assert.equal(configured.stderr, "", "Kit configuration emitted diagnostics");
const selected = JSON.parse(configured.stdout);
assert.ok(typeof selected.npm_dir === "string" && !path.isAbsolute(selected.npm_dir)
  && selected.npm_dir.split("/").every((part) => part && ![".", ".."].includes(part)));
const kitRoot = path.join(root, selected.npm_dir);
const { readKitConfig, regularPath } = await import(pathToFileURL(path.join(kitRoot, "scripts/locate-kit.mjs")).href);
const config = readKitConfig(root, true);
assert.equal(config.packageRoot, kitRoot);
const pins = new Map(JSON.parse(fs.readFileSync(path.join(root, "versions.lock.json"))).tools.map((entry) => [entry.tool, entry.version]));
const lock = JSON.parse(fs.readFileSync(path.join(frontend, "package-lock.json")));
let nativeExecutable;
for (const name of ["oxlint", "oxlint-tsgolint", "@ast-grep/cli"]) {
  const installed = fs.realpathSync(path.join(frontend, "node_modules", name));
  const actual = JSON.parse(fs.readFileSync(path.join(installed, "package.json")));
  assert.equal(actual.name, name); assert.equal(actual.version, pins.get(name));
  assert.equal(lock.packages[`node_modules/${name}`].version, actual.version);
  if (name === "oxlint") {
    const bin = typeof actual.bin === "string" ? actual.bin : actual.bin?.oxlint;
    assert.ok(typeof bin === "string" && !path.isAbsolute(bin)
      && bin.split("/").every((part) => part && ![".", ".."].includes(part)));
    nativeExecutable = fs.realpathSync(path.join(installed, bin));
    assert.ok(nativeExecutable.startsWith(installed + path.sep), "Oxlint executable must belong to the verified package");
    assert.ok(fs.statSync(nativeExecutable).isFile(), "Oxlint executable must be regular");
  }
}

// Explicit source enumeration defeats hidden/VCS ignore files. These are only
// managed dependency/build/report caches, matching the kit's discovery boundary.
const caches = new Set(["node_modules", "dist", ".git", ".gate", ".vitest", "test-results"]);
const files = [];
function walk(directory) {
  for (const entry of fs.readdirSync(directory, { withFileTypes: true }).sort((a, b) => a.name.localeCompare(b.name))) {
    if (caches.has(entry.name)) continue;
    const full = path.join(directory, entry.name), stat = fs.lstatSync(full);
    assert.ok(!stat.isSymbolicLink(), "Frontend source symlinks are refused");
    if (stat.isDirectory()) walk(full);
    else {
      assert.ok(stat.isFile(), "Frontend source must be regular");
      if (/\.(?:[cm]?[jt]s|[jt]sx)$/.test(entry.name)) files.push(path.relative(frontend, full));
    }
  }
}
walk(frontend); assert.ok(files.length > 0);
const relative = `.gate/${descriptor.target.replaceAll(":", "-")}/frontend-lint/run-${randomUUID()}`;
const output = regularPath(root, relative, true); fs.mkdirSync(output, { recursive: true, mode: 0o700 });
const hash = (value) => createHash("sha256").update(value).digest("hex");
const commands = [], artifacts = [];
function run(label, executable, args, cwd) {
  const started = new Date().toISOString();
  const child = spawnSync(executable, args, { cwd, env: process.env, encoding: "utf8", maxBuffer: 64 * 1024 * 1024 });
  const streams = {};
  for (const stream of ["stdout", "stderr"]) {
    const bytes = Buffer.from(child[stream] ?? ""), filename = `${label}.${stream}.log`;
    fs.writeFileSync(path.join(output, filename), bytes, { flag: "wx", mode: 0o600 });
    streams[stream] = { path: `${relative}/${filename}`, sha256: hash(bytes) };
    artifacts.push(`${relative}/${filename} sha256:${hash(bytes)}`);
  }
  const command = { label, command: executable, args, cwd: path.relative(root, cwd) || ".", started,
    finished: new Date().toISOString(), exit_code: child.status ?? -1, signal: child.signal, ...streams,
    ...(child.error ? { error: child.error.message } : {}) };
  commands.push(command);
  if (child.stderr) process.stderr.write(child.stderr);
  return { child, command };
}
const native = run("oxlint", nativeExecutable, ["--config", "oxlint.config.json", "--type-aware", "--type-check",
  "--report-unused-disable-directives-severity", "error", "--no-ignore", "--", ...files], frontend);
if (native.child.stdout) process.stderr.write(native.child.stdout);
const ast = run("kit-ast", process.execPath, [regularPath(root, `${config.npm_dir}/scripts/ast-check.mjs`)], root);
if (ast.child.stdout) process.stderr.write(ast.child.stdout);
let astReport;
try { astReport = JSON.parse(ast.child.stdout); }
catch { astReport = null; }
const status = commands.every((command) => command.exit_code === 0 && !command.signal && !command.error)
  && astReport?.schema === 1 && astReport.check === "v11-lint" && astReport.status === "pass" ? "pass" : "fail";
const report = { schema: 1, check: "cat-frontend-lint", status, sha: descriptor.sha, tree_sha256: descriptor.tree_sha256,
  toolchain_digest: descriptor.toolchain_digest, config_sha256: descriptor.config_sha256, source_files: files,
  commands, artifacts, kit_ast: astReport, capability_equivalence: "PENDING_ACTUAL_ENGINE_PROBE" };
fs.writeFileSync(path.join(output, "report.json"), JSON.stringify(report, null, 2) + "\n", { flag: "wx", mode: 0o600 });
process.stdout.write(JSON.stringify(report) + "\n");
process.exitCode = status === "pass" ? 0 : 1;
