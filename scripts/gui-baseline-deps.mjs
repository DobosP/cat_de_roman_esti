import * as fs from "node:fs";
import path from "node:path";
import { createHash } from "node:crypto";
import { spawnSync } from "node:child_process";

// Missing dependency output is a setup problem, never a baseline exemption.
export function ensureBaselineDependencies(root, io = { fs, spawnSync, env: process.env }) {
  const directory = path.join(root, "tools/gui-baseline-quality");
  const required = ["axe-core/axe.min.js", "axe-core/package.json",
    "web-vitals/dist/web-vitals.iife.js", "web-vitals/package.json"];
  if (required.every((file) => io.fs.existsSync(path.join(directory, "node_modules", file)))) return;
  if (root !== "/work" || !/^[0-9a-f]{40}$/.test(io.env.GATE_SHA || "")
    || !/^[0-9a-f]{64}$/.test(io.env.GATE_TREE_SHA256 || "")) {
    throw new Error("Missing baseline dependencies require the managed Linux runner");
  }
  const digest = (file) => createHash("sha256").update(io.fs.readFileSync(path.join(directory, file))).digest("hex");
  const files = ["package.json", "package-lock.json"], before = files.map(digest);
  const result = io.spawnSync("npm", ["ci", "--ignore-scripts", "--include=dev", "--no-audit", "--no-fund"], {
    cwd: directory, env: io.env, encoding: "utf8", timeout: 120000, maxBuffer: 4 * 1024 * 1024,
  });
  // Baseline stdout is a JSON interface. Installation diagnostics belong on stderr.
  if (result.stdout) process.stderr.write(result.stdout);
  if (result.stderr) process.stderr.write(result.stderr);
  if (files.some((file, index) => digest(file) !== before[index])) throw new Error("Baseline setup changed a committed dependency input");
  if (result.error || result.status !== 0) throw new Error("Locked baseline dependency installation failed", { cause: result.error });
  if (!required.every((file) => io.fs.existsSync(path.join(directory, "node_modules", file)))) {
    throw new Error("Locked baseline dependency output incomplete");
  }
  // Exact library version refusals remain in gui-baseline.mjs, including when
  // existing files are present: wrong versions never trigger a repair or fallback.
}
