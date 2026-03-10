import { defineConfig } from "vite";
import path from "path";

export default defineConfig({
  build: {
    outDir: "dist",
    emptyOutDir: false,
    lib: {
      entry: path.resolve(__dirname, "content/content.ts"),
      name: "content",
      formats: ["iife"],
      fileName: () => "content/content.js",
    },
  },
});
