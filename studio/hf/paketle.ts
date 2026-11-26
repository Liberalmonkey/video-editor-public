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

// Canlı HF grafik kompozisyonları (library/motion/hf/<ad>/index.html ve varsa proje work/edit/hf/<ad>/index.html).
export interface GrafikKayit { w: number; h: number; sure: number; varsayilan: Record<string, unknown>; dosya: string }
const _olcuOku = (ham: string) => {
  const kokM = ham.match(/<[^>]*data-composition-id[^>]*>/);
  const parca = kokM ? kokM[0] : ham;
  const oz: Record<string, number> = {};
  for (const m of parca.matchAll(/data-(width|height|duration)\s*=\s*"([\d.]+)"/g)) oz[m[1]] = Number(m[2]);
  if (oz.width == null || oz.height == null || oz.duration == null) return null;
  let varsayilan: Record<string, unknown> = {};
  const vm = ham.match(/data-composition-variables\s*=\s*(?:'([^']*)'|"([^"]*)")/);
  if (vm) {
    try {
      const arr = JSON.parse((vm[1] ?? vm[2]).replace(/&quot;/g, '"').replace(/&amp;/g, "&")) as { id: string; default?: unknown }[];
      varsayilan = Object.fromEntries(arr.filter((x) => x?.id && "default" in x).map((x) => [x.id, x.default]));
    } catch { /* yoksay */ }
  }
  return { w: Math.round(oz.width), h: Math.round(oz.height), sure: oz.duration, varsayilan };
};

export const grafikHarita = (projeHfKok?: string | null): Record<string, GrafikKayit> => {
  const out: Record<string, GrafikKayit> = {};
  const tara = (kok: string) => {
    if (!existsSync(kok)) return;
    for (const d of readdirSync(kok, { withFileTypes: true })) {
      if (!d.isDirectory()) continue;
      const dosya = join(kok, d.name, "index.html");
      if (!existsSync(dosya)) continue;
      const ham = readFileSync(dosya, "utf-8");
      // three.js sahnesi (uc.js) ve "canli": false canlı gömülmez, önbellekli WebM olur (hf_grafik.canli_mi, ADR 0063).
      if (/src\s*=\s*["']uc\.js["']/.test(ham) || /"canli"\s*:\s*false/.test(ham)) continue;
      const o = _olcuOku(ham);
      if (o) out[d.name] = { ...o, dosya };
    }
  };
  tara(join(KOK, "library", "motion", "hf"));
  if (projeHfKok) tara(projeHfKok); // proje kompozisyonu kütüphaneyi ezer (ADR 0050)
  return out;
};

// Standalone index.html → canlı data-composition-src <template> sahnesi (hf_grafik._sablon_sar ile birebir).
export const grafikKopyasi = (ham: string, kok: string, w: number, h: number): string => {
  if (ham.includes("<template") && ham.includes("__KOK__")) return sahneKopyasi(ham, kok, w, h);
  let stiller = [...ham.matchAll(/<style[^>]*>([\s\S]*?)<\/style>/gi)].map((m) => m[1]).join("\n");
  stiller = stiller.replace(/\bhtml\s*,\s*body\s*,\s*#root\b/g, `#${kok}`).replace(/#root\b/g, `#${kok}`).replace(/\b(?:html|body)\s*\{[^}]*\}/g, "");
  const bodyM = ham.match(/<body[^>]*>([\s\S]*?)<\/body>/i);
  let govde = bodyM ? bodyM[1] : ham;
  const betikler: string[] = [];
  govde = govde.replace(/<script([^>]*)>([\s\S]*?)<\/script>/gi, (_, et: string, ic: string) => {
    if (/\bsrc\s*=/i.test(et)) return "";
    if (ic.trim()) betikler.push(ic);
    return "";
  }).trim();
  govde = govde.replace(/\bid\s*=\s*"root"/, `id="${kok}"`)
    .replace(/\bdata-composition-id\s*=\s*"[^"]*"/, `data-composition-id="${kok}"`)
    .replace(/\bdata-width\s*=\s*"[^"]*"/, `data-width="${w}"`)
    .replace(/\bdata-height\s*=\s*"[^"]*"/, `data-height="${h}"`);
  const vm = ham.match(/data-composition-variables\s*=\s*(?:'([^']*)'|"([^"]*)")/);
  if (vm && !govde.includes("data-composition-variables")) {
    const rawV = vm[1] ?? vm[2];
    govde = govde.replace(`id="${kok}"`, `id="${kok}" data-composition-variables='${rawV}'`);
  }
  // Kök ve parametre okumaları klibe çevrilir (hf_grafik.kok_sorgusu_cevir ile birebir). WHY: bkz.
  // wiki/specs/hf-canli-gomme-ve-dikey-duzen.md: getElementById("root") canlı gömmede null ya da yabancı kök döndürüyordu.
  const js = betikler.join("\n").replace(/window\.__timelines\[\s*["']main["']\s*\]/g, `window.__timelines["${kok}"]`)
    .replace(/document\s*\.\s*(?:getElementById\(\s*["']root["']\s*\)|querySelector\(\s*["']#root["']\s*\))/g, "__kok")
    .replace(/window\.__HF_PARAM\s*(?:\.\s*main\b|\[\s*["']main["']\s*\])/g, `window.__HF_PARAM["${kok}"]`);
  const sarmal = `(() => {
  const __kok = document.getElementById("${kok}");
  if (!__kok) return;
  const __param = (window.__HF_PARAM && window.__HF_PARAM["${kok}"]) || {};
  __kok.querySelectorAll('[data-var-text]').forEach((el) => {
    const k = el.getAttribute('data-var-text');
    if (k && Object.prototype.hasOwnProperty.call(__param, k) && __param[k] != null) el.textContent = String(__param[k]);
  });
  const __q = (s) => __kok.querySelector(s);
  const __qa = (s) => Array.from(__kok.querySelectorAll(s));
  const _gsap = window.gsap;
  const gsap = _gsap ? new Proxy(_gsap, {
    get(target, prop) {
      if (prop === 'timeline') return (cfg) => {
        const tl = target.timeline(cfg);
        const wrap = (fn) => (t, ...rest) => fn.call(tl, typeof t === 'string' ? __qa(t) : t, ...rest);
        ['to', 'from', 'fromTo', 'set'].forEach((m) => { const orig = tl[m]; tl[m] = wrap(orig); });
        return tl;
      };
      return typeof target[prop] === 'function' ? target[prop].bind(target) : target[prop];
    }
  }) : _gsap;
  const HF_CTX = { kok: __kok, param: __param, q: __q, qa: __qa, w: ${w}, h: ${h} };
${js}
})();`;
  // Bileşenin kök kuralı (position: relative; height: 100%) sarmalı ezince kökün yüksekliği sıfıra iniyor, container query
  // kareyi yatay sanıyordu. WHY: bkz. wiki/specs/hf-canli-gomme-ve-dikey-duzen.md. Kaplama kuralı stillerden sonra gelir.
  const kapla = `#${kok}{position:absolute !important;inset:0 !important;width:100% !important;height:100% !important;}`;
  return `<template>\n<style>\n#${kok}{position:absolute;inset:0;background:none;overflow:hidden;}\n${stiller}\n${kapla}\n</style>\n${govde}\n<script>\n${sarmal}\n</script>\n</template>\n`;
};
