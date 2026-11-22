// Tekil native motion kompozisyonu: tek bir bileşeni seçili stil temasıyla tamamen saydam arka planda render eder.
import React, { useEffect, useMemo, useState } from "react";
import { AbsoluteFill, continueRender, delayRender, staticFile, useVideoConfig } from "remotion";
import { TemaSaglayici, type TemaToken } from "../tema";
import type { Bolgeler, Kutu } from "./cekirdek/tipler";
import { guvenliAlan, yerles } from "./cekirdek/yerlesim";
import { KAYIT } from "./kayit";

export interface TekilProps {
  ad: string;
  param?: Record<string, unknown>;
  en_boy?: "9:16" | "16:9" | "1:1";
  sure?: number | null;
  tema?: (TemaToken & { dosyalar?: Record<string, string> }) | null;
  [k: string]: unknown;
}

const VARSAYILAN_SURE_SN = 2;

export const boyutBul = (en_boy?: TekilProps["en_boy"] | null): { w: number; h: number } => {
  switch (en_boy) {
    case "9:16":
      return { w: 1080, h: 1920 };
    case "16:9":
      return { w: 1920, h: 1080 };
    default:
      return { w: 1080, h: 1080 };
  }
};

export const sureHesapla = (ad: string, sure?: number | null): number => {
  if (typeof sure === "number" && Number.isFinite(sure) && sure > 0) return sure;
  return KAYIT[ad]?.meta.sure.varsayilan ?? VARSAYILAN_SURE_SN;
};

const FontYukle: React.FC<{ ad: string; dosya: string }> = ({ ad, dosya }) => {
  const [h] = useState(() => delayRender(`font ${ad}`));
  useEffect(() => {
    new FontFace(ad, `url(${staticFile(`fonts/${dosya}`)})`, { weight: "100 900" })
      .load()
      .then((f) => document.fonts.add(f))
      .catch(() => undefined)
      .finally(() => continueRender(h));
  }, [ad, dosya, h]);
  return null;
};

const TekilIc: React.FC<TekilProps> = (p) => {
  const { width: w, height: h, durationInFrames } = useVideoConfig();
  const fontlar = useMemo(
    () => Object.entries(p.tema?.dosyalar ?? {}).filter(([ad, dosya]) => Boolean(ad && dosya)),
    [p.tema?.dosyalar],
  );
  const tanim = KAYIT[p.ad];

  const kutu = useMemo<Kutu | null>(() => {
    if (!tanim) return null;
    if (tanim.meta.yer.includes("tam")) return { x: 0, y: 0, w, h };
    const bol: Bolgeler = { guvenli: guvenliAlan(w, h), altyazi: null, yuzler: [], platform: [] };
    return yerles(tanim.meta, w, h, bol, "orta").kutu;
  }, [tanim, w, h]);

  const param = useMemo(() => (tanim ? tanim.sema.parse(p.param ?? {}) : null), [tanim, p.param]);

  if (!tanim || !kutu) return <AbsoluteFill />;

  const { Bilesen } = tanim;
  return (
    <AbsoluteFill>
      {fontlar.map(([ad, dosya]) => <FontYukle key={`${ad}:${dosya}`} ad={ad} dosya={dosya} />)}
      <div style={{ position: "absolute", left: kutu.x, top: kutu.y, width: kutu.w, height: kutu.h }}>
        <Bilesen
          param={param}
          kutu={{ ...kutu, x: 0, y: 0 }}
          hedef={null}
          sureKare={durationInFrames}
          u={Math.min(w, h) / 1080}
        />
      </div>
    </AbsoluteFill>
  );
};

export const Tekil: React.FC<TekilProps> = (p) => (
  <TemaSaglayici tema={p.tema}>
    <TekilIc {...p} />
  </TemaSaglayici>
);
