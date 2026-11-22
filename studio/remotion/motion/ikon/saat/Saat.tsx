// Saat: duotone kadran dolgusu, dört yön kadran çentiği, parlak merkez pimi ve mekanik sekerek kilitlenen ibrelerle döner.
// Geometri: Lucide "clock" (ISC, https://lucide.dev/icons/clock), 24 birimlik viewBox.
import React from "react";
import { interpolate } from "remotion";
import { z } from "zod";
import { ikonStil, ton, useTema } from "../../../tema";
import { ikonKalinlik, KONTUR_EK } from "../../cekirdek/olcu";
import { cizgiOfset, useAkis } from "../../cekirdek/zaman";
import { tanimla, type BilesenProps } from "../../cekirdek/tipler";
import meta from "./meta.json";

export const sema = z.strictObject({
  renk: z.enum(["vurgu", "ikincil", "olumlu", "olumsuz", "yazi"]).default("vurgu").describe("Tema rengi adı; onaltılık renk yazılmaz"),
});

const KIS = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const KADRAN_UZ = 63.5;
const YELKOVAN = "M12 12 12 6";
const AKREP = "M12 12 16 14";

const Saat: React.FC<BilesenProps<z.infer<typeof sema>>> = ({ param, kutu, sureKare, u }) => {
  const t = useTema();
  const a = useAkis(sureKare, meta.giris_sn, meta.cikis_sn);
  const gradId = `saat-g-${React.useId().replace(/[^a-zA-Z0-9_-]/g, "")}`;
  const yay = a.yay(0, "ipeksi");
  const otur = a.takip(a.girKare - 2, 175);
  const kadranCiz = 0.25 * a.belir + 0.75 * a.gir;
  const donusBitis = Math.max(a.girKare + 10, Math.round(0.75 * a.fps));
  const donus = a.e.settle(interpolate(a.f, [a.hazirlikKare, Math.max(a.hazirlikKare + 1, donusBitis)], [0, 1], KIS));
  const kilit = Math.max(0, Math.min(1, a.vurgu(donusBitis - 2, Math.round(0.22 * a.fps))));
  const sekme = Math.sin(kilit * Math.PI * 1.5) * (1 - kilit);
  const yelkovanAci = -22 * a.ters + donus * 360 + sekme * 12 + a.nefes * 2.2;
  const akrepAci = -10 * a.ters + (donus - 1) * 90 + sekme * 5;
  const olcek = (1 - 0.06 * a.ters) * (0.92 + 0.08 * Math.min(1.06, yay) + 0.05 * (otur - a.gorunur)) * (1 + 0.015 * a.nefes) * (1 - 0.32 * a.cik);
  const cikAci = 18 * a.cik;
  const cizgi = ikonKalinlik(t, kutu, u, 24);
  const renk = t.renk[param.renk];
  const is = ikonStil(t, renk, u);
  const blur = a.hizBulaniklik > 0.08 ? `blur(${(a.hizBulaniklik * 0.4 * u).toFixed(2)}px) ` : "";

  const ciz = (stroke: string, strokeWidth: number, op = 1, dx = 0, dy = 0) => (
    <g transform={`translate(${dx} ${dy})`} opacity={op}>
      <circle
        cx="12"
        cy="12"
        r="10"
        fill="none"
        stroke={stroke}
        strokeWidth={strokeWidth}
        strokeLinecap="round"
        transform="rotate(-90 12 12)"
        strokeDasharray={KADRAN_UZ}
        strokeDashoffset={cizgiOfset(KADRAN_UZ, kadranCiz)}
      />
      <path d={AKREP} fill="none" stroke={stroke} strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round" transform={`rotate(${akrepAci} 12 12)`} />
      <path d={YELKOVAN} fill="none" stroke={stroke} strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round" transform={`rotate(${yelkovanAci} 12 12)`} />
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
        transform: `scale(${olcek}) rotate(${cikAci}deg)`,
        filter: `${blur}${is.golge}`,
      }}
    >
      <defs>
        <linearGradient id={gradId} x1="0.2" y1="0" x2="0.8" y2="1">
          <stop offset="0%" stopColor={ton(renk, -0.35, 0.38)} />
          <stop offset="100%" stopColor={is.dolgu} />
        </linearGradient>
      </defs>
      {/* Katman 1: duotone kadran hacmi */}
      <circle cx="12" cy="12" r="10" fill={`url(#${gradId})`} opacity={0.9 * a.gir} />
      {/* Katman 2: rafine koyu kontur + canlı ana çizgi + üst parıltı */}
      {ciz(is.kontur, cizgi + KONTUR_EK, 0.9)}
      {ciz(is.vurgu, cizgi, 1)}
      {ciz(is.parilti, cizgi * 0.25, 0.72 * a.gir, -0.18, -0.22)}
      {/* Katman 3: kadran çentikleri ve parlak merkez pimi */}
      <g opacity={0.75 * a.gir}>
        <line x1="12" y1="3.7" x2="12" y2="4.9" stroke={is.parilti} strokeWidth={cizgi * 0.3} strokeLinecap="round" />
        <line x1="20.3" y1="12" x2="19.1" y2="12" stroke={is.parilti} strokeWidth={cizgi * 0.3} strokeLinecap="round" />
        <line x1="12" y1="20.3" x2="12" y2="19.1" stroke={is.parilti} strokeWidth={cizgi * 0.3} strokeLinecap="round" />
        <line x1="3.7" y1="12" x2="4.9" y2="12" stroke={is.parilti} strokeWidth={cizgi * 0.3} strokeLinecap="round" />
        <circle cx="12" cy="12" r={cizgi * 0.42} fill={is.parilti} />
      </g>
    </svg>
  );
};

export default tanimla({ meta: meta as never, sema, Bilesen: Saat });
