// Alıntı kartı: iki tırnak yolu çizilir, sol vurgu rayı iner, metin kelime kelime stagger maskesiyle açılır, yazar sonda oturur + parlama.
import React from "react";
import { interpolate } from "remotion";
import { z } from "zod";
import {
  harf, karistir, parlamaStil, rgba, titremeOpaklik, titresim,
  useTema, yigin, yuzeyStil, yuzeyTipi, yuzeyYazi,
} from "../../../tema";
import { cizgiOfset, useAkis } from "../../cekirdek/zaman";
import { tanimla, type BilesenProps } from "../../cekirdek/tipler";
import meta from "./meta.json";

export const sema = z.strictObject({
  metin: z.string().max(110).default("Sadelik, gereksiz olanı çıkarabilme cesaretidir.").describe("Alıntı veya vurgu cümlesi"),
  yazar: z.string().max(40).default("Editör Notu").describe("İsteğe bağlı kaynak veya söyleyen adı; boşsa gizlenir"),
  renk: z.enum(["vurgu", "ikincil", "olumlu", "olumsuz", "yazi"]).default("vurgu").describe("Tırnak işareti tema rengi adı"),
});

const KIS = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

// İki kavisli tırnak yolu (46x36 viewBox, özgün geometrik çizim).
const TIRNAK_SOL = "M18 8C10 10 6 16 6 24c0 4 3 7 7 7s7-3 7-7-3-6-6-6c-1 0-2 .2-3 .6 1-4 4-7 7-8.4";
const TIRNAK_SAG = "M38 8C30 10 26 16 26 24c0 4 3 7 7 7s7-3 7-7-3-6-6-6c-1 0-2 .2-3 .6 1-4 4-7 7-8.4";
const TIRNAK_UZ = 72;

const Alinti: React.FC<BilesenProps<z.infer<typeof sema>>> = ({ param, kutu, sureKare, u }) => {
  const t = useTema();
  const a = useAkis(sureKare, meta.giris_sn, meta.cikis_sn);
  const tip = yuzeyTipi(t);
  const vurgu = t.renk[param.renk];
  const keskin = tip === "piksel" || tip === "brutalist";

  // Anticipation: a.ters ile tırnak geriye dönerek hazırlanır, panel yayla yükselir, çizim hazirlikKare sonrası başlar.
  const h = a.hazirlikKare;
  const anaGir = Math.max(5, a.girKare - h);
  const kartYay = a.yay(0, "ipeksi");
  const rayIler = a.e.emphasis(interpolate(a.f, [h, h + Math.max(6, Math.round(anaGir * 0.85))], [0, 1], KIS));
  const tirnak1Ham = a.e.enter(interpolate(a.f, [h, h + 8], [0, 1], KIS));
  const tirnak2Ham = a.e.enter(interpolate(a.f, [h + 2, h + 10], [0, 1], KIS));
  const tirnak1 = 0.22 * a.belir + 0.78 * tirnak1Ham;
  const tirnak2 = 0.18 * a.belir + 0.82 * tirnak2Ham;
  const tirnakDolgu = a.e.settle(interpolate(a.f, [h + 6, h + 11], [0, 1], KIS));
  const tirnakOn = -6 * a.ters;

  const kelimeler = harf(t, param.metin).trim().split(/\s+/).filter(Boolean);
  const kelimeAdim = kelimeler.length > 1 ? Math.min(2.2, 8 / (kelimeler.length - 1)) : 0;
  const kelimeSure = Math.max(4, Math.round(anaGir * 0.6));

  const yazarBas = Math.round(h + 2 + Math.max(0, kelimeler.length - 1) * kelimeAdim + 3);
  const yazarGir = a.e.enter(interpolate(a.f, [yazarBas, yazarBas + 6], [0, 1], KIS));

  const kartY = 10 * u * a.ters + (1 - Math.min(1.04, kartYay)) * 28 * u - a.cik * 24 * u + a.nefes * 1.6 * u;
  const blur = a.hizBulaniklik > 0.08 ? `blur(${(a.hizBulaniklik * u).toFixed(2)}px)` : undefined;
  const tit = titremeOpaklik(t, a.f);
  const titr = titresim(t, a.f, u);
  const yuzey = yuzeyStil(t, u, "kart");
  const anaYazi = yuzeyYazi(t, "kart");

  const metinBoy = Math.max(42 * u, Math.round(kutu.h * 0.124));
  const yazarBoy = Math.max(28 * u, Math.round(kutu.h * 0.088));
  const tirnakW = Math.round(52 * u);
  const tirnakH = Math.round(38 * u);

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
          padding: `${Math.round(22 * u)}px ${Math.round(30 * u)}px ${Math.round(22 * u)}px ${Math.round(34 * u)}px`,
          display: "flex",
          flexDirection: "column",
          gap: Math.round(12 * u),
          boxSizing: "border-box",
          transform: `translateY(${kartY}px) scale(${0.96 + 0.04 * Math.min(1.04, kartYay)}) ${titr}`,
          opacity: a.belir * (1 - a.cik) * tit,
          filter: blur,
        }}
      >
        <div
          style={{
            position: "absolute",
            left: 0,
            top: Math.round(16 * u),
            bottom: Math.round(16 * u),
            width: Math.max(4, Math.round(5 * u)),
            borderRadius: keskin ? 0 : Math.round(4 * u),
            background: keskin
              ? vurgu
              : `linear-gradient(180deg, ${vurgu} 0%, ${rgba(vurgu, 0.25)} 100%)`,
            boxShadow: keskin ? undefined : `0 0 ${12 * u}px ${rgba(vurgu, 0.5)}`,
            transformOrigin: "center top",
            transform: `scaleY(${rayIler * (1 - a.cik)})`,
          }}
        />

        <svg
          viewBox="0 0 46 36"
          width={tirnakW}
          height={tirnakH}
          style={{
            overflow: "visible",
            transform: `rotate(${tirnakOn}deg)`,
            transformOrigin: "left top",
            filter: keskin ? undefined : `drop-shadow(0 0 ${8 * u}px ${rgba(vurgu, 0.45)})`,
          }}
        >
          <path
            d={TIRNAK_SOL}
            fill={rgba(vurgu, 0.22 * tirnakDolgu)}
            stroke={vurgu}
            strokeWidth={3.1}
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeDasharray={TIRNAK_UZ}
            strokeDashoffset={cizgiOfset(TIRNAK_UZ, tirnak1)}
          />
          <path
            d={TIRNAK_SAG}
            fill={rgba(vurgu, 0.22 * tirnakDolgu)}
            stroke={vurgu}
            strokeWidth={3.1}
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeDasharray={TIRNAK_UZ}
            strokeDashoffset={cizgiOfset(TIRNAK_UZ, tirnak2)}
          />
        </svg>

        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            columnGap: Math.round(metinBoy * 0.26),
            rowGap: Math.round(metinBoy * 0.12),
            fontFamily: yigin(t.font.baslik),
            fontWeight: t.font.agirlik_baslik,
            fontSize: metinBoy,
            lineHeight: 1.18,
            letterSpacing: `${t.font.izleme}em`,
            color: anaYazi,
          }}
        >
          {kelimeler.map((kelime, i) => {
            const bas = h + 2 + i * kelimeAdim;
            const p = a.e.enter(interpolate(a.f, [bas, bas + kelimeSure], [0, 1], KIS));
            return (
              <span key={i} style={{ display: "inline-block", overflow: "hidden", paddingBottom: Math.round(2 * u) }}>
                <span
                  style={{
                    display: "inline-block",
                    transform: `translateY(${(1 - p) * 112}%)`,
                    opacity: Math.min(1, p * 2.6),
                  }}
                >
                  {kelime}
                </span>
              </span>
            );
          })}
        </div>

        {param.yazar.trim().length > 0 && (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "flex-end",
              gap: Math.round(12 * u),
              paddingTop: Math.round(4 * u),
              opacity: Math.min(1, yazarGir * 2.5),
            }}
          >
            <div
              style={{
                width: Math.round(36 * u),
                height: Math.max(2, Math.round(3 * u)),
                borderRadius: keskin ? 0 : Math.round(3 * u),
                background: keskin
                  ? vurgu
                  : `linear-gradient(90deg, ${rgba(vurgu, 0.25)} 0%, ${karistir(vurgu, t.renk.ikincil, 0.2)} 100%)`,
                transformOrigin: "right center",
                transform: `scaleX(${yazarGir})`,
              }}
            />
            <div
              style={{
                fontFamily: yigin(t.font.govde),
                fontWeight: Math.max(600, t.font.agirlik_govde),
                fontSize: yazarBoy,
                lineHeight: 1.1,
                letterSpacing: `${Math.max(0.03, t.font.izleme)}em`,
                color: t.renk.soluk,
                transform: `translateX(${(1 - yazarGir) * 16 * u}px)`,
              }}
            >
              {harf(t, param.yazar)}
            </div>
          </div>
        )}

        <div style={parlamaStil(t, a.parlama, u)} />
      </div>
    </div>
  );
};

export default tanimla({ meta: meta as never, sema, Bilesen: Alinti });
