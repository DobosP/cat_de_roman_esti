import { defineConfig } from "@playwright/test";
import { existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { isAbsolute, resolve } from "node:path";
import reference from "./playwright.config.mjs";

const root = fileURLToPath(new URL("../", import.meta.url));

function shellQuote(value) {
  if (process.platform === "win32") return `"${value}"`;
  return `'${value.replaceAll("'", "'\\''")}'`;
}

// Browser journeys use the private offline Go planner. The selected server
// handles ordinary game requests; helper answers are never served over HTTP.
export function nativeConfig(runtime, binaryPath) {
  if (!["go", "rust"].includes(runtime)) throw new Error("Unknown native runtime");
  const extension = process.platform === "win32" ? ".exe" : "";
  const relative = runtime === "go"
    ? `build/cat-server${extension}`
    : `rust-backend/target/release/cat-rust-server${extension}`;
  if (process.env.CDR_NATIVE_BINARY && !isAbsolute(process.env.CDR_NATIVE_BINARY)) {
    throw new Error("CDR_NATIVE_BINARY must be an absolute path");
  }
  const binary = resolve(root, process.env.CDR_NATIVE_BINARY || binaryPath || relative);
  if (!existsSync(binary)) throw new Error(`Build the ${runtime} binary first: ${binary}`);
  const baseURL = reference.use.baseURL;
  const address = new URL(baseURL).host;
  const flag = runtime === "go" ? "-listen" : "--listen";
  return defineConfig({
    ...reference,
    testDir: fileURLToPath(new URL("./e2e", import.meta.url)),
    outputDir: process.env.CDR_E2E_OUTPUT_DIR || `./test-results/native-${runtime}`,
    webServer: {
      command: `${shellQuote(binary)} ${flag} ${address}`,
      cwd: root,
      url: `${baseURL}/api/health`,
      reuseExistingServer: false,
      timeout: 120_000,
      gracefulShutdown: { signal: "SIGTERM", timeout: 10_000 },
      env: {
        ...reference.webServer.env,
        CAT_ACCOUNTS_ENABLED: "0",
        CAT_DEBUG: "0",
      },
    },
  });
}
