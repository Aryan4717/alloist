import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  base: "./",
  root: path.resolve(__dirname, "popup"),
  plugins: [react()],
  build: {
    outDir: path.resolve(__dirname, "dist/popup"),
    emptyOutDir: true,
    rollupOptions: {
      input: path.resolve(__dirname, "popup/index.html"),
      output: {
        entryFileNames: "[name].js",
        chunkFileNames: "[name].js",
        assetFileNames: "[name].[ext]",
      },
    },
  },
});
