// HyperFrames kompozisyonunun çalışma zamanı paketleri: render (cli.ts) ve Stüdyo önizlemesi (npm run build) aynı dosyaları
// kullanır. WHY: bkz. wiki/decisions/0051-uctan-uca-hyperframes.md. Önizleme ile render aynı kodu çalıştırmalı.
// Komut satırı: hf/paketle-cli.ts.
import { build } from "esbuild";
import { copyFileSync, existsSync, mkdirSync, readdirSync, readFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import type { NativeKayit } from "./derle";

const burasi = dirname(fileURLToPath(import.meta.url));
export const KOK = resolve(burasi, "../..");

// calisma.js (kurgu çalışma zamanı), ada.js (React adası), native/cekirdek.js (window.HFN), gsap.min.js.
export const paketle = async (hedef: string, { onizleme = false } = {}) => {
  mkdirSync(join(hedef, "native"), { recursive: true });
  await build({ entryPoints: [join(burasi, "calisma.ts")], bundle: true, format: "iife", target: "es2020", minify: true,
    outfile: join(hedef, "calisma.js"), logLevel: "error" });
  // React adası: "remotion" taklide yönlenir; react ve remotion openmontage altından da studio kopyasından çözülür (tek kopya).
  await build({ entryPoints: [join(burasi, "ada.tsx")], bundle: true, format: "iife", target: "es2020", minify: true,
    outfile: join(hedef, "ada.js"), logLevel: "error", jsx: "transform",
    define: { "process.env.NODE_ENV": '"production"' },
    plugins: [{ name: "remotion-taklit", setup(b) {
      b.onResolve({ filter: /[\/]lib[\/]localFonts$/ }, () => ({ path: join(burasi, "yazi-tipi-taklit.ts") }));
      b.onResolve({ filter: /^remotion-gercek$/ }, () => b.resolve("remotion", { resolveDir: burasi, kind: "import-statement", pluginData: "gercek" }).then((r) => ({ path: r.path })));
      b.onResolve({ filter: /^remotion$/ }, (a) => (a.pluginData === "gercek" ? undefined : { path: join(burasi, "remotion-taklit.tsx") }));
      b.onResolve({ filter: /^react(-dom)?(\/.*)?$/ }, async (a) => {
        if (a.pluginData === "studio") return undefined;
        const r = await b.resolve(a.path, { resolveDir: burasi, kind: a.kind, pluginData: "studio" });
        return { path: r.path };
      });
    } }] });
  // Native çekirdeği React'siz ve saf Remotion matematiğiyle: HyperFrames lint'i wall-clock kodunu reddeder.
  await build({ entryPoints: [join(burasi, "native", "cekirdek.ts")], bundle: true, format: "iife", target: "es2020", minify: true,
    outfile: join(hedef, "native", "cekirdek.js"), logLevel: "error",
    plugins: [{ name: "saf", setup(b) {
      b.onResolve({ filter: /^remotion$/ }, () => ({ path: join(burasi, "native", "remotion-saf.ts") }));
      b.onResolve({ filter: /^react$/ }, () => ({ path: join(burasi, "native", "react-saf.ts") }));
    } }] });
  copyFileSync(join(KOK, "library", "vendor", "gsap.min.js"), join(hedef, "gsap.min.js"));
  if (onizleme) {
    const hf = join(KOK, "node_modules", "hyperframes", "dist");
    copyFileSync(join(hf, "hyperframe.runtime.iife.js"), join(hedef, "hyperframe.runtime.iife.js"));
    copyFileSync(join(hf, "hyperframes-player.global.js"), join(hedef, "hyperframes-player.global.js"));
  }
};

// HyperFrames'e taşınmış native bileşenler: library/motion/hf/<aile>-<ad>/sahne.html. Meta ve param varsayılanı
// library/motion/native/sema.json'dan (Remotion bileşenleriyle tek kaynak); klasörde meta.json/sema.json varsa o (yalnız HF).
// Python karşılığı: vedit.hf_kurgu.native_harita (Stüdyo önizlemesi).
export const nativeHarita = (): Record<string, NativeKayit & { dosya: string }> => {
  const HF = join(KOK, "library", "motion", "hf");
  const native: Record<string, NativeKayit & { dosya: string }> = {};
  const semaJson = JSON.parse(readFileSync(join(KOK, "library", "motion", "native", "sema.json"), "utf-8")).bilesenler as
    Record<string, { meta: any; sema: { properties?: Record<string, { default?: unknown }> } }>;
  for (const d of readdirSync(HF, { withFileTypes: true })) {
    const sahne = join(HF, d.name, "sahne.html");
    if (!d.isDirectory() || !existsSync(sahne)) continue;
    const ad = d.name.replace("-", "/");
    const yerel = (n: string) => (existsSync(join(HF, d.name, n)) ? JSON.parse(readFileSync(join(HF, d.name, n), "utf-8")) : null);
    const meta = yerel("meta.json") ?? semaJson[ad]?.meta;
    const sema = yerel("sema.json") ?? semaJson[ad]?.sema;
    if (!meta) continue;
    const ozellik = (sema?.properties ?? {}) as Record<string, { default?: unknown }>;
    const varsayilan = Object.fromEntries(Object.entries(ozellik).filter(([, v]) => "default" in v).map(([k, v]) => [k, v.default]));
    native[ad] = { meta, varsayilan, dosya: sahne };
  }
  return native;
};

// Bağlama kopyası: host, sahne kökü ve zaman çizelgesi anahtarı aynı kimliği taşır (HyperFrames kuralı).
export const sahneKopyasi = (ham: string, kok: string, w: number, h: number) =>
  ham.replace(/__KOK__/g, kok).replace(/__W__/g, String(w)).replace(/__H__/g, String(h));
