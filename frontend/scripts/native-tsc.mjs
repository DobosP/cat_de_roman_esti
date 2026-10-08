import { spawnSync } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { nativeCompiler } from "./compiler-runtime.mjs";
const frontend = path.resolve(fileURLToPath(new URL("../", import.meta.url)));
const binding = nativeCompiler(frontend);
const child = spawnSync(binding.executable, process.argv.slice(2), { cwd: frontend, stdio: "inherit" });
if (child.error) throw child.error;
process.exitCode = child.status ?? 1;
