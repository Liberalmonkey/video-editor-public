// Halftone (baskı tramı) zemini: 26° açılı baskı noktaları yavaşça kayar, kenarlarda belirginleşip merkezde sakinleşerek ön plana yer açar.
import React, { useId } from "react";
import { z } from "zod";
import { rgba, useTema } from "../../../tema";
import { useAkis } from "../../cekirdek/zaman";
import { tanimla, type BilesenProps } from "../../cekirdek/tipler";
import meta from "./meta.json";

export const sema = z.strictObject({
  renk: z.enum(["vurgu", "ikincil", "olumlu", "olumsuz", "yazi"]).default("vurgu").describe("Köşe tram vurgusu tema rengi adı"),
  aralik: z.number().min(20).max(64).default(34).describe("Tram nokta aralığı (1080p piksel)"),
  hiz: z.number().min(0).max(2).default(1).describe("Yavaş sürüklenme hız katsayısı"),
});

const Halftone: React.FC<BilesenProps<z.infer<typeof sema>>> = ({ param, kutu, sureKare, u }) => {
  const t = useTema();
  const a = useAkis(sureKare, meta.giris_sn, meta.cikis_sn);
  const uid = useId().replace(/[^a-zA-Z0-9_-]/g, "");
  const vurgu = t.renk[param.renk];

  const tSn = a.f / a.fps;
  const otur = a.takip(a.hazirlikKare + 2, 145);
  // Anticipation: a.ters ile tram açısı hafif geri yaslanır, sonra 26° baskı açısına oturur.
  const aci = 26 - 4.5 * a.ters + (1 - Math.min(1.04, Math.max(0, otur))) * 5;

  const hucre = Math.max(16, Math.round(param.aralik * u));
  const kay = ((tSn * 14 * param.hiz * u) % hucre + hucre) % hucre;
  const nefes = 0.92 + 0.08 * Math.sin(tSn * 0.85);

  const temelId = `zemin-ht-t-${uid}`;
  const vurguId = `zemin-ht-v-${uid}`;
  const merkezId = `zemin-ht-m-${uid}`;
  const koseId = `zemin-ht-k-${uid}`;

  return (
    <div
      style={{
        position: "relative",
        width: kutu.w,
        height: kutu.h,
        overflow: "hidden",
        background: t.renk.zemin,
        opacity: a.belir * (1 - a.cik),
      }}
    >
      <svg width={kutu.w} height={kutu.h} viewBox={`0 0 ${kutu.w} ${kutu.h}`} style={{ position: "absolute", inset: 0 }}>
        <defs>
          <pattern
            id={temelId}
            width={hucre}
            height={hucre}
            patternUnits="userSpaceOnUse"
            patternTransform={`rotate(${aci.toFixed(2)}) translate(${kay.toFixed(2)} ${(kay * 0.5).toFixed(2)})`}
          >
            <circle cx={hucre * 0.5} cy={hucre * 0.5} r={hucre * 0.14 * nefes} fill={rgba(t.renk.yazi, 0.12)} />
          </pattern>

          <pattern
            id={vurguId}
            width={hucre}
            height={hucre}
            patternUnits="userSpaceOnUse"
            patternTransform={`rotate(${aci.toFixed(2)}) translate(${(kay + hucre * 0.5).toFixed(2)} ${(kay * 0.5 + hucre * 0.5).toFixed(2)})`}
          >
            <circle cx={hucre * 0.5} cy={hucre * 0.5} r={hucre * 0.19 * nefes} fill={rgba(vurgu, 0.16)} />
          </pattern>

          {/* Merkez sakin kalır; ön plandaki yazı ve grafikler kolayca okunur */}
          <radialGradient id={merkezId} cx="50%" cy="50%" r="64%">
            <stop offset="0%" stopColor={t.renk.zemin} stopOpacity={0.78} />
            <stop offset="68%" stopColor={t.renk.zemin} stopOpacity={0.18} />
            <stop offset="100%" stopColor={t.renk.zemin} stopOpacity={0} />
          </radialGradient>

          {/* Köşe vurgu geçişi */}
          <linearGradient id={koseId} x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor={vurgu} stopOpacity={0.12} />
            <stop offset="45%" stopColor={vurgu} stopOpacity={0} />
            <stop offset="55%" stopColor={t.renk.ikincil} stopOpacity={0} />
            <stop offset="100%" stopColor={t.renk.ikincil} stopOpacity={0.1} />
          </linearGradient>
        </defs>

        <rect width={kutu.w} height={kutu.h} fill={`url(#${temelId})`} />
        <rect width={kutu.w} height={kutu.h} fill={`url(#${vurguId})`} opacity={0.7} />
        <rect width={kutu.w} height={kutu.h} fill={`url(#${koseId})`} />
        <rect width={kutu.w} height={kutu.h} fill={`url(#${merkezId})`} />
      </svg>
    </div>
  );
};

export default tanimla({ meta: meta as never, sema, Bilesen: Halftone });
