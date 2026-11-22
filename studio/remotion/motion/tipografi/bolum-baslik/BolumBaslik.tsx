// Bölüm başlığı: kompakt üst kapsül, yaylı numara rozeti, ince dikey ayraç, maskeden kayan keskin başlık ve specular parlama.
import React from "react";
import { z } from "zod";
import {
  harf, koyuMu, parlamaStil, rakamFontu, rgba, titremeOpaklik, titresim,
  ton, useTema, yigin, yuzeyStil, yuzeyTipi, yuzeyYazi, type TemaToken,
} from "../../../tema";
import { useAkis } from "../../cekirdek/zaman";
import { tanimla, type BilesenProps } from "../../cekirdek/tipler";
import meta from "./meta.json";

export const sema = z.strictObject({
  numara: z.string().max(6).default("01").describe("Bölüm numarası veya kısa kod"),
  baslik: z.string().max(32).default("KLASİK REKLAM").describe("Bölüm başlığı"),
  alt: z.string().max(36).default("").describe("İsteğe bağlı kısa alt açıklama; boşsa gizlenir"),
  renk: z.enum(["vurgu", "ikincil", "olumlu", "olumsuz", "yazi"]).default("vurgu").describe("Numara rozeti tema rengi adı"),
});

const kontrastYazi = (t: TemaToken, arkaHex: string) => {
  const acik = koyuMu(t.renk.zemin) ? t.renk.yazi : t.renk.zemin;
  const koyu = koyuMu(t.renk.zemin) ? t.renk.zemin : t.renk.yazi;
  return koyuMu(arkaHex) ? acik : koyu;
};

const BolumBaslik: React.FC<BilesenProps<z.infer<typeof sema>>> = ({ param, kutu, sureKare, u }) => {
  const t = useTema();
  const a = useAkis(sureKare, meta.giris_sn, meta.cikis_sn);
  const tip = yuzeyTipi(t);
  const vurgu = t.renk[param.renk];
  const altVar = param.alt.trim().length > 0;
  const numaraVar = param.numara.trim().length > 0;

  // Kapsül girişi: a.ters ile yukarı kısa hazırlık, sonra yaylı iniş + tutmada 1.5px nefes.
  const kapsulYay = a.yay(0, "ipeksi");
  const rozetYay = a.yay(1, "keskin");
  const ayracGir = a.sirali(1, 2, "enter");
  const baslikGir = a.sirali(2, 2, "enter");
  const altGir = a.sirali(3, 2, "settle");

  const kapsulY = -8 * u * a.ters + (1 - kapsulYay) * -26 * u - a.cik * 22 * u + a.nefes * 1.5 * u;
  const blur = a.hizBulaniklik > 0.08 ? `blur(${(a.hizBulaniklik * u).toFixed(2)}px)` : undefined;
  const tit = titremeOpaklik(t, a.f);
  const titr = titresim(t, a.f, u);
  const yuzey = yuzeyStil(t, u, "rozet");
  const keskin = tip === "piksel" || tip === "brutalist";

  const numaraBoy = Math.max(32 * u, Math.round(kutu.h * 0.3));
  const baslikBoy = Math.max(32 * u, Math.round(kutu.h * (altVar ? 0.27 : 0.33)));
  const altBoy = Math.max(28 * u, Math.round(kutu.h * 0.21));
  const rozetKose = keskin ? 0 : Math.min(999 * u, Math.max(10 * u, t.sekil.kose * u));

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
          padding: `${Math.round(12 * u)}px ${Math.round(24 * u)}px ${Math.round(12 * u)}px ${Math.round(numaraVar ? 12 * u : 24 * u)}px`,
          display: "inline-flex",
          alignItems: "center",
          gap: Math.round(16 * u),
          boxSizing: "border-box",
          transform: `translateY(${kapsulY}px) scale(${0.94 + 0.06 * kapsulYay}) ${titr}`,
          opacity: a.belir * (1 - a.cik) * tit,
          filter: blur,
        }}
      >
        {numaraVar && (
          <div
            style={{
              padding: `${Math.round(7 * u)}px ${Math.round(16 * u)}px`,
              borderRadius: rozetKose,
              background: keskin
                ? vurgu
                : `linear-gradient(145deg, ${ton(vurgu, -0.1)} 0%, ${ton(vurgu, 0.14)} 100%)`,
              boxShadow: keskin
                ? undefined
                : `inset 0 ${1 * u}px 0 ${rgba(t.renk.yazi, 0.28)}, 0 ${4 * u}px ${14 * u}px ${rgba(vurgu, 0.38)}`,
              color: kontrastYazi(t, vurgu),
              fontFamily: rakamFontu(t),
              fontWeight: t.font.agirlik_baslik,
              fontSize: numaraBoy,
              lineHeight: 1.02,
              fontVariantNumeric: "tabular-nums",
              letterSpacing: "0.02em",
              flexShrink: 0,
              transform: `scale(${Math.max(0.4, rozetYay)})`,
              opacity: Math.min(1, rozetYay * 1.6),
            }}
          >
            {harf(t, param.numara)}
          </div>
        )}

        {numaraVar && (
          <div
            style={{
              width: Math.max(1.5, Math.round(2 * u)),
              height: Math.round(Math.min(kutu.h * 0.44, 46 * u)),
              borderRadius: keskin ? 0 : Math.round(2 * u),
              background: rgba(t.renk.yazi, 0.22),
              flexShrink: 0,
              transformOrigin: "center center",
              transform: `scaleY(${ayracGir})`,
            }}
          />
        )}

        <div
          style={{
            minWidth: 0,
            display: "flex",
            flexDirection: "column",
            justifyContent: "center",
            gap: Math.round(2 * u),
          }}
        >
          <div style={{ overflow: "hidden" }}>
            <div
              style={{
                fontFamily: yigin(t.font.baslik),
                fontWeight: t.font.agirlik_baslik,
                fontSize: baslikBoy,
                lineHeight: 1.08,
                letterSpacing: `${Math.max(0.03, t.font.izleme)}em`,
                color: yuzeyYazi(t, "rozet"),
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

          {altVar && (
            <div style={{ overflow: "hidden" }}>
              <div
                style={{
                  fontFamily: yigin(t.font.govde),
                  fontWeight: t.font.agirlik_govde,
                  fontSize: altBoy,
                  lineHeight: 1.12,
                  color: t.renk.soluk,
                  whiteSpace: "nowrap",
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  transform: `translateY(${(1 - altGir) * 95}%)`,
                  opacity: Math.min(1, altGir * 2.2),
                }}
              >
                {harf(t, param.alt)}
              </div>
            </div>
          )}
        </div>

        <div style={parlamaStil(t, a.parlama, u)} />
      </div>
    </div>
  );
};

export default tanimla({ meta: meta as never, sema, Bilesen: BolumBaslik });
