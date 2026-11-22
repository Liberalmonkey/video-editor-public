// Bant çerçeve: yuzeyStil yumuşak katman gölgesi, içi saydam mat çerçeve ve iki karşıt köşeye yapışan yarı saydam dokulu bant parçaları.
import React from "react";
import { z } from "zod";
import { koyuMu, rgba, ton, useTema, yuzeyStil } from "../../../tema";
import { useAkis } from "../../cekirdek/zaman";
import { tanimla, type BilesenProps } from "../../cekirdek/tipler";
import meta from "./meta.json";

export const sema = z.strictObject({
  renk: z.enum(["vurgu", "ikincil", "olumlu", "olumsuz", "yazi"]).default("ikincil").describe("Yapışkan bant tema rengi adı"),
  kose: z.enum(["sol-ust", "sag-ust"]).default("sol-ust").describe("İlk bandın yapışacağı üst köşe; ikinci bant çapraz köşeye gelir"),
});

const BANT_YOL =
  "M6 3 L154 3 L158 9 L153 15 L159 22 L153 29 L158 35 L154 41 L6 41 L2 35 L7 29 L1 22 L7 15 L2 9 Z";

const Bant: React.FC<BilesenProps<z.infer<typeof sema>>> = ({ param, kutu, sureKare, u }) => {
  const t = useTema();
  const a = useAkis(sureKare, meta.giris_sn, meta.cikis_sn);
  const uid = React.useId().replace(/[^a-zA-Z0-9_-]/g, "");
  const bantGradId = `bant-g-${uid}`;
  const bantRenk = t.renk[param.renk];
  const yuzey = yuzeyStil(t, u, "kart");
  const acikCizgi = koyuMu(t.renk.zemin) ? t.renk.yazi : t.renk.zemin;

  const cerceveAci = (1 - a.gir) * 3.5 - 2.2 * a.ters + a.nefes * 0.35 + a.cik * -4;
  const cerceveY = (1 - a.gir) * 28 * u + 10 * u * a.ters + a.nefes * -2 * u + a.cik * 24 * u;
  const blur = a.hizBulaniklik > 0.08 ? `blur(${(a.hizBulaniklik * 0.4 * u).toFixed(2)}px)` : undefined;

  const bant1Sil = a.sirali(0, 3, "enter");
  const bant2Sil = a.sirali(1, 4, "enter");
  const bant1Bas = a.yay(2, "keskin");
  const bant2Bas = a.yay(6, "keskin");

  const bantW = Math.max(112 * u, Math.round(Math.min(kutu.w, kutu.h) * 0.28));
  const bantH = Math.round(bantW * 0.275);
  const kenarKal = Math.max(10 * u, Math.round(12 * u));
  const icPay = Math.round(14 * u);

  const solUstMu = param.kose === "sol-ust";
  const ustAci = solUstMu ? -36 : 36;
  const altAci = solUstMu ? -34 : 34;

  const bantGolge = `drop-shadow(0 ${(4 * u).toFixed(1)}px ${(10 * u).toFixed(1)}px ${rgba(t.renk.ikon_kontur, 0.34)})`;

  const bantStil = (sil: number, bas: number, aci: number): React.CSSProperties => ({
    position: "absolute",
    width: bantW,
    height: bantH,
    overflow: "visible",
    filter: bantGolge,
    transformOrigin: "center center",
    transform: `rotate(${aci}deg) scale(${0.92 + 0.08 * Math.min(1.06, Math.max(0, bas))})`,
    clipPath: `inset(0 ${Math.round((1 - sil) * 100)}% 0 0)`,
    opacity: Math.min(1, sil * 2.4),
  });

  const bantIc = (
    <>
      <defs>
        <linearGradient id={bantGradId} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor={ton(bantRenk, -0.22, 0.84)} />
          <stop offset="55%" stopColor={rgba(bantRenk, 0.78)} />
          <stop offset="100%" stopColor={ton(bantRenk, 0.12, 0.86)} />
        </linearGradient>
      </defs>
      <path d={BANT_YOL} fill={`url(#${bantGradId})`} stroke={rgba(acikCizgi, 0.35)} strokeWidth={1.4} />
      <line x1="16" y1="13" x2="144" y2="13" stroke={ton(bantRenk, -0.55, 0.45)} strokeWidth={2.2} strokeDasharray="12 8" />
      <line x1="22" y1="30" x2="138" y2="30" stroke={rgba(t.renk.ikon_kontur, 0.16)} strokeWidth={1.5} />
    </>
  );

  return (
    <div
      style={{
        position: "relative",
        width: kutu.w,
        height: kutu.h,
        opacity: a.belir * (1 - a.cik),
        filter: blur,
        transform: `translateY(${cerceveY}px) rotate(${cerceveAci}deg)`,
        overflow: "visible",
      }}
    >
      {/* İçi tamamen saydam, yumuşak gerçekçi katman gölgeli çerçeve */}
      <div
        style={{
          position: "absolute",
          inset: icPay,
          borderRadius: yuzey.borderRadius,
          border: `${kenarKal}px solid ${rgba(acikCizgi, 0.94)}`,
          boxShadow: [
            `0 ${2 * u}px ${6 * u}px ${rgba(t.renk.ikon_kontur, 0.28)}`,
            `0 ${18 * u}px ${40 * u}px ${rgba(t.renk.ikon_kontur, 0.36)}`,
            `inset 0 ${3 * u}px ${10 * u}px ${rgba(t.renk.ikon_kontur, 0.28)}`,
          ].join(", "),
          background: "transparent",
          boxSizing: "border-box",
        }}
      />

      {/* Birinci bant parçası (üst köşe) */}
      <svg
        viewBox="0 0 160 44"
        style={{
          ...bantStil(bant1Sil, bant1Bas, ustAci),
          top: Math.round(icPay - bantH * 0.22),
          left: solUstMu ? Math.round(icPay - bantW * 0.24) : undefined,
          right: solUstMu ? undefined : Math.round(icPay - bantW * 0.24),
        }}
      >
        {bantIc}
      </svg>

      {/* İkinci bant parçası (çapraz alt köşe) */}
      <svg
        viewBox="0 0 160 44"
        style={{
          ...bantStil(bant2Sil, bant2Bas, altAci),
          bottom: Math.round(icPay - bantH * 0.22),
          right: solUstMu ? Math.round(icPay - bantW * 0.24) : undefined,
          left: solUstMu ? undefined : Math.round(icPay - bantW * 0.24),
        }}
      >
        {bantIc}
      </svg>
    </div>
  );
};

export default tanimla({ meta: meta as never, sema, Bilesen: Bant });
