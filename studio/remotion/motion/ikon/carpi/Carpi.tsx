// Red ve hata çarpısı: çok katmanlı duotone hacim, üst parlaklık ve darbe köşe kıvılcımlarıyla çaprazlanıp red titreşimiyle oturur.
// Geometri: Lucide "x" (ISC, https://lucide.dev/icons/x), 24 birimlik viewBox.
import React from "react";
import { z } from "zod";
import { ikonStil, useTema } from "../../../tema";
import { ikonKalinlik, KONTUR_EK } from "../../cekirdek/olcu";
import { cizgiOfset, useAkis } from "../../cekirdek/zaman";
import { tanimla, type BilesenProps } from "../../cekirdek/tipler";
import meta from "./meta.json";

export const sema = z.strictObject({
  renk: z.enum(["vurgu", "ikincil", "olumlu", "olumsuz", "yazi"]).default("olumsuz").describe("Tema rengi adı; onaltılık renk yazılmaz"),
});

const YOL_1 = "M18 6 6 18";
const YOL_2 = "m6 6 12 12";
const UZUNLUK = 17.2;
const DARBE_CIZGILER: Array<[number, number, number, number]> = [
  [3.6, 3.6, 1.8, 1.8],
  [20.4, 20.4, 22.2, 22.2],
  [20.4, 3.6, 22.1, 1.9],
];

const Carpi: React.FC<BilesenProps<z.infer<typeof sema>>> = ({ param, kutu, sureKare, u }) => {
  const t = useTema();
  const a = useAkis(sureKare, meta.giris_sn, meta.cikis_sn);
  const p1 = a.sirali(0, 3, "enter");
  const p2 = a.sirali(1, 3, "enter");
  const ciz1 = 0.24 * a.belir + 0.76 * p1;
  const yay = a.yay(0, "keskin");
  const otur = a.takip(a.girKare, 190);
  const tit = Math.max(0, Math.min(1, a.vurgu(a.girKare + 1, Math.round(0.28 * a.fps))));
  const sallantiX = Math.sin(tit * Math.PI * 3) * (1 - tit) * 2.1;
  const kivilcimOp = Math.sin(tit * Math.PI) * (1 - a.cik);
  const olcek = (1 - 0.14 * a.ters) * (0.9 + 0.1 * Math.min(1.06, yay) + 0.05 * (otur - a.gorunur)) * (1 + 0.018 * a.nefes) * (1 - 0.35 * a.cik);
  const aci = 10 * a.ters + a.nefes * 0.9 - 14 * a.cik;
  const cizgi = ikonKalinlik(t, kutu, u, 24);
  const renk = t.renk[param.renk];
  const is = ikonStil(t, renk, u);
  const blur = a.hizBulaniklik > 0.08 ? `blur(${(a.hizBulaniklik * 0.42 * u).toFixed(2)}px) ` : "";

  const ciz = (stroke: string, strokeWidth: number, op = 1, dx = 0, dy = 0) => (
    <g transform={`translate(${sallantiX + dx} ${dy})`} opacity={op}>
      <path
        d={YOL_1}
        fill="none"
        stroke={stroke}
        strokeWidth={strokeWidth}
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeDasharray={UZUNLUK}
        strokeDashoffset={cizgiOfset(UZUNLUK, ciz1)}
      />
      <path
        d={YOL_2}
        fill="none"
        stroke={stroke}
        strokeWidth={strokeWidth}
        strokeLinecap="round"
        strokeLinejoin="round"
        opacity={Math.min(1, p2 * 6)}
        strokeDasharray={UZUNLUK}
        strokeDashoffset={cizgiOfset(UZUNLUK, p2)}
      />
    </g>
  );

  return (
    <svg
      viewBox="0 0 24 24"
      width={kutu.w}
      height={kutu.h}
      style={{
        overflow: "visible",
        opacity: a.belir * (1 - a.cik),
        transform: `scale(${olcek}) rotate(${aci}deg)`,
        filter: `${blur}${is.golge}`,
      }}
    >
      {/* Katman 1: duotone hacim katmanı */}
      {ciz(is.dolgu, cizgi * 1.46, 0.9, 0.35, 0.55)}
      {/* Katman 2: rafine koyu dış kontur + canlı ana çizgi + ince üst parlaklık */}
      {ciz(is.kontur, cizgi + KONTUR_EK, 0.9)}
      {ciz(is.vurgu, cizgi, 1)}
      {ciz(is.parilti, cizgi * 0.28, 0.78 * a.gir, -0.2, -0.24)}
      {/* Katman 3: çarpma köşe kıvılcımları */}
      {kivilcimOp > 0.01 &&
        DARBE_CIZGILER.map(([x1, y1, x2, y2], i) => (
          <line
            key={i}
            x1={x1 + (x2 - x1) * 0.2 * tit}
            y1={y1 + (y2 - y1) * 0.2 * tit}
            x2={x1 + (x2 - x1) * (0.4 + 0.7 * tit)}
            y2={y1 + (y2 - y1) * (0.4 + 0.7 * tit)}
            stroke={i === 0 ? is.parilti : is.vurgu}
            strokeWidth={cizgi * 0.3}
            strokeLinecap="round"
            opacity={kivilcimOp}
          />
        ))}
    </svg>
  );
};

export default tanimla({ meta: meta as never, sema, Bilesen: Carpi });
