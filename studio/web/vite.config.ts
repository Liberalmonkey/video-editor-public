import path from "node:path";
import { fileURLToPath } from "node:url";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

const burasi = path.dirname(fileURLToPath(import.meta.url));
const kok = path.resolve(burasi, "../..");

export default defineConfig({
  root: burasi,
  plugins: [react()],
  // WHY: SplitReel openmontage altında; dedupe olmadan ikinci remotion ve react kopyası yüklenir.
  resolve: {
    dedupe: ["remotion", "react", "react-dom"],
    alias: {
      remotion: path.resolve(burasi, "../node_modules/remotion"),
      react: path.resolve(burasi, "../node_modules/react"),
      "react-dom": path.resolve(burasi, "../node_modules/react-dom"),
    },
  },
  server: {
    fs: { allow: [kok] },
    proxy: { "/api": "http://127.0.0.1:8765", "/dosya": "http://127.0.0.1:8765", "/pub": "http://127.0.0.1:8765" },
  },
  // WHY: bkz. wiki/decisions/0050-hyperframes-birincil-motor.md. Kütüphaneler ayrı parça: arayüz değişince yalnız
  // uygulama parçası yeniden iner, gerisi tarayıcı önbelleğinden gelir.
  build: {
    outDir: "dist",
    emptyOutDir: true,
    chunkSizeWarningLimit: 4000,
    rollupOptions: {
      output: {
        manualChunks(id: string) {
          if (!id.includes("node_modules")) return undefined;
          if (/[\\/](remotion|@remotion)[\\/]/.test(id)) return "remotion";
          if (/[\\/](three|@react-three|postprocessing|@dimforge)[\\/]/.test(id)) return "uc-boyut";
          if (/[\\/](dockview|dockview-core|dockview-react)[\\/]/.test(id)) return "dockview";
          if (/[\\/](react|react-dom|scheduler)[\\/]/.test(id)) return "react";
          return "kutuphane";
        },
      },
    },
  },
  test: { include: ["src/**/*.test.ts", "../remotion/**/*.test.ts", "../hf/**/*.test.ts"] },
});
