// Sağa ok: duotone hacim, kuyruk hız çizgileri ve üst parlaklık vurgusuyla ileri fırlayıp kilitlenir.
// Geometri: Lucide "arrow-right" (ISC, https://lucide.dev/icons/arrow-right), 24 birimlik viewBox.
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

const GOVDE = "M5 12h14";
const UC = "m12 5 7 7-7 7";
const GOVDE_UZ = 14.5;
const UC_UZ = 20.2;

const OkSag: React.FC<BilesenProps<z.infer<typeof sema>>> = ({ param, kutu, sureKare, u }) => {
  const t = useTema();
  const a = useAkis(sureKare, meta.giris_sn, meta.cikis_sn);
  const p1 = a.sirali(0, 3, "enter");
  const p2 = a.sirali(1, 3, "emphasis");
  const yay = a.yay(0, "keskin");
  const otur = a.takip(a.girKare - 2, 195);
  const govdeCiz = 0.35 * a.belir + 0.65 * p1;
  const x = -4.2 * (1 - a.gir) - 2.6 * a.ters + (otur - a.gorunur) * 1.4 + a.nefes * 0.45 + 7.0 * a.cik;
  const govdeSx = 1 - 0.22 * a.ters + 0.24 * Math.max(0, a.gorunur - otur);
  const ucX = -4.0 * (1 - p2) + (a.gorunur - otur) * 1.8;
  const olcek = (0.93 + 0.07 * Math.min(1.06, yay) + 0.04 * (otur - a.gorunur)) * (1 + 0.015 * a.nefes) * (1 - 0.25 * a.cik);
  const kuyrukOp = Math.sin(a.gir * Math.PI) * (1 - a.cik) * 0.78;
  const cizgi = ikonKalinlik(t, kutu, u, 24);
  const renk = t.renk[param.renk];
  const is = ikonStil(t, renk, u);
  const blur = a.hizBulaniklik > 0.08 ? `blur(${(a.hizBulaniklik * 0.45 * u).toFixed(2)}px) ` : "";

  const ciz = (stroke: string, strokeWidth: number, op = 1, dx = 0, dy = 0) => (
    <g transform={`translate(${x + dx} ${dy})`} opacity={op}>
      <g transform={`translate(5 12) scale(${govdeSx} 1) translate(-5 -12)`}>
        <path
          d={GOVDE}
          fill="none"
          stroke={stroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeDasharray={GOVDE_UZ}
          strokeDashoffset={cizgiOfset(GOVDE_UZ, govdeCiz)}
        />
      </g>
      <path
        d={UC}
        fill="none"
        stroke={stroke}
        strokeWidth={strokeWidth}
        strokeLinecap="round"
        strokeLinejoin="round"
        opacity={Math.min(1, Math.max(0, p2 * 6))}
        transform={`translate(${ucX} 0)`}
        strokeDasharray={UC_UZ}
        strokeDashoffset={cizgiOfset(UC_UZ, p2)}
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
        transform: `scale(${olcek})`,
        filter: `${blur}${is.golge}`,
      }}
    >
      {/* Katman 1: yumuşak duotone hacim katmanı */}
      {ciz(is.dolgu, cizgi * 1.46, 0.9, 0.35, 0.55)}
      {/* Katman 2: rafine koyu kontur + canlı ana çizgi + üst parlaklık */}
      {ciz(is.kontur, cizgi + KONTUR_EK, 0.9)}
      {ciz(is.vurgu, cizgi, 1)}
      {ciz(is.parilti, cizgi * 0.28, 0.78 * a.gir, -0.18, -0.24)}
      {/* Katman 3: fırlama anında kuyruk hız çizgileri */}
      {kuyrukOp > 0.01 && (
        <g opacity={kuyrukOp}>
          <line x1={x + 1.2} y1={8.6} x2={x + 5.8} y2={8.6} stroke={is.parilti} strokeWidth={cizgi * 0.28} strokeLinecap="round" />
          <line x1={x + 2.0} y1={15.4} x2={x + 6.4} y2={15.4} stroke={is.vurgu} strokeWidth={cizgi * 0.26} strokeLinecap="round" />
        </g>
      )}
    </svg>
  );
};

export default tanimla({ meta: meta as never, sema, Bilesen: OkSag });
