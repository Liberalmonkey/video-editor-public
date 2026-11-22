// Yıldız patlama: merkezden dışa fırlayan çok katmanlı ışınlar, yumuşak glow çekirdeği ve parlayan uç kıvılcımlarıyla açılır.
import React from "react";
import { interpolate, random } from "remotion";
import { z } from "zod";
import { ikonStil, rgba, ton, useTema } from "../../../tema";
import { useAkis } from "../../cekirdek/zaman";
import { tanimla, type BilesenProps } from "../../cekirdek/tipler";
import meta from "./meta.json";

export const sema = z.strictObject({
  isin: z.number().int().min(8).max(18).default(12).describe("Merkezden dışa fırlayan ışın sayısı (8-18)"),
  renk: z.enum(["vurgu", "ikincil", "olumlu", "olumsuz", "yazi"]).default("vurgu").describe("Ana ışın tema rengi adı"),
  tohum: z.number().int().min(1).max(999).default(3).describe("Işın uzunluğu ve açı varyasyonu için deterministik tohum"),
});

const KIS = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

const YildizPatlama: React.FC<BilesenProps<z.infer<typeof sema>>> = ({ param, kutu, sureKare, u }) => {
  const t = useTema();
  const a = useAkis(sureKare, meta.giris_sn, meta.cikis_sn);
  const uid = React.useId().replace(/[^a-zA-Z0-9_-]/g, "");
  const glowId = `yp-glow-${uid}`;

  const cx = kutu.w / 2;
  const cy = kutu.h / 2;
  const maxR = Math.min(kutu.w, kutu.h) * 0.46;
  const patlamaSure = Math.max(14, Math.round(sureKare * 0.82));
  const anaRenk = t.renk[param.renk];
  const is = ikonStil(t, anaRenk, u);
  const yay = a.yay(0, "elastik");
  const patlamaOlcek = (0.94 + 0.06 * Math.max(0, Math.min(1.08, yay))) * (1 + 0.015 * a.nefes);
  const merkezParla = Math.sin(Math.min(1, a.gir) * Math.PI) * (1 - a.cik);

  const isinlar = Array.from({ length: param.isin }, (_, i) => {
    const k = `yp-${param.tohum}-${i}`;
    const uzunMu = i % 2 === 0;
    const sapma = (random(`${k}-a`) - 0.5) * (Math.PI / param.isin) * 0.45;
    const aci = (i / param.isin) * Math.PI * 2 + sapma;
    const hedefR = maxR * (uzunMu ? 0.88 + random(`${k}-l`) * 0.12 : 0.66 + random(`${k}-l`) * 0.14);

    const gecikme = uzunMu ? 0 : 3;
    const basKare = a.hazirlikKare + gecikme;
    const ucBit = Math.max(basKare + 4, basKare + Math.round(patlamaSure * 0.46));
    const kuyrukBas = basKare + 4;
    const kuyrukBit = Math.max(kuyrukBas + 8, Math.min(sureKare, basKare + patlamaSure));
    const uc = a.e.enter(interpolate(a.f, [basKare, ucBit], [0, 1], KIS));
    const kuyruk = a.e.exit(interpolate(a.f, [kuyrukBas, kuyrukBit], [0, 1], KIS));

    const basR = Math.max(6 * u, 18 * u * (1 - 0.4 * a.ters));
    const r1 = basR + (hedefR - basR) * kuyruk;
    const r2 = Math.max(r1, basR + (hedefR - basR) * (0.14 * a.belir + 0.86 * uc));

    const kal = Math.max(4.2 * u, (uzunMu ? 10 : 6.8) * u * (1 - kuyruk * 0.42));
    const renk = uzunMu ? anaRenk : t.renk.ikincil;
    const iIs = ikonStil(t, renk, u);
    const op = Math.min(1, a.belir * (uzunMu ? 1 : 0.94)) * (1 - Math.pow(kuyruk, 2.4));

    const noktaBit = Math.max(basKare + 8, sureKare - a.cikKare);
    const noktaIlerle = a.e.settle(interpolate(a.f, [basKare + 3, noktaBit], [0, 1], KIS));
    const noktaR = basR + hedefR * (0.38 + 0.66 * noktaIlerle);
    const noktaOp = uzunMu ? Math.min(1, noktaIlerle * 3) * (1 - 0.18 * noktaIlerle) : 0;

    return { aci, r1, r2, kal, renk, iIs, op, noktaR, noktaOp };
  });

  return (
    <svg
      width={kutu.w}
      height={kutu.h}
      viewBox={`0 0 ${kutu.w} ${kutu.h}`}
      style={{
        overflow: "visible",
        filter: is.golge,
        opacity: a.belir * (1 - a.cik),
        transformOrigin: "center center",
        transform: `scale(${patlamaOlcek})`,
      }}
    >
      <defs>
        <filter id={glowId} x="-40%" y="-40%" width="180%" height="180%">
          <feGaussianBlur stdDeviation={(5 * u).toFixed(2)} />
        </filter>
      </defs>

      {/* Yumuşak merkez patlama ışıltısı */}
      {merkezParla > 0.02 && (
        <circle cx={cx} cy={cy} r={maxR * 0.24 * (0.6 + 0.6 * a.gir)} fill={rgba(anaRenk, 0.32 * merkezParla)} filter={`url(#${glowId})`} />
      )}

      {isinlar.map((s, i) => {
        const cos = Math.cos(s.aci);
        const sin = Math.sin(s.aci);
        const x1 = cx + cos * s.r1;
        const y1 = cy + sin * s.r1;
        const x2 = cx + cos * s.r2;
        const y2 = cy + sin * s.r2;
        return (
          <g key={i}>
            {/* Yumuşak ışık kılıfı */}
            <line x1={x1} y1={y1} x2={x2} y2={y2} stroke={s.iIs.dolgu} strokeWidth={s.kal * 1.95} strokeLinecap="round" opacity={s.op * 0.78} />
            {/* Canlı ana ışın */}
            <line x1={x1} y1={y1} x2={x2} y2={y2} stroke={s.renk} strokeWidth={s.kal} strokeLinecap="round" opacity={s.op} />
            {/* Parlak iç çekirdek çizgisi */}
            <line x1={x1} y1={y1} x2={x2} y2={y2} stroke={s.iIs.parilti} strokeWidth={Math.max(1.8 * u, s.kal * 0.3)} strokeLinecap="round" opacity={s.op * 0.9} />
            {s.noktaOp > 0.01 && (
              <g opacity={s.noktaOp}>
                <circle cx={cx + cos * s.noktaR} cy={cy + sin * s.noktaR} r={Math.max(7 * u, 10 * u * s.noktaOp)} fill={rgba(s.renk, 0.34)} />
                <circle cx={cx + cos * s.noktaR} cy={cy + sin * s.noktaR} r={Math.max(3.5 * u, 5 * u * s.noktaOp)} fill={ton(s.renk, -0.62)} />
              </g>
            )}
          </g>
        );
      })}
    </svg>
  );
};

export default tanimla({ meta: meta as never, sema, Bilesen: YildizPatlama });
