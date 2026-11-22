// El çizimi call-out lider çizgisi: organik kalem çizgisi, yumuşak ikonStil gölgesi ve raf ucunda yuzeyStil rozet etiketi + parlama şeridi.
// Geometri: Özgün hedefe bağlı deterministik el çizimi SVG yolu (remotion random).
import React from "react";
import { random } from "remotion";
import { z } from "zod";
import { harf, ikonStil, parlamaStil, rgba, ton, useTema, yigin, yuzeyStil, yuzeyYazi } from "../../../tema";
import { ikonKalinlik } from "../../cekirdek/olcu";
import { cizgiOfset, useAkis } from "../../cekirdek/zaman";
import { tanimla, type BilesenProps } from "../../cekirdek/tipler";
import meta from "./meta.json";

export const sema = z.strictObject({
  renk: z.enum(["vurgu", "ikincil", "olumlu", "olumsuz", "yazi"]).default("vurgu").describe("Tema rengi adı; onaltılık renk yazılmaz"),
  etiket: z.string().max(26).default("").describe("Çağrı rafı ucundaki isteğe bağlı kısa rozet etiketi"),
});

const sapma = (tohum: string, genlik: number) => (random(tohum) - 0.5) * 2 * genlik;

const kubikUz = (p0: [number, number], p1: [number, number], p2: [number, number], p3: [number, number]) => {
  let uz = 0;
  let [ox, oy] = p0;
  for (let i = 1; i <= 16; i++) {
    const t = i / 16;
    const m = 1 - t;
    const x = m * m * m * p0[0] + 3 * m * m * t * p1[0] + 3 * m * t * t * p2[0] + t * t * t * p3[0];
    const y = m * m * m * p0[1] + 3 * m * m * t * p1[1] + 3 * m * t * t * p2[1] + t * t * t * p3[1];
    uz += Math.hypot(x - ox, y - oy);
    ox = x;
    oy = y;
  }
  return uz;
};

const Cagri: React.FC<BilesenProps<z.infer<typeof sema>>> = ({ param, kutu, hedef, sureKare, u }) => {
  const t = useTema();
  const a = useAkis(sureKare, meta.giris_sn, meta.cikis_sn);
  const w = Math.max(1, kutu.w);
  const h = Math.max(1, kutu.h);

  const hx = hedef ? hedef.x : w * 0.5;
  const hy = hedef ? hedef.y : h * 0.92;
  const rafY = hedef ? h * 0.5 : h * 0.24;
  const xSol = w * 0.14;
  const xSag = w * 0.86;
  const soldanMi = hedef ? hx <= w * 0.5 : true;
  const dirsekX = hedef ? (soldanMi ? xSol : xSag) : w * 0.62;
  const rafSonX = hedef ? (soldanMi ? xSag : xSol) : w * 0.92;

  const j = (ad: string, g = 4.5) => sapma(`cizim-cagri-${ad}`, g * u);
  const dx = dirsekX - hx;
  const dy = rafY - hy;
  const mesafe = Math.max(1, Math.hypot(dx, dy));
  const nx = -dy / mesafe;
  const ny = dx / mesafe;
  const kavisYon = ny <= 0 ? 1 : -1;
  const kavis = Math.min(mesafe * 0.26, 68 * u) * kavisYon;
  const rafYon = rafSonX > dirsekX ? 1 : -1;
  const k1: [number, number] = [hx + dx * 0.34 + nx * kavis + j("k1x"), hy + dy * 0.34 + ny * kavis + j("k1y")];
  const ayniYon = dx * rafYon >= 0;
  const k2: [number, number] = ayniYon
    ? [dirsekX - rafYon * Math.min(mesafe * 0.24, 44 * u) + j("k2x"), rafY + j("k2y", 3.5)]
    : [hx + dx * 0.72 + nx * kavis * 0.45 + j("k2x"), hy + dy * 0.72 + ny * kavis * 0.45 + j("k2y", 3.5)];
  const pBas: [number, number] = [hx, hy];
  const pDirsek: [number, number] = [dirsekX + j("dx", 2.5), rafY + j("dy", 2.5)];
  const pRafOrta: [number, number] = [(pDirsek[0] + rafSonX) / 2 + j("rx", 3), rafY + j("ry", 3.5)];
  const pRafSon: [number, number] = [rafSonX + j("sx", 2.5), rafY + j("sy", 2.5)];

  const f = (p: [number, number]) => `${p[0].toFixed(1)} ${p[1].toFixed(1)}`;
  const yol = `M ${f(pBas)} C ${f(k1)} ${f(k2)} ${f(pDirsek)} Q ${f(pRafOrta)} ${f(pRafSon)}`;
  const rafUz = Math.hypot(pRafOrta[0] - pDirsek[0], pRafOrta[1] - pDirsek[1]) + Math.hypot(pRafSon[0] - pRafOrta[0], pRafSon[1] - pRafOrta[1]);
  const yolUz = Math.ceil((kubikUz(pBas, k1, k2, pDirsek) + rafUz) * 1.06);

  const noktaYay = a.yay(0, "elastik");
  const noktaOlcek = (1 - 0.24 * a.ters) * (0.76 + 0.24 * Math.max(0, noktaYay)) * (1 + 0.04 * a.nefes) * (1 - a.cik);
  const pCizgi = a.sirali(1, 3, "enter");
  const rozetYay = a.yay(Math.max(2, a.girKare - a.hazirlikKare - 2), "keskin");
  const halkaP = Math.max(0, Math.min(1, a.vurgu(a.hazirlikKare + 1, Math.round(0.32 * a.fps))));

  const ref = 0.26 * 1080 * u;
  const cizgi = ikonKalinlik(t, { x: 0, y: 0, w: ref, h: ref }, u, ref) * 0.72;
  const noktaR = cizgi * 0.88;
  const halkaR = noktaR * (1.3 + 2.0 * halkaP);
  const halkaOpak = (1 - halkaP) * Math.min(1, halkaP * 6) * (1 - a.cik);
  const cizgiIlerle = Math.max(0, pCizgi * (1 - a.cik));
  const renk = t.renk[param.renk];
  const is = ikonStil(t, renk, u);
  const blur = a.hizBulaniklik > 0.08 ? `blur(${(a.hizBulaniklik * 0.35 * u).toFixed(2)}px) ` : "";
  const etiketTemiz = param.etiket.trim();
  const etiketBoy = Math.max(28 * u, Math.round(30 * u));
  const rozetYuzey = yuzeyStil(t, u, "rozet");
  const rozetOlcek = Math.max(0, Math.min(1.06, rozetYay)) * (1 - a.cik);

  return (
    <div style={{ position: "relative", width: w, height: h, overflow: "visible" }}>
      <svg
        viewBox={`0 0 ${w} ${h}`}
        width={w}
        height={h}
        style={{
          overflow: "visible",
          opacity: a.belir * (1 - a.cik * 0.85),
          filter: `${blur}${is.golge}`,
        }}
      >
        {/* Yumuşak genişleyen odak halkası */}
        {halkaOpak > 0.01 && (
          <>
            <circle cx={hx} cy={hy} r={halkaR * 1.12} fill="none" stroke={is.dolgu} strokeWidth={cizgi * 0.85} opacity={halkaOpak * 0.6} />
            <circle cx={hx} cy={hy} r={halkaR} fill="none" stroke={is.parilti} strokeWidth={cizgi * 0.42} opacity={halkaOpak * 0.9} />
          </>
        )}
        {/* Organik katmanlı lider çizgi: mürekkep tabanı + ana çizgi + üst parıltı */}
        <path
          d={yol}
          fill="none"
          stroke={is.dolgu}
          strokeWidth={cizgi * 1.65}
          strokeLinecap="round"
          strokeLinejoin="round"
          opacity={Math.min(1, cizgiIlerle * 6) * 0.72}
          strokeDasharray={yolUz}
          strokeDashoffset={cizgiOfset(yolUz, cizgiIlerle)}
        />
        <path
          d={yol}
          fill="none"
          stroke={rgba(renk, 0.95)}
          strokeWidth={cizgi}
          strokeLinecap="round"
          strokeLinejoin="round"
          opacity={Math.min(1, cizgiIlerle * 6)}
          strokeDasharray={yolUz}
          strokeDashoffset={cizgiOfset(yolUz, cizgiIlerle)}
        />
        <path
          d={yol}
          fill="none"
          stroke={is.parilti}
          strokeWidth={cizgi * 0.28}
          strokeLinecap="round"
          strokeLinejoin="round"
          transform={`translate(${(-0.5 * u).toFixed(1)} ${(-0.8 * u).toFixed(1)})`}
          opacity={Math.min(1, cizgiIlerle * 6) * 0.78}
          strokeDasharray={yolUz}
          strokeDashoffset={cizgiOfset(yolUz, cizgiIlerle)}
        />
        {/* Parlayan hedef odak noktası */}
        <g transform={`translate(${hx} ${hy}) scale(${noktaOlcek})`}>
          <circle cx={0} cy={0} r={noktaR * 1.65} fill={is.dolgu} />
          <circle cx={0} cy={0} r={noktaR} fill={renk} />
          <circle cx={-noktaR * 0.25} cy={-noktaR * 0.25} r={noktaR * 0.38} fill={is.parilti} />
        </g>
      </svg>

      {/* Çağrı rafı ucundaki rozet etiketi (yuzeyStil + parlamaStil) */}
      <div
        style={{
          ...rozetYuzey,
          position: "absolute",
          left: pRafSon[0],
          top: pRafSon[1],
          transform: `translate(${rafYon > 0 ? "-10%" : "-90%"}, -50%) scale(${rozetOlcek})`,
          transformOrigin: rafYon > 0 ? "left center" : "right center",
          overflow: "hidden",
          display: "inline-flex",
          alignItems: "center",
          gap: Math.round(8 * u),
          padding: etiketTemiz ? `${Math.round(6 * u)}px ${Math.round(16 * u)}px` : `${Math.round(6 * u)}px ${Math.round(12 * u)}px`,
          border: `${Math.max(1.5, Math.round(1.8 * u))}px solid ${rgba(renk, 0.72)}`,
          opacity: Math.min(1, rozetOlcek * 2),
          pointerEvents: "none",
        }}
      >
        <div style={parlamaStil(t, a.parlama, u)} />
        <div
          style={{
            width: Math.max(8 * u, Math.round(10 * u)),
            height: Math.max(8 * u, Math.round(10 * u)),
            borderRadius: Math.round(999 * u),
            background: ton(renk, -0.35),
            boxShadow: `0 0 ${10 * u}px ${rgba(renk, 0.85)}`,
            flexShrink: 0,
          }}
        />
        {etiketTemiz.length > 0 && (
          <div
            style={{
              fontFamily: yigin(t.font.baslik),
              fontWeight: t.font.agirlik_baslik,
              fontSize: etiketBoy,
              lineHeight: 1.08,
              color: yuzeyYazi(t, "rozet"),
              whiteSpace: "nowrap",
            }}
          >
            {harf(t, etiketTemiz)}
          </div>
        )}
      </div>
    </div>
  );
};

export default tanimla({ meta: meta as never, sema, Bilesen: Cagri });
