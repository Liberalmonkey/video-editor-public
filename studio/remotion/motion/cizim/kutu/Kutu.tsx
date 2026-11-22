// El çizimi dikdörtgen: organik katmanlı mürekkep kenarları, yumuşak ikonStil gölgesi ve köşe kilidi parlamasıyla çizilir.
// Geometri: Özgün deterministik el çizimi SVG kenarları (remotion random).
import React from "react";
import { random } from "remotion";
import { z } from "zod";
import { ikonStil, rgba, useTema } from "../../../tema";
import { ikonKalinlik } from "../../cekirdek/olcu";
import { cizgiOfset, useAkis } from "../../cekirdek/zaman";
import { tanimla, type BilesenProps } from "../../cekirdek/tipler";
import meta from "./meta.json";

export const sema = z.strictObject({
  renk: z.enum(["vurgu", "ikincil", "olumlu", "olumsuz", "yazi"]).default("vurgu").describe("Tema rengi adı; onaltılık renk yazılmaz"),
});

const VW = 240;
const VH = 144;

const sapma = (tohum: string, genlik: number) => (random(tohum) - 0.5) * 2 * genlik;

interface KenarYolu {
  d: string;
  uzunluk: number;
  son: [number, number];
}

const elKenari = (x1: number, y1: number, x2: number, y2: number, tohum: string): KenarYolu => {
  const ax = x1 + sapma(`${tohum}-ax`, 2.2);
  const ay = y1 + sapma(`${tohum}-ay`, 2.2);
  const bx = x2 + sapma(`${tohum}-bx`, 2.2);
  const by = y2 + sapma(`${tohum}-by`, 2.2);
  const mx = (ax + bx) / 2 + sapma(`${tohum}-mx`, 2.8);
  const my = (ay + by) / 2 + sapma(`${tohum}-my`, 2.8);
  const d = `M ${ax.toFixed(1)} ${ay.toFixed(1)} Q ${mx.toFixed(1)} ${my.toFixed(1)} ${bx.toFixed(1)} ${by.toFixed(1)}`;
  const uzunluk = Math.ceil((Math.hypot(mx - ax, my - ay) + Math.hypot(bx - mx, by - my)) * 1.05);
  return { d, uzunluk, son: [bx, by] };
};

const KENARLAR: KenarYolu[] = [
  elKenari(12, 22, 230, 20, "cizim-kutu-ust"),
  elKenari(218, 10, 217, 134, "cizim-kutu-sag"),
  elKenari(228, 122, 10, 124, "cizim-kutu-alt"),
  elKenari(22, 134, 24, 10, "cizim-kutu-sol"),
];

const Kutu: React.FC<BilesenProps<z.infer<typeof sema>>> = ({ param, kutu, sureKare, u }) => {
  const t = useTema();
  const a = useAkis(sureKare, meta.giris_sn, meta.cikis_sn);
  const onOlcek = 1 - 0.06 * a.ters;
  const otur = a.takip(a.girKare, 175);
  const kilitParla = Math.sin(Math.max(0, Math.min(1, a.vurgu(a.girKare - 1, Math.round(0.32 * a.fps)))) * Math.PI) * (1 - a.cik);
  const olcek = onOlcek * (0.96 + 0.04 * otur) * (1 + 0.01 * a.nefes) * (1 - 0.08 * a.cik);
  const aci = (1 - otur) * 1.2 + a.nefes * 0.35 - a.cik * 1.4;
  const ref = 0.26 * 1080 * u;
  const cizgiPx = ikonKalinlik(t, { x: 0, y: 0, w: ref, h: ref }, u, ref) * 0.72;
  const svgOlcek = Math.max(0.01, Math.min(kutu.w / VW, kutu.h / VH));
  const cizgi = cizgiPx / svgOlcek;
  const renk = t.renk[param.renk];
  const is = ikonStil(t, renk, u);
  const blur = a.hizBulaniklik > 0.08 ? `blur(${(a.hizBulaniklik * 0.35 * u).toFixed(2)}px) ` : "";

  const ilerlemeler = KENARLAR.map((_, i) => {
    const ham = a.sirali(i, 2, "enter");
    const girP = i === 0 ? 0.14 * a.belir + 0.86 * ham : ham;
    const tersCik = Math.max(0, Math.min(1, a.cik * 1.4 - (3 - i) * 0.12));
    return Math.max(0, girP * (1 - tersCik));
  });

  const ciz = (stroke: string, width: number, op = 1, dx = 0, dy = 0) => (
    <g transform={`translate(${dx} ${dy})`} opacity={op}>
      {KENARLAR.map((k, i) => (
        <path
          key={i}
          d={k.d}
          fill="none"
          stroke={stroke}
          strokeWidth={width}
          strokeLinecap="round"
          strokeLinejoin="round"
          opacity={Math.min(1, ilerlemeler[i] * 6)}
          strokeDasharray={k.uzunluk}
          strokeDashoffset={cizgiOfset(k.uzunluk, ilerlemeler[i])}
        />
      ))}
    </g>
  );

  return (
    <svg
      viewBox={`0 0 ${VW} ${VH}`}
      width={kutu.w}
      height={kutu.h}
      style={{
        overflow: "visible",
        opacity: a.belir * (1 - a.cik * 0.85),
        transform: `scale(${olcek}) rotate(${aci}deg)`,
        filter: `${blur}${is.golge}`,
      }}
    >
      {/* Yarı saydam organik mürekkep yayılım tabanı */}
      {ciz(is.dolgu, cizgi * 1.6, 0.72, 0.6, 0.9)}
      {/* Ana organik kalem çizgisi */}
      {ciz(rgba(renk, 0.95), cizgi, 1)}
      {/* Üst parlama vurgusu */}
      {ciz(is.parilti, cizgi * 0.28, 0.76, -0.6, -0.8)}
      {/* Köşe kapanış parlaması */}
      {kilitParla > 0.02 && (
        <g opacity={kilitParla}>
          <circle cx={23} cy={21} r={cizgi * 1.15} fill={rgba(renk, 0.35)} />
          <circle cx={23} cy={21} r={cizgi * 0.45} fill={is.parilti} />
          <circle cx={218} cy={122} r={cizgi * 0.4} fill={is.parilti} />
        </g>
      )}
    </svg>
  );
};

export default tanimla({ meta: meta as never, sema, Bilesen: Kutu });
