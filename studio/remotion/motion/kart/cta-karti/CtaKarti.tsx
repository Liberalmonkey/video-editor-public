// CTA kartı: frosted-glass / stilize eylem çağrısı kartı — üstte vurgulu rozet, maskeli başlık + alt çağrı, sağda nefes alan yön oku + parlama.
import React from "react";
import { interpolate } from "remotion";
import { z } from "zod";
import {
  harf, karistir, koyuMu, parlamaStil, rgba, titremeOpaklik, titresim,
  ton, useTema, yigin, yuzeyStil, yuzeyTipi, yuzeyYazi, type TemaToken,
} from "../../../tema";
import { cizgiOfset, useAkis } from "../../cekirdek/zaman";
import { tanimla, type BilesenProps } from "../../cekirdek/tipler";
import meta from "./meta.json";

export const sema = z.strictObject({
  baslik: z.string().max(38).default("Promptlar Açıklamada").describe("Ana eylem çağrısı başlığı"),
  alt: z.string().max(48).default("Merak ettiğini yoruma yaz").describe("Destekleyici ikinci satır çağrı; boşsa gizlenir"),
  rozet: z.string().max(18).default("AÇIKLAMA").describe("Üstteki vurgulu küçük rozet metni; boşsa gizlenir"),
  yon: z.enum(["asagi", "sag", "yok"]).default("asagi").describe("Sağdaki yön oku biçimi"),
  renk: z.enum(["vurgu", "ikincil", "olumlu", "olumsuz", "yazi"]).default("vurgu").describe("Rozet, vurgu çizgisi ve ok tema rengi adı"),
});

const KIS = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

const kontrastYazi = (t: TemaToken, arkaHex: string) => {
  const acik = koyuMu(t.renk.zemin) ? t.renk.yazi : t.renk.zemin;
  const koyu = koyuMu(t.renk.zemin) ? t.renk.zemin : t.renk.yazi;
  return koyuMu(arkaHex) ? acik : koyu;
};

const CtaKarti: React.FC<BilesenProps<z.infer<typeof sema>>> = ({ param, kutu, sureKare, u }) => {
  const t = useTema();
  const a = useAkis(sureKare, meta.giris_sn, meta.cikis_sn);
  const tip = yuzeyTipi(t);
  const vurgu = t.renk[param.renk];
  const keskin = tip === "piksel" || tip === "brutalist";
  const rozetVar = param.rozet.trim().length > 0;
  const altVar = param.alt.trim().length > 0;
  const okVar = param.yon !== "yok";

  // Kart yaylı girişi + sol vurgu hattı + rozet/metin stagger + sağ yön oku elastik oturması.
  const kartYay = a.yay(0, "ipeksi");
  const seritIler = a.e.emphasis(interpolate(a.f, [a.hazirlikKare, a.girKare + 2], [0, 1], KIS));
  const rozetYay = a.yay(1, "keskin");
  const baslikGir = a.sirali(1, 2, "enter");
  const altGir = a.sirali(2, 2, "enter");
  const okYay = a.yay(3, "elastik");
  const okCiz = a.e.emphasis(interpolate(a.f, [a.hazirlikKare + 3, a.girKare + 6], [0, 1], KIS));

  const kartY = 12 * u * a.ters + (1 - Math.min(1.04, kartYay)) * 34 * u + a.cik * 28 * u + a.nefes * 1.6 * u;
  const okNefes = a.nefes * 4.5 * u;
  const okKay = param.yon === "asagi" ? `translateY(${okNefes}px)` : `translateX(${okNefes}px)`;

  const blur = a.hizBulaniklik > 0.08 ? `blur(${(a.hizBulaniklik * u).toFixed(2)}px)` : undefined;
  const tit = titremeOpaklik(t, a.f);
  const titr = titresim(t, a.f, u);
  const yuzey = yuzeyStil(t, u, "kart");

  const rozetBoy = Math.max(28 * u, Math.round(kutu.h * 0.13));
  const baslikBoy = Math.max(38 * u, Math.round(kutu.h * 0.2));
  const altBoy = Math.max(28 * u, Math.round(kutu.h * 0.142));
  const okKutu = Math.round(Math.min(kutu.h * 0.44, 84 * u));
  const okIkon = Math.round(okKutu * 0.52);

  const okGovde = param.yon === "asagi" ? "M12 4 L12 19" : "M4 12 L19 12";
  const okBas = param.yon === "asagi" ? "M6 13.5 L12 19.5 L18 13.5" : "M13.5 6 L19.5 12 L13.5 18";

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
          padding: `${Math.round(18 * u)}px ${Math.round(26 * u)}px ${Math.round(18 * u)}px ${Math.round(30 * u)}px`,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: Math.round(20 * u),
          boxSizing: "border-box",
          transform: `translateY(${kartY}px) scale(${(0.95 + 0.05 * Math.min(1.04, kartYay)) * (1 - 0.03 * a.cik)}) ${titr}`,
          opacity: a.belir * (1 - a.cik) * tit,
          filter: blur,
        }}
      >
        <div
          style={{
            position: "absolute",
            left: 0,
            top: Math.round(14 * u),
            bottom: Math.round(14 * u),
            width: Math.max(4, Math.round(5.5 * u)),
            borderRadius: keskin ? 0 : Math.round(5 * u),
            background: keskin
              ? vurgu
              : `linear-gradient(180deg, ${vurgu} 0%, ${karistir(vurgu, t.renk.ikincil, 0.45)} 100%)`,
            boxShadow: keskin ? undefined : `0 0 ${14 * u}px ${rgba(vurgu, 0.65)}`,
            transformOrigin: "center top",
            transform: `scaleY(${seritIler * (1 - a.cik)})`,
          }}
        />

        <div
          style={{
            flex: 1,
            minWidth: 0,
            display: "flex",
            flexDirection: "column",
            alignItems: "flex-start",
            justifyContent: "center",
            gap: Math.round(7 * u),
          }}
        >
          {rozetVar && (
            <div
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: Math.round(8 * u),
                padding: `${Math.round(5 * u)}px ${Math.round(14 * u)}px`,
                borderRadius: keskin ? 0 : Math.min(999 * u, Math.max(8 * u, t.sekil.kose * 0.55 * u)),
                background: keskin
                  ? vurgu
                  : `linear-gradient(135deg, ${ton(vurgu, -0.08)} 0%, ${ton(vurgu, 0.14)} 100%)`,
                boxShadow: keskin
                  ? undefined
                  : `inset 0 ${1 * u}px 0 ${rgba(t.renk.yazi, 0.28)}, 0 ${4 * u}px ${12 * u}px ${rgba(vurgu, 0.35)}`,
                color: kontrastYazi(t, vurgu),
                fontFamily: yigin(t.font.baslik),
                fontWeight: t.font.agirlik_baslik,
                fontSize: rozetBoy,
                lineHeight: 1.05,
                letterSpacing: `${Math.max(0.06, t.font.izleme)}em`,
                transform: `scale(${Math.max(0.5, rozetYay)})`,
                transformOrigin: "left center",
                opacity: Math.min(1, rozetYay * 1.8),
              }}
            >
              {harf(t, param.rozet)}
            </div>
          )}

          <div style={{ width: "100%", overflow: "hidden" }}>
            <div
              style={{
                fontFamily: yigin(t.font.baslik),
                fontWeight: t.font.agirlik_baslik,
                fontSize: baslikBoy,
                lineHeight: 1.12,
                letterSpacing: `${t.font.izleme}em`,
                color: yuzeyYazi(t, "kart"),
                whiteSpace: "nowrap",
                overflow: "hidden",
                textOverflow: "ellipsis",
                transform: `translateY(${(1 - baslikGir) * 105}%)`,
                opacity: Math.min(1, baslikGir * 2.4),
              }}
            >
              {harf(t, param.baslik)}
            </div>
          </div>

          {altVar && (
            <div style={{ width: "100%", overflow: "hidden" }}>
              <div
                style={{
                  fontFamily: yigin(t.font.govde),
                  fontWeight: t.font.agirlik_govde,
                  fontSize: altBoy,
                  lineHeight: 1.18,
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

        {okVar && (
          <div
            style={{
              width: okKutu,
              height: okKutu,
              borderRadius: keskin ? 0 : Math.round(okKutu * 0.5),
              background: rgba(vurgu, 0.16),
              border: `${Math.max(1.5, Math.round(2 * u))}px solid ${rgba(vurgu, 0.55)}`,
              boxShadow: keskin ? undefined : `0 0 ${16 * u}px ${rgba(vurgu, 0.32)}, inset 0 ${1 * u}px 0 ${rgba(t.renk.yazi, 0.2)}`,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              flexShrink: 0,
              transform: `scale(${Math.max(0.4, okYay) * (1 + 0.025 * a.nefes)})`,
              opacity: Math.min(1, okYay * 1.8),
            }}
          >
            <svg
              viewBox="0 0 24 24"
              width={okIkon}
              height={okIkon}
              style={{ overflow: "visible", transform: okKay }}
            >
              <path
                d={okGovde}
                pathLength={1}
                fill="none"
                stroke={vurgu}
                strokeWidth={2.8}
                strokeLinecap={keskin ? "square" : "round"}
                strokeDasharray="1 2"
                strokeDashoffset={cizgiOfset(1, okCiz)}
              />
              <path
                d={okBas}
                pathLength={1}
                fill="none"
                stroke={vurgu}
                strokeWidth={2.8}
                strokeLinecap={keskin ? "square" : "round"}
                strokeLinejoin={keskin ? "miter" : "round"}
                strokeDasharray="1 2"
                strokeDashoffset={cizgiOfset(1, Math.max(0, (okCiz - 0.35) / 0.65))}
              />
            </svg>
          </div>
        )}

        <div style={parlamaStil(t, a.parlama, u)} />
      </div>
    </div>
  );
};

export default tanimla({ meta: meta as never, sema, Bilesen: CtaKarti });
