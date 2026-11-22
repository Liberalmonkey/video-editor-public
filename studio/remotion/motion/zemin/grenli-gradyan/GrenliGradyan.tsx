// Grenli gradyan zemini: tema renklerinden üç yumuşak ışık bulutu Lissajous yörüngesinde yavaşça süzülür, üstünde ince film greni vardır.
import React, { useId } from "react";
import { z } from "zod";
import { dokuKatmani, rgba, useTema } from "../../../tema";
import { useAkis } from "../../cekirdek/zaman";
import { tanimla, type BilesenProps } from "../../cekirdek/tipler";
import meta from "./meta.json";

export const sema = z.strictObject({
  renk: z.enum(["vurgu", "ikincil", "olumlu", "olumsuz", "yazi"]).default("vurgu").describe("Birinci ışık bulutu tema rengi adı"),
  ikinci: z.enum(["vurgu", "ikincil", "olumlu", "olumsuz", "yazi"]).default("ikincil").describe("İkinci ışık bulutu tema rengi adı"),
  yogunluk: z.number().min(0.4).max(1.4).default(1.0).describe("Renk bulutlarının yumuşak parlaklık katsayısı"),
});

const GrenliGradyan: React.FC<BilesenProps<z.infer<typeof sema>>> = ({ param, kutu, sureKare }) => {
  const t = useTema();
  const a = useAkis(sureKare, meta.giris_sn, meta.cikis_sn);
  const uid = useId().replace(/[^a-zA-Z0-9_-]/g, "");

  const tSn = a.f / a.fps;
  // Anticipation: a.ters ile ışık bulutları kısa içe toplanır, sonra a.gir ile yumuşakça yayılır.
  const yayil = (1 - 0.06 * a.ters) * (0.86 + 0.14 * a.gir) * (1 - 0.05 * a.cik);
  const yog = param.yogunluk;

  const r1 = t.renk[param.renk];
  const r2 = t.renk[param.ikinci];
  const r3 = t.renk.soluk;

  // Üç yavaş yörüngeli atmosfer bulutu
  const b1x = 28 + Math.sin(tSn * 0.45) * 16;
  const b1y = 30 + Math.cos(tSn * 0.36) * 14;
  const b2x = 74 + Math.cos(tSn * 0.38 + 1.2) * 15;
  const b2y = 68 + Math.sin(tSn * 0.42 + 0.8) * 14;
  const b3x = 52 + Math.sin(tSn * 0.28 + 2.4) * 18;
  const b3y = 50 + Math.cos(tSn * 0.31 + 1.9) * 15;

  const grenId = `zemin-gren-${uid}`;
  // Film greni her 4 karede ince adım değiştirir (organik sinema dokusu).
  const grenTohum = 1 + (Math.floor(a.f / 4) % 24);
  const doku = dokuKatmani(t);

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
      {/* Düşük kontrastlı üç katmanlı renk bulutları */}
      <div
        style={{
          position: "absolute",
          inset: "-8%",
          transformOrigin: "center center",
          transform: `scale(${yayil})`,
          background: [
            `radial-gradient(ellipse 62% 54% at ${b1x.toFixed(1)}% ${b1y.toFixed(1)}%, ${rgba(r1, 0.2 * yog)} 0%, transparent 70%)`,
            `radial-gradient(ellipse 58% 58% at ${b2x.toFixed(1)}% ${b2y.toFixed(1)}%, ${rgba(r2, 0.16 * yog)} 0%, transparent 72%)`,
            `radial-gradient(ellipse 68% 48% at ${b3x.toFixed(1)}% ${b3y.toFixed(1)}%, ${rgba(r3, 0.12 * yog)} 0%, transparent 74%)`,
          ].join(", "),
        }}
      />

      {/* Tema dokusu varsa uygula */}
      {doku && (
        <div
          style={{
            position: "absolute",
            inset: 0,
            backgroundImage: doku,
            opacity: 0.42,
            pointerEvents: "none",
          }}
        />
      )}

      {/* İnce hareketli film greni katmanı */}
      <svg
        width={kutu.w}
        height={kutu.h}
        viewBox={`0 0 ${kutu.w} ${kutu.h}`}
        style={{ position: "absolute", inset: 0, pointerEvents: "none", opacity: 0.13 }}
      >
        <defs>
          <filter id={grenId}>
            <feTurbulence type="fractalNoise" baseFrequency="0.78" numOctaves={2} seed={grenTohum} stitchTiles="stitch" />
            <feColorMatrix type="saturate" values="0" />
          </filter>
        </defs>
        <rect width={kutu.w} height={kutu.h} filter={`url(#${grenId})`} />
      </svg>
    </div>
  );
};

export default tanimla({ meta: meta as never, sema, Bilesen: GrenliGradyan });
