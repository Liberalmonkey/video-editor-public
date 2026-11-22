// Konum iğnesi: duotone gövde dolgusu, üst parıltı ve sivri ucun zemine değdiği noktada açılan ince temas dalgasıyla oturur.
// Geometri: Lucide "map-pin" (ISC, https://lucide.dev/icons/map-pin), 24 birimlik viewBox.
import React from "react";
import { z } from "zod";
import { ikonStil, ton, useTema } from "../../../tema";
import { ikonKalinlik, KONTUR_EK } from "../../cekirdek/olcu";
import { useAkis } from "../../cekirdek/zaman";
import { tanimla, type BilesenProps } from "../../cekirdek/tipler";
import meta from "./meta.json";

export const sema = z.strictObject({
  renk: z.enum(["vurgu", "ikincil", "olumlu", "olumsuz", "yazi"]).default("vurgu").describe("Tema rengi adı; onaltılık renk yazılmaz"),
});

const IGNE =
  "M20 10c0 4.993-5.539 10.193-7.399 11.799a1 1 0 0 1-1.202 0C9.539 20.193 4 14.993 4 10a8 8 0 0 1 16 0";

const Konum: React.FC<BilesenProps<z.infer<typeof sema>>> = ({ param, kutu, sureKare, u }) => {
  const t = useTema();
  const a = useAkis(sureKare, meta.giris_sn, meta.cikis_sn);
  const gradId = `konum-g-${React.useId().replace(/[^a-zA-Z0-9_-]/g, "")}`;
  const pIc = a.sirali(1, 3, "emphasis");
  const yay = a.yay(0, "elastik");
  const otur = a.takip(a.girKare - 2, 195);
  const y = -8.5 * (1 - a.gir) - 2.6 * a.ters + a.nefes * -0.4 - 3.0 * a.cik;
  const carp = Math.max(0, Math.min(1, a.vurgu(a.girKare - 2, Math.round(0.28 * a.fps))));
  const ezil = Math.sin(carp * Math.PI);
  const sy = (1 + 0.06 * a.ters) * (0.93 + 0.07 * Math.min(1.06, yay) + 0.04 * (otur - a.gorunur) - 0.14 * ezil) * (1 + 0.015 * a.nefes) * (1 - 0.35 * a.cik);
  const sx = (1 - 0.04 * a.ters) * (1 + 0.12 * ezil) * (1 - 0.35 * a.cik);
  const icOlcek = 0.3 + 0.7 * pIc;
  const cizgi = ikonKalinlik(t, kutu, u, 24);
  const renk = t.renk[param.renk];
  const is = ikonStil(t, renk, u);
  const blur = a.hizBulaniklik > 0.08 ? `blur(${(a.hizBulaniklik * 0.42 * u).toFixed(2)}px) ` : "";

  const ciz = (stroke: string, strokeWidth: number, op = 1, dx = 0, dy = 0) => (
    <g transform={`translate(${dx} ${y + dy}) translate(12 22) scale(${sx} ${sy}) translate(-12 -22)`} opacity={op}>
      <path d={IGNE} fill="none" stroke={stroke} strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round" />
      <g transform={`translate(12 10) scale(${icOlcek}) translate(-12 -10)`} opacity={Math.min(1, Math.max(0, pIc * 4))}>
        <circle cx="12" cy="10" r="3" fill="none" stroke={stroke} strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round" />
      </g>
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
      <defs>
        <linearGradient id={gradId} x1="0.2" y1="0" x2="0.8" y2="1">
          <stop offset="0%" stopColor={ton(renk, -0.35, 0.46)} />
          <stop offset="100%" stopColor={is.dolgu} />
        </linearGradient>
      </defs>
      {/* Katman 3 (temas anı): iğne ucunun hemen altında kısa temas kıvılcım çizgileri (arka rozet/disk yok) */}
      {ezil > 0.01 && (
        <g opacity={ezil * (1 - a.cik)}>
          <line x1={8.4} y1={22.8} x2={6.0 - ezil * 1.2} y2={22.2} stroke={is.parilti} strokeWidth={cizgi * 0.3} strokeLinecap="round" />
          <line x1={15.6} y1={22.8} x2={18.0 + ezil * 1.2} y2={22.2} stroke={is.vurgu} strokeWidth={cizgi * 0.3} strokeLinecap="round" />
        </g>
      )}
      {/* Katman 1: duotone iğne gövde hacmi (iç boşluk evenodd ile temiz kalır) */}
      <g transform={`translate(0 ${y}) translate(12 22) scale(${sx} ${sy}) translate(-12 -22)`}>
        <path d={`${IGNE} M15 10a3 3 0 1 0-6 0a3 3 0 1 0 6 0`} fill={`url(#${gradId})`} fillRule="evenodd" opacity={0.95 * a.gir} />
      </g>
      {/* Katman 2: rafine koyu kontur + canlı ana çizgi + üst parıltı */}
      {ciz(is.kontur, cizgi + KONTUR_EK, 0.9)}
      {ciz(is.vurgu, cizgi, 1)}
      {ciz(is.parilti, cizgi * 0.25, 0.74 * a.gir, -0.18, -0.22)}
    </svg>
  );
};

export default tanimla({ meta: meta as never, sema, Bilesen: Konum });
