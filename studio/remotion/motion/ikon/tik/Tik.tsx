// Onay tiki: çok katmanlı duotone hacim, rafine kontur, üst parlama vurgusu ve uçta kıvılcım çizgileriyle çizilip yayla oturur.
// Geometri: Lucide "check" (ISC, https://lucide.dev/icons/check), 24 birimlik viewBox.
import React from "react";
import { z } from "zod";
import { ikonStil, useTema } from "../../../tema";
import { KONTUR_EK, ikonKalinlik } from "../../cekirdek/olcu";
import { cizgiOfset, useAkis } from "../../cekirdek/zaman";
import { tanimla, type BilesenProps } from "../../cekirdek/tipler";
import meta from "./meta.json";

export const sema = z.strictObject({
  renk: z.enum(["olumlu", "vurgu", "ikincil", "olumsuz", "yazi"]).default("olumlu").describe("Tema rengi adı; onaltılık renk yazılmaz"),
});

const YOL = "M20 6 9 17l-5-5";
const UZUNLUK = 22.7; // yolun uzunluğu (11√2 + 5√2 ≈ 22.63), payla
const KIVILCIMLAR: Array<[number, number, number, number]> = [
  [20.2, 4.1, 21.8, 2.3],
  [21.7, 6.2, 23.6, 5.7],
  [18.2, 3.6, 18.6, 1.6],
];

const Tik: React.FC<BilesenProps<z.infer<typeof sema>>> = ({ param, kutu, sureKare, u }) => {
  const t = useTema();
  const a = useAkis(sureKare, meta.giris_sn, meta.cikis_sn);
  // Hazırlık: kısa kol görünür, sol-alta çekilir (ana çizimin tersi); sonra uzun kol sağ-üste atılır.
  const ciz = 0.22 * a.belir + 0.78 * a.gir;
  const yay = a.yay(0, "elastik");
  const otur = a.takip(a.girKare - 2, 160);
  const kivilcim = Math.max(0, Math.min(1, a.vurgu(a.girKare - 2, Math.round(0.32 * a.fps))));
  const kivilcimOp = Math.sin(kivilcim * Math.PI) * (1 - a.cik);
  const geri = -0.05 * kutu.w * a.ters;
  const olcek = (1 - 0.1 * a.ters) * (0.9 + 0.1 * Math.min(1.08, yay)) * (0.96 + 0.04 * otur) * (1 + 0.02 * a.nefes) * (1 - 0.35 * a.cik);
  const cizgi = ikonKalinlik(t, kutu, u, 24);
  const renk = t.renk[param.renk];
  const is = ikonStil(t, renk, u);
  const blur = a.hizBulaniklik > 0.08 ? `blur(${(a.hizBulaniklik * 0.4 * u).toFixed(2)}px) ` : "";
  const ofset = cizgiOfset(UZUNLUK, ciz);

  return (
    <svg
      viewBox="0 0 24 24"
      width={kutu.w}
      height={kutu.h}
      style={{
        overflow: "visible",
        opacity: a.belir * (1 - a.cik),
        transform: `translate(${geri}px, ${-geri + a.nefes * -1.4 * u}px) scale(${olcek})`,
        filter: `${blur}${is.golge}`,
      }}
    >
      {/* Katman 1: yumuşak duotone hacim gölgesi */}
      <path
        d={YOL}
        fill="none"
        stroke={is.dolgu}
        strokeWidth={cizgi * 1.48}
        strokeLinecap="round"
        strokeLinejoin="round"
        transform="translate(0.35 0.55)"
        strokeDasharray={UZUNLUK}
        strokeDashoffset={ofset}
      />
      {/* Katman 2: rafine koyu kontur + canlı ana çizgi + ince üst parlama vurgusu */}
      <path
        d={YOL}
        fill="none"
        stroke={is.kontur}
        strokeWidth={cizgi + KONTUR_EK}
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeOpacity={0.9}
        strokeDasharray={UZUNLUK}
        strokeDashoffset={ofset}
      />
      <path
        d={YOL}
        fill="none"
        stroke={is.vurgu}
        strokeWidth={cizgi}
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeDasharray={UZUNLUK}
        strokeDashoffset={ofset}
      />
      <path
        d={YOL}
        fill="none"
        stroke={is.parilti}
        strokeWidth={cizgi * 0.28}
        strokeLinecap="round"
        strokeLinejoin="round"
        transform="translate(-0.22 -0.26)"
        opacity={0.78 * a.gir}
        strokeDasharray={UZUNLUK}
        strokeDashoffset={ofset}
      />
      {/* Katman 3: uçtan fırlayan onay kıvılcım çizgileri */}
      {kivilcimOp > 0.01 &&
        KIVILCIMLAR.map(([x1, y1, x2, y2], i) => {
          const ax = x1 + (x2 - x1) * (0.25 * kivilcim);
          const ay = y1 + (y2 - y1) * (0.25 * kivilcim);
          const bx = x1 + (x2 - x1) * (0.4 + 0.75 * kivilcim);
          const by = y1 + (y2 - y1) * (0.4 + 0.75 * kivilcim);
          return (
            <line
              key={i}
              x1={ax}
              y1={ay}
              x2={bx}
              y2={by}
              stroke={i === 0 ? is.parilti : is.vurgu}
              strokeWidth={cizgi * 0.32}
              strokeLinecap="round"
              opacity={kivilcimOp}
            />
          );
        })}
    </svg>
  );
};

export default tanimla({ meta: meta as never, sema, Bilesen: Tik });
