import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Asset sync copies this managed build into the native server's embedded tree.
// The development proxy keeps the SPA and API on the same browser origin.
export default defineConfig({
  plugins: [react()],
  build: {
    outDir: "dist",
    emptyOutDir: true,
    // The post-build budget follows this graph's static imports. Dynamic game
    // chunks stay outside the first-load budget because browsers fetch them on play.
    manifest: true,
    sourcemap: false,
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
