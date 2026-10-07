import { defineConfig } from "@playwright/test";
import original from "./playwright.config.mjs";

export default defineConfig({
  ...original,
  outputDir: "../.gate/full/browser-output",
  reporter: "json",
  use: { ...original.use, ...(process.env.GATE_APP_URL ? { baseURL: process.env.GATE_APP_URL } : {}) },
  webServer: process.env.GATE_APP_URL ? undefined : original.webServer,
});
