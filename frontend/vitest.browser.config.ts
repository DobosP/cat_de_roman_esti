import { defineConfig } from "vitest/config";
import { playwright } from "@vitest/browser-playwright";
import preact from "@preact/preset-vite";

// A separate source-test server: never alter the production Vite build graph,
// compression plugin, document CSP or original Go/Playwright baseline runner.
export default defineConfig({
  // Same published core-v1.11 Vitest5/Oxc/Preact transform boundary.
  oxc: { jsx: { runtime: "automatic", importSource: "preact" } },
  plugins: [preact({ reactAliasesEnabled: false })],
  resolve: { dedupe: ["preact"] },
  optimizeDeps: {
    include: ["preact", "preact/hooks", "preact/jsx-runtime", "preact/jsx-dev-runtime", "preact-render-to-string", "motion", "motion/mini"],
    rolldownOptions: { transform: { jsx: { runtime: "automatic", importSource: "preact" } } },
  },
  cacheDir: ".vitest/vite",
  test: {
    include: ["tests/browser/preact-contracts.browser.test.tsx"],
    allowOnly: false,
    passWithNoTests: false,
    retry: 0,
    maxWorkers: 1,
    fileParallelism: false,
    testTimeout: 10000,
    browser: {
      enabled: true,
      headless: true,
      provider: playwright(),
      instances: [{ browser: "chromium", name: "plain-preact" }],
    },
  },
});
