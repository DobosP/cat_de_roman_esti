import test from "node:test";
import assert from "node:assert/strict";
import * as fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createHash } from "node:crypto";
import { gzipSync, gunzipSync, brotliCompressSync, brotliDecompressSync } from "node:zlib";
import vm from "node:vm";
import ts from "@typescript/typescript6";
import * as budget from "@roedu/web-kit/budget";
import * as compressed from "../scripts/gui-precompressed-assets.mjs";
import { parserBinding } from "../scripts/compiler-runtime.mjs";
import { collectInitialBundleFiles, measureGzipFiles, ROMANIAN_FONT_SOURCES } from "../scripts/check-bundle-budget.mjs";
import { measureProfile, verifyTreeRows } from "../../scripts/gui-route-budgets.mjs";
import { readTarGz } from "../../tools/gui-bootstrap-webkit/scripts/kit-sync.mjs";

// NON-NATIVE filesystem/codec/plugin contracts. Real image/HTTP/browser execution
// remains necessary; these fixtures do not manufacture release or runtime proof.
const repo = fileURLToPath(new URL("../../", import.meta.url)).replace(/\/$/, "");
const hash = (bytes) => createHash("sha256").update(bytes).digest("hex");
const account = "src/components/AccountBar.tsx";
const screens = ["Alchimie", "Intrusul", "Perechi", "CaldRece", "Lant", "Conexiuni", "Ranking"];
const routes = ["/", "/alchimie", "/intrusul", "/perechi", "/cald-rece", "/lant", "/conexiuni", "/clasament"];
const budgetBytes = fs.readFileSync(new URL("../../budgets.json", import.meta.url));
const budgets = JSON.parse(budgetBytes);
function write(root, file, bytes) {
  const absolute = path.join(root, file); fs.mkdirSync(path.dirname(absolute), { recursive: true }); fs.writeFileSync(absolute, bytes);
}
function rows(root, prefix = "") {
  return fs.readdirSync(path.join(root, prefix), { withFileTypes: true }).sort((a, b) => a.name.localeCompare(b.name)).flatMap((entry) => {
    const file = prefix + entry.name;
    return entry.isDirectory() ? rows(root, file + "/") : [{ file, bytes: fs.readFileSync(path.join(root, file)) }];
  });
}
function fixture() {
  assert.equal(process.platform, "linux", "Owning Linux runtime required; no host fixture fallback");
  let base = path.join(repo, ".gate");
  assert.ok(fs.lstatSync(base).isDirectory() && !fs.lstatSync(base).isSymbolicLink() && fs.realpathSync(base) === base);
  for (const part of ["_temp", "gui-precompressed-synthetic"]) {
    base = path.join(base, part);
    if (!fs.existsSync(base)) fs.mkdirSync(base, { mode: 0o700 });
    const info = fs.lstatSync(base);
    assert.ok(info.isDirectory() && !info.isSymbolicLink() && fs.realpathSync(base) === base
      && info.uid === process.getuid() && (info.mode & 0o7777) === 0o700, "Owned private retained fixture directory required");
  }
  const parent = fs.mkdtempSync(path.join(base, "NON-NATIVE-")), root = path.join(parent, "dist"); fs.mkdirSync(root);
  const manifest = {
    "index.html": { file: "assets/entry.js", isEntry: true, imports: ["startup"], css: ["assets/global.css"] },
    startup: { file: "assets/startup.js", imports: ["shared"], dynamicImports: [account, ...screens.map((name) => `src/screens/${name}.tsx`)] },
    shared: { file: "assets/shared.js", imports: ["startup"], css: ["assets/shared.css"] },
    [account]: { file: "assets/account.js", isDynamicEntry: true, imports: ["shared"], css: ["assets/account.css"] },
    "global-style": { file: "assets/global.css" },
  };
  for (const [index, name] of screens.entries()) manifest[`src/screens/${name}.tsx`] = {
    file: `assets/game-${index}.js`, isDynamicEntry: true, imports: ["shared"], css: [`assets/game-${index}.css`],
  };
  for (const [index, src] of ROMANIAN_FONT_SOURCES.entries()) {
    manifest[`font-${index}`] = { file: `assets/font-${index}.woff2`, src };
    write(root, `assets/font-${index}.woff2`, `NON-NATIVE font bytes ${index}`);
  }
  for (const item of Object.values(manifest)) {
    if (/\.[cm]?js$/.test(item.file)) write(root, item.file, `/* NON-NATIVE ${item.file} */\nexport const values=${JSON.stringify(Array.from({ length: 160 }, (_, i) => "value" + (i % 11)))};\n`);
    for (const file of item.css ?? []) write(root, file, `/* NON-NATIVE ${file} */ .fixture{color:navy}\n`.repeat(5));
  }
  write(root, "index.html", "<!doctype html><html><head></head><body>NON-NATIVE</body></html>\n");
  write(root, ".vite/manifest.json", JSON.stringify(manifest, null, 2) + "\n");
  write(root, "public.txt", "NON-NATIVE ordinary uncompressed public file\n");
  return { parent, root, manifest };
}
function encodedFixture() {
  const f = fixture(); compressed.emitPrecompressedAssets(f.root); return f;
}
function retainedRows(root) { return rows(root).map(({ file, bytes }) => ({ path: file, bytes: bytes.length, sha256: hash(bytes) })); }

void test("final raw manifest-owned JS/CSS receives exact deterministic gzip9 and Brotli pairs without changing raw bytes or metadata", () => {
  const a = fixture(), b = fixture(), before = rows(a.root), metadata = new Map(before.map(({ file }) => {
    const info = fs.statSync(path.join(a.root, file), { bigint: true });
    return [file, { mode: info.mode, mtime: info.mtimeNs, ctime: info.ctimeNs }];
  }));
  const result = compressed.emitPrecompressedAssets(a.root); compressed.emitPrecompressedAssets(b.root);
  const owned = compressed.manifestCodeFiles(a.manifest);
  assert.deepEqual(result.map((item) => item.file), owned);
  assert.deepEqual(rows(a.root).map((item) => item.file).sort(), [...before.map((item) => item.file), ...owned.flatMap((file) => [file + ".gz", file + ".br"])].sort());
  for (const { file, bytes } of before) {
    assert.deepEqual(fs.readFileSync(path.join(a.root, file)), bytes);
    const info = fs.statSync(path.join(a.root, file), { bigint: true });
    assert.deepEqual({ mode: info.mode, mtime: info.mtimeNs, ctime: info.ctimeNs }, metadata.get(file));
  }
  for (const file of owned) {
    const raw = fs.readFileSync(path.join(a.root, file)), gz = fs.readFileSync(path.join(a.root, file + ".gz")), br = fs.readFileSync(path.join(a.root, file + ".br"));
    assert.deepEqual(gz, gzipSync(raw, { level: 9 })); assert.deepEqual(gunzipSync(gz), raw); assert.deepEqual(brotliDecompressSync(br), raw);
    assert.deepEqual(gz.subarray(4, 8), Buffer.alloc(4)); assert.equal(gz[3], 0);
    assert.deepEqual(gz, fs.readFileSync(path.join(b.root, file + ".gz"))); assert.deepEqual(br, fs.readFileSync(path.join(b.root, file + ".br")));
  }
  for (const file of ["index.html", ".vite/manifest.json", "public.txt", ...ROMANIAN_FONT_SOURCES.map((_, i) => `assets/font-${i}.woff2`)]) {
    assert.equal(fs.existsSync(path.join(a.root, file + ".gz")), false); assert.equal(fs.existsSync(path.join(a.root, file + ".br")), false);
  }
});

for (const [name, mutate] of [
  ["missing gzip", (r) => r.filter((x) => x.file !== "assets/entry.js.gz")],
  ["missing Brotli", (r) => r.filter((x) => x.file !== "assets/entry.js.br")],
  ["missing raw owner", (r) => r.filter((x) => x.file !== "assets/entry.js")],
  ["orphan sidecar", (r) => [...r, { file: "assets/orphan.js.gz", bytes: gzipSync(Buffer.from("orphan")) }]],
  ["nested sidecar", (r) => [...r, { file: "assets/entry.js.gz.br", bytes: Buffer.from("nested") }]],
  ["uppercase sidecar alias", (r) => [...r, { file: "assets/entry.js.GZ", bytes: Buffer.from("uppercase") }]],
  ["compressed HTML", (r) => [...r, { file: "index.html.gz", bytes: gzipSync(Buffer.from("html")) }]],
  ["compressed manifest", (r) => [...r, { file: ".vite/manifest.json.br", bytes: Buffer.from("manifest") }]],
  ["compressed font", (r) => [...r, { file: "assets/font-0.woff2.gz", bytes: gzipSync(Buffer.from("font")) }]],
  ["duplicate row", (r) => [...r, r[0]]],
  ["directory spelling alias", (r) => [...r, { file: "Assets/extra.txt", bytes: Buffer.from("alias") }]],
  ["path traversal", (r) => [...r, { file: "assets/../extra.js.gz", bytes: Buffer.from("escape") }]],
  ["absolute path", (r) => [...r, { file: "/assets/extra.js.gz", bytes: Buffer.from("absolute") }]],
  ["encoded path alias", (r) => [...r, { file: "assets/%65ntry.js.gz", bytes: Buffer.from("encoded") }]],
  ["sparse rows", (r) => { const x = [...r]; delete x[0]; return x; }],
  ["nonbyte row", (r) => r.map((x) => x.file === "assets/entry.js.gz" ? { ...x, bytes: "not actual bytes" } : x)],
]) void test("complete pair validation refuses " + name, () => {
  const f = encodedFixture(); assert.throws(() => compressed.validatePrecompressedAssets(f.manifest, mutate(rows(f.root))));
});

for (const [name, change] of [
  ["malformed gzip", () => Buffer.from("not-gzip")],
  ["stale gzip", () => gzipSync(Buffer.from("different raw owner"), { level: 9 })],
  ["timestamped gzip", (raw) => { const x = gzipSync(raw, { level: 9 }); x[4] = 1; return x; }],
  ["gzip output beyond raw bound", () => gzipSync(Buffer.alloc(2 * 1024 * 1024, 65), { level: 9 })],
  ["different gzip level", (raw) => gzipSync(raw, { level: 1 })],
  ["concatenated empty gzip member", (raw) => Buffer.concat([gzipSync(raw, { level: 9 }), gzipSync(Buffer.alloc(0), { level: 9 })])],
  ["trailing gzip padding", (raw) => Buffer.concat([gzipSync(raw, { level: 9 }), Buffer.from([0])])],
]) void test("gzip validation refuses " + name, () => {
  const f = encodedFixture(), all = rows(f.root), raw = all.find((x) => x.file === "assets/entry.js").bytes;
  const changed = all.map((x) => x.file === "assets/entry.js.gz" ? { ...x, bytes: change(raw) } : x);
  assert.throws(() => compressed.validatePrecompressedAssets(f.manifest, changed));
});
void test("Brotli validation refuses malformed bytes and stale decoded content", () => {
  const f = encodedFixture(), all = rows(f.root), other = all.find((x) => x.file === "assets/account.js.br").bytes;
  const own = all.find((x) => x.file === "assets/entry.js.br").bytes;
  for (const bytes of [Buffer.from("not-brotli"), other, Buffer.concat([own, Buffer.from([0])]), brotliCompressSync(Buffer.alloc(2 * 1024 * 1024, 65))]) assert.throws(() => compressed.validatePrecompressedAssets(f.manifest,
    all.map((x) => x.file === "assets/entry.js.br" ? { ...x, bytes } : x)));
});
void test("manifest code ownership includes record.css and refuses compressed owners, sparse metadata and case aliases", () => {
  const f = fixture(); assert.ok(compressed.manifestCodeFiles(f.manifest).includes("assets/global.css"));
  for (const mutate of [
    (m) => { m["index.html"].file = "assets/entry.js.gz"; },
    (m) => { m["index.html"].css = new Array(1); },
    (m) => { m.alias = { file: "Assets/other.js" }; },
    (m) => { m.bad = { file: "assets/entry.js/child.css" }; },
  ]) { const changed = structuredClone(f.manifest); mutate(changed); assert.throws(() => compressed.manifestCodeFiles(changed)); }
});
void test("emission refuses existing sidecars and file/directory symlinks rather than overwriting or following them", () => {
  const existing = encodedFixture(), kept = rows(existing.root); assert.throws(() => compressed.emitPrecompressedAssets(existing.root), /existing sidecars/);
  assert.deepEqual(rows(existing.root), kept);
  for (const directory of [false, true]) {
    const f = fixture(), leaf = directory ? "alias" : "alias.js";
    fs.symlinkSync(directory ? "assets" : "assets/entry.js", path.join(f.root, leaf));
    assert.throws(() => compressed.emitPrecompressedAssets(f.root), /symlink/);
    assert.equal(fs.existsSync(path.join(f.root, "assets/entry.js.gz")), false);
  }
  const f = fixture(); fs.unlinkSync(path.join(f.root, "assets/entry.js")); fs.mkdirSync(path.join(f.root, "assets/entry.js"));
  assert.throws(() => compressed.emitPrecompressedAssets(f.root), /raw asset/);
});

void test("complete current inventory/sync keeps paired representations while the genuine frozen thirty-file payload stays exact", () => {
  const f = encodedFixture(), current = rows(f.root), destination = path.join(f.parent, "embedded-current");
  compressed.copyManagedAssetFiles(destination, current);
  assert.deepEqual(rows(destination), current);
  verifyTreeRows(f.parent, "embedded-current", retainedRows(f.root));
  const proofBytes = fs.readFileSync(path.join(repo, "legacy/original-bundle.json")), proof = JSON.parse(proofBytes);
  const archiveBytes = fs.readFileSync(path.join(repo, proof.archive));
  assert.equal(hash(archiveBytes), "742bb11130fa2bf52ba5c64cb9cfd452f7d8ac3a4fd9dc6d77e8064a6b8fef65");
  const members = readTarGz(archiveBytes); assert.equal(members.size, 30); assert.equal(proof.files.length, 30);
  const legacy = proof.files.map((row) => {
    const member = members.get(row.path); assert.equal(member.type, "file"); assert.equal(hash(member.data), row.sha256); assert.equal(member.data.length, row.bytes);
    return { file: row.path, bytes: member.data };
  }).sort((a, b) => a.file.localeCompare(b.file));
  const rollback = path.join(f.parent, "embedded-legacy"); compressed.copyManagedAssetFiles(rollback, legacy);
  assert.deepEqual(rows(rollback), legacy); assert.equal(rows(rollback).length, 30);
  assert.deepEqual(fs.readFileSync(path.join(repo, "legacy/original-bundle.json")), proofBytes);
  assert.deepEqual(fs.readFileSync(path.join(repo, proof.archive)), archiveBytes);
  fs.appendFileSync(path.join(destination, "assets/entry.js.gz"), "tampered");
  assert.throws(() => verifyTreeRows(f.parent, "embedded-current", retainedRows(f.root)), /differs/);
});

void test("raw manifest, budget roots and limits remain exact while unchanged SDK accounting measures real level9 sidecars", () => {
  const f = fixture(), original = rows(f.root), manifestBytes = fs.readFileSync(path.join(f.root, ".vite/manifest.json"));
  const selected = collectInitialBundleFiles(f.manifest, { eagerRoots: [account] }), initial = measureGzipFiles(f.root, selected);
  const before = measureProfile(f.root, budgets, routes, budget);
  compressed.emitPrecompressedAssets(f.root);
  const after = measureProfile(f.root, budgets, routes, budget);
  assert.deepEqual(fs.readFileSync(path.join(f.root, ".vite/manifest.json")), manifestBytes);
  assert.deepEqual(collectInitialBundleFiles(f.manifest, { eagerRoots: [account] }), selected);
  assert.deepEqual(measureGzipFiles(f.root, selected), initial);
  assert.deepEqual(fs.readFileSync(new URL("../../budgets.json", import.meta.url)), budgetBytes);
  for (const [index, row] of after.report.routes.entries()) {
    assert.deepEqual(row.js.files, before.report.routes[index].js.files); assert.deepEqual(row.css.files, before.report.routes[index].css.files);
    assert.equal(row.js.limit_gz, before.report.routes[index].js.limit_gz); assert.equal(row.js.target_gz, before.report.routes[index].js.target_gz);
    assert.equal(row.js.actual_gz, row.js.files.reduce((sum, file) => sum + fs.readFileSync(path.join(f.root, file + ".gz")).length, 0));
  }
  for (const item of original) assert.deepEqual(fs.readFileSync(path.join(f.root, item.file)), item.bytes);
});

function actualPlugin() {
  parserBinding(path.join(repo, "frontend"), ts);
  const filename = fileURLToPath(new URL("../scripts/gui-precompressed-plugin.mts", import.meta.url));
  const source = fs.readFileSync(filename, "utf8"), result = ts.transpileModule(source, {
    fileName: filename, reportDiagnostics: true,
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2021, esModuleInterop: true },
  });
  assert.equal((result.diagnostics ?? []).filter((item) => item.category === ts.DiagnosticCategory.Error).length, 0);
  const exports = {}, dependencies = { "node:path": path, "node:assert/strict": assert, "./gui-precompressed-assets.mjs": compressed };
  vm.runInNewContext(result.outputText, { exports, require(name) {
    assert.ok(Object.hasOwn(dependencies, name), "Unknown actual plugin module binding: " + name); return dependencies[name];
  } }, { filename });
  return exports.guiPrecompressedPlugin();
}
void test("actual post-close plugin reads finalized on-disk bytes and emits nothing for failed or unwritten builds", () => {
  for (const state of ["failed", "unwritten", "finalized"]) {
    const f = fixture(), plugin = actualPlugin();
    plugin.configResolved({ root: f.parent, build: { outDir: "dist", manifest: true, write: true } }); plugin.buildStart();
    plugin.buildEnd(state === "failed" ? Error("NON-NATIVE build failure") : null);
    if (state !== "unwritten") plugin.writeBundle();
    write(f.root, "assets/entry.js", "/* NON-NATIVE finalized minified bytes, after earlier build hooks */export const final=7;\n");
    assert.equal(plugin.closeBundle.order, "post"); assert.equal(plugin.closeBundle.sequential, true); plugin.closeBundle.handler();
    assert.equal(fs.existsSync(path.join(f.root, "assets/entry.js.gz")), state === "finalized");
    if (state === "finalized") assert.deepEqual(gunzipSync(fs.readFileSync(path.join(f.root, "assets/entry.js.gz"))), fs.readFileSync(path.join(f.root, "assets/entry.js")));
  }
});
