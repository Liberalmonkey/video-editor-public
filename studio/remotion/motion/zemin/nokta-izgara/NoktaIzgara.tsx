// Nokta ızgara zemini: iki katmanlı paralaks nokta matrisi, tema renkleriyle düşük kontrastlı yavaş sürüklenme.
import React, { useId } from "react";
import { z } from "zod";
import { rgba, useTema } from "../../../tema";
import { useAkis } from "../../cekirdek/zaman";
import { tanimla, type BilesenProps } from "../../cekirdek/tipler";
import meta from "./meta.json";

export const sema = z.strictObject({
  renk: z.enum(["vurgu", "ikincil", "olumlu", "olumsuz", "yazi"]).default("vurgu").describe("İkincil paralaks nokta katmanı tema rengi adı"),
  aralik: z.number().min(28).max(96).default(48).describe("Nokta aralığı (1080p piksel)"),
  hiz: z.number().min(0).max(2).default(1).describe("Yavaş sürüklenme hız katsayısı"),
});

const NoktaIzgara: React.FC<BilesenProps<z.infer<typeof sema>>> = ({ param, kutu, sureKare, u }) => {
  const t = useTema();
  const a = useAkis(sureKare, meta.giris_sn, meta.cikis_sn);
  const uid = useId().replace(/[^a-zA-Z0-9_-]/g, "");
  const vurgu = t.renk[param.renk];

  const tSn = a.f / a.fps;
  const otur = a.takip(a.hazirlikKare + 2, 140);
  // Anticipation: a.ters ile noktalar çok hafif küçülür, sonra yerine oturur.
  const capKat = (1 - 0.22 * a.ters) * (0.72 + 0.28 * Math.min(1.05, Math.max(0, otur)));

  const adim1 = Math.max(20, Math.round(param.aralik * u));
  const adim2 = adim1 * 3;
  const r1 = Math.max(2.4 * u, 3.4 * u) * capKat;
  const r2 = Math.max(3.6 * u, 5.0 * u) * capKat;

  const dx1 = ((tSn * 14 * param.hiz * u) % adim1 + adim1) % adim1;
  const dy1 = ((tSn * 9 * param.hiz * u) % adim1 + adim1) % adim1;
  const dx2 = ((-tSn * 8 * param.hiz * u) % adim2 + adim2) % adim2;
  const dy2 = ((tSn * 6 * param.hiz * u) % adim2 + adim2) % adim2;

  const nefes = 0.9 + 0.1 * Math.sin(tSn * 1.15);
  const kat1Id = `zemin-nokta-1-${uid}`;
  const kat2Id = `zemin-nokta-2-${uid}`;
  const vinyetId = `zemin-nokta-v-${uid}`;

  return (
    <div
      style={{
        position: "relative",
        width: kutu.w,
        height: kutu.h,
        overflow: "hidden",
        background: t.renk.zemin,
        opacity: a.belir * (1 - a.cik),
      }}
    >
      <svg width={kutu.w} height={kutu.h} viewBox={`0 0 ${kutu.w} ${kutu.h}`} style={{ position: "absolute", inset: 0 }}>
        <defs>
          <pattern
            id={kat1Id}
            width={adim1}
            height={adim1}
            patternUnits="userSpaceOnUse"
            patternTransform={`translate(${dx1.toFixed(2)} ${dy1.toFixed(2)})`}
          >
            <circle cx={adim1 / 2} cy={adim1 / 2} r={r1} fill={rgba(t.renk.yazi, 0.26 * nefes)} />
          </pattern>

          <pattern
            id={kat2Id}
            width={adim2}
            height={adim2}
            patternUnits="userSpaceOnUse"
            patternTransform={`translate(${dx2.toFixed(2)} ${dy2.toFixed(2)})`}
          >
            <circle cx={adim2 * 0.25} cy={adim2 * 0.25} r={r2} fill={rgba(vurgu, 0.3)} />
            <circle cx={adim2 * 0.75} cy={adim2 * 0.75} r={r2 * 0.82} fill={rgba(t.renk.ikincil, 0.24)} />
          </pattern>

          <radialGradient id={vinyetId} cx="50%" cy="50%" r="74%">
            <stop offset="56%" stopColor={t.renk.zemin} stopOpacity={0} />
            <stop offset="100%" stopColor={t.renk.zemin} stopOpacity={0.36} />
          </radialGradient>
        </defs>

        <rect width={kutu.w} height={kutu.h} fill={`url(#${kat1Id})`} />
        <rect width={kutu.w} height={kutu.h} fill={`url(#${kat2Id})`} />
        <rect width={kutu.w} height={kutu.h} fill={`url(#${vinyetId})`} />
      </svg>
    </div>
  );
};

export default tanimla({ meta: meta as never, sema, Bilesen: NoktaIzgara });
