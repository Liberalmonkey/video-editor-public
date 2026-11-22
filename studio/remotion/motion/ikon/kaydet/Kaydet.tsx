// Yer imi (kaydet): duotone şerit hacmi, dikey ışık katı ve alt çentik kilitlenirken köşede parlayan kıvılcımla oturur.
// Geometri: Lucide "bookmark" (ISC, https://lucide.dev/icons/bookmark), 24 birimlik viewBox.
import React from "react";
import { z } from "zod";
import { ikonStil, ton, useTema } from "../../../tema";
import { ikonKalinlik, KONTUR_EK } from "../../cekirdek/olcu";
import { useAkis } from "../../cekirdek/zaman";
import { tanimla, type BilesenProps } from "../../cekirdek/tipler";
import meta from "./meta.json";

export const sema = z.strictObject({
  renk: z.enum(["vurgu", "ikincil", "olumlu", "olumsuz", "yazi"]).default("ikincil").describe("Tema rengi adı; onaltılık renk yazılmaz"),
});

const Kaydet: React.FC<BilesenProps<z.infer<typeof sema>>> = ({ param, kutu, sureKare, u }) => {
  const t = useTema();
  const a = useAkis(sureKare, meta.giris_sn, meta.cikis_sn);
  const gradId = `kaydet-g-${React.useId().replace(/[^a-zA-Z0-9_-]/g, "")}`;
  const yay = a.yay(0, "elastik");
  const otur = a.takip(a.girKare - 2, 175);
  const y = -8.0 * (1 - a.gir) - 2.4 * a.ters + (otur - a.gorunur) * 1.2 + a.nefes * -0.35 - 7.5 * a.cik;
  const kilit = Math.max(0, Math.min(1, a.vurgu(a.girKare + 1, Math.round(0.28 * a.fps))));
  const esne = Math.sin(kilit * Math.PI);
  const centikY = (17 + 1.5 * esne).toFixed(2);
  const yol = `M19 21 L12 ${centikY} L5 21 V5 a2 2 0 0 1 2-2 h10 a2 2 0 0 1 2 2 Z`;
  const sy = (1 - 0.08 * a.ters) * (0.94 + 0.06 * Math.min(1.06, yay)) * (1 + 0.07 * esne + 0.015 * a.nefes) * (1 - 0.25 * a.cik);
  const sx = (1 + 0.05 * a.ters) * (1 - 0.04 * esne) * (1 - 0.15 * a.cik);
  const cizgi = ikonKalinlik(t, kutu, u, 24);
  const renk = t.renk[param.renk];
  const is = ikonStil(t, renk, u);
  const blur = a.hizBulaniklik > 0.08 ? `blur(${(a.hizBulaniklik * 0.4 * u).toFixed(2)}px) ` : "";

  const ciz = (stroke: string, strokeWidth: number, op = 1, dx = 0, dy = 0) => (
    <g transform={`translate(${dx} ${y + dy}) translate(12 3) scale(${sx} ${sy}) translate(-12 -3)`} opacity={op}>
      <path d={yol} fill="none" stroke={stroke} strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round" />
    </g>
  );

  return (
    <svg
      viewBox="0 0 24 24"
      width={kutu.w}
      height={kutu.h}
      style={{
        overflow: "visible",
        opacity: a.belir * (1 - a.cik),
        filter: `${blur}${is.golge}`,
      }}
    >
      <defs>
        <linearGradient id={gradId} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor={ton(renk, -0.35, 0.46)} />
          <stop offset="100%" stopColor={is.dolgu} />
        </linearGradient>
      </defs>
      {/* Katman 1: duotone şerit hacim dolgusu ve ince dikey ışık şeridi */}
      <g transform={`translate(0 ${y}) translate(12 3) scale(${sx} ${sy}) translate(-12 -3)`}>
        <path d={yol} fill={`url(#${gradId})`} opacity={0.95 * a.gir} />
        <line x1="8.6" y1="6.4" x2="8.6" y2="13.2" stroke={is.parilti} strokeWidth={cizgi * 0.3} strokeLinecap="round" opacity={0.75 * a.gir} />
      </g>
      {/* Katman 2: rafine koyu kontur + canlı ana çizgi + üst parıltı */}
      {ciz(is.kontur, cizgi + KONTUR_EK, 0.9)}
      {ciz(is.vurgu, cizgi, 1)}
      {ciz(is.parilti, cizgi * 0.24, 0.72 * a.gir, -0.18, -0.22)}
      {/* Katman 3: kilitlenme anında sağ üst köşede küçük parıltı */}
      {esne > 0.01 && (
        <g opacity={esne * (1 - a.cik)} transform={`translate(0 ${y})`}>
          <line x1={20.2} y1={2.6} x2={22.2} y2={1.2} stroke={is.parilti} strokeWidth={cizgi * 0.3} strokeLinecap="round" />
          <line x1={21.0} y1={5.2} x2={23.0} y2={5.0} stroke={is.vurgu} strokeWidth={cizgi * 0.28} strokeLinecap="round" />
        </g>
      )}
    </svg>
  );
};

export default tanimla({ meta: meta as never, sema, Bilesen: Kaydet });
