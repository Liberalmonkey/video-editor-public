// Kıvrık ok: duotone hacim katmanı, üst parlaklık ve dirsek kıvrımında parlayan yön kıvılcımıyla hızlanarak oturur.
// Geometri: Lucide "corner-down-right" (ISC, https://lucide.dev/icons/corner-down-right), 24 birimlik viewBox.
import React from "react";
import { interpolate } from "remotion";
import { z } from "zod";
import { ikonStil, useTema } from "../../../tema";
import { ikonKalinlik, KONTUR_EK } from "../../cekirdek/olcu";
import { cizgiOfset, useAkis } from "../../cekirdek/zaman";
import { tanimla, type BilesenProps } from "../../cekirdek/tipler";
import meta from "./meta.json";

export const sema = z.strictObject({
  renk: z.enum(["vurgu", "ikincil", "olumlu", "olumsuz", "yazi"]).default("vurgu").describe("Tema rengi adı; onaltılık renk yazılmaz"),
});

const KIS = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const GOVDE = "M4 4v7a4 4 0 0 0 4 4h12";
const UC = "15 10 20 15 15 20";
const GOVDE_UZ = 25.5;
const UC_UZ = 14.6;

const OkKivrik: React.FC<BilesenProps<z.infer<typeof sema>>> = ({ param, kutu, sureKare, u }) => {
  const t = useTema();
  const a = useAkis(sureKare, meta.giris_sn, meta.cikis_sn);
  const p2 = a.sirali(1, 4, "emphasis");
  const yay = a.yay(0, "keskin");
  const otur = a.takip(a.girKare - 1, 185);
  const koseKare = a.hazirlikKare + Math.max(1, Math.round((a.girKare - a.hazirlikKare) * 0.45));
  const bitisKare = Math.max(koseKare + 1, a.girKare);
  const dikInis = a.e.settle(interpolate(a.f, [a.hazirlikKare, koseKare], [0, 1], KIS));
  const yatayCikis = Math.min(1, Math.max(0, a.e.emphasis(interpolate(a.f, [koseKare, bitisKare], [0, 1], KIS))));
  const govdeCiz = 0.18 * a.belir + 0.3 * dikInis + 0.52 * yatayCikis;
  const koseAtim = Math.sin(Math.max(0, Math.min(1, a.vurgu(koseKare, Math.round(0.26 * a.fps)))) * Math.PI);
  const donAci = -6 * koseAtim + a.nefes * 1.1;
  const x = -2.0 * a.ters + a.nefes * 0.35 + 5.5 * a.cik;
  const y = -2.2 * a.ters;
  const ucEkX = (otur - a.gorunur) * 1.5;
  const olcek = (1 - 0.06 * a.ters) * (0.93 + 0.07 * Math.min(1.06, yay) + 0.04 * (otur - a.gorunur)) * (1 + 0.015 * a.nefes) * (1 - 0.25 * a.cik);
  const cizgi = ikonKalinlik(t, kutu, u, 24);
  const renk = t.renk[param.renk];
  const is = ikonStil(t, renk, u);
  const blur = a.hizBulaniklik > 0.08 ? `blur(${(a.hizBulaniklik * 0.42 * u).toFixed(2)}px) ` : "";

  const ciz = (stroke: string, strokeWidth: number, op = 1, dx = 0, dy = 0) => (
    <g transform={`translate(${x + dx} ${y + dy}) rotate(${donAci} 8 11)`} opacity={op}>
      <path
        d={GOVDE}
        fill="none"
        stroke={stroke}
        strokeWidth={strokeWidth}
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeDasharray={GOVDE_UZ}
        strokeDashoffset={cizgiOfset(GOVDE_UZ, govdeCiz)}
      />
      <polyline
        points={UC}
        fill="none"
        stroke={stroke}
        strokeWidth={strokeWidth}
        strokeLinecap="round"
        strokeLinejoin="round"
        opacity={Math.min(1, Math.max(0, p2 * 6))}
        transform={`translate(${ucEkX} 0)`}
        strokeDasharray={UC_UZ}
        strokeDashoffset={cizgiOfset(UC_UZ, p2)}
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
      {/* Katman 1: duotone hacim katmanı */}
      {ciz(is.dolgu, cizgi * 1.46, 0.9, 0.35, 0.55)}
      {/* Katman 2: rafine koyu kontur + canlı ana çizgi + ince üst parıltı */}
      {ciz(is.kontur, cizgi + KONTUR_EK, 0.9)}
      {ciz(is.vurgu, cizgi, 1)}
      {ciz(is.parilti, cizgi * 0.28, 0.78 * a.gir, -0.18, -0.24)}
      {/* Katman 3: dirsek dönüş kıvılcımları */}
      {koseAtim > 0.01 && (
        <g opacity={koseAtim * (1 - a.cik)}>
          <line x1={3.4} y1={17.2} x2={1.6} y2={19.0} stroke={is.parilti} strokeWidth={cizgi * 0.3} strokeLinecap="round" />
          <line x1={6.2} y1={18.6} x2={5.5} y2={20.8} stroke={is.vurgu} strokeWidth={cizgi * 0.28} strokeLinecap="round" />
        </g>
      )}
    </svg>
  );
};

export default tanimla({ meta: meta as never, sema, Bilesen: OkKivrik });
