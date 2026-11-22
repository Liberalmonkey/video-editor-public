// Yıldız parıltıları: tam sahnede kenar ve köşe bölgelerinde orta yüzü kapatmadan bokeh derinlik katmanlarıyla parlayıp süzülür.
import React from "react";
import { interpolate, random } from "remotion";
import { z } from "zod";
import { ikonStil, rgba, ton, useTema } from "../../../tema";
import { useAkis } from "../../cekirdek/zaman";
import { tanimla, type BilesenProps } from "../../cekirdek/tipler";
import meta from "./meta.json";

export const sema = z.strictObject({
  adet: z.number().int().min(3).max(6).default(5).describe("Parlayan yıldız sayısı (3-6)"),
  renk: z.enum(["vurgu", "ikincil", "olumlu", "olumsuz", "yazi"]).default("ikincil").describe("Ana parıltı tema rengi adı"),
  tohum: z.number().int().min(1).max(999).default(5).describe("Yıldız yerleşimi için deterministik rastgele tohum"),
});

const KIS = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const YILDIZ_YOL = "M0 -1 Q0.14 -0.14 1 0 Q0.14 0.14 0 1 Q-0.14 0.14 -1 0 Q-0.14 -0.14 0 -1 Z";

// Orta yüz bölgesini açık bırakan 6 dış kenar/köşe çerçeve bölgesi (normalize x, y).
const KENAR_BOLGELER: Array<[number, number]> = [
  [0.09, 0.14],
  [0.91, 0.15],
  [0.09, 0.68],
  [0.91, 0.67],
  [0.15, 0.83],
  [0.85, 0.82],
];

const Parilti: React.FC<BilesenProps<z.infer<typeof sema>>> = ({ param, kutu, sureKare, u }) => {
  const t = useTema();
  const a = useAkis(sureKare, meta.giris_sn, meta.cikis_sn);
  const uid = React.useId().replace(/[^a-zA-Z0-9_-]/g, "");
  const bokehId = `parilti-bokeh-${uid}`;
  const gradId = `parilti-grad-${uid}`;
  const anaRenk = t.renk[param.renk];
  const is = ikonStil(t, anaRenk, u);

  const renkler = [anaRenk, ton(anaRenk, -0.45), t.renk.vurgu];
  const minKenar = Math.min(kutu.w, kutu.h);

  const yildizlar = Array.from({ length: param.adet }, (_, i) => {
    const k = `pr-${param.tohum}-${i}`;
    const [bx, by] = KENAR_BOLGELER[i % KENAR_BOLGELER.length];
    const x = kutu.w * (bx + (random(`${k}-jx`) - 0.5) * 0.04);
    const y = kutu.h * (by + (random(`${k}-jy`) - 0.5) * 0.04) + a.nefes * (i % 2 === 0 ? -4 : 4) * u;
    const katman = i % 3; // 0: arka küçük net, 1: orta parlak, 2: ön plan yumuşak bokeh
    const boy = minKenar * (katman === 0 ? 0.028 : katman === 1 ? 0.042 : 0.056) * (0.85 + random(`${k}-s`) * 0.3);
    const renk = renkler[i % renkler.length];
    const parilti = ton(renk, -0.7);

    const bas = a.hazirlikKare + i * 3;
    const yay = a.yay(i * 3, "elastik");
    const gir = a.sirali(i, 3, "emphasis");
    const sonBas = Math.max(0, Math.min(sureKare - 2, Math.max(bas + 4, sureKare - a.cikKare - (param.adet - 1 - i) * 2)));
    const sonBit = Math.max(sonBas + 2, sureKare);
    const son = a.e.exit(interpolate(a.f, [sonBas, sonBit], [0, 1], KIS));
    const geri = i === 0 ? 1 - 0.18 * a.ters : 1;
    const olcek = Math.max(0, (0.22 * a.belir * (i === 0 ? 1 : 0) + Math.max(0, yay) * 0.92) * geri * (1 + 0.06 * a.nefes) * (1 - son));
    const don = -20 * a.ters + gir * 45 + a.nefes * 8 + son * 25;
    const op = Math.min(1, i === 0 ? a.belir : gir * 1.8) * (1 - son) * (katman === 0 ? 0.78 : katman === 2 ? 0.72 : 0.96);
    const hale = a.e.settle(interpolate(a.f, [bas + 2, bas + 13], [0, 1], KIS));

    return { x, y, boy, renk, parilti, olcek, don, op, hale, katman };
  });

  const cizYildiz = (y: (typeof yildizlar)[number], i: number) => (
    <g key={i} opacity={y.op} transform={`translate(${y.x.toFixed(1)}, ${y.y.toFixed(1)})`}>
      {/* Yumuşak radyal ışıltı halesi (sert kenarlı daire lekesi yok) */}
      <circle cx={0} cy={0} r={y.boy * (1.25 + 0.3 * y.olcek)} fill={`url(#${gradId})`} opacity={0.55} />
      <circle
        cx={0}
        cy={0}
        r={y.boy * (0.45 + y.hale * 0.85)}
        fill="none"
        stroke={rgba(y.parilti, Math.max(0, (1 - y.hale) * 0.55))}
        strokeWidth={Math.max(1.2, 1.8 * u)}
      />
      {/* Çift katmanlı 4 köşeli yıldız (dış renk + parlak iç çekirdek) */}
      <g transform={`rotate(${y.don.toFixed(1)}) scale(${(y.boy * y.olcek).toFixed(2)})`}>
        <path d={YILDIZ_YOL} fill={y.renk} />
        <path d={YILDIZ_YOL} fill={y.parilti} transform="scale(0.56)" />
      </g>
    </g>
  );

  return (
    <svg
      width={kutu.w}
      height={kutu.h}
      viewBox={`0 0 ${kutu.w} ${kutu.h}`}
      style={{
        overflow: "hidden",
        opacity: a.belir * (1 - a.cik),
      }}
    >
      <defs>
        <radialGradient id={gradId} cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor={anaRenk} stopOpacity="0.65" />
          <stop offset="45%" stopColor={anaRenk} stopOpacity="0.18" />
          <stop offset="100%" stopColor={anaRenk} stopOpacity="0" />
        </radialGradient>
        <filter id={bokehId} x="-40%" y="-40%" width="180%" height="180%">
          <feGaussianBlur stdDeviation={(2.2 * u).toFixed(2)} />
        </filter>
      </defs>

      {/* Arka plan küçük keskin yıldızlar */}
      <g>{yildizlar.filter((y) => y.katman === 0).map(cizYildiz)}</g>

      {/* Orta plan parlak stüdyo yıldızları */}
      <g style={{ filter: is.golge }}>{yildizlar.filter((y) => y.katman === 1).map(cizYildiz)}</g>

      {/* Ön plan sinematik bokeh ışık küreleri ve yumuşak yıldızlar */}
      <g filter={`url(#${bokehId})`}>{yildizlar.filter((y) => y.katman === 2).map(cizYildiz)}</g>
    </svg>
  );
};

export default tanimla({ meta: meta as never, sema, Bilesen: Parilti });
