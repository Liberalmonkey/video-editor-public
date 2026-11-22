// Şok dalgası: yumuşak çok halkalı glow/parlama, ikonStil katmanları ve parlak radyal kıvılcımlarla dışa yayılır. Saydam alfa üstüne.
import React from "react";
import { interpolate } from "remotion";
import { z } from "zod";
import { ikonStil, rgba, ton, useTema } from "../../../tema";
import { useAkis } from "../../cekirdek/zaman";
import { tanimla, type BilesenProps } from "../../cekirdek/tipler";
import meta from "./meta.json";

export const sema = z.strictObject({
  renk: z.enum(["vurgu", "ikincil", "olumlu", "olumsuz", "yazi"]).default("vurgu").describe("Birincil şok halkası tema rengi adı"),
  halka: z.number().int().min(1).max(3).default(2).describe("Art arda yayılan halka sayısı (1-3)"),
});

const KIS = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

const SokDalgasi: React.FC<BilesenProps<z.infer<typeof sema>>> = ({ param, kutu, sureKare, u }) => {
  const t = useTema();
  const a = useAkis(sureKare, meta.giris_sn, meta.cikis_sn);
  const uid = React.useId().replace(/[^a-zA-Z0-9_-]/g, "");
  const glowId = `sok-glow-${uid}`;
  const anaRenk = t.renk[param.renk];
  const is = ikonStil(t, anaRenk, u);

  const cx = kutu.w / 2;
  const cy = kutu.h / 2;
  const maxR = Math.min(kutu.w, kutu.h) * 0.45;
  const basR = Math.max(14 * u, maxR * 0.18);

  const renkler = [anaRenk, t.renk.ikincil, anaRenk];
  const yayilimBitis = Math.max(a.hazirlikKare + 10, sureKare - a.cikKare);

  const cekirdekR = basR * (1 - 0.28 * a.ters);
  const yay = a.yay(0, "keskin");
  const cikisGenisle = a.cik * 16 * u;

  const halkalar = Array.from({ length: param.halka }, (_, i) => {
    const basKare = a.hazirlikKare + i * 4;
    const bitKare = Math.max(basKare + 6, yayilimBitis + i * 2);
    const p = a.e.settle(interpolate(a.f, [basKare, bitKare], [0, 1], KIS));
    const hedefOran = 1 - i * 0.24;
    const baslangicR = i === 0 ? cekirdekR : basR * (0.86 - i * 0.08);
    const r = baslangicR + (maxR * hedefOran - baslangicR) * p + cikisGenisle + a.nefes * 2.5 * u;

    const minKal = 8 * u;
    const basKal = (i === 0 ? 22 : i === 1 ? 16 : 12) * u;
    const kalinlik = minKal + (basKal - minKal) * Math.pow(1 - p, 1.15);

    const gor = i === 0 ? a.belir : a.e.enter(interpolate(a.f, [basKare, basKare + 4], [0, 1], KIS));
    const op = gor * (1 - 0.14 * p);
    const renk = renkler[i % renkler.length];
    const hIs = ikonStil(t, renk, u);
    return { r, kalinlik, op, renk, hIs };
  });

  const oncu = a.e.settle(interpolate(a.f, [a.hazirlikKare + 2, yayilimBitis], [0, 1], KIS));
  const cizgiOp = Math.min(1, oncu * 3) * (1 - 0.16 * oncu);
  const kivilcimOlcek = 0.94 + 0.06 * Math.max(0, Math.min(1.08, yay));

  return (
    <svg
      width={kutu.w}
      height={kutu.h}
      viewBox={`0 0 ${kutu.w} ${kutu.h}`}
      style={{
        overflow: "visible",
        filter: is.golge,
        opacity: a.belir * (1 - a.cik),
      }}
    >
      <defs>
        <filter id={glowId} x="-35%" y="-35%" width="170%" height="170%">
          <feGaussianBlur stdDeviation={(5.5 * u).toFixed(2)} />
        </filter>
      </defs>

      {halkalar.map((h, i) => (
        <g key={i} opacity={h.op}>
          {/* Yumuşak dış glow aura halkası */}
          <circle
            cx={cx}
            cy={cy}
            r={h.r}
            fill="none"
            stroke={rgba(h.renk, 0.42)}
            strokeWidth={h.kalinlik * 2.1}
            filter={`url(#${glowId})`}
          />
          {/* Duotone dolgu kılıfı */}
          <circle cx={cx} cy={cy} r={h.r} fill="none" stroke={h.hIs.dolgu} strokeWidth={h.kalinlik * 1.45} />
          {/* Canlı ana şok halkası */}
          <circle cx={cx} cy={cy} r={h.r} fill="none" stroke={h.renk} strokeWidth={h.kalinlik} />
          {/* İnce parlak iç ışık çekirdeği */}
          <circle cx={cx} cy={cy} r={h.r} fill="none" stroke={h.hIs.parilti} strokeWidth={Math.max(2 * u, h.kalinlik * 0.28)} opacity={0.85} />
        </g>
      ))}

      {/* Dışa fırlayan 8 parlak radyal şok kıvılcımı */}
      <g style={{ transformOrigin: `${cx}px ${cy}px`, transform: `scale(${kivilcimOlcek})` }}>
        {Array.from({ length: 8 }, (_, i) => {
          const aci = (i / 8) * Math.PI * 2 + Math.PI / 8;
          const r1 = basR + maxR * 0.72 * oncu + cikisGenisle;
          const r2 = r1 + Math.max(14 * u, 28 * u * (1 - oncu * 0.45));
          const kal = Math.max(4 * u, 6.2 * u * (1 - oncu * 0.3));
          const x1 = cx + Math.cos(aci) * r1;
          const y1 = cy + Math.sin(aci) * r1;
          const x2 = cx + Math.cos(aci) * r2;
          const y2 = cy + Math.sin(aci) * r2;
          return (
            <g key={i} opacity={cizgiOp}>
              <line x1={x1} y1={y1} x2={x2} y2={y2} stroke={is.dolgu} strokeWidth={kal * 1.9} strokeLinecap="round" />
              <line x1={x1} y1={y1} x2={x2} y2={y2} stroke={anaRenk} strokeWidth={kal} strokeLinecap="round" />
              <line x1={x1} y1={y1} x2={x2} y2={y2} stroke={ton(anaRenk, -0.58)} strokeWidth={kal * 0.34} strokeLinecap="round" />
            </g>
          );
        })}
      </g>
    </svg>
  );
};

export default tanimla({ meta: meta as never, sema, Bilesen: SokDalgasi });
