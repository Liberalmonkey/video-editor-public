// Mekanik odometre: yüzey malzemesi, parlama şeridi, kademeli dönen tambur yuvaları ve elastik hedef kilidiyle oturur.
import React from "react";
import { interpolate } from "remotion";
import { z } from "zod";
import { golge, harf, karistir, parlamaStil, rakamFontu, rgba, ton, useTema, yigin, yuzeyStil } from "../../../tema";
import { useAkis } from "../../cekirdek/zaman";
import { tanimla, type BilesenProps } from "../../cekirdek/tipler";
import meta from "./meta.json";

export const sema = z.strictObject({
  deger: z.number().int().min(0).max(99999999).default(12450).describe("Gösterilecek tam sayı değeri"),
  onek: z.string().max(6).default("₺").describe("Rakam önündeki simge (örn. ₺, $, +)"),
  sonek: z.string().max(8).default("").describe("Rakam sonundaki birim (örn. +, K, adet)"),
  etiket: z.string().max(36).default("Aylık Gelir").describe("Göstergenin üstündeki kısa başlık"),
  turSayisi: z.number().int().min(1).max(3).default(1).describe("Şeritlerin oturmadan önce yapacağı ek tam tur sayısı"),
  renk: z.enum(["vurgu", "ikincil", "olumlu", "olumsuz", "yazi"]).default("vurgu").describe("Üst şerit ve aktif yuva vurgusu tema rengi adı"),
});

const KIS = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

const Odometre: React.FC<BilesenProps<z.infer<typeof sema>>> = ({ param, kutu, sureKare, u }) => {
  const t = useTema();
  const a = useAkis(sureKare, meta.giris_sn, meta.cikis_sn);
  const g = golge(t, u);
  const vurgu = t.renk[param.renk];
  const yuzey = yuzeyStil(t, u, "kart");

  const bicimli = param.deger.toLocaleString("tr-TR");
  const karakterler = Array.from(bicimli);
  const rakamSayisi = karakterler.filter((c) => c >= "0" && c <= "9").length;

  const govdeY = 10 * u * a.ters + (1 - a.gir) * 28 * u + a.nefes * -2 * u + a.cik * -24 * u;
  const blur = a.hizBulaniklik > 0.08 ? `blur(${(a.hizBulaniklik * 0.45 * u).toFixed(2)}px)` : undefined;
  const kose = t.sekil.kose * u;
  const etiketTemiz = param.etiket.trim();

  const etiketBoy = Math.max(28 * u, Math.round(kutu.h * 0.125));
  const pencereH = Math.max(76 * u, Math.round(kutu.h * 0.36));
  const rakamBoy = Math.max(64 * u, Math.round(pencereH * 0.78));
  const yuvaW = Math.max(48 * u, Math.min(Math.round(rakamBoy * 0.76), Math.round((kutu.w * 0.78) / Math.max(4, karakterler.length + 1))));

  const tabanBit = Math.max(a.girKare + 6, Math.min(sureKare - a.cikKare - 6, Math.round(sureKare * 0.56)));
  const kilitVurgu = a.vurgu(tabanBit, Math.max(4, Math.round(0.28 * a.fps)));
  const etiketGir = a.sirali(1, 3, "enter");

  let rakamSira = 0;

  return (
    <div
      style={{
        width: kutu.w,
        height: kutu.h,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        boxSizing: "border-box",
      }}
    >
      <div
        style={{
          ...yuzey,
          position: "relative",
          width: "100%",
          overflow: "hidden",
          padding: `${Math.round(20 * u)}px ${Math.round(24 * u)}px`,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: Math.round(14 * u),
          boxSizing: "border-box",
          opacity: a.belir * (1 - a.cik),
          filter: blur,
          transform: `translateY(${govdeY}px) scale(${1 + 0.005 * a.nefes})`,
        }}
      >
        <div style={parlamaStil(t, a.parlama, u)} />

        <div
          style={{
            position: "absolute",
            left: 0,
            top: 0,
            right: 0,
            height: Math.max(4 * u, Math.round(5 * u)),
            background: `linear-gradient(90deg, ${vurgu}, ${ton(vurgu, -0.42)})`,
            boxShadow: `0 0 ${14 * u}px ${rgba(vurgu, 0.55)}`,
            transformOrigin: "left center",
            transform: `scaleX(${Math.min(1, a.gir * 0.65 + kilitVurgu * 0.35) * (1 - a.cik)})`,
          }}
        />

        {etiketTemiz.length > 0 && (
          <div style={{ overflow: "hidden", maxWidth: "100%" }}>
            <div
              style={{
                fontFamily: yigin(t.font.govde),
                fontWeight: t.font.agirlik_govde,
                fontSize: etiketBoy,
                lineHeight: 1.15,
                letterSpacing: `${t.font.izleme}em`,
                color: t.renk.soluk,
                whiteSpace: "nowrap",
                overflow: "hidden",
                textOverflow: "ellipsis",
                opacity: a.belir * (0.3 + 0.7 * etiketGir),
                transform: `translateY(${(1 - etiketGir) * 100}%)`,
              }}
            >
              {harf(t, etiketTemiz)}
            </div>
          </div>
        )}

        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: Math.round(6 * u),
            maxWidth: "100%",
          }}
        >
          {param.onek.length > 0 && (
            <div
              style={{
                fontFamily: rakamFontu(t),
                fontWeight: t.font.agirlik_baslik,
                fontSize: rakamBoy,
                lineHeight: 1,
                color: vurgu,
                textShadow: `0 0 ${14 * u}px ${rgba(vurgu, 0.4)}, ${g.yazi !== "none" ? g.yazi : `0 ${2 * u}px ${8 * u}px ${rgba(t.renk.ikon_kontur, 0.45)}`}`,
                marginRight: Math.round(4 * u),
                transform: `scale(${1 + 0.06 * Math.sin(Math.PI * Math.min(1, kilitVurgu))})`,
              }}
            >
              {param.onek}
            </div>
          )}

          {karakterler.map((kar, idx) => {
            const rakamMi = kar >= "0" && kar <= "9";
            if (!rakamMi) {
              return (
                <div
                  key={`ayrac-${idx}`}
                  style={{
                    fontFamily: rakamFontu(t),
                    fontWeight: t.font.agirlik_baslik,
                    fontSize: rakamBoy,
                    lineHeight: 1,
                    color: t.renk.soluk,
                    width: Math.round(yuvaW * 0.32),
                    textAlign: "center",
                    transform: `translateY(${Math.round(pencereH * 0.14)}px)`,
                  }}
                >
                  {kar}
                </div>
              );
            }

            const i = rakamSira++;
            const hedef = parseInt(kar, 10);
            const bas = a.hazirlikKare + i * 3;
            const oran = rakamSayisi > 1 ? i / (rakamSayisi - 1) : 1;
            const bit = Math.max(bas + 6, Math.round(tabanBit - (1 - oran) * Math.min(10, Math.max(0, tabanBit - bas - 6))));
            const ilerle = a.e.settle(interpolate(a.f, [bas, bit], [0, 1], KIS));
            const hiz = ilerle > 0 && ilerle < 1 ? 1 - ilerle : 0;
            const turlar = param.turSayisi + (i % 2);
            const toplamAdim = turlar * 10 + hedef;
            const konum = Math.max(-0.35, ilerle * toplamAdim - 0.28 * a.ters);
            const tam = Math.floor(konum);
            const kesir = konum - tam;
            const mod10 = (n: number) => ((n % 10) + 10) % 10;
            const komsular = [-1, 0, 1];
            const kilitYay = a.yay(Math.max(0, bit - a.hazirlikKare), "elastik");
            const yuvaVurgu = Math.max(0, Math.min(1, kilitYay));

            return (
              <div
                key={`hane-${idx}`}
                style={{
                  position: "relative",
                  width: yuvaW,
                  height: pencereH,
                  overflow: "hidden",
                  borderRadius: Math.max(4 * u, Math.min(kose * 0.55, 12 * u)),
                  background: `linear-gradient(180deg, ${rgba(t.renk.ikon_kontur, 0.22)} 0%, ${rgba(t.renk.yazi, 0.08)} 50%, ${rgba(t.renk.ikon_kontur, 0.22)} 100%)`,
                  border: `${Math.max(1, Math.round(1.5 * u))}px solid ${karistir(t.renk.yazi, vurgu, yuvaVurgu, 0.22 + 0.42 * yuvaVurgu)}`,
                  boxShadow: `inset 0 ${1 * u}px 0 ${rgba(t.renk.yazi, 0.16)}, 0 0 ${12 * u * yuvaVurgu}px ${rgba(vurgu, 0.22 * yuvaVurgu)}`,
                  boxSizing: "border-box",
                  transform: `scale(${1 + 0.05 * (kilitYay > 0 ? kilitYay - 1 : 0)})`,
                }}
              >
                {komsular.map((ofset) => {
                  const rakam = mod10(tam + ofset);
                  const yPx = (ofset - kesir) * pencereH;
                  return (
                    <div
                      key={ofset}
                      style={{
                        position: "absolute",
                        left: 0,
                        right: 0,
                        top: 0,
                        height: pencereH,
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        fontFamily: rakamFontu(t),
                        fontWeight: t.font.agirlik_baslik,
                        fontSize: rakamBoy,
                        lineHeight: 1,
                        fontVariantNumeric: "tabular-nums",
                        color: t.renk.yazi,
                        textShadow: g.yazi,
                        transform: `translateY(${yPx}px) scaleY(${1 + 0.09 * hiz})`,
                      }}
                    >
                      {rakam}
                    </div>
                  );
                })}
                <div
                  style={{
                    position: "absolute",
                    left: 0,
                    right: 0,
                    top: 0,
                    height: Math.round(pencereH * 0.24),
                    background: `linear-gradient(to bottom, ${rgba(t.renk.zemin, 0.72)}, ${rgba(t.renk.zemin, 0)})`,
                    pointerEvents: "none",
                  }}
                />
                <div
                  style={{
                    position: "absolute",
                    left: 0,
                    right: 0,
                    bottom: 0,
                    height: Math.round(pencereH * 0.24),
                    background: `linear-gradient(to top, ${rgba(t.renk.zemin, 0.72)}, ${rgba(t.renk.zemin, 0)})`,
                    pointerEvents: "none",
                  }}
                />
              </div>
            );
          })}

          {param.sonek.length > 0 && (
            <div
              style={{
                fontFamily: rakamFontu(t),
                fontWeight: t.font.agirlik_baslik,
                fontSize: Math.max(64 * u, Math.round(rakamBoy * 0.88)),
                lineHeight: 1,
                color: vurgu,
                textShadow: g.yazi,
                marginLeft: Math.round(4 * u),
              }}
            >
              {param.sonek}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default tanimla({ meta: meta as never, sema, Bilesen: Odometre });
