// Alev: çok katmanlı duotone dolgu, parlak iç çekirdek alev ve yükselen köz kıvılcımlarıyla organik titremeyle yanar.
// Geometri: Lucide "flame" (ISC, https://lucide.dev/icons/flame), 24 birimlik viewBox.
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

const YOL =
  "M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z";
const IC_ALEV = "M12 10.6c.9 1.6 2.5 2.8 2.5 4.9a2.8 2.8 0 1 1-5.6 0c0-1.1.5-2.1 1.4-3 .3.7.9 1.1 1.4.8.4-.3.4-1.3.3-2.7z";

const Ates: React.FC<BilesenProps<z.infer<typeof sema>>> = ({ param, kutu, sureKare, u }) => {
  const t = useTema();
  const a = useAkis(sureKare, meta.giris_sn, meta.cikis_sn);
  const uid = React.useId().replace(/[^a-zA-Z0-9_-]/g, "");
  const klipId = `ates-${uid}`;
  const gradId = `ates-g-${uid}`;
  const yay = a.yay(0, "elastik");
  const otur = a.takip(a.girKare - 2, 175);
  const tSn = a.f / a.fps;
  const tit = (Math.sin(tSn * 22) * 0.6 + Math.sin(tSn * 35 + 1.1) * 0.4) * a.gorunur;
  const sy = (1 - 0.22 * a.ters) * (0.94 + 0.06 * Math.min(1.08, yay)) * (1 + 0.1 * (a.gorunur - otur)) * (1 + 0.06 * tit + 0.02 * a.nefes) * (1 - 0.45 * a.cik);
  const sx = (1 + 0.18 * a.ters) * (1 - 0.06 * (a.gorunur - otur)) * (1 - 0.03 * tit - 0.01 * a.nefes) * (1 - 0.25 * a.cik);
  const egimX = Math.sin(tSn * 17 + 0.5) * 3.0 * a.gorunur;
  const klipY = 16.5 - 20.5 * a.gir;
  const cizgi = ikonKalinlik(t, kutu, u, 24);
  const renk = t.renk[param.renk];
  const is = ikonStil(t, renk, u);
  const blur = a.hizBulaniklik > 0.08 ? `blur(${(a.hizBulaniklik * 0.42 * u).toFixed(2)}px) ` : "";

  // Yükselen iki küçük köz parçacığı (kendi geometrisinden yukarı süzülür)
  const koz1 = (tSn * 1.15) % 1;
  const koz2 = (tSn * 1.15 + 0.48) % 1;
  const kozOp = (p: number) => Math.sin(p * Math.PI) * a.gorunur;

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
        <clipPath id={klipId}>
          <rect x="-4" y={klipY} width="32" height="32" />
        </clipPath>
        <linearGradient id={gradId} x1="0.5" y1="0" x2="0.5" y2="1">
          <stop offset="0%" stopColor={ton(renk, -0.4, 0.48)} />
          <stop offset="100%" stopColor={is.dolgu} />
        </linearGradient>
      </defs>
      <g clipPath={`url(#${klipId})`}>
        <g transform={`translate(12 21) skewX(${egimX}) scale(${sx} ${sy}) translate(-12 -21)`}>
          {/* Katman 1: duotone hacim dolgusu + sıcak çekirdek alev */}
          <path d={YOL} fill={`url(#${gradId})`} opacity={0.9 * a.gir} />
          <path d={IC_ALEV} fill={is.parilti} opacity={0.42 * a.gorunur * (0.85 + 0.15 * tit)} />
          {/* Katman 2: rafine koyu kontur + canlı ana çizgi + ince parlama */}
          <path
            d={YOL}
            fill="none"
            stroke={is.kontur}
            strokeWidth={cizgi + KONTUR_EK}
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeOpacity={0.9}
          />
          <path
            d={YOL}
            fill="none"
            stroke={is.vurgu}
            strokeWidth={cizgi}
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          <path
            d={YOL}
            fill="none"
            stroke={is.parilti}
            strokeWidth={cizgi * 0.26}
            strokeLinecap="round"
            strokeLinejoin="round"
            transform="translate(-0.18 -0.24)"
            opacity={0.72 * a.gir}
          />
        </g>
      </g>
      {/* Katman 3: uçtan yükselen iki ince köz kıvılcımı */}
      <circle
        cx={10.2 + Math.sin(koz1 * Math.PI * 2) * 1.1}
        cy={4.2 - koz1 * 4.5}
        r={0.85 * (1 - koz1 * 0.55)}
        fill={is.parilti}
        opacity={kozOp(koz1) * 0.9}
      />
      <circle
        cx={14.6 + Math.cos(koz2 * Math.PI * 2) * 1.0}
        cy={5.4 - koz2 * 4.2}
        r={0.75 * (1 - koz2 * 0.55)}
        fill={is.vurgu}
        opacity={kozOp(koz2) * 0.85}
      />
    </svg>
  );
};

export default tanimla({ meta: meta as never, sema, Bilesen: Ates });
