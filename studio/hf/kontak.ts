// Native motion galeri kontağı (ADR 0045, 0051): bileşenler ızgarada, her hücre dama zemin ya da gerçek kare üstünde,
// istenen evrede. Hücre bir HyperFrames sahne bağlamasıdır; bütün hücreler tek anda (T) yakalanır: her host'un başlangıcı
// T − evre·süre olur. vedit motion kontak çağırır, sonra `hyperframes snapshot --at T` alır.
// Kullanım: vite-node hf/kontak.ts -- <secenek.json> <proje-klasörü>   (stdout: {"t": T})
import { copyFileSync, existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { basename, join, resolve } from "node:path";
import { guvenliAlan, yerles } from "../remotion/motion/cekirdek/yerlesim";
import type { Yer } from "./native/cekirdek";
import { nativeHarita, paketle, sahneKopyasi } from "./paketle";

interface Secenek {
  adlar: string[]; zemin: "dama" | "kare"; kare?: string | null; faz: number;
  hucre: { w: number; h: number }; sutun: number; tema?: Record<string, unknown> | null; tema_css: string;
}

const argv = process.argv.slice(2).filter((a) => a !== "--");
const s = JSON.parse(readFileSync(argv[0], "utf-8")) as Secenek;
const proje = resolve(argv[1]);
mkdirSync(join(proje, "hf", "n"), { recursive: true });
await paketle(join(proje, "hf"));
writeFileSync(join(proje, "hf", "tema.css"), s.tema_css, "utf-8");
const native = nativeHarita();
const FPS = 30, ARA = 6, { w, h } = s.hucre, DAMA = "repeating-conic-gradient(#c8c8c8 0% 25%, #ffffff 0% 50%) 0 0 / 48px 48px";
const adlar = s.adlar.filter((a) => native[a]);
const kare = s.kare && existsSync(s.kare) ? `kare-${basename(s.kare)}` : null;
if (kare) copyFileSync(s.kare!, join(proje, kare));

// Evre karesi: Galeri.tsx ile aynı (sureKare − 1 sınırı).
const evre = adlar.map((ad) => {
  const sureKare = Math.round(native[ad].meta.sure.varsayilan * FPS);
  return { ad, sureKare, f: Math.min(sureKare - 1, Math.round(s.faz * sureKare)) };
});
const T = Math.max(...evre.map((e) => e.f)) / FPS;
const yerler: Record<string, Yer> = {};
const hucreler = evre.map((e, i) => {
  const kok = `k-${i}`;
  const sec = yerles(native[e.ad].meta, w, h, { guvenli: guvenliAlan(w, h), altyazi: null, yuzler: [], platform: [] }, "orta");
  yerler[kok] = { kutu: sec.kutu, u: Math.min(w, h) / 1080, hedef: { x: sec.kutu.w / 2, y: sec.kutu.h + 80 }, sureKare: e.sureKare, fps: FPS,
    ofset: 0, giris_sn: native[e.ad].meta.giris_sn, cikis_sn: native[e.ad].meta.cikis_sn, karart: false, w, h, param: native[e.ad].varsayilan };
  writeFileSync(join(proje, "hf", "n", `${kok}.html`), sahneKopyasi(readFileSync(native[e.ad].dosya, "utf-8"), kok, w, h), "utf-8");
  const x = (i % s.sutun) * (w + ARA), y = Math.floor(i / s.sutun) * (h + ARA); // Galeri.tsx ızgarası: 6 px ara
  const bas = T - e.f / FPS;
  return `<div style="position:absolute;left:${x}px;top:${y}px;width:${w}px;height:${h}px;overflow:hidden;background:${s.zemin === "dama" ? DAMA : "#808080"}">`
    + (s.zemin === "kare" && kare ? `<img src="${kare}" alt="" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover">` : "")
    + `<div id="${kok}" data-composition-id="${kok}" data-composition-src="hf/n/${kok}.html" data-start="${+bas.toFixed(6)}" data-duration="${+(e.sureKare / FPS).toFixed(6)}"`
    + ` data-track-index="${i}" data-width="${w}" data-height="${h}" style="position:absolute;inset:0"></div>`
    + `<div style="position:absolute;left:8px;bottom:8px;padding:4px 10px;background:rgba(0,0,0,0.7);color:#ffffff;font:600 28px sans-serif">${e.ad}</div></div>`;
});
const satir = Math.ceil(adlar.length / s.sutun);
const W = s.sutun * w + (s.sutun - 1) * ARA, H = satir * h + (satir - 1) * ARA;
const sureTop = Math.max(T + 1 / FPS, ...evre.map((e) => T - e.f / FPS + e.sureKare / FPS));
writeFileSync(join(proje, "index.html"), `<!doctype html>
<html lang="tr">
<head>
<meta charset="utf-8">
<link rel="stylesheet" href="hf/tema.css">
<style>html, body { margin: 0; background: #202020; } #root { position: relative; background: #202020; width: ${W}px; height: ${H}px; overflow: hidden; }</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="${+sureTop.toFixed(6)}" data-width="${W}" data-height="${H}" data-fps="${FPS}">
${hucreler.join("\n")}
</div>
<script>window.__TEMA = ${JSON.stringify(s.tema ?? null)}; window.__HFN_YER = ${JSON.stringify(yerler)};</script>
<script src="hf/gsap.min.js"></script>
<script src="hf/native/cekirdek.js"></script>
<script>window.__timelines = window.__timelines || {}; window.__timelines["main"] = gsap.timeline({ paused: true }).to({}, { duration: ${+sureTop.toFixed(6)} });</script>
</body>
</html>
`, "utf-8");
process.stdout.write(JSON.stringify({ t: T, w: W, h: H, adlar }) + "\n");
