// Çizgi grafik: yüzey malzemesi + parlama, gradyan trend çizgisi, çizim ucunda parlayan nokta ve kademeli yay açılışıyla akar.
import React from "react";
import { interpolate } from "remotion";
import { z } from "zod";
import { golge, harf, karistir, parlamaStil, rakamFontu, rgba, ton, useTema, yigin, yuzeyStil } from "../../../tema";
import { cizgiOfset, useAkis } from "../../cekirdek/zaman";
import { tanimla, type BilesenProps } from "../../cekirdek/tipler";
import meta from "./meta.json";

export const sema = z.strictObject({
  baslik: z.string().max(38).default("Haftalık İzlenme İvmesi").describe("Grafiğin üst başlığı"),
  birim: z.string().max(8).default("K").describe("Son değerin sonundaki birim"),
  noktalar: z
    .array(z.number())
    .min(2)
    .max(8)
    .default([12, 18, 16, 28, 35, 54])
    .describe("2 ile 8 arası sıradüzenli sayısal veri noktaları"),
  etiketler: z
    .array(z.string().max(10))
    .min(2)
    .max(8)
    .default(["H1", "H2", "H3", "H4", "H5", "H6"])
    .describe("Yatay eksen kısa etiketleri"),
  renk: z.enum(["vurgu", "ikincil", "olumlu", "olumsuz", "yazi"]).default("vurgu").describe("Çizgi ve son nokta tema rengi adı"),
});

const KIS = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

const Cizgi: React.FC<BilesenProps<z.infer<typeof sema>>> = ({ param, kutu, sureKare, u }) => {
  const t = useTema();
  const a = useAkis(sureKare, meta.giris_sn, meta.cikis_sn);
  const g = golge(t, u);
  const vurgu = t.renk[param.renk];
  const yuzey = yuzeyStil(t, u, "kart");
  const gradId = React.useId().replace(/[^a-zA-Z0-9_-]/g, "");

  const noktalar = param.noktalar;
  const n = noktalar.length;
  const minD = Math.min(...noktalar);
  const maxD = Math.max(...noktalar);
  const duzMu = maxD - minD < 1e-6;
  const aralik = duzMu ? 1 : maxD - minD;

  const padX = Math.round(24 * u);
  const padY = Math.round(18 * u);
  const svgW = Math.max(220 * u, kutu.w - padX * 2);
  const svgH = Math.max(92 * u, Math.round(kutu.h * 0.44));
  const icSol = Math.round(24 * u);
  const icSag = svgW - Math.round(24 * u);
  const icUst = Math.round(16 * u);
  const icAlt = svgH - Math.round(14 * u);
  const cizimW = Math.max(10, icSag - icSol);
  const cizimH = Math.max(10, icAlt - icUst);

  const koord = noktalar.map((d, i) => {
    const x = icSol + (cizimW * i) / (n - 1);
    const norm = duzMu ? 0.5 : (d - minD) / aralik;
    const y = icAlt - norm * cizimH;
    return { x, y, d };
  });

  const kum: number[] = [0];
  let toplamUzunluk = 0;
  for (let i = 1; i < koord.length; i++) {
    toplamUzunluk += Math.hypot(koord[i].x - koord[i - 1].x, koord[i].y - koord[i - 1].y);
    kum.push(toplamUzunluk);
  }
  const guvenliUzunluk = Math.max(1, toplamUzunluk);
  const kumOran = kum.map((k) => k / guvenliUzunluk);

  const yol = koord.map((p, i) => `${i === 0 ? "M" : "L"} ${p.x.toFixed(1)} ${p.y.toFixed(1)}`).join(" ");
  const alanYol = `${yol} L ${koord[n - 1].x.toFixed(1)} ${icAlt.toFixed(1)} L ${koord[0].x.toFixed(1)} ${icAlt.toFixed(1)} Z`;

  const tersX = -10 * u * a.ters;
  const girX = (1 - a.gir) * -24 * u;
  const cikX = a.cik * 24 * u;
  const blur = a.hizBulaniklik > 0.08 ? `blur(${(a.hizBulaniklik * 0.45 * u).toFixed(2)}px)` : undefined;

  const cizBas = a.hazirlikKare + 1;
  const cizBit = Math.max(cizBas + 8, Math.min(sureKare - a.cikKare - 6, Math.round(sureKare * 0.55)));
  const cizIlerle = a.e.enter(interpolate(a.f, [cizBas, cizBit], [0, 1], KIS));
  const cizEfektif = Math.min(1, 0.04 * a.belir + 0.96 * cizIlerle) * (1 - a.cik);

  const sonYay = a.yay(Math.max(0, cizBit - a.hazirlikKare), "elastik");
  const sonVurgu = a.vurgu(cizBit, Math.max(4, Math.round(0.36 * a.fps)));
  const yankiYaricap = (8 + 22 * sonVurgu) * u;
  const yankiOp = (1 - sonVurgu) * (cizIlerle > 0.96 ? 0.85 : 0) * (1 - a.cik);
  const sonAtim = Math.sin(Math.PI * Math.min(1, Math.max(0, sonVurgu)));

  // Çizim ucunun anlık koordinatı (parlayan hareketli baş nokta)
  let anlikDeger = noktalar[0];
  let ucX = koord[0].x;
  let ucY = koord[0].y;
  if (cizIlerle >= 1) {
    anlikDeger = noktalar[n - 1];
    ucX = koord[n - 1].x;
    ucY = koord[n - 1].y;
  } else if (cizIlerle > 0) {
    for (let i = 1; i < n; i++) {
      if (cizIlerle <= kumOran[i] || i === n - 1) {
        const aralikOran = Math.max(1e-6, kumOran[i] - kumOran[i - 1]);
        const seg = Math.max(0, Math.min(1, (cizIlerle - kumOran[i - 1]) / aralikOran));
        anlikDeger = noktalar[i - 1] + (noktalar[i] - noktalar[i - 1]) * seg;
        ucX = koord[i - 1].x + (koord[i].x - koord[i - 1].x) * seg;
        ucY = koord[i - 1].y + (koord[i].y - koord[i - 1].y) * seg;
        break;
      }
    }
  }

  const ondalikVar = noktalar.some((d) => Math.abs(d - Math.round(d)) > 1e-4);
  const bicimliDeger = ondalikVar
    ? anlikDeger.toLocaleString("tr-TR", { minimumFractionDigits: 1, maximumFractionDigits: 1 })
    : Math.round(anlikDeger).toLocaleString("tr-TR");
  const birimTemiz = param.birim.trim();
  const onekBirimiMi = birimTemiz === "%" || birimTemiz === "₺" || birimTemiz === "$" || birimTemiz === "€";
  const heroMetin = onekBirimiMi ? `${param.birim}${bicimliDeger}` : `${bicimliDeger}${param.birim}`;

  const baslikBoy = Math.max(28 * u, Math.round(kutu.h * 0.092));
  const heroSayiBoy = Math.max(64 * u, Math.round(kutu.h * 0.19));
  const etiketBoy = Math.max(28 * u, Math.round(kutu.h * 0.08));
  const cizgiKalinlik = Math.max(4 * u, Math.round(5.5 * u));

  const adimGen = cizimW / Math.max(1, n - 1);
  const hepsiSigar = n <= 6 && adimGen >= etiketBoy * 1.9;
  const etiketIndeksleri = hepsiSigar
    ? koord.map((_, i) => i)
    : Array.from(new Set([0, Math.round((n - 1) / 3), Math.round(((n - 1) * 2) / 3), n - 1]));

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
          width: "100%",
          height: "100%",
          padding: `${padY}px ${padX}px`,
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          boxSizing: "border-box",
          overflow: "hidden",
          opacity: a.belir * (1 - a.cik),
          filter: blur,
          transform: `translateX(${tersX + girX + cikX}px) translateY(${a.nefes * -1.8 * u}px) scale(${1 + 0.005 * a.nefes})`,
        }}
      >
        <div style={parlamaStil(t, a.parlama, u)} />

        <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", gap: Math.round(14 * u) }}>
          <div
            style={{
              fontFamily: yigin(t.font.baslik),
              fontWeight: t.font.agirlik_baslik,
              fontSize: baslikBoy,
              lineHeight: 1.12,
              letterSpacing: `${t.font.izleme}em`,
              color: t.renk.yazi,
              textShadow: g.yazi,
              whiteSpace: "nowrap",
              overflow: "hidden",
              textOverflow: "ellipsis",
            }}
          >
            {harf(t, param.baslik)}
          </div>
          <div
            style={{
              fontFamily: rakamFontu(t),
              fontWeight: t.font.agirlik_baslik,
              fontSize: heroSayiBoy,
              lineHeight: 0.95,
              fontVariantNumeric: "tabular-nums",
              color: vurgu,
              textShadow: `0 0 ${16 * u}px ${rgba(vurgu, 0.42)}, ${g.yazi !== "none" ? g.yazi : `0 ${2 * u}px ${8 * u}px ${rgba(t.renk.ikon_kontur, 0.45)}`}`,
              whiteSpace: "nowrap",
              flexShrink: 0,
              transform: `scale(${1 + 0.08 * sonAtim + 0.03 * (sonYay > 0 ? sonYay - 1 : 0)})`,
              transformOrigin: "right center",
            }}
          >
            {heroMetin}
          </div>
        </div>

        <div style={{ position: "relative", width: svgW, height: svgH }}>
          <svg width={svgW} height={svgH} viewBox={`0 0 ${svgW} ${svgH}`} style={{ overflow: "visible", display: "block" }}>
            <defs>
              <linearGradient id={gradId} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={vurgu} stopOpacity={0.36} />
                <stop offset="100%" stopColor={vurgu} stopOpacity={0} />
              </linearGradient>
              <linearGradient id={`${gradId}-stroke`} x1="0" y1="0" x2="1" y2="0">
                <stop offset="0%" stopColor={karistir(vurgu, t.renk.ikincil, 0.4)} />
                <stop offset="65%" stopColor={vurgu} />
                <stop offset="100%" stopColor={ton(vurgu, -0.4)} />
              </linearGradient>
              <clipPath id={`${gradId}-clip`}>
                <rect x={0} y={0} width={icSol + cizimW * cizEfektif} height={svgH} />
              </clipPath>
            </defs>

            {[0, 0.5, 1].map((oran, idx) => {
              const y = icUst + cizimH * oran;
              return (
                <line
                  key={idx}
                  x1={icSol}
                  y1={y}
                  x2={icSag}
                  y2={y}
                  stroke={rgba(t.renk.yazi, idx === 2 ? 0.22 : 0.1)}
                  strokeWidth={Math.max(1, 1.5 * u)}
                  strokeDasharray={idx === 2 ? undefined : `${6 * u} ${6 * u}`}
                />
              );
            })}

            <path d={alanYol} fill={`url(#${gradId})`} clipPath={`url(#${gradId}-clip)`} />

            <path
              d={yol}
              fill="none"
              stroke={`url(#${gradId}-stroke)`}
              strokeWidth={cizgiKalinlik}
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeDasharray={guvenliUzunluk}
              strokeDashoffset={cizgiOfset(guvenliUzunluk, cizEfektif)}
              style={{ filter: `drop-shadow(0 0 ${(8 * u).toFixed(1)}px ${rgba(vurgu, 0.55)})` }}
            />

            {koord.map((p, i) => {
              const sonMu = i === n - 1;
              const uyan = a.e.emphasis(interpolate(cizIlerle, [Math.max(0, kumOran[i] - 0.05), Math.min(1, kumOran[i] + 0.04)], [0, 1], KIS));
              const r = sonMu ? Math.max(6 * u, 9.5 * u * Math.max(0.2, Math.min(1.12, sonYay))) : Math.max(3.5 * u, 5.5 * u * uyan);
              const op = (sonMu ? Math.max(uyan, sonYay > 0.05 ? 1 : 0) : uyan) * (1 - a.cik);
              return (
                <g key={i} opacity={op}>
                  {sonMu && (
                    <circle cx={p.x} cy={p.y} r={yankiYaricap} fill="none" stroke={ton(vurgu, -0.3)} strokeWidth={Math.max(2, 3 * u)} opacity={yankiOp} />
                  )}
                  <circle cx={p.x} cy={p.y} r={r} fill={sonMu ? vurgu : t.renk.zemin} stroke={sonMu ? ton(vurgu, -0.55) : vurgu} strokeWidth={Math.max(2, (sonMu ? 3 : 2.5) * u)} />
                </g>
              );
            })}

            {/* Çizim ucunda parlayan hareketli nokta */}
            <g opacity={a.belir * (1 - a.cik)}>
              <circle cx={ucX} cy={ucY} r={Math.max(8 * u, 11 * u)} fill={rgba(vurgu, 0.35)} />
              <circle cx={ucX} cy={ucY} r={Math.max(3.5 * u, 4.5 * u)} fill={ton(vurgu, -0.65)} />
            </g>
          </svg>
        </div>

        <div style={{ position: "relative", width: svgW, height: Math.round(etiketBoy * 1.32), flexShrink: 0 }}>
          {etiketIndeksleri.map((idx, sira) => {
            const etYay = a.yay(sira * 2 + 2, "keskin");
            const etGir = Math.max(0, Math.min(1, etYay));
            const sonMu = idx === n - 1;
            const metin = param.etiketler[idx] ?? `${idx + 1}`;
            return (
              <div
                key={idx}
                style={{
                  position: "absolute",
                  left: koord[idx].x,
                  top: 0,
                  fontFamily: yigin(t.font.govde),
                  fontWeight: sonMu ? t.font.agirlik_baslik : t.font.agirlik_govde,
                  fontSize: etiketBoy,
                  lineHeight: 1.1,
                  color: sonMu ? vurgu : t.renk.soluk,
                  whiteSpace: "nowrap",
                  opacity: 0.25 + 0.75 * etGir,
                  transform: `translate(-50%, ${(1 - etGir) * 10 * u}px)`,
                }}
              >
                {harf(t, metin)}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default tanimla({ meta: meta as never, sema, Bilesen: Cizgi });
