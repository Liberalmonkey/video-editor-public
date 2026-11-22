// Fosforlu kalem bandı: yarı saydam katmanlı organik mürekkep, yumuşak ikonStil gölgesi ve uçta ince ışık parlamasıyla akar.
// Geometri: Özgün deterministik kesik uçlu (chisel) fosforlu bant SVG yolları (remotion random).
import React from "react";
import { random } from "remotion";
import { z } from "zod";
import { ikonStil, rgba, useTema } from "../../../tema";
import { ikonKalinlik } from "../../cekirdek/olcu";
import { cizgiOfset, useAkis } from "../../cekirdek/zaman";
import { tanimla, type BilesenProps } from "../../cekirdek/tipler";
import meta from "./meta.json";

export const sema = z.strictObject({
  renk: z.enum(["vurgu", "ikincil", "olumlu", "olumsuz", "yazi"]).default("vurgu").describe("Tema rengi adı; onaltılık renk yazılmaz"),
});

const VW = 280;
const VH = 56;

const sapma = (tohum: string, genlik: number) => (random(tohum) - 0.5) * 2 * genlik;

const bantYolu = (xBas: number, xSon: number, yMerkez: number, tohum: string) => {
  const adim = 8;
  const noktalar: Array<[number, number]> = [];
  for (let i = 0; i <= adim; i++) {
    const k = i / adim;
    const x = xBas + (xSon - xBas) * k;
    const hafifEgim = (k - 0.5) * -3.4;
    const y = yMerkez + hafifEgim + sapma(`cizim-fosforlu-${tohum}-${i}`, 1.7);
    noktalar.push([x, y]);
  }
  let d = `M ${noktalar[0][0].toFixed(1)} ${noktalar[0][1].toFixed(1)}`;
  let uz = 0;
  for (let i = 1; i < noktalar.length - 1; i++) {
    const [x1, y1] = noktalar[i];
    const [x2, y2] = noktalar[i + 1];
    d += ` Q ${x1.toFixed(1)} ${y1.toFixed(1)} ${((x1 + x2) / 2).toFixed(1)} ${((y1 + y2) / 2).toFixed(1)}`;
    uz += Math.hypot(x1 - noktalar[i - 1][0], y1 - noktalar[i - 1][1]);
  }
  const son = noktalar[noktalar.length - 1];
  const onceki = noktalar[noktalar.length - 2];
  d += ` L ${son[0].toFixed(1)} ${son[1].toFixed(1)}`;
  uz += Math.hypot(son[0] - onceki[0], son[1] - onceki[1]);
  return { d, uzunluk: Math.ceil(uz * 1.05), noktalar };
};

const ANA_BANT = bantYolu(10, 270, 29, "ana");
const IC_KATMAN = bantYolu(16, 264, 27.2, "ic");
const KENAR_UST = bantYolu(12, 268, 16.5, "ust");
const KENAR_ALT = bantYolu(14, 266, 40.5, "alt");

const Fosforlu: React.FC<BilesenProps<z.infer<typeof sema>>> = ({ param, kutu, sureKare, u }) => {
  const t = useTema();
  const a = useAkis(sureKare, meta.giris_sn, meta.cikis_sn);
  const pAna = a.gir;
  const cizAna = 0.1 * a.belir + 0.9 * pAna;
  const pIc = a.sirali(1, 2, "enter");
  const pKenar = a.sirali(1, 3, "settle");
  const onX = -6 * u * a.ters;
  const otur = a.takip(a.girKare - 1, 160);
  const baskiY = (0.92 + 0.08 * otur) * (1 + 0.012 * a.nefes);
  const egim = -1.8 * a.ters - 0.6 + a.nefes * 0.25;

  const ofset = (uz: number, p: number) => (a.cik > 0 && p > 0.98 ? -uz * a.cik : cizgiOfset(uz, p * (1 - a.cik)));
  const ref = 0.26 * 1080 * u;
  const cizgiPx = ikonKalinlik(t, { x: 0, y: 0, w: ref, h: ref }, u, ref) * 0.72;
  const svgOlcek = Math.max(0.01, Math.min(kutu.w / VW, kutu.h / VH));
  const cizgi = cizgiPx / svgOlcek;
  const bantKalin = Math.min(34, Math.max(22, cizgi * 4.2));
  const icKalin = bantKalin * 0.62;
  const kenarKalin = Math.max(1.2, cizgi * 0.28);
  const renk = t.renk[param.renk];
  const is = ikonStil(t, renk, u);
  const blur = a.hizBulaniklik > 0.08 ? `blur(${(a.hizBulaniklik * 0.35 * u).toFixed(2)}px) ` : "";
  const ucX = 10 + 260 * Math.min(1, cizAna);
  const ucParla = Math.sin(Math.min(1, Math.max(0, cizAna)) * Math.PI) * (1 - a.cik);

  return (
    <svg
      viewBox={`0 0 ${VW} ${VH}`}
      width={kutu.w}
      height={kutu.h}
      style={{
        overflow: "visible",
        opacity: a.belir * (1 - a.cik * 0.9),
        transform: `translateX(${onX + a.cik * 9 * u}px) scaleY(${baskiY}) skewX(-8deg) rotate(${egim}deg)`,
        filter: `${blur}${is.golge}`,
      }}
    >
      {/* Yarı saydam ana fosforlu katman */}
      <path
        d={ANA_BANT.d}
        fill="none"
        stroke={rgba(renk, 0.44)}
        strokeWidth={bantKalin}
        strokeLinecap="butt"
        strokeLinejoin="round"
        strokeDasharray={ANA_BANT.uzunluk}
        strokeDashoffset={ofset(ANA_BANT.uzunluk, cizAna)}
      />
      {/* İç yoğun mürekkep çekirdeği */}
      <path
        d={IC_KATMAN.d}
        fill="none"
        stroke={rgba(renk, 0.3)}
        strokeWidth={icKalin}
        strokeLinecap="butt"
        strokeLinejoin="round"
        opacity={Math.min(1, pIc * 5)}
        strokeDasharray={IC_KATMAN.uzunluk}
        strokeDashoffset={ofset(IC_KATMAN.uzunluk, pIc)}
      />
      {/* Üst ışık parlaması + alt mürekkep birikimi */}
      <path
        d={KENAR_UST.d}
        fill="none"
        stroke={is.parilti}
        strokeWidth={kenarKalin * 1.1}
        strokeLinecap="round"
        opacity={Math.min(1, pKenar * 5) * 0.72}
        strokeDasharray={KENAR_UST.uzunluk}
        strokeDashoffset={ofset(KENAR_UST.uzunluk, pKenar)}
      />
      <path
        d={KENAR_ALT.d}
        fill="none"
        stroke={rgba(renk, 0.6)}
        strokeWidth={kenarKalin}
        strokeLinecap="round"
        opacity={Math.min(1, pKenar * 5) * 0.65}
        strokeDasharray={KENAR_ALT.uzunluk}
        strokeDashoffset={ofset(KENAR_ALT.uzunluk, pKenar)}
      />
      {/* Kesik kalem ucu parlama çizgisi */}
      {ucParla > 0.02 && (
        <line
          x1={ucX}
          y1={14}
          x2={ucX}
          y2={42}
          stroke={is.parilti}
          strokeWidth={Math.max(2, cizgi * 0.45)}
          strokeLinecap="round"
          opacity={ucParla * 0.85}
        />
      )}
    </svg>
  );
};

export default tanimla({ meta: meta as never, sema, Bilesen: Fosforlu });
