// Kalp: çok katmanlı duotone hacim dolgusu, sol üst ışık yansıması ve nabızda sıçrayan mikro parıltılarla atıp oturur.
// Geometri: Lucide "heart" (ISC, https://lucide.dev/icons/heart), 24 birimlik viewBox.
import React from "react";
import { z } from "zod";
import { ikonStil, ton, useTema } from "../../../tema";
import { ikonKalinlik, KONTUR_EK } from "../../cekirdek/olcu";
import { cizgiOfset, useAkis } from "../../cekirdek/zaman";
import { tanimla, type BilesenProps } from "../../cekirdek/tipler";
import meta from "./meta.json";

export const sema = z.strictObject({
  renk: z.enum(["vurgu", "ikincil", "olumlu", "olumsuz", "yazi"]).default("vurgu").describe("Tema rengi adı; onaltılık renk yazılmaz"),
});

const YOL =
  "M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z";
const UZUNLUK = 62;
const PARILTI_YAY = "M5.3 7.6A2.6 2.6 0 0 1 8.4 5.5";

const Kalp: React.FC<BilesenProps<z.infer<typeof sema>>> = ({ param, kutu, sureKare, u }) => {
  const t = useTema();
  const a = useAkis(sureKare, meta.giris_sn, meta.cikis_sn);
  const gradId = `kalp-g-${React.useId().replace(/[^a-zA-Z0-9_-]/g, "")}`;
  const ciz = 0.28 * a.belir + 0.72 * a.gir;
  const yay = a.yay(0, "elastik");
  const sikis = 1 - 0.12 * a.ters;
  const at1 = Math.max(0, Math.min(1, a.vurgu(a.hazirlikKare, Math.round(0.28 * a.fps))));
  const at2 = Math.max(0, Math.min(1, a.vurgu(a.girKare + Math.round(0.16 * a.fps), Math.round(0.24 * a.fps))));
  const nabiz = 1 + 0.12 * Math.sin(at1 * Math.PI) + 0.07 * Math.sin(at2 * Math.PI) + 0.02 * a.nefes;
  const kaldirY = 0.8 * a.ters - 0.9 * Math.sin(at1 * Math.PI) - 0.5 * Math.sin(at2 * Math.PI) + a.nefes * -0.35;
  const olcek = sikis * (0.92 + 0.08 * Math.min(1.08, yay)) * nabiz * (1 - 0.35 * a.cik);
  const kivilcimOp = Math.sin(at2 * Math.PI) * (1 - a.cik);
  const cizgi = ikonKalinlik(t, kutu, u, 24);
  const renk = t.renk[param.renk];
  const is = ikonStil(t, renk, u);
  const blur = a.hizBulaniklik > 0.08 ? `blur(${(a.hizBulaniklik * 0.4 * u).toFixed(2)}px) ` : "";
  const ofset = cizgiOfset(UZUNLUK, ciz);

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
      <g transform={`translate(0 ${kaldirY})`}>
        {/* Katman 1: yumuşak duotone hacim dolgusu */}
        <path d={YOL} fill={`url(#${gradId})`} opacity={0.95 * a.gir} />
        {/* Katman 2: rafine koyu kontur + canlı ana çizgi + sol üst parlaklık yayı */}
        <path
          d={YOL}
          fill="none"
          stroke={is.kontur}
          strokeWidth={cizgi + KONTUR_EK}
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeOpacity={0.9}
          strokeDasharray={UZUNLUK}
          strokeDashoffset={ofset}
        />
        <path
          d={YOL}
          fill="none"
          stroke={is.vurgu}
          strokeWidth={cizgi}
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeDasharray={UZUNLUK}
          strokeDashoffset={ofset}
        />
        <path
          d={PARILTI_YAY}
          fill="none"
          stroke={is.parilti}
          strokeWidth={cizgi * 0.34}
          strokeLinecap="round"
          opacity={0.85 * a.gir}
        />
      </g>
      {/* Katman 3: ikinci nabızda sağ üstten sıçrayan ince parıltı aksanı */}
      {kivilcimOp > 0.01 && (
        <g opacity={kivilcimOp}>
          <line x1={19.8} y1={3.2} x2={21.8} y2={1.4} stroke={is.parilti} strokeWidth={cizgi * 0.3} strokeLinecap="round" />
          <line x1={21.4} y1={5.6} x2={23.4} y2={5.0} stroke={is.vurgu} strokeWidth={cizgi * 0.28} strokeLinecap="round" />
        </g>
      )}
    </svg>
  );
};

export default tanimla({ meta: meta as never, sema, Bilesen: Kalp });
