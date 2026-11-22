// Paylaş (kağıt uçak): duotone katlı kanat dolgusu, üst parıltı ve çapraz uçuşta kuyruk rüzgar çizgileriyle fırlar.
// Geometri: Lucide "send" (ISC, https://lucide.dev/icons/send), 24 birimlik viewBox.
import React from "react";
import { z } from "zod";
import { ikonStil, ton, useTema } from "../../../tema";
import { ikonKalinlik, KONTUR_EK } from "../../cekirdek/olcu";
import { cizgiOfset, useAkis } from "../../cekirdek/zaman";
import { tanimla, type BilesenProps } from "../../cekirdek/tipler";
import meta from "./meta.json";

export const sema = z.strictObject({
  renk: z.enum(["vurgu", "ikincil", "olumlu", "olumsuz", "yazi"]).default("vurgu").describe("Tema rengi adı; onaltılık renk yazılmaz"),
});

const GOVDE =
  "M14.536 21.686a.5.5 0 0 0 .937-.024l6.5-19a.496.496 0 0 0-.635-.635l-19 6.5a.5.5 0 0 0-.024.937l7.93 3.18a2 2 0 0 1 1.112 1.11z";
const KAT = "m21.854 2.147-10.94 10.939";
const KAT_UZ = 16;

const Paylas: React.FC<BilesenProps<z.infer<typeof sema>>> = ({ param, kutu, sureKare, u }) => {
  const t = useTema();
  const a = useAkis(sureKare, meta.giris_sn, meta.cikis_sn);
  const gradId = `paylas-g-${React.useId().replace(/[^a-zA-Z0-9_-]/g, "")}`;
  const pKat = a.sirali(1, 3, "enter");
  const yay = a.yay(0, "keskin");
  const otur = a.takip(a.girKare - 3, 185);
  const x = -7.5 * (1 - a.gir) - 3.0 * a.ters + (otur - a.gorunur) * 1.5 + a.nefes * 0.4 + 9.5 * a.cik;
  const y = 7.5 * (1 - a.gir) + 3.0 * a.ters - (otur - a.gorunur) * 1.5 - a.nefes * 0.4 - 9.5 * a.cik;
  const aci = -8 * a.ters + 7 * (1 - a.gir) - 5 * (a.gorunur - otur) + a.nefes * 1.2 - 6 * a.cik;
  const olcek = (1 - 0.08 * a.ters) * (0.91 + 0.09 * Math.min(1.06, yay) + 0.04 * (otur - a.gorunur)) * (1 + 0.015 * a.nefes) * (1 - 0.25 * a.cik);
  const ruzgarOp = Math.sin(a.gir * Math.PI) * (1 - a.cik) * 0.8;
  const cizgi = ikonKalinlik(t, kutu, u, 24);
  const renk = t.renk[param.renk];
  const is = ikonStil(t, renk, u);
  const blur = a.hizBulaniklik > 0.08 ? `blur(${(a.hizBulaniklik * 0.45 * u).toFixed(2)}px) ` : "";

  const ciz = (stroke: string, strokeWidth: number, op = 1, dx = 0, dy = 0) => (
    <g transform={`translate(${x + dx} ${y + dy}) rotate(${aci} 12 12)`} opacity={op}>
      <path d={GOVDE} fill="none" stroke={stroke} strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round" />
      <path
        d={KAT}
        fill="none"
        stroke={stroke}
        strokeWidth={strokeWidth}
        strokeLinecap="round"
        strokeLinejoin="round"
        opacity={Math.min(1, pKat * 6)}
        strokeDasharray={KAT_UZ}
        strokeDashoffset={cizgiOfset(KAT_UZ, pKat)}
      />
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
          <stop offset="0%" stopColor={ton(renk, -0.38, 0.46)} />
          <stop offset="100%" stopColor={is.dolgu} />
        </linearGradient>
      </defs>
      {/* Katman 1: duotone kağıt uçak hacmi */}
      <g transform={`translate(${x} ${y}) rotate(${aci} 12 12)`}>
        <path d={GOVDE} fill={`url(#${gradId})`} opacity={0.95 * a.gir} />
      </g>
      {/* Katman 2: rafine koyu kontur + canlı ana çizgi + üst parıltı */}
      {ciz(is.kontur, cizgi + KONTUR_EK, 0.9)}
      {ciz(is.vurgu, cizgi, 1)}
      {ciz(is.parilti, cizgi * 0.24, 0.76 * a.gir, -0.18, -0.22)}
      {/* Katman 3: uçuş kuyruğundan çıkan iki ince hız çizgisi */}
      {ruzgarOp > 0.01 && (
        <g opacity={ruzgarOp}>
          <line x1={x + 2.2} y1={y + 19.6} x2={x + 6.4} y2={y + 15.4} stroke={is.parilti} strokeWidth={cizgi * 0.28} strokeLinecap="round" />
          <line x1={x + 4.8} y1={y + 21.8} x2={x + 8.4} y2={y + 18.2} stroke={is.vurgu} strokeWidth={cizgi * 0.26} strokeLinecap="round" />
        </g>
      )}
    </svg>
  );
};

export default tanimla({ meta: meta as never, sema, Bilesen: Paylas });
