import * as fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { readTarGz } from "../tools/gui-bootstrap-webkit/scripts/kit-sync.mjs";
import { DEFAULT_INITIAL_GZIP_LIMIT_KIB, assertRomanianFontSubsets, collectInitialBundleFiles, measureGzipFiles } from "../frontend/scripts/check-bundle-budget.mjs";

const root = process.cwd(), mode = process.argv[2];
const hash = (bytes) => createHash("sha256").update(bytes).digest("hex");
const frozenLegacySHA256 = "742bb11130fa2bf52ba5c64cb9cfd452f7d8ac3a4fd9dc6d77e8064a6b8fef65";
function safeRelative(value) {
  if (typeof value !== "string" || !value || value.startsWith("/") || /[\\:\x00-\x1f\x7f]/.test(value)
    || value.split("/").some((part) => !part || part === "." || part === "..")) throw new Error("Unsafe managed asset path");
  return value;
}
function confined(relative, missing = false) {
  const parts = safeRelative(relative).split("/");
  let cursor = root;
  for (const [index, part] of parts.entries()) {
    cursor = path.join(cursor, part);
    let stat;
    try { stat = fs.lstatSync(cursor); }
    catch (error) { if (missing && error.code === "ENOENT") continue; throw error; }
    if (stat.isSymbolicLink() || (!stat.isDirectory() && !stat.isFile())
      || (index < parts.length - 1 && !stat.isDirectory())) throw new Error("Nonregular managed asset path");
  }
  return cursor;
}
function files(directory, prefix = "") {
  if (!fs.lstatSync(directory).isDirectory() || fs.lstatSync(directory).isSymbolicLink()) throw new Error("Asset directory refused");
  return fs.readdirSync(directory, { withFileTypes: true }).sort((a, b) => a.name.localeCompare(b.name)).flatMap((entry) => {
    if (entry.isSymbolicLink()) throw new Error("Asset symlink refused");
    const relative = safeRelative(prefix + entry.name);
    if (entry.isDirectory()) return files(path.join(directory, entry.name), relative + "/");
    if (!entry.isFile()) throw new Error("Nonregular asset refused");
    return [{ file: relative, bytes: fs.readFileSync(path.join(directory, entry.name)) }];
  });
}
function replace(destination, source) {
  fs.mkdirSync(destination, { recursive: true });
  for (const name of fs.readdirSync(destination)) {
    if (name !== ".keep") fs.rmSync(path.join(destination, name), { recursive: true, force: true });
  }
  for (const item of source) {
    safeRelative(item.file);
    const file = path.join(destination, item.file);
    fs.mkdirSync(path.dirname(file), { recursive: true }); fs.writeFileSync(file, item.bytes);
  }
}
if (mode === "freeze") {
  const source = path.join(root, "cat_de_roman_esti/web/static"), original = files(source);
  if (original.length !== 30 || !original.some((item) => item.file === "index.html") || !original.some((item) => item.file === ".vite/manifest.json")) throw new Error("Exact original thirty-file bundle required before source retirement");
  const sha = process.env.GATE_SHA;
  if (!/^[a-f0-9]{40}$/.test(sha)) throw new Error("Wrapper SHA required");
  fs.mkdirSync("legacy", { recursive: true });
  const archive = `legacy/cat_de_roman_esti-legacy-${sha}.tgz`;
  const child = spawnSync("tar", ["--format=ustar", "--sort=name", "--mtime=@0", "--owner=0", "--group=0", "--numeric-owner", "-czf", path.join(root, archive), "-C", source, ...original.map((item) => item.file)], { encoding: "utf8" });
  if (child.status !== 0) throw new Error(`Actual legacy tar failed: ${child.stderr}`);
  const data = fs.readFileSync(archive), unpacked = readTarGz(data);
  if (unpacked.size !== original.length || original.some((item) => !unpacked.get(item.file)?.data.equals(item.bytes))) throw new Error("Frozen archive differs from original file bytes");
  fs.writeFileSync(archive + ".sha256", `${hash(data)}  ${path.basename(archive)}\n`);
  const proof = { schema: 1, sha, tree_sha256: process.env.GATE_TREE_SHA256, toolchain_digest: process.env.TOOLCHAIN_DIGEST, archive, sha256: hash(data), files: original.map((item) => ({ path: item.file, bytes: item.bytes.length, sha256: hash(item.bytes) })) };
  fs.writeFileSync("legacy/original-bundle.json", JSON.stringify(proof, null, 2) + "\n");
  process.stdout.write(JSON.stringify(proof) + "\n");
} else if (mode === "sync") {
  const proof = JSON.parse(fs.readFileSync(confined("legacy/original-bundle.json")));
  if (proof.schema !== 1 || proof.sha256 !== frozenLegacySHA256 || !proof.archive?.startsWith("legacy/")
    || !Array.isArray(proof.files) || proof.files.length !== 30) throw new Error("Exact frozen legacy proof required");
  const data = fs.readFileSync(confined(proof.archive));
  if (hash(data) !== frozenLegacySHA256 || fs.readFileSync(confined(proof.archive + ".sha256"), "utf8") !== `${proof.sha256}  ${path.basename(proof.archive)}\n`) throw new Error("Legacy hash/sidecar mismatch");
  const entries = readTarGz(data), old = [...entries].map(([file, entry]) => {
    safeRelative(file);
    if (entry.type !== "file") throw new Error("Legacy archive must contain only regular members");
    return { file, bytes: entry.data };
  });
  const proved = new Set();
  if (old.length !== 30 || proof.files.some((item) => {
    safeRelative(item.path);
    const entry = entries.get(item.path), duplicate = proved.has(item.path);
    proved.add(item.path);
    return duplicate || !entry || entry.data.length !== item.bytes || hash(entry.data) !== item.sha256;
  })) throw new Error("Legacy file proof mismatch");
  const source = confined("frontend/dist");
  const current = files(source), indexed = new Map(current.map((item) => [item.file, item.bytes]));
  if (!indexed.has("index.html") || !indexed.has(".vite/manifest.json")) throw new Error("Build managed frontend/dist before asset sync");
  const manifest = JSON.parse(indexed.get(".vite/manifest.json"));
  if (!manifest["index.html"]?.isEntry) throw new Error("Managed index entry required");
  for (const entry of Object.values(manifest)) {
    for (const file of [entry.file, ...entry.css ?? [], ...entry.assets ?? []]) {
      safeRelative(file);
      if (!indexed.has(file)) throw new Error(`Missing managed manifest asset: ${file}`);
    }
    for (const key of [...entry.imports ?? [], ...entry.dynamicImports ?? []]) {
      if (!manifest[key]) throw new Error(`Missing managed manifest import: ${key}`);
    }
  }
  assertRomanianFontSubsets(manifest);
  const initialGzipBytes = measureGzipFiles(source, collectInitialBundleFiles(manifest)).reduce((sum, item) => sum + item.bytes, 0);
  if (initialGzipBytes > DEFAULT_INITIAL_GZIP_LIMIT_KIB * 1024) throw new Error("Managed initial bundle exceeds unchanged 120 KiB ceiling");
  const destinations = ["go-backend/embedfs/dist", "go-backend/embedfs/legacy"].map((relative) => confined(relative, true));
  // Check both existing trees before mutating either managed destination.
  for (const destination of destinations) if (fs.existsSync(destination)) files(destination);
  replace(destinations[0], current); replace(destinations[1], old);
  const rows = (items) => items.map((item) => ({ path: item.file, bytes: item.bytes.length, sha256: hash(item.bytes) }));
  process.stdout.write(JSON.stringify({ schema: 1, sha: process.env.GATE_SHA, tree_sha256: process.env.GATE_TREE_SHA256,
    toolchain_digest: process.env.TOOLCHAIN_DIGEST, dist_files: current.length, legacy_files: old.length,
    legacy_sha256: proof.sha256, manifest_sha256: hash(indexed.get(".vite/manifest.json")), initial_gzip_bytes: initialGzipBytes,
    dist: rows(current), legacy: rows(old) }) + "\n");
} else throw new Error("Expected sync or freeze");
