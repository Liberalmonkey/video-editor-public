// Kinetik başlık: kelime kelime alt maskeden yayla fırlama, vurgu kelimesinde renk/glow + alt parlak çizgi, zarif yüzey plakası.
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
  metin: z.string().max(52).default("Böyle Yaparsan İzlenmez").describe("Ana kinetik başlık metni"),
  vurguKelime: z.string().max(20).default("İzlenmez").describe("Tema vurgu rengiyle patlayacak anahtar kelime"),
  altMetin: z.string().max(40).default("").describe("İsteğe bağlı kısa destekleyici alt satır; boşsa gizlenir"),
  renk: z.enum(["vurgu", "ikincil", "olumlu", "olumsuz", "yazi"]).default("vurgu").describe("Vurgu kelimesi ve çizgisinin tema rengi adı"),
  odakKarart: z.boolean().default(false).describe("Arka planı yumuşak karartarak başlığı öne çıkarır"),
});

const KIS = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const temizle = (s: string) => s.replace(/^[^\p{L}\p{N}]+|[^\p{L}\p{N}]+$/gu, "").toLocaleLowerCase("tr-TR");

const KinetikBaslik: React.FC<BilesenProps<z.infer<typeof sema>>> = ({ param, kutu, sureKare, u }) => {
  const t = useTema();
  const a = useAkis(sureKare, meta.giris_sn, meta.cikis_sn);
  const g = golge(t, u);
  const tip = yuzeyTipi(t);
  const koyu = koyuMu(t.renk.zemin);
  const vurgu = t.renk[param.renk];
  const anaYazi = yuzeyYazi(t, "kart");

  const kelimeler = harf(t, param.metin).trim().split(/\s+/).filter(Boolean);
  const aranan = temizle(param.vurguKelime.trim());
  const altVar = param.altMetin.trim().length > 0;

  // Anticipation + kartın yaylı yükselişi + tutmada ince nefes canlılığı.
  const kartYay = a.yay(0, "ipeksi");
  const kartY = 10 * u * a.ters + (1 - kartYay) * 28 * u - a.cik * 24 * u + a.nefes * 1.8 * u;
  const kartOlcek = (0.95 + 0.05 * kartYay) * (1 - 0.04 * a.cik) * (1 + 0.004 * a.nefes);
  const ustCizgi = a.e.emphasis(interpolate(a.f, [a.hazirlikKare, a.girKare + 3], [0, 1], KIS));
  const altGir = a.sirali(Math.min(5, kelimeler.length + 1), 2, "settle");

  const uzunluk = param.metin.trim().length;
  const oran = uzunluk > 36 ? 0.18 : uzunluk > 24 ? 0.22 : 0.265;
  const baslikBoy = Math.max(38 * u, Math.round(kutu.h * (altVar ? oran * 0.9 : oran)));
  const altBoy = Math.max(28 * u, Math.round(kutu.h * 0.125));

  const blur = a.hizBulaniklik > 0.08 ? `blur(${(a.hizBulaniklik * u).toFixed(2)}px)` : undefined;
  const tit = titremeOpaklik(t, a.f);
  const titr = titresim(t, a.f, u);
  const yuzey = yuzeyStil(t, u, "kart");
  const keskin = tip === "piksel" || tip === "brutalist";

  // Okunurluk için yumuşak halo/gölge (kaba meme stroke yok).
  const metinGolge = keskin
    ? g.yazi
    : `0 ${3 * u}px ${14 * u}px ${rgba(t.renk.ikon_kontur, koyu ? 0.65 : 0.14)}`;
  const vurguGolge = keskin
    ? g.yazi
    : `0 0 ${18 * u}px ${rgba(vurgu, koyu ? 0.55 : 0.22)}, 0 ${3 * u}px ${14 * u}px ${rgba(t.renk.ikon_kontur, koyu ? 0.65 : 0.16)}`;

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
          width: "100%",
          padding: `${Math.round(20 * u)}px ${Math.round(30 * u)}px ${Math.round(22 * u)}px`,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: Math.round(10 * u),
          boxSizing: "border-box",
          transform: `translateY(${kartY}px) scale(${kartOlcek}) ${titr}`,
          opacity: a.belir * (1 - a.cik) * tit,
          filter: blur,
        }}
      >
        <div
          style={{
            position: "absolute",
            top: 0,
            left: "14%",
            right: "14%",
            height: Math.max(2, Math.round(3 * u)),
            borderRadius: Math.round(3 * u),
            background: keskin
              ? vurgu
              : `linear-gradient(90deg, transparent 0%, ${vurgu} 50%, transparent 100%)`,
            transform: `scaleX(${ustCizgi * (1 - a.cik)})`,
            opacity: 0.9,
          }}
        />

        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            justifyContent: "center",
            alignItems: "baseline",
            columnGap: Math.round(baslikBoy * 0.27),
            rowGap: Math.round(baslikBoy * 0.14),
            fontFamily: yigin(t.font.baslik),
            fontWeight: t.font.agirlik_baslik,
            fontSize: baslikBoy,
            lineHeight: 1.12,
            letterSpacing: `${t.font.izleme - 0.01}em`,
            textAlign: "center",
          }}
        >
          {kelimeler.map((kelime, i) => {
            const eslesti = aranan.length > 0 && temizle(kelime) === aranan;
            const sir = a.sirali(i, 2, "enter");
            const yay = a.yay(i * 2, eslesti ? "elastik" : "keskin");
            const karma = 0.45 * sir + 0.55 * Math.min(1.08, yay);
            const cizgiIler = eslesti
              ? a.e.emphasis(interpolate(a.f, [a.hazirlikKare + i * 2 + 2, a.hazirlikKare + i * 2 + 11], [0, 1], KIS))
              : 0;
            const kelimeOlcek = eslesti ? 0.94 + 0.09 * Math.min(1.12, yay) : 1;

            return (
              <span
                key={i}
                style={{
                  position: "relative",
                  display: "inline-flex",
                  flexDirection: "column",
                  alignItems: "center",
                  overflow: "hidden",
                  padding: `${Math.round(3 * u)}px ${Math.round(3 * u)}px ${Math.round(eslesti ? 8 * u : 4 * u)}px`,
                }}
              >
                <span
                  style={{
                    display: "inline-block",
                    color: eslesti ? (koyuMu(t.renk.zemin) ? karistir(vurgu, t.renk.yazi, 0.36) : vurgu) : anaYazi,
                    textShadow: eslesti ? vurguGolge : metinGolge,
                    transform: `translateY(${(1 - karma) * 112}%) scale(${kelimeOlcek})`,
                    opacity: Math.min(1, sir * 2.6),
                  }}
                >
                  {kelime}
                </span>
                {eslesti && (
                  <span
                    style={{
                      position: "absolute",
                      left: Math.round(2 * u),
                      right: Math.round(2 * u),
                      bottom: Math.round(1 * u),
                      height: Math.max(3, Math.round(5 * u)),
                      borderRadius: keskin ? 0 : Math.round(4 * u),
                      background: keskin
                        ? vurgu
                        : `linear-gradient(90deg, ${vurgu} 0%, ${karistir(vurgu, t.renk.ikincil, 0.45)} 100%)`,
                      boxShadow: keskin ? undefined : `0 0 ${12 * u}px ${rgba(vurgu, 0.72)}`,
                      transformOrigin: "left center",
                      transform: `scaleX(${cizgiIler * (1 - a.cik)})`,
                    }}
                  />
                )}
              </span>
            );
          })}
        </div>

        {altVar && (
          <div style={{ overflow: "hidden", maxWidth: "94%" }}>
            <div
              style={{
                fontFamily: yigin(t.font.govde),
                fontWeight: t.font.agirlik_govde,
                fontSize: altBoy,
                lineHeight: 1.2,
                letterSpacing: `${Math.max(0.02, t.font.izleme)}em`,
                color: t.renk.soluk,
                textAlign: "center",
                whiteSpace: "nowrap",
                overflow: "hidden",
                textOverflow: "ellipsis",
                transform: `translateY(${(1 - altGir) * 85}%)`,
                opacity: Math.min(1, altGir * 2.2),
              }}
            >
              {harf(t, param.altMetin)}
            </div>
          </div>
        )}

        <div style={parlamaStil(t, a.parlama, u)} />
      </div>
    </div>
  );
};

export default tanimla({ meta: meta as never, sema, Bilesen: KinetikBaslik });
