// Takip / Abone düğmesi: stilize vurgulu kapsül yerleşir, ok imleci kavisle gelip tıklar, düğme çöküp cam onay durumuna döner + parlama.
import React from "react";
import { interpolate, spring } from "remotion";
import { z } from "zod";
import {
  golge, harf, koyuMu, parlamaStil, rgba, titremeOpaklik, titresim,
  useTema, yigin, yuzeyStil, yuzeyTipi, yuzeyYazi, type TemaToken,
} from "../../../tema";
import { cizgiOfset, useAkis } from "../../cekirdek/zaman";
import { tanimla, type BilesenProps } from "../../cekirdek/tipler";
import meta from "./meta.json";

export const sema = z.strictObject({
  metin: z.string().max(24).default("Takip et").describe("Tıklanmadan önceki düğme metni"),
  tamam: z.string().max(24).default("Takip edildi").describe("Tıklandıktan sonraki onay metni"),
  renk: z.enum(["vurgu", "ikincil", "olumlu", "olumsuz", "yazi"]).default("vurgu").describe("Düğmenin tema rengi adı"),
});

const KIS = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const TIK_YOL = "M4 12.5 9.5 18 20 6.5";
const TIK_UZ = 24;
// Sade vektör ok imleci (platform logosu değil).
const IMLEC_YOL = "M3 2l17 10.5-7.4 1.8L10 21.5 3 2z";

const kontrastYazi = (t: TemaToken, arkaHex: string) => {
  const acik = koyuMu(t.renk.zemin) ? t.renk.yazi : t.renk.zemin;
  const koyu = koyuMu(t.renk.zemin) ? t.renk.zemin : t.renk.yazi;
  return koyuMu(arkaHex) ? acik : koyu;
};

const Abone: React.FC<BilesenProps<z.infer<typeof sema>>> = ({ param, kutu, sureKare, u }) => {
  const t = useTema();
  const a = useAkis(sureKare, meta.giris_sn, meta.cikis_sn);
  const g = golge(t, u);
  const tip = yuzeyTipi(t);
  const vurgu = t.renk[param.renk];
  const tRenk: TemaToken = param.renk === "vurgu" ? t : { ...t, renk: { ...t.renk, vurgu } };
  const keskin = tip === "piksel" || tip === "brutalist";

  // Düğme girişi: a.ters ile aşağı kısa hazırlık, ardından yayla yukarı kayma yerleşmesi + tutmada nefes.
  const dugmeYay = a.yay(0, "keskin");
  const onY = 10 * u * a.ters;
  const dugmeY = (1 - Math.min(1.06, dugmeYay)) * 30 * u + onY + a.cik * 26 * u + a.nefes * 1.5 * u;

  // İmleç yaklaşması ve tıklama karesi.
  const tikKare = Math.max(a.girKare + 4, Math.min(Math.max(a.girKare + 4, sureKare - a.cikKare - 10), Math.round(sureKare * 0.44)));
  const imlecBas = Math.min(tikKare - 2, Math.max(a.girKare - 2, tikKare - 11));
  const imlecGir = a.e.enter(interpolate(a.f, [imlecBas, tikKare - 1], [0, 1], KIS));
  const imlecCikBas = tikKare + 12;
  const imlecCik = a.e.exit(interpolate(a.f, [imlecCikBas, imlecCikBas + 8], [0, 1], KIS));

  // Basma tepkisi: 3 kare çökme + tek sönümlü yayla geri fırlama.
  const basma = a.e.emphasis(interpolate(a.f, [tikKare - 1, tikKare + 2], [0, 1], KIS));
  const birak = spring({
    frame: Math.max(0, a.f - (tikKare + 2)),
    fps: a.fps,
    config: { damping: 14, stiffness: 210, mass: 0.8 },
  });
  const tiklandi = a.f >= tikKare + 2;
  const cokus = basma * (1 - birak);
  const dugmeOlcek = (1 - 0.07 * cokus) * (1 + 0.005 * a.nefes);
  const dugmeBasY = 4 * u * cokus;

  // Tıklama sonrası onay çizgisi, dalga halkası ve ikinci parlama süpürmesi.
  const onayGir = a.e.enter(interpolate(a.f, [tikKare + 2, tikKare + 10], [0, 1], KIS));
  const onayParlama = a.e.settle(
    interpolate(a.f, [tikKare + 3, tikKare + 3 + Math.max(8, Math.round(0.5 * a.fps))], [0, 1], KIS),
  );
  const dalga = a.e.settle(interpolate(a.f, [tikKare + 1, tikKare + 14], [0, 1], KIS));
  const dalgaOp = dalga > 0.01 && dalga < 0.99 ? (1 - dalga) * 0.72 : 0;

  // Kavisli imleç yolu (sağ alttan düğme üstüne).
  const imlecX = (1 - imlecGir) * 96 * u + imlecCik * 72 * u;
  const imlecY = (1 - imlecGir) * 74 * u - Math.sin(imlecGir * Math.PI) * 18 * u + imlecCik * 56 * u;
  const imlecOlcek = 1 - 0.16 * cokus;
  const imlecOp = Math.min(1, imlecGir * 3) * (1 - imlecCik) * (1 - a.cik);

  const dugmeYuk = Math.round(kutu.h * 0.68);
  const yaziBoy = Math.max(42 * u, Math.round(kutu.h * 0.27));
  const tikIkon = Math.round(yaziBoy * 0.76);
  const imlecIkon = Math.round(46 * u);

  const blur = a.hizBulaniklik > 0.08 ? `blur(${(a.hizBulaniklik * u).toFixed(2)}px)` : undefined;
  const tit = titremeOpaklik(t, a.f);
  const titr = titresim(t, a.f, u);

  const rozetYuzey = yuzeyStil(t, u, "rozet");
  const vurguluYuzey = yuzeyStil(tRenk, u, "vurgulu");
  const aktifYuzey = tiklandi
    ? {
        ...rozetYuzey,
        borderColor: keskin ? rozetYuzey.borderColor : rgba(vurgu, 0.72),
      }
    : {
        ...vurguluYuzey,
        borderRadius: rozetYuzey.borderRadius,
      };
  const yaziRenk = tiklandi
    ? yuzeyYazi(t, "rozet")
    : tip === "neon"
      ? t.renk.yazi
      : kontrastYazi(t, vurgu);
  const kose = typeof rozetYuzey.borderRadius === "number" ? rozetYuzey.borderRadius : dugmeYuk * 0.5;

  return (
    <div
      style={{
        position: "relative",
        width: kutu.w,
        height: kutu.h,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        overflow: "visible",
      }}
    >
      <div
        style={{
          ...aktifYuzey,
          position: "relative",
          minWidth: Math.round(kutu.w * 0.72),
          maxWidth: "100%",
          height: dugmeYuk,
          padding: `0 ${Math.round(34 * u)}px`,
          display: "inline-flex",
          alignItems: "center",
          justifyContent: "center",
          gap: Math.round(14 * u),
          boxSizing: "border-box",
          transform: `translateY(${dugmeY + dugmeBasY}px) scale(${dugmeOlcek}) ${titr}`,
          opacity: a.belir * (1 - a.cik) * tit,
          filter: blur,
        }}
      >
        <div
          style={{
            position: "absolute",
            inset: 0,
            overflow: "hidden",
            borderRadius: "inherit",
            pointerEvents: "none",
          }}
        >
          <div style={parlamaStil(tiklandi ? t : tRenk, tiklandi ? onayParlama : a.parlama, u)} />
        </div>

        <div
          style={{
            position: "absolute",
            inset: Math.round(-4 * u),
            borderRadius: keskin ? 0 : kose + Math.round(4 * u),
            border: `${Math.max(2, Math.round(3 * u))}px solid ${rgba(vurgu, 0.9)}`,
            transform: `scale(${1 + dalga * 0.2}, ${1 + dalga * 0.4})`,
            opacity: dalgaOp,
            pointerEvents: "none",
          }}
        />

        {tiklandi && (
          <svg
            viewBox="0 0 24 24"
            width={tikIkon}
            height={tikIkon}
            style={{ overflow: "visible", flexShrink: 0 }}
          >
            <path
              d={TIK_YOL}
              fill="none"
              stroke={t.renk.olumlu}
              strokeWidth={3.4}
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeDasharray={TIK_UZ}
              strokeDashoffset={cizgiOfset(TIK_UZ, onayGir)}
              style={{
                filter: keskin ? undefined : `drop-shadow(0 0 ${6 * u}px ${rgba(t.renk.olumlu, 0.7)})`,
              }}
            />
          </svg>
        )}

        <div
          style={{
            fontFamily: yigin(t.font.baslik),
            fontWeight: t.font.agirlik_baslik,
            fontSize: yaziBoy,
            lineHeight: 1.04,
            letterSpacing: `${t.font.izleme}em`,
            color: yaziRenk,
            whiteSpace: "nowrap",
            overflow: "hidden",
            textOverflow: "ellipsis",
            transform: tiklandi ? `translateY(${(1 - onayGir) * 10 * u}px)` : undefined,
          }}
        >
          {harf(t, tiklandi ? param.tamam : param.metin)}
        </div>

        <svg
          viewBox="0 0 24 24"
          width={imlecIkon}
          height={imlecIkon}
          style={{
            position: "absolute",
            right: Math.round(22 * u),
            bottom: Math.round(-16 * u),
            overflow: "visible",
            filter: g.filtre,
            transformOrigin: "3px 2px",
            transform: `translate(${imlecX}px, ${imlecY}px) scale(${imlecOlcek})`,
            opacity: imlecOp,
          }}
        >
          <path
            d={IMLEC_YOL}
            fill={t.renk.yazi}
            stroke={t.renk.ikon_kontur}
            strokeWidth={2.2}
            strokeLinejoin="round"
          />
        </svg>
      </div>
    </div>
  );
};

export default tanimla({ meta: meta as never, sema, Bilesen: Abone });
