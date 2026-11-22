// Sayı sayacı: zemin varsa yüzey malzemesi + parlama, yoksa temiz stüdyo gölgesi, parlak gradyan vurgu çubuğu ve elastik hedef kilidiyle sayar.
import React from "react";
import { interpolate } from "remotion";
import { z } from "zod";
import { golge, harf, parlamaStil, rakamFontu, rgba, ton, useTema, yigin, yuzeyStil } from "../../../tema";
import { useAkis } from "../../cekirdek/zaman";
import { tanimla, type BilesenProps } from "../../cekirdek/tipler";
import meta from "./meta.json";

export const sema = z.strictObject({
  baslangic: z.number().default(0).describe("Saymaya başlanacak başlangıç değeri"),
  deger: z.number().default(84).describe("Ulaşılacak hedef sayısal değer"),
  onek: z.string().max(8).default("%").describe("Sayının önündeki simge ya da metin (örn. %, +, ₺, $)"),
  sonek: z.string().max(10).default("").describe("Sayının sonundaki birim ya da simge (örn. K, M, x, sn)"),
  ondalik: z.number().int().min(0).max(2).default(0).describe("Ondalık basamak sayısı (0-2)"),
  etiket: z.string().max(36).default("Tamamlama Oranı").describe("Sayının altındaki kısa açıklama etiketi"),
  zemin: z.boolean().default(false).describe("Arka planda tema paneli gösterilsin mi"),
  renk: z.enum(["vurgu", "ikincil", "olumlu", "olumsuz", "yazi"]).default("vurgu").describe("Sayı ve alt vurgu şeridi tema rengi adı"),
});

const KIS = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

const Sayac: React.FC<BilesenProps<z.infer<typeof sema>>> = ({ param, kutu, sureKare, u }) => {
  const t = useTema();
  const a = useAkis(sureKare, meta.giris_sn, meta.cikis_sn);
  const g = golge(t, u);
  const vurgu = t.renk[param.renk];
  const yuzey = param.zemin ? yuzeyStil(t, u, "kart") : {};

  const sayBas = a.hazirlikKare;
  const sayBit = Math.max(sayBas + 6, Math.min(sureKare - a.cikKare - 4, Math.round(sureKare * 0.52)));
  const sayIlerle = a.e.settle(interpolate(a.f, [sayBas, sayBit], [0, 1], KIS));
  const anlik = param.baslangic + (param.deger - param.baslangic) * sayIlerle;

  // Elastik hedef kilidi + alt şerit parlaması + etiket follow-through.
  const hedefYay = a.yay(Math.max(0, sayBit - a.hazirlikKare), "elastik");
  const atim = a.vurgu(sayBit, Math.max(4, Math.round(0.28 * a.fps)));
  const vuru = Math.sin(Math.PI * Math.min(1, Math.max(0, atim)));
  const etiketGir = a.sirali(2, 3, "enter");

  const tersY = 12 * u * a.ters;
  const girY = (1 - a.gir) * 32 * u;
  const cikY = a.cik * -26 * u;
  const sayiOlcek = (1 - 0.07 * a.ters) * (1 + 0.08 * vuru + 0.04 * (hedefYay > 0 ? hedefYay - 1 : 0)) * (1 + 0.008 * a.nefes) * (1 - 0.14 * a.cik);
  const seritGenislik = Math.max(0, Math.min(1.06, 0.22 * a.gir + 0.78 * Math.max(0, hedefYay))) * (1 - a.cik);
  const blur = a.hizBulaniklik > 0.08 ? `blur(${(a.hizBulaniklik * 0.45 * u).toFixed(2)}px)` : undefined;

  const bicimli = anlik.toLocaleString("tr-TR", {
    minimumFractionDigits: param.ondalik,
    maximumFractionDigits: param.ondalik,
  });
  const metin = `${param.onek}${bicimli}${param.sonek}`;
  const etiketTemiz = param.etiket.trim();

  const sayiBoy = Math.max(64 * u, Math.round(kutu.h * (etiketTemiz ? 0.44 : 0.58)));
  const etiketBoy = Math.max(28 * u, Math.round(kutu.h * 0.145));
  const konturRenk = t.altyazi.kontur_renk;
  const saydamYazi = t.altyazi.renk;
  const sayiRenk = param.zemin || param.renk !== "yazi" ? vurgu : saydamYazi;
  const etiketRenk = param.zemin ? t.renk.yazi : saydamYazi;
  const etiketAgirlik = param.zemin ? t.font.agirlik_govde : Math.max(600, t.font.agirlik_govde);

  // Kaba 8-yön kontur yerine çok katmanlı temiz stüdyo okunurluk gölgesi.
  const temizGolge = [
    `0 ${Math.round(2 * u)}px ${Math.round(5 * u)}px ${rgba(konturRenk, 0.82)}`,
    `0 ${Math.round(10 * u)}px ${Math.round(28 * u)}px ${rgba(konturRenk, 0.62)}`,
    `0 0 ${Math.round(2 * u)}px ${rgba(konturRenk, 0.85)}`,
  ].join(", ");
  const yaziGolge = param.zemin
    ? g.yazi
    : g.yazi !== "none"
      ? `${g.yazi}, ${temizGolge}`
      : temizGolge;

  return (
    <div
      style={{
        width: kutu.w,
        height: kutu.h,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        boxSizing: "border-box",
      }}
    >
      <div
        style={{
          ...yuzey,
          position: "relative",
          width: param.zemin ? "100%" : "auto",
          maxWidth: "100%",
          padding: param.zemin ? `${Math.round(20 * u)}px ${Math.round(28 * u)}px` : `${Math.round(8 * u)}px ${Math.round(16 * u)}px`,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: Math.round(10 * u),
          boxSizing: "border-box",
          overflow: param.zemin ? "hidden" : "visible",
          opacity: a.belir * (1 - a.cik),
          filter: blur,
          transform: `translateY(${tersY + girY + cikY + a.nefes * -2 * u}px)`,
        }}
      >
        {param.zemin && <div style={parlamaStil(t, a.parlama, u)} />}

        <div
          style={{
            fontFamily: rakamFontu(t),
            fontWeight: t.font.agirlik_baslik,
            fontSize: sayiBoy,
            lineHeight: 1.0,
            letterSpacing: `${t.font.izleme}em`,
            fontVariantNumeric: "tabular-nums",
            color: sayiRenk,
            textShadow: yaziGolge,
            whiteSpace: "nowrap",
            transform: `scale(${sayiOlcek})`,
            transformOrigin: "center bottom",
          }}
        >
          {metin}
        </div>

        <div
          style={{
            width: Math.min(kutu.w * 0.56, Math.round(240 * u)),
            height: Math.max(5 * u, Math.round(6 * u)),
            borderRadius: Math.round(999 * u),
            background: `linear-gradient(90deg, ${ton(vurgu, 0.12)}, ${vurgu} 50%, ${ton(vurgu, -0.45)})`,
            boxShadow: `0 0 ${16 * u}px ${rgba(vurgu, 0.58)}, 0 ${2 * u}px ${8 * u}px ${rgba(konturRenk, 0.45)}`,
            transform: `scaleX(${seritGenislik})`,
            transformOrigin: "center center",
          }}
        />

        {etiketTemiz.length > 0 && (
          <div style={{ overflow: "hidden", maxWidth: "100%" }}>
            <div
              style={{
                padding: `${Math.round(4 * u)}px ${Math.round(8 * u)}px`,
                fontFamily: yigin(t.font.govde),
                fontWeight: etiketAgirlik,
                fontSize: etiketBoy,
                lineHeight: 1.18,
                color: etiketRenk,
                textShadow: yaziGolge,
                whiteSpace: "nowrap",
                overflow: "hidden",
                textOverflow: "ellipsis",
                opacity: 0.25 + 0.75 * etiketGir,
                transform: `translateY(${(1 - etiketGir) * 95}%)`,
              }}
            >
              {harf(t, etiketTemiz)}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default tanimla({ meta: meta as never, sema, Bilesen: Sayac });
