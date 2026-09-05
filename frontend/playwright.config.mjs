import { defineConfig, devices } from "@playwright/test";
import { fileURLToPath } from "node:url";

const root = fileURLToPath(new URL("../", import.meta.url));
const port = process.env.CDR_E2E_PORT || "8138";
const baseURL = `http://127.0.0.1:${port}`;

export default defineConfig({
  testDir: "./e2e",
  outputDir: process.env.CDR_E2E_OUTPUT_DIR || "./test-results",
  fullyParallel: false,
  workers: 1,
  retries: 0,
  timeout: 45_000,
  expect: { timeout: 10_000 },
  reporter: "list",
  use: {
    baseURL,
    locale: "ro-RO",
    timezoneId: "Europe/Bucharest",
    reducedMotion: "reduce",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [
    { name: "desktop", use: { ...devices["Desktop Chrome"] } },
    { name: "mobile", use: { ...devices["Pixel 7"] } },
  ],
  webServer: {
    command: `python3 -m cat_de_roman_esti.web --host 127.0.0.1 --port ${port} --log-level warning`,
    cwd: root,
    url: `${baseURL}/api/health`,
    reuseExistingServer: false,
    timeout: 120_000,
    env: {
      PYTHONPATH: root,
      CAT_ACCOUNTS_ENABLED: "0",
      CAT_DEBUG: "1",
      ROEDU_API_URL: "",
      ROEDU_API_KEY: "",
    },
  },
});
