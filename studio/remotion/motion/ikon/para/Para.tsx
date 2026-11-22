// Banknot: duotone kağıt hacmi, orta madeni parıltı ve sağa kayışta uçan iki parlaklık çizgisiyle oturur.
// Geometri: Lucide "banknote" (ISC, https://lucide.dev/icons/banknote), 24 birimlik viewBox.
import React from "react";
import { z } from "zod";
import { ikonStil, ton, useTema } from "../../../tema";
import { ikonKalinlik, KONTUR_EK } from "../../cekirdek/olcu";
import { useAkis } from "../../cekirdek/zaman";
import { tanimla, type BilesenProps } from "../../cekirdek/tipler";
import meta from "./meta.json";

export const sema = z.strictObject({
  renk: z.enum(["vurgu", "ikincil", "olumlu", "olumsuz", "yazi"]).default("olumlu").describe("Tema rengi adı; onaltılık renk yazılmaz"),
});

const NOKTALAR = "M6 12h.01M18 12h.01";

const Para: React.FC<BilesenProps<z.infer<typeof sema>>> = ({ param, kutu, sureKare, u }) => {
  const t = useTema();
  const a = useAkis(sureKare, meta.giris_sn, meta.cikis_sn);
  const gradId = `para-g-${React.useId().replace(/[^a-zA-Z0-9_-]/g, "")}`;
  const p1 = a.sirali(1, 3, "emphasis");
  const p2 = a.sirali(2, 3, "enter");
  const yay = a.yay(0, "keskin");
  const otur = a.takip(a.girKare - 3, 180);
  const parla = Math.max(0, Math.min(1, a.vurgu(a.girKare - 1, Math.round(0.32 * a.fps))));
  const parOp = Math.sin(parla * Math.PI) * (1 - a.cik);
  const x = -9.5 * (1 - a.gir) - 2.8 * a.ters + (otur - a.gorunur) * 1.4 + 9.5 * a.cik;
  const aci = -5 * a.ters + 7 * (1 - a.gir) + (a.gorunur - otur) * 4 + a.nefes * 1.3 + 5 * a.cik;
  const olcek = (0.94 + 0.06 * Math.min(1.06, yay)) * (1 + 0.016 * a.nefes);
  const icOlcek = 0.5 + 0.5 * p1;
  const cizgi = ikonKalinlik(t, kutu, u, 24);
  const renk = t.renk[param.renk];
  const is = ikonStil(t, renk, u);
  const blur = a.hizBulaniklik > 0.08 ? `blur(${(a.hizBulaniklik * 0.42 * u).toFixed(2)}px) ` : "";

  const ciz = (stroke: string, strokeWidth: number, op = 1, dx = 0, dy = 0) => (
    <g transform={`translate(${x + dx} ${dy + a.nefes * -0.3}) rotate(${aci} 12 12)`} opacity={op}>
      <rect width="20" height="12" x="2" y="6" rx="2" fill="none" stroke={stroke} strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round" />
      <g transform={`translate(12 12) scale(${icOlcek}) translate(-12 -12)`} opacity={Math.min(1, Math.max(0, p1 * 4))}>
        <circle cx="12" cy="12" r="2" fill="none" stroke={stroke} strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round" />
      </g>
      <path d={NOKTALAR} fill="none" stroke={stroke} strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round" opacity={p2} />
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
        transform: `scale(${olcek})`,
        filter: `${blur}${is.golge}`,
      }}
    >
      <defs>
        <linearGradient id={gradId} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor={ton(renk, -0.35, 0.42)} />
          <stop offset="100%" stopColor={is.dolgu} />
        </linearGradient>
      </defs>
      {/* Katman 1: duotone banknot dolgusu + orta parıltı diski */}
      <g transform={`translate(${x} ${a.nefes * -0.3}) rotate(${aci} 12 12)`}>
        <rect width="20" height="12" x="2" y="6" rx="2" fill={`url(#${gradId})`} opacity={0.95 * a.gir} />
        <circle cx="12" cy="12" r="2" fill={is.parilti} opacity={0.45 * p1} />
      </g>
      {/* Katman 2: rafine koyu kontur + canlı ana çizgi + üst parıltı */}
      {ciz(is.kontur, cizgi + KONTUR_EK, 0.9)}
      {ciz(is.vurgu, cizgi, 1)}
      {ciz(is.parilti, cizgi * 0.25, 0.72 * a.gir, -0.18, -0.22)}
      {/* Katman 3: sağ üst köşede değer parıltısı */}
      {parOp > 0.01 && (
        <g opacity={parOp}>
          <line x1={21.2} y1={4.4} x2={23.0} y2={2.6} stroke={is.parilti} strokeWidth={cizgi * 0.3} strokeLinecap="round" />
          <line x1={18.6} y1={3.4} x2={19.4} y2={1.5} stroke={is.vurgu} strokeWidth={cizgi * 0.28} strokeLinecap="round" />
        </g>
      )}
    </svg>
  );
};

export default tanimla({ meta: meta as never, sema, Bilesen: Para });
