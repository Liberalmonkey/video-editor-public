// El çizimi üstünü çizme: organik katmanlı kalem mürekkebi, yumuşak ikonStil gölgesi ve uç parlamasıyla kararlıca çizilir.
// Geometri: Özgün deterministik el çizimi SVG yolu (remotion random).
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
  cizgi: z.enum(["tek", "cift"]).default("tek").describe("Tek çizgi mi çift çapraz çizgi mi"),
});

const VW = 260;
const VH = 64;

const sapma = (tohum: string, genlik: number) => (random(tohum) - 0.5) * 2 * genlik;

const darbeYolu = (x1: number, y1: number, x2: number, y2: number, kavis: number, tohum: string) => {
  const adim = 8;
  const noktalar: Array<[number, number]> = [];
  for (let i = 0; i <= adim; i++) {
    const k = i / adim;
    const x = x1 + (x2 - x1) * k + sapma(`${tohum}-x-${i}`, 1.4);
    const y = y1 + (y2 - y1) * k + Math.sin(k * Math.PI) * kavis + sapma(`${tohum}-y-${i}`, 1.8);
    noktalar.push([x, y]);
  }
  let d = `M ${noktalar[0][0].toFixed(1)} ${noktalar[0][1].toFixed(1)}`;
  let uz = 0;
  for (let i = 1; i < noktalar.length - 1; i++) {
    const [ax, ay] = noktalar[i];
    const [bx, by] = noktalar[i + 1];
    d += ` Q ${ax.toFixed(1)} ${ay.toFixed(1)} ${((ax + bx) / 2).toFixed(1)} ${((ay + by) / 2).toFixed(1)}`;
    uz += Math.hypot(ax - noktalar[i - 1][0], ay - noktalar[i - 1][1]);
  }
  const son = noktalar[noktalar.length - 1];
  const onceki = noktalar[noktalar.length - 2];
  d += ` L ${son[0].toFixed(1)} ${son[1].toFixed(1)}`;
  uz += Math.hypot(son[0] - onceki[0], son[1] - onceki[1]);
  return { d, uzunluk: Math.ceil(uz * 1.05), noktalar };
};

const BIRINCI = darbeYolu(10, 44, 250, 20, -4.5, "cizim-ustunuciz-1");
const IKINCI = darbeYolu(14, 18, 246, 46, 3.8, "cizim-ustunuciz-2");

const UstunuCiz: React.FC<BilesenProps<z.infer<typeof sema>>> = ({ param, kutu, sureKare, u }) => {
  const t = useTema();
  const a = useAkis(sureKare, meta.giris_sn, meta.cikis_sn);
  const cift = param.cizgi === "cift";
  const p1 = a.sirali(0, 3, "emphasis");
  const p2 = cift ? a.sirali(1, 4, "emphasis") : 0;
  const ciz1 = 0.12 * a.belir + 0.88 * p1;

  const onX = -8 * u * a.ters;
  const onY = 2.8 * u * a.ters;
  const darbeKare = cift ? a.girKare + 2 : a.girKare - 1;
  const tit = Math.max(0, Math.min(1, a.vurgu(darbeKare, Math.round(0.26 * a.fps))));
  const sarsintiX = Math.sin(tit * Math.PI * 2.5) * (1 - tit) * 3.4 * u;
  const otur = a.takip(darbeKare - 1, 195);

  const ofset = (uz: number, p: number) => (a.cik > 0 && p > 0.98 ? -uz * a.cik : cizgiOfset(uz, p * (1 - a.cik)));
  const ref = 0.26 * 1080 * u;
  const cizgiPx = ikonKalinlik(t, { x: 0, y: 0, w: ref, h: ref }, u, ref) * 0.72;
  const svgOlcek = Math.max(0.01, Math.min(kutu.w / VW, kutu.h / VH));
  const cizgi = cizgiPx / svgOlcek;
  const renk = t.renk[param.renk];
  const is = ikonStil(t, renk, u);
  const blur = a.hizBulaniklik > 0.08 ? `blur(${(a.hizBulaniklik * 0.35 * u).toFixed(2)}px) ` : "";

  const aktifYol = cift && p2 > 0.05 ? IKINCI : BIRINCI;
  const aktifP = cift && p2 > 0.05 ? p2 : ciz1;
  const ucIdx = Math.min(aktifYol.noktalar.length - 1, Math.round(Math.min(1, aktifP) * (aktifYol.noktalar.length - 1)));
  const [ux, uy] = aktifYol.noktalar[ucIdx];
  const ucParla = Math.sin(Math.min(1, Math.max(0, aktifP)) * Math.PI) * (1 - a.cik);

  const ciz = (stroke: string, width: number, op = 1, dx = 0, dy = 0) => (
    <g transform={`translate(${dx} ${dy})`} opacity={op}>
      <path
        d={BIRINCI.d}
        fill="none"
        stroke={stroke}
        strokeWidth={width}
        strokeLinecap="round"
        strokeLinejoin="round"
        opacity={Math.min(1, ciz1 * 6)}
        strokeDasharray={BIRINCI.uzunluk}
        strokeDashoffset={ofset(BIRINCI.uzunluk, ciz1)}
      />
      {cift && (
        <path
          d={IKINCI.d}
          fill="none"
          stroke={stroke}
          strokeWidth={width}
          strokeLinecap="round"
          strokeLinejoin="round"
          opacity={Math.min(1, p2 * 6)}
          strokeDasharray={IKINCI.uzunluk}
          strokeDashoffset={ofset(IKINCI.uzunluk, p2)}
        />
      )}
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
        transform: `translate(${onX + sarsintiX + a.cik * 8 * u}px, ${onY + a.nefes * -0.8 * u - a.cik * 3 * u}px) scale(${0.96 + 0.04 * otur + 0.008 * a.nefes})`,
        filter: `${blur}${is.golge}`,
      }}
    >
      {/* Organik mürekkep yayılım tabanı */}
      {ciz(is.dolgu, cizgi * 1.62, 0.72, 0.5, 1.0)}
      {/* Ana kalem vuruşu */}
      {ciz(rgba(renk, 0.95), cizgi, 1)}
      {/* İnce üst parlaklık vurgusu */}
      {ciz(is.parilti, cizgi * 0.28, 0.78, -0.6, -0.9)}
      {/* Uçta ince parlama noktası */}
      {ucParla > 0.02 && (
        <g opacity={ucParla}>
          <circle cx={ux} cy={uy} r={cizgi * 1.05} fill={rgba(renk, 0.35)} />
          <circle cx={ux} cy={uy} r={cizgi * 0.44} fill={is.parilti} />
        </g>
      )}
    </svg>
  );
};

export default tanimla({ meta: meta as never, sema, Bilesen: UstunuCiz });
