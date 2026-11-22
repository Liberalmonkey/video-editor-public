// HyperFrames "React adası": metin grafikleri ve SplitReel sahneleri Remotion'daki bileşenlerin aynısıyla çizilir.
// WHY: bkz. wiki/decisions/0051-uctan-uca-hyperframes.md. "remotion" modülü remotion-taklit.tsx'e yönlenir (cli.ts paketi);
// her karede görünür adalar flushSync ile eşzamanlı çizilir, böylece kare yalnız t'nin fonksiyonudur (HyperFrames sözleşmesi).
// Ayrı paket (hf/ada.js): ada gerekmeyen projeye React yüklenmez. calisma.ts her karede window.__ada.ciz(t) çağırır.
import React from "react";
import { flushSync } from "react-dom";
import { createRoot, type Root } from "react-dom/client";
import { FullTitle, STAGE_H, StageScene, T, ez, rgbaOf, temaUygula } from "../../openmontage/remotion-composer/src/SplitReel";
import { MetinGrafik, Vurgu } from "../remotion/MotionMetin";
import { TemaSaglayici, type TemaToken } from "../remotion/tema";
import type { Kaynak, Klip } from "../remotion/tipler";
import { AbsoluteFill, KareSaglayici, useCurrentFrame, useVideoConfig } from "./remotion-taklit";

// derle.ts'in yazdığı ada kaydı. bas/sure kare cinsinden (Remotion Sequence from/durationInFrames ile aynı yuvarlama).
export interface AdaKayit {
  id: string;
  tur: "metin" | "vurgu" | "tam" | "baslik" | "bolunmus";
  bas: number; sure: number;
  klip?: Klip; kaynak?: Kaynak | null; sahne?: any;
}

const YATAY_BASLIK_KAYMA = -530; // Kurgu.tsx ile aynı: FullTitle yatayda alt üçte bire iner

// Kurgu.tsx TamSahne birebir.
const TamSahne: React.FC<{ s: any }> = ({ s }) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const D = Math.round((s.end - s.start) * fps);
  const olcek = width > height ? (height * 0.92) / STAGE_H : 1;
  const ust = width > height ? (height - STAGE_H * olcek) / 2 : 190;
  const zemin = s.bg === "saydam" ? rgbaOf(T.bg, 0.62) : s.bg === "light" ? T.light : T.bg;
  return (
    <AbsoluteFill style={{ background: zemin, opacity: Math.min(ez(frame, 0, 6), 1 - ez(frame, D - 6, D)) }}>
      <div style={{ position: "absolute", left: (width - 1080 * olcek) / 2, top: ust, width: 1080, height: STAGE_H, transformOrigin: "0 0", transform: `scale(${olcek})` }}>
        <StageScene s={s} />
      </div>
    </AbsoluteFill>
  );
};

const Icerik: React.FC<{ a: AdaKayit }> = ({ a }) => {
  const { width, height } = useVideoConfig();
  if (a.tur === "metin") return <MetinGrafik k={a.klip!} m={a.klip!.metin_stil!} />;
  if (a.tur === "vurgu") return <Vurgu k={a.klip!} m={a.klip!.metin_stil!} kaynak={a.kaynak ?? undefined} />;
  if (a.tur === "tam") return <TamSahne s={a.sahne} />;
  if (a.tur === "baslik") return width > height
    ? <AbsoluteFill style={{ transform: `translateY(${YATAY_BASLIK_KAYMA}px)` }}><FullTitle s={a.sahne} /></AbsoluteFill>
    : <FullTitle s={a.sahne} />;
  // Bölünmüş sahne: dikeyde üst kutu, yatayda sol sütun (Kurgu.tsx yatayDuzen).
  if (width > height) {
    const olcek = height / STAGE_H;
    return <div style={{ position: "absolute", left: 0, top: 0, width: 1080, height: STAGE_H, overflow: "hidden", transformOrigin: "0 0", transform: `scale(${olcek})` }}><StageScene s={a.sahne} /></div>;
  }
  return <StageScene s={a.sahne} />;
};

interface Ada { a: AdaKayit; kok: Root; dolu: boolean }

const kur = () => {
  const veri = window.__KURGU;
  const { w, h, fps } = veri.sekans;
  const tema = (veri.tema as TemaToken | undefined) ?? null;
  temaUygula(tema as any); // SplitReel sahneleri (T, F) stilin paletini ve fontunu alır (Kurgu.tsx ile aynı)
  const adalar: Ada[] = [];
  for (const a of (veri.adalar ?? []) as AdaKayit[]) {
    const el = document.getElementById(`ada-${a.id}`);
    if (el) adalar.push({ a, kok: createRoot(el), dolu: false });
  }
  const ciz = (t: number) => {
    const F = Math.round(t * fps);
    for (const o of adalar) {
      const f = F - o.a.bas;
      const icinde = f >= 0 && f < o.a.sure;
      if (!icinde && !o.dolu) continue;
      // Render'da hata saklanmaz (Kurgu.tsx SahneKoruma etkin değil): iş durur, sorun görünür.
      flushSync(() => o.kok.render(icinde
        ? <KareSaglayici value={{ frame: f, fps, width: w, height: h, durationInFrames: o.a.sure }}><TemaSaglayici tema={tema}><Icerik a={o.a} /></TemaSaglayici></KareSaglayici>
        : null));
      o.dolu = icinde;
    }
  };
  window.__ada = { ciz };
};

declare global { interface Window { __KURGU: any; __ada?: { ciz: (t: number) => void } } }
if (typeof window !== "undefined" && window.__KURGU) kur();
