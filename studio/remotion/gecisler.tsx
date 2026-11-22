// V1 kesim geçişleri (ADR 0045). Kural: sonraki çekim her karede görünür, düz tam kare renk en çok 2 kare;
// orta nokta kesimin üstündedir (giren klip sürenin yarısı kadar önden başlar, çıkan klip yarısı kadar uzar).
// Resmi sunumlar @remotion/transitions'tan, aynı arayüzle (presentationProgress/Direction) özel sunumlar burada.
import React from "react";
import { AbsoluteFill, Easing, random } from "remotion";
import { clockWipe } from "@remotion/transitions/clock-wipe";
import { fade } from "@remotion/transitions/fade";
import { iris } from "@remotion/transitions/iris";
import { slide } from "@remotion/transitions/slide";
import { wipe } from "@remotion/transitions/wipe";
import { rgba, useTema } from "./tema";
import type { Gecis, Yon } from "./tipler";

// flip yok: yapısı gereği sürenin yarısında gelen çekim arkası dönük, görünmez (%80 ölçütünü karşılamaz).
export const ORTA_GECIS = [
  "sil", "kay", "saat", "iris", "kirbac", "isik", "piksel",
  "zoom_kirbac", "film_yanigi", "bolunme", "bozulma", "yirtma",
] as const;
export type OrtaGecis = (typeof ORTA_GECIS)[number];
export const ortaMi = (g?: Gecis | null): g is Gecis & { tur: OrtaGecis } => !!g && (ORTA_GECIS as readonly string[]).includes(g.tur);
// Çıkan klip de hareket eder mi (kaydırma, kırbaç, zoom kırbaç, bozulma). Diğerlerinde çıkan klip altta sakin durur.
const IKI_YONLU: OrtaGecis[] = ["kay", "kirbac", "zoom_kirbac", "bozulma"];
// Alanı karesel büyüyen açılışlar hızlı açılır: ilk karelerde de gelen çekim görünür.
const ACILIS = Easing.bezier(0.22, 0.8, 0.36, 1);
const KIS = Easing.bezier(0.65, 0, 0.35, 1); // orta noktası hızlı: kesim en hızlı anda
const YERLES = Easing.bezier(0.16, 1, 0.3, 1); // hızlı sönümlü oturma
const HIZLAN = Easing.bezier(0.55, 0, 1, 0.45);
const egriSec = (tur: string) => (["saat", "iris", "isik", "piksel", "zoom_kirbac", "film_yanigi", "bolunme", "bozulma", "yirtma"].includes(tur) ? ACILIS : KIS);
export const cikanHareketli = (g?: Gecis | null) => ortaMi(g) && IKI_YONLU.includes(g.tur);

type Yonlu = "from-left" | "from-right" | "from-top" | "from-bottom";
// yon: görüntünün gittiği yön (it ve savur ile aynı anlam): "sol" → yeni çekim sağdan gelir.
const GELIS: Record<Yon, Yonlu> = { sol: "from-right", sag: "from-left", yukari: "from-bottom", asagi: "from-top" };

interface Ozel { ilerleme: number; yon: "entering" | "exiting"; g: Gecis; w: number; h: number; children: React.ReactNode }

// Kırbaç: iki çekim aynı yönde hızla kayar; orta noktada yumuşak yön bulanıklığı, hareket ekseninde ince ölçek esnemesi.
const Kirbac: React.FC<Ozel> = ({ ilerleme, yon, g, w, h, children }) => {
  const a = KIS(ilerleme);
  const tepe = Math.sin(Math.PI * ilerleme);
  const [vx, vy] = ({ sol: [-1, 0], sag: [1, 0], yukari: [0, -1], asagi: [0, 1] } as const)[g.yon ?? "sol"];
  const kay = yon === "entering" ? 1 - a : -a;
  const bul = Math.pow(tepe, 1.25) * 28;
  const esne = 1 + 0.045 * tepe;
  const sx = vx ? esne : 1 + 0.015 * tepe;
  const sy = vy ? esne : 1 + 0.015 * tepe;
  const parl = 1 + 0.08 * tepe;
  const filtre = [bul > 0.4 && `blur(${bul.toFixed(2)}px)`, parl > 1.005 && `brightness(${parl.toFixed(3)})`].filter(Boolean).join(" ");
  return (
    <AbsoluteFill style={{ transform: `translate(${vx * kay * w}px, ${vy * kay * h}px) scale(${sx}, ${sy})`, filter: filtre || undefined }}>
      {children}
    </AbsoluteFill>
  );
};

// Işık sızıntısı: yumuşak kenarlı süpürme, hafif ölçek oturması ve süpürme kenarında tepe yapan sıcak ışık.
const Isik: React.FC<Ozel> = ({ ilerleme, yon, w, h, children }) => {
  const t = useTema();
  const tepe = Math.sin(Math.PI * ilerleme);
  if (yon === "exiting") {
    const s = 1 + 0.025 * ilerleme;
    return <AbsoluteFill style={{ transform: `scale(${s})`, filter: tepe > 0.02 ? `brightness(${(1 + 0.1 * tepe).toFixed(3)})` : undefined }}>{children}</AbsoluteFill>;
  }
  const a = ACILIS(ilerleme);
  const x = 15 + 70 * ilerleme;
  const kenar = -20 + 150 * a; // % : yumuşak kenar soldan sağa geçer
  const maske = `linear-gradient(102deg, rgba(0,0,0,1) ${kenar - 28}%, transparent ${kenar}%)`;
  const bul = (1 - a) * 3.5;
  const s = 1.035 - 0.035 * YERLES(ilerleme);
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{ WebkitMaskImage: maske, maskImage: maske, transform: `scale(${s})`, filter: bul > 0.25 ? `blur(${bul.toFixed(2)}px)` : undefined }}>
        {children}
      </AbsoluteFill>
      <AbsoluteFill style={{ mixBlendMode: "screen", opacity: 0.52 * tepe, background: `radial-gradient(ellipse ${w * 0.9}px ${h * 0.7}px at ${x}% 32%, ${rgba(t.renk.ikincil, 0.85)}, ${rgba(t.renk.vurgu, 0.42)} 46%, transparent 76%)` }} />
    </AbsoluteFill>
  );
};

// Piksel çözülme: yeni çekim rastgele bloklarla belirir (blok sırası tohumla sabit, kare kareye aynı).
const Piksel: React.FC<Ozel> = ({ ilerleme, yon, w, h, children }) => {
  if (yon === "exiting") return <AbsoluteFill>{children}</AbsoluteFill>;
  const n = 14, b = Math.ceil(w / n), m = Math.ceil(h / b);
  let yol = "";
  for (let j = 0; j < m; j++) for (let i = 0; i < n; i++) {
    if (random(`piksel-${i}-${j}`) < ACILIS(ilerleme)) yol += `M${i * b} ${j * b}h${b}v${b}h${-b}z`;
  }
  return <AbsoluteFill style={{ clipPath: yol ? `path('${yol}')` : "inset(100%)" }}>{children}</AbsoluteFill>;
};

// Zoom kırbaç: giden çekim hızla büyüyüp hafif bulanıklaşır; gelen çekim 1.18→1.0 hızlı sönümlü oturur + orta karede ince vurgu parlaması.
const ZoomKirbac: React.FC<Ozel> = ({ ilerleme, yon, w, h, children }) => {
  const t = useTema();
  const tepe = Math.sin(Math.PI * ilerleme);
  if (yon === "exiting") {
    const s = 1 + 0.36 * HIZLAN(ilerleme);
    const bul = tepe * 12;
    return <AbsoluteFill style={{ transform: `scale(${s})`, filter: bul > 0.3 ? `blur(${bul.toFixed(2)}px)` : undefined }}>{children}</AbsoluteFill>;
  }
  const a = ACILIS(ilerleme);
  const s = 1.18 - 0.18 * YERLES(ilerleme);
  const bul = (1 - YERLES(ilerleme)) * 9;
  // Yumuşak radyal açılış: ilk kareden itibaren merkezde yeni çekim net görünür, düz tam kare oluşmaz.
  const ic = Math.max(0, a * 125 - 12);
  const dis = a * 135;
  const maske = a <= 0.001
    ? "radial-gradient(circle at 50% 50%, transparent 0%, transparent 100%)"
    : `radial-gradient(ellipse ${w * 0.8}px ${h * 0.8}px at 50% 50%, rgba(0,0,0,1) ${ic}%, transparent ${dis}%)`;
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{
        WebkitMaskImage: maske, maskImage: maske,
        transform: `scale(${s})`,
        filter: bul > 0.25 ? `blur(${bul.toFixed(2)}px)` : undefined,
      }}>
        {children}
      </AbsoluteFill>
      <AbsoluteFill style={{
        mixBlendMode: "screen",
        opacity: 0.42 * tepe,
        background: `radial-gradient(ellipse ${w * 0.85}px ${h * 0.65}px at 50% 50%, ${rgba(t.renk.vurgu, 0.72)} 0%, ${rgba(t.renk.ikincil, 0.28)} 42%, transparent 74%)`,
      }} />
    </AbsoluteFill>
  );
};

// Film yanığı: çok katmanlı organik sıcak ışık sızıntısı + yumuşak diyagonal maske açılışı (düz tam kare yok).
const FilmYanigi: React.FC<Ozel> = ({ ilerleme, yon, w, h, children }) => {
  const t = useTema();
  const tepe = Math.sin(Math.PI * ilerleme);
  if (yon === "exiting") {
    return <AbsoluteFill style={{ filter: tepe > 0.02 ? `brightness(${(1 + 0.12 * tepe).toFixed(3)}) saturate(${(1 + 0.18 * tepe).toFixed(3)})` : undefined }}>{children}</AbsoluteFill>;
  }
  const a = ACILIS(ilerleme);
  const kenar = 138 * a;
  const maske = a <= 0.001
    ? "linear-gradient(124deg, transparent 0%, transparent 100%)"
    : `linear-gradient(124deg, rgba(0,0,0,1) ${kenar - 20}%, transparent ${kenar}%)`;
  const s = 1.03 - 0.03 * YERLES(ilerleme);
  const x1 = 10 + 82 * ilerleme;
  const x2 = 85 - 65 * ilerleme;
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{ WebkitMaskImage: maske, maskImage: maske, transform: `scale(${s})` }}>{children}</AbsoluteFill>
      {/* Birincil sıcak film sızıntısı */}
      <AbsoluteFill style={{
        mixBlendMode: "screen",
        opacity: 0.5 * tepe,
        background: `radial-gradient(ellipse ${w * 0.75}px ${h * 0.6}px at ${x1}% 28%, ${rgba(t.renk.vurgu, 0.88)} 0%, ${rgba(t.renk.ikincil, 0.35)} 45%, transparent 76%)`,
      }} />
      {/* İkincil organik karşı köşe parlaması */}
      <AbsoluteFill style={{
        mixBlendMode: "screen",
        opacity: 0.4 * tepe,
        background: `radial-gradient(ellipse ${w * 0.65}px ${h * 0.55}px at ${x2}% 72%, ${rgba(t.renk.ikincil, 0.8)} 0%, ${rgba(t.renk.vurgu, 0.25)} 48%, transparent 78%)`,
      }} />
      {/* Yanık kenar boyunca ince halation çizgisi */}
      <AbsoluteFill style={{
        mixBlendMode: "screen",
        opacity: 0.35 * tepe,
        background: `linear-gradient(124deg, transparent ${kenar - 26}%, ${rgba(t.renk.vurgu, 0.6)} ${kenar - 10}%, ${rgba(t.renk.yazi, 0.35)} ${kenar - 4}%, transparent ${kenar + 12}%)`,
      }} />
    </AbsoluteFill>
  );
};

// Bölünme: iki kanatlı dikey/yatay split açılış — ortadan dışa kapı gibi açılıp yeni çekimi gösterir.
const Bolunme: React.FC<Ozel> = ({ ilerleme, yon, g, w, h, children }) => {
  const t = useTema();
  if (yon === "exiting") return <AbsoluteFill>{children}</AbsoluteFill>;
  const a = ACILIS(ilerleme);
  const tepe = Math.sin(Math.PI * ilerleme);
  const yatay = g.yon === "yukari" || g.yon === "asagi";
  const kapali = (1 - a) * 50;
  const clip = yatay ? `inset(${kapali}% 0 ${kapali}% 0)` : `inset(0 ${kapali}% 0 ${kapali}%)`;
  const s = 1.05 - 0.05 * YERLES(ilerleme);
  const cizgi = Math.max(2, Math.round(Math.min(w, h) * 0.004));
  const kenarStil = (pos: number): React.CSSProperties => (yatay
    ? { position: "absolute", left: 0, right: 0, top: `${pos}%`, height: cizgi, transform: "translateY(-50%)", background: t.renk.vurgu, opacity: 0.85 * tepe, boxShadow: `0 0 ${cizgi * 4}px ${rgba(t.renk.vurgu, 0.7)}` }
    : { position: "absolute", top: 0, bottom: 0, left: `${pos}%`, width: cizgi, transform: "translateX(-50%)", background: t.renk.vurgu, opacity: 0.85 * tepe, boxShadow: `0 0 ${cizgi * 4}px ${rgba(t.renk.vurgu, 0.7)}` });
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{ clipPath: clip, transform: `scale(${s})` }}>{children}</AbsoluteFill>
      {tepe > 0.02 && <div style={kenarStil(kapali)} />}
      {tepe > 0.02 && <div style={kenarStil(100 - kapali)} />}
    </AbsoluteFill>
  );
};

// Bozulma: kontrollü RGB/şerit kayması ile yeni çekimin 6 yatay şeritle keskin açılışı (neon/retro/piksel için).
const BOZ_SIRA = [0, 3, 1, 5, 2, 4];
const Bozulma: React.FC<Ozel> = ({ ilerleme, yon, w, h, children }) => {
  const t = useTema();
  const tepe = Math.sin(Math.PI * ilerleme);
  if (yon === "exiting") {
    const kay = (random(`boz-ex-${Math.floor(ilerleme * 12)}`) - 0.5) * 18 * tepe;
    return <AbsoluteFill style={{ transform: `translateX(${kay}px)`, filter: tepe > 0.05 ? `hue-rotate(${(tepe * 18).toFixed(1)}deg) contrast(${(1 + 0.14 * tepe).toFixed(2)})` : undefined }}>{children}</AbsoluteFill>;
  }
  const a = ACILIS(ilerleme);
  const n = 6, sh = Math.ceil(h / n);
  let yol = "";
  for (let i = 0; i < n; i++) {
    const bas = BOZ_SIRA[i] * 0.055;
    const p = Math.max(0, Math.min(1, (a - bas) / (1 - 0.275)));
    const bw = Math.round(w * p);
    if (bw > 0) {
      const bx = i % 2 === 0 ? 0 : w - bw;
      yol += `M${bx} ${i * sh}h${bw}v${sh}h${-bw}z`;
    }
  }
  const kay = (1 - a) * (Math.floor(ilerleme * 12) % 2 === 0 ? 1 : -1) * Math.round(w * 0.035);
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{ clipPath: yol ? `path('${yol}')` : "inset(100%)", transform: kay ? `translateX(${kay}px)` : undefined }}>{children}</AbsoluteFill>
      {/* Kontrollü kromatik/tarama şerit parlamaları (ince bant, kareyi kapatmaz) */}
      {tepe > 0.05 && [1, 4].map((idx) => (
        <div key={idx} style={{
          position: "absolute", left: 0, right: 0,
          top: `${(idx + 0.45) * (100 / n)}%`,
          height: Math.max(3, Math.round(sh * 0.08)),
          background: `linear-gradient(90deg, transparent 5%, ${rgba(idx === 1 ? t.renk.vurgu : t.renk.ikincil, 0.72)} 35%, ${rgba(t.renk.yazi, 0.5)} 50%, ${rgba(idx === 1 ? t.renk.ikincil : t.renk.vurgu, 0.72)} 70%, transparent 95%)`,
          mixBlendMode: "screen", opacity: 0.7 * tepe,
          transform: `translateX(${(idx === 1 ? 1 : -1) * 14 * tepe}px)`,
        }} />
      ))}
    </AbsoluteFill>
  );
};

// Yırtma: organik dalgalı kâğıt kenarıyla kayarak açılış + ince gölge ve kâğıt lifi kenarı (editoryal/kolaj için).
const Yirtma: React.FC<Ozel> = ({ ilerleme, yon, g, w, h, children }) => {
  const t = useTema();
  if (yon === "exiting") return <AbsoluteFill>{children}</AbsoluteFill>;
  const a = ACILIS(ilerleme);
  const tepe = Math.sin(Math.PI * ilerleme);
  const adim = 20;
  const yonTip = g.yon ?? "sol";
  const dikey = yonTip === "yukari" || yonTip === "asagi";
  const ters = yonTip === "sol" || yonTip === "yukari"; // sol: sağdan sola açılır
  const dalga = (j: number) => (random(`yirt-${j}`) - 0.5) * 0.05 * tepe;
  const noktalar: [number, number][] = [];
  if (!dikey) {
    const bazX = ters ? (1 - a) * w : a * w;
    for (let j = 0; j <= adim; j++) {
      const py = (j / adim) * h;
      const px = Math.max(0, Math.min(w, bazX + dalga(j) * w));
      noktalar.push([px, py]);
    }
  } else {
    const bazY = ters ? (1 - a) * h : a * h;
    for (let j = 0; j <= adim; j++) {
      const px = (j / adim) * w;
      const py = Math.max(0, Math.min(h, bazY + dalga(j) * h));
      noktalar.push([px, py]);
    }
  }
  const kenarYolu = noktalar.map(([x, y], i) => `${i === 0 ? "M" : "L"}${x.toFixed(1)} ${y.toFixed(1)}`).join(" ");
  let clipPoligon: string;
  if (a <= 0.001) {
    clipPoligon = "inset(100%)";
  } else if (!dikey) {
    const kenar = noktalar.map(([x, y]) => `${x.toFixed(1)}px ${y.toFixed(1)}px`).join(", ");
    clipPoligon = ters ? `polygon(${w}px 0px, ${w}px ${h}px, ${noktalar.slice().reverse().map(([x, y]) => `${x.toFixed(1)}px ${y.toFixed(1)}px`).join(", ")})`
      : `polygon(0px 0px, ${kenar}, 0px ${h}px)`;
  } else {
    const kenar = noktalar.map(([x, y]) => `${x.toFixed(1)}px ${y.toFixed(1)}px`).join(", ");
    clipPoligon = ters ? `polygon(0px ${h}px, ${w}px ${h}px, ${noktalar.slice().reverse().map(([x, y]) => `${x.toFixed(1)}px ${y.toFixed(1)}px`).join(", ")})`
      : `polygon(0px 0px, ${w}px 0px, ${noktalar.slice().reverse().map(([x, y]) => `${x.toFixed(1)}px ${y.toFixed(1)}px`).join(", ")})`;
  }
  const kayPx = (1 - a) * 20;
  const kay = !dikey ? `translateX(${(ters ? 1 : -1) * kayPx}px)` : `translateY(${(ters ? 1 : -1) * kayPx}px)`;
  const kalin = Math.max(3, Math.round(Math.min(w, h) * 0.006));
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{ clipPath: clipPoligon, transform: kay }}>{children}</AbsoluteFill>
      {tepe > 0.02 && (
        <svg width={w} height={h} style={{ position: "absolute", inset: 0, overflow: "visible", pointerEvents: "none" }}>
          <path d={kenarYolu} fill="none" stroke="rgba(0,0,0,0.34)" strokeWidth={kalin * 2.2} strokeLinejoin="round"
            style={{ filter: `blur(${kalin}px)`, opacity: tepe }} />
          <path d={kenarYolu} fill="none" stroke={rgba(t.renk.zemin, 0.92)} strokeWidth={kalin} strokeLinejoin="round" opacity={0.9 * tepe} />
        </svg>
      )}
    </AbsoluteFill>
  );
};

const OZEL: Partial<Record<OrtaGecis, React.FC<Ozel>>> = {
  kirbac: Kirbac, isik: Isik, piksel: Piksel,
  zoom_kirbac: ZoomKirbac, film_yanigi: FilmYanigi, bolunme: Bolunme, bozulma: Bozulma, yirtma: Yirtma,
};

export const GecisSarici: React.FC<{ g: Gecis; ilerleme: number; yon: "entering" | "exiting"; w: number; h: number; sureKare: number; children: React.ReactNode }> = ({ g, ilerleme, yon, w, h, sureKare, children }) => {
  const p = Math.max(0, Math.min(1, ilerleme));
  const O = OZEL[g.tur as OrtaGecis];
  if (O) return <O ilerleme={p} yon={yon} g={g} w={w} h={h}>{children}</O>;
  const yonlu = GELIS[g.yon ?? "sol"];
  const sunum = g.tur === "sil" ? wipe({ direction: yonlu }) : g.tur === "kay" ? slide({ direction: yonlu }) : g.tur === "saat" ? clockWipe({ width: w, height: h })
    : g.tur === "iris" ? iris({ width: w, height: h }) : fade();
  const C = sunum.component as React.FC<any>;
  return <C presentationProgress={egriSec(g.tur)(p)} presentationDirection={yon} passedProps={sunum.props} presentationDurationInFrames={sureKare}
    onElementImage={() => undefined} onUnmount={() => undefined} bothEnteringAndExiting={IKI_YONLU.includes(g.tur as OrtaGecis)}>{children}</C>;
};
