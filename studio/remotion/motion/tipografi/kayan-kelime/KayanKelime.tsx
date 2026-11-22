// Kayan kelime: kısa, vurucu kinetik tipografi patlaması — hız bulanıklığı + maskeli kelime girişi + altından çizilen parlak vurgu çizgisi.
import React from "react";
import { interpolate } from "remotion";
import { z } from "zod";
import {
  golge, harf, karistir, koyuMu, parlamaStil, rgba, titremeOpaklik, titresim,
  useTema, yigin, yuzeyStil, yuzeyTipi, yuzeyYazi,
} from "../../../tema";
import { useAkis } from "../../cekirdek/zaman";
import { tanimla, type BilesenProps } from "../../cekirdek/tipler";
import meta from "./meta.json";

export const sema = z.strictObject({
  metin: z.string().max(26).default("VİRAL").describe("Kısa, vurucu tek veya çift kelimelik başlık"),
  alt: z.string().max(32).default("").describe("İsteğe bağlı kısa destekleyici alt kelime; boşsa gizlenir"),
  renk: z.enum(["vurgu", "ikincil", "olumlu", "olumsuz", "yazi"]).default("vurgu").describe("Alt vurgu çizgisi ve parıltı tema rengi adı"),
});

const KIS = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

const KayanKelime: React.FC<BilesenProps<z.infer<typeof sema>>> = ({ param, kutu, sureKare, u }) => {
  const t = useTema();
  const a = useAkis(sureKare, meta.giris_sn, meta.cikis_sn);
  const g = golge(t, u);
  const tip = yuzeyTipi(t);
  const koyu = koyuMu(t.renk.zemin);
  const vurgu = t.renk[param.renk];
  const keskin = tip === "piksel" || tip === "brutalist";
  const altVar = param.alt.trim().length > 0;

  const kelimeler = harf(t, param.metin).trim().split(/\s+/).filter(Boolean);
  const plakaYay = a.yay(0, "keskin");
  const cizgiIler = a.e.emphasis(interpolate(a.f, [a.hazirlikKare + 1, a.girKare + 3], [0, 1], KIS));
  const altGir = a.sirali(Math.min(3, kelimeler.length + 1), 2, "settle");

  const kaymaX = -14 * u * a.ters + (1 - Math.min(1.06, plakaYay)) * -44 * u + a.cik * 38 * u;
  const egim = (1 - Math.min(1, a.gir)) * -7 + a.cik * 6;
  const olcek = (0.92 + 0.08 * Math.min(1.06, plakaYay)) * (1 - 0.05 * a.cik) * (1 + 0.007 * a.nefes);

  const uzunluk = param.metin.trim().length;
  const oran = uzunluk > 18 ? 0.28 : uzunluk > 10 ? 0.35 : 0.43;
  const kelimeBoy = Math.max(42 * u, Math.round(kutu.h * (altVar ? oran * 0.86 : oran)));
  const altBoy = Math.max(28 * u, Math.round(kutu.h * 0.17));

  const blur = a.hizBulaniklik > 0.08 ? `blur(${(a.hizBulaniklik * u).toFixed(2)}px)` : undefined;
  const tit = titremeOpaklik(t, a.f);
  const titr = titresim(t, a.f, u);
  const yuzey = yuzeyStil(t, u, "bant");
  const metinGolge = keskin
    ? g.yazi
    : `0 ${3 * u}px ${14 * u}px ${rgba(t.renk.ikon_kontur, koyu ? 0.65 : 0.16)}`;

  return (
    <div
      style={{
        width: kutu.w,
        height: kutu.h,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <div
        style={{
          ...yuzey,
          position: "relative",
          overflow: "hidden",
          maxWidth: "100%",
          padding: `${Math.round(14 * u)}px ${Math.round(32 * u)}px ${Math.round(16 * u)}px`,
          display: "inline-flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: Math.round(8 * u),
          boxSizing: "border-box",
          transform: `translateX(${kaymaX}px) skewX(${egim}deg) scale(${olcek}) ${titr}`,
          opacity: a.belir * (1 - a.cik) * tit,
          filter: blur,
        }}
      >
        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            alignItems: "baseline",
            justifyContent: "center",
            columnGap: Math.round(kelimeBoy * 0.24),
            rowGap: Math.round(kelimeBoy * 0.08),
            fontFamily: yigin(t.font.baslik),
            fontWeight: t.font.agirlik_baslik,
            fontSize: kelimeBoy,
            lineHeight: 1.04,
            letterSpacing: `${Math.max(0.02, t.font.izleme)}em`,
            color: yuzeyYazi(t, "bant"),
            textShadow: metinGolge,
            textAlign: "center",
            maxWidth: "100%",
          }}
        >
          {kelimeler.map((kelime, i) => {
            const kYay = a.yay(i * 2, "keskin");
            const kSir = a.sirali(i, 2, "enter");
            return (
              <span key={i} style={{ display: "inline-block", overflow: "hidden", paddingBottom: Math.round(2 * u) }}>
                <span
                  style={{
                    display: "inline-block",
                    transform: `translateY(${(1 - Math.min(1.06, kYay)) * 112}%)`,
                    opacity: Math.min(1, kSir * 2.6),
                  }}
                >
                  {kelime}
                </span>
              </span>
            );
          })}
        </div>

        <div
          style={{
            position: "relative",
            width: "100%",
            height: Math.max(4, Math.round(6 * u)),
            borderRadius: keskin ? 0 : Math.round(6 * u),
            background: rgba(t.renk.yazi, 0.12),
            overflow: "hidden",
          }}
        >
          <div
            style={{
              width: "100%",
              height: "100%",
              borderRadius: keskin ? 0 : Math.round(6 * u),
              background: keskin
                ? vurgu
                : `linear-gradient(90deg, ${vurgu} 0%, ${karistir(vurgu, t.renk.ikincil, 0.45)} 100%)`,
              boxShadow: keskin ? undefined : `0 0 ${14 * u}px ${rgba(vurgu, 0.8)}`,
              transformOrigin: "left center",
              transform: `scaleX(${cizgiIler * (1 - a.cik)})`,
            }}
          />
        </div>

        {altVar && (
          <div style={{ overflow: "hidden", maxWidth: "100%" }}>
            <div
              style={{
                fontFamily: yigin(t.font.govde),
                fontWeight: Math.max(600, t.font.agirlik_govde),
                fontSize: altBoy,
                lineHeight: 1.12,
                letterSpacing: `${Math.max(0.05, t.font.izleme)}em`,
                color: t.renk.soluk,
                whiteSpace: "nowrap",
                overflow: "hidden",
                textOverflow: "ellipsis",
                transform: `translateY(${(1 - altGir) * 85}%)`,
                opacity: Math.min(1, altGir * 2.2),
              }}
            >
              {harf(t, param.alt)}
            </div>
          </div>
        )}

        <div style={parlamaStil(t, a.parlama, u)} />
      </div>
    </div>
  );
};

export default tanimla({ meta: meta as never, sema, Bilesen: KayanKelime });
