// Kağıt dokulu çerçeve: yuzeyStil katman gölgesi, lifli paspartu kenarlık, parlama şeridi ve içi tamamen saydam pencere.
import React, { useId } from "react";
import { interpolate } from "remotion";
import { z } from "zod";
import { dokuKatmani, parlamaStil, rgba, ton, useTema, yuzeyStil } from "../../../tema";
import { cizgiOfset, useAkis } from "../../cekirdek/zaman";
import { tanimla, type BilesenProps } from "../../cekirdek/tipler";
import meta from "./meta.json";

export const sema = z.strictObject({
  renk: z.enum(["vurgu", "ikincil", "olumlu", "olumsuz", "yazi"]).default("vurgu").describe("İç paspartu ince çizgi tema rengi adı"),
  kalinlik: z.number().min(0.05).max(0.16).default(0.09).describe("Kağıt kenar kalınlığının kısa kenara oranı"),
});

const KIS = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

const Kagit: React.FC<BilesenProps<z.infer<typeof sema>>> = ({ param, kutu, sureKare, u }) => {
  const t = useTema();
  const a = useAkis(sureKare, meta.giris_sn, meta.cikis_sn);
  const uid = useId().replace(/[^a-zA-Z0-9_-]/g, "");
  const vurgu = t.renk[param.renk];
  const yuzey = yuzeyStil(t, u, "kart");

  const otur = a.yay(3, "ipeksi");
  const olcek = (1 - 0.05 * a.ters) * (0.93 + 0.07 * Math.max(0, Math.min(1.06, otur))) * (1 + 0.005 * a.nefes) * (1 - 0.06 * a.cik);
  const icCiz = a.e.enter(interpolate(a.f, [a.hazirlikKare + 2, a.girKare + 5], [0, 1], KIS));
  const blur = a.hizBulaniklik > 0.08 ? `blur(${(a.hizBulaniklik * 0.4 * u).toFixed(2)}px)` : undefined;

  const kenarPx = Math.max(24 * u, Math.round(Math.min(kutu.w, kutu.h) * param.kalinlik));
  const kose = Math.max(4 * u, Math.round(t.sekil.kose * 0.45 * u));

  const doku = dokuKatmani(t);
  const matGradyan = `linear-gradient(165deg, ${rgba(t.renk.zemin, 0.96)} 0%, ${ton(t.renk.zemin, 0.08, 0.95)} 100%)`;
  const kagitArka = doku ? `${doku}, ${matGradyan}` : matGradyan;

  const icW = Math.max(40, kutu.w - kenarPx * 2);
  const icH = Math.max(40, kutu.h - kenarPx * 2);
  const cizgiPay = Math.round(kenarPx * 0.34);
  const cizgiX = kenarPx - cizgiPay;
  const cizgiY = kenarPx - cizgiPay;
  const cizgiW = icW + cizgiPay * 2;
  const cizgiH = icH + cizgiPay * 2;
  const cevre = (cizgiW + cizgiH) * 2;

  const lifId = `kagit-lif-${uid}`;
  const maskeId = `kagit-pencere-${uid}`;
  const cerceveYol = `M0 0 H${kutu.w} V${kutu.h} H0 Z M${kenarPx} ${kenarPx} H${kenarPx + icW} V${kenarPx + icH} H${kenarPx} Z`;

  return (
    <div
      style={{
        position: "relative",
        width: kutu.w,
        height: kutu.h,
        display: "flex",
        flexDirection: "column",
        borderRadius: kose,
        overflow: "hidden",
        border: yuzey.border,
        boxShadow: `0 ${2 * u}px ${6 * u}px ${rgba(t.renk.ikon_kontur, 0.25)}, 0 ${20 * u}px ${44 * u}px ${rgba(t.renk.ikon_kontur, 0.38)}`,
        boxSizing: "border-box",
        opacity: a.belir * (1 - a.cik),
        filter: blur,
        transformOrigin: "center center",
        transform: `translateY(${a.nefes * -1.8 * u}px) scale(${olcek})`,
      }}
    >
      {/* Üst kağıt şeridi */}
      <div style={{ position: "relative", height: kenarPx, width: "100%", background: kagitArka, flexShrink: 0, overflow: "hidden" }}>
        <div style={parlamaStil(t, a.parlama, u)} />
      </div>

      {/* Orta satır: sol şerit + içi %100 saydam pencere + sağ şerit */}
      <div style={{ flex: 1, display: "flex", minHeight: 0 }}>
        <div style={{ width: kenarPx, background: kagitArka, flexShrink: 0 }} />
        <div
          style={{
            flex: 1,
            background: "transparent",
            boxShadow: `inset 0 ${4 * u}px ${14 * u}px ${rgba(t.renk.ikon_kontur, 0.36)}, inset 0 0 0 ${Math.max(1.5, Math.round(1.5 * u))}px ${rgba(t.renk.yazi, 0.2)}`,
          }}
        />
        <div style={{ width: kenarPx, background: kagitArka, flexShrink: 0 }} />
      </div>

      {/* Alt kağıt şeridi */}
      <div style={{ height: kenarPx, width: "100%", background: kagitArka, flexShrink: 0 }} />

      {/* Yalnız paspartu kenarına uygulanan kağıt lifi dokusu + çizilen ince vurgu çizgisi */}
      <svg width={kutu.w} height={kutu.h} viewBox={`0 0 ${kutu.w} ${kutu.h}`} style={{ position: "absolute", inset: 0, pointerEvents: "none" }}>
        <defs>
          <filter id={lifId}>
            <feTurbulence type="fractalNoise" baseFrequency="0.045" numOctaves={4} seed={9} stitchTiles="stitch" />
          </filter>
          <clipPath id={maskeId}>
            <path d={cerceveYol} clipRule="evenodd" />
          </clipPath>
        </defs>

        <rect width={kutu.w} height={kutu.h} filter={`url(#${lifId})`} opacity={0.14} clipPath={`url(#${maskeId})`} />

        <rect
          x={cizgiX}
          y={cizgiY}
          width={cizgiW}
          height={cizgiH}
          fill="none"
          stroke={ton(vurgu, -0.15, 0.85)}
          strokeWidth={Math.max(1.5, 2.2 * u)}
          strokeDasharray={cevre}
          strokeDashoffset={cizgiOfset(cevre, icCiz)}
        />
      </svg>
    </div>
  );
};

export default tanimla({ meta: meta as never, sema, Bilesen: Kagit });
