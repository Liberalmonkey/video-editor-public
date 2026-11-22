// Konfeti patlaması: tam sahnede sol/sağ alt ve üst köşelerden fırlayıp orta yüz bölgesini kapatmadan sinematik bokeh derinlik katmanlarıyla süzülür.
import React from "react";
import { interpolate, random } from "remotion";
import { z } from "zod";
import { ikonStil, ton, useTema } from "../../../tema";
import { useAkis } from "../../cekirdek/zaman";
import { tanimla, type BilesenProps } from "../../cekirdek/tipler";
import meta from "./meta.json";

export const sema = z.strictObject({
  adet: z.number().int().min(40).max(80).default(58).describe("Konfeti parça sayısı (40-80)"),
  tohum: z.number().int().min(1).max(999).default(11).describe("Parçaların dağılımı ve hızı için deterministik tohum"),
  renk: z.enum(["vurgu", "ikincil", "olumlu", "olumsuz", "yazi"]).default("vurgu").describe("Baskın vurgu tema rengi adı"),
});

const KIS = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

const Konfeti: React.FC<BilesenProps<z.infer<typeof sema>>> = ({ param, kutu, sureKare, u }) => {
  const t = useTema();
  const a = useAkis(sureKare, meta.giris_sn, meta.cikis_sn);
  const uid = React.useId().replace(/[^a-zA-Z0-9_-]/g, "");
  const bokehId = `konfeti-bokeh-${uid}`;
  const anaRenk = t.renk[param.renk];
  const is = ikonStil(t, anaRenk, u);

  const palet = [
    anaRenk,
    t.renk.ikincil,
    t.renk.olumlu,
    ton(anaRenk, -0.45),
    t.renk.yazi,
  ];

  const tSn = Math.max(0, (a.f - a.hazirlikKare) / a.fps);
  const sonBas = Math.max(0, Math.min(sureKare - 3, Math.max(a.girKare + 2, sureKare - a.cikKare - 8)));
  const sonBit = Math.max(sonBas + 2, sureKare - 1);
  const sonlanma = a.e.exit(interpolate(a.f, [sonBas, sonBit], [0, 1], KIS));

  // Dört köşe fırlatıcı: sol-alt, sağ-alt (ana toplar), sol-üst, sağ-üst (çerçeve serpme).
  const parcalar = Array.from({ length: param.adet }, (_, i) => {
    const k = `k-${param.tohum}-${i}`;
    // 0: sol-alt (%35), 1: sağ-alt (%35), 2: sol-üst (%15), 3: sağ-üst (%15)
    const koseZar = random(`${k}-ks`);
    const kose = koseZar < 0.35 ? 0 : koseZar < 0.7 ? 1 : koseZar < 0.85 ? 2 : 3;

    // 3 sinematik derinlik katmanı: 0 arka plan (küçük net), 1 orta plan (canlı net), 2 ön plan bokeh (büyük hafif bulanık)
    const katmanZar = random(`${k}-dp`);
    const katman = katmanZar < 0.35 ? 0 : katmanZar < 0.8 ? 1 : 2;
    const derinlikOlcek = katman === 0 ? 0.62 : katman === 1 ? 1.0 : 1.55;
    const hizDerinlik = katman === 0 ? 0.76 : katman === 1 ? 1.0 : 1.24;

    const solMu = kose === 0 || kose === 2;
    const altMi = kose === 0 || kose === 1;

    const basX = solMu ? kutu.w * (0.02 + random(`${k}-bx`) * 0.08) : kutu.w * (0.98 - random(`${k}-bx`) * 0.08);
    const basY = altMi
      ? kutu.h * (0.94 - random(`${k}-by`) * 0.1) + 14 * u * a.ters
      : kutu.h * (0.04 + random(`${k}-by`) * 0.08) - 10 * u * a.ters;

    // Kenar koridorlarına doğru kavisli fırlatma açıları (ekranın orta yüz bölgesini kapatmaz)
    const hizKat = (0.72 + random(`${k}-v`) * 0.75) * hizDerinlik;
    let aci: number;
    if (kose === 0) {
      // Sol-alt: dik yukarı ve hafif sağ-yukarı (-86° .. -50°)
      aci = -Math.PI * (0.48 - random(`${k}-a`) * 0.2);
    } else if (kose === 1) {
      // Sağ-alt: dik yukarı ve hafif sol-yukarı (-130° .. -94°)
      aci = -Math.PI * (0.52 + random(`${k}-a`) * 0.2);
    } else if (kose === 2) {
      // Sol-üst: aşağı-sağa süzülme (28° .. 72°)
      aci = Math.PI * (0.16 + random(`${k}-a`) * 0.24);
    } else {
      // Sağ-üst: aşağı-sola süzülme (108° .. 152°)
      aci = Math.PI * (0.6 + random(`${k}-a`) * 0.24);
    }

    const vx = Math.cos(aci) * kutu.w * (altMi ? 0.42 : 0.32) * hizKat;
    const vy = Math.sin(aci) * kutu.h * (altMi ? 0.96 : 0.48) * hizKat;

    const suruk = 1.9 + random(`${k}-d`) * 1.1;
    const s = (1 - Math.exp(-suruk * tSn)) / suruk;
    const yercekimi = kutu.h * (altMi ? 0.42 : 0.34);
    const dusus = (yercekimi * (tSn - s)) / suruk;

    const faz = random(`${k}-p`) * Math.PI * 2;
    const salinimFrek = 4.6 + random(`${k}-f`) * 4.4;
    const salinimGen = (10 + random(`${k}-g`) * 14) * u * derinlikOlcek;
    const salinimKat = Math.min(1, tSn * 2.4);

    const x = basX + vx * s + Math.sin(tSn * salinimFrek + faz) * salinimGen * salinimKat;
    const y = basY + vy * s + dusus;

    const don0 = random(`${k}-r0`) * 360;
    const donHiz = (random(`${k}-rv`) - 0.5) * 520;
    const don = don0 + donHiz * tSn;
    const taklaHiz = 5.0 + random(`${k}-tk`) * 7.5;
    const taklaY = 0.38 + 0.62 * Math.abs(Math.cos(tSn * taklaHiz + faz));

    // Orta yüz bölgesine (elips x: 0.28..0.72, y: 0.22..0.66) giren kaçak parçaları yumuşakça saydamlaştır
    const nx = (x / Math.max(1, kutu.w) - 0.5) / 0.23;
    const ny = (y / Math.max(1, kutu.h) - 0.44) / 0.24;
    const yuzMesafe = Math.hypot(nx, ny);
    const yuzKacis = interpolate(yuzMesafe, [0.7, 1.25], [0.16, 1], KIS);

    const olcek = derinlikOlcek * (0.4 + 0.6 * a.gir) * (1 - 0.18 * a.ters);
    const w = (18 + random(`${k}-w`) * 12) * u;
    const h = (10 + random(`${k}-h`) * 5.5) * u;
    const sekil = Math.floor(random(`${k}-sh`) * 3);
    const renk = palet[Math.floor(random(`${k}-c`) * palet.length)];
    const parlak = ton(renk, -0.48, 0.72);
    const tabanOp = katman === 0 ? 0.72 : katman === 1 ? 0.94 : 0.82;
    const parcaOp = Math.max(0, 1 - sonlanma * (0.85 + random(`${k}-op`) * 0.35)) * tabanOp * yuzKacis;

    return { x, y, don, taklaY, olcek, w, h, sekil, renk, parlak, parcaOp, katman };
  });

  const cizParca = (p: (typeof parcalar)[number], i: number) => (
    <g
      key={i}
      opacity={p.parcaOp}
      transform={`translate(${p.x.toFixed(1)}, ${p.y.toFixed(1)}) rotate(${p.don.toFixed(1)}) scale(${p.olcek.toFixed(3)}, ${(p.olcek * p.taklaY).toFixed(3)})`}
    >
      {p.sekil === 0 && (
        <>
          <rect x={-p.w / 2} y={-p.h / 2} width={p.w} height={p.h} rx={2.5 * u} fill={p.renk} />
          <rect x={-p.w * 0.42} y={-p.h * 0.36} width={p.w * 0.84} height={p.h * 0.26} rx={1.2 * u} fill={p.parlak} />
        </>
      )}
      {p.sekil === 1 && (
        <>
          <rect x={-p.w * 0.64} y={-p.h / 2} width={p.w * 1.28} height={p.h} rx={p.h * 0.5} fill={p.renk} />
          <rect x={-p.w * 0.5} y={-p.h * 0.32} width={p.w} height={p.h * 0.24} rx={p.h * 0.12} fill={p.parlak} />
        </>
      )}
      {p.sekil === 2 && (
        <>
          <circle cx={0} cy={0} r={Math.max(p.h * 0.65, 8 * u)} fill={p.renk} />
          <circle cx={-p.h * 0.18} cy={-p.h * 0.18} r={Math.max(p.h * 0.24, 3 * u)} fill={p.parlak} />
        </>
      )}
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
        <filter id={bokehId} x="-20%" y="-20%" width="140%" height="140%">
          <feGaussianBlur stdDeviation={(2.8 * u).toFixed(2)} />
        </filter>
      </defs>

      {/* Arka plan: küçük ve net derinlik parçacıkları */}
      <g>{parcalar.filter((p) => p.katman === 0).map(cizParca)}</g>

      {/* Orta plan: canlı ve parlak ana konfeti katmanı */}
      <g style={{ filter: is.golge }}>{parcalar.filter((p) => p.katman === 1).map(cizParca)}</g>

      {/* Ön plan: sinematik bokeh (büyük, hafif bulanık kenar derinliği) */}
      <g filter={`url(#${bokehId})`}>{parcalar.filter((p) => p.katman === 2).map(cizParca)}</g>
    </svg>
  );
};

export default tanimla({ meta: meta as never, sema, Bilesen: Konfeti });
