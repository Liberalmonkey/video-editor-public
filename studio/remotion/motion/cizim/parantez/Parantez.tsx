// El çizimi süslü parantezler: organik katmanlı mürekkep, yumuşak ikonStil gölgesi ve orta uç parlamasıyla sarar.
// Geometri: Özgün deterministik el çizimi kübik Bezier süslü parantez yolları (remotion random).
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
const VH = 120;

const sapma = (tohum: string, genlik: number) => (random(tohum) - 0.5) * 2 * genlik;

const kubikUz = (p0: [number, number], p1: [number, number], p2: [number, number], p3: [number, number]) => {
  let uz = 0;
  let [ox, oy] = p0;
  for (let i = 1; i <= 12; i++) {
    const t = i / 12;
    const m = 1 - t;
    const x = m * m * m * p0[0] + 3 * m * m * t * p1[0] + 3 * m * t * t * p2[0] + t * t * t * p3[0];
    const y = m * m * m * p0[1] + 3 * m * m * t * p1[1] + 3 * m * t * t * p2[1] + t * t * t * p3[1];
    uz += Math.hypot(x - ox, y - oy);
    ox = x;
    oy = y;
  }
  return uz;
};

const parantezYolu = (merkezX: number, yon: -1 | 1, tohum: string) => {
  const j = (ad: string, g = 1.9) => sapma(`${tohum}-${ad}`, g);
  const ustUc: [number, number] = [merkezX - yon * 14 + j("ux"), 12 + j("uy")];
  const ustK1: [number, number] = [merkezX + yon * 3 + j("uk1x"), 11 + j("uk1y")];
  const ustK2: [number, number] = [merkezX - yon * 4 + j("uk2x"), 54 + j("uk2y")];
  const ortaUc: [number, number] = [merkezX + yon * 13 + j("ox"), 60 + j("oy")];
  const altK1: [number, number] = [merkezX - yon * 4 + j("ak1x"), 66 + j("ak1y")];
  const altK2: [number, number] = [merkezX + yon * 3 + j("ak2x"), 109 + j("ak2y")];
  const altUc: [number, number] = [merkezX - yon * 14 + j("ax"), 108 + j("ay")];

  const f = (p: [number, number]) => `${p[0].toFixed(1)} ${p[1].toFixed(1)}`;
  const d = `M ${f(ustUc)} C ${f(ustK1)} ${f(ustK2)} ${f(ortaUc)} C ${f(altK1)} ${f(altK2)} ${f(altUc)}`;
  const uzunluk = Math.ceil((kubikUz(ustUc, ustK1, ustK2, ortaUc) + kubikUz(ortaUc, altK1, altK2, altUc)) * 1.06);
  return { d, uzunluk, ortaUc };
};

const SOL = parantezYolu(25, -1, "cizim-parantez-sol");
const SAG = parantezYolu(VW - 25, 1, "cizim-parantez-sag");

const Parantez: React.FC<BilesenProps<z.infer<typeof sema>>> = ({ param, kutu, sureKare, u }) => {
  const t = useTema();
  const a = useAkis(sureKare, meta.giris_sn, meta.cikis_sn);
  const pSol = a.sirali(0, 4, "enter");
  const pSag = a.sirali(1, 4, "enter");
  const cizSol = 0.14 * a.belir + 0.86 * pSol;
  const cizSag = 0.14 * a.belir + 0.86 * pSag;
  const onAcik = 7.5 * a.ters;
  const oturSol = a.takip(a.girKare - 3, 175);
  const oturSag = a.takip(a.girKare + 1, 175);
  const solX = -onAcik + (1 - oturSol) * -5 - a.nefes * 1.2 - a.cik * 4;
  const sagX = onAcik + (1 - oturSag) * 5 + a.nefes * 1.2 + a.cik * 4;
  const ucParla = Math.sin(Math.max(0, Math.min(1, a.vurgu(a.girKare - 1, Math.round(0.32 * a.fps)))) * Math.PI) * (1 - a.cik);

  const ofset = (uz: number, p: number) => cizgiOfset(uz, Math.max(0, p * (1 - a.cik)));
  const ref = 0.26 * 1080 * u;
  const cizgiPx = ikonKalinlik(t, { x: 0, y: 0, w: ref, h: ref }, u, ref) * 0.72;
  const svgOlcek = Math.max(0.01, Math.min(kutu.w / VW, kutu.h / VH));
  const cizgi = cizgiPx / svgOlcek;
  const renk = t.renk[param.renk];
  const is = ikonStil(t, renk, u);
  const blur = a.hizBulaniklik > 0.08 ? `blur(${(a.hizBulaniklik * 0.35 * u).toFixed(2)}px) ` : "";

  const ciz = (stroke: string, width: number, op = 1, dx = 0, dy = 0) => (
    <g transform={`translate(${dx} ${dy})`} opacity={op}>
      <path
        d={SOL.d}
        fill="none"
        stroke={stroke}
        strokeWidth={width}
        strokeLinecap="round"
        strokeLinejoin="round"
        opacity={Math.min(1, cizSol * 6)}
        transform={`translate(${solX} 0)`}
        strokeDasharray={SOL.uzunluk}
        strokeDashoffset={ofset(SOL.uzunluk, cizSol)}
      />
      <path
        d={SAG.d}
        fill="none"
        stroke={stroke}
        strokeWidth={width}
        strokeLinecap="round"
        strokeLinejoin="round"
        opacity={Math.min(1, cizSag * 6)}
        transform={`translate(${sagX} 0)`}
        strokeDasharray={SAG.uzunluk}
        strokeDashoffset={ofset(SAG.uzunluk, cizSag)}
      />
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
        filter: `${blur}${is.golge}`,
      }}
    >
      {/* Organik mürekkep yayılım tabanı */}
      {ciz(is.dolgu, cizgi * 1.6, 0.72, 0.5, 0.9)}
      {/* Ana kalem vuruşu */}
      {ciz(rgba(renk, 0.95), cizgi, 1)}
      {/* İnce üst parlama vurgusu */}
      {ciz(is.parilti, cizgi * 0.28, 0.76, -0.5, -0.8)}
      {/* Parantez uçlarında ince parlama noktaları */}
      {ucParla > 0.02 && (
        <g opacity={ucParla}>
          <circle cx={SOL.ortaUc[0] + solX} cy={SOL.ortaUc[1]} r={cizgi * 0.55} fill={is.parilti} />
          <circle cx={SAG.ortaUc[0] + sagX} cy={SAG.ortaUc[1]} r={cizgi * 0.55} fill={is.parilti} />
        </g>
      )}
    </svg>
  );
};

export default tanimla({ meta: meta as never, sema, Bilesen: Parantez });
