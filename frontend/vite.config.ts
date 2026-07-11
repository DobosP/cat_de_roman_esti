import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The SPA and the Django BFF share an origin in production: Vite emits the build
// into the package WhiteNoise serves at `/`. In dev, `/api` is proxied to the
// BFF (default http://127.0.0.1:8000) so the SPA and API stay same-origin.
export default defineConfig({
  plugins: [react()],
  build: {
    // Built SPA lands where Django/WhiteNoise serves it.
    outDir: "../cat_de_roman_esti/web/static",
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
