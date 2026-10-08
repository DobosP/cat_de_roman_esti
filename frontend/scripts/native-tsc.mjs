import { spawnSync } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { nativeCompiler } from "./compiler-runtime.mjs";
const frontend = path.resolve(fileURLToPath(new URL("../", import.meta.url)));
const binding = nativeCompiler(frontend);
const args = process.argv.slice(2);
const selectedProject = args.some((arg) => arg === "--project" || arg === "-p" || arg.startsWith("--project=") || arg.startsWith("-p="));
const projects = selectedProject ? [args] : ["tsconfig.json", "tsconfig.tools.json"].map((project) => ["--project", project, ...args]);
for (const projectArgs of projects) {
  const child = spawnSync(binding.executable, projectArgs, { cwd: frontend, stdio: "inherit" });
  if (child.error) throw child.error;
  if (child.status !== 0) { process.exitCode = child.status ?? 1; break; }
}
