// Blok alt bant: sol gradyan vurgu şeridi gerilip açılır, yüzey paneli soldan maskeyle genişler, etiket rozeti ve başlık kademeli oturur + parlama.
import React from "react";
import { interpolate } from "remotion";
import { z } from "zod";
import {
  harf, karistir, koyuMu, parlamaStil, rgba, titremeOpaklik, titresim,
  ton, useTema, yigin, yuzeyStil, yuzeyTipi, yuzeyYazi, type TemaToken,
} from "../../../tema";
import { useAkis } from "../../cekirdek/zaman";
import { tanimla, type BilesenProps } from "../../cekirdek/tipler";
import meta from "./meta.json";

export const sema = z.strictObject({
  etiket: z.string().max(24).default("BÖLÜM 01").describe("Üstteki küçük kategori veya bölüm etiketi"),
  baslik: z.string().max(48).default("Doğru Başlangıç").describe("Alt bandın ana başlığı"),
  renk: z.enum(["vurgu", "ikincil", "olumlu", "olumsuz", "yazi"]).default("vurgu").describe("Etiket ve sol şerit tema rengi"),
});

const KIS = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

const kontrastYazi = (t: TemaToken, arkaHex: string) => {
  const acik = koyuMu(t.renk.zemin) ? t.renk.yazi : t.renk.zemin;
  const koyu = koyuMu(t.renk.zemin) ? t.renk.zemin : t.renk.yazi;
  return koyuMu(arkaHex) ? acik : koyu;
};

const AltbantBlok: React.FC<BilesenProps<z.infer<typeof sema>>> = ({ param, kutu, sureKare, u }) => {
  const t = useTema();
  const a = useAkis(sureKare, meta.giris_sn, meta.cikis_sn);
  const tip = yuzeyTipi(t);
  const vurgu = t.renk[param.renk];
  const keskin = tip === "piksel" || tip === "brutalist";

  // Anticipation: sol şerit a.ters ile aşağı sıkışıp sola çekilir; hazirlikKare sonrası yukarı fırlayıp paneli sağa açar.
  const h = a.hazirlikKare;
  const anaGir = Math.max(4, a.girKare - h);
  const cubukGir = a.e.emphasis(interpolate(a.f, [h, h + Math.max(4, Math.round(anaGir * 0.55))], [0, 1], KIS));
  const panelGir = a.e.enter(interpolate(a.f, [h, a.girKare], [0, 1], KIS));
  const cipGir = a.sirali(1, 2, "enter");
  const cipYay = a.yay(2, "keskin");
  const baslikGir = a.sirali(2, 2, "enter");
  const onX = -10 * u * a.ters;

  // Ters sırada hızlı çıkış.
  const cikBas = sureKare - a.cikKare;
  const icCik = a.e.exit(interpolate(a.f, [cikBas, cikBas + Math.max(2, Math.round(a.cikKare * 0.65))], [0, 1], KIS));
  const panelCik = a.e.exit(interpolate(a.f, [cikBas + 1, sureKare], [0, 1], KIS));

  const cubukOlcek = Math.max(0, (0.32 * a.belir + 0.68 * cubukGir) * (1 - 0.35 * a.ters) * (1 - panelCik));
  const acilma = Math.max(0, Math.min(1, panelGir * (1 - panelCik)));

  const blur = a.hizBulaniklik > 0.08 ? `blur(${(a.hizBulaniklik * u).toFixed(2)}px)` : undefined;
  const tit = titremeOpaklik(t, a.f);
  const titr = titresim(t, a.f, u);
  const yuzey = yuzeyStil(t, u, "bant");
  const kose = typeof yuzey.borderRadius === "number" ? yuzey.borderRadius : t.sekil.kose * 0.6 * u;
  const cubukEn = Math.max(7, Math.round(9 * u));
  const etiketBoy = Math.max(28 * u, Math.round(kutu.h * 0.155));
  const baslikBoy = Math.max(42 * u, Math.round(kutu.h * 0.265));

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
          position: "relative",
          width: "100%",
          display: "flex",
          alignItems: "stretch",
          transform: `translate(${onX}px, ${a.nefes * 1.4 * u}px) ${titr}`,
          opacity: a.belir * (1 - panelCik) * tit,
          filter: blur,
        }}
      >
        <div
          style={{
            width: cubukEn,
            borderRadius: `${kose}px 0 0 ${kose}px`,
            background: keskin
              ? vurgu
              : `linear-gradient(180deg, ${vurgu} 0%, ${karistir(vurgu, t.renk.ikincil, 0.4)} 100%)`,
            boxShadow: keskin ? undefined : `0 0 ${14 * u}px ${rgba(vurgu, 0.55)}`,
            transformOrigin: "center bottom",
            transform: `scaleY(${cubukOlcek})`,
            flexShrink: 0,
            zIndex: 2,
          }}
        />

        <div
          style={{
            ...yuzey,
            position: "relative",
            overflow: "hidden",
            flex: 1,
            minWidth: 0,
            borderRadius: `0 ${kose}px ${kose}px 0`,
            borderLeft: "none",
            padding: `${Math.round(16 * u)}px ${Math.round(28 * u)}px`,
            clipPath: acilma < 0.995 ? `inset(0 ${((1 - acilma) * 100).toFixed(2)}% 0 0 round 0 ${kose}px ${kose}px 0)` : undefined,
            display: "flex",
            flexDirection: "column",
            justifyContent: "center",
            alignItems: "flex-start",
            gap: Math.round(9 * u),
            boxSizing: "border-box",
          }}
        >
          {param.etiket.trim().length > 0 && (
            <div
              style={{
                display: "inline-flex",
                alignItems: "center",
                padding: `${Math.round(6 * u)}px ${Math.round(15 * u)}px`,
                borderRadius: keskin ? 0 : Math.min(999 * u, Math.max(8 * u, kose * 0.75)),
                background: keskin
                  ? vurgu
                  : `linear-gradient(135deg, ${ton(vurgu, -0.08)} 0%, ${ton(vurgu, 0.14)} 100%)`,
                boxShadow: keskin
                  ? undefined
                  : `inset 0 ${1 * u}px 0 ${rgba(t.renk.yazi, 0.28)}, 0 ${4 * u}px ${12 * u}px ${rgba(vurgu, 0.32)}`,
                color: kontrastYazi(t, vurgu),
                fontFamily: yigin(t.font.baslik),
                fontWeight: t.font.agirlik_baslik,
                fontSize: etiketBoy,
                lineHeight: 1.05,
                letterSpacing: `${Math.max(0.05, t.font.izleme)}em`,
                transform: `translateX(${(1 - cipGir) * -26 * u + (1 - Math.min(1.04, cipYay)) * 6 * u - icCik * 18 * u}px)`,
                opacity: Math.min(1, cipGir * 2.5) * (1 - icCik),
              }}
            >
              {harf(t, param.etiket)}
            </div>
          )}

          <div style={{ width: "100%", overflow: "hidden" }}>
            <div
              style={{
                fontFamily: yigin(t.font.baslik),
                fontWeight: t.font.agirlik_baslik,
                fontSize: baslikBoy,
                lineHeight: 1.1,
                letterSpacing: `${t.font.izleme}em`,
                color: yuzeyYazi(t, "bant"),
                whiteSpace: "nowrap",
                overflow: "hidden",
                textOverflow: "ellipsis",
                transform: `translateY(${(1 - baslikGir) * 95 + icCik * 40}%)`,
                opacity: Math.min(1, baslikGir * 2.5) * (1 - icCik),
              }}
            >
              {harf(t, param.baslik)}
            </div>
          </div>

          <div style={parlamaStil(t, a.parlama, u)} />
        </div>
      </div>
    </div>
  );
};

export default tanimla({ meta: meta as never, sema, Bilesen: AltbantBlok });
