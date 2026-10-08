import assert from "node:assert/strict";
import { createHash, randomUUID } from "node:crypto";
import * as fs from "node:fs";
import path from "node:path";
import test from "node:test";
import ts from "@typescript/typescript6";
import {
  ORIGINAL_OWNERS, bindSourceInput, absolutePath, repoRelative, applyEdits, extractRendererUnitless,
  extractUnitlessPolicy, analyzeStyles, publishStylePlan, nativeDiagnosticResult,
} from "../../scripts/gui-style-plan.mjs";

// This lane exercises parser/checker/planner decisions with narrow virtual JSX
// declarations. It does not render React, run the SDK hook, or prove DOM/CSSOM,
// ref delivery, Motion frames, gates, or an actual full-product conversion.
const fixtures = JSON.parse(fs.readFileSync(new URL("fixtures/gui-style-plan.json", import.meta.url), "utf8"));
const policy = fs.readFileSync(new URL("../src/components/cssUnits.ts", import.meta.url));
const unitless = extractUnitlessPolicy(policy);
const sha = (bytes) => createHash("sha256").update(bytes).digest("hex");
const ambient = `
interface FixtureCss {
  gap?: string | number; marginTop?: string | number; width?: string | number;
  color?: string; opacity?: string | number; columnCount?: string | number;
  [name: \`--\${string}\`]: string | number | undefined;
}
interface FixtureProps {
  style?: FixtureCss; css?: FixtureCss; className?: string; id?: string;
  ref?: (node: unknown) => void; disabled?: boolean; 'aria-label'?: string;
  initial?: { opacity?: number; scale?: number }; animate?: { opacity?: number };
  exit?: { opacity?: number }; onClick?: () => void; children?: unknown;
}
declare namespace JSX {
  interface Element {}
  interface IntrinsicElements {
    div: FixtureProps; button: FixtureProps; aside: FixtureProps;
  }
}
declare module 'react' { export interface CSSProperties extends FixtureCss {} }
declare module 'framer-motion' {
  export const m: { button: (props: FixtureProps) => JSX.Element; div: (props: FixtureProps) => JSX.Element };
}
declare module '@roedu/ui' { export const Button: (props: FixtureProps) => JSX.Element; }
`;
const adapter = `
export declare const Csp: { div: (props: FixtureProps) => JSX.Element; button: (props: FixtureProps) => JSX.Element };
export declare const CspMotion: { div: (props: FixtureProps) => JSX.Element; button: (props: FixtureProps) => JSX.Element };
export declare const CspButton: (props: FixtureProps) => JSX.Element;
export declare function cssLength(value: string | number | undefined): string | undefined;
`;
const owners = {
  "frontend/src/screens/Alchimie.tsx": `
import { m } from 'framer-motion';
export function Alchimie({ item }: { item: { depleted: boolean } }) {
  const attach = (node: unknown) => { void node; };
  return <><m.div /><m.button ref={attach} initial={{ opacity: 0, scale: 0.4 }} animate={{ opacity: 1 }} onClick={() => {}} disabled={item.depleted} aria-label="inventory" className="inventory-token" style={{ gap: 4, opacity: item.depleted ? 0.5 : 1 }}>cue</m.button></>;
}
`,
  "frontend/src/screens/Conexiuni.tsx": `
import { m } from 'framer-motion';
export function Conexiuni({ actionsLocked, isSel }: { actionsLocked: boolean; isSel: boolean }) {
  const attach = (node: unknown) => { void node; };
  return <><m.div /><m.button ref={attach} initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={() => {}} disabled={actionsLocked} aria-label="connection" className="word-tile" style={{ opacity: actionsLocked && !isSel ? 0.55 : 1, gap: 4 }}>cue</m.button></>;
}
`,
};
function analyze(body, { root = "/virtual-cat", changes = {}, omit = [], candidateCaseAliases = false, authoritativeDiagnostics, diagnoseCandidate } = {}) {
  const all = {
    "frontend/src/fixture-types.d.ts": ambient,
    "frontend/src/components/CspStyle.ts": adapter,
    ...owners,
    "frontend/src/screens/Fixture.tsx": body,
    ...changes,
  };
  for (const name of omit) delete all[name];
  const files = new Map(Object.entries(all).map(([name, text]) => [absolutePath(`${root}/${name}`), text]));
  const directories = new Set();
  for (const name of files.keys()) { let current = name; while (current.includes("/")) { current = current.slice(0, current.lastIndexOf("/")); if (directories.has(current)) break; directories.add(current || "/"); } }
  const options = { target: ts.ScriptTarget.ESNext, module: ts.ModuleKind.ESNext,
    moduleResolution: ts.ModuleResolutionKind.Bundler, jsx: ts.JsxEmit.Preserve,
    strict: true, noUnusedLocals: true, noUnusedParameters: true, noEmit: true,
    types: [], lib: ["lib.esnext.d.ts"], skipLibCheck: false };
  let hostCount = 0;
  function makeHost(compilerOptions) {
    hostCount += 1;
    const host = ts.createCompilerHost(compilerOptions, true), read = host.readFile.bind(host), get = host.getSourceFile.bind(host), exists = host.fileExists.bind(host), dir = host.directoryExists.bind(host);
    const aliases = candidateCaseAliases && hostCount > 1;
    const key = (name) => { const value = absolutePath(path.isAbsolute(name) || /^[A-Za-z]:[\\/]/.test(name) ? name : path.resolve(name)); return aliases ? value.toLowerCase() : value; };
    const virtual = new Map([...files].map(([name, text]) => [key(name), text]));
    const virtualDirectories = new Set([...directories].map(key));
    host.readFile = (name) => virtual.get(key(name)) ?? read(name);
    host.fileExists = (name) => virtual.has(key(name)) || exists(name);
    host.directoryExists = (name) => virtualDirectories.has(key(name)) || dir(name);
    host.getSourceFile = (name, language, onError, fresh) => virtual.has(key(name)) ? ts.createSourceFile(name, virtual.get(key(name)), language, true) : get(name, language, onError, fresh);
    if (aliases) {
      // Real Windows hosts canonicalize case. Force alternate casing into the
      // overlay lookup on any native future test host to exercise that contract.
      host.getCanonicalFileName = (name) => name.toLowerCase();
      host.useCaseSensitiveFileNames = () => false;
      const aliasGet = host.getSourceFile.bind(host);
      Object.defineProperty(host, "getSourceFile", {
        configurable: true, get: () => aliasGet,
        set: (overlay) => { Object.defineProperty(host, "getSourceFile", { configurable: true, writable: true, value: (name, ...args) => overlay(virtual.has(key(name)) ? name.toUpperCase() : name, ...args) }); },
      });
    }
    return host;
  }
  const program = ts.createProgram({ rootNames: [...files.keys()], options, host: makeHost(options) });
  return analyzeStyles(program, { root, unitless, makeHost, authoritativeDiagnostics, diagnoseCandidate, readBytes: (file) => Buffer.from(files.get(absolutePath(file))) });
}
const textOf = (plan, file = "frontend/src/screens/Fixture.tsx") => plan.files.find((item) => item.file === file)?.text;
const assertFailed = (plan) => {
  assert.equal(plan.status, "fail"); assert.equal(plan.application_ready, false);
  assert.deepEqual(plan.files, []);
  assert.ok(plan.diagnostics.length || plan.candidate_diagnostics.length || plan.manual.length, "Failure must retain an actionable reason");
};

void test("repeated source reads cannot replace a previously checked provenance binding", () => {
  const inputs = {}, original = Buffer.from("original-owner");
  assert.equal(bindSourceInput(inputs, "frontend/src/screens/Alchimie.tsx", original), original);
  const record = inputs["frontend/src/screens/Alchimie.tsx"];
  bindSourceInput(inputs, "frontend/src/screens/Alchimie.tsx", Buffer.from("original-owner"));
  assert.equal(inputs["frontend/src/screens/Alchimie.tsx"], record);
  assert.throws(() => bindSourceInput(inputs, "frontend/src/screens/Alchimie.tsx", Buffer.from("changed--owner")), /Repeated source input changed/);
  assert.throws(() => bindSourceInput(inputs, "frontend/src/screens/Alchimie.tsx", Buffer.from("different-length")), /Repeated source input changed/);
  assert.deepEqual(record, { sha256: sha(original), bytes: original.length });
});

void test("native CLI diagnostic data retains failures and refuses launch or unexplained-success shapes", () => {
  // Pure data controls; no command is run and no synthetic native receipt is earned.
  assert.deepEqual(nativeDiagnosticResult({ status: 0, stdout: "", stderr: "" }), []);
  const message = "src/fixture.tsx(1,1): error TS2322: incompatible value\n";
  assert.deepEqual(nativeDiagnosticResult({ status: 1, stdout: message, stderr: "" }), [{ code: "native-tsc-exit", category: "Error", compiler: "typescript@7.0.2 native CLI", exit_code: 1, message }]);
  for (const child of [{ status: null, error: Error("launch") }, { status: 0, error: Error("launch") }, { status: 0, signal: "SIGTERM" }, { status: 0, stdout: message }, { status: 1, stdout: "" }]) assert.throws(() => nativeDiagnosticResult(child));
});
void test("authoritative before diagnostics stop source proposals before any candidate check", () => {
  const failure = [{ code: "native-tsc-exit", message: "DATA ONLY native before refusal" }];
  const plan = analyze('export const View = () => <div style={{ gap: 4 }} />;', { authoritativeDiagnostics: failure, diagnoseCandidate: () => assert.fail("Refused before check reached candidate") });
  assertFailed(plan); assert.deepEqual(plan.diagnostics, failure); assert.deepEqual(plan.sites, []);
});
void test("authoritative candidate diagnostics revoke every proposal while retaining causal inputs", () => {
  let observed;
  const failure = [{ code: "native-tsc-exit", message: "DATA ONLY native candidate refusal" }];
  const plan = analyze('export const View = () => <div style={{ gap: 4 }} />;', { authoritativeDiagnostics: [], diagnoseCandidate: (files) => { observed = files; return failure; } });
  assertFailed(plan); assert.deepEqual(plan.diagnostics, []); assert.deepEqual(plan.candidate_diagnostics, failure);
  assert.ok(observed.length === 3 && observed.every((file) => file.before_sha256 && file.after_sha256 && file.text));
  assert.ok(plan.proposals.length === 3 && plan.owners.length === 2);
});

void test("paths normalize both separators and confine whole segments", () => {
  assert.equal(repoRelative("C:\\work\\cat", "C:\\work\\cat\\frontend\\src\\Cue.tsx"), "frontend/src/Cue.tsx");
  assert.equal(repoRelative("C:/work/cat", "C:/work/cat/frontend/src/../src/Cue.tsx"), "frontend/src/Cue.tsx");
  assert.equal(repoRelative("/work/cat", "/work/cat/frontend/src/Cue.tsx"), "frontend/src/Cue.tsx");
  assert.equal(repoRelative("C:/work/cat", "frontend\\src\\Cue.tsx"), "frontend/src/Cue.tsx");
  assert.equal(repoRelative("/work/cat", "frontend/src/Cue.tsx"), "frontend/src/Cue.tsx");
  for (const [root, file] of [["/work/cat", "/work/cat-other/a"], ["C:/work/cat", "C:/work/cat-other/a"], ["C:/work/cat", "D:/work/cat/a"], ["/work/cat", "/work/cat/../a"]]) assert.throws(() => repoRelative(root, file));
  for (const file of ["relative/path", "C:relative", "//server/share/file", "C:/file\0"]) assert.throws(() => absolutePath(file));
  assert.throws(() => repoRelative("C:/work/cat", "C:relative"));
});
void test("actual parser accepts only the pinned71 declaration or assignment form", () => {
  const literal = JSON.stringify(unitless.join(" "));
  for (const code of [`const unitlessNumbers = new Set(${literal}.split(" "));`, `unitlessNumbers = new Set(${literal}.split(" "));`]) assert.deepEqual(extractRendererUnitless(Buffer.from(code)), unitless);
  assert.equal(unitless.length, 71); assert.ok(unitless.includes("WebKitBoxFlexGroup"));
  for (const code of [
    `const unitlessNumbers = new Set(dynamic);`, `const unitlessNumbers = new Set(${literal}.split(","));`,
    `const unitlessNumbers = new Set(${literal}.split(" ")); unitlessNumbers = new Set(${literal}.split(" "));`,
    `unitlessNumbers += new Set(${literal}.split(" "));`, `const unitlessNumbers = new Set("opacity".split(" "));`,
    `const unitlessNumbers =`,
  ]) assert.throws(() => extractRendererUnitless(Buffer.from(code)));
  const duplicate = [...unitless]; duplicate[1] = duplicate[0];
  assert.throws(() => extractRendererUnitless(Buffer.from(`const unitlessNumbers = new Set(${JSON.stringify(duplicate.join(" "))}.split(" "));`)));
  assert.throws(() => extractUnitlessPolicy(Buffer.from('const UNITLESS_PROPERTIES = ["opacity"] as const;')));
});
void test("edit ranges are validated before any transformed text is returned", () => {
  assert.equal(applyEdits("abcd", [{ start: 1, end: 3, value: "x" }]), "axd");
  assert.equal(applyEdits("abcd", [{ start: 0, end: 0, value: "!" }, { start: 0, end: 1, value: "A" }]), "!Abcd");
  for (const edits of [ [{ start: -1, end: 1, value: "x" }], [{ start: 0, end: 5, value: "x" }], [{ start: 0, end: 2, value: "x" }, { start: 1, end: 3, value: "y" }], [{ start: 1, end: 1, value: "x" }, { start: 1, end: 1, value: "y" }] ]) assert.throws(() => applyEdits("abcd", edits));
});
for (const fixture of fixtures.passing) void test(fixture.name, () => {
  const plan = analyze(fixture.body);
  assert.equal(plan.status, "pass", JSON.stringify(plan)); assert.equal(plan.application_ready, true);
  assert.deepEqual(plan.diagnostics, []); assert.deepEqual(plan.candidate_diagnostics, []);
  for (const expected of fixture.expected) assert.ok(textOf(plan).includes(expected), expected);
  for (const absent of fixture.absent ?? []) assert.ok(!textOf(plan).includes(absent), absent);
});
for (const fixture of fixtures.refusing) void test(fixture.name, () => {
  const plan = analyze(fixture.body); assertFailed(plan);
  if (fixture.candidate_diagnostics) { assert.deepEqual(plan.diagnostics, []); assert.ok(plan.candidate_diagnostics.some((item) => item.code === 6133)); }
});
void test("Windows virtual source paths produce the same repo-relative plan", () => {
  const body = "export function Fixture() { return <div style={{ width: 1 }} />; }";
  const posix = analyze(body), windows = analyze(body, { root: "C:/virtual-cat" });
  assert.equal(windows.status, "pass", JSON.stringify(windows)); assert.equal(posix.status, "pass", JSON.stringify(posix));
  assert.deepEqual(windows.files.map(({ file, text }) => ({ file, text })), posix.files.map(({ file, text }) => ({ file, text })));
});
void test("canonical case aliases still check transformed semantic bytes", () => {
  const plan = analyze("import { m } from 'framer-motion'; export function Fixture() { return <m.div style={{ width: 1 }} />; }", { candidateCaseAliases: true });
  assertFailed(plan); assert.deepEqual(plan.diagnostics, []);
  assert.ok(plan.candidate_diagnostics.some((item) => item.code === 6133), JSON.stringify(plan));
});
void test("both original Motion owners preserve every non-style/class attribute byte", () => {
  const plan = analyze("export function Fixture() { return <div style={{ width: 1 }} />; }");
  assert.equal(plan.status, "pass", JSON.stringify(plan)); assert.equal(plan.owners.length, 2);
  for (const owner of plan.owners) {
    assert.equal(owner.owner_class, ORIGINAL_OWNERS[owner.file].className);
    assert.ok(textOf(plan, owner.file).includes(owner.values.find((value) => value.key === "opacity").predicate));
    assert.ok(textOf(plan, owner.file).includes(owner.owner_class));
    for (const attribute of owner.preserved_attributes) {
      const before = ts.createSourceFile(owner.file, owners[owner.file], ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
      const after = ts.createSourceFile(owner.file, textOf(plan, owner.file), ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
      const collect = (source) => { const matches = []; function visit(node) { if (ts.isJsxAttribute(node) && node.name.text === attribute.name) matches.push(node.getText(source)); ts.forEachChild(node, visit); } visit(source); return matches; };
      assert.ok(collect(before).some((text) => sha(text) === attribute.sha256));
      assert.ok(collect(after).some((text) => sha(text) === attribute.sha256));
    }
  }
});
for (const [file, from, replacement] of [
  ["frontend/src/screens/Alchimie.tsx", "style={{ gap: 4, opacity: item.depleted ? 0.5 : 1 }}",
    "style={{\n    gap: 4,\n    opacity: item.depleted ? 0.5 : 1,\n  }}"],
  ["frontend/src/screens/Conexiuni.tsx", "style={{ opacity: actionsLocked && !isSel ? 0.55 : 1, gap: 4 }}",
    "style={{\n    opacity: actionsLocked && !isSel ? 0.55 : 1, // retain ownership note\n    gap: 4,\n  }}"],
]) void test(`Motion opacity member removal preserves adjacent text without trailing whitespace: ${file}`, () => {
  assert.ok(owners[file].includes(from));
  const plan = analyze("export function Fixture() { return <div style={{ width: 1 }} />; }", {
    changes: { [file]: owners[file].replace(from, replacement) },
  });
  assert.equal(plan.status, "pass", JSON.stringify(plan));
  const output = textOf(plan, file);
  assert.doesNotMatch(output, /[ \t]+$/m);
  assert.ok(output.includes('gap: "4px"'));
  assert.ok(output.includes(ORIGINAL_OWNERS[file].className));
  if (replacement.includes("// retain ownership note")) assert.ok(output.includes("// retain ownership note"));
});

for (const fixture of fixtures.owner_mutations) void test(fixture.name, () => {
  assert.ok(owners[fixture.file].includes(fixture.find));
  assertFailed(analyze("export function Fixture() { return <div style={{ width: 1 }} />; }", { changes: { [fixture.file]: owners[fixture.file].replace(fixture.find, fixture.replace) } }));
});
void test("missing and duplicate original owners fail the whole plan", () => {
  const body = "export function Fixture() { return <div style={{ width: 1 }} />; }";
  assertFailed(analyze(body, { omit: ["frontend/src/screens/Alchimie.tsx"] }));
  const file = "frontend/src/screens/Alchimie.tsx";
  assertFailed(analyze(body, { changes: { [file]: owners[file] + owners[file].replaceAll("Alchimie", "SecondAlchimie").replace("import { m } from 'framer-motion';", "") } }));
});
// Physical publication probes require the real owning native unit/full first.
// This does not create descriptors, change env, earn a gate, or select a tree.
// Before EVERY --fresh/mirror reset, the operator
// must preserve this entire NON-RELEASE case root AND the complete actual ROOT
// with its target/config/bootstrap/command streams and descriptors. Diagnostics
// and JSON inventories alone do not preserve physical files or literal links.
function publicationFixture(t, label, body) {
  const hex = /^[a-f0-9]{64}$/, uuid = /^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$/;
  const closed = (value, fields, optional = []) => value && typeof value === "object" && !Array.isArray(value)
    && fields.every(key => Object.hasOwn(value, key)) && Object.keys(value).every(key => fields.includes(key) || optional.includes(key));
  const literal = (name, dot = false) => {
    assert.ok(typeof name === "string" && (dot && name === "." || name && !name.startsWith("/") && !Array.from(name).some((character) => { const code = character.charCodeAt(0); return code === 92 || code === 58 || code <= 31 || code === 127; })
      && name.split("/").every(part => /^[A-Za-z0-9_@.-]+$/.test(part) && part !== "." && part !== ".."
        && !part.endsWith(".") && !/^(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\.|$)/i.test(part))), "Literal confined path required");
    return name;
  };
  assert.equal(process.platform, "linux", "Required actual native /work fixtures cannot be skipped");
  assert.equal(new URL("../../", import.meta.url).href, "file:///work/", "Owning test must be inside the real /work source");
  assert.equal(import.meta.url, "file:///work/frontend/tests/gui-style-plan.test.mjs", "Actual executing test source path required");
  assert.equal(process.cwd(), "/work/frontend", "Actual Cat npm unit/full test cwd required");
  const repository = "/work", uid = process.getuid(), repositoryStat = fs.lstatSync(repository, { bigint: true });
  for (const ancestor of ["/", repository]) {
    const stat = fs.lstatSync(ancestor);
    assert.ok(stat.isDirectory() && !stat.isSymbolicLink()); assert.equal(fs.realpathSync.native(ancestor), ancestor);
  }
  assert.equal(repositoryStat.uid, BigInt(uid), "Native mirror owner must match the actual runner uid");
  function regular(name, directory = false) {
    literal(name); let file = repository;
    const parts = name.split("/");
    for (let index = 0; index < parts.length; index++) {
      file = path.join(file, parts[index]); const stat = fs.lstatSync(file, { bigint: true });
      assert.ok(!stat.isSymbolicLink() && (index < parts.length - 1 || directory ? stat.isDirectory() : stat.isFile()), "No alias/nonregular native component");
      assert.equal(stat.dev, repositoryStat.dev, "Fixture/evidence must remain on the owning mirror device");
      assert.equal(fs.realpathSync.native(file), file);
    }
    return file;
  }
  function read(name) {
    const file = regular(name), before = fs.lstatSync(file, { bigint: true });
    assert.equal(before.nlink, 1n, "Aliased regular input refused");
    const fd = fs.openSync(file, fs.constants.O_RDONLY | fs.constants.O_NOFOLLOW);
    try {
      const opened = fs.fstatSync(fd, { bigint: true }), bytes = fs.readFileSync(fd), after = fs.lstatSync(file, { bigint: true });
      assert.ok(opened.isFile() && after.isFile() && !after.isSymbolicLink());
      for (const key of ["dev", "ino", "size", "mtimeNs", "ctimeNs", "mode", "uid", "nlink"]) {
        assert.equal(opened[key], before[key]); assert.equal(after[key], before[key]);
      }
      assert.equal(BigInt(bytes.length), before.size); regular(name); return bytes;
    } finally { fs.closeSync(fd); }
  }
  const descriptorBytes = read(".gate/wrapper-current.json"), actual = JSON.parse(descriptorBytes);
  assert.ok(closed(actual, ["schema", "invocation", "target", "sha", "tree_sha256", "toolchain_digest", "config_sha256", "config_path", "config_file_sha256"]));
  assert.equal(actual.schema, 1); assert.ok(["unit", "full"].includes(actual.target)); assert.match(actual.invocation, uuid);
  assert.match(actual.sha, /^[a-f0-9]{40}$/); assert.match(actual.tree_sha256, hex); assert.match(actual.toolchain_digest, /^sha256:[a-f0-9]{64}$/);
  assert.equal(actual.sha, process.env.GATE_SHA); assert.equal(actual.tree_sha256, process.env.GATE_TREE_SHA256);
  assert.equal(actual.toolchain_digest, process.env.TOOLCHAIN_DIGEST); assert.ok(["true", "false"].includes(process.env.GATE_DIRTY));
  assert.equal(process.env.GATE_VERSIONS_RESOLVE, "0", "Publication probes do not authorize version resolution");
  const prefix = `.gate/${actual.target}/`, primaryBytes = read(prefix + "wrapper-current.json");
  assert.deepEqual(primaryBytes, descriptorBytes); assert.equal(actual.config_path, prefix + "wrapper-kit-config.json");
  assert.match(actual.config_sha256, hex); assert.match(actual.config_file_sha256, hex);
  const configBytes = read(actual.config_path), captured = JSON.parse(configBytes);
  assert.equal(sha(configBytes), actual.config_file_sha256);
  assert.ok(closed(captured, ["schema", "target", "sha", "tree_sha256", "toolchain_digest", "config", "config_sha256", "command"]));
  for (const key of ["schema", "target", "sha", "tree_sha256", "toolchain_digest", "config_sha256"]) assert.equal(captured[key], actual[key]);
  const config = captured.config;
  assert.ok(closed(config, ["role", "app", "npm_dir", "vendor_dir", "go_dirs"], ["ui_adoption"]));
  assert.equal(config.role, "consumer"); assert.equal(config.app, "cat_de_roman_esti");
  literal(config.npm_dir); literal(config.vendor_dir); assert.ok(Array.isArray(config.go_dirs) && config.go_dirs.length && new Set(config.go_dirs).size === config.go_dirs.length);
  config.go_dirs.forEach(name => literal(name, true));
  let phase;
  if (Object.hasOwn(config, "ui_adoption")) {
    phase = config.ui_adoption; assert.ok(closed(phase, ["mode", "until", "legacy"]));
    assert.equal(phase.mode, "staged-react"); assert.equal(phase.until, "S1-M2");
    const legacy = phase.legacy; assert.ok(closed(legacy, ["version", "archive_sha256", "source_sha", "receipt", "receipt_sha256"]));
    assert.equal(legacy.version, "0.3.0"); assert.match(legacy.archive_sha256, hex); assert.match(legacy.source_sha, /^[a-f0-9]{40}(?:[a-f0-9]{24})?$/); assert.match(legacy.receipt_sha256, hex);
    literal(legacy.receipt);
    assert.ok(!/\.tsbuildinfo(?:\.(?:gz|br))?$/.test(legacy.receipt)
      && !legacy.receipt.split("/").some(part => part.startsWith(".") || ["kit", "node_modules", "third_party", "vendor", "dist", "embedfs", "test-results", "TASK_BRIEF.md", "TASK_RESULT.md", "SWARM_RESULT.md"].includes(part))
      && ![config.npm_dir, config.vendor_dir].some(dir => legacy.receipt === dir || legacy.receipt.startsWith(dir + "/")));
  }
  const projected = { role: config.role, app: config.app, npm_dir: config.npm_dir, vendor_dir: config.vendor_dir, go_dirs: [...config.go_dirs], ...(phase ? { ui_adoption: phase } : {}) };
  assert.equal(JSON.stringify(config), JSON.stringify(projected)); assert.equal(sha(JSON.stringify(projected)), actual.config_sha256);
  const command = captured.command;
  assert.ok(closed(command, ["command", "args", "exit_code", "duration_ms", "stdout_sha256", "stderr_sha256"]));
  assert.equal(command.command, "task"); assert.deepEqual(command.args, ["--silent", "repo:kit-config"]); assert.equal(command.exit_code, 0);
  assert.ok(Number.isInteger(command.duration_ms) && command.duration_ms >= 0); assert.match(command.stdout_sha256, hex); assert.match(command.stderr_sha256, hex);
  for (const name of [".gate", prefix.slice(0, -1)]) {
    const file = regular(name, true), stat = fs.lstatSync(file);
    assert.equal(stat.uid, uid, "Wrapper evidence ancestors must belong to the real runner");
    assert.ok([0o755, 0o775].includes(stat.mode & 0o777), "Unexpected ordinary wrapper ancestor mode");
  }
  const privateParent = fs.lstatSync(regular(".gate/_temp", true));
  assert.equal(privateParent.uid, uid, "Private staging must belong to the real runner");
  assert.equal(privateParent.mode & 0o777, 0o700, "Private staging must be owner-only");
  for (const name of [".gate/wrapper-current.json", prefix + "wrapper-current.json", actual.config_path]) {
    const stat = fs.lstatSync(regular(name)); assert.equal(stat.uid, uid); assert.equal(stat.mode & 0o222, 0, "Real wrapper-owned immutable receipt required");
  }
  const bootstrapPath = prefix + "bootstrap-execution.json", bootstrapBytes = read(bootstrapPath), bootstrap = JSON.parse(bootstrapBytes);
  assert.ok(closed(bootstrap, ["schema", "target", "invocation", "sha", "tree_sha256", "toolchain_digest", "started", "config", "config_sha256", "wrapper_target", "wrapper_config", "wrapper_config_sha256", "wrapper_invocation", "wrapper_descriptor", "wrapper_descriptor_sha256", "actions", "artifacts", "finished"]));
  for (const key of ["schema", "target", "sha", "tree_sha256", "toolchain_digest", "config_sha256"]) assert.equal(bootstrap[key], actual[key]);
  assert.match(bootstrap.invocation, uuid); // Real runner I is distinct in purpose from wrapper W; no invented W=I requirement.
  assert.equal(bootstrap.wrapper_target, actual.target); assert.equal(bootstrap.wrapper_config, actual.config_path);
  assert.equal(bootstrap.wrapper_config_sha256, actual.config_file_sha256); assert.equal(bootstrap.wrapper_invocation, actual.invocation);
  assert.equal(bootstrap.wrapper_descriptor, ".gate/wrapper-current.json"); assert.equal(bootstrap.wrapper_descriptor_sha256, sha(descriptorBytes));
  assert.equal(JSON.stringify(bootstrap.config), JSON.stringify(projected));
  assert.ok(Number.isFinite(Date.parse(bootstrap.started)) && Number.isFinite(Date.parse(bootstrap.finished)) && Date.parse(bootstrap.finished) >= Date.parse(bootstrap.started));
  assert.ok(Array.isArray(bootstrap.actions) && bootstrap.actions.length && Array.isArray(bootstrap.artifacts));
  const retainedInputs = new Map([["wrapper-current.json", descriptorBytes], ["primary-wrapper-current.json", primaryBytes], ["wrapper-kit-config.json", configBytes], ["bootstrap-execution.json", bootstrapBytes]]);
  const listed = new Map();
  for (const artifact of bootstrap.artifacts) {
    const match = /^(.+) sha256:([a-f0-9]{64})$/.exec(artifact);
    assert.ok(match && match[1].startsWith(prefix + "logs/" + bootstrap.invocation + "-bootstrap-") && !listed.has(match[1]));
    assert.equal(path.posix.dirname(match[1]), prefix + "logs");
    assert.ok(!retainedInputs.has("logs/" + path.basename(match[1])), "Colliding actual log basename refused");
    const bytes = read(match[1]); assert.equal(sha(bytes), match[2]); listed.set(match[1], match[2]);
    retainedInputs.set("logs/" + path.basename(match[1]), bytes);
  }
  const used = new Set(); let configCommands = 0;
  for (const action of bootstrap.actions) {
    assert.ok(closed(action, ["phase", "kind", "command", "argument_count", "args_sha256", "cwd", "exit_code", "duration_ms", "stdout_sha256", "stderr_sha256", "stdout_log", "stderr_log"]));
    assert.equal(action.kind, "command"); assert.equal(action.cwd, "."); assert.equal(action.exit_code, 0);
    assert.match(action.phase, /^[A-Za-z][A-Za-z0-9._-]*$/); assert.ok(typeof action.command === "string" && action.command);
    assert.ok(Number.isInteger(action.argument_count) && action.argument_count >= 0 && Number.isInteger(action.duration_ms) && action.duration_ms >= 0); assert.match(action.args_sha256, hex);
    for (const stream of ["stdout", "stderr"]) { const name = action[stream + "_log"]; assert.equal(listed.get(name), action[stream + "_sha256"]); assert.ok(!used.has(name)); used.add(name); }
    if (action.phase === "config") {
      assert.equal(action.command, "task"); assert.equal(action.argument_count, 2); assert.equal(action.args_sha256, sha(JSON.stringify(["--silent", "repo:kit-config"])));
      assert.equal(JSON.stringify(JSON.parse(retainedInputs.get("logs/" + path.basename(action.stdout_log)))), JSON.stringify(projected)); configCommands += 1;
    }
  }
  assert.equal(used.size, listed.size); assert.equal(listed.size, bootstrap.actions.length * 2); assert.ok(configCommands > 0);
  const sourceInputs = [
    ["scripts/gui-style-plan.mjs", "8121c917f20995afed34d2612c45543b965918a64f7a18b0af4463ca96bf872f"],
    ["frontend/tests/fixtures/gui-style-plan.json", "24bdcb858dcc74878e99aca0de338bf335cf3b1b3c14e8b68820fca1be9ca8b9"],
    ["frontend/src/components/cssUnits.ts", "5681d320b14511757894cff3a850b7f67114d78e9b1eb0d2c36e4d7551c1b873"],
    ["frontend/src/components/CspStyle.ts", "2ea61764325b4cb9ecd036d106466594d0f32f2f6d83b09a547981c0317fa320"],
    ["frontend/src/components/CspElements.tsx", "f1c5478b8d243223d16baedb9fc6f0ced38f073377e0d7393e252b5a598b32c3"],
  ].map(([name, expected]) => { const bytes = read(name); assert.equal(sha(bytes), expected); return { path: name, bytes: bytes.length, sha256: expected }; });
  const testBytes = read("frontend/tests/gui-style-plan.test.mjs");
  sourceInputs.push({ path: "frontend/tests/gui-style-plan.test.mjs", bytes: testBytes.length, sha256: sha(testBytes) });
  // Admission above is read-only. No parent is created or repaired; an absent
  // canonical .gate/_temp is a required native-readiness failure, not a skip.
  const caseRoot = path.join(regular(".gate/_temp", true), "NON-RELEASE-style-plan-" + randomUUID());
  fs.mkdirSync(caseRoot, { mode: 0o700 }); // Exclusive: EEXIST is a failure, never reuse.
  const caseRelative = path.relative(repository, caseRoot).split(path.sep).join("/");
  const root = path.join(caseRoot, "fixture"), probe = path.join(caseRoot, "private-probe"), observations = path.join(caseRoot, "observations");
  const authority = { scope: "NON-RELEASE-PLANNER-PUBLICATION-PROBE", label, actual_root: repository, actual_target_directory: prefix,
    physical_case_root: caseRoot, physical_fixture_root: root, runner_uid: uid, wrapper: actual, bootstrap_invocation: bootstrap.invocation,
    descriptor_sha256: sha(descriptorBytes), source_inputs: sourceInputs,
    preservation_required: "Manually preserve this complete physical case root AND complete actual ROOT/target/config/bootstrap/command receipts before EVERY --fresh/mirror reset; diagnostic JSON is not physical preservation.",
    automatic_fresh_or_teardown_survival: "UNSET", release_qualified: false };
  function retain(stage) {
    const rows = [];
    function inventory(name) {
      const file = path.join(repository, ...name.split("/")), stat = fs.lstatSync(file, { bigint: true });
      const row = { path: path.relative(caseRoot, file).split(path.sep).join("/") || ".", mode: Number(stat.mode), uid: Number(stat.uid) };
      assert.equal(stat.dev, repositoryStat.dev); assert.equal(stat.uid, BigInt(uid));
      if (stat.isSymbolicLink()) {
        const text = fs.readlinkSync(file); rows.push({ ...row, kind: "literal-symlink", link_text: text, link_text_sha256: sha(text), followed: false });
        assert.equal(label, "literal-symlink-probe", "Unexpected publication link refused without following it");
        assert.equal(file, path.join(root, ".gate")); assert.equal(text, path.join(probe, "referent"));
        assert.ok(path.isAbsolute(text) && path.resolve(text) === text && text.startsWith(caseRoot + path.sep), "Escaping/aliased literal referent refused");
      }
      else if (stat.isDirectory()) { regular(name, true); rows.push({ ...row, kind: "directory" }); for (const child of fs.readdirSync(file).sort()) inventory(name + "/" + literal(child)); }
      else if (stat.isFile()) { const bytes = read(name); rows.push({ ...row, kind: "regular", bytes: bytes.length, sha256: sha(bytes) }); }
      else { rows.push({ ...row, kind: "nonregular-refused", followed: false }); throw Error("Nonregular physical probe refused"); }
    }
    let inventoryFailure;
    try {
      try {
        assert.deepEqual(read(".gate/wrapper-current.json"), descriptorBytes);
        assert.deepEqual(read(prefix + "wrapper-current.json"), primaryBytes);
        assert.deepEqual(read(actual.config_path), configBytes);
        assert.deepEqual(read(bootstrapPath), bootstrapBytes);
        inventory(caseRelative);
      } catch (error) { inventoryFailure = error; }
      const file = path.join(observations, "literal-inventory-" + randomUUID() + ".json");
      regular(caseRelative + "/observations", true);
      fs.writeFileSync(file, JSON.stringify({ schema: 1, stage, authority, cleanup_performed: false,
        ...(inventoryFailure ? { inventory_refusal: inventoryFailure.message } : {}), rows }, null, 2) + "\n", { flag: "wx", mode: 0o600 });
      if (inventoryFailure) throw inventoryFailure;
    } finally { t.diagnostic(`Physical NON-RELEASE case root: ${caseRoot}; fixture: ${root}; actual ROOT: ${repository}; target receipts: ${prefix}; preservation required before EVERY fresh/reset; stage: ${stage}`); }
  }
  // Register retention immediately after exclusive allocation so later setup
  // failures still disclose the retained physical root. Never recursively clean.
  t.after(() => retain("after-test-success-or-failure"));
  try {
    const stat = fs.lstatSync(regular(caseRelative, true)); assert.equal(stat.mode & 0o777, 0o700); assert.equal(stat.uid, uid);
    for (const directory of [observations, root, probe, path.join(caseRoot, "actual-input-association"), path.join(caseRoot, "actual-input-association/logs")]) fs.mkdirSync(directory, { mode: 0o700 });
    for (const [name, bytes] of retainedInputs) fs.writeFileSync(path.join(caseRoot, "actual-input-association", ...name.split("/")), bytes, { flag: "wx", mode: 0o600 });
    fs.writeFileSync(path.join(caseRoot, "NON-RELEASE-CANARY.txt"), "Retain literal physical fixture trees; this is no gate-success or release receipt.\n", { flag: "wx", mode: 0o600 });
    fs.writeFileSync(path.join(caseRoot, "native-root-association.json"), JSON.stringify(authority, null, 2) + "\n", { flag: "wx", mode: 0o600 });
    retain("before-publication-or-probe");
    return body(root, probe, retain);
  } finally { retain("finally-success-or-real-failure"); }
}

void test("publication retains prior artifacts and failure evidence without selecting a tree", t => publicationFixture(t, "prior-artifacts", (root, _probe, retain) => {
  const old = path.join(root, ".gate/gen/styles/converted/frontend/src/old.tsx");
  fs.mkdirSync(path.dirname(old), { recursive: true }); fs.writeFileSync(old, "prior-evidence", { flag: "wx" });
  retain("prior-artifact-before-assertions");
  const failed = analyze("export function Fixture({ value }: { value: any }) { return <div style={{ width: value }} />; }");
  assertFailed(failed);
  const first = publishStylePlan(root, failed), second = publishStylePlan(root, failed);
  retain("both-publications-before-assertions");
  for (const report of [first, second]) {
    assert.equal(report.converted, null); assert.equal(report.application_ready, false);
    assert.ok(fs.existsSync(path.join(root, report.output, "analysis.json")));
    assert.ok(fs.existsSync(path.join(root, report.report_json)));
    assert.equal(fs.existsSync(path.join(root, report.output, "candidate")), false);
  }
  assert.notEqual(first.output, second.output); assert.equal(fs.readFileSync(old, "utf8"), "prior-evidence");
}));
void test("a publication hash failure preserves partial evidence and publishes no tree path", t => publicationFixture(t, "partial-hash-failure", (root, _probe, retain) => {
  const valid = analyze("export function Fixture() { return <div style={{ width: 1 }} />; }");
  assert.equal(valid.status, "pass", JSON.stringify(valid));
  const plan = { ...valid, files: valid.files.map((file, index) => index === 0 ? { ...file, after_sha256: "0".repeat(64) } : file) };
  const report = publishStylePlan(root, plan);
  retain("partial-publication-before-assertions");
  assert.equal(report.status, "fail"); assert.equal(report.application_ready, false); assert.equal(report.converted, null);
  assert.ok(fs.existsSync(path.join(root, report.output, "analysis.json")));
  assert.ok(fs.existsSync(path.join(root, report.output, "candidate")));
  assert.ok(fs.existsSync(path.join(root, report.report_json)));
  assert.ok(!fs.existsSync(path.join(root, report.output, "report.json")));
}));
void test("publication refuses stream/reserved path components without exposing a tree", t => {
  for (const file of ["frontend/src/old.tsx:stream.tsx", "frontend/src/CON.tsx", "frontend/src/LPT1.tsx", "frontend/src/trailing./Cue.tsx"]) {
    publicationFixture(t, "reserved-component:" + file, (root, _probe, retain) => {
      const report = publishStylePlan(root, { status: "pass", application_ready: true, files: [{ file, text: "cue", after_sha256: sha("cue") }], manual: [], diagnostics: [], candidate_diagnostics: [] });
      retain("refused-path-publication-before-assertions");
      assert.equal(report.status, "fail"); assert.equal(report.application_ready, false); assert.equal(report.converted, null);
      assert.ok(report.manual.length);
    });
  }
});
void test("publication refuses a symlinked output ancestor and retains the other tree", t => publicationFixture(t, "literal-symlink-probe", (root, probe, retain) => {
  const other = path.join(probe, "referent"); fs.mkdirSync(other, { mode: 0o700 });
  fs.writeFileSync(path.join(other, "kept.txt"), "other-evidence", { flag: "wx" });
  fs.symlinkSync(other, path.join(root, ".gate"), "dir");
  retain("literal-link-and-referent-canary-before-publication");
  const report = publishStylePlan(root, { status: "fail", application_ready: false, files: [], manual: [{ reason: "fixture" }], diagnostics: [], candidate_diagnostics: [] });
  retain("refused-symlink-publication-before-assertions");
  assert.equal(report.status, "fail"); assert.equal(report.application_ready, false); assert.equal(report.converted, null);
  assert.equal(report.report_json, null); assert.equal(report.output, null);
  assert.equal(fs.readFileSync(path.join(other, "kept.txt"), "utf8"), "other-evidence");
}));
