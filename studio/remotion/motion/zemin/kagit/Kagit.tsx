// Kağıt dokulu zemin: tema zemini üstüne ince kağıt lifleri, adımlı analog mikro kayma ve çok hafif ışık geçişi. Ön planı boğmaz.
import React, { useId } from "react";
import { random } from "remotion";
import { z } from "zod";
import { dokuKatmani, rgba, useTema } from "../../../tema";
import { useAkis } from "../../cekirdek/zaman";
import { tanimla, type BilesenProps } from "../../cekirdek/tipler";
import meta from "./meta.json";

export const sema = z.strictObject({
  tohum: z.number().int().min(1).max(999).default(17).describe("Kağıt lifi ve benek yerleşimi için deterministik tohum"),
  doku: z.number().min(0.3).max(1.5).default(1.0).describe("Kağıt lifi görünürlük katsayısı"),
  renk: z.enum(["vurgu", "ikincil", "olumlu", "olumsuz", "yazi"]).default("ikincil").describe("Çok hafif sıcak kenar ışığı tema rengi adı"),
});

const Kagit: React.FC<BilesenProps<z.infer<typeof sema>>> = ({ param, kutu, sureKare, u }) => {
  const t = useTema();
  const a = useAkis(sureKare, meta.giris_sn, meta.cikis_sn);
  const uid = useId().replace(/[^a-zA-Z0-9_-]/g, "");

  const tSn = a.f / a.fps;
  // Anticipation: a.ters ile kağıt tabakası hafif yukarı yoklar, sonra yerine oturur; 10 karede bir analog mikro nefes alır.
  const kayY = (1 - a.gir) * 18 * u - 8 * u * a.ters + a.cik * -14 * u;
  const adim = Math.floor(a.f / 10);
  const mikroX = (random(`zk-${param.tohum}-mx-${adim}`) - 0.5) * 4 * u;
  const mikroY = (random(`zk-${param.tohum}-my-${adim}`) - 0.5) * 4 * u;

  const isikX = 36 + Math.sin(tSn * 0.25) * 16;
  const isikY = 32 + Math.cos(tSn * 0.22) * 14;
  const lifId = `zemin-kagit-lif-${uid}`;
  const cizgiId = `zemin-kagit-cz-${uid}`;
  const doku = dokuKatmani(t);

  const payX = Math.round(kutu.w * 0.04);
  const payY = Math.round(kutu.h * 0.04);
  const svgW = kutu.w + payX * 2;
  const svgH = kutu.h + payY * 2;

  // Çok hafif organik kağıt benekleri (düşük kontrast, ön planı bozmaz).
  const benekler = Array.from({ length: 28 }, (_, i) => {
    const k = `zkb-${param.tohum}-${i}`;
    return {
      x: random(`${k}-x`) * svgW,
      y: random(`${k}-y`) * svgH,
      r: (1.2 + random(`${k}-r`) * 2.2) * u,
      op: (0.06 + random(`${k}-o`) * 0.07) * param.doku,
    };
  });

  const cizgiAralik = Math.max(18, Math.round(28 * u));

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
      {/* Yavaş gezinen çok hafif kağıt ışığı */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: `radial-gradient(ellipse 75% 65% at ${isikX.toFixed(1)}% ${isikY.toFixed(1)}%, ${rgba(t.renk[param.renk], 0.075)} 0%, transparent 72%)`,
        }}
      />

      {doku && (
        <div
          style={{
            position: "absolute",
            inset: "-4%",
            backgroundImage: doku,
            opacity: 0.45 * param.doku,
            transform: `translate(${mikroX.toFixed(1)}px, ${(kayY + mikroY).toFixed(1)}px)`,
          }}
        />
      )}

      {/* Kağıt lifi, yatay ince su yolu çizgileri ve organik benekler (-4% taşma payı) */}
      <svg
        width={svgW}
        height={svgH}
        viewBox={`0 0 ${svgW} ${svgH}`}
        style={{
          position: "absolute",
          left: -payX,
          top: -payY,
          transform: `translate(${mikroX.toFixed(1)}px, ${(kayY + mikroY).toFixed(1)}px)`,
        }}
      >
        <defs>
          <filter id={lifId}>
            <feTurbulence
              type="fractalNoise"
              baseFrequency="0.24"
              numOctaves={4}
              seed={param.tohum}
              stitchTiles="stitch"
            />
            <feColorMatrix type="saturate" values="0" />
          </filter>
          <pattern id={cizgiId} width={cizgiAralik} height={cizgiAralik} patternUnits="userSpaceOnUse">
            <line
              x1={0}
              y1={cizgiAralik * 0.5}
              x2={cizgiAralik}
              y2={cizgiAralik * 0.5}
              stroke={rgba(t.renk.yazi, 0.085 * param.doku)}
              strokeWidth={Math.max(1.2 * u, 1.5 * u)}
            />
          </pattern>
        </defs>

        <rect width={svgW} height={svgH} filter={`url(#${lifId})`} opacity={0.16 * param.doku} />
        <rect width={svgW} height={svgH} fill={`url(#${cizgiId})`} />
        {benekler.map((b, i) => (
          <circle key={i} cx={b.x} cy={b.y} r={b.r} fill={t.renk.yazi} opacity={b.op} />
        ))}
      </svg>
    </div>
  );
};

export default tanimla({ meta: meta as never, sema, Bilesen: Kagit });
