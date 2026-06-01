import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

/**
 * Vite configuration for the XRD Analysis System frontend.
 *
 * - React plugin for JSX/Fast-Refresh support
 * - Dev-server proxy: all /api requests are forwarded to the FastAPI backend
 *   so the frontend never has to worry about CORS during development.
 */
export default defineConfig({
  plugins: [react()],

  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",  // ← change from localhost to 127.0.0.1
        changeOrigin: true,
        secure: false,
      },
      "/reports": {
        target: "http://127.0.0.1:8000",  // ← same here
        changeOrigin: true,
        secure: false,
      },
    },
  },

  build: {
    outDir: "build",
    sourcemap: false,
    chunkSizeWarningLimit: 1000,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ["react", "react-dom", "react-router-dom"],
          plotly: ["react-plotly.js", "plotly.js-dist-min"],
        },
      },
    },
  },

  resolve: {
    alias: {
      "@": "/src",
    },
  },
});