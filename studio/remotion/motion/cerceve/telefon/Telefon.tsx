// Telefon çerçevesi: içi saydam ekran penceresi, metalik kenar yansıması (specular rim + parlamaStil) ve a.nefes mikro 3B süzülmeyle oturur.
import React from "react";
import { interpolate } from "remotion";
import { z } from "zod";
import { karistir, koyuMu, parlamaStil, rgba, ton, useTema } from "../../../tema";
import { useAkis } from "../../cekirdek/zaman";
import { tanimla, type BilesenProps } from "../../cekirdek/tipler";
import meta from "./meta.json";

export const sema = z.strictObject({
  renk: z.enum(["vurgu", "ikincil", "olumlu", "olumsuz", "yazi"]).default("vurgu").describe("Kenar vurgu ışığı tema rengi adı"),
  centik: z.boolean().default(true).describe("Üst dinamik çentik gösterilsin mi"),
  parlama: z.boolean().default(true).describe("Çerçeve kenarında ince ışık parlaması olsun mu"),
});

const KIS = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

const yuvarlakYol = (x: number, y: number, w: number, h: number, r: number) => {
  const k = Math.max(0, Math.min(r, w / 2, h / 2));
  return `M${x + k} ${y}H${x + w - k}A${k} ${k} 0 0 1 ${x + w} ${y + k}V${y + h - k}A${k} ${k} 0 0 1 ${x + w - k} ${y + h}H${x + k}A${k} ${k} 0 0 1 ${x} ${y + h - k}V${y + k}A${k} ${k} 0 0 1 ${x + k} ${y}Z`;
};

const Telefon: React.FC<BilesenProps<z.infer<typeof sema>>> = ({ param, kutu, sureKare, u }) => {
  const t = useTema();
  const a = useAkis(sureKare, meta.giris_sn, meta.cikis_sn);
  const uid = React.useId().replace(/[^a-zA-Z0-9_-]/g, "");
  const govdeGradId = `tel-govde-${uid}`;
  const rimGradId = `tel-rim-${uid}`;
  const vurgu = t.renk[param.renk];

  const geriY = 18 * u * a.ters;
  const kayY = (1 - a.gir) * 58 * u + geriY + a.nefes * -3.2 * u + a.cik * 46 * u;
  const egimX = (1 - a.gir) * 14 + 3.5 * a.ters + a.nefes * 1.15 - a.cik * 10;
  const egimY = a.nefes * 1.5;
  const tusYay = a.yay(3, "keskin");
  const centikYay = a.yay(5, "elastik");
  const cubukGir = a.e.settle(interpolate(a.f, [a.hazirlikKare + 4, a.girKare + 4], [0, 1], KIS));
  const parlamaKonum = interpolate(a.f, [a.girKare, Math.max(a.girKare + 12, sureKare - a.cikKare)], [0, 1], KIS);

  const tusPay = Math.round(7 * u);
  const govdeX = tusPay;
  const govdeY = Math.round(4 * u);
  const govdeW = Math.max(60, kutu.w - tusPay * 2);
  const govdeH = Math.max(100, kutu.h - govdeY * 2);
  const kenarKal = Math.max(14 * u, Math.round(Math.min(govdeW, govdeH) * 0.044));
  const disKose = Math.max(24 * u, Math.round(Math.min(govdeW, govdeH) * 0.11));
  const icKose = Math.max(14 * u, disKose - kenarKal * 0.72);

  const disYol = yuvarlakYol(govdeX, govdeY, govdeW, govdeH, disKose);
  const icYol = yuvarlakYol(govdeX + kenarKal, govdeY + kenarKal, govdeW - kenarKal * 2, govdeH - kenarKal * 2, icKose);

  const govdeRenk = koyuMu(t.renk.zemin) ? t.renk.zemin : t.renk.ikon_kontur;
  const acikDolgu = koyuMu(t.renk.zemin) ? t.renk.yazi : t.renk.zemin;
  const cizgiRenk = rgba(acikDolgu, 0.34);

  const centikW = Math.round(govdeW * 0.28);
  const centikH = Math.max(16 * u, Math.round(kenarKal * 1.15));
  const centikX = govdeX + (govdeW - centikW) / 2;
  const centikY = govdeY + kenarKal + Math.round(10 * u);

  const altCubukW = Math.round(govdeW * 0.32);
  const altCubukH = Math.max(6 * u, Math.round(7 * u));
  const altCubukY = govdeY + govdeH - kenarKal - Math.round(16 * u);

  const tusXSol = govdeX - tusPay * Math.min(1, Math.max(0, tusYay));
  const tusXSag = govdeX + govdeW - tusPay * (1 - Math.min(1, Math.max(0, tusYay)));
  const blur = a.hizBulaniklik > 0.08 ? `blur(${(a.hizBulaniklik * 0.42 * u).toFixed(2)}px) ` : "";
  const katmanGolge = `drop-shadow(0 ${(18 * u).toFixed(1)}px ${(36 * u).toFixed(1)}px ${rgba(t.renk.ikon_kontur, 0.48)}) drop-shadow(0 ${(3 * u).toFixed(1)}px ${(8 * u).toFixed(1)}px ${rgba(t.renk.ikon_kontur, 0.35)})`;

  return (
    <div
      style={{
        width: kutu.w,
        height: kutu.h,
        perspective: Math.round(1150 * u),
        overflow: "visible",
      }}
    >
      <div
        style={{
          position: "relative",
          width: kutu.w,
          height: kutu.h,
          opacity: a.belir * (1 - a.cik),
          transformOrigin: "center bottom",
          transform: `translateY(${kayY}px) rotateX(${egimX}deg) rotateY(${egimY}deg)`,
          filter: `${blur}${katmanGolge}`,
        }}
      >
        <svg width={kutu.w} height={kutu.h} viewBox={`0 0 ${kutu.w} ${kutu.h}`} style={{ overflow: "visible", display: "block" }}>
          <defs>
            <linearGradient id={govdeGradId} x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stopColor={karistir(govdeRenk, acikDolgu, 0.16)} />
              <stop offset="48%" stopColor={govdeRenk} />
              <stop offset="100%" stopColor={ton(govdeRenk, 0.25)} />
            </linearGradient>
            <linearGradient id={rimGradId} x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stopColor={rgba(acikDolgu, 0.68)} />
              <stop offset="35%" stopColor={rgba(acikDolgu, 0.18)} />
              <stop offset="70%" stopColor={rgba(vurgu, 0.42)} />
              <stop offset="100%" stopColor={rgba(acikDolgu, 0.55)} />
            </linearGradient>
          </defs>

          {/* Yan metalik tuşlar */}
          <rect x={tusXSol} y={govdeY + govdeH * 0.19} width={tusPay + 2} height={govdeH * 0.065} rx={Math.round(3 * u)} fill={`url(#${govdeGradId})`} stroke={cizgiRenk} strokeWidth={Math.max(1, 1.2 * u)} />
          <rect x={tusXSol} y={govdeY + govdeH * 0.28} width={tusPay + 2} height={govdeH * 0.065} rx={Math.round(3 * u)} fill={`url(#${govdeGradId})`} stroke={cizgiRenk} strokeWidth={Math.max(1, 1.2 * u)} />
          <rect x={tusXSag - 2} y={govdeY + govdeH * 0.23} width={tusPay + 2} height={govdeH * 0.095} rx={Math.round(3 * u)} fill={`url(#${govdeGradId})`} stroke={cizgiRenk} strokeWidth={Math.max(1, 1.2 * u)} />

          {/* Metalik dış çerçeve - ekran içi evenodd ile %100 saydam */}
          <path d={`${disYol} ${icYol}`} fill={`url(#${govdeGradId})`} fillRule="evenodd" />

          {/* Gerçekçi specular rim yansıması */}
          <path d={disYol} fill="none" stroke={`url(#${rimGradId})`} strokeWidth={Math.max(2, 2.6 * u)} />
          <path d={icYol} fill="none" stroke={rgba(vurgu, 0.35)} strokeWidth={Math.max(1, 1.4 * u)} />

          {/* Süpüren specular kenar parlaması */}
          {param.parlama && (
            <>
              <path
                d={disYol}
                fill="none"
                stroke={ton(vurgu, -0.45, 0.8)}
                strokeWidth={Math.max(2.2, 2.8 * u)}
                strokeLinecap="round"
                strokeDasharray={`${Math.round(govdeW * 0.32)} ${Math.round((govdeW + govdeH) * 2)}`}
                strokeDashoffset={-parlamaKonum * (govdeW + govdeH) * 1.4}
              />
              <path
                d={disYol}
                fill="none"
                stroke={rgba(acikDolgu, 0.85)}
                strokeWidth={Math.max(1.2, 1.4 * u)}
                strokeLinecap="round"
                strokeDasharray={`${Math.round(govdeW * 0.14)} ${Math.round((govdeW + govdeH) * 2)}`}
                strokeDashoffset={-parlamaKonum * (govdeW + govdeH) * 1.4 - Math.round(govdeW * 0.08)}
              />
            </>
          )}

          {/* Üst dinamik çentik */}
          {param.centik && (
            <g style={{ transformOrigin: `${govdeX + govdeW / 2}px ${centikY + centikH / 2}px`, transform: `scale(${Math.max(0, centikYay)})` }}>
              <rect x={centikX} y={centikY} width={centikW} height={centikH} rx={centikH / 2} fill={govdeRenk} stroke={rgba(acikDolgu, 0.22)} strokeWidth={Math.max(1, 1.2 * u)} />
              <circle cx={centikX + centikW - centikH * 0.55} cy={centikY + centikH / 2} r={Math.max(2.5 * u, centikH * 0.22)} fill={ton(vurgu, -0.25, 0.72)} />
            </g>
          )}

          {/* Alt gezinme çubuğu */}
          <rect
            x={govdeX + (govdeW - altCubukW) / 2}
            y={altCubukY}
            width={altCubukW}
            height={altCubukH}
            rx={altCubukH / 2}
            fill={rgba(acikDolgu, 0.92)}
            style={{
              transformOrigin: `${govdeX + govdeW / 2}px ${altCubukY + altCubukH / 2}px`,
              transform: `scaleX(${cubukGir * (1 - a.cik)})`,
            }}
          />
        </svg>

        {/* Üst çerçeve şeridinde ince parlamaStil ışık geçişi (iç ekranı kapatmaz) */}
        {param.parlama && (
          <div
            style={{
              position: "absolute",
              left: govdeX,
              top: govdeY,
              width: govdeW,
              height: kenarKal,
              borderTopLeftRadius: disKose,
              borderTopRightRadius: disKose,
              overflow: "hidden",
              pointerEvents: "none",
            }}
          >
            <div style={parlamaStil(t, a.parlama, u)} />
          </div>
        )}
      </div>
    </div>
  );
};

export default tanimla({ meta: meta as never, sema, Bilesen: Telefon });
