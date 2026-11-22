// Native motion grafiklerinin HyperFrames çekirdeği: window.HFN. Kompozisyonlar (library/motion/hf/<aile>-<ad>/sahne.html)
// kare matematiğini buradan alır; Remotion bileşenleriyle aynı fonksiyonlar olduğu için iki motor aynı sayıyı üretir.
// WHY: bkz. wiki/decisions/0051-uctan-uca-hyperframes.md. Bileşenler kare başına hesaplanan eğri, yay ve nefes kullanır;
// bunları GSAP ara geçişlerine çevirmek kayıplıdır. Sahne yine saf HyperFrames'tir: HTML/SVG, duraklatılmış tek GSAP
// zaman çizelgesi, değişkenler; çizim yalnız zaman çizelgesinin saatinden türer (birikmiş durum yok).
// Paket: cli.ts (esbuild, "remotion" → remotion-taklit) → hf/native/cekirdek.js.
import { interpolate, random, spring } from "remotion";
import * as tema from "../../remotion/tema";
import { IKON_CIZGI_ORAN, KONTUR_EK, ikonKalinlik } from "../../remotion/motion/cekirdek/olcu";
import { YAY_PROFIL, akisHesapla, cizgiOfset, type Akis } from "../../remotion/motion/cekirdek/zaman";
import type { Kutu, Nokta } from "../../remotion/motion/cekirdek/tipler";

type Tema = tema.TemaToken;

// Bir bağlamanın (mount) verisi: derle.ts yerleşimi seçer, cli.ts/önizleme window.__HFN_YER'e yazar.
export interface Yer {
  kutu: Kutu;              // kare koordinatında (bilgi); sahne kendi kökünde 0,0'dan çizer
  u: number;               // kısa kenar / 1080
  hedef: Nokta | null;     // kutuya göre (px)
  sureKare: number;        // klibin kare süresi (Remotion Sequence durationInFrames ile aynı)
  giris_sn: number; cikis_sn: number; // meta (sema.json): useAkis(sureKare, meta.giris_sn, meta.cikis_sn) ile aynı
  karart: boolean;         // odak_karart: kutunun arkasında radyal karartma (Katman.tsx)
  w: number; h: number;    // sekans boyu
  fps: number;
  ofset: number;           // pencereli derlemede klibin başı pencereden önceyse atlanan saniye
  param: Record<string, any>;
}

export interface Baglam extends Omit<Yer, "kutu"> {
  kutu: Kutu;              // x = y = 0, w/h kutu boyu (Remotion'da Bilesen'e verilen kutu)
  t: Tema;
  kok: HTMLElement;
  $: <T extends Element = HTMLElement>(sec: string) => T;
  $$: <T extends Element = HTMLElement>(sec: string) => T[];
  kimlik: (ad: string) => string; // sahne içi tekil id (SVG gradient, filtre): aynı sahne iki kez bağlanabilir
}

// React CSSProperties gibi: birimsiz sayıya px eklenir (React'in kuralı); tire ve camelCase ikisi de geçer.
const BIRIMSIZ = new Set(["opacity", "zIndex", "fontWeight", "lineHeight", "flex", "flexGrow", "flexShrink", "order", "zoom", "scale", "fillOpacity", "strokeOpacity", "stopOpacity"]);
export const stil = (el: HTMLElement | SVGElement, s: Record<string, unknown>) => {
  const st = (el as HTMLElement).style;
  for (const [k, v] of Object.entries(s)) {
    const ad = k.startsWith("--") ? k : k.replace(/[A-Z]/g, (m) => `-${m.toLowerCase()}`).replace(/^webkit-/, "-webkit-");
    if (v == null || v === false) { st.removeProperty(ad); continue; }
    st.setProperty(ad, typeof v === "number" && !BIRIMSIZ.has(k) && !k.startsWith("--") ? `${v}px` : String(v));
  }
};
// SVG öznitelikleri: null kaldırır.
export const oz = (el: Element, s: Record<string, unknown>) => {
  for (const [k, v] of Object.entries(s)) {
    if (v == null || v === false) el.removeAttribute(k);
    else el.setAttribute(k, String(v));
  }
};

const VARSAYILAN_TEMA = () => ((window as any).__TEMA as Tema | null) ?? tema.VARSAYILAN;

// Sahne kurulumu. `kur` öğeleri bir kez hazırlar ve kare çizicisini döner; çizici yalnız (a, f) ile çalışır.
export const sahne = (kokId: string, kur: (b: Baglam) => (a: Akis) => void, ayar: { hazirlik?: number } = {}) => {
  const w = window as any;
  const yer: Yer = w.__HFN_YER?.[kokId];
  const kok = document.getElementById(kokId) as HTMLElement;
  if (!yer || !kok) throw new Error(`HFN: ${kokId} bağlaması bulunamadı`);
  const t = VARSAYILAN_TEMA();
  // Kök tam karedir (sözleşme: inset 0). İçerik Katman.tsx gibi kutuya taşınır; odak karartması kutunun arkasında, tam karede.
  const k = yer.kutu;
  const kutuEl = document.createElement("div");
  stil(kutuEl, { position: "absolute", left: k.x, top: k.y, width: k.w, height: k.h });
  while (kok.firstChild) kutuEl.appendChild(kok.firstChild);
  let karartEl: HTMLElement | null = null;
  if (yer.karart) {
    karartEl = document.createElement("div");
    const cx = k.x + k.w / 2, cy = k.y + k.h / 2, tam = k.w >= yer.w - 1 && k.h >= yer.h - 1, r = t.renk.ikon_kontur;
    stil(karartEl, { position: "absolute", inset: 0, background: tam
      ? `radial-gradient(ellipse 75% 65% at 50% 50%, transparent 30%, ${tema.rgba(r, 0.36)} 100%)`
      : `radial-gradient(ellipse ${Math.max(k.w * 1.25, yer.w * 0.5)}px ${Math.max(k.h * 1.6, yer.h * 0.3)}px at ${cx}px ${cy}px, ${tema.rgba(r, 0.36)} 0%, ${tema.rgba(r, 0.22)} 55%, transparent 100%)` });
    kok.appendChild(karartEl);
  }
  kok.appendChild(kutuEl);
  const b: Baglam = {
    ...yer, t, kok, kutu: { x: 0, y: 0, w: yer.kutu.w, h: yer.kutu.h },
    $: (s) => kok.querySelector(s) as any,
    $$: (s) => Array.from(kok.querySelectorAll(s)) as any,
    kimlik: (ad) => `${kokId}-${ad}`,
  };
  const ciz = kur(b);
  const kare = (zaman: number) => {
    const f = Math.round((zaman + yer.ofset) * yer.fps);
    ciz(akisHesapla(t, f, yer.fps, yer.sureKare, yer.giris_sn, yer.cikis_sn, ayar.hazirlik ?? 3));
    // Katman.tsx: karartma useAkis(sureKare, giris, cikis, 0).gorunur ile açılır.
    if (karartEl) karartEl.style.opacity = String(akisHesapla(t, f, yer.fps, yer.sureKare, yer.giris_sn, yer.cikis_sn, 0).gorunur);
  };
  const D = Math.max(1 / yer.fps, yer.sureKare / yer.fps - yer.ofset);
  const tl = w.gsap.timeline({ paused: true });
  const saat = { s: 0 };
  tl.to(saat, { s: D, duration: D, ease: "none", onUpdate: () => kare(tl.time()) }, 0);
  kare(0);
  w.__timelines = w.__timelines || {};
  w.__timelines[kokId] = tl;
  return tl;
};

const HFN = {
  sahne, stil, oz,
  akis: akisHesapla, cizgiOfset, YAY_PROFIL,
  interpolate, spring, random,
  ikonKalinlik, KONTUR_EK, IKON_CIZGI_ORAN,
  ...tema,
};
export type HFNTip = typeof HFN;
(window as any).HFN = HFN;
