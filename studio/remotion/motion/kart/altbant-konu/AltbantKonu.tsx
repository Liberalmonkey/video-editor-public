// Konu alt bandı: küçük konu etiketi ve 2 satıra saran büyük metin; ağırlıklı yaylı kayma, parlak üst vurgu ve kademeli maske açılışı.
import React from "react";
import { interpolate } from "remotion";
import { z } from "zod";
import {
  harf, karistir, parlamaStil, rgba, titremeOpaklik, titresim,
  useTema, yigin, yuzeyStil, yuzeyTipi, yuzeyYazi,
} from "../../../tema";
import { useAkis } from "../../cekirdek/zaman";
import { tanimla, type BilesenProps } from "../../cekirdek/tipler";
import meta from "./meta.json";

export const sema = z.strictObject({
  konu: z.string().max(24).default("ANA FİKİR").describe("Üstteki küçük konu veya başlık etiketi"),
  metin: z.string().max(84).default("İyi kurgu izleyiciye hissettirmeden akar").describe("İki satıra sarabilen büyük konu metni"),
  renk: z.enum(["vurgu", "ikincil", "olumlu", "olumsuz", "yazi"]).default("vurgu").describe("Üst vurgu çizgisinin tema rengi adı"),
});

const KIS = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

const AltbantKonu: React.FC<BilesenProps<z.infer<typeof sema>>> = ({ param, kutu, sureKare, u }) => {
  const t = useTema();
  const a = useAkis(sureKare, meta.giris_sn, meta.cikis_sn);
  const tip = yuzeyTipi(t);
  const vurgu = t.renk[param.renk];
  const keskin = tip === "piksel" || tip === "brutalist";

  // Anticipation: a.ters ile aşağı gerilim, ardından ağırlıklı yayla yukarı yükselme + tutmada ince nefes.
  const h = a.hazirlikKare;
  const anaGir = Math.max(4, a.girKare - h);
  const kartYay = a.yay(0, "agir");
  const onY = 12 * u * a.ters;
  const panelY = (1 - Math.min(1.03, kartYay)) * 40 * u + onY + a.cik * 32 * u + a.nefes * 1.5 * u;

  const cizgiGir = a.e.emphasis(interpolate(a.f, [h, h + Math.max(5, Math.round(anaGir * 0.72))], [0, 1], KIS));
  const konuGir = a.sirali(1, 2, "enter");
  const metinGir = a.sirali(2, 2, "enter");

  const cikBas = sureKare - a.cikKare;
  const metinCik = a.e.exit(interpolate(a.f, [cikBas, cikBas + Math.max(2, Math.round(a.cikKare * 0.7))], [0, 1], KIS));

  const blur = a.hizBulaniklik > 0.08 ? `blur(${(a.hizBulaniklik * u).toFixed(2)}px)` : undefined;
  const tit = titremeOpaklik(t, a.f);
  const titr = titresim(t, a.f, u);
  const yuzey = yuzeyStil(t, u, "kart");

  const konuBoy = Math.max(28 * u, Math.round(kutu.h * 0.13));
  const metinBoy = Math.max(42 * u, Math.round(kutu.h * 0.195));
  const cizgiEn = Math.round(32 * u);

  return (
    <div
      style={{
        width: kutu.w,
        height: kutu.h,
        display: "flex",
        alignItems: "center",
      }}
    >
      <div
        style={{
          ...yuzey,
          position: "relative",
          overflow: "hidden",
          width: "100%",
          padding: `${Math.round(18 * u)}px ${Math.round(28 * u)}px`,
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          gap: Math.round(10 * u),
          boxSizing: "border-box",
          transform: `translateY(${panelY}px) ${titr}`,
          opacity: a.belir * (1 - a.cik) * tit,
          filter: blur,
        }}
      >
        <div
          style={{
            position: "absolute",
            top: 0,
            left: 0,
            right: 0,
            height: Math.max(2, Math.round(3 * u)),
            background: keskin
              ? vurgu
              : `linear-gradient(90deg, ${vurgu} 0%, ${rgba(vurgu, 0.35)} 50%, transparent 100%)`,
            transformOrigin: "left center",
            transform: `scaleX(${cizgiGir * (1 - metinCik)})`,
          }}
        />

        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: Math.round(11 * u),
          }}
        >
          <div
            style={{
              width: cizgiEn,
              height: Math.max(4, Math.round(5 * u)),
              borderRadius: keskin ? 0 : Math.round(4 * u),
              background: keskin
                ? vurgu
                : `linear-gradient(90deg, ${vurgu} 0%, ${karistir(vurgu, t.renk.ikincil, 0.35)} 100%)`,
              boxShadow: keskin ? undefined : `0 0 ${10 * u}px ${rgba(vurgu, 0.6)}`,
              transformOrigin: "left center",
              transform: `scaleX(${cizgiGir})`,
              opacity: 1 - metinCik,
              flexShrink: 0,
            }}
          />
          <div
            style={{
              fontFamily: yigin(t.font.baslik),
              fontWeight: t.font.agirlik_baslik,
              fontSize: konuBoy,
              lineHeight: 1.08,
              letterSpacing: `${Math.max(0.07, t.font.izleme)}em`,
              color: vurgu,
              opacity: Math.min(1, konuGir * 2.5) * (1 - metinCik),
              transform: `translateX(${(1 - konuGir) * -18 * u}px)`,
              whiteSpace: "nowrap",
              overflow: "hidden",
              textOverflow: "ellipsis",
            }}
          >
            {harf(t, param.konu)}
          </div>
        </div>

        <div style={{ overflow: "hidden" }}>
          <div
            style={{
              fontFamily: yigin(t.font.baslik),
              fontWeight: t.font.agirlik_baslik,
              fontSize: metinBoy,
              lineHeight: 1.18,
              letterSpacing: `${t.font.izleme}em`,
              color: yuzeyYazi(t, "kart"),
              display: "-webkit-box",
              WebkitLineClamp: 2,
              WebkitBoxOrient: "vertical",
              overflow: "hidden",
              transform: `translateY(${(1 - metinGir) * 52 * u + metinCik * 26 * u}px)`,
              opacity: Math.min(1, metinGir * 2.4) * (1 - metinCik),
            }}
          >
            {harf(t, param.metin)}
          </div>
        </div>

        <div style={parlamaStil(t, a.parlama, u)} />
      </div>
    </div>
  );
};

export default tanimla({ meta: meta as never, sema, Bilesen: AltbantKonu });
