import { defineConfig } from "@playwright/test";
import { readFileSync } from "node:fs";
import { guiBrowserWorkers } from "../scripts/gui-browser-workers.mjs";
import original from "./playwright.config.mjs";

export default defineConfig({
  ...original,
  outputDir: "../.gate/full/browser-output",
  reporter: "json",
  workers: process.env.GATE_APP_URL
    ? guiBrowserWorkers(process.env, readFileSync(new URL("../.gate.env", import.meta.url), "utf8"))
    : original.workers,
  use: { ...original.use, ...(process.env.GATE_APP_URL ? { baseURL: process.env.GATE_APP_URL } : {}) },
  webServer: process.env.GATE_APP_URL ? undefined : original.webServer,
});
