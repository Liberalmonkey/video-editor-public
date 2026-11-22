// Yüzde halkası: yüzey malzemesi, gradyan yay dolgusu, parlayan uç noktası, temiz gölge ve elastik hedef kilidiyle dolar.
import React from "react";
import { interpolate } from "remotion";
import { z } from "zod";
import { golge, harf, karistir, parlamaStil, rakamFontu, rgba, ton, useTema, yigin, yuzeyStil } from "../../../tema";
import { cizgiOfset, useAkis } from "../../cekirdek/zaman";
import { tanimla, type BilesenProps } from "../../cekirdek/tipler";
import meta from "./meta.json";

export const sema = z.strictObject({
  yuzde: z.number().min(0).max(100).default(78).describe("Gösterilecek yüzde değeri (0-100)"),
  etiket: z.string().max(32).default("İzlenme Tutma").describe("Halkanın yanındaki ana etiket"),
  alt: z.string().max(42).default("İlk 30 saniye ortalaması").describe("İsteğe bağlı ikincil kısa açıklama"),
  zemin: z.boolean().default(false).describe("Arka planda tema paneli gösterilsin mi"),
  renk: z.enum(["vurgu", "ikincil", "olumlu", "olumsuz", "yazi"]).default("vurgu").describe("Dolu yay ve yüzde vurgu tema rengi adı"),
});

const KIS = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

const Halka: React.FC<BilesenProps<z.infer<typeof sema>>> = ({ param, kutu, sureKare, u }) => {
  const t = useTema();
  const a = useAkis(sureKare, meta.giris_sn, meta.cikis_sn);
  const gradId = `halka-g-${React.useId().replace(/[^a-zA-Z0-9_-]/g, "")}`;
  const g = golge(t, u);
  const vurgu = !param.zemin && param.renk === "yazi" ? t.altyazi.renk : t.renk[param.renk];
  const yuzey = param.zemin ? yuzeyStil(t, u, "kart") : {};

  const yayBas = a.hazirlikKare;
  const yayBit = Math.max(yayBas + 8, Math.min(sureKare - a.cikKare - 5, Math.round(sureKare * 0.54)));
  const ilerle = a.e.settle(interpolate(a.f, [yayBas, yayBit], [0, 1], KIS));
  const hedefOran = param.yuzde / 100;
  const anlikOran = Math.max(0, Math.min(1, hedefOran * ilerle));
  const anlikYuzde = Math.round(param.yuzde * ilerle);

  const kurAci = -16 * a.ters;
  const hedefVurgu = a.vurgu(yayBit, Math.max(4, Math.round(0.28 * a.fps)));
  const atim = Math.sin(Math.PI * Math.min(1, Math.max(0, hedefVurgu)));
  const girYay = a.yay(0, "ipeksi");
  const kilitYay = a.yay(Math.max(0, yayBit - a.hazirlikKare), "elastik");
  const halkaOlcek = (1 - 0.06 * a.ters) * (0.9 + 0.1 * Math.min(1.06, girYay)) * (1 + 0.012 * a.nefes) * (1 - 0.2 * a.cik);
  const blur = a.hizBulaniklik > 0.08 ? `blur(${(a.hizBulaniklik * 0.45 * u).toFixed(2)}px)` : undefined;

  const etiketTemiz = param.etiket.trim();
  const altTemiz = param.alt.trim();
  const metinVar = etiketTemiz.length > 0 || altTemiz.length > 0;
  const etiketGir = a.sirali(1, 3, "enter");
  const altGir = a.sirali(2, 3, "enter");

  const icPay = param.zemin ? Math.round(20 * u) : Math.round(8 * u);
  const cap = Math.max(170 * u, Math.min(kutu.h - icPay * 2, metinVar ? kutu.w * 0.42 : kutu.w * 0.86));
  const cizgi = Math.max(12 * u, Math.round(cap * 0.095));
  const r = Math.max(20, cap / 2 - cizgi);
  const cevre = 2 * Math.PI * r;
  const merkez = cap / 2;

  const ucAci = (-90 + anlikOran * 360) * (Math.PI / 180);
  const ucX = merkez + r * Math.cos(ucAci);
  const ucY = merkez + r * Math.sin(ucAci);

  const sayiBoy = Math.max(64 * u, Math.round(cap * 0.27));
  const etiketBoy = Math.max(32 * u, Math.round(kutu.h * 0.135));
  const altBoy = Math.max(28 * u, Math.round(kutu.h * 0.098));

  const konturRenk = t.altyazi.kontur_renk;
  const saydamYazi = t.altyazi.renk;
  const yaziRenk = param.zemin ? t.renk.yazi : saydamYazi;
  const altRenk = param.zemin ? t.renk.soluk : saydamYazi;
  const altAgirlik = param.zemin ? t.font.agirlik_govde : Math.max(600, t.font.agirlik_govde);
  const temizGolge = [
    `0 ${Math.round(2 * u)}px ${Math.round(5 * u)}px ${rgba(konturRenk, 0.82)}`,
    `0 ${Math.round(8 * u)}px ${Math.round(24 * u)}px ${rgba(konturRenk, 0.6)}`,
  ].join(", ");
  const yaziGolge = param.zemin ? g.yazi : g.yazi !== "none" ? `${g.yazi}, ${temizGolge}` : temizGolge;

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
          height: param.zemin ? "100%" : "auto",
          padding: `${icPay}px ${Math.round(24 * u)}px`,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          gap: Math.round(24 * u),
          boxSizing: "border-box",
          overflow: param.zemin ? "hidden" : "visible",
          opacity: a.belir * (1 - a.cik),
          filter: blur,
          transform: `translateY(${a.nefes * -2 * u}px)`,
        }}
      >
        {param.zemin && <div style={parlamaStil(t, a.parlama, u)} />}

        <div
          style={{
            position: "relative",
            width: cap,
            height: cap,
            flexShrink: 0,
            transform: `scale(${halkaOlcek})`,
          }}
        >
          <svg
            width={cap}
            height={cap}
            viewBox={`0 0 ${cap} ${cap}`}
            style={{
              overflow: "visible",
              filter: `${g.filtre !== "none" ? g.filtre : ""} drop-shadow(0 0 ${(10 * u).toFixed(1)}px ${rgba(vurgu, 0.42)})`.trim(),
              transform: `rotate(${kurAci}deg)`,
            }}
          >
            <defs>
              <linearGradient id={gradId} x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stopColor={ton(vurgu, -0.4)} />
                <stop offset="55%" stopColor={vurgu} />
                <stop offset="100%" stopColor={karistir(vurgu, t.renk.ikincil, 0.35)} />
              </linearGradient>
            </defs>

            {!param.zemin && (
              <circle cx={merkez} cy={merkez} r={r} fill="none" stroke={rgba(konturRenk, 0.55)} strokeWidth={cizgi + 4 * u} />
            )}
            <circle
              cx={merkez}
              cy={merkez}
              r={r}
              fill="none"
              stroke={param.zemin ? rgba(t.renk.yazi, 0.16) : rgba(saydamYazi, 0.24)}
              strokeWidth={cizgi}
            />
            <circle
              cx={merkez}
              cy={merkez}
              r={r}
              fill="none"
              stroke={`url(#${gradId})`}
              strokeWidth={cizgi}
              strokeLinecap="round"
              strokeDasharray={cevre}
              strokeDashoffset={cizgiOfset(cevre, (param.yuzde > 0 ? Math.max(0.015 * a.belir, anlikOran) : 0) * (1 - a.cik))}
              transform={`rotate(-90 ${merkez} ${merkez})`}
            />
            {anlikOran > 0.02 && (
              <g opacity={1 - a.cik}>
                <circle cx={ucX} cy={ucY} r={Math.max(8 * u, cizgi * 0.68)} fill={rgba(vurgu, 0.38)} />
                <circle cx={ucX} cy={ucY} r={Math.max(4 * u, cizgi * 0.32)} fill={ton(vurgu, -0.65)} />
              </g>
            )}
          </svg>

          <div
            style={{
              position: "absolute",
              inset: 0,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontFamily: rakamFontu(t),
              fontWeight: t.font.agirlik_baslik,
              fontSize: sayiBoy,
              lineHeight: 1,
              fontVariantNumeric: "tabular-nums",
              color: yaziRenk,
              textShadow: yaziGolge,
              transform: `scale(${1 + 0.08 * atim + 0.03 * (kilitYay > 0 ? kilitYay - 1 : 0)})`,
            }}
          >
            {`%${anlikYuzde}`}
          </div>
        </div>

        {metinVar && (
          <div style={{ display: "flex", flexDirection: "column", justifyContent: "center", gap: Math.round(6 * u), minWidth: 0, flex: 1 }}>
            {etiketTemiz.length > 0 && (
              <div style={{ overflow: "hidden" }}>
                <div
                  style={{
                    padding: `${Math.round(4 * u)}px ${Math.round(6 * u)}px`,
                    fontFamily: yigin(t.font.baslik),
                    fontWeight: t.font.agirlik_baslik,
                    fontSize: etiketBoy,
                    lineHeight: 1.12,
                    letterSpacing: `${t.font.izleme}em`,
                    color: yaziRenk,
                    textShadow: yaziGolge,
                    whiteSpace: "nowrap",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    opacity: 0.25 + 0.75 * etiketGir,
                    transform: `translateX(${(1 - etiketGir) * -28 * u}px)`,
                  }}
                >
                  {harf(t, etiketTemiz)}
                </div>
              </div>
            )}
            {altTemiz.length > 0 && (
              <div style={{ overflow: "hidden" }}>
                <div
                  style={{
                    padding: `${Math.round(4 * u)}px ${Math.round(6 * u)}px`,
                    fontFamily: yigin(t.font.govde),
                    fontWeight: altAgirlik,
                    fontSize: altBoy,
                    lineHeight: 1.2,
                    color: altRenk,
                    textShadow: yaziGolge,
                    whiteSpace: "nowrap",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    opacity: 0.25 + 0.75 * altGir,
                    transform: `translateX(${(1 - altGir) * -22 * u}px)`,
                  }}
                >
                  {harf(t, altTemiz)}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default tanimla({ meta: meta as never, sema, Bilesen: Halka });
