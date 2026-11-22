// Bildirim kartı: modern cam/stilize bildirim bandı — üstten yayla iner, harf monogram rozeti nabız halkasıyla oturur + specular parlama.
import React from "react";
import { z } from "zod";
import {
  harf, koyuMu, parlamaStil, rgba, titremeOpaklik, titresim,
  ton, useTema, yigin, yuzeyStil, yuzeyTipi, yuzeyYazi, type TemaToken,
} from "../../../tema";
import { useAkis } from "../../cekirdek/zaman";
import { tanimla, type BilesenProps } from "../../cekirdek/tipler";
import meta from "./meta.json";

export const sema = z.strictObject({
  baslik: z.string().max(32).default("Yeni İpucu").describe("Bildirim başlığı"),
  metin: z.string().max(72).default("Bu ayarı kaydet, bir sonraki videoda dene.").describe("Kısa bildirim metni"),
  renk: z.enum(["vurgu", "ikincil", "olumlu", "olumsuz", "yazi"]).default("vurgu").describe("Yuvarlak harf rozetinin tema rengi adı"),
});

const kontrastYazi = (t: TemaToken, arkaHex: string) => {
  const acik = koyuMu(t.renk.zemin) ? t.renk.yazi : t.renk.zemin;
  const koyu = koyuMu(t.renk.zemin) ? t.renk.zemin : t.renk.yazi;
  return koyuMu(arkaHex) ? acik : koyu;
};

const Bildirim: React.FC<BilesenProps<z.infer<typeof sema>>> = ({ param, kutu, sureKare, u }) => {
  const t = useTema();
  const a = useAkis(sureKare, meta.giris_sn, meta.cikis_sn);
  const tip = yuzeyTipi(t);
  const vurgu = t.renk[param.renk];
  const keskin = tip === "piksel" || tip === "brutalist";

  // Anticipation: a.ters ile yukarı kısa gerilme, ardından üstten yaylı iniş ve tek sönümlü yerleşme.
  const h = a.hazirlikKare;
  const inis = a.yay(0, "keskin");
  const onY = -14 * u * a.ters;
  const kartY = (1 - Math.min(1.06, inis)) * -kutu.h * 0.42 + onY - a.cik * kutu.h * 0.9 + a.nefes * 1.5 * u;

  // Follow-through: monogram rozeti 3 kare sonra elastik oturur ve tek nabız halkası yayar.
  const rozetYay = a.yay(3, "elastik");
  const rozetAci = (1 - Math.min(1.08, rozetYay)) * -14;
  const nabiz = a.vurgu(Math.max(h + 4, a.girKare - 2), Math.round(0.38 * a.fps));
  const baslikGir = a.sirali(1, 2, "enter");
  const metinGir = a.sirali(2, 2, "enter");

  const rozetCap = Math.round(Math.min(kutu.h * 0.5, 86 * u));
  const rozetKose = keskin ? 0 : Math.round(rozetCap * 0.3);
  const baslikBoy = Math.max(40 * u, Math.round(kutu.h * 0.215));
  const metinBoy = Math.max(28 * u, Math.round(kutu.h * 0.145));
  const zamanBoy = Math.max(28 * u, Math.round(kutu.h * 0.14));
  const ilkHarf = harf(t, param.baslik.trim().charAt(0) || "B").toLocaleUpperCase("tr-TR");

  const halkaOlcek = 1 + nabiz * 0.42;
  const halkaOp = nabiz > 0.01 && nabiz < 0.99 ? Math.sin(nabiz * Math.PI) * 0.65 : 0;

  const blur = a.hizBulaniklik > 0.08 ? `blur(${(a.hizBulaniklik * u).toFixed(2)}px)` : undefined;
  const tit = titremeOpaklik(t, a.f);
  const titr = titresim(t, a.f, u);
  const yuzey = yuzeyStil(t, u, "kart");
  const anaYazi = yuzeyYazi(t, "kart");

  return (
    <div
      style={{
        width: kutu.w,
        height: kutu.h,
        display: "flex",
        alignItems: "center",
      }}
    >
      <div
        style={{
          ...yuzey,
          position: "relative",
          width: "100%",
          padding: `${Math.round(18 * u)}px ${Math.round(24 * u)}px`,
          display: "flex",
          alignItems: "center",
          gap: Math.round(18 * u),
          boxSizing: "border-box",
          transform: `translateY(${kartY}px) ${titr}`,
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
          <div style={parlamaStil(t, a.parlama, u)} />
        </div>

        <div
          style={{
            position: "relative",
            width: rozetCap,
            height: rozetCap,
            flexShrink: 0,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <div
            style={{
              position: "absolute",
              inset: 0,
              borderRadius: rozetKose,
              border: `${Math.max(2, Math.round(3 * u))}px solid ${vurgu}`,
              transform: `scale(${halkaOlcek})`,
              opacity: halkaOp,
            }}
          />
          <div
            style={{
              width: rozetCap,
              height: rozetCap,
              borderRadius: rozetKose,
              background: keskin
                ? vurgu
                : `linear-gradient(145deg, ${ton(vurgu, -0.14)} 0%, ${ton(vurgu, 0.14)} 100%)`,
              boxShadow: keskin
                ? undefined
                : `inset 0 ${1.5 * u}px 0 ${rgba(t.renk.yazi, 0.34)}, 0 ${6 * u}px ${16 * u}px ${rgba(vurgu, 0.42)}`,
              color: kontrastYazi(t, vurgu),
              fontFamily: yigin(t.font.baslik),
              fontWeight: t.font.agirlik_baslik,
              fontSize: Math.round(rozetCap * 0.48),
              lineHeight: 1,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              transform: `rotate(${rozetAci}deg) scale(${Math.max(0.5, Math.min(1.08, rozetYay))})`,
            }}
          >
            {ilkHarf}
          </div>
        </div>

        <div style={{ flex: 1, minWidth: 0, display: "flex", flexDirection: "column", gap: Math.round(5 * u) }}>
          <div
            style={{
              display: "flex",
              alignItems: "baseline",
              justifyContent: "space-between",
              gap: Math.round(12 * u),
              transform: `translateY(${(1 - baslikGir) * 14 * u}px)`,
              opacity: Math.min(1, baslikGir * 2.4),
            }}
          >
            <div
              style={{
                fontFamily: yigin(t.font.baslik),
                fontWeight: t.font.agirlik_baslik,
                fontSize: baslikBoy,
                lineHeight: 1.08,
                letterSpacing: `${t.font.izleme}em`,
                color: anaYazi,
                whiteSpace: "nowrap",
                overflow: "hidden",
                textOverflow: "ellipsis",
              }}
            >
              {harf(t, param.baslik)}
            </div>
            <div
              style={{
                fontFamily: yigin(t.font.govde),
                fontWeight: t.font.agirlik_govde,
                fontSize: zamanBoy,
                color: t.renk.soluk,
                flexShrink: 0,
              }}
            >
              {harf(t, "şimdi")}
            </div>
          </div>

          <div
            style={{
              fontFamily: yigin(t.font.govde),
              fontWeight: t.font.agirlik_govde,
              fontSize: metinBoy,
              lineHeight: 1.22,
              color: rgba(anaYazi, 0.86),
              display: "-webkit-box",
              WebkitLineClamp: 2,
              WebkitBoxOrient: "vertical",
              overflow: "hidden",
              transform: `translateY(${(1 - metinGir) * 14 * u}px)`,
              opacity: Math.min(1, metinGir * 2.4),
            }}
          >
            {harf(t, param.metin)}
          </div>
        </div>
      </div>
    </div>
  );
};

export default tanimla({ meta: meta as never, sema, Bilesen: Bildirim });
