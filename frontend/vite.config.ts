import path from "node:path";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { guiSdkAllocationPlugin } from "./scripts/gui-sdk-allocation-plugin.mts";

const accountBarModule = path.resolve("src/components/AccountBar.tsx");
const mainModule = path.resolve("src/main.tsx");

// Asset sync copies this managed build into the native server's embedded tree.
// The development proxy keeps the SPA and API on the same browser origin.
export default defineConfig({
  plugins: [react(), guiSdkAllocationPlugin()],
  build: {
    outDir: "dist",
    emptyOutDir: true,
    // The post-build budget follows this graph's static imports. Dynamic game
    // chunks stay outside the first-load budget because browsers fetch them on play.
    manifest: true,
    sourcemap: false,
    rolldownOptions: {
      // Keep real entry facades and their exports when sharing implementation.
      preserveEntrySignatures: "strict",
      output: {
        codeSplitting: {
          groups: [{
            debugName: "startup-entry-and-accountbar",
            // Keep real executable roots separate; only their already-counted
            // static dependencies share implementation. Never follow dynamic edges.
            name(moduleId, context) {
              const module = context.getModuleInfo(moduleId);
              if (moduleId === mainModule || moduleId === accountBarModule || module?.isEntry) return null;
              const pending = [moduleId], seen = new Set<string>();
              while (pending.length > 0) {
                const current = pending.pop()!;
                if (seen.has(current)) continue;
                seen.add(current);
                const info = context.getModuleInfo(current);
                if (!info) continue;
                if (info.isEntry || current === mainModule || current === accountBarModule) return "startup";
                pending.push(...info.importers);
              }
              return null;
            },
            includeDependenciesRecursively: true,
          }],
        },
      },
    },
  },
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
      // allauth login/callback (Sign-in-with-Google) when CAT_ACCOUNTS_ENABLED=1.
      "/accounts": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
});
