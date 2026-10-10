import assert from "node:assert/strict";
import * as fs from "node:fs";
import path from "node:path";
import { createHash } from "node:crypto";
import { gzipSync, gunzipSync, brotliCompressSync, brotliDecompressSync, constants } from "node:zlib";

const hash = (bytes) => createHash("sha256").update(bytes).digest("hex");
const code = (name) => /\.(?:[cm]?js|css)(?![\s\S])/.test(name);
const sidecar = (name) => /\.(?:gz|br)(?![\s\S])/i.test(name);
const brotliOptions = { params: { [constants.BROTLI_PARAM_QUALITY]: 11, [constants.BROTLI_PARAM_MODE]: constants.BROTLI_MODE_TEXT } };
const encode = (encoding, raw) => encoding === "gzip" ? gzipSync(raw, { level: 9 }) : brotliCompressSync(raw, brotliOptions);
function hasAsciiControl(name) {
  for (let index = 0; index < name.length; index++) {
    const unit = name.charCodeAt(index);
    if (unit <= 0x1f || unit === 0x7f) return true;
  }
  return false;
}
function relative(name) {
  assert.ok(typeof name === "string" && name && !path.isAbsolute(name) && !/[\\:%?#]/.test(name) && !hasAsciiControl(name)
    && name.split("/").every((part) => part && part !== "." && part !== ".." && !/[. ]$/.test(part)), "Confined canonical asset path required");
  return name;
}
function registry() {
  const spelling = new Map(), directories = new Set(), leaves = new Set();
  return (name) => {
    const parts = relative(name).split("/");
    for (let index = 0; index < parts.length; index++) {
      const prefix = parts.slice(0, index + 1).join("/"), folded = prefix.toLowerCase();
      assert.ok(!spelling.has(folded) || spelling.get(folded) === prefix, "Asset path spelling alias refused");
      spelling.set(folded, prefix);
      if (index < parts.length - 1) { assert.ok(!leaves.has(folded), "Asset file/directory alias refused"); directories.add(folded); }
      else { assert.ok(!directories.has(folded), "Asset directory/file alias refused"); leaves.add(folded); }
    }
  };
}
function dense(value) {
  assert.ok(Array.isArray(value), "Dense asset array required");
  for (let index = 0; index < value.length; index++) assert.ok(Object.hasOwn(value, index), "Sparse asset array refused");
  return value;
}
export function manifestCodeFiles(manifest) {
  assert.ok(manifest && typeof manifest === "object" && !Array.isArray(manifest) && Object.keys(manifest).length, "Actual nonempty Vite manifest required");
  const result = new Set(), register = registry();
  for (const item of Object.values(manifest)) {
    assert.ok(item && typeof item === "object" && !Array.isArray(item), "Manifest record required");
    for (const file of [item.file, ...dense(item.css ?? []), ...dense(item.assets ?? [])]) {
      register(file);
      assert.ok(!sidecar(file), "Compressed file cannot become a manifest owner");
      if (code(file)) result.add(file);
    }
  }
  assert.ok(result.size, "Manifest-owned JS/CSS required");
  return [...result].sort((left, right) => left < right ? -1 : left > right ? 1 : 0);
}
export function validatePrecompressedAssets(manifest, records) {
  const owned = manifestCodeFiles(manifest), expected = new Set(owned.flatMap((file) => [file + ".gz", file + ".br"]));
  const indexed = new Map(), register = registry();
  for (const item of dense(records)) {
    assert.ok(item && Buffer.isBuffer(item.bytes), "Actual regular asset bytes required");
    register(item.file); assert.ok(!indexed.has(item.file), "Duplicate asset path refused"); indexed.set(item.file, item.bytes);
    if (sidecar(item.file)) assert.ok(expected.has(item.file), "Orphan, nested or unowned compressed asset refused");
  }
  return owned.map((file) => {
    const raw = indexed.get(file); assert.ok(raw, "Manifest-owned raw asset missing");
    const pair = { file, bytes: raw.length, sha256: hash(raw) };
    for (const [encoding, suffix, decode] of [["gzip", ".gz", gunzipSync], ["br", ".br", brotliDecompressSync]]) {
      const encoded = indexed.get(file + suffix); assert.ok(encoded?.length, "Complete gzip/Brotli asset pair required");
      if (encoding === "gzip") assert.ok(encoded.length >= 10 && encoded[0] === 31 && encoded[1] === 139 && encoded[2] === 8
        && encoded[3] === 0 && encoded.subarray(4, 8).equals(Buffer.alloc(4)), "Deterministic gzip header required");
      const decoded = decode(encoded, { maxOutputLength: raw.length + 1 });
      assert.ok(decoded.equals(raw), "Stale compressed asset differs from finalized raw owner");
      assert.ok(encoded.equals(encode(encoding, raw)), "Compressed representation differs from deterministic producer bytes");
      pair[encoding] = { file: file + suffix, bytes: encoded.length, sha256: hash(encoded) };
    }
    return pair;
  });
}
function directory(name) {
  assert.ok(path.isAbsolute(name) && path.resolve(name) === name, "Absolute canonical output directory required");
  let cursor = path.parse(name).root;
  for (const part of name.slice(cursor.length).split(path.sep)) {
    cursor = path.join(cursor, part); const info = fs.lstatSync(cursor);
    assert.ok(info.isDirectory() && !info.isSymbolicLink() && fs.realpathSync(cursor) === cursor, "Regular output ancestry required");
  }
}
function outputFiles(root, prefix = "") {
  directory(prefix ? path.join(root, prefix.slice(0, -1)) : root);
  return fs.readdirSync(path.join(root, prefix), { withFileTypes: true }).sort((a, b) => a.name.localeCompare(b.name)).flatMap((entry) => {
    const file = relative(prefix + entry.name), absolute = path.join(root, file);
    assert.ok(!entry.isSymbolicLink(), "Asset symlink refused");
    if (entry.isDirectory()) return outputFiles(root, file + "/");
    assert.ok(entry.isFile(), "Nonregular asset refused");
    const before = fs.lstatSync(absolute, { bigint: true }), fd = fs.openSync(absolute, fs.constants.O_RDONLY | fs.constants.O_NOFOLLOW);
    try {
      const opened = fs.fstatSync(fd, { bigint: true }), bytes = fs.readFileSync(fd), after = fs.fstatSync(fd, { bigint: true });
      assert.ok(opened.isFile() && opened.dev === before.dev && opened.ino === before.ino
        && ["dev", "ino", "mode", "size", "mtimeNs", "ctimeNs"].every((key) => opened[key] === after[key])
        && BigInt(bytes.length) === after.size, "Raw asset changed during acquisition");
      return [{ file, bytes, identity: after }];
    } finally { fs.closeSync(fd); }
  });
}
function writeSidecar(root, file, bytes) {
  const target = path.join(root, relative(file)), parent = path.dirname(target); directory(parent);
  const before = fs.lstatSync(parent), parentfd = fs.openSync(parent, fs.constants.O_RDONLY | fs.constants.O_DIRECTORY | fs.constants.O_NOFOLLOW);
  try {
    const opened = fs.fstatSync(parentfd); assert.ok(opened.dev === before.dev && opened.ino === before.ino, "Output directory identity changed");
    const fd = fs.openSync("/proc/self/fd/" + parentfd + "/" + path.basename(target), fs.constants.O_WRONLY | fs.constants.O_CREAT | fs.constants.O_EXCL | fs.constants.O_NOFOLLOW, 0o644);
    try { fs.writeFileSync(fd, bytes); fs.fsyncSync(fd); } finally { fs.closeSync(fd); }
    fs.fsyncSync(parentfd);
  } finally { fs.closeSync(parentfd); }
}
export function emitPrecompressedAssets(root) {
  const before = outputFiles(root), indexed = new Map(before.map((item) => [item.file, item]));
  assert.ok(indexed.has("index.html") && indexed.has(".vite/manifest.json"), "Finalized Vite HTML and manifest required");
  assert.ok(before.every((item) => !sidecar(item.file)), "Fresh finalized output must not contain existing sidecars");
  const manifest = JSON.parse(indexed.get(".vite/manifest.json").bytes.toString("utf8"));
  const generated = manifestCodeFiles(manifest).flatMap((file) => {
    const owner = indexed.get(file); assert.ok(owner, "Final manifest-owned raw asset required");
    return [{ file: file + ".gz", bytes: encode("gzip", owner.bytes) },
      { file: file + ".br", bytes: encode("br", owner.bytes) }];
  });
  // Validate every in-memory pair before writing any compressed representation.
  validatePrecompressedAssets(manifest, [...before, ...generated]);
  for (const item of generated) writeSidecar(root, item.file, item.bytes);
  const after = outputFiles(root), actual = new Map(after.map((item) => [item.file, item]));
  assert.deepEqual([...actual.keys()].sort((left, right) => left < right ? -1 : left > right ? 1 : 0), [...before, ...generated].map((item) => item.file).sort((left, right) => left < right ? -1 : left > right ? 1 : 0), "Final output membership changed");
  for (const item of before) {
    const kept = actual.get(item.file); assert.ok(kept.bytes.equals(item.bytes), "Raw output bytes changed during compression");
    assert.ok(["dev", "ino", "mode", "size", "mtimeNs", "ctimeNs"].every((key) => kept.identity[key] === item.identity[key]), "Raw output metadata changed during compression");
  }
  return validatePrecompressedAssets(manifest, after);
}

// The existing assets-sync copy operation, shared so its complete-file behavior
// can be exercised without weakening the actual wrapper/Docker context checks.
export function copyManagedAssetFiles(destination, source) {
  fs.mkdirSync(destination, { recursive: true });
  for (const name of fs.readdirSync(destination)) {
    if (name !== ".keep") fs.rmSync(path.join(destination, name), { recursive: true, force: true });
  }
  for (const item of source) {
    relative(item.file);
    const file = path.join(destination, item.file);
    fs.mkdirSync(path.dirname(file), { recursive: true }); fs.writeFileSync(file, item.bytes);
  }
}
