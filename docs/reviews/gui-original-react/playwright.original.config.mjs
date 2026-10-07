import { defineConfig, devices } from "@playwright/test";
import { fileURLToPath } from "node:url";

const root = fileURLToPath(new URL("../", import.meta.url));
const port = 8138;
if (!process.env.CDR_NATIVE_BINARY || !process.env.CDR_BROWSER_PLAN_BINARY) {
  throw new Error("Original qualification requires binaries built by the pinned repo hook");
}
export default defineConfig({
  testDir: "./e2e/original",
  outputDir: "../.gate/gen/original/browser-output",
  fullyParallel: false,
  workers: 1,
  retries: 0,
  timeout: 45_000,
  expect: { timeout: 10_000 },
  reporter: [["./e2e/original/reporter.mjs"]],
  projects: [{ name: "original-motion-on", use: { ...devices["Desktop Chrome"] } }],
  use: {
    baseURL: `http://127.0.0.1:${port}`,
    locale: "ro-RO",
    timezoneId: "Europe/Bucharest",
    reducedMotion: "no-preference",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  webServer: {
    command: `'${process.env.CDR_NATIVE_BINARY}' -listen 127.0.0.1:${port}`,
    cwd: root,
    url: `http://127.0.0.1:${port}/api/health`,
    reuseExistingServer: false,
    timeout: 120_000,
    env: { CAT_ACCOUNTS_ENABLED: "0", CAT_SUBMISSIONS_ENABLED: "0", ROEDU_API_URL: "", ROEDU_API_KEY: "" },
  },
});
