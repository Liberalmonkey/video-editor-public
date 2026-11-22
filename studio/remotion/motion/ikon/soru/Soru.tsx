// Soru işareti: çok katmanlı duotone hacim, parlak eğri üst ışığı ve merak kıvılcımıyla çizilip yayla oturur.
// Geometri: Lucide "circle-help" iç eğrisi (ISC, https://lucide.dev/icons/circle-help), 24 birimlik viewBox'a ölçekli; daire çizilmez.
import React from "react";
import { z } from "zod";
import { ikonStil, useTema } from "../../../tema";
import { ikonKalinlik, KONTUR_EK } from "../../cekirdek/olcu";
import { cizgiOfset, useAkis } from "../../cekirdek/zaman";
import { tanimla, type BilesenProps } from "../../cekirdek/tipler";
import meta from "./meta.json";

export const sema = z.strictObject({
  renk: z.enum(["vurgu", "ikincil", "olumlu", "olumsuz", "yazi"]).default("vurgu").describe("Tema rengi adı; onaltılık renk yazılmaz"),
});

const EGRI = "M7.63 7.75a4.5 4.5 0 0 1 8.75 1.5c0 3-4.38 4.5-4.38 5";
const EGRI_UZ = 21;

const Soru: React.FC<BilesenProps<z.infer<typeof sema>>> = ({ param, kutu, sureKare, u }) => {
  const t = useTema();
  const a = useAkis(sureKare, meta.giris_sn, meta.cikis_sn);
  const yay = a.yay(0, "elastik");
  const otur = a.takip(a.girKare - 2, 165);
  const egriCiz = 0.22 * a.belir + 0.78 * a.gir;
  const egim = -10 * a.ters + 7 * (a.gorunur - otur) + a.nefes * 1.8 - 10 * a.cik;
  const noktaYay = a.takip(Math.round(a.girKare * 0.55), 210);
  const noktaY = (1 - noktaYay) * -4.2 * (1 - a.cik);
  const noktaOp = Math.min(1, noktaYay * 4);
  const merak = Math.max(0, Math.min(1, a.vurgu(a.girKare, Math.round(0.32 * a.fps))));
  const kivilcimOp = Math.sin(merak * Math.PI) * (1 - a.cik);
  const olcek = (1 - 0.07 * a.ters) * (0.92 + 0.08 * Math.min(1.06, yay) + 0.05 * (otur - a.gorunur)) * (1 + 0.018 * a.nefes) * (1 - 0.3 * a.cik);
  const cikY = -3.2 * a.cik;
  const cizgi = ikonKalinlik(t, kutu, u, 24);
  const noktaR = cizgi * 0.68;
  const renk = t.renk[param.renk];
  const is = ikonStil(t, renk, u);
  const blur = a.hizBulaniklik > 0.08 ? `blur(${(a.hizBulaniklik * 0.4 * u).toFixed(2)}px) ` : "";
  const ofset = cizgiOfset(EGRI_UZ, egriCiz);

  const ciz = (stroke: string, strokeWidth: number, noktaEk: number, op = 1, dx = 0, dy = 0) => (
    <g transform={`translate(${dx} ${cikY + dy})`} opacity={op}>
      <path
        d={EGRI}
        fill="none"
        stroke={stroke}
        strokeWidth={strokeWidth}
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeDasharray={EGRI_UZ}
        strokeDashoffset={ofset}
      />
      <circle
        cx="12"
        cy="19.5"
        r={Math.max(0.2, noktaR + noktaEk)}
        fill={stroke}
        opacity={noktaOp}
        transform={`translate(0 ${noktaY})`}
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
        transform: `scale(${olcek}) rotate(${egim}deg)`,
        filter: `${blur}${is.golge}`,
      }}
    >
      {/* Katman 1: duotone hacim katmanı */}
      {ciz(is.dolgu, cizgi * 1.46, cizgi * 0.24, 0.9, 0.35, 0.5)}
      {/* Katman 2: rafine koyu kontur + canlı ana çizgi + üst parlaklık */}
      {ciz(is.kontur, cizgi + KONTUR_EK, KONTUR_EK / 2, 0.9)}
      {ciz(is.vurgu, cizgi, 0, 1)}
      <g transform={`translate(0 ${cikY})`} opacity={0.8 * a.gir}>
        <path
          d={EGRI}
          fill="none"
          stroke={is.parilti}
          strokeWidth={cizgi * 0.28}
          strokeLinecap="round"
          strokeLinejoin="round"
          transform="translate(-0.2 -0.25)"
          strokeDasharray={EGRI_UZ}
          strokeDashoffset={ofset}
        />
        <circle cx="11.5" cy="19.0" r={noktaR * 0.34} fill={is.parilti} opacity={noktaOp} transform={`translate(0 ${noktaY})`} />
      </g>
      {/* Katman 3: eğri tepesinden sıçrayan iki küçük merak aksanı */}
      {kivilcimOp > 0.01 && (
        <g opacity={kivilcimOp}>
          <line x1={17.8} y1={4.6} x2={19.8} y2={3.0} stroke={is.parilti} strokeWidth={cizgi * 0.3} strokeLinecap="round" />
          <line x1={18.8} y1={7.4} x2={21.0} y2={7.1} stroke={is.vurgu} strokeWidth={cizgi * 0.28} strokeLinecap="round" />
        </g>
      )}
    </svg>
  );
};

export default tanimla({ meta: meta as never, sema, Bilesen: Soru });
