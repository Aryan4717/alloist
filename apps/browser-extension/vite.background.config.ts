import { defineConfig } from "vite";
import path from "path";

export default defineConfig({
  build: {
    outDir: "dist",
    emptyOutDir: false,
    lib: {
      entry: path.resolve(__dirname, "background/service-worker.ts"),
      name: "sw",
      formats: ["iife"],
      fileName: () => "background/service-worker.js",
    },
  },
});
