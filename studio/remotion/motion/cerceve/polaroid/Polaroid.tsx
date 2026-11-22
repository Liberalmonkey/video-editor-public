// Polaroid fotoğraf çerçevesi: yuzeyStil katman gölgesi, yumuşak kağıt gradyanı, parlama şeridi ve içi saydam pencereyle eğik düşüp oturur.
import React from "react";
import { interpolate } from "remotion";
import { z } from "zod";
import { dokuKatmani, harf, koyuMu, parlamaStil, rgba, ton, useTema, yigin, yuzeyStil } from "../../../tema";
import { useAkis } from "../../cekirdek/zaman";
import { tanimla, type BilesenProps } from "../../cekirdek/tipler";
import meta from "./meta.json";

export const sema = z.strictObject({
  not: z.string().max(36).default("O anı yakala").describe("Alt beyaz kenarda yazan kısa not; boşsa gizlenir"),
  egim: z.number().min(-10).max(10).default(-3.5).describe("Oturduğundaki hafif eğim açısı (derece)"),
  renk: z.enum(["vurgu", "ikincil", "olumlu", "olumsuz", "yazi"]).default("vurgu").describe("Alt köşe damga vurgu rengi adı"),
});

const KIS = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

const Polaroid: React.FC<BilesenProps<z.infer<typeof sema>>> = ({ param, kutu, sureKare, u }) => {
  const t = useTema();
  const a = useAkis(sureKare, meta.giris_sn, meta.cikis_sn);
  const vurgu = t.renk[param.renk];
  const yuzey = yuzeyStil(t, u, "kart");

  const otur = a.yay(2, "ipeksi");
  const dusY = (1 - a.gir) * -68 * u - 14 * u * a.ters + a.nefes * -2.2 * u + a.cik * 52 * u;
  const aci = param.egim + (1 - Math.min(1.06, otur)) * -10 + 3 * a.ters + a.nefes * 0.45 + a.cik * 8;
  const olcek = 1 + (1 - a.gir) * 0.08 + 0.02 * a.ters - 0.06 * a.cik;
  const blur = a.hizBulaniklik > 0.08 ? `blur(${(a.hizBulaniklik * 0.4 * u).toFixed(2)}px)` : undefined;

  const yaziSil = a.e.enter(interpolate(a.f, [a.girKare - 2, a.girKare + 10], [0, 1], KIS));

  const kagitRenk = koyuMu(t.renk.zemin) ? t.renk.yazi : t.renk.zemin;
  const murekkep = koyuMu(t.renk.zemin) ? t.renk.zemin : t.renk.yazi;
  const doku = dokuKatmani(t);
  const kagitGradyan = `linear-gradient(170deg, ${kagitRenk} 0%, ${ton(kagitRenk, 0.06)} 100%)`;
  const kagitArka = doku ? `${doku}, ${kagitGradyan}` : kagitGradyan;

  const yan = Math.max(20 * u, Math.round(kutu.w * 0.055));
  const ust = yan;
  const alt = Math.max(108 * u, Math.round(kutu.h * 0.21));
  const yaziBoy = Math.max(28 * u, Math.round(alt * 0.34));
  const disKose = Math.max(4 * u, Math.round(t.sekil.kose * 0.35 * u));

  return (
    <div
      style={{
        position: "relative",
        width: kutu.w,
        height: kutu.h,
        display: "flex",
        flexDirection: "column",
        borderRadius: disKose,
        overflow: "hidden",
        border: yuzey.border,
        boxShadow: `0 ${2 * u}px ${6 * u}px ${rgba(t.renk.ikon_kontur, 0.28)}, 0 ${22 * u}px ${48 * u}px ${rgba(t.renk.ikon_kontur, 0.42)}`,
        opacity: a.belir * (1 - a.cik),
        filter: blur,
        transformOrigin: "center center",
        transform: `translateY(${dusY}px) rotate(${aci}deg) scale(${olcek})`,
      }}
    >
      {/* Üst kenar */}
      <div style={{ position: "relative", height: ust, width: "100%", background: kagitArka, flexShrink: 0, overflow: "hidden" }}>
        <div style={parlamaStil(t, a.parlama, u)} />
      </div>

      {/* Orta satır: içi %100 saydam fotoğraf penceresi + derinlikli paspartu gölgesi */}
      <div style={{ flex: 1, display: "flex", minHeight: 0 }}>
        <div style={{ width: yan, background: kagitArka, flexShrink: 0 }} />
        <div
          style={{
            flex: 1,
            background: "transparent",
            boxShadow: `inset 0 ${3 * u}px ${10 * u}px ${rgba(murekkep, 0.26)}, inset 0 0 0 ${Math.max(1.5, Math.round(1.5 * u))}px ${rgba(murekkep, 0.16)}`,
          }}
        />
        <div style={{ width: yan, background: kagitArka, flexShrink: 0 }} />
      </div>

      {/* Alt geniş not şeridi */}
      <div
        style={{
          position: "relative",
          height: alt,
          width: "100%",
          background: kagitArka,
          flexShrink: 0,
          padding: `0 ${yan + Math.round(6 * u)}px`,
          boxSizing: "border-box",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: Math.round(14 * u),
          overflow: "hidden",
        }}
      >
        <div style={parlamaStil(t, a.parlama, u)} />
        {param.not.trim().length > 0 ? (
          <div
            style={{
              fontFamily: yigin(t.font.baslik),
              fontWeight: t.font.agirlik_baslik,
              fontSize: yaziBoy,
              lineHeight: 1.1,
              letterSpacing: `${t.font.izleme}em`,
              color: murekkep,
              whiteSpace: "nowrap",
              overflow: "hidden",
              textOverflow: "ellipsis",
              clipPath: `inset(0 ${Math.round((1 - yaziSil) * 100)}% 0 0)`,
            }}
          >
            {harf(t, param.not)}
          </div>
        ) : (
          <div />
        )}
        <div
          style={{
            width: Math.round(14 * u),
            height: Math.round(14 * u),
            borderRadius: Math.round(14 * u),
            background: `radial-gradient(circle at 35% 30%, ${ton(vurgu, -0.4)}, ${vurgu})`,
            boxShadow: `0 0 ${8 * u}px ${rgba(vurgu, 0.5)}`,
            flexShrink: 0,
            transform: `scale(${Math.max(0, yaziSil)})`,
          }}
        />
      </div>
    </div>
  );
};

export default tanimla({ meta: meta as never, sema, Bilesen: Polaroid });
