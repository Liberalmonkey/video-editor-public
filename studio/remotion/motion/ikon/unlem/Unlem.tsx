// Ünlem uyarısı: çok katmanlı duotone hacim, parlak nokta vurgusu ve tepe uyarı kıvılcımlarıyla inip kilitlenir.
// Geometri: Lucide "circle-alert" iç formu (ISC, https://lucide.dev/icons/circle-alert), 24 birimlik viewBox'a ölçekli; daire çizilmez.
import React from "react";
import { z } from "zod";
import { ikonStil, useTema } from "../../../tema";
import { ikonKalinlik, KONTUR_EK } from "../../cekirdek/olcu";
import { useAkis } from "../../cekirdek/zaman";
import { tanimla, type BilesenProps } from "../../cekirdek/tipler";
import meta from "./meta.json";

export const sema = z.strictObject({
  renk: z.enum(["vurgu", "ikincil", "olumlu", "olumsuz", "yazi"]).default("olumsuz").describe("Tema rengi adı; onaltılık renk yazılmaz"),
});

const Unlem: React.FC<BilesenProps<z.infer<typeof sema>>> = ({ param, kutu, sureKare, u }) => {
  const t = useTema();
  const a = useAkis(sureKare, meta.giris_sn, meta.cikis_sn);
  const yay = a.yay(0, "keskin");
  const govdeYay = a.takip(a.girKare - 3, 210);
  const govdeY = -5.2 * (1 - a.gir) - 2.0 * a.ters + (govdeYay - a.gorunur) * 0.9 + a.nefes * -0.35;
  const noktaYay = a.takip(Math.round(a.girKare * 0.55), 200);
  const noktaY = (1 - noktaYay) * 3.8 * (1 - a.cik) + a.nefes * 0.15;
  const noktaOp = Math.min(1, noktaYay * 4);
  const vurgu = Math.max(0, Math.min(1, a.vurgu(a.girKare + 2, Math.round(0.26 * a.fps))));
  const uyariAtim = Math.sin(vurgu * Math.PI);
  const olcek = (1 - 0.06 * a.ters) * (0.93 + 0.07 * Math.min(1.06, yay)) * (1 + 0.08 * uyariAtim + 0.018 * a.nefes) * (1 - 0.32 * a.cik);
  const cikY = -3.2 * a.cik;
  const cizgi = ikonKalinlik(t, kutu, u, 24);
  const noktaR = cizgi * 0.68;
  const renk = t.renk[param.renk];
  const is = ikonStil(t, renk, u);
  const blur = a.hizBulaniklik > 0.08 ? `blur(${(a.hizBulaniklik * 0.42 * u).toFixed(2)}px) ` : "";

  const ciz = (stroke: string, strokeWidth: number, noktaEk: number, op = 1, dx = 0, dy = 0) => (
    <g transform={`translate(${dx} ${cikY + dy})`} opacity={op}>
      <line
        x1="12"
        x2="12"
        y1="3.5"
        y2="14"
        stroke={stroke}
        strokeWidth={strokeWidth}
        strokeLinecap="round"
        transform={`translate(0 ${govdeY})`}
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
        transform: `scale(${olcek})`,
        filter: `${blur}${is.golge}`,
      }}
    >
      {/* Katman 1: yumuşak duotone hacim katmanı */}
      {ciz(is.dolgu, cizgi * 1.48, cizgi * 0.25, 0.9, 0.35, 0.5)}
      {/* Katman 2: rafine koyu kontur + canlı ana çizgi + üst parlaklık */}
      {ciz(is.kontur, cizgi + KONTUR_EK, KONTUR_EK / 2, 0.9)}
      {ciz(is.vurgu, cizgi, 0, 1)}
      <g transform={`translate(0 ${cikY})`} opacity={0.82 * a.gir}>
        <line
          x1="11.75"
          x2="11.75"
          y1="4.0"
          y2="12.4"
          stroke={is.parilti}
          strokeWidth={cizgi * 0.28}
          strokeLinecap="round"
          transform={`translate(0 ${govdeY})`}
        />
        <circle
          cx="11.5"
          cy="19.0"
          r={noktaR * 0.34}
          fill={is.parilti}
          opacity={noktaOp}
          transform={`translate(0 ${noktaY})`}
        />
      </g>
      {/* Katman 3: uyarı anında tepeden fırlayan iki yan kıvılcım çizgisi */}
      {uyariAtim > 0.01 && (
        <g opacity={uyariAtim * (1 - a.cik)} transform={`translate(0 ${cikY})`}>
          <line x1={7.8} y1={5.2} x2={5.6 - uyariAtim * 0.8} y2={3.6 - uyariAtim * 0.6} stroke={is.parilti} strokeWidth={cizgi * 0.3} strokeLinecap="round" />
          <line x1={16.2} y1={5.2} x2={18.4 + uyariAtim * 0.8} y2={3.6 - uyariAtim * 0.6} stroke={is.vurgu} strokeWidth={cizgi * 0.3} strokeLinecap="round" />
        </g>
      )}
    </svg>
  );
};

export default tanimla({ meta: meta as never, sema, Bilesen: Unlem });
