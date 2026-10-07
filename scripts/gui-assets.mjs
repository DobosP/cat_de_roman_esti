import * as fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { readTarGz } from "../tools/gui-bootstrap-webkit/scripts/kit-sync.mjs";

const root = process.cwd(), mode = process.argv[2];
const hash = (bytes) => createHash("sha256").update(bytes).digest("hex");
function files(directory, prefix = "") {
  return fs.readdirSync(directory, { withFileTypes: true }).sort((a, b) => a.name.localeCompare(b.name)).flatMap((entry) => {
    if (entry.isSymbolicLink()) throw new Error("Asset symlink refused");
    const relative = prefix + entry.name;
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
    if (!item.file || item.file.startsWith("/") || item.file.split("/").some((part) => !part || part === ".." || part === ".")) throw new Error("Unsafe managed asset path");
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
  const proof = JSON.parse(fs.readFileSync("legacy/original-bundle.json"));
  const data = fs.readFileSync(proof.archive);
  if (hash(data) !== proof.sha256 || fs.readFileSync(proof.archive + ".sha256", "utf8") !== `${proof.sha256}  ${path.basename(proof.archive)}\n`) throw new Error("Legacy hash/sidecar mismatch");
  const entries = readTarGz(data), old = [...entries].filter(([, entry]) => entry.type === "file").map(([file, entry]) => ({ file, bytes: entry.data }));
  if (old.length !== proof.files.length || proof.files.some((item) => hash(entries.get(item.path).data) !== item.sha256)) throw new Error("Legacy file proof mismatch");
  const source = path.join(root, "frontend/dist");
  if (!fs.existsSync(path.join(source, ".vite/manifest.json"))) throw new Error("Build managed frontend/dist before asset sync");
  const current = files(source);
  replace(path.join(root, "go-backend/embedfs/dist"), current);
  replace(path.join(root, "go-backend/embedfs/legacy"), old);
  process.stdout.write(JSON.stringify({ schema: 1, dist_files: current.length, legacy_files: old.length, legacy_sha256: proof.sha256 }) + "\n");
} else throw new Error("Expected sync or freeze");
