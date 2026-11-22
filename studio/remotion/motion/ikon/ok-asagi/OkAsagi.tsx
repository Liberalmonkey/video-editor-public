// Aşağı ok: duotone hacim katmanı, düşüş hız çizgileri, üst parlaklık ve zemine çarpınca uçta sıçrayan iki ince kıvılcımla iner.
// Geometri: Lucide "arrow-down" (ISC, https://lucide.dev/icons/arrow-down), 24 birimlik viewBox.
import React from "react";
import { interpolate } from "remotion";
import { z } from "zod";
import { ikonStil, useTema } from "../../../tema";
import { ikonKalinlik, KONTUR_EK } from "../../cekirdek/olcu";
import { useAkis } from "../../cekirdek/zaman";
import { tanimla, type BilesenProps } from "../../cekirdek/tipler";
import meta from "./meta.json";

export const sema = z.strictObject({
  renk: z.enum(["vurgu", "ikincil", "olumlu", "olumsuz", "yazi"]).default("vurgu").describe("Tema rengi adı; onaltılık renk yazılmaz"),
});

const KIS = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const GOVDE = "M12 5v14";
const UC = "m19 12-7 7-7-7";

const OkAsagi: React.FC<BilesenProps<z.infer<typeof sema>>> = ({ param, kutu, sureKare, u }) => {
  const t = useTema();
  const a = useAkis(sureKare, meta.giris_sn, meta.cikis_sn);
  const dus = a.e.exit(interpolate(a.f, [a.hazirlikKare, Math.max(a.hazirlikKare + 1, a.girKare)], [0, 1], KIS));
  const yay = a.yay(0, "keskin");
  const carp = Math.max(0, Math.min(1, a.vurgu(a.girKare - 1, Math.round(0.22 * a.fps))));
  const ezil = Math.sin(carp * Math.PI);
  const sek = Math.max(0, Math.min(1, a.vurgu(a.girKare + Math.round(0.14 * a.fps), Math.round(0.22 * a.fps))));
  const sekY = -2.2 * Math.sin(sek * Math.PI);
  const y = -8.5 * (1 - dus) - 2.6 * a.ters + sekY + a.nefes * 0.45 + 7.5 * a.cik;
  const sy = (1 + 0.08 * a.ters) * (0.94 + 0.06 * Math.min(1.06, yay)) * (1 - 0.2 * ezil) * (1 - 0.25 * a.cik);
  const sx = (1 - 0.05 * a.ters) * (1 + 0.16 * ezil) * (1 - 0.15 * a.cik);
  const ucEkY = 1.2 * ezil;
  const izOp = Math.sin(dus * Math.PI) * (1 - a.cik) * 0.72;
  const cizgi = ikonKalinlik(t, kutu, u, 24);
  const renk = t.renk[param.renk];
  const is = ikonStil(t, renk, u);
  const blur = a.hizBulaniklik > 0.08 ? `blur(${(a.hizBulaniklik * 0.45 * u).toFixed(2)}px) ` : "";

  const ciz = (stroke: string, strokeWidth: number, op = 1, dx = 0, dy = 0) => (
    <g transform={`translate(${dx} ${y + dy}) translate(12 19) scale(${sx} ${sy}) translate(-12 -19)`} opacity={op}>
      <path d={GOVDE} fill="none" stroke={stroke} strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round" />
      <path d={UC} fill="none" stroke={stroke} strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round" transform={`translate(0 ${ucEkY})`} />
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
        filter: `${blur}${is.golge}`,
      }}
    >
      {/* Katman 1: yumuşak duotone hacim katmanı */}
      {ciz(is.dolgu, cizgi * 1.46, 0.9, 0.35, 0.55)}
      {/* Katman 2: rafine koyu dış kontur + canlı ana çizgi + üst parlama */}
      {ciz(is.kontur, cizgi + KONTUR_EK, 0.9)}
      {ciz(is.vurgu, cizgi, 1)}
      {ciz(is.parilti, cizgi * 0.28, 0.78 * a.gir, -0.2, -0.24)}
      {/* Katman 3: düşüş hız izi + çarpma anında uçtan sıçrayan iki kıvılcım */}
      {izOp > 0.01 && (
        <g opacity={izOp}>
          <line x1={8.5} y1={y + 1.5} x2={8.5} y2={y + 6.0} stroke={is.parilti} strokeWidth={cizgi * 0.26} strokeLinecap="round" />
          <line x1={15.5} y1={y + 2.2} x2={15.5} y2={y + 6.4} stroke={is.vurgu} strokeWidth={cizgi * 0.26} strokeLinecap="round" />
        </g>
      )}
      {ezil > 0.01 && (
        <g opacity={ezil * (1 - a.cik)}>
          <line x1={8.2} y1={21.0} x2={6.0 - ezil * 0.8} y2={20.2} stroke={is.parilti} strokeWidth={cizgi * 0.3} strokeLinecap="round" />
          <line x1={15.8} y1={21.0} x2={18.0 + ezil * 0.8} y2={20.2} stroke={is.vurgu} strokeWidth={cizgi * 0.3} strokeLinecap="round" />
        </g>
      )}
    </svg>
  );
};

export default tanimla({ meta: meta as never, sema, Bilesen: OkAsagi });
