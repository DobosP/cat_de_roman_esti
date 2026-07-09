import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The SPA and the FastAPI BFF share an origin in production: Vite emits the build
// into the package the FastAPI app mounts at `/`. In dev, `/api` is proxied to the
// BFF (default http://127.0.0.1:8000) so the SPA and API stay same-origin.
export default defineConfig({
  plugins: [react()],
  build: {
    // Built SPA lands where the FastAPI app serves StaticFiles(html=True).
    outDir: "../cat_de_roman_esti/web/static",
    emptyOutDir: true,
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
