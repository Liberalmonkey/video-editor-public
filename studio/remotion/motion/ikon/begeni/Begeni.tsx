// Beğeni başparmağı: duotone el dolgusu, üst parıltı vurgusu ve başparmak tepesinden yayılan onay ışınlarıyla kalkıp oturur.
// Geometri: Lucide "thumbs-up" (ISC, https://lucide.dev/icons/thumbs-up), 24 birimlik viewBox.
import React from "react";
import { z } from "zod";
import { ikonStil, ton, useTema } from "../../../tema";
import { ikonKalinlik, KONTUR_EK } from "../../cekirdek/olcu";
import { cizgiOfset, useAkis } from "../../cekirdek/zaman";
import { tanimla, type BilesenProps } from "../../cekirdek/tipler";
import meta from "./meta.json";

export const sema = z.strictObject({
  renk: z.enum(["vurgu", "ikincil", "olumlu", "olumsuz", "yazi"]).default("olumlu").describe("Tema rengi adı; onaltılık renk yazılmaz"),
});

const BILEK = "M7 10v12";
const EL =
  "M15 5.88 14 10h5.83a2 2 0 0 1 1.92 2.56l-2.33 8A2 2 0 0 1 17.5 22H4a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2h2.76a2 2 0 0 0 1.79-1.11L12 2a3.13 3.13 0 0 1 3 3.88Z";
const BILEK_UZ = 12.5;
const ISINLAR: Array<[number, number, number, number]> = [
  [12.2, 0.2, 12.4, -1.9],
  [9.2, 1.3, 7.6, -0.3],
  [15.4, 1.4, 17.1, -0.1],
];

const Begeni: React.FC<BilesenProps<z.infer<typeof sema>>> = ({ param, kutu, sureKare, u }) => {
  const t = useTema();
  const a = useAkis(sureKare, meta.giris_sn, meta.cikis_sn);
  const gradId = `begeni-g-${React.useId().replace(/[^a-zA-Z0-9_-]/g, "")}`;
  const pBilek = a.sirali(1, 3, "enter");
  const yay = a.yay(0, "elastik");
  const otur = a.takip(a.girKare - 2, 165);
  const isin = Math.max(0, Math.min(1, a.vurgu(a.girKare - 2, Math.round(0.32 * a.fps))));
  const isinOp = Math.sin(isin * Math.PI) * (1 - a.cik);
  const aci = 4 * (1 - a.gir) + 12 * a.ters - 12 * (a.gorunur - otur) + a.nefes * 1.4 + 14 * a.cik;
  const y = 3.5 * (1 - a.gir) + 1.6 * a.ters + a.nefes * -0.35 + 4.0 * a.cik;
  const olcek = (1 - 0.06 * a.ters) * (0.9 + 0.1 * Math.min(1.08, yay) + 0.05 * (otur - a.gorunur)) * (1 + 0.015 * a.nefes) * (1 - 0.3 * a.cik);
  const cizgi = ikonKalinlik(t, kutu, u, 24);
  const renk = t.renk[param.renk];
  const is = ikonStil(t, renk, u);
  const blur = a.hizBulaniklik > 0.08 ? `blur(${(a.hizBulaniklik * 0.4 * u).toFixed(2)}px) ` : "";

  const ciz = (stroke: string, strokeWidth: number, op = 1, dx = 0, dy = 0) => (
    <g transform={`translate(${dx} ${y + dy}) rotate(${aci} 5 19)`} opacity={op}>
      <path d={EL} fill="none" stroke={stroke} strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round" />
      <path
        d={BILEK}
        fill="none"
        stroke={stroke}
        strokeWidth={strokeWidth}
        strokeLinecap="round"
        strokeLinejoin="round"
        opacity={Math.min(1, pBilek * 6)}
        strokeDasharray={BILEK_UZ}
        strokeDashoffset={cizgiOfset(BILEK_UZ, pBilek)}
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
      <defs>
        <linearGradient id={gradId} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor={ton(renk, -0.35, 0.44)} />
          <stop offset="100%" stopColor={is.dolgu} />
        </linearGradient>
      </defs>
      {/* Katman 1: duotone el dolgusu */}
      <g transform={`translate(0 ${y}) rotate(${aci} 5 19)`}>
        <path d={EL} fill={`url(#${gradId})`} opacity={0.95 * a.gir} />
      </g>
      {/* Katman 2: rafine koyu kontur + canlı ana çizgi + ince üst parıltı */}
      {ciz(is.kontur, cizgi + KONTUR_EK, 0.9)}
      {ciz(is.vurgu, cizgi, 1)}
      {ciz(is.parilti, cizgi * 0.25, 0.72 * a.gir, -0.18, -0.22)}
      {/* Katman 3: başparmak tepesinden yayılan onay ışınları */}
      {isinOp > 0.01 &&
        ISINLAR.map(([x1, y1, x2, y2], i) => (
          <line
            key={i}
            x1={x1 + (x2 - x1) * 0.2 * isin}
            y1={y1 + (y2 - y1) * 0.2 * isin}
            x2={x1 + (x2 - x1) * (0.4 + 0.7 * isin)}
            y2={y1 + (y2 - y1) * (0.4 + 0.7 * isin)}
            stroke={i === 0 ? is.parilti : is.vurgu}
            strokeWidth={cizgi * 0.3}
            strokeLinecap="round"
            opacity={isinOp}
          />
        ))}
    </svg>
  );
};

export default tanimla({ meta: meta as never, sema, Bilesen: Begeni });
