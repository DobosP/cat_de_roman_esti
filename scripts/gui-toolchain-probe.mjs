import * as fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
import { pathToFileURL } from "node:url";
import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { nativeCompiler, parserBinding } from "../frontend/scripts/compiler-runtime.mjs";

const root = process.cwd(), frontend = path.join(root, "frontend");
const output = path.join(root, ".gate/deps/toolchain-probe");
fs.mkdirSync(output, { recursive: true });
const sha = (bytes) => createHash("sha256").update(bytes).digest("hex");
const lock = JSON.parse(fs.readFileSync(path.join(root, "versions.lock.json")));
const selected = new Map(lock.tools.map((item) => [item.tool, item]));
const checks = [], commands = [], packages = [];
function check(name, action) {
  try { checks.push({ name, status: "pass", observation: action() }); }
  catch (error) { checks.push({ name, status: "fail", reason: error.message }); }
}
function packageInfo(name, expected) {
  const file = path.join(frontend, "node_modules", name, "package.json");
  const bytes = fs.readFileSync(file), pkg = JSON.parse(bytes);
  const item = { name: pkg.name, version: pkg.version, path: path.relative(root, file), sha256: sha(bytes) };
  packages.push(item);
  if (pkg.name !== name || pkg.version !== expected) throw new Error(`Installed package differs: ${name}: ${pkg.version} expected ${expected}`);
  return item;
}
function command(name, binary, args) {
  const started = new Date().toISOString();
  const result = spawnSync(binary, args, { cwd: frontend, encoding: "utf8", maxBuffer: 16 * 1024 * 1024 });
  const stdout = `${name}.stdout.log`, stderr = `${name}.stderr.log`;
  fs.writeFileSync(path.join(output, stdout), result.stdout || "");
  fs.writeFileSync(path.join(output, stderr), result.stderr || "");
  commands.push({ name, command: binary, args, started, finished: new Date().toISOString(), exit_code: result.status ?? -1,
    stdout: { path: `.gate/deps/toolchain-probe/${stdout}`, sha256: sha(result.stdout || "") },
    stderr: { path: `.gate/deps/toolchain-probe/${stderr}`, sha256: sha(result.stderr || "") } });
  if (result.status !== 0) throw new Error(`${name} failed (${result.status}): ${result.stderr || result.error?.message || ""}`);
  return result.stdout;
}
for (const name of ["typescript", "@typescript/typescript6", "motion", "framer-motion", "oxlint", "oxlint-tsgolint", "@ast-grep/cli"])
  check(`installed:${name}`, () => packageInfo(name, selected.get(name).version));
check("installed:old-active-ui", () => packageInfo("@roedu/ui", "0.3.0"));
check("installed:declared-web-kit", () => packageInfo("@roedu/web-kit", "0.1.4"));
check("actual-native-tsc-version", () => {
  const text = command("tsc-version", nativeCompiler(frontend).executable, ["--version"]);
  if (text.trim() !== `Version ${selected.get("typescript").version}`) throw new Error("Actual tsc version differs from selected compiler");
  return text.trim();
});
check("actual-oxlint-version", () => command("oxlint-version", path.join(frontend, "node_modules/.bin/oxlint"), ["--version"]).trim());
check("actual-oxlint-rules", () => ({ bytes: command("oxlint-rules", path.join(frontend, "node_modules/.bin/oxlint"), ["--rules"]).length }));
check("actual-consumer-oxlint-config", () => ({ bytes: command("oxlint-print-config", path.join(frontend, "node_modules/.bin/oxlint"), ["--config", "oxlint.config.json", "--print-config"]).length }));
let jsApi;
try {
  const require = createRequire(path.join(frontend, "package.json"));
  const file = require.resolve("typescript"), loaded = await import(pathToFileURL(file).href), api = loaded.default ?? loaded;
  const functions = Object.fromEntries(["createProgram", "getPreEmitDiagnostics", "transpileModule", "createSourceFile", "readConfigFile"].map((name) => [name, typeof api[name]]));
  jsApi = { status: "observed", entry: path.relative(root, file), sha256: sha(fs.readFileSync(file)), version: api.version ?? null, functions };
  // The captured predecessor genuinely proved these functions unavailable.
  // This remains an observation, while the explicit approved API below is now
  // mandatory for AST/transpile services. Native7 remains the checked CLI.
  checks.push({ name: "actual-ts7-js-api-observation", status: "pass", observation: jsApi });
} catch (error) {
  jsApi = { status: "import-failed", code: error.code ?? null, reason: error.message };
  checks.push({ name: "actual-ts7-js-api-observation", status: "fail", observation: jsApi, reason: error.message });
}
let parserApi;
try {
  const require = createRequire(path.join(frontend, "package.json"));
  const file = require.resolve("@typescript/typescript6"), loaded = await import(pathToFileURL(file).href), api = loaded.default ?? loaded;
  const functions = Object.fromEntries(["createProgram", "getPreEmitDiagnostics", "transpileModule", "createSourceFile", "readConfigFile"].map((name) => [name, typeof api[name]]));
  parserApi = { name: "@typescript/typescript6", entry: path.relative(root, file), sha256: sha(fs.readFileSync(file)), version: api.version ?? null, functions,
    role: "Explicit approved AST/transpilation API; never authoritative native7 typecheck/declaration diagnostics" };
  const missing = Object.entries(functions).filter(([, type]) => type !== "function").map(([name]) => name);
  const binding = parserBinding(frontend, api);
  parserApi.binding = binding;
  const matches = binding.package.version === selected.get("@typescript/typescript6").version;
  checks.push({ name: "actual-approved-parser-api", status: matches && missing.length === 0 ? "pass" : "fail", observation: parserApi,
    ...(missing.length || !matches ? { reason: `Required approved API version/functions differ: ${missing.join(", ")}` } : {}) });
} catch (error) {
  parserApi = { status: "import-failed", code: error.code ?? null, reason: error.message };
  checks.push({ name: "actual-approved-parser-api", status: "fail", observation: parserApi, reason: error.message });
}
const report = { schema: 1, scope: "Actual installed normalized-toolchain capability probe; no original/canonical/UI adoption claim",
  sha: process.env.GATE_SHA, tree_sha256: process.env.GATE_TREE_SHA256, toolchain_digest: process.env.TOOLCHAIN_DIGEST,
  checks, packages, commands, js_api: jsApi, parser_api: parserApi, status: checks.every((item) => item.status === "pass") ? "pass" : "fail" };
fs.writeFileSync(path.join(output, "report.json"), JSON.stringify(report, null, 2) + "\n");
process.stdout.write(JSON.stringify(report) + "\n");
process.exitCode = report.status === "pass" ? 0 : 1;
