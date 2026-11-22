import React, { useEffect, useState } from "react";
import { AbsoluteFill, continueRender, delayRender, useCurrentFrame, useVideoConfig } from "remotion";

// WHY: bkz. wiki/decisions/0039-fizik-ritim-galeri.md. Kodla çizilen konuşan karakter. Ağız kare başına viseme'den
// (vedit viseme), baş ve kol vurgu anlarından gelir. Hareket zamanın işlevidir: her kare bağımsız ve aynı çizilir.

export type KarakterTanim = {
  ad: string;
  renk: { govde: string; govde_golge: string; yuz: string; goz: string; ag: string; dil: string; yanak: string; vurgu: string };
  oran?: { en?: number; boy?: number; goz_aralik?: number; goz_r?: number };
  kas?: boolean;
};
export type KarakterVeri = { karakter: KarakterTanim; fps: number; viseme: string; vurgular: number[]; tohum: number };

// Ağız biçimleri: [genişlik, yükseklik, köşe kalkışı]. K kapalı çizgi, U yarı açık, A geniş, E yayvan, O yuvarlak.
const AGIZ: Record<string, [number, number, number]> = { K: [110, 4, 10], U: [70, 34, 4], A: [130, 112, 0], E: [168, 58, 6], O: [78, 96, 0] };

// Tohumlu rastgele (mulberry32): her render aynı kırpma zamanlarını verir.
const rastgele = (tohum: number) => () => {
  tohum |= 0; tohum = (tohum + 0x6d2b79f5) | 0;
  let t = Math.imul(tohum ^ (tohum >>> 15), 1 | tohum);
  t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
  return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
};

export const kirpmalar = (tohum: number, kare: number, fps: number): number[] => {
  const r = rastgele(tohum), cikti: number[] = [];
  for (let t = fps * (0.8 + r()); t < kare; t += fps * (2.2 + r() * 2.4)) cikti.push(Math.round(t));
  return cikti;
};

// Vurgudan sonraki sönümlü salınım: gecikme kare (follow-through), 0-1 arası tepe.
export const salinim = (n: number, vurgular: number[], gecikme = 0, fps = 30) => {
  let v = 0;
  for (const a of vurgular) {
    const d = (n - a - gecikme) / fps;
    if (d >= 0 && d < 0.9) v += Math.exp(-d * 6) * Math.sin(d * 18);
  }
  return Math.max(-1, Math.min(1, v));
};

export const agizDurumu = (viseme: string, n: number): [number, number, number] => {
  const a = AGIZ[viseme[n] ?? "K"] ?? AGIZ.K, b = AGIZ[viseme[n - 1] ?? "K"] ?? AGIZ.K;
  // Önceki kareyle %35 karışım: biçimler arası sıçrama yumuşar, açılma zamanı kaymaz.
  return [0, 1, 2].map((i) => a[i] * 0.65 + b[i] * 0.35) as [number, number, number];
};

export const KarakterCizim: React.FC<{ v: KarakterVeri; n: number }> = ({ v, n }) => {
  const { fps } = v;
  const c = v.karakter.renk;
  const en = v.karakter.oran?.en ?? 1, boy = v.karakter.oran?.boy ?? 1;
  const t = n / fps;
  const nefes = Math.sin((t / 3.1) * Math.PI * 2) * 0.012;
  const bas = salinim(n, v.vurgular, 0, fps);
  const govdeGec = salinim(n, v.vurgular, 2, fps); // gövde 2 kare geriden gelir
  const kol = salinim(n, v.vurgular, 3, fps);
  // Göz kırpma 4 kare: kapanış 2, açılış 2. İki göz aynı karede kırpar (gerçek kırpma), kaşlar bir kare farkla.
  const kirp = kirpmalar(v.tohum, n + 10, fps).reduce((m, k) => { const d = n - k; return d >= 0 && d < 4 ? Math.min(m, [0.55, 0.08, 0.35, 0.85][d]) : m; }, 1);
  const [aw, ah, akalk] = agizDurumu(v.viseme, n);
  const gozR = 34 * (v.karakter.oran?.goz_r ?? 1), gozA = 92 * (v.karakter.oran?.goz_aralik ?? 1);
  const bakis = Math.sin(t * 0.7) * 6;
  const gw = 300 * en, gh = 340 * boy;
  return (
    <svg viewBox="0 0 1000 1000" style={{ width: "100%", height: "100%", overflow: "visible" }}>
      <ellipse cx={500} cy={905} rx={gw * (0.82 - nefes * 4)} ry={26} fill="#000" opacity={0.22} />
      <g transform={`translate(500 900) rotate(${govdeGec * -2.5}) scale(${1 + nefes * 0.5 - govdeGec * 0.015} ${1 - nefes + govdeGec * 0.02}) translate(-500 -900)`}>
        {/* Kollar: sol kol vurguda kalkar; sağ kol bir kare geriden ve daha az (ikizleme yok). */}
        <path d={`M ${500 - gw * 0.92} 660 q ${-70} ${60 - kol * 150} ${-40} ${150 - kol * 260}`} stroke={c.govde_golge} strokeWidth={46} strokeLinecap="round" fill="none" />
        <path d={`M ${500 + gw * 0.92} 660 q 70 ${60 - salinim(n, v.vurgular, 4, fps) * 60} 40 150`} stroke={c.govde_golge} strokeWidth={46} strokeLinecap="round" fill="none" />
        <defs><clipPath id={`govde-${v.tohum}`}><ellipse cx={500} cy={900 - gh} rx={gw} ry={gh} /></clipPath></defs>
        <ellipse cx={500} cy={900 - gh} rx={gw} ry={gh} fill={c.govde} />
        {/* Gölge gövdeye kırpılır: ışık sol üstten, gölge sağ altta, silüetin dışına taşmaz. */}
        <ellipse cx={500 + gw * 0.25} cy={900 - gh * 0.55} rx={gw * 0.55} ry={gh * 0.7} fill={c.govde_golge} opacity={0.35} clipPath={`url(#govde-${v.tohum})`} />
        <g transform={`translate(500 ${900 - gh * 1.15}) rotate(${bas * 5}) translate(-500 ${-(900 - gh * 1.15)})`}>
          <ellipse cx={500} cy={900 - gh * 1.15} rx={gw * 0.74} ry={gh * 0.5} fill={c.yuz} />
          {[-1, 1].map((y) => (
            <g key={y}>
              <rect x={500 + y * gozA - 40} y={900 - gh * 1.42 - Math.max(0, bas) * 10 - (y > 0 ? salinim(n, v.vurgular, 1, fps) * 6 : 0)} width={80} height={12} rx={6} fill={c.goz} opacity={0.85} />
              <ellipse cx={500 + y * gozA} cy={900 - gh * 1.22} rx={gozR} ry={gozR * 1.15 * kirp} fill="#fff" />
              <circle cx={500 + y * gozA + bakis} cy={900 - gh * 1.22 + 4} r={gozR * 0.55 * Math.min(1, kirp * 1.6)} fill={c.goz} />
              <ellipse cx={500 + y * (gozA + 60)} cy={900 - gh * 1.02} rx={34} ry={18} fill={c.yanak} opacity={0.5} />
            </g>
          ))}
          {ah < 8
            ? <path d={`M ${500 - aw / 2} ${900 - gh * 0.98} Q 500 ${900 - gh * 0.98 + akalk + 8} ${500 + aw / 2} ${900 - gh * 0.98}`} stroke={c.ag} strokeWidth={12} strokeLinecap="round" fill="none" />
            : <g>
              <ellipse cx={500} cy={900 - gh * 0.98 + ah / 2 - 6} rx={aw / 2} ry={ah / 2} fill={c.ag} />
              <ellipse cx={500} cy={900 - gh * 0.98 + ah * 0.78 - 6} rx={aw * 0.3} ry={ah * 0.2} fill={c.dil} />
            </g>}
        </g>
      </g>
    </svg>
  );
};

export const KarakterSahne: React.FC<{ url: string; s: Record<string, any> }> = ({ url, s }) => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();
  const [v, setV] = useState<KarakterVeri | null>(null);
  const [h] = useState(() => delayRender(`karakter ${url}`));
  useEffect(() => {
    let iptal = false;
    fetch(url).then((r) => r.json()).then((j) => { if (!iptal) setV(j); }).finally(() => continueRender(h));
    return () => { iptal = true; };
  }, [url, h]);
  if (!v) return null;
  const boyut = Math.min(width, height) * (s.olcek ?? 0.78);
  const zemin = s.bg === "saydam" ? "transparent" : s.zemin ?? v.karakter.renk.vurgu;
  return (
    <AbsoluteFill style={{ background: zemin, alignItems: "center", justifyContent: "flex-end" }}>
      <div style={{ width: boyut, height: boyut, marginBottom: height * (width > height ? 0.04 : 0.24) }}>
        <KarakterCizim v={v} n={frame} />
      </div>
    </AbsoluteFill>
  );
};
