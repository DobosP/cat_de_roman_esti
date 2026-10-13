import test from "node:test";
import assert from "node:assert/strict";
import { digestNativeInputs, parseGoPackageStream, classifyGoPackages, createNativeProof, validateNativeReuse,
  BACKEND_RACE_ARGS, NATIVE_GRAPH_ARGS } from "../../scripts/gui-native-reuse.mjs";

// Synthetic in-memory parser/security fixtures only; no gate evidence is emitted.
const module = "github.com/DobosP/cat_de_roman_esti/go-backend";
const embed = `${module}/embedfs`, plain = `${module}/internal/plain`, ui = `${module}/internal/ui`;
const external = `${module}/internal/external`, accounts = `${module}/internal/accounts`;
const context = { sha: "a".repeat(40), tree_sha256: "b".repeat(64), toolchain_digest: `sha256:${"c".repeat(64)}` };
function inputs() {
  return ["go-backend/source.go", "docs/content/evidence.json", "scripts/check.sh", "kit/recipe.json", "legacy/archive.tar", "content/source.json",
    "frontend/package.json", "frontend/package-lock.json", "frontend/src/release.ts", "frontend/e2e/seeded-starts.json",
    "frontend/src/ui.tsx", "go-backend/embedfs/dist/index.html", "go-backend/embedfs/build/dist/id.json", "go-backend/embedfs/legacy/index.html"]
    .map((path) => ({ path, mode: 0o644, bytes: path }));
}
function packages() {
  const records = [{ ImportPath: embed, Match: ["./..."] }];
  for (const name of [plain, ui, external, accounts]) {
    const deps = name === ui ? [embed] : [];
    records.push({ ImportPath: name, Match: ["./..."], TestGoFiles: ["source_test.go"], Imports: deps, Deps: deps });
    records.push({ ImportPath: `${name} [${name}.test]`, ForTest: name, Imports: deps, Deps: deps });
    records.push({ ImportPath: `${name}.test`, Imports: [`${name} [${name}.test]`], Deps: [`${name} [${name}.test]`, ...deps] });
  }
  records.push({ ImportPath: `${external}_test [${external}.test]`, ForTest: external, Imports: [embed], Deps: [embed] });
  return records;
}
const stream = (records) => records.map((value) => JSON.stringify(value, null, 2)).join("\n\n") + "\n";
function raceEvents(graph) {
  return graph.roots.flatMap((name) => name === embed ? [
    { Action: "start", Package: name }, { Action: "output", Package: name, Output: `? ${name} [no test files]\n` }, { Action: "skip", Package: name },
  ] : [
    { Action: "start", Package: name }, { Action: "run", Package: name, Test: "TestContract" },
    { Action: name === accounts ? "skip" : "pass", Package: name, Test: "TestContract" }, { Action: "pass", Package: name },
  ]);
}
function fixture() {
  const graphOutput = stream(packages()), graph = classifyGoPackages(graphOutput);
  const proof = createNativeProof({ input: digestNativeInputs(inputs()), graph, context });
  const current = createNativeProof({ input: digestNativeInputs(inputs()), graph, context: { ...context, sha: "d".repeat(40), tree_sha256: "e".repeat(64) } });
  return { proof, current, graphOutput, raceOutput: raceEvents(graph).map((event) => JSON.stringify(event)).join("\n") };
}

void test("native key binds all docs, scripts, kit, legacy, content and exact frontend runtime reads", () => {
  const base = inputs(), key = digestNativeInputs(base).digest;
  for (const entry of base.slice(0, 10)) {
    const changed = structuredClone(base); changed.find((item) => item.path === entry.path).bytes += "changed";
    assert.notEqual(digestNativeInputs(changed).digest, key, entry.path);
  }
});
void test("native key permits frontend source changes and exactly generated embed asset subtrees", () => {
  const base = inputs(), changed = structuredClone(base);
  for (const entry of changed.slice(10)) entry.bytes += "changed";
  assert.equal(digestNativeInputs(changed).digest, digestNativeInputs(base).digest);
  for (const name of ["go-backend/embedfs/assets.go", "go-backend/embedfs/build/source.go", "go-backend/embedfs/builder/source.go", "go-backend/embedfs/legacy-source.go", "go-backend/third_party/webkit/dist/contract.go", "shared-go/authcore/dist/contract.go"]) {
    assert.notEqual(digestNativeInputs([...base, { path: name, mode: 0o644, bytes: "new" }]).digest, digestNativeInputs(base).digest);
  }
});
void test("native key includes executable mode and file additions/deletions, with deterministic ordering", () => {
  const base = inputs(), key = digestNativeInputs(base).digest;
  assert.equal(digestNativeInputs([...base].reverse()).digest, key);
  const changed = structuredClone(base); changed[0].mode = 0o755;
  assert.notEqual(digestNativeInputs(changed).digest, key);
  assert.notEqual(digestNativeInputs(base.slice(1)).digest, key);
  assert.notEqual(digestNativeInputs([...base, { path: "docs/new.md", mode: 0o644, bytes: "new" }]).digest, key);
});
void test("native key ignores only wrapper caches, metadata and secret files", () => {
  const base = inputs(), ignored = [".git/config", "frontend/node_modules/a.js", ".gate/unit/result.json", "x/.vitest/out", "x/test-results/log", "dist/file",
    "TASK_BRIEF.md", "TASK_RESULT.md", "SWARM_RESULT.md", ".env", "x/.env.production"];
  assert.equal(digestNativeInputs([...base, ...ignored.map((path) => ({ path, bytes: "ignored", mode: 0o644 }))]).digest, digestNativeInputs(base).digest);
});
void test("native key refuses nonregular, duplicate and unsafe included inputs", () => {
  for (const entry of [
    { path: "source.go", mode: 0o644, bytes: "x", type: "symlink" }, { path: "../outside", mode: 0o644, bytes: "x" },
    { path: "/absolute", mode: 0o644, bytes: "x" }, { path: "docs/../escape", mode: 0o644, bytes: "x" },
    { path: "source.go", mode: -1, bytes: "x" }, inputs()[0],
  ]) assert.throws(() => digestNativeInputs([...inputs(), entry]));
});
void test("actual command recipes bind race instrumentation and disable Go test result caching", () => {
  assert.deepEqual(NATIVE_GRAPH_ARGS, ["list", "-race", "-deps", "-test", "-json", "./..."]);
  assert.deepEqual(BACKEND_RACE_ARGS, ["test", "-race", "-timeout=30m", "-count=1", "-json", "./..."]);
});
void test("Go stream parsing handles pretty objects and escaped braces inside strings", () => {
  const values = [{ name: 'brace } \\" {' }, { second: {} }];
  assert.deepEqual(parseGoPackageStream(stream(values)), values);
});
void test("Go stream parsing refuses truncated, nonobject and trailing input", () => {
  for (const raw of ["", "{} x", "[]", '{"x":"open', '{"x":{}']) assert.throws(() => parseGoPackageStream(raw));
});
void test("graph partition includes ordinary, internal test, external test and executable closures", () => {
  const graph = classifyGoPackages(stream(packages()));
  assert.deepEqual(graph.reusablePackages, [plain]);
  assert.deepEqual(graph.freshPackages, [embed, accounts, external, ui].sort());
  const records = packages();
  records.find((item) => item.ImportPath === `${plain}.test`).Deps.push(embed);
  assert.ok(classifyGoPackages(stream(records)).freshPackages.includes(plain));
});
void test("graph closure detects an embedfs test variant with no direct ordinary embedfs dependency", () => {
  const records = packages(), variant = `${embed} [${plain}.test]`;
  records.push({ ImportPath: variant, ForTest: plain });
  records.find((item) => item.ImportPath === `${plain}.test`).Deps.push(variant);
  assert.ok(classifyGoPackages(stream(records)).freshPackages.includes(plain));
});
void test("actual Go test variants may repeat normal imports without losing dependencies", () => {
  const records = packages(), original = classifyGoPackages(stream(records));
  const variant = records.find((item) => item.ImportPath === `${ui} [${ui}.test]`);
  variant.Imports = [...variant.Imports, embed, embed];
  const repeated = classifyGoPackages(stream(records));
  assert.equal(repeated.digest, original.digest);
  assert.deepEqual(repeated.freshPackages, original.freshPackages);
  assert.deepEqual(repeated.reusablePackages, original.reusablePackages);
});
void test("graph normalization ignores object order, filesystem directories and build-cache identities", () => {
  const records = packages(), graph = classifyGoPackages(stream(records));
  for (const value of records) { value.Dir = "/different/mirror"; value.BuildID = "changed"; value.EmbedFiles = ["different-asset.js"]; }
  assert.equal(classifyGoPackages(stream(records.reverse())).digest, graph.digest);
});
void test("graph refuses missing roots, variants, dependencies, duplicates and Go errors", () => {
  const mutations = [
    (r) => r.forEach((item) => { delete item.Match; }),
    (r) => r.splice(r.findIndex((item) => item.ImportPath === `${plain}.test`), 1),
    (r) => r.find((item) => item.ImportPath === plain).Deps.push("missing/dependency"),
    (r) => r.push(structuredClone(r[0])),
    (r) => { r[0].Error = { Err: "failed" }; },
    (r) => { r[0].Incomplete = true; },
    (r) => { r[0].DepsErrors = [{ Err: "failed" }]; },
  ];
  for (const mutate of mutations) { const records = packages(); mutate(records); assert.throws(() => classifyGoPackages(stream(records))); }
});
void test("native reuse accepts a completed original race for identical inputs across frontend SHAs", () => {
  const result = validateNativeReuse(fixture());
  assert.equal(result.status, "hit"); assert.deepEqual(result.reusablePackages, [plain]);
});
void test("native reuse rejects changed input, toolchain, graph, raw graph and original recipe", () => {
  for (const mutate of [
    (f) => { f.current.input_sha256 = "f".repeat(64); }, (f) => { f.current.input_count++; },
    (f) => { f.current.toolchain_digest = `sha256:${"f".repeat(64)}`; }, (f) => { f.current.graph.digest = "f".repeat(64); },
    (f) => { f.proof.graph.reusablePackages.push(ui); }, (f) => { f.graphOutput += "\n"; },
    (f) => { f.proof.command.args_sha256 = "f".repeat(64); }, (f) => { f.proof.command.CGO_ENABLED = "0"; },
  ]) { const value = fixture(); mutate(value); assert.throws(() => validateNativeReuse(value)); }
});
void test("native reuse rejects failed/skipped/incomplete/duplicate/cached/missing original test evidence", () => {
  for (const mutate of [
    (events) => { events.find((e) => e.Package === plain && e.Test && e.Action === "pass").Action = "fail"; },
    (events) => { events.find((e) => e.Package === plain && e.Test && e.Action === "pass").Action = "skip"; },
    (events) => events.splice(events.findIndex((e) => e.Package === plain && e.Test && e.Action === "pass"), 1),
    (events) => events.splice(events.findIndex((e) => e.Package === plain && !e.Test && e.Action === "pass"), 1),
    (events) => events.push({ Action: "pass", Package: plain }),
    (events) => events.splice(events.findIndex((e) => e.Package === plain && !e.Test && e.Action === "pass"), 0, { Action: "output", Package: plain, Output: "ok plain (cached)\n" }),
    (events) => events.push({ Action: "start", Package: `${module}/unknown` }),
    (events) => { for (let n = events.length - 1; n >= 0; n--) if (events[n].Package === plain && events[n].Test) events.splice(n, 1); },
  ]) {
    const value = fixture(), events = value.raceOutput.split("\n").map((line) => JSON.parse(line)); mutate(events);
    value.raceOutput = events.map((event) => JSON.stringify(event)).join("\n"); assert.throws(() => validateNativeReuse(value));
  }
});
void test("native reuse refuses missing no-test marker and skipped assertions outside explicit fresh PG roots", () => {
  for (const packageName of [embed, ui]) {
    const value = fixture(), events = value.raceOutput.split("\n").map((line) => JSON.parse(line));
    if (packageName === embed) events.find((e) => e.Package === embed && e.Action === "output").Output = "unknown skip";
    else events.find((e) => e.Package === ui && e.Test && e.Action === "pass").Action = "skip";
    value.raceOutput = events.map((event) => JSON.stringify(event)).join("\n"); assert.throws(() => validateNativeReuse(value));
  }
});
