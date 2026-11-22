// Vurgu söz: iki aşamalı sinematik fikir dönüşümü — eski kavram belirip üstü çizilerek soluklaşır, yeni kavram elastik yayla vurgulu karta kilitlenir.
import React from "react";
import { interpolate } from "remotion";
import { z } from "zod";
import {
  harf, koyuMu, parlamaStil, rgba, titremeOpaklik, titresim,
  useTema, yigin, yuzeyStil, yuzeyTipi, yuzeyYazi, type TemaToken,
} from "../../../tema";
import { cizgiOfset, useAkis } from "../../cekirdek/zaman";
import { tanimla, type BilesenProps } from "../../cekirdek/tipler";
import meta from "./meta.json";

export const sema = z.strictObject({
  eski: z.string().max(24).default("ÜRÜN").describe("Üstü çizilip geçilecek eski kavram"),
  yeni: z.string().max(24).default("HİKÂYE").describe("Öne çıkacak yeni ana kavram"),
  etiket: z.string().max(28).default("ÖNEMLİ OLAN").describe("Üstteki küçük bağlam etiketi; boşsa gizlenir"),
  renk: z.enum(["vurgu", "ikincil", "olumlu", "olumsuz", "yazi"]).default("vurgu").describe("Yeni kavram kartının tema rengi adı"),
  odakKarart: z.boolean().default(true).describe("Arka planı yumuşak karartarak tezatı öne çıkarır"),
});

const KIS = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

const kontrastYazi = (t: TemaToken, arkaHex: string) => {
  const acik = koyuMu(t.renk.zemin) ? t.renk.yazi : t.renk.zemin;
  const koyu = koyuMu(t.renk.zemin) ? t.renk.zemin : t.renk.yazi;
  return koyuMu(arkaHex) ? acik : koyu;
};

const VurguSoz: React.FC<BilesenProps<z.infer<typeof sema>>> = ({ param, kutu, sureKare, u }) => {
  const t = useTema();
  const a = useAkis(sureKare, meta.giris_sn, meta.cikis_sn);
  const tip = yuzeyTipi(t);
  const vurgu = t.renk[param.renk];
  const tRenk: TemaToken = param.renk === "vurgu" ? t : { ...t, renk: { ...t.renk, vurgu } };
  const cizgiRenk = param.renk === "olumsuz" ? t.renk.yazi : t.renk.olumsuz;
  const etiketVar = param.etiket.trim().length > 0;

  // Aşama 1: kart + etiket + eski kavram girer.
  const kartYay = a.yay(0, "ipeksi");
  const etiketGir = a.sirali(0, 2, "enter");
  const eskiYay = a.yay(2, "keskin");

  // Aşama 2: dönüşüm karesinde eski üstü çizilir ve soluklaşır; yeni elastik yayla fırlayıp kilitlenir.
  const donusumKare = Math.max(
    a.girKare + 3,
    Math.min(Math.max(a.girKare + 3, sureKare - a.cikKare - 14), Math.round(sureKare * 0.34)),
  );
  const cizgiIler = a.e.emphasis(interpolate(a.f, [donusumKare, donusumKare + 9], [0, 1], KIS));
  const eskiSoluk = a.e.settle(interpolate(a.f, [donusumKare + 2, donusumKare + 12], [0, 1], KIS));
  const yeniGecikme = Math.max(2, donusumKare - a.hazirlikKare + 2);
  const yeniYay = a.yay(yeniGecikme, "elastik");
  const yeniOp = a.e.enter(interpolate(a.f, [donusumKare + 1, donusumKare + 7], [0, 1], KIS));
  const yeniParlama = a.e.settle(
    interpolate(a.f, [donusumKare + 8, donusumKare + 8 + Math.max(8, Math.round(0.55 * a.fps))], [0, 1], KIS),
  );

  const kartY = 12 * u * a.ters + (1 - kartYay) * 30 * u - a.cik * 26 * u + a.nefes * 1.6 * u;
  const blur = a.hizBulaniklik > 0.08 ? `blur(${(a.hizBulaniklik * u).toFixed(2)}px)` : undefined;
  const tit = titremeOpaklik(t, a.f);
  const titr = titresim(t, a.f, u);
  const kartYuzey = yuzeyStil(t, u, "kart");
  const yeniYuzey = yuzeyStil(tRenk, u, "vurgulu");
  const yeniMetinRenk = tip === "neon" ? t.renk.yazi : kontrastYazi(t, vurgu);
  const keskin = tip === "piksel" || tip === "brutalist";

  const etiketBoy = Math.max(28 * u, Math.round(kutu.h * 0.1));
  const eskiBoy = Math.max(38 * u, Math.round(kutu.h * (param.eski.length > 16 ? 0.145 : 0.175)));
  const yeniBoy = Math.max(46 * u, Math.round(kutu.h * (param.yeni.length > 14 ? 0.185 : 0.225)));

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
          ...kartYuzey,
          position: "relative",
          overflow: "hidden",
          width: "100%",
          padding: `${Math.round(18 * u)}px ${Math.round(28 * u)}px ${Math.round(22 * u)}px`,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: Math.round(10 * u),
          boxSizing: "border-box",
          transform: `translateY(${kartY}px) scale(${(0.94 + 0.06 * kartYay) * (1 - 0.04 * a.cik)}) ${titr}`,
          opacity: a.belir * (1 - a.cik) * tit,
          filter: blur,
        }}
      >
        {etiketVar && (
          <div style={{ overflow: "hidden", maxWidth: "96%" }}>
            <div
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: Math.round(10 * u),
                fontFamily: yigin(t.font.govde),
                fontWeight: Math.max(600, t.font.agirlik_govde),
                fontSize: etiketBoy,
                lineHeight: 1.08,
                letterSpacing: `${Math.max(0.08, t.font.izleme)}em`,
                color: t.renk.soluk,
                transform: `translateY(${(1 - etiketGir) * 90}%)`,
                opacity: Math.min(1, etiketGir * 2.2),
              }}
            >
              <span
                style={{
                  width: Math.round(16 * u),
                  height: Math.max(2, Math.round(2.5 * u)),
                  borderRadius: keskin ? 0 : Math.round(2 * u),
                  background: rgba(vurgu, 0.7),
                }}
              />
              <span>{harf(t, param.etiket)}</span>
              <span
                style={{
                  width: Math.round(16 * u),
                  height: Math.max(2, Math.round(2.5 * u)),
                  borderRadius: keskin ? 0 : Math.round(2 * u),
                  background: rgba(vurgu, 0.7),
                }}
              />
            </div>
          </div>
        )}

        <div style={{ position: "relative", display: "inline-flex", alignItems: "center", justifyContent: "center", maxWidth: "96%" }}>
          <div style={{ overflow: "hidden", padding: `${Math.round(2 * u)}px ${Math.round(10 * u)}px` }}>
            <div
              style={{
                fontFamily: yigin(t.font.baslik),
                fontWeight: t.font.agirlik_baslik,
                fontSize: eskiBoy,
                lineHeight: 1.08,
                letterSpacing: `${t.font.izleme}em`,
                color: yuzeyYazi(t, "kart"),
                whiteSpace: "nowrap",
                overflow: "hidden",
                textOverflow: "ellipsis",
                transform: `translateY(${(1 - Math.min(1, eskiYay)) * 105}%) scale(${1 - 0.06 * eskiSoluk})`,
                opacity: Math.min(1, eskiYay * 2.2) * (1 - 0.56 * eskiSoluk),
              }}
            >
              {harf(t, param.eski)}
            </div>
          </div>

          <svg
            viewBox="0 0 200 28"
            preserveAspectRatio="none"
            style={{
              position: "absolute",
              left: Math.round(-6 * u),
              right: Math.round(-6 * u),
              top: "50%",
              width: `calc(100% + ${Math.round(12 * u)}px)`,
              height: Math.round(24 * u),
              transform: "translateY(-50%)",
              overflow: "visible",
              pointerEvents: "none",
            }}
          >
            <path
              d="M 4 19 Q 102 10 196 11"
              pathLength={1}
              fill="none"
              stroke={cizgiRenk}
              strokeWidth={Math.max(4, Math.round(5.5 * u))}
              vectorEffect="non-scaling-stroke"
              strokeLinecap={keskin ? "square" : "round"}
              strokeDasharray="1 2"
              strokeDashoffset={cizgiOfset(1, cizgiIler)}
              style={{
                filter: keskin ? undefined : `drop-shadow(0 0 ${8 * u}px ${rgba(cizgiRenk, 0.7)})`,
              }}
            />
          </svg>
        </div>

        <div style={{ overflow: "hidden", maxWidth: "100%", padding: `${Math.round(4 * u)}px ${Math.round(8 * u)}px` }}>
          <div
            style={{
              ...yeniYuzey,
              position: "relative",
              overflow: "hidden",
              display: "inline-flex",
              alignItems: "center",
              justifyContent: "center",
              padding: `${Math.round(10 * u)}px ${Math.round(30 * u)}px`,
              transform: `translateY(${(1 - Math.min(1.06, yeniYay)) * 96}%) scale(${(0.86 + 0.14 * yeniYay) * (1 + 0.006 * a.nefes)})`,
              opacity: yeniOp,
            }}
          >
            <div
              style={{
                fontFamily: yigin(t.font.baslik),
                fontWeight: t.font.agirlik_baslik,
                fontSize: yeniBoy,
                lineHeight: 1.04,
                letterSpacing: `${t.font.izleme}em`,
                color: yeniMetinRenk,
                whiteSpace: "nowrap",
              }}
            >
              {harf(t, param.yeni)}
            </div>
            <div style={parlamaStil(tRenk, yeniParlama, u)} />
          </div>
        </div>

        <div style={parlamaStil(t, a.parlama, u)} />
      </div>
    </div>
  );
};

export default tanimla({ meta: meta as never, sema, Bilesen: VurguSoz });
