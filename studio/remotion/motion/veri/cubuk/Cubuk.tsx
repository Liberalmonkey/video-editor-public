// Çubuk grafik: yüzey malzemesi + parlama, gradyan çubuk dolguları, üst parlayan uç noktaları ve kademeli yay açılışıyla yükselir.
import React from "react";
import { z } from "zod";
import { golge, harf, karistir, parlamaStil, rakamFontu, rgba, ton, useTema, yigin, yuzeyStil } from "../../../tema";
import { useAkis } from "../../cekirdek/zaman";
import { tanimla, type BilesenProps } from "../../cekirdek/tipler";
import meta from "./meta.json";

const cubukOge = z.strictObject({
  etiket: z.string().max(14).describe("Çubuk alt etiketi"),
  deger: z.number().min(0).describe("Çubuk sayısal değeri"),
});

export const sema = z.strictObject({
  baslik: z.string().max(38).default("Kanal Bazlı Dönüşüm").describe("Grafiğin üst başlığı"),
  onek: z.string().max(8).default("%").describe("Değerlerin önündeki simge (örn. %, ₺, $)"),
  sonek: z.string().max(8).default("").describe("Değerlerin sonundaki birim (örn. K, M, adet)"),
  veriler: z
    .array(cubukOge)
    .min(2)
    .max(5)
    .default([
      { etiket: "Video", deger: 68 },
      { etiket: "Görsel", deger: 42 },
      { etiket: "Yazı", deger: 29 },
      { etiket: "Ses", deger: 51 },
    ])
    .describe("2 ile 5 arası çubuk verisi"),
  renk: z.enum(["vurgu", "ikincil", "olumlu", "olumsuz", "yazi"]).default("vurgu").describe("En yüksek çubuğun tema rengi adı"),
});

const Cubuk: React.FC<BilesenProps<z.infer<typeof sema>>> = ({ param, kutu, sureKare, u }) => {
  const t = useTema();
  const a = useAkis(sureKare, meta.giris_sn, meta.cikis_sn);
  const g = golge(t, u);
  const vurgu = t.renk[param.renk];
  const yuzey = yuzeyStil(t, u, "kart");

  const veriler = param.veriler;
  let enBuyukIdx = 0;
  let enBuyukDeger = veriler[0]?.deger ?? 1;
  for (let i = 1; i < veriler.length; i++) {
    if (veriler[i].deger > enBuyukDeger) {
      enBuyukDeger = veriler[i].deger;
      enBuyukIdx = i;
    }
  }
  const enBuyukEtiket = veriler[enBuyukIdx]?.etiket ?? "";
  const tavan = Math.max(1, enBuyukDeger);
  const bicimle = (d: number) => `${param.onek}${d.toLocaleString("tr-TR")}${param.sonek}`;

  const panelY = 10 * u * a.ters + (1 - a.gir) * 26 * u + a.nefes * -2 * u + a.cik * 24 * u;
  const blur = a.hizBulaniklik > 0.08 ? `blur(${(a.hizBulaniklik * 0.45 * u).toFixed(2)}px)` : undefined;
  const kose = t.sekil.kose * u;
  const baslikBoy = Math.max(28 * u, Math.round(kutu.h * 0.092));
  const rozetBoy = Math.max(28 * u, Math.round(kutu.h * 0.088));
  const etiketBoy = Math.max(28 * u, Math.round(kutu.h * 0.082));
  const degerBoy = Math.max(28 * u, Math.round(kutu.h * 0.08));
  const kazananDegerBoy = Math.max(36 * u, Math.round(kutu.h * 0.115));

  const kazananKare = a.hazirlikKare + enBuyukIdx * 3 + Math.max(4, Math.round(a.girKare * 0.7));
  const kazananVurgu = a.vurgu(kazananKare, Math.max(4, Math.round(0.3 * a.fps)));
  const kazananAtim = Math.sin(Math.PI * Math.min(1, Math.max(0, kazananVurgu)));
  const eksenOlcek = a.gir * (1 - a.cik);
  const cubukAlanH = Math.max(84 * u, Math.round(kutu.h * 0.4));

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
          height: "100%",
          padding: `${Math.round(18 * u)}px ${Math.round(24 * u)}px ${Math.round(18 * u)}px ${Math.round(30 * u)}px`,
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          boxSizing: "border-box",
          overflow: "hidden",
          opacity: a.belir * (1 - a.cik),
          filter: blur,
          transform: `translateY(${panelY}px) scale(${1 + 0.005 * a.nefes})`,
        }}
      >
        <div style={parlamaStil(t, a.parlama, u)} />

        <div
          style={{
            position: "absolute",
            left: 0,
            top: 0,
            bottom: 0,
            width: Math.max(5 * u, Math.round(7 * u)),
            background: `linear-gradient(180deg, ${ton(vurgu, -0.35)}, ${vurgu}, ${karistir(vurgu, t.renk.ikincil, 0.35)})`,
            boxShadow: `0 0 ${14 * u}px ${rgba(vurgu, 0.5)}`,
            transformOrigin: "center bottom",
            transform: `scaleY(${eksenOlcek})`,
          }}
        />

        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: Math.round(14 * u) }}>
          <div
            style={{
              fontFamily: yigin(t.font.baslik),
              fontWeight: t.font.agirlik_baslik,
              fontSize: baslikBoy,
              lineHeight: 1.12,
              letterSpacing: `${t.font.izleme}em`,
              color: t.renk.yazi,
              textShadow: g.yazi,
              whiteSpace: "nowrap",
              overflow: "hidden",
              textOverflow: "ellipsis",
              minWidth: 0,
            }}
          >
            {harf(t, param.baslik)}
          </div>
          <div
            style={{
              ...yuzeyStil(t, u, "rozet"),
              padding: `${Math.round(6 * u)}px ${Math.round(16 * u)}px`,
              background: `linear-gradient(135deg, ${rgba(vurgu, 0.24)}, ${rgba(vurgu, 0.1)})`,
              border: `${Math.max(1.5, Math.round(2 * u))}px solid ${rgba(vurgu, 0.72)}`,
              fontFamily: rakamFontu(t),
              fontWeight: t.font.agirlik_baslik,
              fontSize: rozetBoy,
              lineHeight: 1.05,
              fontVariantNumeric: "tabular-nums",
              color: ton(vurgu, -0.25),
              whiteSpace: "nowrap",
              flexShrink: 0,
              transform: `scale(${1 + 0.06 * kazananAtim})`,
              transformOrigin: "right center",
            }}
          >
            {`${harf(t, enBuyukEtiket)} · ${bicimle(enBuyukDeger)}`}
          </div>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: Math.round(8 * u) }}>
          <div
            style={{
              display: "flex",
              alignItems: "flex-end",
              justifyContent: "space-around",
              gap: Math.round(14 * u),
              height: cubukAlanH + kazananDegerBoy + Math.round(10 * u),
              paddingBottom: Math.round(4 * u),
            }}
          >
            {veriler.map((v, i) => {
              const kazananMi = i === enBuyukIdx;
              const yay = a.yay(i * 3, kazananMi ? "elastik" : "keskin");
              const gir = a.sirali(i, 3, "enter");
              const oran = Math.max(0.08, v.deger / tavan);
              const yukseklik = Math.round(cubukAlanH * oran);
              const olcekY = Math.max(0.04, (0.06 * a.belir * (1 - 0.5 * a.ters) + 0.94 * Math.max(0, yay)) * (1 - a.cik));
              const degerOp = Math.min(1, gir * 2.1);

              return (
                <div
                  key={i}
                  style={{
                    flex: 1,
                    minWidth: 0,
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "center",
                    justifyContent: "flex-end",
                    height: "100%",
                    gap: Math.round(6 * u),
                  }}
                >
                  <div
                    style={{
                      fontFamily: rakamFontu(t),
                      fontWeight: t.font.agirlik_baslik,
                      fontSize: kazananMi ? kazananDegerBoy : degerBoy,
                      lineHeight: 1,
                      fontVariantNumeric: "tabular-nums",
                      color: kazananMi ? vurgu : t.renk.soluk,
                      textShadow: kazananMi ? `0 0 ${14 * u}px ${rgba(vurgu, 0.45)}` : undefined,
                      opacity: degerOp,
                      transform: `translateY(${(1 - gir) * 14 * u}px) scale(${kazananMi ? 1 + 0.08 * kazananAtim : 1})`,
                      whiteSpace: "nowrap",
                    }}
                  >
                    {bicimle(v.deger)}
                  </div>
                  <div
                    style={{
                      position: "relative",
                      width: "76%",
                      maxWidth: Math.round(92 * u),
                      height: yukseklik,
                      borderRadius: `${Math.min(kose * 0.55, 12 * u)}px ${Math.min(kose * 0.55, 12 * u)}px ${Math.round(3 * u)}px ${Math.round(3 * u)}px`,
                      background: kazananMi
                        ? `linear-gradient(180deg, ${ton(vurgu, -0.35)} 0%, ${vurgu} 55%, ${karistir(vurgu, t.renk.ikincil, 0.3)} 100%)`
                        : `linear-gradient(180deg, ${rgba(t.renk.yazi, 0.36)} 0%, ${rgba(t.renk.yazi, 0.14)} 100%)`,
                      boxShadow: kazananMi
                        ? `inset 0 ${1.5 * u}px 0 ${ton(vurgu, -0.6, 0.85)}, 0 0 ${18 * u}px ${rgba(vurgu, 0.45)}`
                        : `inset 0 ${1 * u}px 0 ${rgba(t.renk.yazi, 0.25)}`,
                      transformOrigin: "center bottom",
                      transform: `scaleY(${olcekY})`,
                      overflow: "visible",
                    }}
                  >
                    {/* Çubuk tepesinde parlayan uç nokta */}
                    <div
                      style={{
                        position: "absolute",
                        top: Math.round(-4 * u),
                        left: "50%",
                        width: Math.round((kazananMi ? 10 : 6) * u),
                        height: Math.round((kazananMi ? 10 : 6) * u),
                        borderRadius: Math.round(999 * u),
                        transform: "translateX(-50%)",
                        background: kazananMi ? ton(vurgu, -0.6) : rgba(t.renk.yazi, 0.72),
                        boxShadow: kazananMi ? `0 0 ${12 * u}px ${rgba(vurgu, 0.9)}` : undefined,
                        opacity: Math.min(1, gir * 1.6),
                      }}
                    />
                  </div>
                </div>
              );
            })}
          </div>

          <div
            style={{
              width: "100%",
              height: Math.max(2 * u, Math.round(2.5 * u)),
              borderRadius: Math.round(2 * u),
              background: rgba(t.renk.yazi, 0.22),
              transformOrigin: "left center",
              transform: `scaleX(${eksenOlcek})`,
            }}
          />

          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-around", gap: Math.round(14 * u) }}>
            {veriler.map((v, i) => {
              const kazananMi = i === enBuyukIdx;
              const etGir = a.sirali(i + 1, 3, "settle");
              return (
                <div key={i} style={{ flex: 1, minWidth: 0, overflow: "hidden", textAlign: "center" }}>
                  <div
                    style={{
                      fontFamily: yigin(t.font.govde),
                      fontWeight: kazananMi ? t.font.agirlik_baslik : t.font.agirlik_govde,
                      fontSize: etiketBoy,
                      lineHeight: 1.15,
                      color: kazananMi ? t.renk.yazi : t.renk.soluk,
                      whiteSpace: "nowrap",
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                      opacity: 0.25 + 0.75 * etGir,
                      transform: `translateY(${(1 - etGir) * 85}%)`,
                    }}
                  >
                    {harf(t, v.etiket)}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};

export default tanimla({ meta: meta as never, sema, Bilesen: Cubuk });
