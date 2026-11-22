// El çizimi fırça alt çizgisi: organik mürekkep katmanları, yumuşak ikonStil gölgesi ve hareketli uç parlamasıyla hızla çekilir.
// Geometri: Özgün çok katmanlı incelen (taper) fırça SVG yolu (remotion random).
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

const VW = 300;
const VH = 40;

const sapma = (tohum: string, genlik: number) => (random(tohum) - 0.5) * 2 * genlik;

const fircaOmurga = (xBas: number, xSon: number, yOfset: number, tohumEk: string) => {
  const adim = 10;
  const noktalar: Array<[number, number]> = [];
  for (let i = 0; i <= adim; i++) {
    const k = i / adim;
    const x = xBas + (xSon - xBas) * k;
    const oran = (x - 8) / (VW - 16);
    const yay = -Math.sin(oran * Math.PI) * 5.2 + (oran - 0.5) * -2.2;
    const y = 21 + yOfset + yay + sapma(`cizim-altcizgi-${tohumEk}-${i}`, 1.25);
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

const UC_YOL = fircaOmurga(8, 292, 0, "uc");
const ORTA_YOL = fircaOmurga(36, 260, -0.3, "orta");
const GOVDE_YOL = fircaOmurga(68, 224, -0.5, "govde");
const IZ_YOL = fircaOmurga(78, 276, 8.5, "iz");

const AltCizgi: React.FC<BilesenProps<z.infer<typeof sema>>> = ({ param, kutu, sureKare, u }) => {
  const t = useTema();
  const a = useAkis(sureKare, meta.giris_sn, meta.cikis_sn);
  const pAna = a.gir;
  const cizAna = 0.12 * a.belir + 0.88 * pAna;
  const pOrta = Math.max(0, (pAna - 0.08) / 0.92);
  const pGovde = Math.max(0, (pAna - 0.16) / 0.84);
  const pIz = a.sirali(1, 3, "settle");
  const otur = a.takip(a.girKare - 2, 185);
  const onX = -7 * u * a.ters;
  const kayX = onX + (otur - pAna) * 3.8 * u + a.cik * 10 * u;
  const kayY = a.nefes * -0.8 * u - a.cik * 2.5 * u;
  const egim = -1.6 * a.ters + (1 - otur) * -0.9 + a.nefes * 0.25;

  const ofset = (uz: number, p: number) => (a.cik > 0 && p > 0.98 ? -uz * a.cik : cizgiOfset(uz, p * (1 - a.cik)));
  const ref = 0.26 * 1080 * u;
  const cizgiPx = ikonKalinlik(t, { x: 0, y: 0, w: ref, h: ref }, u, ref) * 0.72;
  const svgOlcek = Math.max(0.01, Math.min(kutu.w / VW, kutu.h / VH));
  const cizgi = cizgiPx / svgOlcek;
  const renk = t.renk[param.renk];
  const is = ikonStil(t, renk, u);
  const blur = a.hizBulaniklik > 0.08 ? `blur(${(a.hizBulaniklik * 0.35 * u).toFixed(2)}px) ` : "";

  const kIdx = Math.min(UC_YOL.noktalar.length - 1, Math.round(Math.min(1, cizAna) * (UC_YOL.noktalar.length - 1)));
  const [ux, uy] = UC_YOL.noktalar[kIdx];
  const ucParla = Math.sin(Math.min(1, Math.max(0, cizAna)) * Math.PI) * (1 - a.cik);

  const katman = (stroke: string, olcekKal: number, op: number, dx = 0, dy = 0) => (
    <g transform={`translate(${dx} ${dy})`} opacity={op}>
      <path d={UC_YOL.d} fill="none" stroke={stroke} strokeWidth={cizgi * 0.52 * olcekKal} strokeLinecap="round" strokeLinejoin="round" strokeDasharray={UC_YOL.uzunluk} strokeDashoffset={ofset(UC_YOL.uzunluk, cizAna)} />
      <path d={ORTA_YOL.d} fill="none" stroke={stroke} strokeWidth={cizgi * 0.92 * olcekKal} strokeLinecap="round" strokeLinejoin="round" opacity={Math.min(1, pOrta * 6)} strokeDasharray={ORTA_YOL.uzunluk} strokeDashoffset={ofset(ORTA_YOL.uzunluk, pOrta)} />
      <path d={GOVDE_YOL.d} fill="none" stroke={stroke} strokeWidth={cizgi * 1.15 * olcekKal} strokeLinecap="round" strokeLinejoin="round" opacity={Math.min(1, pGovde * 6)} strokeDasharray={GOVDE_YOL.uzunluk} strokeDashoffset={ofset(GOVDE_YOL.uzunluk, pGovde)} />
      <path d={IZ_YOL.d} fill="none" stroke={stroke} strokeWidth={cizgi * 0.34 * olcekKal} strokeLinecap="round" strokeLinejoin="round" opacity={Math.min(1, pIz * 5) * 0.62} strokeDasharray={IZ_YOL.uzunluk} strokeDashoffset={ofset(IZ_YOL.uzunluk, pIz)} />
    </g>
  );

  return (
    <svg
      viewBox={`0 0 ${VW} ${VH}`}
      width={kutu.w}
      height={kutu.h}
      style={{
        overflow: "visible",
        opacity: a.belir * (1 - a.cik * 0.85),
        transform: `translate(${kayX}px, ${kayY}px) rotate(${egim}deg)`,
        filter: `${blur}${is.golge}`,
      }}
    >
      {/* Yarı saydam mürekkep yayılım tabanı */}
      {katman(is.dolgu, 1.55, 0.72, 0.5, 1.0)}
      {/* Organik canlı fırça darbesi */}
      {katman(rgba(renk, 0.94), 1, 1)}
      {/* Üst ışık parıltısı */}
      {katman(is.parilti, 0.32, 0.76, -0.5, -1.0)}
      {/* Uçta ince parlama noktası */}
      {ucParla > 0.02 && (
        <g opacity={ucParla}>
          <circle cx={ux} cy={uy} r={cizgi * 1.05} fill={rgba(renk, 0.36)} />
          <circle cx={ux} cy={uy} r={cizgi * 0.42} fill={is.parilti} />
        </g>
      )}
    </svg>
  );
};

export default tanimla({ meta: meta as never, sema, Bilesen: AltCizgi });
