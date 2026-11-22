// Etiket çipi: yatay ters hazırlıkla hızla kayıp eğimle frenler, tek sönümde dikleşir; canlı nabızlı vurgu noktası + parlama.
import React from "react";
import { interpolate } from "remotion";
import { z } from "zod";
import {
  harf, parlamaStil, rgba, titremeOpaklik, titresim,
  useTema, yigin, yuzeyStil, yuzeyTipi, yuzeyYazi,
} from "../../../tema";
import { useAkis } from "../../cekirdek/zaman";
import { tanimla, type BilesenProps } from "../../cekirdek/tipler";
import meta from "./meta.json";

export const sema = z.strictObject({
  metin: z.string().max(24).default("KLİŞE").describe("Tek kelimelik kısa etiket metni"),
  renk: z.enum(["vurgu", "ikincil", "olumlu", "olumsuz", "yazi"]).default("vurgu").describe("Çip kenar ve nokta tema rengi adı"),
});

const KIS = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

const Cip: React.FC<BilesenProps<z.infer<typeof sema>>> = ({ param, kutu, sureKare, u }) => {
  const t = useTema();
  const a = useAkis(sureKare, meta.giris_sn, meta.cikis_sn);
  const tip = yuzeyTipi(t);
  const vurgu = t.renk[param.renk];
  const keskin = tip === "piksel" || tip === "brutalist";

  // Anticipation: a.ters ile sola çekilip ters eğilir, sonra yatay ivmeyle gelip tek sönümde dikleşir.
  const h = a.hazirlikKare;
  const onX = -14 * u * a.ters;
  const girX = (1 - a.gir) * -66 * u;
  const cikX = a.cik * 58 * u;
  const otur = a.yay(2, "keskin");
  const egimAna = interpolate(a.e.emphasis(interpolate(a.f, [h, a.girKare], [0, 1], KIS)), [0, 0.25, 0.65, 1], [0, 7, -3.5, 0], KIS);
  const egimGir = -4 * a.ters + egimAna;
  const egimCik = a.cik * 7;
  const icTakipX = (1 - a.sirali(1, 3, "settle")) * -16 * u;
  const noktaYay = a.yay(3, "elastik");
  const nabiz = 0.5 + 0.5 * a.nefes;

  const blur = a.hizBulaniklik > 0.08 ? `blur(${(a.hizBulaniklik * u).toFixed(2)}px)` : undefined;
  const tit = titremeOpaklik(t, a.f);
  const titr = titresim(t, a.f, u);
  const yuzey = yuzeyStil(t, u, "rozet");

  const yaziBoy = Math.max(42 * u, Math.round(kutu.h * 0.41));
  const noktaCap = Math.round(14 * u);

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
          padding: `${Math.round(14 * u)}px ${Math.round(30 * u)}px`,
          borderColor: keskin ? yuzey.borderColor : rgba(vurgu, tip === "neon" ? 0.92 : 0.48),
          display: "inline-flex",
          alignItems: "center",
          gap: Math.round(15 * u),
          boxSizing: "border-box",
          transform: `translate(${onX + girX + cikX + (1 - Math.min(1.04, otur)) * 8 * u}px, ${a.nefes * 1.4 * u}px) skewX(${egimGir + egimCik}deg) ${titr}`,
          opacity: a.belir * (1 - a.cik) * tit,
          filter: blur,
        }}
      >
        <div
          style={{
            position: "relative",
            width: noktaCap,
            height: noktaCap,
            flexShrink: 0,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            transform: `scale(${Math.max(0, noktaYay)})`,
          }}
        >
          {!keskin && (
            <div
              style={{
                position: "absolute",
                inset: Math.round(-4 * u),
                borderRadius: noktaCap,
                background: rgba(vurgu, 0.3 * (1 - nabiz * 0.55)),
                transform: `scale(${0.85 + 0.6 * nabiz})`,
              }}
            />
          )}
          <div
            style={{
              width: noktaCap,
              height: noktaCap,
              borderRadius: keskin ? 0 : noktaCap,
              background: vurgu,
              boxShadow: keskin ? undefined : `0 0 ${10 * u}px ${rgba(vurgu, 0.85)}`,
            }}
          />
        </div>

        <div
          style={{
            fontFamily: yigin(t.font.baslik),
            fontWeight: t.font.agirlik_baslik,
            fontSize: yaziBoy,
            lineHeight: 1.04,
            letterSpacing: `${Math.max(0.05, t.font.izleme)}em`,
            color: yuzeyYazi(t, "rozet"),
            whiteSpace: "nowrap",
            overflow: "hidden",
            textOverflow: "ellipsis",
            transform: `translateX(${icTakipX}px)`,
          }}
        >
          {harf(t, param.metin)}
        </div>

        <div style={parlamaStil(t, a.parlama, u)} />
      </div>
    </div>
  );
};

export default tanimla({ meta: meta as never, sema, Bilesen: Cip });
