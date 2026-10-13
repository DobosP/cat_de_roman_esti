// Historical race evidence may be reused only under an exact reviewed native
// source audit, unchanged data and fresh GUI/API contracts. This is a source-
// based audit, not a claim that test binaries or compiler inputs are identical.
// Original result/command/log bindings are checked by gui-unit-reuse.
import * as fs from "node:fs";
import path from "node:path";
import { createHash } from "node:crypto";
import { spawnSync } from "node:child_process";
import { pathToFileURL } from "node:url";

const hash = (value) => createHash("sha256").update(value).digest("hex");
const HEX = /^[a-f0-9]{64}$/;
const SHA = /^[a-f0-9]{40}(?:[a-f0-9]{24})?$/;
const MODULE = "github.com/DobosP/cat_de_roman_esti/go-backend";
const EMBED = `${MODULE}/embedfs`;
const CONTENT_RAILS = `${MODULE}/internal/contentrails`;
const PG = new Set([`${MODULE}/internal/accounts`, `${MODULE}/internal/httpapi`]);
const ALWAYS_FRESH = new Set([...PG, ...["internal/httpgolden", "internal/guibuild", "cmd/cat-server", "cmd/cat-browser-plan",
  "internal/browserplan", "internal/content", "internal/doccheck"].map((name) => `${MODULE}/${name}`)]);
export const NATIVE_REUSE_POLICY = "historical-audited-source-reuse-with-fresh-gui-api-contracts-v2";
// Independently reviewed source at e82e5562; never regenerate this pin after a
// native change without another explicit semantic audit and review. Rows are
// sorted {path,mode:0777,sha256} for every .go/go.mod/go.sum in both native trees.
export const AUDITED_NATIVE_SOURCE = Object.freeze({ count: 238, sha256: "6eb3a47f4fb5d7445dc916c01a47d1db6e627c4ea39752ab16a30e1c63946b3c" });
const ignored = new Set([".git", "node_modules", ".gate", ".vitest", "test-results", "TASK_BRIEF.md", "TASK_RESULT.md", "SWARM_RESULT.md"]);
const frontendInputs = new Set(["frontend/package.json", "frontend/package-lock.json", "frontend/src/release.ts", "frontend/e2e/seeded-starts.json"]);
export const BACKEND_RACE_ARGS = Object.freeze(["test", "-race", "-timeout=30m", "-count=1", "-json", "./..."]);
export const NATIVE_GRAPH_ARGS = Object.freeze(["list", "-race", "-deps", "-test", "-json", "./..."]);
function demand(condition, reason) { if (!condition) throw Error(reason); }
const equal = (a, b) => JSON.stringify(a) === JSON.stringify(b);
function relative(name) {
  demand(typeof name === "string" && name.length > 0 && !name.startsWith("/") && !/[\\\x00-\x1f\x7f]/.test(name)
    && name.split("/").every((part) => part && part !== "." && part !== ".."), "unsafe native input path");
  return name;
}
function excluded(name) {
  return name.split("/").some((part) => ignored.has(part) || part === ".env" || part.startsWith(".env."))
    || /^(?:dist|frontend\/dist)(?:\/|$)/.test(name);
}
const generated = name => /^go-backend\/embedfs\/(?:dist|build\/dist|legacy)(?:\/|$)/.test(name);
const markdown = name => /\.md$/i.test(name);
function nativeProvenanceInput(name) {
  const base = path.posix.basename(name);
  // Conservative superset of contentrails/rail.go runtimePaths: retain tests
  // too, and every JSON member beneath any contentrails/sources directory.
  return base.endsWith(".go") || ["go.mod", "go.sum", "rules_unicode15.json", "provenance.json", "rules_provenance.json", "bundled.json"].includes(base)
    || name.includes("/contentrails/sources/") && name.endsWith(".json");
}
const nativeAuditInput = name => /^(?:go-backend|shared-go)\//.test(name)
  && (name.endsWith(".go") || ["go.mod", "go.sum"].includes(path.posix.basename(name)));
function included(name) {
  return !excluded(name) && (!generated(name) || nativeProvenanceInput(name) || markdown(name))
    && (!name.startsWith("frontend/") || frontendInputs.has(name) || markdown(name));
}

// Pure fixture seam: no synthetic fixture writes a gate receipt or source tree.
export function digestNativeInputs(entries) {
  const files = [], seen = new Set();
  for (const entry of entries) {
    const name = relative(entry.path);
    if (!included(name)) continue;
    demand(!seen.has(name), "duplicate native input"); seen.add(name);
    demand(entry.type === undefined || entry.type === "file", "nonregular native input");
    demand(Number.isInteger(entry.mode) && entry.mode >= 0 && (typeof entry.bytes === "string" || Buffer.isBuffer(entry.bytes)), "invalid native input");
    files.push({ path: name, mode: entry.mode & 0o777, sha256: hash(entry.bytes) });
  }
  files.sort((a, b) => a.path < b.path ? -1 : a.path > b.path ? 1 : 0);
  demand(files.length > 0, "empty native input set");
  const audited = files.filter((file) => nativeAuditInput(file.path));
  return { digest: hash(JSON.stringify(files)), files, native_audit_sha256: hash(JSON.stringify(audited)), native_audit_count: audited.length };
}

export function inputKey(root) {
  demand(path.isAbsolute(root) && path.resolve(root) === root && fs.realpathSync(root) === root, "canonical native input root required");
  const entries = [];
  function walk(directory, prefix = "") {
    for (const entry of fs.readdirSync(directory, { withFileTypes: true }).sort((a, b) => a.name.localeCompare(b.name))) {
      const name = prefix ? `${prefix}/${entry.name}` : entry.name;
      if (excluded(name)) continue;
      relative(name);
      const file = path.join(root, name), before = fs.lstatSync(file, { bigint: true });
      demand(!before.isSymbolicLink(), "symlinked native input");
      if (before.isDirectory()) { walk(file, name); continue; }
      demand(before.isFile(), "nonregular native input");
      if (!included(name)) continue;
      demand(fs.realpathSync(file) === file, "symlinked native input ancestor");
      const fd = fs.openSync(file, fs.constants.O_RDONLY | fs.constants.O_NOFOLLOW | fs.constants.O_NONBLOCK);
      try {
        const opened = fs.fstatSync(fd, { bigint: true });
        demand(opened.isFile() && opened.ino === before.ino && opened.dev === before.dev, "native input changed before opening");
        const bytes = fs.readFileSync(fd), after = fs.fstatSync(fd, { bigint: true }), named = fs.lstatSync(file, { bigint: true });
        demand(fs.realpathSync(file) === file && named.isFile() && !named.isSymbolicLink() && named.ino === opened.ino && named.dev === opened.dev
          && after.ino === before.ino && after.dev === before.dev && before.mode === after.mode && before.size === after.size
          && before.mtimeNs === after.mtimeNs && after.size === BigInt(bytes.length), "native input changed while reading");
        entries.push({ path: name, mode: Number(before.mode), bytes });
      } finally { fs.closeSync(fd); }
    }
  }
  walk(root);
  return digestNativeInputs(entries);
}

// go list -json is a stream of pretty-printed objects, not JSON lines.
export function parseGoPackageStream(raw) {
  const text = String(raw), records = [];
  let start = -1, depth = 0, quoted = false, escaped = false;
  for (let index = 0; index < text.length; index++) {
    const char = text[index];
    if (start < 0) {
      if (/\s/.test(char)) continue;
      demand(char === "{", "invalid Go package stream"); start = index; depth = 1; continue;
    }
    if (quoted) {
      if (escaped) escaped = false;
      else if (char === "\\") escaped = true;
      else if (char === '"') quoted = false;
    } else if (char === '"') quoted = true;
    else if (char === "{") depth++;
    else if (char === "}" && --depth === 0) { records.push(JSON.parse(text.slice(start, index + 1))); start = -1; }
  }
  demand(start === -1 && records.length > 0, "incomplete or empty Go package stream");
  return records;
}
function strings(value = [], repeatedImports = false) {
  demand(Array.isArray(value) && value.every((item) => typeof item === "string" && item.length > 0 && !/[\x00-\x1f]/.test(item))
    && (repeatedImports || new Set(value).size === value.length), "invalid package graph list");
  // Go test variants concatenate test imports and normal imports, so Imports
  // can repeat a package. The dependency closure is the complete set of both.
  return [...new Set(value)].sort();
}
function moduleIdentity(value) {
  if (value === undefined) return null;
  demand(value && typeof value === "object" && typeof value.Path === "string" && !value.Error, "invalid package module");
  return { path: value.Path, version: value.Version ?? "", sum: value.Sum ?? "", go: value.GoVersion ?? "", main: value.Main === true,
    replace: value.Replace === undefined ? null : moduleIdentity(value.Replace) };
}
export function classifyGoPackages(raw, input) {
  const originals = parseGoPackageStream(raw), byName = new Map();
  for (const value of originals) {
    demand(typeof value.ImportPath === "string" && value.ImportPath.length > 0 && !/[\x00-\x1f]/.test(value.ImportPath)
      && !byName.has(value.ImportPath) && !value.Error && !value.Incomplete && !value.DepsErrors?.length, "invalid/incomplete or duplicate Go package");
    const maps = value.ImportMap ?? {};
    demand(maps && typeof maps === "object" && !Array.isArray(maps) && Object.values(maps).every((item) => typeof item === "string"), "invalid import map");
    byName.set(value.ImportPath, { ImportPath: value.ImportPath, ForTest: value.ForTest ?? "", Match: strings(value.Match),
      Imports: strings(value.Imports, true), Deps: strings(value.Deps), TestImports: strings(value.TestImports), XTestImports: strings(value.XTestImports),
      TestGoFiles: strings(value.TestGoFiles), XTestGoFiles: strings(value.XTestGoFiles),
      ImportMap: Object.fromEntries(Object.entries(maps).sort(([a], [b]) => a < b ? -1 : a > b ? 1 : 0)), Module: moduleIdentity(value.Module) });
  }
  const roots = [...byName.values()].filter((value) => value.Match.includes("./...") && !value.ForTest && !value.ImportPath.endsWith(".test")
    && !value.ImportPath.includes(" [")).map((value) => value.ImportPath).sort();
  demand(roots.length > 0 && roots.every((name) => name === MODULE || name.startsWith(`${MODULE}/`)) && byName.has(EMBED), "missing native roots or embed package");
  for (const record of byName.values()) {
    demand(typeof record.ForTest === "string", "invalid test package owner");
    for (const name of [...record.Imports, ...record.Deps]) demand(name === "C" || byName.has(name), `incomplete Go dependency graph: ${name}`);
  }
  const audit = { policy: NATIVE_REUSE_POLICY, expected_sha256: AUDITED_NATIVE_SOURCE.sha256, expected_count: AUDITED_NATIVE_SOURCE.count,
    actual_sha256: input?.native_audit_sha256 ?? null, actual_count: input?.native_audit_count ?? null,
    matched: input?.native_audit_sha256 === AUDITED_NATIVE_SOURCE.sha256 && input?.native_audit_count === AUDITED_NATIVE_SOURCE.count };
  const freshPackages = [], reusablePackages = [], historicalSourcePackages = [];
  for (const name of roots) {
    const original = byName.get(name), hasTests = original.TestGoFiles.length + original.XTestGoFiles.length > 0;
    const testRoots = [...byName.values()].filter((item) => item.ImportPath === name || item.ForTest === name || item.ImportPath === `${name}.test`);
    if (hasTests) demand(byName.has(`${name}.test`), "test executable missing from package graph");
    const closure = new Set(), pending = testRoots.map((item) => item.ImportPath);
    while (pending.length) {
      const next = pending.pop(); if (closure.has(next) || next === "C") continue;
      closure.add(next);
      const item = byName.get(next); demand(item, "package closure is incomplete");
      pending.push(...item.Imports, ...item.Deps);
    }
    // No-test packages and opt-in PostgreSQL tests stay fresh. Reused packages
    // must have actual run/pass evidence, with no skipped assertion.
    const reachesEmbed = [...closure].some((dependency) => dependency === EMBED || dependency.startsWith(`${EMBED} [`));
    // The sole audited exception calls game JSON APIs without observing GUI
    // bytes. The exact native audit pin guards that interpretation; all API,
    // content, HTML and build-identity contracts still execute whole packages.
    const historicalSource = audit.matched && name === CONTENT_RAILS && hasTests;
    const fresh = !audit.matched || !hasTests || ALWAYS_FRESH.has(name) || reachesEmbed && !historicalSource;
    (fresh ? freshPackages : reusablePackages).push(name);
    if (historicalSource && !fresh) historicalSourcePackages.push(name);
  }
  const records = [...byName.values()].sort((a, b) => a.ImportPath < b.ImportPath ? -1 : a.ImportPath > b.ImportPath ? 1 : 0);
  return { digest: hash(JSON.stringify(records)), raw_sha256: hash(raw), audit, roots, freshPackages, reusablePackages, historicalSourcePackages, records };
}

function graphSummary(graph) {
  return { digest: graph.digest, raw_sha256: graph.raw_sha256, audit: graph.audit, roots: graph.roots, freshPackages: graph.freshPackages,
    reusablePackages: graph.reusablePackages, historicalSourcePackages: graph.historicalSourcePackages };
}
export function createNativeProof({ input, graph, context }) {
  demand(HEX.test(input?.digest) && Array.isArray(input.files) && input.files.length > 0 && HEX.test(graph?.digest)
    && HEX.test(input.native_audit_sha256) && Number.isInteger(input.native_audit_count) && input.native_audit_count >= 0
    && graph.audit?.actual_sha256 === input.native_audit_sha256 && graph.audit.actual_count === input.native_audit_count
    && SHA.test(context?.sha) && HEX.test(context.tree_sha256) && /^sha256:[a-f0-9]{64}$/.test(context.toolchain_digest), "incomplete native input proof");
  return { schema: 1, policy: NATIVE_REUSE_POLICY, sha: context.sha, tree_sha256: context.tree_sha256,
    toolchain_digest: context.toolchain_digest, input_sha256: input.digest, input_count: input.files.length,
    native_audit_sha256: input.native_audit_sha256, native_audit_count: input.native_audit_count,
    graph: graphSummary(graph), command: { executable: "go", args_sha256: hash(JSON.stringify(BACKEND_RACE_ARGS)), cwd: "go-backend", CGO_ENABLED: "1" } };
}

export function validateNativeReuse({ proof, current, graphOutput, raceOutput }) {
  demand(proof?.schema === 1 && proof.policy === NATIVE_REUSE_POLICY && current?.policy === NATIVE_REUSE_POLICY && current.schema === 1 && SHA.test(proof.sha) && HEX.test(proof.tree_sha256)
    && proof.toolchain_digest === current.toolchain_digest && /^sha256:[a-f0-9]{64}$/.test(proof.toolchain_digest)
    && HEX.test(proof.input_sha256) && proof.input_sha256 === current.input_sha256 && proof.input_count === current.input_count
    && Number.isInteger(proof.input_count) && proof.input_count > 0, "native input/toolchain identity differs");
  demand([proof, current].every((value) => value.native_audit_sha256 === AUDITED_NATIVE_SOURCE.sha256
    && value.native_audit_count === AUDITED_NATIVE_SOURCE.count), "native semantic audit differs; original complete race is required");
  const recipe = { executable: "go", args_sha256: hash(JSON.stringify(BACKEND_RACE_ARGS)), cwd: "go-backend", CGO_ENABLED: "1" };
  demand(equal(proof.command, recipe) && equal(current.command, recipe), "original race recipe differs");
  const graph = classifyGoPackages(graphOutput, proof);
  demand(equal(proof.graph, graphSummary(graph)) && proof.graph.digest === current.graph?.digest
    && ["audit", "roots", "freshPackages", "reusablePackages", "historicalSourcePackages"].every((key) => equal(proof.graph[key], current.graph[key]))
    && graph.reusablePackages.length > 0, "native test graph differs or has no reusable roots");
  const roots = new Set(graph.roots), reusable = new Set(graph.reusablePackages);
  const states = new Map(graph.roots.map((name) => [name, { started: false, finished: false, tests: new Map(), noTests: false }]));
  const lines = String(raceOutput).split("\n").filter((line) => line.trim());
  demand(lines.length > 0, "empty original race output");
  for (const line of lines) {
    const event = JSON.parse(line);
    demand(event && roots.has(event.Package) && typeof event.Action === "string", "unexpected original race package/event");
    const state = states.get(event.Package), action = event.Action, test = event.Test;
    demand(action !== "fail" && action !== "build-fail", "failed original race event");
    if (test !== undefined) {
      demand(typeof test === "string" && test.length > 0 && state.started && !state.finished, "test outside active package");
      const previous = state.tests.get(test);
      if (action === "run") { demand(!previous, "duplicate test execution"); state.tests.set(test, "running"); }
      else if (action === "pass" || action === "skip") {
        demand(previous === "running" && (action === "pass" || (!reusable.has(event.Package) && PG.has(event.Package))), "incomplete or skipped reusable test");
        state.tests.set(test, action);
      } else demand(["output", "pause", "cont"].includes(action) && previous === "running", "unexpected test event");
    } else if (action === "start") { demand(!state.started, "duplicate package start"); state.started = true; }
    else if (action === "pass" || action === "skip") {
      const record = graph.records.find((item) => item.ImportPath === event.Package);
      demand(state.started && !state.finished && [...state.tests.values()].every((status) => status === "pass" || status === "skip")
        && (action === "pass" || (!reusable.has(event.Package) && record.TestGoFiles.length + record.XTestGoFiles.length === 0 && state.noTests)), "incomplete or skipped package");
      demand(!reusable.has(event.Package) || state.tests.size > 0, "reusable package has no executed tests");
      state.finished = true;
    } else {
      demand(action === "output" && state.started && !state.finished && typeof event.Output === "string", "unexpected package event");
      if (event.Output.includes("[no test files]")) state.noTests = true;
      demand(!/\(cached\)/.test(event.Output), "cached original race output");
    }
  }
  demand([...states.values()].every((state) => state.started && state.finished), "missing original race package completion");
  return { status: "hit", policy: NATIVE_REUSE_POLICY, source_sha: proof.sha, input_sha256: proof.input_sha256, graph_sha256: graph.digest,
    native_audit: graph.audit, race_stdout_sha256: hash(raceOutput), freshPackages: graph.freshPackages,
    reusablePackages: graph.reusablePackages, historicalSourcePackages: graph.historicalSourcePackages };
}

function writeArtifact(root, name, bytes) {
  demand(fs.realpathSync(root) === root, "canonical graph artifact root required");
  let cursor = root;
  for (const part of relative(name).split("/").slice(0, -1)) {
    cursor = path.join(cursor, part);
    try { fs.mkdirSync(cursor); } catch (error) { if (error.code !== "EEXIST") throw error; }
    const stat = fs.lstatSync(cursor); demand(stat.isDirectory() && !stat.isSymbolicLink(), "unsafe graph artifact directory");
  }
  const file = path.join(root, name);
  demand(fs.realpathSync(path.dirname(file)) === path.dirname(file), "symlinked graph artifact ancestor");
  const fd = fs.openSync(file, fs.constants.O_WRONLY | fs.constants.O_CREAT | fs.constants.O_EXCL | fs.constants.O_NOFOLLOW, 0o644);
  try { fs.writeFileSync(fd, bytes); } finally { fs.closeSync(fd); }
}
function graphCommand(target) {
  demand(["unit", "full"].includes(target), "native graph target must be unit or full");
  const root = process.cwd(), prefix = `.gate/${target}/native-reuse`, started = Date.now();
  const result = spawnSync("go", NATIVE_GRAPH_ARGS, { cwd: path.join(root, "go-backend"), env: { ...process.env, CGO_ENABLED: "1" }, encoding: "utf8", maxBuffer: 64 * 1024 * 1024 });
  const stdout = result.stdout ?? "", stderr = result.stderr ?? "";
  writeArtifact(root, `${prefix}/graph.stdout.json`, stdout);
  writeArtifact(root, `${prefix}/graph.stderr.log`, stderr);
  writeArtifact(root, `${prefix}/graph-command.json`, JSON.stringify({ schema: 1, command: "go", args: NATIVE_GRAPH_ARGS, cwd: "go-backend", CGO_ENABLED: "1",
    exit_code: result.status, duration_ms: Date.now() - started, stdout_sha256: hash(stdout), stderr_sha256: hash(stderr) }, null, 2) + "\n");
  demand(!result.error && result.status === 0, "actual Go test dependency discovery failed");
  const graph = classifyGoPackages(stdout, inputKey(root)), bytes = JSON.stringify(graph) + "\n", name = `${prefix}/graph.json`;
  writeArtifact(root, name, bytes);
  process.stdout.write(JSON.stringify({ schema: 1, path: name, sha256: hash(bytes), digest: graph.digest,
    audit: graph.audit, freshPackages: graph.freshPackages, reusablePackages: graph.reusablePackages,
    historicalSourcePackages: graph.historicalSourcePackages }) + "\n");
}
if (process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href) {
  try { demand(process.argv.length === 4 && process.argv[2] === "graph", "usage: node scripts/gui-native-reuse.mjs graph <unit|full>"); graphCommand(process.argv[3]); }
  catch (error) { process.stderr.write(String(error?.message ?? error) + "\n"); process.exitCode = 1; }
}
