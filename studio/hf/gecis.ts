// Orta noktalı V1 geçişleri (ADR 0045) HyperFrames için: her karede sarıcıya stil ve üstüne ışık katmanı.
// WHY: bkz. wiki/decisions/0051-uctan-uca-hyperframes.md. gecisler.tsx ile birebir: sil/kay/saat/iris
// @remotion/transitions sunumlarının matematiği, diğer sekizi gecisler.tsx'teki özel sunumlar. random() Remotion'la
// aynı tohum işlevi (mulberry32 + hashCode), piksel ve bozulma blok sırası iki motorda aynı.
import type { Gecis, Yon } from "../remotion/tipler";
import { bezier } from "./bezier";

export const ORTA_GECIS = [
  "sil", "kay", "saat", "iris", "kirbac", "isik", "piksel", "zoom_kirbac", "film_yanigi", "bolunme", "bozulma", "yirtma",
  "tikla_iris", "buton_zoom", "kart_dunyaya", "bulanik_takas", "dip_kesim",
];
const IKI_YONLU = ["kay", "kirbac", "zoom_kirbac", "bozulma", "buton_zoom", "bulanik_takas", "dip_kesim"];
const ACILIS = bezier(0.22, 0.8, 0.36, 1);
const KIS = bezier(0.65, 0, 0.35, 1);
const YERLES = bezier(0.16, 1, 0.3, 1);
const HIZLAN = bezier(0.55, 0, 1, 0.45);
const egriSec = (tur: string) => (["saat", "iris", "isik", "piksel", "zoom_kirbac", "film_yanigi", "bolunme", "bozulma", "yirtma"].includes(tur) ? ACILIS : KIS);
export const cikanHareketli = (g?: Gecis | null) => !!g && IKI_YONLU.includes(g.tur);

const mulberry32 = (a: number) => {
  let t = a + 0x6d2b79f5;
  t = Math.imul(t ^ (t >>> 15), t | 1);
  t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
  return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
};
const hashCode = (s: string) => { let h = 0; for (let i = 0; i < s.length; i++) { h = (h << 5) - h + s.charCodeAt(i); h |= 0; } return h; };
export const random = (tohum: string) => mulberry32(hashCode(tohum));

export interface Renkler { vurgu: string; ikincil: string; yazi: string; zemin: string }
const rgba = (hex: string, a: number) => {
  const n = parseInt(hex.replace("#", "").slice(0, 6), 16);
  return `rgba(${(n >> 16) & 255},${(n >> 8) & 255},${n & 255},${a})`;
};

export interface GecisStil { transform: string; filter: string; clipPath: string; mask: string; opacity: string; katman: string }
const bos = (): GecisStil => ({ transform: "", filter: "", clipPath: "", mask: "", opacity: "", katman: "" });
const tam = (style: string) => `<div style="position:absolute;inset:0;${style}"></div>`;

type Yonlu = "from-left" | "from-right" | "from-top" | "from-bottom";
const GELIS: Record<Yon, Yonlu> = { sol: "from-right", sag: "from-left", yukari: "from-bottom", asagi: "from-top" };

const silGirer = (p: number, d: Yonlu) => {
  const q = p * 100;
  return { "from-left": `polygon(0% 0%, ${q}% 0%, ${q}% 100%, 0% 100%)`, "from-top": `polygon(0% 0%, 100% 0%, 100% ${q}%, 0% ${q}%)`,
    "from-right": `polygon(100% 0%, 100% 100%, ${100 - q}% 100%, ${100 - q}% 0%)`, "from-bottom": `polygon(0% 100%, 100% 100%, 100% ${100 - q}%, 0% ${100 - q}%)` }[d];
};
const silCikar = (p: number, d: Yonlu) => {
  const q = p * 100;
  return { "from-left": `polygon(100% 100%, ${100 - q}% 100%, ${100 - q}% 0%, 100% 0%)`, "from-top": `polygon(100% 100%, 0% 100%, 0% ${100 - q}%, 100% ${100 - q}%)`,
    "from-right": `polygon(0% 0%, ${q}% 0%, ${q}% 100%, 0% 100%)`, "from-bottom": `polygon(100% 0%, 0% 0%, 0% ${q}%, 100% ${q}%)` }[d];
};
const kayStil = (p: number, yon: "entering" | "exiting", d: Yonlu) => {
  const e = p === 1 ? p * 100 : p * 100 - 0.01;
  if (yon === "exiting") return { "from-left": `translateX(${e}%)`, "from-right": `translateX(${-p * 100}%)`, "from-top": `translateY(${e}%)`, "from-bottom": `translateY(${-p * 100}%)` }[d];
  return { "from-left": `translateX(${-100 + p * 100}%)`, "from-right": `translateX(${100 - e}%)`, "from-top": `translateY(${-100 + p * 100}%)`, "from-bottom": `translateY(${100 - e}%)` }[d];
};
const yuvarla5 = (v: number) => Math.round(v * 100000) / 100000;
// @remotion/shapes makePie (saat yönünde, tepe noktadan) + translatePath.
const pasta = (p: number, w: number, h: number) => {
  const r = Math.sqrt(w * w + h * h) / 2, dx = -(r * 2 - w) / 2, dy = -(r * 2 - h) / 2;
  const a = Math.min(Math.max(p, 0), 1);
  const k = (q: number, c: "x" | "y") => yuvarla5(Math[c === "x" ? "cos" : "sin"](q * Math.PI * 2 + Math.PI * 1.5) * r + r);
  const P = (x: number, y: number) => `${x + dx} ${y + dy}`;
  let d = `M ${P(k(0, "x"), k(0, "y"))} A ${r} ${r} 0 0 1 ${P(a <= 0.5 ? k(a, "x") : k(0.5, "x"), a <= 0.5 ? k(a, "y") : k(0.5, "y"))}`;
  if (a > 0.5) d += ` A ${r} ${r} 0 0 1 ${P(k(a, "x"), k(a, "y"))}`;
  if (a > 0 && a < 1) d += ` L ${P(r, r)}`;
  return `path("${d} Z")`;
};
const daire = (yaricap: number, w: number, h: number) => {
  const r = yaricap, x = w / 2 - r, y = h / 2 - r;
  return `path("M ${r + x} ${y} a ${r} ${r} 0 1 1 0 ${r * 2} a ${r} ${r} 0 1 1 0 ${-r * 2} Z")`;
};

// ilerleme: 0..1 (gecisler.tsx GecisSarici ile aynı kırpma); yon: giren mi çıkan mı.
export const gecisStil = (g: Gecis, ilerleme: number, yon: "entering" | "exiting", w: number, h: number, renk: Renkler): GecisStil => {
  const p = Math.max(0, Math.min(1, ilerleme));
  const s = bos();
  const tepe = Math.sin(Math.PI * p);
  switch (g.tur) {
    case "sil": case "kay": case "saat": case "iris": {
      const e = egriSec(g.tur)(p), d = GELIS[g.yon ?? "sol"];
      if (g.tur === "sil") s.clipPath = yon === "entering" ? silGirer(e, d) : silCikar(1 - e, d);
      else if (g.tur === "kay") s.transform = kayStil(e, yon, d);
      else if (yon === "entering") {
        const maks = Math.sqrt(w * w + h * h) / 2;
        s.clipPath = g.tur === "saat" ? pasta(e, w, h) : daire(maks * e, w, h);
      }
      return s;
    }
    case "kirbac": {
      const a = KIS(p);
      const [vx, vy] = ({ sol: [-1, 0], sag: [1, 0], yukari: [0, -1], asagi: [0, 1] } as const)[g.yon ?? "sol"];
      const kay = yon === "entering" ? 1 - a : -a;
      const bul = Math.pow(tepe, 1.25) * 28, esne = 1 + 0.045 * tepe;
      const sx = vx ? esne : 1 + 0.015 * tepe, sy = vy ? esne : 1 + 0.015 * tepe, parl = 1 + 0.08 * tepe;
      s.transform = `translate(${vx * kay * w}px, ${vy * kay * h}px) scale(${sx}, ${sy})`;
      s.filter = [bul > 0.4 && `blur(${bul.toFixed(2)}px)`, parl > 1.005 && `brightness(${parl.toFixed(3)})`].filter(Boolean).join(" ");
      return s;
    }
    case "isik": {
      if (yon === "exiting") {
        s.transform = `scale(${1 + 0.025 * p})`;
        if (tepe > 0.02) s.filter = `brightness(${(1 + 0.1 * tepe).toFixed(3)})`;
        return s;
      }
      const a = ACILIS(p), x = 15 + 70 * p, kenar = -20 + 150 * a, bul = (1 - a) * 3.5;
      s.mask = `linear-gradient(102deg, rgba(0,0,0,1) ${kenar - 28}%, transparent ${kenar}%)`;
      s.transform = `scale(${1.035 - 0.035 * YERLES(p)})`;
      if (bul > 0.25) s.filter = `blur(${bul.toFixed(2)}px)`;
      s.katman = tam(`mix-blend-mode:screen;opacity:${0.52 * tepe};background:radial-gradient(ellipse ${w * 0.9}px ${h * 0.7}px at ${x}% 32%, ${rgba(renk.ikincil, 0.85)}, ${rgba(renk.vurgu, 0.42)} 46%, transparent 76%)`);
      return s;
    }
    case "piksel": {
      if (yon === "exiting") return s;
      const n = 14, b = Math.ceil(w / n), m = Math.ceil(h / b);
      let yol = "";
      for (let j = 0; j < m; j++) for (let i = 0; i < n; i++) if (random(`piksel-${i}-${j}`) < ACILIS(p)) yol += `M${i * b} ${j * b}h${b}v${b}h${-b}z`;
      s.clipPath = yol ? `path('${yol}')` : "inset(100%)";
      return s;
    }
    case "zoom_kirbac": {
      if (yon === "exiting") {
        s.transform = `scale(${1 + 0.36 * HIZLAN(p)})`;
        if (tepe * 12 > 0.3) s.filter = `blur(${(tepe * 12).toFixed(2)}px)`;
        return s;
      }
      const a = ACILIS(p), bul = (1 - YERLES(p)) * 9, ic = Math.max(0, a * 125 - 12), dis = a * 135;
      s.mask = a <= 0.001 ? "radial-gradient(circle at 50% 50%, transparent 0%, transparent 100%)"
        : `radial-gradient(ellipse ${w * 0.8}px ${h * 0.8}px at 50% 50%, rgba(0,0,0,1) ${ic}%, transparent ${dis}%)`;
      s.transform = `scale(${1.18 - 0.18 * YERLES(p)})`;
      if (bul > 0.25) s.filter = `blur(${bul.toFixed(2)}px)`;
      s.katman = tam(`mix-blend-mode:screen;opacity:${0.42 * tepe};background:radial-gradient(ellipse ${w * 0.85}px ${h * 0.65}px at 50% 50%, ${rgba(renk.vurgu, 0.72)} 0%, ${rgba(renk.ikincil, 0.28)} 42%, transparent 74%)`);
      return s;
    }
    case "film_yanigi": {
      if (yon === "exiting") {
        if (tepe > 0.02) s.filter = `brightness(${(1 + 0.12 * tepe).toFixed(3)}) saturate(${(1 + 0.18 * tepe).toFixed(3)})`;
        return s;
      }
      const a = ACILIS(p), kenar = 138 * a, x1 = 10 + 82 * p, x2 = 85 - 65 * p;
      s.mask = a <= 0.001 ? "linear-gradient(124deg, transparent 0%, transparent 100%)" : `linear-gradient(124deg, rgba(0,0,0,1) ${kenar - 20}%, transparent ${kenar}%)`;
      s.transform = `scale(${1.03 - 0.03 * YERLES(p)})`;
      s.katman = tam(`mix-blend-mode:screen;opacity:${0.5 * tepe};background:radial-gradient(ellipse ${w * 0.75}px ${h * 0.6}px at ${x1}% 28%, ${rgba(renk.vurgu, 0.88)} 0%, ${rgba(renk.ikincil, 0.35)} 45%, transparent 76%)`)
        + tam(`mix-blend-mode:screen;opacity:${0.4 * tepe};background:radial-gradient(ellipse ${w * 0.65}px ${h * 0.55}px at ${x2}% 72%, ${rgba(renk.ikincil, 0.8)} 0%, ${rgba(renk.vurgu, 0.25)} 48%, transparent 78%)`)
        + tam(`mix-blend-mode:screen;opacity:${0.35 * tepe};background:linear-gradient(124deg, transparent ${kenar - 26}%, ${rgba(renk.vurgu, 0.6)} ${kenar - 10}%, ${rgba(renk.yazi, 0.35)} ${kenar - 4}%, transparent ${kenar + 12}%)`);
      return s;
    }
    case "bolunme": {
      if (yon === "exiting") return s;
      const a = ACILIS(p), yatay = g.yon === "yukari" || g.yon === "asagi", kapali = (1 - a) * 50;
      s.clipPath = yatay ? `inset(${kapali}% 0 ${kapali}% 0)` : `inset(0 ${kapali}% 0 ${kapali}%)`;
      s.transform = `scale(${1.05 - 0.05 * YERLES(p)})`;
      if (tepe > 0.02) {
        const c = Math.max(2, Math.round(Math.min(w, h) * 0.004));
        const kenar = (pos: number) => yatay
          ? `position:absolute;left:0;right:0;top:${pos}%;height:${c}px;transform:translateY(-50%)`
          : `position:absolute;top:0;bottom:0;left:${pos}%;width:${c}px;transform:translateX(-50%)`;
        const ortak = `;background:${renk.vurgu};opacity:${0.85 * tepe};box-shadow:0 0 ${c * 4}px ${rgba(renk.vurgu, 0.7)}`;
        s.katman = `<div style="${kenar(kapali)}${ortak}"></div><div style="${kenar(100 - kapali)}${ortak}"></div>`;
      }
      return s;
    }
    case "bozulma": {
      if (yon === "exiting") {
        const kay = (random(`boz-ex-${Math.floor(p * 12)}`) - 0.5) * 18 * tepe;
        s.transform = `translateX(${kay}px)`;
        if (tepe > 0.05) s.filter = `hue-rotate(${(tepe * 18).toFixed(1)}deg) contrast(${(1 + 0.14 * tepe).toFixed(2)})`;
        return s;
      }
      const a = ACILIS(p), n = 6, sh = Math.ceil(h / n), SIRA = [0, 3, 1, 5, 2, 4];
      let yol = "";
      for (let i = 0; i < n; i++) {
        const q = Math.max(0, Math.min(1, (a - SIRA[i] * 0.055) / (1 - 0.275)));
        const bw = Math.round(w * q);
        if (bw > 0) yol += `M${i % 2 === 0 ? 0 : w - bw} ${i * sh}h${bw}v${sh}h${-bw}z`;
      }
      const kay = (1 - a) * (Math.floor(p * 12) % 2 === 0 ? 1 : -1) * Math.round(w * 0.035);
      s.clipPath = yol ? `path('${yol}')` : "inset(100%)";
      if (kay) s.transform = `translateX(${kay}px)`;
      if (tepe > 0.05) s.katman = [1, 4].map((idx) => `<div style="position:absolute;left:0;right:0;top:${(idx + 0.45) * (100 / n)}%;`
        + `height:${Math.max(3, Math.round(sh * 0.08))}px;background:linear-gradient(90deg, transparent 5%, ${rgba(idx === 1 ? renk.vurgu : renk.ikincil, 0.72)} 35%, `
        + `${rgba(renk.yazi, 0.5)} 50%, ${rgba(idx === 1 ? renk.ikincil : renk.vurgu, 0.72)} 70%, transparent 95%);mix-blend-mode:screen;opacity:${0.7 * tepe};`
        + `transform:translateX(${(idx === 1 ? 1 : -1) * 14 * tepe}px)"></div>`).join("");
      return s;
    }
    case "yirtma": {
      if (yon === "exiting") return s;
      const a = ACILIS(p), adim = 20, yt = g.yon ?? "sol", dikey = yt === "yukari" || yt === "asagi", ters = yt === "sol" || yt === "yukari";
      const dalga = (j: number) => (random(`yirt-${j}`) - 0.5) * 0.05 * tepe;
      const nk: [number, number][] = [];
      for (let j = 0; j <= adim; j++) {
        if (!dikey) nk.push([Math.max(0, Math.min(w, (ters ? (1 - a) * w : a * w) + dalga(j) * w)), (j / adim) * h]);
        else nk.push([(j / adim) * w, Math.max(0, Math.min(h, (ters ? (1 - a) * h : a * h) + dalga(j) * h))]);
      }
      const pt = (l: [number, number][]) => l.map(([x, y]) => `${x.toFixed(1)}px ${y.toFixed(1)}px`).join(", ");
      const geri = nk.slice().reverse();
      s.clipPath = a <= 0.001 ? "inset(100%)" : !dikey
        ? (ters ? `polygon(${w}px 0px, ${w}px ${h}px, ${pt(geri)})` : `polygon(0px 0px, ${pt(nk)}, 0px ${h}px)`)
        : (ters ? `polygon(0px ${h}px, ${w}px ${h}px, ${pt(geri)})` : `polygon(0px 0px, ${w}px 0px, ${pt(geri)})`);
      const kp = (1 - a) * 20;
      s.transform = !dikey ? `translateX(${(ters ? 1 : -1) * kp}px)` : `translateY(${(ters ? 1 : -1) * kp}px)`;
      if (tepe > 0.02) {
        const kalin = Math.max(3, Math.round(Math.min(w, h) * 0.006));
        const d = nk.map(([x, y], i) => `${i === 0 ? "M" : "L"}${x.toFixed(1)} ${y.toFixed(1)}`).join(" ");
        s.katman = `<svg width="${w}" height="${h}" style="position:absolute;inset:0;overflow:visible"><path d="${d}" fill="none" stroke="rgba(0,0,0,0.34)" `
          + `stroke-width="${kalin * 2.2}" stroke-linejoin="round" style="filter:blur(${kalin}px);opacity:${tepe}"/><path d="${d}" fill="none" `
          + `stroke="${rgba(renk.zemin, 0.92)}" stroke-width="${kalin}" stroke-linejoin="round" opacity="${0.9 * tepe}"/></svg>`;
      }
      return s;
    }
    case "tikla_iris": {
      if (yon === "exiting") return s;
      const a = ACILIS(p);
      const [cx, cy] = ({ sol: [28, 52], sag: [72, 52], yukari: [50, 32], asagi: [50, 68] } as const)[g.yon ?? "sag"];
      const maks = Math.hypot(w, h);
      const r = maks * a;
      s.clipPath = `circle(${r.toFixed(1)}px at ${cx}% ${cy}%)`;
      if (tepe > 0.02) {
        s.katman = `<div style="position:absolute;left:${cx}%;top:${cy}%;width:${(r * 2).toFixed(1)}px;height:${(r * 2).toFixed(1)}px;border-radius:50%;transform:translate(-50%,-50%);border:3px solid ${rgba(renk.vurgu, 0.85 * tepe)};box-shadow:0 0 24px ${rgba(renk.vurgu, 0.45 * tepe)}"></div>`;
      }
      return s;
    }
    case "buton_zoom": {
      if (yon === "exiting") {
        const z = 1 + 1.45 * HIZLAN(p);
        s.transform = `scale(${z.toFixed(4)})`;
        const bul = HIZLAN(p) * 14;
        if (bul > 0.3) s.filter = `blur(${bul.toFixed(2)}px)`;
        s.opacity = String(Math.max(0, 1 - HIZLAN(p) * 1.15));
        return s;
      }
      const y = YERLES(p);
      s.transform = `scale(${(0.78 + 0.22 * y).toFixed(4)})`;
      const bul = (1 - y) * 10;
      if (bul > 0.25) s.filter = `blur(${bul.toFixed(2)}px)`;
      s.opacity = String(Math.min(1, ACILIS(p) * 1.15));
      if (tepe > 0.02) s.katman = tam(`mix-blend-mode:screen;opacity:${0.26 * tepe};background:radial-gradient(circle at 50% 50%, ${rgba(renk.vurgu, 0.7)}, transparent 68%)`);
      return s;
    }
    case "kart_dunyaya": {
      if (yon === "exiting") return s;
      const a = YERLES(p), kenarX = (1 - a) * 18, kenarY = (1 - a) * 20, kose = (1 - a) * 32;
      s.clipPath = `inset(${kenarY.toFixed(2)}% ${kenarX.toFixed(2)}% round ${kose.toFixed(1)}px)`;
      s.transform = `scale(${(0.92 + 0.08 * a).toFixed(4)})`;
      if (tepe > 0.02) {
        s.katman = `<div style="position:absolute;inset:${kenarY.toFixed(2)}% ${kenarX.toFixed(2)}%;border-radius:${kose.toFixed(1)}px;border:2px solid ${rgba(renk.vurgu, 0.75 * tepe)};box-shadow:0 0 28px ${rgba(renk.vurgu, 0.35 * tepe)}"></div>`;
      }
      return s;
    }
    case "bulanik_takas": {
      if (yon === "exiting") {
        const hiz = KIS(p);
        s.filter = `blur(${(hiz * 10).toFixed(2)}px)`;
        s.opacity = String((1 - hiz).toFixed(4));
        return s;
      }
      const y = YERLES(p);
      s.filter = `blur(${((1 - y) * 10).toFixed(2)}px)`;
      s.transform = `scale(${(1.03 - 0.03 * y).toFixed(4)})`;
      s.opacity = String(y.toFixed(4));
      return s;
    }
    case "dip_kesim": {
      const kar = 1 - 0.44 * tepe;
      s.filter = `brightness(${kar.toFixed(3)})`;
      s.opacity = yon === "exiting" ? (p < 0.5 ? "1" : "0") : (p >= 0.5 ? "1" : "0");
      return s;
    }
  }
  return s;
};
