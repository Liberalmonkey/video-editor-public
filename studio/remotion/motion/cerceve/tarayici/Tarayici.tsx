// Tarayıcı penceresi çerçevesi: yüzey malzemeli üst çubuk + parlamaStil kenar yansıması, ince specular çerçeve ve a.nefes mikro 3B süzülme.
import React from "react";
import { interpolate } from "remotion";
import { z } from "zod";
import { koyuMu, parlamaStil, rgba, ton, useTema, yigin, yuzeyStil } from "../../../tema";
import { cizgiOfset, useAkis } from "../../cekirdek/zaman";
import { tanimla, type BilesenProps } from "../../cekirdek/tipler";
import meta from "./meta.json";

export const sema = z.strictObject({
  adres: z.string().max(42).default("ornek.com/panel").describe("Adres çubuğunda görünen URL ya da sayfa adı"),
  renk: z.enum(["vurgu", "ikincil", "olumlu", "olumsuz", "yazi"]).default("vurgu").describe("Vurgu şeridi ve kilit simgesi tema rengi adı"),
});

const KIS = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

const Tarayici: React.FC<BilesenProps<z.infer<typeof sema>>> = ({ param, kutu, sureKare, u }) => {
  const t = useTema();
  const a = useAkis(sureKare, meta.giris_sn, meta.cikis_sn);
  const uid = React.useId().replace(/[^a-zA-Z0-9_-]/g, "");
  const rimId = `tar-rim-${uid}`;
  const vurgu = t.renk[param.renk];
  const yuzey = yuzeyStil(t, u, "kart");
  const acikCizgi = koyuMu(t.renk.zemin) ? t.renk.yazi : t.renk.zemin;

  const h = a.hazirlikKare;
  const onY = -12 * u * a.ters + a.nefes * -2.6 * u;
  const barAcil = 0.14 * a.belir + 0.86 * a.gir;
  const kenarCiz = a.e.enter(interpolate(a.f, [h + 2, a.girKare + 3], [0, 1], KIS));
  const adresGir = a.sirali(2, 2, "enter");
  const blur = a.hizBulaniklik > 0.08 ? `blur(${(a.hizBulaniklik * 0.42 * u).toFixed(2)}px) ` : "";

  const kose = Math.max(12 * u, t.sekil.kose * u);
  const barH = Math.max(68 * u, Math.round(kutu.h * 0.145));
  const kenarKal = Math.max(5 * u, Math.round(7 * u));
  const noktaCap = Math.max(12 * u, Math.round(barH * 0.21));
  const adresBoy = Math.max(28 * u, Math.round(barH * 0.4));

  const noktalar = [t.renk.olumsuz, t.renk.ikincil, t.renk.olumlu];

  const yarim = kenarKal / 2;
  const altH = Math.max(40, kutu.h - barH);
  const altR = Math.min(kose, altH / 2, kutu.w / 4);
  const cerceveYol = `M${yarim} ${barH}V${kutu.h - altR}A${altR} ${altR} 0 0 0 ${altR} ${kutu.h - yarim}H${kutu.w - altR}A${altR} ${altR} 0 0 0 ${kutu.w - yarim} ${kutu.h - altR}V${barH}`;
  const cerceveUz = altH * 2 + kutu.w + altR * 2;
  const katmanGolge = `drop-shadow(0 ${(18 * u).toFixed(1)}px ${(36 * u).toFixed(1)}px ${rgba(t.renk.ikon_kontur, 0.42)}) drop-shadow(0 ${(3 * u).toFixed(1)}px ${(8 * u).toFixed(1)}px ${rgba(t.renk.ikon_kontur, 0.28)})`;

  return (
    <div style={{ width: kutu.w, height: kutu.h, perspective: Math.round(1200 * u), overflow: "visible" }}>
      <div
        style={{
          position: "relative",
          width: kutu.w,
          height: kutu.h,
          opacity: a.belir * (1 - a.cik),
          transform: `translateY(${onY + a.cik * -24 * u}px) rotateX(${a.nefes * 0.9}deg) rotateY(${a.nefes * 1.2}deg)`,
          filter: `${blur}${katmanGolge}`,
        }}
      >
        {/* Üst tarayıcı çubuğu (yuzeyStil + parlamaStil) */}
        <div
          style={{
            ...yuzey,
            position: "relative",
            zIndex: 2,
            width: "100%",
            height: barH,
            borderRadius: 0,
            borderTopLeftRadius: kose,
            borderTopRightRadius: kose,
            borderBottom: `${Math.max(2 * u, Math.round(2.5 * u))}px solid ${rgba(vurgu, 0.72)}`,
            boxSizing: "border-box",
            padding: `0 ${Math.round(20 * u)}px`,
            display: "flex",
            alignItems: "center",
            gap: Math.round(18 * u),
            transformOrigin: "left center",
            transform: `scaleX(${barAcil})`,
            overflow: "hidden",
          }}
        >
          <div style={parlamaStil(t, a.parlama, u)} />

          {/* 3 pencere noktası */}
          <div style={{ display: "flex", alignItems: "center", gap: Math.round(9 * u), flexShrink: 0 }}>
            {noktalar.map((renk, i) => {
              const p = a.yay(i * 2, "elastik");
              return (
                <div
                  key={i}
                  style={{
                    width: noktaCap,
                    height: noktaCap,
                    borderRadius: noktaCap,
                    background: `radial-gradient(circle at 35% 30%, ${ton(renk, -0.45)}, ${renk})`,
                    boxShadow: `0 0 ${6 * u}px ${rgba(renk, 0.45)}`,
                    transform: `scale(${Math.max(0, p)})`,
                  }}
                />
              );
            })}
          </div>

          {/* Adres çubuğu */}
          <div
            style={{
              flex: 1,
              height: Math.round(barH * 0.66),
              borderRadius: Math.round(barH * 0.33),
              background: rgba(t.renk.yazi, 0.08),
              border: `${Math.max(1, Math.round(1.2 * u))}px solid ${rgba(t.renk.yazi, 0.16)}`,
              boxShadow: `inset 0 ${1 * u}px ${3 * u}px ${rgba(t.renk.ikon_kontur, 0.25)}`,
              padding: `0 ${Math.round(18 * u)}px`,
              display: "flex",
              alignItems: "center",
              gap: Math.round(10 * u),
              overflow: "hidden",
            }}
          >
            <div
              style={{
                width: Math.round(10 * u),
                height: Math.round(10 * u),
                borderRadius: Math.round(10 * u),
                background: ton(vurgu, -0.25),
                boxShadow: `0 0 ${8 * u}px ${rgba(vurgu, 0.75)}`,
                flexShrink: 0,
                transform: `scale(${adresGir})`,
              }}
            />
            <div
              style={{
                fontFamily: yigin(t.font.mono),
                fontWeight: t.font.agirlik_govde,
                fontSize: adresBoy,
                lineHeight: 1.05,
                color: t.renk.yazi,
                whiteSpace: "nowrap",
                overflow: "hidden",
                textOverflow: "ellipsis",
                transform: `translateY(${(1 - adresGir) * 110}%)`,
                opacity: Math.min(1, adresGir * 2.2),
              }}
            >
              {param.adres}
            </div>
          </div>
        </div>

        {/* Şeffaf ekran penceresinin ince specular rim çerçevesi */}
        <svg width={kutu.w} height={kutu.h} viewBox={`0 0 ${kutu.w} ${kutu.h}`} style={{ position: "absolute", inset: 0, pointerEvents: "none", overflow: "visible" }}>
          <defs>
            <linearGradient id={rimId} x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stopColor={rgba(acikCizgi, 0.82)} />
              <stop offset="50%" stopColor={rgba(vurgu, 0.52)} />
              <stop offset="100%" stopColor={rgba(acikCizgi, 0.65)} />
            </linearGradient>
          </defs>
          <path
            d={cerceveYol}
            fill="none"
            stroke={rgba(t.renk.ikon_kontur, 0.55)}
            strokeWidth={kenarKal + 3 * u}
            strokeLinecap="butt"
            strokeLinejoin="round"
            strokeDasharray={cerceveUz}
            strokeDashoffset={cizgiOfset(cerceveUz, kenarCiz)}
          />
          <path
            d={cerceveYol}
            fill="none"
            stroke={`url(#${rimId})`}
            strokeWidth={kenarKal}
            strokeLinecap="butt"
            strokeLinejoin="round"
            strokeDasharray={cerceveUz}
            strokeDashoffset={cizgiOfset(cerceveUz, kenarCiz)}
          />
        </svg>
      </div>
    </div>
  );
};

export default tanimla({ meta: meta as never, sema, Bilesen: Tarayici });
