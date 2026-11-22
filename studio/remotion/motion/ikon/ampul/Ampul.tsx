// Fikir ampulü: duotone cam kubbe dolgusu, iç flaman ışıması ve yanma anında dışa fırlayan 3 ince ışık ışınıyla parlar.
// Geometri: Lucide "lightbulb" (ISC, https://lucide.dev/icons/lightbulb), 24 birimlik viewBox.
import React from "react";
import { z } from "zod";
import { ikonStil, rgba, ton, useTema } from "../../../tema";
import { ikonKalinlik, KONTUR_EK } from "../../cekirdek/olcu";
import { cizgiOfset, useAkis } from "../../cekirdek/zaman";
import { tanimla, type BilesenProps } from "../../cekirdek/tipler";
import meta from "./meta.json";

export const sema = z.strictObject({
  renk: z.enum(["vurgu", "ikincil", "olumlu", "olumsuz", "yazi"]).default("ikincil").describe("Tema rengi adı; onaltılık renk yazılmaz"),
});

const KUBBE =
  "M15 14c.2-1 .7-1.7 1.5-2.5 1-.9 1.5-2.2 1.5-3.5A6 6 0 0 0 6 8c0 1 .2 2.2 1.5 3.5.7.7 1.3 1.5 1.5 2.5";
const KUBBE_DOLGU = `${KUBBE} Z`;
const TABAN_1 = "M9 17.8h6";
const TABAN_2 = "M10 23h4";
const KUBBE_UZ = 39;
const TABAN_1_UZ = 6.5;
const TABAN_2_UZ = 4.5;
const ISINLAR: Array<[number, number, number, number]> = [
  [12, 0.2, 12, -2.0],
  [4.8, 3.2, 3.1, 1.6],
  [19.2, 3.2, 20.9, 1.6],
];

const Ampul: React.FC<BilesenProps<z.infer<typeof sema>>> = ({ param, kutu, sureKare, u }) => {
  const t = useTema();
  const a = useAkis(sureKare, meta.giris_sn, meta.cikis_sn);
  const gradId = `ampul-g-${React.useId().replace(/[^a-zA-Z0-9_-]/g, "")}`;
  const p0 = a.sirali(0, 3, "enter");
  const p1 = a.sirali(1, 3, "enter");
  const p2 = a.sirali(2, 3, "enter");
  const cizKubbe = 0.22 * a.belir + 0.78 * p0;
  const yay = a.yay(0, "ipeksi");
  const onY = 1.8 * a.ters + a.nefes * -0.35;
  const otur = a.takip(a.girKare - 1, 170);
  const parla = Math.max(0, Math.min(1, a.vurgu(a.girKare, Math.round(0.42 * a.fps))));
  const isik = Math.sin(parla * Math.PI);
  const olcek = (1 - 0.06 * a.ters) * (0.92 + 0.08 * Math.min(1.06, yay) + 0.05 * (otur - a.gorunur) + 0.06 * isik) * (1 + 0.018 * a.nefes) * (1 - 0.3 * a.cik);
  const cizgi = ikonKalinlik(t, kutu, u, 24);
  const renk = t.renk[param.renk];
  const is = ikonStil(t, renk, u);
  const blur = a.hizBulaniklik > 0.08 ? `blur(${(a.hizBulaniklik * 0.4 * u).toFixed(2)}px) ` : "";
  const pariltiFiltre = isik > 0.01 ? ` drop-shadow(0 0 ${(14 * u * isik).toFixed(1)}px ${rgba(renk, 0.85 * isik)})` : "";

  const ciz = (stroke: string, strokeWidth: number, op = 1, dx = 0, dy = 0) => (
    <g transform={`translate(${dx} ${onY + dy})`} opacity={op}>
      <path
        d={KUBBE}
        fill="none"
        stroke={stroke}
        strokeWidth={strokeWidth}
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeDasharray={KUBBE_UZ}
        strokeDashoffset={cizgiOfset(KUBBE_UZ, cizKubbe)}
      />
      <path
        d={TABAN_1}
        fill="none"
        stroke={stroke}
        strokeWidth={strokeWidth}
        strokeLinecap="round"
        strokeLinejoin="round"
        opacity={Math.min(1, p1 * 6)}
        strokeDasharray={TABAN_1_UZ}
        strokeDashoffset={cizgiOfset(TABAN_1_UZ, p1)}
      />
      <path
        d={TABAN_2}
        fill="none"
        stroke={stroke}
        strokeWidth={strokeWidth}
        strokeLinecap="round"
        strokeLinejoin="round"
        opacity={Math.min(1, p2 * 6)}
        strokeDasharray={TABAN_2_UZ}
        strokeDashoffset={cizgiOfset(TABAN_2_UZ, p2)}
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
        filter: `${blur}${is.golge}${pariltiFiltre}`,
      }}
    >
      <defs>
        <radialGradient id={gradId} cx="45%" cy="35%" r="65%">
          <stop offset="0%" stopColor={ton(renk, -0.55, 0.65)} />
          <stop offset="100%" stopColor={is.dolgu} />
        </radialGradient>
      </defs>
      {/* Katman 1: duotone cam kubbe dolgusu ve iç flaman ışıması */}
      <g transform={`translate(0 ${onY})`}>
        <path d={KUBBE_DOLGU} fill={`url(#${gradId})`} opacity={(0.75 + 0.25 * isik) * a.gir} />
        <path
          d="M10.2 9.5 Q12 7.2 13.8 9.5"
          fill="none"
          stroke={is.parilti}
          strokeWidth={cizgi * 0.34}
          strokeLinecap="round"
          opacity={(0.65 + 0.35 * isik) * a.gir}
        />
      </g>
      {/* Katman 2: rafine koyu kontur + canlı ana çizgi + üst parıltı */}
      {ciz(is.kontur, cizgi + KONTUR_EK, 0.9)}
      {ciz(is.vurgu, cizgi, 1)}
      {ciz(is.parilti, cizgi * 0.26, 0.78 * a.gir, -0.18, -0.22)}
      {/* Katman 3: ampul yanarken dışa açılan 3 ışık ışını */}
      {(isik > 0.02 || a.gorunur > 0.5) &&
        ISINLAR.map(([x1, y1, x2, y2], i) => {
          const aktif = Math.max(isik, 0.32 * a.gorunur * (0.85 + 0.15 * a.nefes));
          return (
            <line
              key={i}
              x1={x1}
              y1={y1 + onY}
              x2={x1 + (x2 - x1) * (0.55 + 0.55 * isik)}
              y2={y1 + onY + (y2 - y1) * (0.55 + 0.55 * isik)}
              stroke={i === 0 ? is.parilti : is.vurgu}
              strokeWidth={cizgi * 0.32}
              strokeLinecap="round"
              opacity={aktif * (1 - a.cik)}
            />
          );
        })}
    </svg>
  );
};

export default tanimla({ meta: meta as never, sema, Bilesen: Ampul });
