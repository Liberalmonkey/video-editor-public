// Bildirim zili: duotone çan gövdesi, üst parlaklık vurgusu ve çınlarken iki yandan titreşen ses dalgası yaylarıyla sallanır.
// Geometri: Lucide "bell" (ISC, https://lucide.dev/icons/bell), 24 birimlik viewBox.
import React from "react";
import { z } from "zod";
import { ikonStil, ton, useTema } from "../../../tema";
import { ikonKalinlik, KONTUR_EK } from "../../cekirdek/olcu";
import { useAkis } from "../../cekirdek/zaman";
import { tanimla, type BilesenProps } from "../../cekirdek/tipler";
import meta from "./meta.json";

export const sema = z.strictObject({
  renk: z.enum(["vurgu", "ikincil", "olumlu", "olumsuz", "yazi"]).default("ikincil").describe("Tema rengi adı; onaltılık renk yazılmaz"),
});

const TOKMAK = "M10.268 21a2 2 0 0 0 3.464 0";
const GOVDE =
  "M3.262 15.326A1 1 0 0 0 4 17h16a1 1 0 0 0 .74-1.673C19.41 13.956 18 12.499 18 8A6 6 0 0 0 6 8c0 4.499-1.411 5.956-2.738 7.326";

const Zil: React.FC<BilesenProps<z.infer<typeof sema>>> = ({ param, kutu, sureKare, u }) => {
  const t = useTema();
  const a = useAkis(sureKare, meta.giris_sn, meta.cikis_sn);
  const gradId = `zil-g-${React.useId().replace(/[^a-zA-Z0-9_-]/g, "")}`;
  const yay = a.yay(0, "elastik");
  const otur = a.takip(a.girKare - 3, 180);
  const cal = Math.max(0, Math.min(1, a.vurgu(a.hazirlikKare, Math.round(0.75 * a.fps))));
  const aci = -10 * a.ters + Math.sin(cal * Math.PI * 3.5) * Math.pow(1 - cal, 1.4) * 20 + a.nefes * 1.4;
  const calGec = Math.max(0, Math.min(1, a.vurgu(a.hazirlikKare + 2, Math.round(0.75 * a.fps))));
  const tokmakX = 0.7 * a.ters + Math.sin(calGec * Math.PI * 3.5) * Math.pow(1 - calGec, 1.3) * 1.4;
  const dalgaOp = Math.sin(cal * Math.PI) * (1 - cal * 0.4) * (1 - a.cik);
  const y = -3.4 * (1 - a.gir) - 1.4 * a.ters + a.nefes * -0.3 - 3.8 * a.cik;
  const olcek = (1 - 0.06 * a.ters) * (0.91 + 0.09 * Math.min(1.06, yay) + 0.05 * (otur - a.gorunur)) * (1 + 0.015 * a.nefes) * (1 - 0.3 * a.cik);
  const cizgi = ikonKalinlik(t, kutu, u, 24);
  const renk = t.renk[param.renk];
  const is = ikonStil(t, renk, u);
  const blur = a.hizBulaniklik > 0.08 ? `blur(${(a.hizBulaniklik * 0.4 * u).toFixed(2)}px) ` : "";

  const ciz = (stroke: string, strokeWidth: number, op = 1, dx = 0, dy = 0) => (
    <g transform={`translate(${dx} ${y + dy}) rotate(${aci} 12 3)`} opacity={op}>
      <path d={GOVDE} fill="none" stroke={stroke} strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round" />
      <path d={TOKMAK} fill="none" stroke={stroke} strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round" transform={`translate(${tokmakX} 0)`} />
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
      <defs>
        <linearGradient id={gradId} x1="0.2" y1="0" x2="0.8" y2="1">
          <stop offset="0%" stopColor={ton(renk, -0.35, 0.45)} />
          <stop offset="100%" stopColor={is.dolgu} />
        </linearGradient>
      </defs>
      {/* Katman 1: duotone çan hacim dolgusu */}
      <g transform={`translate(0 ${y}) rotate(${aci} 12 3)`}>
        <path d={`${GOVDE} Z`} fill={`url(#${gradId})`} opacity={0.95 * a.gir} />
      </g>
      {/* Katman 2: rafine koyu kontur + canlı ana çizgi + üst parıltı */}
      {ciz(is.kontur, cizgi + KONTUR_EK, 0.9)}
      {ciz(is.vurgu, cizgi, 1)}
      {ciz(is.parilti, cizgi * 0.25, 0.74 * a.gir, -0.18, -0.22)}
      {/* Katman 3: iki yandan yayılan çınlama ses dalgaları */}
      {dalgaOp > 0.01 && (
        <g opacity={dalgaOp} transform={`translate(0 ${y})`}>
          <path d="M2.2 6.8A10 10 0 0 1 4.6 3.5" fill="none" stroke={is.parilti} strokeWidth={cizgi * 0.32} strokeLinecap="round" />
          <path d="M21.8 6.8A10 10 0 0 0 19.4 3.5" fill="none" stroke={is.vurgu} strokeWidth={cizgi * 0.32} strokeLinecap="round" />
        </g>
      )}
    </svg>
  );
};

export default tanimla({ meta: meta as never, sema, Bilesen: Zil });
