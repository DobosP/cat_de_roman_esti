import path from "node:path";
import { defineConfig } from "vite";
import preact from "@preact/preset-vite";
import { guiPrecompressedPlugin } from "./scripts/gui-precompressed-plugin.mts";

const accountBarModule = path.resolve("src/components/AccountBar.tsx");
const mainModule = path.resolve("src/main.tsx");
const scoreWriterModule = path.resolve("src/scores/record.ts");

// Asset sync copies this managed build into the native server's embedded tree.
// The development proxy keeps the SPA and API on the same browser origin.
// Preact 11 is the only runtime: no compat aliases, no React import source.
export default defineConfig({
  plugins: [preact({ reactAliasesEnabled: false }), guiPrecompressedPlugin()],
  resolve: { dedupe: ["preact"] },
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
            priority: 10,
            // Keep real executable roots separate; only their already-counted
            // static dependencies share implementation. Never follow dynamic edges.
            name(moduleId, context) {
              const module = context.getModuleInfo(moduleId);
              if (moduleId === mainModule || moduleId === accountBarModule || module?.isEntry) return null;
              // Keep the writer with its storage helpers; every importing route
              // still pays for this whole chunk, even before recording a result.
              if (moduleId === scoreWriterModule) return "startup";
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
          }, {
            // Home and Ranking use this small styling boundary too. Give it
            // priority over game controls so those screens never import the
            // game-recovery and option controls through a shared style helper.
            name: "csp-elements",
            priority: 5,
            test: /\/src\/components\/(?:CspElements|CspStyle)\.tsx?$/,
            includeDependenciesRecursively: true,
          }, {
            // Home's history view uses the same immutable share helpers as the
            // games. Keep their module separate from game-only recovery code.
            name: "share",
            priority: 5,
            test: /\/src\/share\.ts$/,
            includeDependenciesRecursively: true,
          }, {
            // These shared controls already mount with the selected game. Keep
            // one implementation chunk; every importing route pays for its full
            // static closure, including controls it does not itself render.
            name: "game-controls",
            priority: 0,
            test: /\/src\/(?:components\/(?:GameShell|GameHelp|GameOptions|GameSetupOptions|CategoryPicker|ResultCard|GameIntro|PlayGuide|StartFailureNotice|Hud|Confetti|DifficultyPicker)|hooks\/(?:useSavedGameResume|useElementMotion|useRecordScore|useActiveGame))\.(?:tsx?|mjs)$/,
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
