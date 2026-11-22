// Süreç adımları: yüzey malzemesi + parlama, gradyan bağlantı hattı, parlayan akış ucu ve kademeli yay düğümleriyle ilerler.
import React from "react";
import { interpolate } from "remotion";
import { z } from "zod";
import { golge, harf, karistir, koyuMu, parlamaStil, rakamFontu, rgba, ton, useTema, yigin, yuzeyStil } from "../../../tema";
import { cizgiOfset, useAkis } from "../../cekirdek/zaman";
import { tanimla, type BilesenProps } from "../../cekirdek/tipler";
import meta from "./meta.json";

export const sema = z.strictObject({
  baslik: z.string().max(36).default("Üretim Süreci").describe("Süreç şeridinin ortalanmış üst başlığı"),
  adimlar: z
    .array(z.string().max(16))
    .min(3)
    .max(5)
    .default(["Fikir", "Kurgu", "Yayın", "Büyüme"])
    .describe("3 ile 5 arası kısa adım etiketi"),
  etkin: z.number().int().min(0).max(4).default(1).describe("Etkin adımın sıfır tabanlı indeksi (0..adım sayısı-1)"),
  zemin: z.boolean().default(false).describe("Arka planda tema paneli gösterilsin mi (varsayılan saydam + temiz gölge)"),
  renk: z.enum(["vurgu", "ikincil", "olumlu", "olumsuz", "yazi"]).default("vurgu").describe("Etkin adım ve dolan bağlantı çizgisi tema rengi adı"),
});

const KIS = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

const Adimlar: React.FC<BilesenProps<z.infer<typeof sema>>> = ({ param, kutu, sureKare, u }) => {
  const t = useTema();
  const a = useAkis(sureKare, meta.giris_sn, meta.cikis_sn);
  const gradId = `adimlar-g-${React.useId().replace(/[^a-zA-Z0-9_-]/g, "")}`;
  const g = golge(t, u);
  const vurgu = !param.zemin && param.renk === "yazi" ? t.altyazi.renk : t.renk[param.renk];
  const yuzey = param.zemin ? yuzeyStil(t, u, "kart") : {};

  const liste = param.adimlar;
  const n = liste.length;
  const etkinIdx = Math.max(0, Math.min(n - 1, param.etkin));

  const panelX = -10 * u * a.ters + (1 - a.gir) * -26 * u + a.cik * 24 * u;
  const blur = a.hizBulaniklik > 0.08 ? `blur(${(a.hizBulaniklik * 0.45 * u).toFixed(2)}px)` : undefined;

  const hatBas = a.hazirlikKare + 3;
  const hatBit = Math.max(hatBas + 8, Math.min(sureKare - a.cikKare - 6, Math.round(sureKare * 0.54)));
  const hatIlerle = etkinIdx === 0 ? a.gir : a.e.enter(interpolate(a.f, [hatBas, hatBit], [0, 1], KIS));

  const etkinKare = etkinIdx === 0 ? a.hazirlikKare + 4 : hatBit;
  const etkinYay = a.yay(Math.max(0, etkinKare - a.hazirlikKare), "elastik");
  const etkinVurgu = a.vurgu(etkinKare, Math.max(4, Math.round(0.36 * a.fps)));
  const etkinAtim = Math.sin(Math.PI * Math.min(1, Math.max(0, etkinVurgu)));

  const padX = param.zemin ? Math.round(24 * u) : Math.round(12 * u);
  const padY = param.zemin ? Math.round(18 * u) : Math.round(8 * u);
  const baslikBoy = Math.max(32 * u, Math.round(kutu.h * 0.11));
  const rozetBoy = Math.max(28 * u, Math.round(kutu.h * 0.092));
  const etiketBoy = Math.max(28 * u, Math.round(kutu.h * 0.09));
  const dugumBoy = Math.max(28 * u, Math.round(kutu.h * 0.095));

  const icW = Math.max(220 * u, kutu.w - padX * 2);
  const dugumCap = Math.max(52 * u, Math.min(Math.round(kutu.h * 0.22), Math.round(icW / (n * 1.9))));
  const rayH = Math.round(dugumCap * 1.44);
  const rayY = Math.round(rayH / 2);
  const kenarPay = Math.round(icW / (n * 2));
  const xler = liste.map((_, i) => kenarPay + ((icW - kenarPay * 2) * i) / (n - 1));

  const toplamRay = Math.max(1, xler[n - 1] - xler[0]);
  const etkinRay = Math.max(0, xler[etkinIdx] - xler[0]);
  const doluOran = etkinRay > 0 ? hatIlerle : 0;
  const ucX = xler[0] + etkinRay * doluOran;

  const adimMetni = `${String(etkinIdx + 1).padStart(2, "0")}/${String(n).padStart(2, "0")}`;

  const konturRenk = t.altyazi.kontur_renk;
  const saydamYazi = t.altyazi.renk;
  const vurguUstYazi = koyuMu(vurgu) ? saydamYazi : konturRenk;
  const temizGolge = [
    `0 ${Math.round(2 * u)}px ${Math.round(5 * u)}px ${rgba(konturRenk, 0.82)}`,
    `0 ${Math.round(8 * u)}px ${Math.round(22 * u)}px ${rgba(konturRenk, 0.58)}`,
  ].join(", ");
  const yaziGolge = param.zemin ? g.yazi : g.yazi !== "none" ? `${g.yazi}, ${temizGolge}` : temizGolge;
  const rayKalinlik = Math.max(5 * u, Math.round(6 * u));

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
          height: param.zemin ? "100%" : "auto",
          padding: `${padY}px ${padX}px`,
          display: "flex",
          flexDirection: "column",
          justifyContent: param.zemin ? "space-between" : "center",
          gap: param.zemin ? Math.round(10 * u) : Math.round(14 * u),
          boxSizing: "border-box",
          overflow: param.zemin ? "hidden" : "visible",
          opacity: a.belir * (1 - a.cik),
          filter: blur,
          transform: `translateX(${panelX}px) translateY(${a.nefes * -1.8 * u}px)`,
        }}
      >
        {param.zemin && <div style={parlamaStil(t, a.parlama, u)} />}

        <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: Math.round(14 * u), maxWidth: "100%" }}>
          <div
            style={{
              ...yuzeyStil(t, u, "rozet"),
              position: "relative",
              overflow: "hidden",
              padding: `${Math.round(6 * u)}px ${Math.round(16 * u)}px`,
              background: `linear-gradient(135deg, ${ton(vurgu, -0.25)}, ${vurgu})`,
              border: `${Math.max(1.5, Math.round(2 * u))}px solid ${ton(vurgu, -0.45, 0.7)}`,
              boxShadow: `0 0 ${16 * u}px ${rgba(vurgu, 0.45)}, 0 ${4 * u}px ${12 * u}px ${rgba(konturRenk, 0.45)}`,
              fontFamily: rakamFontu(t),
              fontWeight: t.font.agirlik_baslik,
              fontSize: rozetBoy,
              lineHeight: 1,
              fontVariantNumeric: "tabular-nums",
              color: vurguUstYazi,
              whiteSpace: "nowrap",
              flexShrink: 0,
              transform: `scale(${1 + 0.08 * etkinAtim})`,
            }}
          >
            <div style={parlamaStil(t, a.parlama, u)} />
            {adimMetni}
          </div>

          <div
            style={{
              padding: `${Math.round(4 * u)}px ${Math.round(6 * u)}px`,
              fontFamily: yigin(t.font.baslik),
              fontWeight: t.font.agirlik_baslik,
              fontSize: baslikBoy,
              lineHeight: 1.12,
              letterSpacing: `${t.font.izleme}em`,
              color: param.zemin ? t.renk.yazi : saydamYazi,
              textShadow: yaziGolge,
              whiteSpace: "nowrap",
              overflow: "hidden",
              textOverflow: "ellipsis",
            }}
          >
            {harf(t, param.baslik)}
          </div>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: Math.round(8 * u) }}>
          <div style={{ position: "relative", width: icW, height: rayH }}>
            <svg width={icW} height={rayH} viewBox={`0 0 ${icW} ${rayH}`} style={{ overflow: "visible", display: "block" }}>
              <defs>
                <linearGradient id={gradId} x1="0" y1="0" x2="1" y2="0">
                  <stop offset="0%" stopColor={karistir(vurgu, t.renk.ikincil, 0.35)} />
                  <stop offset="60%" stopColor={vurgu} />
                  <stop offset="100%" stopColor={ton(vurgu, -0.4)} />
                </linearGradient>
                <linearGradient id={`${gradId}-node`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={ton(vurgu, -0.35)} />
                  <stop offset="100%" stopColor={vurgu} />
                </linearGradient>
              </defs>

              {!param.zemin && (
                <line
                  x1={xler[0]}
                  y1={rayY}
                  x2={xler[n - 1]}
                  y2={rayY}
                  stroke={rgba(konturRenk, 0.52)}
                  strokeWidth={rayKalinlik + 4 * u}
                  strokeLinecap="round"
                  strokeDasharray={toplamRay}
                  strokeDashoffset={cizgiOfset(toplamRay, a.gir * (1 - a.cik))}
                />
              )}

              <line
                x1={xler[0]}
                y1={rayY}
                x2={xler[n - 1]}
                y2={rayY}
                stroke={param.zemin ? rgba(t.renk.yazi, 0.18) : rgba(saydamYazi, 0.32)}
                strokeWidth={rayKalinlik}
                strokeLinecap="round"
                strokeDasharray={toplamRay}
                strokeDashoffset={cizgiOfset(toplamRay, a.gir * (1 - a.cik))}
              />

              {etkinRay > 0 && (
                <>
                  <line
                    x1={xler[0]}
                    y1={rayY}
                    x2={xler[etkinIdx]}
                    y2={rayY}
                    stroke={`url(#${gradId})`}
                    strokeWidth={rayKalinlik + 1.4 * u}
                    strokeLinecap="round"
                    strokeDasharray={etkinRay}
                    strokeDashoffset={cizgiOfset(etkinRay, doluOran * (1 - a.cik))}
                    style={{ filter: `drop-shadow(0 0 ${(8 * u).toFixed(1)}px ${rgba(vurgu, 0.55)})` }}
                  />
                  {/* Akış ucunda parlayan nokta */}
                  {doluOran > 0.03 && doluOran < 0.99 && (
                    <g opacity={1 - a.cik}>
                      <circle cx={ucX} cy={rayY} r={Math.max(8 * u, rayKalinlik * 1.6)} fill={rgba(vurgu, 0.4)} />
                      <circle cx={ucX} cy={rayY} r={Math.max(3.5 * u, rayKalinlik * 0.65)} fill={ton(vurgu, -0.65)} />
                    </g>
                  )}
                </>
              )}

              {liste.map((_, i) => {
                const cx = xler[i];
                const dugumYay = a.yay(i * 3, "keskin");
                const tamamlandiMi = i < etkinIdx;
                const etkinMi = i === etkinIdx;
                const ulasmaOrani = etkinIdx > 0 ? i / etkinIdx : 0;
                const hatUlasti = i === 0 || (etkinIdx > 0 && hatIlerle >= ulasmaOrani - 0.02);
                const doluMu = tamamlandiMi && hatUlasti;
                const aktifMi = etkinMi && (etkinIdx === 0 || hatIlerle >= 0.96);

                const yaricap = (dugumCap / 2) * (etkinMi ? 1.08 : 0.94);
                const olcek = (0.3 * a.belir * (1 - 0.1 * a.ters) + 0.7 * Math.max(0, dugumYay)) * (aktifMi ? 0.94 + 0.06 * Math.min(1.12, etkinYay) : 1);
                const nabizR = yaricap + 18 * u * etkinVurgu;
                const nabizOp = (1 - etkinVurgu) * (aktifMi ? 0.85 : 0);

                const dugumDolgu = aktifMi || doluMu ? `url(#${gradId}-node)` : param.zemin ? t.renk.zemin : rgba(konturRenk, 0.78);
                const dugumCizgi = aktifMi
                  ? ton(vurgu, -0.55)
                  : doluMu
                    ? vurgu
                    : param.zemin
                      ? rgba(t.renk.yazi, 0.28)
                      : rgba(saydamYazi, 0.6);
                const icMetinRenk = aktifMi || doluMu ? (param.zemin ? t.renk.zemin : vurguUstYazi) : param.zemin ? t.renk.soluk : saydamYazi;

                return (
                  <g
                    key={i}
                    transform={`translate(${cx}, ${rayY}) scale(${Math.max(0.01, olcek)})`}
                    style={{ filter: aktifMi ? `drop-shadow(0 0 ${(10 * u).toFixed(1)}px ${rgba(vurgu, 0.55)})` : undefined }}
                  >
                    {etkinMi && (
                      <circle cx={0} cy={0} r={nabizR} fill="none" stroke={ton(vurgu, -0.35)} strokeWidth={Math.max(2, 3 * u)} opacity={nabizOp} />
                    )}
                    <circle cx={0} cy={0} r={yaricap} fill={dugumDolgu} stroke={dugumCizgi} strokeWidth={Math.max(2.5 * u, (aktifMi ? 3.2 : 2.2) * u)} />
                    {doluMu ? (
                      <path
                        d={`M ${-yaricap * 0.36} ${0} L ${-yaricap * 0.08} ${yaricap * 0.28} L ${yaricap * 0.38} ${-yaricap * 0.26}`}
                        fill="none"
                        stroke={icMetinRenk}
                        strokeWidth={Math.max(3 * u, 4 * u)}
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    ) : (
                      <text
                        x={0}
                        y={0}
                        textAnchor="middle"
                        dominantBaseline="central"
                        fill={icMetinRenk}
                        style={{ fontFamily: rakamFontu(t), fontWeight: t.font.agirlik_baslik, fontSize: dugumBoy }}
                      >
                        {i + 1}
                      </text>
                    )}
                  </g>
                );
              })}
            </svg>
          </div>

          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            {liste.map((ad, i) => {
              const etGir = a.sirali(i, 3, "enter");
              const etkinMi = i === etkinIdx;
              const tamamMi = i < etkinIdx;
              const etkinHapi = !param.zemin && etkinMi;
              const etiketRenk = etkinHapi
                ? vurguUstYazi
                : etkinMi
                  ? vurgu
                  : param.zemin
                    ? tamamMi
                      ? t.renk.yazi
                      : t.renk.soluk
                    : saydamYazi;
              const etiketAgirlik = etkinMi ? t.font.agirlik_baslik : param.zemin ? t.font.agirlik_govde : Math.max(600, t.font.agirlik_govde);
              const etiketY = (1 - etGir) * 14 * u;
              const etiketOlcek = etkinHapi ? 1 + 0.05 * etkinAtim : 1;

              return (
                <div
                  key={i}
                  style={{
                    flex: 1,
                    minWidth: 0,
                    padding: `0 ${Math.round(4 * u)}px`,
                    boxSizing: "border-box",
                    display: "flex",
                    justifyContent: "center",
                    overflow: "visible",
                  }}
                >
                  <div
                    style={{
                      ...(etkinHapi ? yuzeyStil(t, u, "rozet") : {}),
                      position: "relative",
                      maxWidth: "100%",
                      boxSizing: "border-box",
                      padding: etkinHapi ? `${Math.round(5 * u)}px ${Math.round(14 * u)}px` : `${Math.round(5 * u)}px ${Math.round(8 * u)}px`,
                      background: etkinHapi ? `linear-gradient(135deg, ${ton(vurgu, -0.25)}, ${vurgu})` : "transparent",
                      border: etkinHapi ? `${Math.max(1.5, Math.round(1.8 * u))}px solid ${ton(vurgu, -0.45, 0.7)}` : undefined,
                      boxShadow: etkinHapi ? `0 0 ${14 * u}px ${rgba(vurgu, 0.45)}, 0 ${4 * u}px ${12 * u}px ${rgba(konturRenk, 0.45)}` : undefined,
                      fontFamily: yigin(t.font.govde),
                      fontWeight: etiketAgirlik,
                      fontSize: etiketBoy,
                      lineHeight: 1.15,
                      color: etiketRenk,
                      textShadow: etkinHapi ? "none" : yaziGolge,
                      whiteSpace: "nowrap",
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                      opacity: (etkinMi || tamamMi ? 1 : 0.9) * etGir,
                      transform: `translateY(${etiketY}px) scale(${etiketOlcek})`,
                    }}
                  >
                    {harf(t, ad)}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};

export default tanimla({ meta: meta as never, sema, Bilesen: Adimlar });
