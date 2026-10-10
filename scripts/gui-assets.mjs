import * as fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { readTarGz } from "../tools/gui-bootstrap-webkit/scripts/kit-sync.mjs";
import { DEFAULT_INITIAL_GZIP_LIMIT_KIB, assertRomanianFontSubsets, collectInitialBundleFiles, measureGzipFiles } from "../frontend/scripts/check-bundle-budget.mjs";
import { validatePrecompressedAssets, copyManagedAssetFiles as replace } from "../frontend/scripts/gui-precompressed-assets.mjs";

const root = process.cwd(), mode = process.argv[2];
const hash = (bytes) => createHash("sha256").update(bytes).digest("hex");
const frozenLegacySHA256 = "742bb11130fa2bf52ba5c64cb9cfd452f7d8ac3a4fd9dc6d77e8064a6b8fef65";
const managedOutputs = ["frontend/dist", "go-backend/embedfs/dist", "go-backend/embedfs/build/dist"];
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
function currentContext(required = false) {
  if (!fs.existsSync(path.join(root, ".gate/wrapper-current.json"))) {
    if (required) throw new Error("Actual wrapper context required for managed output preparation");
    if (process.platform !== "linux" || root !== "/build") throw new Error("Asset sync requires the owning wrapper or Dockerfile.gui build root");
    return null; // Dockerfile.gui builds and syncs before its explicit identity bake.
  }
  const descriptorBytes = fs.readFileSync(confined(".gate/wrapper-current.json"));
  const descriptor = JSON.parse(descriptorBytes);
  if (process.platform !== "linux" || root !== "/work" || fs.realpathSync(root) !== root || descriptor.schema !== 1
    || !["unit", "full", "gen", "build"].includes(descriptor.target)
    || !/^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$/.test(descriptor.invocation ?? "")
    || descriptor.sha !== process.env.GATE_SHA || descriptor.tree_sha256 !== process.env.GATE_TREE_SHA256
    || descriptor.toolchain_digest !== process.env.TOOLCHAIN_DIGEST
    || descriptor.config_path !== `.gate/${descriptor.target}/wrapper-kit-config.json`
    || !fs.readFileSync(confined(`.gate/${descriptor.target}/wrapper-current.json`)).equals(descriptorBytes)) throw new Error("Current managed output context differs");
  const configBytes = fs.readFileSync(confined(descriptor.config_path)), captured = JSON.parse(configBytes);
  if (hash(configBytes) !== descriptor.config_file_sha256
    || ["schema", "target", "sha", "tree_sha256", "toolchain_digest", "config_sha256"].some((key) => captured[key] !== descriptor[key])
    || captured.config?.role !== "consumer" || captured.config.app !== "cat_de_roman_esti"
    || hash(JSON.stringify(captured.config)) !== descriptor.config_sha256) throw new Error("Current managed output config differs");
  return { ...descriptor, descriptor_sha256: hash(descriptorBytes) };
}
function emit(context, name, report) {
  const bytes = JSON.stringify(report, null, 2) + "\n";
  if (context) {
    const file = confined(`.gate/${context.target}/managed-assets/${name}.json`, true);
    fs.mkdirSync(path.dirname(file), { recursive: true }); fs.writeFileSync(file, bytes);
  }
  process.stdout.write(bytes);
}
function requirePrepared(context) {
  if (!context) return;
  const receipt = JSON.parse(fs.readFileSync(confined(`.gate/${context.target}/managed-assets/prepare.json`)));
  if (receipt.schema !== 1 || receipt.status !== "prepared" || JSON.stringify(receipt.context) !== JSON.stringify(context)
    || JSON.stringify(receipt.outputs.map((item) => item.path)) !== JSON.stringify(managedOutputs)) throw new Error("Fresh owning managed output preparation required");
}
function clearGenerated(relative) {
  const destination = confined(relative, true);
  if (fs.existsSync(destination)) {
    const previous = files(destination);
    if (previous.some((item) => item.file === ".keep" && item.bytes.length !== 0)) throw new Error("Managed scaffold must be empty");
  }
  fs.mkdirSync(destination, { recursive: true, mode: 0o700 });
  for (const name of fs.readdirSync(destination)) {
    if (name !== ".keep") fs.rmSync(path.join(destination, name), { recursive: true });
  }
  if (relative.startsWith("go-backend/embedfs/") && !fs.existsSync(path.join(destination, ".keep"))) {
    // The trusted mirror excludes dist directories, including source .keep.
    // This empty compile scaffold is never a manifest or qualifying UI input.
    fs.writeFileSync(path.join(destination, ".keep"), "", { flag: "wx", mode: 0o600 });
  }
}
function currentBundle() {
  const source = confined("frontend/dist"), current = files(source);
  const indexed = new Map(current.map((item) => [item.file, item.bytes]));
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
  const fonts = assertRomanianFontSubsets(manifest);
  validatePrecompressedAssets(manifest, current);
  const eagerRoots = ["src/components/AccountBar.tsx"];
  const initialGzipBytes = measureGzipFiles(source, collectInitialBundleFiles(manifest)).reduce((sum, item) => sum + item.bytes, 0);
  const eagerStartupGzipBytes = measureGzipFiles(source, collectInitialBundleFiles(manifest, { eagerRoots })).reduce((sum, item) => sum + item.bytes, 0);
  return { current, indexed, fonts, eagerRoots, initialGzipBytes, eagerStartupGzipBytes };
}
const rows = (items) => items.map((item) => ({ path: item.file, bytes: item.bytes.length, sha256: hash(item.bytes) }));
if (mode === "prepare") {
  // Parent capture must close before this owning gate is invoked. Only the
  // fixed generated trees are cleared; frozen original/legacy bytes stay intact.
  const context = currentContext(true);
  for (const name of ["prepare", "inventory", "sync"]) {
    const oldReport = confined(`.gate/${context.target}/managed-assets/${name}.json`, true);
    if (fs.existsSync(oldReport)) {
      if (!fs.lstatSync(oldReport).isFile()) throw new Error("Managed report must be regular");
      fs.rmSync(oldReport);
    }
  }
  const prepared = managedOutputs.map((relative) => {
    const destination = confined(relative, true);
    const previous = fs.existsSync(destination) ? files(destination) : [];
    if (previous.some((item) => item.file === ".keep" && item.bytes.length !== 0)) throw new Error("Managed scaffold must be empty");
    return { relative, destination, previous };
  });
  for (const { relative } of prepared) clearGenerated(relative);
  emit(context, "prepare", { schema: 1, status: "prepared", qualified: false, context,
    outputs: prepared.map(({ relative, previous }) => ({ path: relative, removed: rows(previous.filter((item) => item.file !== ".keep")), scaffold_preserved: relative.startsWith("go-backend/embedfs/") })) });
} else if (mode === "inventory") {
  const context = currentContext(true); requirePrepared(context);
  const { current, indexed, fonts, eagerRoots, initialGzipBytes, eagerStartupGzipBytes } = currentBundle();
  emit(context, "inventory", { schema: 1, status: "measured", qualified: false, context, eager_roots: eagerRoots,
    manifest_sha256: hash(indexed.get(".vite/manifest.json")), initial_gzip_bytes: initialGzipBytes,
    initial_scope: "entry-recursive-static-JS-CSS", eager_startup_gzip_bytes: eagerStartupGzipBytes,
    eager_startup_scope: "entry-and-mandatory-AccountBar-recursive-static-JS-CSS",
    limit_bytes: DEFAULT_INITIAL_GZIP_LIMIT_KIB * 1024, within_budget: eagerStartupGzipBytes <= DEFAULT_INITIAL_GZIP_LIMIT_KIB * 1024,
    font_sources: fonts, files: rows(current) });
} else if (mode === "freeze") {
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
  const context = currentContext(); requirePrepared(context);
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
  const { current, indexed, initialGzipBytes, eagerStartupGzipBytes, eagerRoots } = currentBundle();
  if (eagerStartupGzipBytes > DEFAULT_INITIAL_GZIP_LIMIT_KIB * 1024) throw new Error("Managed eager startup bundle exceeds unchanged 120 KiB ceiling");
  const destinations = ["go-backend/embedfs/dist", "go-backend/embedfs/legacy"].map((relative) => confined(relative, true));
  // Check both existing trees before mutating either managed destination.
  for (const destination of destinations) if (fs.existsSync(destination)) files(destination);
  // A standalone sync also invalidates any earlier identity. The owning caller
  // must bake metadata from the newly synced manifest before server compilation.
  clearGenerated("go-backend/embedfs/build/dist");
  replace(destinations[0], current); replace(destinations[1], old);
  emit(context, "sync", { schema: 1, sha: process.env.GATE_SHA, tree_sha256: process.env.GATE_TREE_SHA256,
    toolchain_digest: process.env.TOOLCHAIN_DIGEST, dist_files: current.length, legacy_files: old.length,
    legacy_sha256: proof.sha256, manifest_sha256: hash(indexed.get(".vite/manifest.json")), initial_gzip_bytes: initialGzipBytes,
    initial_scope: "entry-recursive-static-JS-CSS", eager_startup_gzip_bytes: eagerStartupGzipBytes, eager_roots: eagerRoots,
    eager_startup_scope: "entry-and-mandatory-AccountBar-recursive-static-JS-CSS",
    dist: rows(current), legacy: rows(old) });
} else throw new Error("Expected prepare, inventory, sync or freeze");
