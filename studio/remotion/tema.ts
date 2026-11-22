import React, { createContext, useContext } from "react";
import { Easing } from "remotion";
import varsayilan from "../../library/motion/tema/varsayilan.json";

// WHY: bkz. wiki/decisions/0043-stile-bagli-tema-tokenlari.md. Bileşenler renk, font, köşe, gölge ve hareketi
// buradan okur; sabit renk yazmaz. Token'ı vedit kurgu.render.json'a (render) ya da Stüdyo API'si (önizleme) koyar.
// Tema yoksa varsayilan.json: ADR 0014 dünyası (Montserrat, turuncu vurgu).

// ADR 0045: adlı eğriler. Bezier [x1, y1, x2, y2]; adim varsa basamaklı (steps).
export type Bezier = [number, number, number, number];
export interface EgriToken { enter: Bezier; exit: Bezier; emphasis: Bezier; settle: Bezier; adim?: number | null }

export interface TemaToken {
  ad: string;
  renk: { vurgu: string; ikincil: string; ikincil_yazi: string; zemin: string; yazi: string; soluk: string; olumlu: string; olumsuz: string; ikon_kontur: string; ikon_golge: string };
  font: { baslik: string; govde: string; mono: string; rakam?: string | null; agirlik_baslik: number; agirlik_govde: number; izleme: number; harf: "normal" | "buyuk" };
  sekil: { kose: number; cizgi: number; kontur: number; golge: "yok" | "yumusak" | "sert" | "glow"; doku: "yok" | "gren" | "kagit" | "halftone" | "tarama" | "piksel"; piksel: number; ikon_cizgi?: number | null };
  hareket: { easing: "yumusak" | "keskin" | "yay" | "basamak"; sure_kat: number; davranis: "yok" | "titresim" | "titreme-giris"; adim_fps: number | null; egri?: EgriToken | null };
  altyazi: { font: string; agirlik: number; renk: string; aktif_renk: string; kontur: number; kontur_renk: string; kutu: boolean; pop: boolean; solma: boolean };
  gecis: string[];
  kacin: string[];
}

export const VARSAYILAN = varsayilan as unknown as TemaToken;
const TemaBaglam = createContext<TemaToken>(VARSAYILAN);
export const TemaSaglayici: React.FC<{ tema?: TemaToken | null; children: React.ReactNode }> = ({ tema, children }) =>
  React.createElement(TemaBaglam.Provider, { value: tema ?? VARSAYILAN }, children);
export const useTema = () => useContext(TemaBaglam);

const YEDEK: Record<string, string> = {
  Fraunces: "serif", "Playfair Display": "serif", "EB Garamond": "serif", Caveat: "cursive", "JetBrains Mono": "monospace", VT323: "monospace",
};
export const yigin = (ad: string) => `'${ad}', ${YEDEK[ad] ?? "sans-serif"}`;

export const rgba = (hex: string, a: number) => {
  const n = parseInt(hex.slice(1), 16);
  return `rgba(${(n >> 16) & 255},${(n >> 8) & 255},${n & 255},${a})`;
};
const parlak = (hex: string) => {
  const n = parseInt(hex.slice(1), 16);
  const k = (v: number) => { v /= 255; return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; };
  return 0.2126 * k((n >> 16) & 255) + 0.7152 * k((n >> 8) & 255) + 0.0722 * k(n & 255);
};
export const koyuMu = (hex: string) => parlak(hex) < 0.18;

// Panel: stilin zemini; video üstünde okunsun diye hafif saydam. Açık zeminli stil açık panel kullanır.
export const panel = (t: TemaToken, a = 0.92) => rgba(t.renk.zemin, a);

// Doku panelin arka planına katman olarak eklenir (CSS background listesi); şekil çizmez.
const GREN = "url(\"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='160' height='160'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='2' stitchTiles='stitch'/></filter><rect width='100%' height='100%' filter='url(%23n)' opacity='.22'/></svg>\")";
export const dokuKatmani = (t: TemaToken): string | null => {
  switch (t.sekil.doku) {
    case "gren": return GREN;
    case "kagit": return GREN.replace(".9' numOctaves='2'", ".035' numOctaves='4'");
    case "halftone": return `radial-gradient(${rgba(t.renk.yazi, 0.16)} 22%, transparent 24%) 0 0/14px 14px`;
    case "tarama": return `repeating-linear-gradient(0deg, ${rgba("#000000", 0.2)} 0 2px, transparent 2px 5px)`;
    default: return null;
  }
};
export const panelArka = (t: TemaToken, renk?: string) => {
  const d = dokuKatmani(t);
  return d ? `${d}, ${renk ?? panel(t)}` : renk ?? panel(t);
};

// Gölge: (box-shadow, text-shadow, filter). u ölçek katsayısıdır.
export const golge = (t: TemaToken, u = 1) => {
  const r = t.renk;
  switch (t.sekil.golge) {
    case "yumusak": return { kutu: `0 ${10 * u}px ${28 * u}px rgba(0,0,0,0.35)`, yazi: `0 ${4 * u}px ${14 * u}px rgba(0,0,0,0.5)`, filtre: `drop-shadow(0 ${8 * u}px ${16 * u}px rgba(0,0,0,0.35))` };
    case "sert": {
      const k = Math.max(4, t.sekil.cizgi) * u, c = koyuMu(r.zemin) ? "#000000" : r.yazi;
      return { kutu: `${k}px ${k}px 0 ${c}`, yazi: `${k * 0.6}px ${k * 0.6}px 0 ${c}`, filtre: `drop-shadow(${k}px ${k}px 0 ${c})` };
    }
    case "glow": return { kutu: `0 0 ${18 * u}px ${rgba(r.vurgu, 0.55)}, 0 0 ${4 * u}px ${rgba(r.vurgu, 0.9)}`, yazi: `0 0 ${12 * u}px ${rgba(r.vurgu, 0.8)}`, filtre: `drop-shadow(0 0 ${10 * u}px ${rgba(r.vurgu, 0.7)})` };
    default: return { kutu: "none", yazi: "none", filtre: "none" };
  }
};

// Çerçeve: stil konturu varsa panel kenarı; yoksa yok.
export const kenar = (t: TemaToken, u = 1) => (t.sekil.kontur > 0 ? `${t.sekil.kontur * u}px solid ${t.renk.yazi}` : undefined);

// İşe göre easing: giriş, çıkış ve "pop" (yay stilinde taşar, keskin stilde taşmaz, basamakta adımlı).
const adimli = (n: number) => (x: number) => Math.min(1, Math.floor(x * n) / (n - 1 || 1));
export const egriler = (t: TemaToken) => {
  switch (t.hareket.easing) {
    case "yumusak": return { gir: Easing.bezier(0.45, 0, 0.2, 1), cik: Easing.bezier(0.5, 0, 0.75, 0), pop: Easing.bezier(0.25, 1, 0.5, 1) };
    case "yay": return { gir: Easing.bezier(0.16, 1, 0.3, 1), cik: Easing.bezier(0.7, 0, 0.84, 0), pop: Easing.bezier(0.34, 1.56, 0.64, 1) };
    case "basamak": return { gir: adimli(4), cik: adimli(3), pop: adimli(4) };
    default: return { gir: Easing.bezier(0.16, 1, 0.3, 1), cik: Easing.bezier(0.7, 0, 0.84, 0), pop: Easing.bezier(0.16, 1, 0.3, 1) };
  }
};

// ADR 0045: native motion bileşenlerinin dört adlı eğrisi. Stil `hareket.egri` verdiyse o, yoksa easing türünden türetilir.
// Doğrusal eğri yoktur; adim varsa her eğri basamaklıdır.
export type EgriFn = (x: number) => number;
export interface Egriler { enter: EgriFn; exit: EgriFn; emphasis: EgriFn; settle: EgriFn }
const TURETILMIS: Record<TemaToken["hareket"]["easing"], EgriToken> = {
  yumusak: { enter: [0.45, 0, 0.2, 1], exit: [0.5, 0, 0.75, 0], emphasis: [0.25, 1, 0.5, 1], settle: [0.33, 1, 0.68, 1] },
  keskin: { enter: [0.16, 1, 0.3, 1], exit: [0.7, 0, 0.84, 0], emphasis: [0.22, 1.25, 0.36, 1], settle: [0.22, 1, 0.36, 1] },
  yay: { enter: [0.16, 1, 0.3, 1], exit: [0.7, 0, 0.84, 0], emphasis: [0.34, 1.56, 0.64, 1], settle: [0.34, 1.3, 0.64, 1] },
  basamak: { enter: [0.16, 1, 0.3, 1], exit: [0.7, 0, 0.84, 0], emphasis: [0.16, 1, 0.3, 1], settle: [0.16, 1, 0.3, 1], adim: 4 },
};
export const egriToken = (t: TemaToken): EgriToken => t.hareket.egri ?? TURETILMIS[t.hareket.easing] ?? TURETILMIS.keskin;
export const adliEgriler = (t: TemaToken): Egriler => {
  const e = egriToken(t);
  const yap = (b: Bezier): EgriFn => {
    const f = Easing.bezier(...b);
    return e.adim ? (x) => f(Math.min(1, Math.floor(x * e.adim!) / (e.adim! - 1 || 1))) : f;
  };
  return { enter: yap(e.enter), exit: yap(e.exit), emphasis: yap(e.emphasis), settle: yap(e.settle) };
};
// İkon çizgisi (px, 1080 kısa kenarda). Telefonda okunur alt sınır 6.
export const ikonCizgi = (t: TemaToken) => Math.max(6, t.sekil.ikon_cizgi ?? Math.round(t.sekil.cizgi * 1.1));

// Adımlı stil (8 fps piksel, 12 fps lastik hortum): grafik karesi tema kare hızına yuvarlanır.
export const adimKare = (t: TemaToken, f: number, fps: number) => {
  const a = t.hareket.adim_fps;
  if (!a || a >= fps) return f;
  const k = fps / a;
  return Math.floor(f / k) * k;
};

// Titreşim (el çizimi): kareye bağlı küçük, tekrarlanabilir kayma.
export const titresim = (t: TemaToken, f: number, u = 1) => {
  if (t.hareket.davranis !== "titresim") return "";
  const s = Math.floor(f / 3);
  return `translate(${Math.sin(s * 12.9898) * 1.5 * u}px, ${Math.cos(s * 78.233) * 1.5 * u}px) rotate(${Math.sin(s * 3.7) * 0.4}deg)`;
};

// Neon titreme girişi: ilk 14 karede aç-kapa.
export const titremeOpaklik = (t: TemaToken, f: number) =>
  t.hareket.davranis !== "titreme-giris" ? 1 : f < 14 ? ([0.25, 1, 0.3, 1, 1, 0.35, 1, 1, 0.5, 1][Math.floor(f / 1.4)] ?? 1) : 1;

// ---------------------------------------------------------------------------------------------------------------
// Malzeme ve yüzey sistemi. Düz renk kutu + tek gölge (2010'lar clipart kartı) yerine stilin token'ından türeyen
// malzeme: cam, kurumsal, editoryal, neon, piksel, brutalist. Hiçbir yardımcı sabit renk yazmaz; renkler token'dan,
// nötr gölge rgba(0,0,0,a) ile (ışığın yokluğu: stil rengi değil).
// ---------------------------------------------------------------------------------------------------------------
export type YuzeyTipi = "cam" | "kurumsal" | "editoryal" | "neon" | "piksel" | "brutalist";
export type YuzeyKip = "kart" | "rozet" | "bant" | "vurgulu";

const kanallar = (hex: string): [number, number, number] => {
  const n = parseInt(hex.slice(1), 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
};
// İki token rengini karıştırır (k: 0 → a, 1 → b); sonuç rgba() dizgesi.
export const karistir = (a: string, b: string, k: number, al = 1) => {
  const x = kanallar(a), y = kanallar(b);
  const c = x.map((v, i) => Math.round(v + (y[i] - v) * k));
  return `rgba(${c[0]},${c[1]},${c[2]},${al})`;
};
// Rengi koyulaştır (k > 0) ya da açar (k < 0); nötr siyah/beyaza doğru, sabit hex olmadan.
export const ton = (hex: string, k: number, al = 1) => {
  const c = kanallar(hex).map((v) => Math.round(k >= 0 ? v * (1 - k) : v + (255 - v) * -k));
  return `rgba(${c[0]},${c[1]},${c[2]},${al})`;
};
const SIYAH = (a: number) => `rgba(0,0,0,${a})`;

// Token özelliklerinden yüzey ailesi. Sıra önemlidir: piksel > neon > editoryal > brutalist > cam > kurumsal.
// Not: adim_fps yalnız 8 fps ve altıysa piksel sayılır; 10-12 fps kesik kâğıt/lastik hortum dokusunu korur.
export const yuzeyTipi = (t: TemaToken): YuzeyTipi => {
  const s = t.sekil;
  if (s.doku === "piksel" || (s.piksel ?? 1) > 1 || (t.hareket.adim_fps != null && t.hareket.adim_fps <= 8) || t.ad.includes("piksel")) return "piksel";
  if (s.golge === "glow" || s.doku === "tarama") return "neon";
  if (s.doku === "kagit" || s.doku === "halftone") return "editoryal";
  if (s.golge === "sert" && (s.kose <= 6 || s.kontur > 0 || t.hareket.adim_fps != null)) return "brutalist";
  if (s.kose >= 14 && s.golge === "yumusak" && koyuMu(t.renk.zemin)) return "cam";
  return "kurumsal";
};

const kipKose = (t: TemaToken, u: number, kip: YuzeyKip, tip: YuzeyTipi) => {
  const k = t.sekil.kose * u;
  if (tip === "piksel") return 0;
  if (tip === "brutalist") return Math.min(k, 6 * u);
  if (kip === "rozet") return k === 0 ? 0 : 999 * u;
  if (kip === "bant") return k * 0.6;
  return k;
};

// Yüzey stili: kartın arka planı, kenarı, köşesi, gölgesi ve (cam/neon) arka bulanıklığı.
// Kullanım: <div style={{ ...yuzeyStil(t, u), padding }}>…; parlama için position: relative + overflow: hidden ekle.
export const yuzeyStil = (t: TemaToken, u: number, kip: YuzeyKip = "kart"): React.CSSProperties => {
  const r = t.renk, tip = yuzeyTipi(t), koyu = koyuMu(r.zemin);
  const vur = kip === "vurgulu";
  const doku = dokuKatmani(t);
  const katla = (zemin: string) => (doku ? `${doku}, ${zemin}` : zemin);
  const borderRadius = kipKose(t, u, kip, tip);
  const ince = Math.max(1, 1.25 * u);
  const yogun = kip === "bant" ? 0.7 : kip === "rozet" ? 0.8 : 1; // küçük öğede gölge daha kısa
  switch (tip) {
    case "cam": {
      const a = vur ? r.vurgu : r.zemin;
      return {
        background: katla(`linear-gradient(155deg, ${rgba(a, vur ? 0.78 : 0.66)} 0%, ${rgba(a, vur ? 0.6 : 0.42)} 55%, ${rgba(a, vur ? 0.7 : 0.5)} 100%)`),
        backdropFilter: `blur(${18 * u}px) saturate(1.3)`,
        WebkitBackdropFilter: `blur(${18 * u}px) saturate(1.3)`,
        border: `${ince}px solid ${rgba(r.yazi, vur ? 0.3 : 0.14)}`,
        borderRadius,
        boxShadow: [
          `inset 0 ${1.5 * u}px 0 ${rgba(r.yazi, 0.26)}`,          // üst rim ışığı
          `inset 0 ${-1 * u}px 0 ${SIYAH(0.22)}`,                   // alt kenar
          `0 ${2 * u}px ${6 * u}px ${SIYAH(0.2 * yogun)}`,          // temas gölgesi
          `0 ${18 * u * yogun}px ${48 * u * yogun}px ${SIYAH(0.4 * yogun)}`, // ortam gölgesi
        ].join(", "),
      };
    }
    case "neon": {
      const g = r.vurgu;
      return {
        background: katla(vur
          ? `linear-gradient(160deg, ${rgba(g, 0.32)} 0%, ${rgba(r.zemin, 0.72)} 100%)`
          : `linear-gradient(160deg, ${rgba(r.zemin, 0.8)} 0%, ${rgba(r.zemin, 0.62)} 100%)`),
        backdropFilter: `blur(${10 * u}px)`,
        WebkitBackdropFilter: `blur(${10 * u}px)`,
        border: `${Math.max(1.5, 2 * u)}px solid ${rgba(g, 0.9)}`,
        borderRadius,
        boxShadow: [
          `0 0 ${2 * u}px ${rgba(g, 0.9)}`,
          `0 0 ${16 * u * yogun}px ${rgba(g, 0.45)}`,
          `0 0 ${42 * u * yogun}px ${rgba(g, 0.2)}`,
          `inset 0 0 ${18 * u}px ${rgba(g, 0.18)}`,
        ].join(", "),
      };
    }
    case "editoryal": {
      const a = vur ? r.vurgu : r.zemin;
      const sert = t.sekil.golge === "sert";
      return {
        background: katla(`linear-gradient(175deg, ${rgba(a, 0.98)} 0%, ${karistir(a, r.yazi, 0.04, 0.96)} 100%)`),
        border: `${ince}px solid ${rgba(r.yazi, vur ? 0.35 : 0.24)}`,
        borderRadius,
        boxShadow: [
          `inset 0 ${1 * u}px 0 ${rgba(r.yazi, 0.04)}`,
          sert ? `${3 * u}px ${4 * u}px 0 ${rgba(r.ikon_golge, 0.85)}` : `0 ${1 * u}px ${2 * u}px ${SIYAH(0.12)}`,
          `0 ${6 * u * yogun}px ${16 * u * yogun}px ${SIYAH(0.16 * yogun)}`,
        ].join(", "),
      };
    }
    case "piksel":
    case "brutalist": {
      const a = vur ? r.vurgu : r.zemin;
      const k = Math.max(4, Math.min(10, t.sekil.cizgi)) * u * (kip === "bant" ? 0.7 : 1);
      const ofset = koyu ? r.vurgu : r.yazi;
      return {
        background: katla(rgba(a, 0.97)),
        border: `${Math.max(3, t.sekil.kontur || t.sekil.cizgi * 0.5) * u}px solid ${vur ? r.yazi : koyu ? r.yazi : r.ikon_kontur}`,
        borderRadius,
        boxShadow: `${k}px ${k}px 0 ${vur ? r.yazi : ofset}`,
      };
    }
    default: {
      // kurumsal: yarı mat gradyan, kıl payı kenar, iki katmanlı yumuşak gölge. Stil gölgesizse yalnız temas gölgesi.
      const a = vur ? r.vurgu : r.zemin;
      const gol = t.sekil.golge !== "yok";
      return {
        background: katla(`linear-gradient(180deg, ${karistir(a, r.yazi, koyu && !vur ? 0.05 : 0, 0.97)} 0%, ${ton(a, vur ? 0.08 : koyu ? 0.12 : 0.03, 0.95)} 100%)`),
        border: `${ince}px solid ${rgba(r.yazi, vur ? 0.18 : koyu ? 0.12 : 0.1)}`,
        borderRadius,
        boxShadow: [
          `inset 0 ${1 * u}px 0 ${rgba(r.yazi, koyu ? 0.1 : 0.0)}`,
          `0 ${1 * u}px ${2 * u}px ${SIYAH(0.14)}`,
          ...(gol ? [`0 ${10 * u * yogun}px ${28 * u * yogun}px ${SIYAH(0.24 * yogun)}`, `0 ${2 * u}px ${8 * u}px ${SIYAH(0.12)}`] : []),
        ].join(", "),
      };
    }
  }
};
// Yüzeyin üstündeki ana yazı rengi (vurgulu kipte vurgunun üstü).
export const yuzeyYazi = (t: TemaToken, kip: YuzeyKip = "kart") => (kip === "vurgulu" ? (koyuMu(t.renk.vurgu) ? t.renk.yazi : t.renk.zemin) : t.renk.yazi);

// Specular ışık şeridi: kartın üstünden çapraz geçen ince parıltı. ilerleme 0..1 (Akis.parlama); 0 ve 1'de görünmez.
// Kart kabında position: relative ve overflow: hidden olmalı; bu stil bir iç <div>'e verilir.
export const parlamaStil = (t: TemaToken, ilerleme: number, u: number): React.CSSProperties => {
  const p = Math.max(0, Math.min(1, ilerleme));
  const tip = yuzeyTipi(t);
  const op = Math.sin(Math.PI * p);
  const x = -25 + 150 * p;
  const renk = tip === "neon" ? t.renk.vurgu : t.renk.yazi;
  const guc = tip === "piksel" || tip === "brutalist" ? 0.22 : koyuMu(t.renk.zemin) ? 0.2 : 0.42;
  const gen = tip === "piksel" ? 0 : 7; // piksel: keskin bant
  const bant = 6 * Math.max(0.6, u);
  return {
    position: "absolute", inset: 0, pointerEvents: "none", borderRadius: "inherit",
    opacity: op < 0.002 ? 0 : op,
    background: `linear-gradient(112deg, transparent ${x - bant - gen}%, ${rgba(renk, guc * 0.35)} ${x - bant}%, ${rgba(renk, guc)} ${x}%, ${rgba(renk, guc * 0.35)} ${x + bant}%, transparent ${x + bant + gen}%)`,
    mixBlendMode: koyuMu(t.renk.zemin) || tip === "neon" ? "screen" : "soft-light",
  };
};

// Çok katmanlı duotone ikon paleti: arka dolgu, ön vurgu, parıltı (üst ışık), dış kontur ve gölge filtresi.
export const ikonStil = (t: TemaToken, renk: string, u: number) => {
  const tip = yuzeyTipi(t);
  const neon = tip === "neon";
  return {
    dolgu: rgba(renk, neon ? 0.16 : 0.24),
    vurgu: renk,
    parilti: ton(renk, -0.55, 0.9),
    kontur: t.renk.ikon_kontur,
    golge: neon
      ? `drop-shadow(0 0 ${6 * u}px ${rgba(renk, 0.75)})`
      : tip === "piksel" || tip === "brutalist"
        ? `drop-shadow(${4 * u}px ${4 * u}px 0 ${rgba(t.renk.ikon_golge, 0.9)})`
        : `drop-shadow(0 ${3 * u}px ${6 * u}px ${rgba(t.renk.ikon_golge, 0.45)})`,
  };
};

export const rakamFontu = (t: TemaToken) => yigin(t.font.rakam ?? t.font.baslik);
export const harf = (t: TemaToken, s: string) => (t.font.harf === "buyuk" ? s.toLocaleUpperCase("tr-TR") : s);
