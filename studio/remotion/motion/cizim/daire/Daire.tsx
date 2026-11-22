// El çizimi oval vurgu: organik katmanlı mürekkep vuruşu, yumuşak ikonStil gölgesi ve çizim ucunda ince parlamayla kapanır.
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
});

const VW = 240;
const VH = 144;

const sapma = (tohum: string, genlik: number) => (random(tohum) - 0.5) * 2 * genlik;

const daireYolu = () => {
  const cx = VW / 2;
  const cy = VH / 2;
  const rx = 100;
  const ry = 54;
  const adim = 18;
  const basAci = -Math.PI * 0.72;
  const toplamAci = Math.PI * 2.21;
  const noktalar: Array<[number, number]> = [];
  for (let i = 0; i <= adim; i++) {
    const k = i / adim;
    const aci = basAci + k * toplamAci;
    const binme = k > 0.85 ? (k - 0.85) * 22 : 0;
    const rX = rx + binme + sapma(`cizim-daire-rx-${i}`, 3.8);
    const rY = ry + binme * 0.55 + sapma(`cizim-daire-ry-${i}`, 2.9);
    noktalar.push([cx + Math.cos(aci) * rX, cy + Math.sin(aci) * rY]);
  }
  let d = `M ${noktalar[0][0].toFixed(1)} ${noktalar[0][1].toFixed(1)}`;
  let uz = 0;
  for (let i = 1; i < noktalar.length - 1; i++) {
    const [x1, y1] = noktalar[i];
    const [x2, y2] = noktalar[i + 1];
    const mx = (x1 + x2) / 2;
    const my = (y1 + y2) / 2;
    d += ` Q ${x1.toFixed(1)} ${y1.toFixed(1)} ${mx.toFixed(1)} ${my.toFixed(1)}`;
    uz += Math.hypot(x1 - noktalar[i - 1][0], y1 - noktalar[i - 1][1]);
  }
  const son = noktalar[noktalar.length - 1];
  const onceki = noktalar[noktalar.length - 2];
  d += ` L ${son[0].toFixed(1)} ${son[1].toFixed(1)}`;
  uz += Math.hypot(son[0] - onceki[0], son[1] - onceki[1]);
  return { d, uzunluk: Math.ceil(uz * 1.06), noktalar };
};

const { d: YOL, uzunluk: UZUNLUK, noktalar: NOKTALAR } = daireYolu();

const ucNokta = (p: number): [number, number] => {
  const k = Math.max(0, Math.min(1, p)) * (NOKTALAR.length - 1);
  const i = Math.min(NOKTALAR.length - 2, Math.floor(k));
  const f = k - i;
  return [NOKTALAR[i][0] + (NOKTALAR[i + 1][0] - NOKTALAR[i][0]) * f, NOKTALAR[i][1] + (NOKTALAR[i + 1][1] - NOKTALAR[i][1]) * f];
};

const Daire: React.FC<BilesenProps<z.infer<typeof sema>>> = ({ param, kutu, sureKare, u }) => {
  const t = useTema();
  const a = useAkis(sureKare, meta.giris_sn, meta.cikis_sn);
  const ciz = 0.1 * a.belir + 0.9 * a.gir;
  const onAci = -3.4 * a.ters;
  const otur = a.takip(a.girKare - 2, 165);
  const titKare = Math.floor(a.f / 3);
  const titX = sapma(`cizim-daire-tx-${titKare}`, 0.7) * u;
  const titY = sapma(`cizim-daire-ty-${titKare}`, 0.6) * u;
  const titAci = sapma(`cizim-daire-ta-${titKare}`, 0.28);

  const ofset = a.cik > 0 && a.gir > 0.98 ? -UZUNLUK * a.cik : cizgiOfset(UZUNLUK, ciz * (1 - a.cik));
  const aci = onAci + (1 - otur) * -2.4 + titAci + a.nefes * 0.6 + a.cik * 2.2;
  const olcek = (1 - 0.04 * a.ters) * (0.95 + 0.05 * otur) * (1 + 0.01 * a.nefes) * (1 - 0.06 * a.cik);
  const ref = 0.26 * 1080 * u;
  const cizgiPx = ikonKalinlik(t, { x: 0, y: 0, w: ref, h: ref }, u, ref) * 0.72;
  const svgOlcek = Math.max(0.01, Math.min(kutu.w / VW, kutu.h / VH));
  const cizgi = cizgiPx / svgOlcek;
  const renk = t.renk[param.renk];
  const is = ikonStil(t, renk, u);
  const blur = a.hizBulaniklik > 0.08 ? `blur(${(a.hizBulaniklik * 0.35 * u).toFixed(2)}px) ` : "";
  const [ux, uy] = ucNokta(ciz);
  const ucParla = Math.sin(Math.min(1, Math.max(0, ciz)) * Math.PI) * (1 - a.cik);

  return (
    <svg
      viewBox={`0 0 ${VW} ${VH}`}
      width={kutu.w}
      height={kutu.h}
      style={{
        overflow: "visible",
        opacity: a.belir * (1 - a.cik * 0.85),
        transform: `translate(${titX}px, ${titY}px) scale(${olcek}) rotate(${aci}deg)`,
        filter: `${blur}${is.golge}`,
      }}
    >
      {/* Yarı saydam organik mürekkep yayılım tabanı */}
      <path
        d={YOL}
        fill="none"
        stroke={is.dolgu}
        strokeWidth={cizgi * 1.65}
        strokeLinecap="round"
        strokeLinejoin="round"
        opacity={0.72}
        strokeDasharray={UZUNLUK}
        strokeDashoffset={ofset}
      />
      {/* Ana organik kalem mürekkebi */}
      <path
        d={YOL}
        fill="none"
        stroke={rgba(renk, 0.94)}
        strokeWidth={cizgi}
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeDasharray={UZUNLUK}
        strokeDashoffset={ofset}
      />
      {/* İnce üst parlama vurgusu */}
      <path
        d={YOL}
        fill="none"
        stroke={is.parilti}
        strokeWidth={cizgi * 0.28}
        strokeLinecap="round"
        strokeLinejoin="round"
        transform="translate(-0.9 -1.1)"
        opacity={0.72}
        strokeDasharray={UZUNLUK}
        strokeDashoffset={ofset}
      />
      {/* Kalem ucunda hareketli ince parlama noktası */}
      {ucParla > 0.02 && (
        <g opacity={ucParla}>
          <circle cx={ux} cy={uy} r={cizgi * 1.1} fill={rgba(renk, 0.35)} />
          <circle cx={ux} cy={uy} r={cizgi * 0.45} fill={is.parilti} />
        </g>
      )}
    </svg>
  );
};

export default tanimla({ meta: meta as never, sema, Bilesen: Daire });
