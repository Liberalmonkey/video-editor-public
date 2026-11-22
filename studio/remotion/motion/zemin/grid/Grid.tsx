// Teknik ızgara zemini: tema rengiyle ince ve ana ızgara çizgileri, yavaş çapraz sürüklenme ve yumuşak kenar vinyeti. Ön planı boğmaz.
import React, { useId } from "react";
import { z } from "zod";
import { rgba, useTema } from "../../../tema";
import { useAkis } from "../../cekirdek/zaman";
import { tanimla, type BilesenProps } from "../../cekirdek/tipler";
import meta from "./meta.json";

export const sema = z.strictObject({
  renk: z.enum(["vurgu", "ikincil", "olumlu", "olumsuz", "yazi"]).default("vurgu").describe("Ana ızgara kesişimleri için vurgu tema rengi adı"),
  aralik: z.number().min(40).max(140).default(72).describe("Küçük kare aralığı (1080p piksel)"),
  hiz: z.number().min(0).max(2).default(1).describe("Yavaş sürüklenme hız katsayısı"),
});

const Grid: React.FC<BilesenProps<z.infer<typeof sema>>> = ({ param, kutu, sureKare, u }) => {
  const t = useTema();
  const a = useAkis(sureKare, meta.giris_sn, meta.cikis_sn);
  const uid = useId().replace(/[^a-zA-Z0-9_-]/g, "");
  const vurgu = t.renk[param.renk];

  // Anticipation: a.ters ile hafif içe toparlanma, ardından ızgara nefes alarak yerine oturur ve yavaş sürüklenir.
  const tSn = a.f / a.fps;
  const olcek = (1 - 0.018 * a.ters) * (0.97 + 0.03 * a.gir) * (1 - 0.015 * a.cik);
  const hucre = Math.max(24, Math.round(param.aralik * u));
  const anaHucre = hucre * 4;

  const dx = ((tSn * 16 * param.hiz * u) % anaHucre + anaHucre) % anaHucre;
  const dy = ((tSn * 11 * param.hiz * u) % anaHucre + anaHucre) % anaHucre;
  const isikX = 50 + Math.sin(tSn * 0.42) * 18;
  const isikY = 50 + Math.cos(tSn * 0.34) * 14;

  const kucukId = `zemin-grid-k-${uid}`;
  const buyukId = `zemin-grid-b-${uid}`;
  const vinyetId = `zemin-grid-v-${uid}`;

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
      {/* Yavaş gezinen çok hafif tema ışığı */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: `radial-gradient(circle at ${isikX.toFixed(1)}% ${isikY.toFixed(1)}%, ${rgba(vurgu, 0.11)} 0%, transparent 58%)`,
        }}
      />

      <svg
        width={kutu.w}
        height={kutu.h}
        viewBox={`0 0 ${kutu.w} ${kutu.h}`}
        style={{
          position: "absolute",
          inset: 0,
          transformOrigin: "center center",
          transform: `scale(${olcek})`,
        }}
      >
        <defs>
          <pattern id={kucukId} width={hucre} height={hucre} patternUnits="userSpaceOnUse">
            <path
              d={`M ${hucre} 0 L 0 0 0 ${hucre}`}
              fill="none"
              stroke={rgba(t.renk.yazi, 0.15)}
              strokeWidth={2 * u}
            />
          </pattern>
          <pattern
            id={buyukId}
            width={anaHucre}
            height={anaHucre}
            patternUnits="userSpaceOnUse"
            patternTransform={`translate(${dx.toFixed(2)} ${dy.toFixed(2)})`}
          >
            <rect width={anaHucre} height={anaHucre} fill={`url(#${kucukId})`} />
            <path
              d={`M ${anaHucre} 0 L 0 0 0 ${anaHucre}`}
              fill="none"
              stroke={rgba(vurgu, 0.26)}
              strokeWidth={2.8 * u}
            />
            <line x1={0} y1={-7 * u} x2={0} y2={7 * u} stroke={rgba(vurgu, 0.42)} strokeWidth={2.8 * u} />
            <line x1={-7 * u} y1={0} x2={7 * u} y2={0} stroke={rgba(vurgu, 0.42)} strokeWidth={2.8 * u} />
          </pattern>
          <radialGradient id={vinyetId} cx="50%" cy="50%" r="72%">
            <stop offset="54%" stopColor={t.renk.zemin} stopOpacity={0} />
            <stop offset="100%" stopColor={t.renk.zemin} stopOpacity={0.38} />
          </radialGradient>
        </defs>

        <rect width={kutu.w} height={kutu.h} fill={`url(#${buyukId})`} />
        <rect width={kutu.w} height={kutu.h} fill={`url(#${vinyetId})`} />
      </svg>
    </div>
  );
};

export default tanimla({ meta: meta as never, sema, Bilesen: Grid });
