// Durum rozeti: canlı nabız atan durum noktası + yön oku SVG + etiket/değer + seviyeye kadar dolan ince gösterge barı + parlama.
import React from "react";
import { interpolate } from "remotion";
import { z } from "zod";
import {
  harf, karistir, koyuMu, parlamaStil, rgba, titremeOpaklik, titresim,
  useTema, yigin, yuzeyStil, yuzeyTipi, yuzeyYazi,
} from "../../../tema";
import { cizgiOfset, useAkis } from "../../cekirdek/zaman";
import { tanimla, type BilesenProps } from "../../cekirdek/tipler";
import meta from "./meta.json";

export const sema = z.strictObject({
  etiket: z.string().max(20).default("İZLENME").describe("Metrik veya durum etiketi"),
  deger: z.string().max(20).default("DÜŞÜK").describe("Sonuç veya durum değeri"),
  yon: z.enum(["yukari", "asagi", "yatay"]).default("asagi").describe("Trend yönü oku"),
  seviye: z.number().min(0).max(100).default(25).describe("Alt gösterge çubuğunun doluluk yüzdesi (0-100)"),
  renk: z.enum(["vurgu", "ikincil", "olumlu", "olumsuz", "yazi"]).default("olumsuz").describe("Durum noktası, ok ve gösterge barı tema rengi adı"),
});

const KIS = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

const OK_YOLLARI: Record<"yukari" | "asagi" | "yatay", { govde: string; bas: string }> = {
  yukari: { govde: "M5 19 L19 5", bas: "M10 5 L19 5 L19 14" },
  asagi: { govde: "M5 5 L19 19", bas: "M19 10 L19 19 L10 19" },
  yatay: { govde: "M4 12 L20 12", bas: "M14 6 L20 12 L14 18" },
};

const DurumRozeti: React.FC<BilesenProps<z.infer<typeof sema>>> = ({ param, kutu, sureKare, u }) => {
  const t = useTema();
  const a = useAkis(sureKare, meta.giris_sn, meta.cikis_sn);
  const tip = yuzeyTipi(t);
  const vurgu = t.renk[param.renk];
  const keskin = tip === "piksel" || tip === "brutalist";

  // Kapsül girişi + içerik stagger + gösterge barı dolumu + nabız canlılığı.
  const kapsulYay = a.yay(0, "keskin");
  const etiketGir = a.sirali(1, 2, "enter");
  const degerGir = a.sirali(2, 2, "enter");
  const okCiz = a.e.emphasis(interpolate(a.f, [a.hazirlikKare + 2, a.girKare + 4], [0, 1], KIS));
  const barDol = Math.min(1, a.yay(4, "ipeksi")) * (param.seviye / 100);

  const kapsulY = 8 * u * a.ters + (1 - Math.min(1.06, kapsulYay)) * 26 * u + a.cik * 22 * u + a.nefes * 1.4 * u;
  const nabiz = 0.5 + 0.5 * a.nefes;
  const okNudge = a.nefes * 2.2 * u;
  const okKay =
    param.yon === "yukari"
      ? `translate(${okNudge * 0.6}px, ${-okNudge}px)`
      : param.yon === "asagi"
        ? `translate(${okNudge * 0.6}px, ${okNudge}px)`
        : `translateX(${okNudge}px)`;

  const blur = a.hizBulaniklik > 0.08 ? `blur(${(a.hizBulaniklik * u).toFixed(2)}px)` : undefined;
  const tit = titremeOpaklik(t, a.f);
  const titr = titresim(t, a.f, u);
  const yuzey = yuzeyStil(t, u, "rozet");
  const okYol = OK_YOLLARI[param.yon];

  const etiketBoy = Math.max(28 * u, Math.round(kutu.h * 0.195));
  const degerBoy = Math.max(32 * u, Math.round(kutu.h * 0.255));
  const ikonKutu = Math.round(Math.min(kutu.h * 0.54, 70 * u));
  const noktaCap = Math.round(13 * u);
  const barYuk = Math.max(5, Math.round(6.5 * u));

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
          width: "100%",
          padding: `${Math.round(14 * u)}px ${Math.round(36 * u)}px ${Math.round(14 * u)}px ${Math.round(20 * u)}px`,
          display: "flex",
          alignItems: "center",
          gap: Math.round(16 * u),
          boxSizing: "border-box",
          transform: `translateY(${kapsulY}px) scale(${0.94 + 0.06 * Math.min(1.04, kapsulYay)}) ${titr}`,
          opacity: a.belir * (1 - a.cik) * tit,
          filter: blur,
        }}
      >
        <div
          style={{
            position: "relative",
            width: ikonKutu,
            height: ikonKutu,
            borderRadius: keskin ? 0 : ikonKutu,
            background: rgba(vurgu, 0.16),
            border: `${Math.max(1.5, Math.round(2 * u))}px solid ${rgba(vurgu, 0.45)}`,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            flexShrink: 0,
          }}
        >
          <div
            style={{
              position: "absolute",
              top: Math.round(-2 * u),
              right: Math.round(-2 * u),
              width: noktaCap,
              height: noktaCap,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <div
              style={{
                position: "absolute",
                inset: Math.round(-4 * u),
                borderRadius: keskin ? 0 : noktaCap,
                background: rgba(vurgu, 0.32 * (1 - nabiz * 0.6)),
                transform: `scale(${0.85 + 0.65 * nabiz})`,
              }}
            />
            <div
              style={{
                width: noktaCap,
                height: noktaCap,
                borderRadius: keskin ? 0 : noktaCap,
                background: vurgu,
                boxShadow: keskin ? undefined : `0 0 ${8 * u}px ${rgba(vurgu, 0.85)}`,
              }}
            />
          </div>

          <svg
            viewBox="0 0 24 24"
            width={Math.round(ikonKutu * 0.56)}
            height={Math.round(ikonKutu * 0.56)}
            style={{ overflow: "visible", transform: okKay }}
          >
            <path
              d={okYol.govde}
              pathLength={1}
              fill="none"
              stroke={vurgu}
              strokeWidth={3}
              strokeLinecap={keskin ? "square" : "round"}
              strokeDasharray="1 2"
              strokeDashoffset={cizgiOfset(1, okCiz)}
            />
            <path
              d={okYol.bas}
              pathLength={1}
              fill="none"
              stroke={vurgu}
              strokeWidth={3}
              strokeLinecap={keskin ? "square" : "round"}
              strokeLinejoin={keskin ? "miter" : "round"}
              strokeDasharray="1 2"
              strokeDashoffset={cizgiOfset(1, Math.max(0, (okCiz - 0.35) / 0.65))}
            />
          </svg>
        </div>

        <div
          style={{
            flex: 1,
            minWidth: 0,
            display: "flex",
            flexDirection: "column",
            justifyContent: "center",
            gap: Math.round(5 * u),
          }}
        >
          <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", gap: Math.round(12 * u) }}>
            <div style={{ overflow: "hidden", minWidth: 0 }}>
              <div
                style={{
                  fontFamily: yigin(t.font.govde),
                  fontWeight: Math.max(600, t.font.agirlik_govde),
                  fontSize: etiketBoy,
                  lineHeight: 1.05,
                  letterSpacing: `${Math.max(0.05, t.font.izleme)}em`,
                  color: karistir(t.renk.yazi, t.renk.soluk, 0.4),
                  whiteSpace: "nowrap",
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  transform: `translateY(${(1 - etiketGir) * 90}%)`,
                  opacity: Math.min(1, etiketGir * 2.4),
                }}
              >
                {harf(t, param.etiket)}
              </div>
            </div>
          </div>

          <div style={{ overflow: "hidden" }}>
            <div
              style={{
                fontFamily: yigin(t.font.baslik),
                fontWeight: t.font.agirlik_baslik,
                fontSize: degerBoy,
                lineHeight: 1.06,
                letterSpacing: `${t.font.izleme}em`,
                color: yuzeyYazi(t, "rozet"),
                whiteSpace: "nowrap",
                overflow: "hidden",
                textOverflow: "ellipsis",
                transform: `translateY(${(1 - degerGir) * 100}%)`,
                opacity: Math.min(1, degerGir * 2.4),
              }}
            >
              <span style={{ color: koyuMu(t.renk.zemin) ? karistir(vurgu, t.renk.yazi, 0.36) : vurgu }}>{harf(t, param.deger)}</span>
            </div>
          </div>

          <div
            style={{
              position: "relative",
              width: "100%",
              height: barYuk,
              borderRadius: keskin ? 0 : barYuk,
              background: rgba(t.renk.yazi, 0.14),
              overflow: "hidden",
              marginTop: Math.round(3 * u),
            }}
          >
            <div
              style={{
                position: "relative",
                width: `${Math.max(0, Math.min(100, barDol * 100))}%`,
                height: "100%",
                borderRadius: keskin ? 0 : barYuk,
                background: keskin
                  ? vurgu
                  : `linear-gradient(90deg, ${rgba(vurgu, 0.7)} 0%, ${vurgu} 75%, ${karistir(vurgu, t.renk.yazi, 0.35)} 100%)`,
                boxShadow: keskin ? undefined : `0 0 ${10 * u}px ${rgba(vurgu, 0.7)}`,
              }}
            />
          </div>
        </div>

        <div style={parlamaStil(t, a.parlama, u)} />
      </div>
    </div>
  );
};

export default tanimla({ meta: meta as never, sema, Bilesen: DurumRozeti });
