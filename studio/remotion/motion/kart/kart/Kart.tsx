// Bilgi kartı: perspektif eğimden yayla düzleşerek açılır, üst gradyan vurgu şeridi çizilir, başlık ve 1-2 madde sıralı oturur + parlama.
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
  baslik: z.string().max(42).default("İki Temel Kural").describe("Kartın ana başlığı"),
  madde1: z.string().max(64).default("İlk iki saniyede merak uyandır").describe("Birinci özet maddesi"),
  madde2: z.string().max(64).default("Her kesimde tek net fikir ver").describe("İsteğe bağlı ikinci özet maddesi; boşsa gizlenir"),
  renk: z.enum(["vurgu", "ikincil", "olumlu", "olumsuz", "yazi"]).default("vurgu").describe("Üst şerit ve madde imi tema rengi adı"),
});

const KIS = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

const Kart: React.FC<BilesenProps<z.infer<typeof sema>>> = ({ param, kutu, sureKare, u }) => {
  const t = useTema();
  const a = useAkis(sureKare, meta.giris_sn, meta.cikis_sn);
  const tip = yuzeyTipi(t);
  const vurgu = t.renk[param.renk];
  const keskin = tip === "piksel" || tip === "brutalist";

  // Anticipation: a.ters ile aşağı eğik hazırlık, ardından yayla düzleşerek yükselme + tutmada ince nefes.
  const h = a.hazirlikKare;
  const anaGir = Math.max(4, a.girKare - h);
  const kartYay = a.yay(0, "ipeksi");
  const onY = 12 * u * a.ters;
  const egim = (1 - Math.min(1.04, kartYay)) * 11 + 3 * a.ters - a.cik * 8;
  const kartY = (1 - Math.min(1.04, kartYay)) * 32 * u + onY + a.cik * 28 * u + a.nefes * 1.8 * u;
  const ustCizgi = a.e.emphasis(interpolate(a.f, [h, h + Math.max(5, Math.round(anaGir * 0.85))], [0, 1], KIS));
  const baslikGir = a.sirali(1, 2, "enter");

  const maddeler = [param.madde1, param.madde2].map((m) => m.trim()).filter((m) => m.length > 0);
  const baslikBoy = Math.max(44 * u, Math.round(kutu.h * 0.145));
  const maddeBoy = Math.max(30 * u, Math.round(kutu.h * 0.098));
  const imCap = Math.round(12 * u);

  const blur = a.hizBulaniklik > 0.08 ? `blur(${(a.hizBulaniklik * u).toFixed(2)}px)` : undefined;
  const tit = titremeOpaklik(t, a.f);
  const titr = titresim(t, a.f, u);
  const yuzey = yuzeyStil(t, u, "kart");
  const anaYazi = yuzeyYazi(t, "kart");

  return (
    <div
      style={{
        width: kutu.w,
        height: kutu.h,
        display: "flex",
        alignItems: "center",
        perspective: Math.round(900 * u),
      }}
    >
      <div
        style={{
          ...yuzey,
          position: "relative",
          width: "100%",
          overflow: "hidden",
          padding: `${Math.round(24 * u)}px ${Math.round(30 * u)}px`,
          display: "flex",
          flexDirection: "column",
          gap: Math.round(14 * u),
          boxSizing: "border-box",
          transformOrigin: "center bottom",
          transform: `translateY(${kartY}px) rotateX(${egim}deg) ${titr}`,
          opacity: a.belir * (1 - a.cik) * tit,
          filter: blur,
        }}
      >
        <div
          style={{
            position: "absolute",
            left: 0,
            top: 0,
            right: 0,
            height: Math.max(4, Math.round(5 * u)),
            background: keskin
              ? vurgu
              : `linear-gradient(90deg, ${vurgu} 0%, ${karistir(vurgu, t.renk.ikincil, 0.4)} 68%, transparent 100%)`,
            boxShadow: keskin ? undefined : `0 0 ${12 * u}px ${rgba(vurgu, 0.55)}`,
            transformOrigin: "left center",
            transform: `scaleX(${ustCizgi * (1 - a.cik)})`,
          }}
        />

        <div style={{ overflow: "hidden", paddingTop: Math.round(4 * u) }}>
          <div
            style={{
              fontFamily: yigin(t.font.baslik),
              fontWeight: t.font.agirlik_baslik,
              fontSize: baslikBoy,
              lineHeight: 1.12,
              letterSpacing: `${t.font.izleme}em`,
              color: anaYazi,
              whiteSpace: "nowrap",
              overflow: "hidden",
              textOverflow: "ellipsis",
              transform: `translateY(${(1 - baslikGir) * 105}%)`,
              opacity: Math.min(1, baslikGir * 2.5),
            }}
          >
            {harf(t, param.baslik)}
          </div>
        </div>

        <div
          style={{
            width: "100%",
            height: Math.max(1, Math.round(1.5 * u)),
            background: keskin
              ? rgba(t.renk.yazi, 0.25)
              : `linear-gradient(90deg, ${rgba(t.renk.yazi, 0.24)} 0%, ${rgba(t.renk.yazi, 0.08)} 70%, transparent 100%)`,
            transformOrigin: "left center",
            transform: `scaleX(${baslikGir})`,
          }}
        />

        <div style={{ display: "flex", flexDirection: "column", gap: Math.round(13 * u) }}>
          {maddeler.map((m, i) => {
            const p = a.sirali(i + 2, 3, "enter");
            const imYay = a.yay((i + 1) * 3 + 2, "keskin");
            return (
              <div
                key={i}
                style={{
                  display: "flex",
                  alignItems: "flex-start",
                  gap: Math.round(15 * u),
                  opacity: Math.min(1, p * 2.4),
                  transform: `translateX(${(1 - p) * -26 * u}px)`,
                }}
              >
                <div
                  style={{
                    width: imCap,
                    height: imCap,
                    marginTop: Math.round(maddeBoy * 0.36),
                    borderRadius: keskin ? 0 : imCap,
                    background: vurgu,
                    boxShadow: keskin ? undefined : `0 0 ${10 * u}px ${rgba(vurgu, 0.65)}`,
                    flexShrink: 0,
                    transform: `scale(${Math.max(0, imYay)})`,
                  }}
                />
                <div
                  style={{
                    fontFamily: yigin(t.font.govde),
                    fontWeight: t.font.agirlik_govde,
                    fontSize: maddeBoy,
                    lineHeight: 1.24,
                    color: rgba(anaYazi, 0.92),
                    display: "-webkit-box",
                    WebkitLineClamp: 2,
                    WebkitBoxOrient: "vertical",
                    overflow: "hidden",
                  }}
                >
                  {harf(t, m)}
                </div>
              </div>
            );
          })}
        </div>

        <div style={parlamaStil(t, a.parlama, u)} />
      </div>
    </div>
  );
};

export default tanimla({ meta: meta as never, sema, Bilesen: Kart });
