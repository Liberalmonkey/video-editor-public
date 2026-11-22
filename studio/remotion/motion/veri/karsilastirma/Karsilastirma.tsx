// İki sütun karşılaştırma: yüzey malzemesi, kazanan sütunda canlı vurgu rim-light ve parlama şeridi, kaybeden sütunda yumuşak soluklaştırma.
import React from "react";
import { z } from "zod";
import { golge, harf, parlamaStil, rakamFontu, rgba, ton, useTema, yigin, yuzeyStil } from "../../../tema";
import { cizgiOfset, useAkis } from "../../cekirdek/zaman";
import { tanimla, type BilesenProps } from "../../cekirdek/tipler";
import meta from "./meta.json";

export const sema = z.strictObject({
  solBaslik: z.string().max(20).default("Önce").describe("Sol sütun başlığı"),
  solDeger: z.string().max(14).default("%18").describe("Sol sütunun büyük sayısal ya da kısa değeri"),
  solAlt: z.string().max(28).default("Eski kurgu düzeni").describe("Sol sütun alt açıklaması"),
  sagBaslik: z.string().max(20).default("Sonra").describe("Sağ sütun başlığı"),
  sagDeger: z.string().max(14).default("%64").describe("Sağ sütunun büyük sayısal ya da kısa değeri"),
  sagAlt: z.string().max(28).default("Yeni ritim ve grafik").describe("Sağ sütun alt açıklaması"),
  kazanan: z.enum(["sag", "sol", "yok"]).default("sag").describe("Vurgulanacak kazanan sütun"),
  renk: z.enum(["vurgu", "ikincil", "olumlu", "olumsuz", "yazi"]).default("olumlu").describe("Kazanan taraf vurgu tema rengi adı"),
  odakKarart: z.boolean().default(false).describe("Kaybeden sütunu daha belirgin soluklaştırıp kazananı öne çıkar"),
});

const Karsilastirma: React.FC<BilesenProps<z.infer<typeof sema>>> = ({ param, kutu, sureKare, u }) => {
  const t = useTema();
  const a = useAkis(sureKare, meta.giris_sn, meta.cikis_sn);
  const g = golge(t, u);
  const vurgu = t.renk[param.renk];
  const yuzey = yuzeyStil(t, u, "kart");

  const solGir = a.sirali(1, 3, "enter");
  const sagGir = a.sirali(2, 3, "enter");
  const ayracCiz = Math.min(1, 0.14 * a.belir + 0.86 * a.gir) * (1 - a.cik);

  const kazananBas = Math.max(a.hazirlikKare + 4, Math.min(sureKare - a.cikKare - 6, a.girKare + 5));
  const kazananVurgu = a.vurgu(kazananBas, Math.max(4, Math.round(0.32 * a.fps)));
  const kazananYay = a.yay(Math.max(0, kazananBas - a.hazirlikKare), "elastik");
  const kazananAtim = Math.sin(Math.PI * Math.min(1, Math.max(0, kazananVurgu)));

  const solX = 10 * u * a.ters + (1 - solGir) * 34 * u + a.cik * 28 * u;
  const sagX = -10 * u * a.ters + (1 - sagGir) * -34 * u + a.cik * -28 * u;
  const blur = a.hizBulaniklik > 0.08 ? `blur(${(a.hizBulaniklik * 0.45 * u).toFixed(2)}px)` : undefined;

  const kose = t.sekil.kose * u;
  const baslikBoy = Math.max(28 * u, Math.round(kutu.h * 0.095));
  const degerBoy = Math.max(64 * u, Math.round(kutu.h * 0.23));
  const altBoy = Math.max(28 * u, Math.round(kutu.h * 0.088));
  const ayracH = Math.max(120 * u, Math.round(kutu.h * 0.72));
  const yarim = ayracH / 2;

  const sutunlar = [
    { anahtar: "sol" as const, baslik: param.solBaslik, deger: param.solDeger, alt: param.solAlt, x: solX, gir: solGir },
    { anahtar: "sag" as const, baslik: param.sagBaslik, deger: param.sagDeger, alt: param.sagAlt, x: sagX, gir: sagGir },
  ];

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
          padding: `${Math.round(16 * u)}px ${Math.round(18 * u)}px`,
          display: "flex",
          alignItems: "stretch",
          justifyContent: "space-between",
          gap: Math.round(10 * u),
          boxSizing: "border-box",
          overflow: "hidden",
          opacity: a.belir * (1 - a.cik),
          filter: blur,
          transform: `scale(${(1 - 0.03 * a.ters) * (1 + 0.005 * a.nefes) * (1 - 0.06 * a.cik)})`,
        }}
      >
        <div style={parlamaStil(t, a.parlama, u)} />

        {sutunlar.map((s, idx) => {
          const kazananMi = param.kazanan === s.anahtar;
          const rakipMi = param.kazanan !== "yok" && !kazananMi;
          const vurguAcik = kazananMi ? Math.min(1, Math.max(0, kazananYay)) : 0;
          const icKose = Math.max(6 * u, kose * 0.65);
          const solmaHedef = param.odakKarart ? 0.44 : 0.26;
          const sakinOp = rakipMi ? 1 - solmaHedef * Math.min(1, kazananVurgu) : 1;

          return (
            <React.Fragment key={s.anahtar}>
              {idx === 1 && (
                <div
                  style={{
                    width: Math.round(28 * u),
                    flexShrink: 0,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    position: "relative",
                  }}
                >
                  <svg width={Math.round(24 * u)} height={ayracH} viewBox={`0 0 24 ${ayracH}`} style={{ overflow: "visible" }}>
                    <line
                      x1={12}
                      y1={yarim}
                      x2={12}
                      y2={0}
                      stroke={rgba(t.renk.yazi, 0.28)}
                      strokeWidth={Math.max(2, 2.5 * u)}
                      strokeLinecap="round"
                      strokeDasharray={yarim}
                      strokeDashoffset={cizgiOfset(yarim, ayracCiz)}
                    />
                    <line
                      x1={12}
                      y1={yarim}
                      x2={12}
                      y2={ayracH}
                      stroke={rgba(t.renk.yazi, 0.28)}
                      strokeWidth={Math.max(2, 2.5 * u)}
                      strokeLinecap="round"
                      strokeDasharray={yarim}
                      strokeDashoffset={cizgiOfset(yarim, ayracCiz)}
                    />
                    <circle cx={12} cy={yarim} r={Math.max(8 * u, 10 * u) * ayracCiz} fill={rgba(vurgu, 0.28)} />
                    <circle cx={12} cy={yarim} r={Math.max(4 * u, 5.5 * u) * Math.min(1, a.belir + 0.2 * ayracCiz)} fill={ton(vurgu, -0.35)} />
                  </svg>
                </div>
              )}

              <div
                style={{
                  position: "relative",
                  flex: 1,
                  minWidth: 0,
                  borderRadius: icKose,
                  background: kazananMi
                    ? `linear-gradient(160deg, ${rgba(vurgu, 0.22 * vurguAcik)} 0%, ${rgba(vurgu, 0.06 * vurguAcik)} 100%)`
                    : rakipMi && param.odakKarart
                      ? rgba(t.renk.ikon_kontur, 0.16 * Math.min(1, kazananVurgu))
                      : "transparent",
                  border: kazananMi
                    ? `${Math.max(1.5, Math.round(2 * u))}px solid ${rgba(vurgu, 0.72 * vurguAcik)}`
                    : `${Math.max(1, Math.round(1 * u))}px solid ${rgba(t.renk.yazi, 0.06)}`,
                  boxShadow: kazananMi
                    ? `inset 0 ${1.5 * u}px 0 ${ton(vurgu, -0.45, 0.7 * vurguAcik)}, 0 0 ${24 * u}px ${rgba(vurgu, 0.22 * vurguAcik)}`
                    : undefined,
                  padding: `${Math.round(14 * u)}px ${Math.round(16 * u)}px`,
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  justifyContent: "center",
                  gap: Math.round(8 * u),
                  boxSizing: "border-box",
                  overflow: "hidden",
                  opacity: a.belir * (0.28 + 0.72 * s.gir) * sakinOp * (1 - a.cik),
                  transform: `translateX(${s.x}px) scale(${kazananMi ? 1 + 0.014 * vurguAcik : 1})`,
                }}
              >
                {kazananMi && (
                  <>
                    <div
                      style={{
                        position: "absolute",
                        left: 0,
                        right: 0,
                        top: 0,
                        height: Math.max(4 * u, Math.round(5 * u)),
                        background: `linear-gradient(90deg, ${ton(vurgu, -0.35)}, ${vurgu}, ${ton(vurgu, -0.35)})`,
                        boxShadow: `0 0 ${12 * u}px ${rgba(vurgu, 0.65)}`,
                        transformOrigin: "center center",
                        transform: `scaleX(${vurguAcik * (1 - a.cik)})`,
                      }}
                    />
                    <div style={parlamaStil(t, Math.min(1, kazananVurgu), u)} />
                  </>
                )}

                <div
                  style={{
                    fontFamily: yigin(t.font.baslik),
                    fontWeight: t.font.agirlik_baslik,
                    fontSize: baslikBoy,
                    lineHeight: 1.1,
                    letterSpacing: `${Math.max(0.04, t.font.izleme)}em`,
                    color: kazananMi ? ton(vurgu, -0.25) : t.renk.soluk,
                    whiteSpace: "nowrap",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    maxWidth: "100%",
                  }}
                >
                  {harf(t, s.baslik)}
                </div>

                <div
                  style={{
                    fontFamily: rakamFontu(t),
                    fontWeight: t.font.agirlik_baslik,
                    fontSize: degerBoy,
                    lineHeight: 1.0,
                    fontVariantNumeric: "tabular-nums",
                    color: kazananMi ? vurgu : t.renk.yazi,
                    textShadow: kazananMi
                      ? `0 0 ${18 * u}px ${rgba(vurgu, 0.45)}, ${g.yazi !== "none" ? g.yazi : `0 ${3 * u}px ${10 * u}px ${rgba(t.renk.ikon_kontur, 0.45)}`}`
                      : g.yazi,
                    whiteSpace: "nowrap",
                    transform: `scale(${kazananMi ? 1 + 0.08 * kazananAtim + 0.02 * (kazananYay - 1) : 1})`,
                  }}
                >
                  {s.deger}
                </div>

                {s.alt.trim().length > 0 && (
                  <div
                    style={{
                      fontFamily: yigin(t.font.govde),
                      fontWeight: t.font.agirlik_govde,
                      fontSize: altBoy,
                      lineHeight: 1.18,
                      color: kazananMi ? t.renk.yazi : t.renk.soluk,
                      textAlign: "center",
                      whiteSpace: "nowrap",
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                      maxWidth: "100%",
                    }}
                  >
                    {harf(t, s.alt)}
                  </div>
                )}
              </div>
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
};

export default tanimla({ meta: meta as never, sema, Bilesen: Karsilastirma });
