import { defineConfig } from "@playwright/test";
import { existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { resolve } from "node:path";
import reference from "./playwright.config.mjs";

const root = fileURLToPath(new URL("../", import.meta.url));

function shellQuote(value) {
  if (process.platform === "win32") return `"${value}"`;
  return `'${value.replaceAll("'", "'\\''")}'`;
}

// Python remains an offline fixture oracle in e2e helpers. The serving process
// below is exclusively the selected native binary, with no Python upstream.
export function nativeConfig(runtime, binaryPath) {
  if (!["go", "rust"].includes(runtime)) throw new Error("Unknown native runtime");
  const extension = process.platform === "win32" ? ".exe" : "";
  const relative = runtime === "go"
    ? `build/cat-server${extension}`
    : `rust-backend/target/release/cat-rust-server${extension}`;
  const binary = resolve(root, binaryPath || relative);
  if (!existsSync(binary)) throw new Error(`Build the ${runtime} binary first: ${binary}`);
  const baseURL = reference.use.baseURL;
  const address = new URL(baseURL).host;
  const flag = runtime === "go" ? "-listen" : "--listen";
  return defineConfig({
    ...reference,
    testDir: fileURLToPath(new URL("./e2e", import.meta.url)),
    outputDir: `./test-results/native-${runtime}`,
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
