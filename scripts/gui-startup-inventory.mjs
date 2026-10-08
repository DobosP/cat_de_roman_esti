import * as fs from "node:fs";
import path from "node:path";
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { collectInitialBundleFiles, measureGzipFiles, assertRomanianFontSubsets, DEFAULT_INITIAL_GZIP_LIMIT_KIB } from "../frontend/scripts/check-bundle-budget.mjs";

const root = fs.realpathSync(process.cwd());
const sha256 = (bytes) => createHash("sha256").update(bytes).digest("hex");
function regular(relative) {
  assert.equal(typeof relative, "string");
  assert.ok(relative && !path.isAbsolute(relative) && !/[\\:\x00-\x1f\x7f]/.test(relative));
  const parts = relative.split("/");
  assert.ok(parts.every((part) => part && part !== "." && part !== ".."));
  let current = root;
  for (let i = 0; i < parts.length; i += 1) {
    current = path.join(current, parts[i]);
    const stat = fs.lstatSync(current);
    assert.ok(!stat.isSymbolicLink() && (i < parts.length - 1 ? stat.isDirectory() : stat.isFile()), "Regular confined startup input required");
  }
  return current;
}
const read = (relative) => fs.readFileSync(regular(relative));
assert.equal(process.argv.length, 2, "Startup measurement accepts no caller-selected scope or limit");
const descriptorBytes = read(".gate/gen/wrapper-current.json");
const descriptor = JSON.parse(descriptorBytes);
assert.equal(descriptor.target, "gen");
assert.equal(descriptor.sha, process.env.GATE_SHA);
assert.equal(descriptor.tree_sha256, process.env.GATE_TREE_SHA256);
assert.equal(descriptor.toolchain_digest, process.env.TOOLCHAIN_DIGEST);
assert.deepEqual(descriptorBytes, read(".gate/wrapper-current.json"));
const request = JSON.parse(read("scripts/gui-gen-request.json"));
assert.deepEqual(request, { schema: 1, operation: "replay-normalized-react", fixtures: "frontend/e2e/original/runtime.spec.mjs" });
assert.equal(DEFAULT_INITIAL_GZIP_LIMIT_KIB, 120);
const manifestBytes = read("frontend/dist/.vite/manifest.json");
const manifest = JSON.parse(manifestBytes);
assert.ok(manifest && typeof manifest === "object" && !Array.isArray(manifest));
const eagerRoots = ["src/components/AccountBar.tsx"];
const files = collectInitialBundleFiles(manifest, { eagerRoots });
assert.ok(files.length > 0 && files.length === new Set(files).size);
const staticFiles = collectInitialBundleFiles(manifest);
const rows = measureGzipFiles(path.join(root, "frontend/dist"), files).map(({ file, bytes }) => {
  const data = read(`frontend/dist/${file}`);
  return { file, kind: file.endsWith(".css") ? "css" : "js", bytes: data.length, sha256: sha256(data), gzip_level: 9, gzip_bytes: bytes, in_static_closure: staticFiles.includes(file) };
});
const fontSources = assertRomanianFontSubsets(manifest);
const fonts = Object.values(manifest).filter((chunk) => fontSources.includes(chunk.src)).map((chunk) => {
  const data = read(`frontend/dist/${chunk.file}`);
  return { source: chunk.src, file: chunk.file, bytes: data.length, sha256: sha256(data) };
}).sort((a, b) => a.source.localeCompare(b.source));
const sum = (selected) => selected.reduce((total, row) => total + row.gzip_bytes, 0);
const output = ".gate/gen/normalized-react/startup-measurement.json";
const report = {
  schema: 1, scope: "fresh-emitted-entry-and-mandatory-AccountBar-static-JS-CSS", status: "measured", qualified: false,
  sha: descriptor.sha, tree_sha256: descriptor.tree_sha256, toolchain_digest: descriptor.toolchain_digest, invocation: descriptor.invocation,
  descriptor_sha256: sha256(descriptorBytes), acquired: new Date().toISOString(), eager_roots: eagerRoots,
  inputs: Object.fromEntries(["frontend/package.json", "frontend/package-lock.json", "frontend/src/App.tsx", "frontend/scripts/check-bundle-budget.mjs", "scripts/gui-startup-inventory.mjs"].map((file) => { const data = read(file); return [file, { bytes: data.length, sha256: sha256(data) }]; })),
  manifest: { path: "frontend/dist/.vite/manifest.json", bytes: manifestBytes.length, sha256: sha256(manifestBytes) },
  files: rows, font_files: fonts, static_only_gzip_bytes: sum(rows.filter((row) => row.in_static_closure)),
  initial_js_css_gzip_bytes: sum(rows), initial_js_gzip_bytes: sum(rows.filter((row) => row.kind === "js")), initial_css_gzip_bytes: sum(rows.filter((row) => row.kind === "css")),
  frontend_default_limit_bytes: 122880, frontend_default_exceeded: sum(rows) > 122880,
  canonical_js_ceiling_bytes: 40960, canonical_js_target_bytes: 30720, canonical_assessment: "requires the owning canonical gate",
};
fs.mkdirSync(path.join(root, path.dirname(output)), { recursive: true });
const bytes = Buffer.from(JSON.stringify(report, null, 2) + "\n");
fs.writeFileSync(path.join(root, output), bytes, { flag: "wx" });
process.stdout.write(JSON.stringify({ output, sha256: sha256(bytes), initial_js_css_gzip_bytes: report.initial_js_css_gzip_bytes, frontend_default_exceeded: report.frontend_default_exceeded }) + "\n");
