// Çizgili alt bant: parlak gradyan vurgu çizgisi soldan uzar, başlık +2 karede maskeden yukarı çıkar, alt satır +4 karede aşağı açılır + parlama.
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
  baslik: z.string().max(48).default("Ahmet Yılmaz").describe("Ana başlık veya konuşmacı adı"),
  alt: z.string().max(64).default("Ürün Tasarımı Lideri").describe("İkincil alt satır veya unvan"),
  renk: z.enum(["vurgu", "ikincil", "olumlu", "olumsuz", "yazi"]).default("vurgu").describe("Vurgu çizgisinin tema rengi adı"),
});

const KIS = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

const AltbantCizgi: React.FC<BilesenProps<z.infer<typeof sema>>> = ({ param, kutu, sureKare, u }) => {
  const t = useTema();
  const a = useAkis(sureKare, meta.giris_sn, meta.cikis_sn);
  const tip = yuzeyTipi(t);
  const cizgiRenk = t.renk[param.renk];
  const keskin = tip === "piksel" || tip === "brutalist";

  // Anticipation: a.ters ile sola çekilme; ardından çizgi hazirlikKare'de, başlık +2, alt satır +4 karede maskeden açılır.
  const h = a.hazirlikKare;
  const anaGir = Math.max(4, a.girKare - h);
  const cizgiKare = Math.max(4, Math.round(anaGir * 0.72));
  const cizgiGir = a.e.enter(interpolate(a.f, [h, h + cizgiKare], [0, 1], KIS));
  const baslikGir = a.sirali(1, 2, "enter");
  const altGir = a.sirali(2, 2, "enter");
  const otur = a.yay(2, "keskin");
  const onX = -12 * u * a.ters;

  // Ters sırada hızlı çıkış: alt satır önce kapanır, sonra başlık, en son çizgi ve panel.
  const cikBas = sureKare - a.cikKare;
  const altCik = a.e.exit(interpolate(a.f, [cikBas, cikBas + Math.max(1, Math.round(a.cikKare * 0.65))], [0, 1], KIS));
  const baslikCikBas = cikBas + Math.round(a.cikKare * 0.15);
  const baslikCik = a.e.exit(interpolate(a.f, [baslikCikBas, Math.max(baslikCikBas + 1, sureKare)], [0, 1], KIS));
  const cizgiCikBas = cikBas + Math.round(a.cikKare * 0.3);
  const cizgiCik = a.e.exit(interpolate(a.f, [cizgiCikBas, Math.max(cizgiCikBas + 1, sureKare)], [0, 1], KIS));

  const cizgiAc = 0.16 * a.belir + 0.84 * cizgiGir;
  const cizgiOlcek = Math.max(0, Math.min(1, cizgiAc * (1 - cizgiCik)));
  const baslikY = (1 - baslikGir) * 115 + baslikCik * 115 + (1 - Math.min(1.04, otur)) * 4;
  const altY = -(1 - altGir) * 115 - altCik * 115;

  const baslikBoy = Math.max(42 * u, Math.round(kutu.h * 0.275));
  const altBoy = Math.max(28 * u, Math.round(kutu.h * 0.175));
  const cizgiYuk = Math.max(3, Math.round(4 * u));

  const blur = a.hizBulaniklik > 0.08 ? `blur(${(a.hizBulaniklik * u).toFixed(2)}px)` : undefined;
  const tit = titremeOpaklik(t, a.f);
  const titr = titresim(t, a.f, u);
  const yuzey = yuzeyStil(t, u, "bant");
  const kose = typeof yuzey.borderRadius === "number" ? yuzey.borderRadius : t.sekil.kose * 0.6 * u;
  const panelOp = a.belir * (1 - cizgiCik) * tit;

  return (
    <div
      style={{
        width: kutu.w,
        height: kutu.h,
        display: "flex",
        alignItems: "center",
        transform: `translate(${onX}px, ${a.nefes * 1.4 * u}px) ${titr}`,
      }}
    >
      <div
        style={{
          ...yuzey,
          position: "relative",
          overflow: "hidden",
          width: "100%",
          padding: `${Math.round(16 * u)}px ${Math.round(28 * u)}px`,
          opacity: panelOp,
          clipPath: cizgiOlcek < 0.995 ? `inset(0 ${((1 - cizgiOlcek) * 100).toFixed(2)}% 0 0 round ${kose}px)` : undefined,
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          gap: Math.round(8 * u),
          boxSizing: "border-box",
          filter: blur,
        }}
      >
        <div style={{ overflow: "hidden", paddingBottom: Math.round(2 * u) }}>
          <div
            style={{
              fontFamily: yigin(t.font.baslik),
              fontWeight: t.font.agirlik_baslik,
              fontSize: baslikBoy,
              lineHeight: 1.08,
              letterSpacing: `${t.font.izleme}em`,
              color: yuzeyYazi(t, "bant"),
              whiteSpace: "nowrap",
              overflow: "hidden",
              textOverflow: "ellipsis",
              transform: `translateY(${baslikY}%)`,
              opacity: Math.min(1, baslikGir * 2.5) * (1 - baslikCik),
            }}
          >
            {harf(t, param.baslik)}
          </div>
        </div>

        <div
          style={{
            width: "100%",
            height: cizgiYuk,
            borderRadius: keskin ? 0 : cizgiYuk,
            background: keskin
              ? cizgiRenk
              : `linear-gradient(90deg, ${cizgiRenk} 0%, ${karistir(cizgiRenk, t.renk.ikincil, 0.35)} 65%, ${rgba(cizgiRenk, 0.14)} 100%)`,
            boxShadow: keskin ? undefined : `0 0 ${10 * u}px ${rgba(cizgiRenk, 0.55)}`,
            transformOrigin: "left center",
            transform: `scaleX(${cizgiOlcek})`,
          }}
        />

        {param.alt.trim().length > 0 && (
          <div style={{ overflow: "hidden", paddingTop: Math.round(1 * u) }}>
            <div
              style={{
                fontFamily: yigin(t.font.govde),
                fontWeight: t.font.agirlik_govde,
                fontSize: altBoy,
                lineHeight: 1.18,
                letterSpacing: `${Math.max(0.01, t.font.izleme)}em`,
                color: t.renk.soluk,
                whiteSpace: "nowrap",
                overflow: "hidden",
                textOverflow: "ellipsis",
                transform: `translateY(${altY}%)`,
                opacity: Math.min(1, altGir * 2.5) * (1 - altCik),
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

export default tanimla({ meta: meta as never, sema, Bilesen: AltbantCizgi });
