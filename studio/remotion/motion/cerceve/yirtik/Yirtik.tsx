// Yırtık kağıt kenarlı şerit çerçeve: yuzeyStil uyumlu yumuşak çok katmanlı kağıt gölgesi, doğal lif kenarı ve saydam orta pencere.
import React, { useId } from "react";
import { random } from "remotion";
import { z } from "zod";
import { koyuMu, rgba, ton, useTema, yuzeyStil } from "../../../tema";
import { useAkis } from "../../cekirdek/zaman";
import { tanimla, type BilesenProps } from "../../cekirdek/tipler";
import meta from "./meta.json";

export const sema = z.strictObject({
  tohum: z.number().int().min(1).max(999).default(7).describe("Yırtık kenar profili için deterministik rastgele tohum"),
  renk: z.enum(["vurgu", "ikincil", "olumlu", "olumsuz", "yazi"]).default("vurgu").describe("Şerit iç kenar vurgu çizgisi tema rengi adı"),
  serit: z.number().min(0.12).max(0.26).default(0.18).describe("Üst ve alt yırtık şerit yüksekliğinin kutu boyuna oranı"),
});

const yirtikNoktalar = (w: number, tabanY: number, genlik: number, adimSayi: number, anahtar: string) => {
  const noktalar: Array<[number, number]> = [];
  for (let i = 0; i <= adimSayi; i++) {
    const x = (i / adimSayi) * w;
    const dalga = (random(`${anahtar}-y-${i}`) - 0.5) * 2 * genlik;
    const kucuk = (random(`${anahtar}-k-${i}`) - 0.5) * genlik * 0.55;
    noktalar.push([Math.round(x * 10) / 10, Math.round((tabanY + dalga + kucuk) * 10) / 10]);
  }
  return noktalar;
};

const ustYol = (w: number, noktalar: Array<[number, number]>) =>
  `M0 0 H${w} ` + noktalar.slice().reverse().map(([x, y]) => `L${x} ${y}`).join(" ") + " Z";

const altYol = (w: number, h: number, noktalar: Array<[number, number]>) =>
  `M0 ${h} ` + noktalar.map(([x, y]) => `L${x} ${y}`).join(" ") + ` L${w} ${h} Z`;

const cizgiYol = (noktalar: Array<[number, number]>) =>
  noktalar.map(([x, y], i) => `${i === 0 ? "M" : "L"}${x} ${y}`).join(" ");

const Yirtik: React.FC<BilesenProps<z.infer<typeof sema>>> = ({ param, kutu, sureKare, u }) => {
  const t = useTema();
  const a = useAkis(sureKare, meta.giris_sn, meta.cikis_sn);
  const uid = useId().replace(/[^a-zA-Z0-9_-]/g, "");
  const vurgu = t.renk[param.renk];
  const yuzey = yuzeyStil(t, u, "kart");

  const otur = a.yay(3, "ipeksi");
  const kapaliMesafe = kutu.h * 0.18;
  const acilma = (1 - a.gir) * kapaliMesafe + 12 * u * a.ters + a.nefes * -1.8 * u + a.cik * (kapaliMesafe * 0.85);
  const lifTakip = (1 - Math.min(1.06, Math.max(0, otur))) * 8 * u;
  const egim = (1 - a.gir) * 2.2 - 1.1 * a.ters + a.nefes * 0.25;
  const blur = a.hizBulaniklik > 0.08 ? `blur(${(a.hizBulaniklik * 0.4 * u).toFixed(2)}px) ` : "";

  const seritH = Math.max(36 * u, Math.round(kutu.h * param.serit));
  const genlik = Math.max(7 * u, Math.round(seritH * 0.16));
  const adim = 34;

  const ustN = yirtikNoktalar(kutu.w, seritH, genlik, adim, `y-${param.tohum}-u`);
  const ustLifN = yirtikNoktalar(kutu.w, seritH + Math.round(5 * u), genlik * 0.9, adim, `y-${param.tohum}-ul`);
  const altN = yirtikNoktalar(kutu.w, kutu.h - seritH, genlik, adim, `y-${param.tohum}-a`);
  const altLifN = yirtikNoktalar(kutu.w, kutu.h - seritH - Math.round(5 * u), genlik * 0.9, adim, `y-${param.tohum}-al`);

  const kagitRenk = koyuMu(t.renk.zemin) ? t.renk.yazi : t.renk.zemin;
  const lifRenk = ton(kagitRenk, 0.18, 0.88);
  const yumusakKenar = rgba(t.renk.ikon_kontur, 0.28);
  // Gerçekçi iki katmanlı kağıt kıvrım gölgesi (temas + ortam gölgesi)
  const kagitGolge = `drop-shadow(0 ${(2 * u).toFixed(1)}px ${(4 * u).toFixed(1)}px ${rgba(t.renk.ikon_kontur, 0.34)}) drop-shadow(0 ${(12 * u).toFixed(1)}px ${(26 * u).toFixed(1)}px ${rgba(t.renk.ikon_kontur, 0.36)})`;
  const dokuId = `yirtik-doku-${uid}`;
  const gradUstId = `yirtik-gu-${uid}`;
  const gradAltId = `yirtik-ga-${uid}`;
  const ustMaskeId = `yirtik-ust-${uid}`;
  const altMaskeId = `yirtik-alt-${uid}`;
  const ustAna = ustYol(kutu.w, ustN);
  const altAna = altYol(kutu.w, kutu.h, altN);

  return (
    <div style={{ width: kutu.w, height: kutu.h, borderRadius: yuzey.borderRadius, overflow: "visible" }}>
      <svg
        width={kutu.w}
        height={kutu.h}
        viewBox={`0 0 ${kutu.w} ${kutu.h}`}
        style={{
          overflow: "visible",
          filter: `${blur}${kagitGolge}`,
          opacity: a.belir * (1 - a.cik),
        }}
      >
        <defs>
          <filter id={dokuId}>
            <feTurbulence type="fractalNoise" baseFrequency="0.22" numOctaves={3} seed={param.tohum} />
            <feColorMatrix type="saturate" values="0" />
          </filter>
          <linearGradient id={gradUstId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={kagitRenk} />
            <stop offset="100%" stopColor={ton(kagitRenk, 0.08)} />
          </linearGradient>
          <linearGradient id={gradAltId} x1="0" y1="1" x2="0" y2="0">
            <stop offset="0%" stopColor={kagitRenk} />
            <stop offset="100%" stopColor={ton(kagitRenk, 0.08)} />
          </linearGradient>
          <clipPath id={ustMaskeId}>
            <path d={ustAna} />
          </clipPath>
          <clipPath id={altMaskeId}>
            <path d={altAna} />
          </clipPath>
        </defs>

        {/* Üst yırtık kağıt şeridi (orta bant %100 saydam) */}
        <g style={{ transformOrigin: `${kutu.w / 2}px 0px`, transform: `translateY(${acilma}px) rotate(${-egim}deg)` }}>
          <path d={ustYol(kutu.w, ustLifN)} fill={lifRenk} stroke={yumusakKenar} strokeWidth={Math.max(1 * u, 1.4 * u)} style={{ transform: `translateY(${lifTakip}px)` }} />
          <path d={ustAna} fill={`url(#${gradUstId})`} stroke={yumusakKenar} strokeWidth={Math.max(1.2 * u, 1.6 * u)} strokeLinejoin="round" />
          <rect width={kutu.w} height={seritH + genlik * 2} filter={`url(#${dokuId})`} opacity={0.14} clipPath={`url(#${ustMaskeId})`} />
          <path d={cizgiYol(ustN)} fill="none" stroke={rgba(vurgu, 0.72)} strokeWidth={Math.max(1.8 * u, 2.4 * u)} strokeLinecap="round" />
        </g>

        {/* Alt yırtık kağıt şeridi */}
        <g style={{ transformOrigin: `${kutu.w / 2}px ${kutu.h}px`, transform: `translateY(${-acilma}px) rotate(${egim}deg)` }}>
          <path d={altYol(kutu.w, kutu.h, altLifN)} fill={lifRenk} stroke={yumusakKenar} strokeWidth={Math.max(1 * u, 1.4 * u)} style={{ transform: `translateY(${-lifTakip}px)` }} />
          <path d={altAna} fill={`url(#${gradAltId})`} stroke={yumusakKenar} strokeWidth={Math.max(1.2 * u, 1.6 * u)} strokeLinejoin="round" />
          <rect y={kutu.h - seritH - genlik * 2} width={kutu.w} height={seritH + genlik * 2} filter={`url(#${dokuId})`} opacity={0.14} clipPath={`url(#${altMaskeId})`} />
          <path d={cizgiYol(altN)} fill="none" stroke={rgba(vurgu, 0.72)} strokeWidth={Math.max(1.8 * u, 2.4 * u)} strokeLinecap="round" />
        </g>
      </svg>
    </div>
  );
};

export default tanimla({ meta: meta as never, sema, Bilesen: Yirtik });
