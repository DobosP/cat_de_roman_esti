// Private test-process helper; no solution data enters the product bundle.
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { isAbsolute } from "node:path";

const root = fileURLToPath(new URL("../../", import.meta.url));
const binary = process.env.CDR_BROWSER_PLAN_BINARY
  || fileURLToPath(new URL("../../build/cat-browser-plan", import.meta.url))
    + (process.platform === "win32" ? ".exe" : "");

if (!isAbsolute(binary)) throw new Error("CDR_BROWSER_PLAN_BINARY must be an absolute path");

export function nativePlan(args) {
  return JSON.parse(execFileSync(binary, args, {
    cwd: root,
    encoding: "utf8",
    timeout: 60_000,
    maxBuffer: 4 * 1024 * 1024,
    env: { ...process.env, CAT_ACCOUNTS_ENABLED: "0", CAT_SUBMISSIONS_ENABLED: "0" },
  }));
}
