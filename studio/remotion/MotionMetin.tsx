import React from "react";
import { Easing, useCurrentFrame, useVideoConfig } from "remotion";
import { ez } from "../../openmontage/remotion-composer/src/SplitReel";
import { duz, metinG, parca, sigdir, yerlesim } from "./metinOlcu";
import {
  adimKare, egriler, golge, harf, kenar, panel, panelArka, parlamaStil, rakamFontu,
  rgba, titremeOpaklik, titresim, useTema, yigin, yuzeyStil, yuzeyYazi, type TemaToken,
} from "./tema";
import type { Kaynak, Klip, MetinStil } from "./tipler";

// WHY: bkz. wiki/decisions/0031-motion-grafik.md ve 0043-stile-bagli-tema-tokenlari.md. Altyazıdan ayrı nesneler:
// kutu/şerit olabilir. Renk, font, köşe, gölge, doku, yüzey malzemesi ve hareket seçili stilin token'ından gelir (tema.ts);
// klipteki metin_stil rengi yalnız istisnadır. Giriş ve çıkış klibin kendi süresinden hesaplanır.

const useZarf = (k: Klip) => {
  const t = useTema();
  const ham = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const f = adimKare(t, ham, fps);
  const D = Math.max(2, Math.round(k.sure * fps));
  const n = Math.max(2, Math.min(10, Math.floor(D / 4)));
  const e = egriler(t);
  const u = Math.min(width, height) / 1080;
  const cik = 1 - ez(f, D - n, D, e.cik);
  const basamak = t.hareket.easing === "basamak" || !!t.hareket.adim_fps;
  const pBas = Math.min(8, Math.floor(D * 0.2));
  const pSon = Math.min(D - 1, pBas + Math.max(10, Math.round(0.55 * fps)));
  const parlama = ez(f, pBas, pSon, e.gir);
  const nefes = basamak ? 0 : Math.sin((2 * Math.PI * f) / (fps * 2.4)) * cik;
  const blurGir = (p: number, maxPx = 4): string | undefined => {
    if (basamak || p >= 0.96) return undefined;
    const px = (1 - p) * maxPx * u;
    return px > 0.2 ? `blur(${px.toFixed(2)}px)` : undefined;
  };
  return {
    t, e, f, fps, D, W: width, H: height, u, cik, basamak, parlama, nefes, blurGir,
    POP: e.pop, ICE: e.cik,
    fb: yigin(t.font.baslik), fg: yigin(t.font.govde), g: golge(t, u), kose: t.sekil.kose * u,
    ek: titresim(t, f, u), tit: titremeOpaklik(t, f),
  };
};
// Video üstündeki yazı (panelsiz): altyazı token'ının gövde ve kontur rengi, vurgu altyazının aktif rengi.
const ustYazi = (t: TemaToken) => ({ renk: t.altyazi.renk, kontur: t.altyazi.kontur_renk, vurgu: t.altyazi.aktif_renk });

// Çapa noktasına yerleşir; hiza çapadan gelir (metinOlcu.yerlesim).
const Yer: React.FC<{ y: ReturnType<typeof yerlesim>; donus?: string; style?: React.CSSProperties; children: React.ReactNode }> = ({ y, donus = "", style, children }) => {
  const tx = y.hiza === "sol" ? 0 : y.hiza === "sag" ? -100 : -50;
  return (
    <div style={{ position: "absolute", left: y.x, top: y.y, maxWidth: y.genislik, transform: `translate(${tx}%, -50%) ${donus}`,
      transformOrigin: `${-tx}% 50%`, textAlign: y.hiza === "sol" ? "left" : y.hiza === "sag" ? "right" : "center", ...style }}>{children}</div>
  );
};

const Parcali: React.FC<{ s: string; vurgu: string }> = ({ s, vurgu }) => <>{parca(s).map((p, i) => <span key={i} style={p.v ? { color: vurgu } : undefined}>{p.t}</span>)}</>;
const buyut = (s: string, m: MetinStil, vars: boolean) => ((m.buyuk ?? vars) ? s.toLocaleUpperCase("tr-TR") : s);
// Klip rengi istisnadır (kurgu-denetle stil dışı rengi uyarır); yoksa stilin rengi.
const vurguOf = (m: MetinStil, t: TemaToken) => m.vurgu ?? t.renk.vurgu;

type P = { k: Klip; m: MetinStil };

const Anahtar: React.FC<P> = ({ k, m }) => {
  const z = useZarf(k);
  const y = yerlesim("anahtar", m.konum, z.W, z.H);
  const metin = buyut(k.metin ?? "", m, true);
  const b = sigdir(duz(metin), (m.boyut ?? 150) * z.u, y.genislik, 2);
  const gir = ez(z.f, 0, 11, z.e.gir);
  const pop = ez(z.f, 0, 10, z.POP);
  const s = (0.9 + 0.1 * pop) * (0.95 + 0.05 * z.cik) * (1 + 0.004 * z.nefes);
  const o = ustYazi(z.t);
  const pay = Math.round(b * 0.22);
  return (
    <Yer y={y} donus={`scale(${s}) ${z.ek}`} style={{ opacity: Math.min(ez(z.f, 0, 4), z.cik) * z.tit, filter: z.blurGir(gir, 5), width: "max-content" }}>
      <div style={{ overflow: "hidden", padding: `${pay}px ${Math.round(pay * 0.7)}px`, margin: `-${pay}px -${Math.round(pay * 0.7)}px` }}>
        <div style={{
          transform: `translateY(${(1 - gir) * 38}%)`,
          fontFamily: z.fb, fontWeight: z.t.font.agirlik_baslik, fontSize: b, lineHeight: 1.02,
          letterSpacing: `${z.t.font.izleme - 0.01}em`, color: m.renk ?? o.renk,
          WebkitTextStroke: `${b * 0.07}px ${o.kontur}`, paintOrder: "stroke fill" as any,
          textShadow: z.g.yazi,
        }}>
          <Parcali s={metin} vurgu={m.vurgu ?? o.vurgu} />
        </div>
      </div>
    </Yer>
  );
};

const Altbant: React.FC<P> = ({ k, m }) => {
  const z = useZarf(k);
  const y = yerlesim("altbant", m.konum, z.W, z.H);
  const [ad = "", unvan = ""] = (k.metin ?? "").split("\n");
  const ic = y.genislik - 80 * z.u;
  const adB = sigdir(ad, (m.boyut ?? 62) * z.u, ic, 1), unvanB = sigdir(unvan, 0.58 * (m.boyut ?? 62) * z.u, ic, 1);
  const cik = ez(z.f, z.D - 12, z.D, z.ICE);
  const bar = ez(z.f, 0, 8, z.e.gir) * (1 - ez(z.f, z.D - 6, z.D, z.ICE));
  const acil = ez(z.f, 2, 14, z.e.gir);
  const adGir = ez(z.f, 6, 17, z.e.gir);
  const unvGir = ez(z.f, 10, 21, z.e.gir);
  const yuzey = yuzeyStil(z.t, z.u, "bant");
  const renk = vurguOf(m, z.t);
  return (
    <Yer y={y} donus={z.ek} style={{ display: "flex", alignItems: "stretch", textAlign: "left", opacity: z.tit }}>
      <div style={{
        width: Math.max(8, z.t.sekil.cizgi * 2) * z.u, flex: "none",
        background: `linear-gradient(180deg, ${renk} 0%, ${rgba(renk, 0.78)} 100%)`,
        borderRadius: `${z.kose * 0.4}px 0 0 ${z.kose * 0.4}px`,
        boxShadow: `0 0 ${12 * z.u}px ${rgba(renk, 0.45)}`,
        transform: `scaleY(${bar})`, transformOrigin: "50% 100%",
      }} />
      <div style={{
        ...yuzey,
        ...(m.arka ? { background: m.arka } : {}),
        position: "relative", overflow: "hidden",
        padding: `${18 * z.u}px ${34 * z.u}px ${20 * z.u}px ${26 * z.u}px`,
        borderRadius: `0 ${z.kose}px ${z.kose}px 0`,
        borderLeft: "none",
        clipPath: `inset(0 ${Math.min(100, (1 - acil + cik) * 100)}% 0 0)`,
        filter: z.blurGir(acil, 3.5),
      }}>
        <div style={{ fontFamily: z.fb, whiteSpace: "nowrap" }}>
          <div style={{ overflow: "hidden" }}>
            <div style={{
              opacity: adGir, transform: `translateY(${(1 - adGir) * 85}%)`,
              fontWeight: z.t.font.agirlik_baslik, fontSize: adB, lineHeight: 1.12,
              color: m.renk ?? z.t.renk.yazi, letterSpacing: `${z.t.font.izleme}em`,
            }}>{harf(z.t, ad)}</div>
          </div>
          {unvan && (
            <div style={{ overflow: "hidden", marginTop: 4 * z.u }}>
              <div style={{
                opacity: unvGir, transform: `translateY(${(1 - unvGir) * 90}%)`,
                fontFamily: z.fg, fontWeight: z.t.font.agirlik_govde, fontSize: unvanB, lineHeight: 1.2,
                color: z.t.renk.soluk,
              }}>{unvan}</div>
            </div>
          )}
        </div>
        <div style={parlamaStil(z.t, z.parlama, z.u)} />
      </div>
    </Yer>
  );
};

const Etiket: React.FC<P> = ({ k, m }) => {
  const z = useZarf(k);
  const y = yerlesim("etiket", m.konum, z.W, z.H);
  const metin = k.metin ?? "";
  const b = sigdir(duz(metin), (m.boyut ?? 52) * z.u, y.genislik - 56 * z.u, 2);
  const p = ez(z.f, 0, 10, z.POP);
  const yaziGir = ez(z.f, 2, 12, z.e.gir);
  const rozet = yuzeyStil(z.t, z.u, "rozet");
  const vurg = yuzeyStil(z.t, z.u, "vurgulu");
  const ozelArka = m.arka ? { background: m.arka } : m.vurgu ? { background: panelArka(z.t, m.vurgu) } : {};
  return (
    <Yer
      y={y}
      donus={`translateY(${(1 - z.cik) * -12 * z.u}px) scale(${(0.88 + 0.12 * p) * (1 + 0.005 * z.nefes)}) ${z.ek}`}
      style={{
        ...vurg,
        borderRadius: rozet.borderRadius,
        ...ozelArka,
        position: "relative", overflow: "hidden",
        opacity: Math.min(ez(z.f, 0, 4), z.cik) * z.tit,
        filter: z.blurGir(p, 3.5),
        color: m.renk ?? yuzeyYazi(z.t, "vurgulu"),
        padding: `${12 * z.u}px ${28 * z.u}px`,
        fontFamily: z.fb, fontWeight: z.t.font.agirlik_baslik, fontSize: b, lineHeight: 1.12,
        width: "max-content",
      }}
    >
      <div style={{ overflow: "hidden" }}>
        <div style={{ transform: `translateY(${(1 - yaziGir) * 75}%)`, opacity: yaziGir }}>
          <Parcali s={harf(z.t, metin)} vurgu={z.t.renk.yazi} />
        </div>
      </div>
      <div style={parlamaStil(z.t, z.parlama, z.u)} />
    </Yer>
  );
};

const Cagri: React.FC<P> = ({ k, m }) => {
  const z = useZarf(k);
  const y = yerlesim("cagri", m.konum, z.W, z.H);
  const h = m.hedef ?? { x: 0.5, y: 0.4 };
  const hx = h.x * z.W, hy = h.y * z.H, renk = vurguOf(m, z.t);
  const metin = k.metin ?? "";
  const b = sigdir(duz(metin), (m.boyut ?? 44) * z.u, Math.min(y.genislik, 0.7 * z.W) - 52 * z.u, 2);
  // Etiketin çizim merkezi (hizaya göre) çizginin başıdır; etiket çizginin üstünde durur.
  const genis = Math.min(metinG(duz(metin)) * b + 52 * z.u, y.genislik);
  const lx = y.hiza === "sol" ? y.x + genis / 2 : y.hiza === "sag" ? y.x - genis / 2 : y.x;
  const kartGir = ez(z.f, 0, 10, z.POP);
  const yaziGir = ez(z.f, 3, 13, z.e.gir);
  const cizgi = ez(z.f, 4, 17, z.e.gir), nokta = ez(z.f, 14, 23, z.POP), dalga = ez(z.f, 17, 40, z.e.gir);
  const kare = z.t.sekil.kose === 0, cap = kare ? "square" : "round";
  const yuzey = yuzeyStil(z.t, z.u, "kart");
  return (
    <div style={{ position: "absolute", inset: 0, opacity: z.cik * z.tit }}>
      <svg width={z.W} height={z.H} style={{ position: "absolute", inset: 0, overflow: "visible", filter: z.g.filtre }}>
        <path d={`M ${lx} ${y.y} L ${hx} ${hy}`} pathLength={1} fill="none" stroke={renk} strokeWidth={Math.max(3.5, z.t.sekil.cizgi) * 1.4 * z.u} strokeLinecap={cap}
          strokeDasharray="1 2" strokeDashoffset={1 - cizgi} />
        <circle cx={hx} cy={hy} r={13 * z.u * (1 + 1.5 * dalga)} fill="none" stroke={renk} strokeWidth={Math.max(2.5, z.t.sekil.cizgi * 0.8) * z.u} opacity={nokta * (1 - dalga) * 0.85} />
        {kare
          ? <rect x={hx - 12 * z.u * nokta} y={hy - 12 * z.u * nokta} width={24 * z.u * nokta} height={24 * z.u * nokta} fill={renk} stroke={z.t.renk.ikon_kontur} strokeWidth={3 * z.u} />
          : <circle cx={hx} cy={hy} r={12 * z.u * nokta} fill={renk} stroke={z.t.renk.ikon_kontur} strokeWidth={3 * z.u} />}
      </svg>
      <Yer
        y={y}
        donus={`scale(${0.88 + 0.12 * kartGir}) ${z.ek}`}
        style={{
          ...yuzey,
          ...(m.arka ? { background: m.arka } : {}),
          position: "relative", overflow: "hidden",
          opacity: ez(z.f, 0, 4),
          filter: z.blurGir(kartGir, 3.5),
          color: m.renk ?? z.t.renk.yazi,
          borderColor: rgba(renk, 0.72),
          padding: `${13 * z.u}px ${24 * z.u}px`,
          fontFamily: z.fb, fontWeight: z.t.font.agirlik_baslik,
          fontSize: b, lineHeight: 1.15, width: "max-content", maxWidth: Math.min(y.genislik, 0.7 * z.W),
        }}
      >
        <div style={{ overflow: "hidden" }}>
          <div style={{ transform: `translateY(${(1 - yaziGir) * 70}%)`, opacity: yaziGir }}>
            <Parcali s={metin} vurgu={renk} />
          </div>
        </div>
        <div style={parlamaStil(z.t, z.parlama, z.u)} />
      </Yer>
    </div>
  );
};

const Daktilo: React.FC<P> = ({ k, m }) => {
  const z = useZarf(k);
  const y = yerlesim("daktilo", m.konum, z.W, z.H);
  const harfler = [...(k.metin ?? "")];
  const n = Math.floor(Math.min(harfler.length, Math.max(0, ((z.f - 4) / z.fps) * (m.hiz ?? 22))));
  const b = sigdir(k.metin ?? "", (m.boyut ?? 58) * z.u, y.genislik - 60 * z.u, 3);
  const yanar = n < harfler.length || Math.floor(z.f / (z.fps * 0.5)) % 2 === 0;
  const gir = ez(z.f, 0, 8, z.e.gir);
  const yuzey = yuzeyStil(z.t, z.u, "kart");
  const renk = vurguOf(m, z.t);
  return (
    <Yer
      y={y}
      donus={`scale(${0.95 + 0.05 * gir}) ${z.ek}`}
      style={{
        ...yuzey,
        ...(m.arka ? { background: m.arka } : {}),
        position: "relative", overflow: "hidden",
        opacity: Math.min(ez(z.f, 0, 6), z.cik) * z.tit,
        filter: z.blurGir(gir, 3.5),
        padding: `${22 * z.u}px ${30 * z.u}px`,
        fontFamily: yigin(z.t.font.mono), fontWeight: 600, fontSize: b, lineHeight: 1.22,
        color: m.renk ?? z.t.renk.yazi, whiteSpace: "pre-wrap", textAlign: "left",
      }}
    >
      <div style={{
        position: "absolute", top: 0, left: 0, right: 0, height: Math.max(2, 2.5 * z.u),
        background: `linear-gradient(90deg, ${renk} 0%, ${rgba(renk, 0.35)} 55%, transparent 100%)`,
      }} />
      {harfler.slice(0, n).join("")}
      <span style={{ position: "relative" }}>
        <span style={{
          position: "absolute", left: 2, top: "0.1em", width: "0.085em", height: "0.96em",
          background: renk, borderRadius: 1 * z.u,
          boxShadow: `0 0 ${8 * z.u}px ${rgba(renk, 0.75)}`,
          opacity: yanar ? 1 : 0,
        }} />
      </span>
      {/* kalan harfler yer tutar: yazarken satır kırılımı oynamaz */}
      <span style={{ color: "transparent" }}>{harfler.slice(n).join("")}</span>
      <div style={parlamaStil(z.t, z.parlama, z.u)} />
    </Yer>
  );
};

const Sayac: React.FC<P> = ({ k, m }) => {
  const z = useZarf(k);
  const y = yerlesim("sayac", m.konum, z.W, z.H);
  const d = m.ondalik ?? 0, bas = m.baslangic ?? 0, hedef = Number(m.deger ?? 0);
  const sure = Math.min(1.2 * z.fps, 0.6 * z.D);
  const kk = ez(z.f, 4, 4 + sure, z.t.hareket.easing === "basamak" ? z.e.gir : Easing.out(Easing.exp));
  const bicim = (v: number) => v.toLocaleString("tr-TR", { minimumFractionDigits: d, maximumFractionDigits: d });
  const son = `${m.onek ?? ""}${bicim(hedef)}${m.sonek ?? ""}`;
  const b = sigdir(son, (m.boyut ?? 170) * z.u, y.genislik - 80 * z.u, 1);
  const bitti = z.f - (4 + sure);
  const pop = bitti > 0 ? 1 + 0.055 * Math.sin(Math.min(1, bitti / (0.3 * z.fps)) * Math.PI) : 1;
  const gir = ez(z.f, 0, 10, z.POP);
  const yaziGir = ez(z.f, 3, 13, z.e.gir);
  const altGir = ez(z.f, 7, 17, z.e.gir);
  const parl = ez(z.f, 4 + Math.round(sure * 0.7), Math.min(z.D - 1, 4 + Math.round(sure * 0.7) + Math.round(0.55 * z.fps)), z.e.gir);
  const renk = vurguOf(m, z.t);
  const yuzey = yuzeyStil(z.t, z.u, "kart");
  return (
    <Yer
      y={y}
      donus={`scale(${(0.88 + 0.12 * gir) * pop * (1 + 0.004 * z.nefes)}) ${z.ek}`}
      style={{
        ...yuzey,
        ...(m.arka ? { background: m.arka } : {}),
        position: "relative", overflow: "hidden",
        opacity: Math.min(ez(z.f, 0, 4), z.cik) * z.tit,
        filter: z.blurGir(gir, 4),
        padding: `${18 * z.u}px ${42 * z.u}px ${22 * z.u}px`,
        borderRadius: z.kose * 1.4,
        fontFamily: z.fb, color: m.renk ?? z.t.renk.yazi, textAlign: "center",
      }}
    >
      <div style={{ overflow: "hidden" }}>
        <div style={{
          transform: `translateY(${(1 - yaziGir) * 55}%)`, opacity: yaziGir,
          fontFamily: rakamFontu(z.t), fontWeight: z.t.font.agirlik_baslik, fontSize: b, lineHeight: 1.05,
          fontVariantNumeric: "tabular-nums", whiteSpace: "nowrap", minWidth: metinG(son) * b * 0.94,
        }}>
          {m.onek && <span style={{ color: renk }}>{m.onek}</span>}
          {bicim(bas + (hedef - bas) * kk)}
          {m.sonek && <span style={{ color: renk }}>{m.sonek}</span>}
        </div>
      </div>
      {k.metin && (
        <div style={{ overflow: "hidden", marginTop: 6 * z.u }}>
          <div style={{
            transform: `translateY(${(1 - altGir) * 75}%)`, opacity: altGir,
            fontFamily: z.fg, fontWeight: z.t.font.agirlik_govde,
            fontSize: sigdir(k.metin, 40 * z.u, y.genislik - 80 * z.u, 2),
            lineHeight: 1.2, color: z.t.renk.soluk,
          }}>{harf(z.t, k.metin)}</div>
        </div>
      )}
      <div style={parlamaStil(z.t, parl, z.u)} />
    </Yer>
  );
};

const Ilerleme: React.FC<P> = ({ k, m }) => {
  const z = useZarf(k);
  const y = yerlesim("ilerleme", m.konum, z.W, z.H);
  const toplam = Math.max(1, Math.round(m.toplam ?? 3)), adim = Math.min(toplam, Math.max(1, Math.round(m.adim ?? 1)));
  const genis = Math.min(y.genislik, 0.84 * z.W), renk = vurguOf(m, z.t);
  const dol = ez(z.f, 6, 22, z.e.gir);
  const g = ez(z.f, 0, 10);
  const yazi = sigdir(k.metin ?? "", 34 * z.u, genis - 160 * z.u, 1);
  return (
    <Yer y={y} donus={`translateY(${(1 - g) * -20 * z.u}px) ${z.ek}`} style={{ opacity: Math.min(g, z.cik) * z.tit, width: genis, boxSizing: "border-box", background: m.arka ?? panelArka(z.t),
      padding: `${14 * z.u}px ${22 * z.u}px ${18 * z.u}px`, borderRadius: z.kose, border: kenar(z.t, z.u), boxShadow: z.g.kutu, fontFamily: z.fb, textAlign: "left" }}>
      <div style={{ display: "flex", alignItems: "baseline", gap: 16 * z.u, marginBottom: 12 * z.u, whiteSpace: "nowrap" }}>
        <span style={{ fontFamily: rakamFontu(z.t), fontWeight: z.t.font.agirlik_baslik, fontSize: 34 * z.u, color: renk, fontVariantNumeric: "tabular-nums" }}>{adim}/{toplam}</span>
        <span style={{ fontWeight: z.t.font.agirlik_baslik, fontSize: yazi, color: m.renk ?? z.t.renk.yazi }}>{harf(z.t, k.metin ?? "")}</span>
      </div>
      <div style={{ display: "flex", gap: 8 * z.u }}>
        {Array.from({ length: toplam }, (_, i) => (
          <div key={i} style={{ flex: 1, height: 12 * z.u, borderRadius: Math.min(6, z.t.sekil.kose / 2) * z.u, background: rgba(z.t.renk.yazi, 0.18), overflow: "hidden" }}>
            <div style={{ height: "100%", background: renk, width: `${(i < adim - 1 ? 1 : i === adim - 1 ? dol : 0) * 100}%` }} />
          </div>
        ))}
      </div>
    </Yer>
  );
};

const Bolum: React.FC<P> = ({ k, m }) => {
  const z = useZarf(k);
  const y = yerlesim("bolum", m.konum, z.W, z.H);
  const baslik = buyut(k.metin ?? "", m, true), no = String(m.numara ?? "01");
  const genis = Math.min(y.genislik, (z.W > z.H ? 0.62 : 0.9) * z.W);
  const noB = 110 * z.u;
  const b = sigdir(duz(baslik), (m.boyut ?? 84) * z.u, genis - metinG(no) * noB - 120 * z.u, 2);
  const serit = ez(z.f, 0, 10, z.e.gir), acil = ez(z.f, 6, 18, z.e.gir), kapan = ez(z.f, z.D - 12, z.D, z.ICE);
  const renk = vurguOf(m, z.t);
  return (
    <Yer y={y} donus={z.ek} style={{ width: genis, opacity: z.tit, filter: z.g.filtre }}>
      <div style={{ position: "relative", clipPath: `inset(0 ${(1 - acil) * 100}% 0 ${kapan * 100}%)`, background: m.arka ?? panelArka(z.t, panel(z.t, 0.96)),
        borderRadius: z.kose * 1.4, border: kenar(z.t, z.u), padding: `${26 * z.u}px ${36 * z.u}px`, display: "flex", alignItems: "center", gap: 28 * z.u, textAlign: "left", fontFamily: z.fb }}>
        <span style={{ fontFamily: rakamFontu(z.t), fontWeight: z.t.font.agirlik_baslik, fontSize: noB, lineHeight: 1, color: renk, fontVariantNumeric: "tabular-nums" }}>{no}</span>
        <span style={{ alignSelf: "stretch", width: Math.max(2, z.t.sekil.cizgi) * z.u, background: rgba(z.t.renk.yazi, 0.22), flex: "none" }} />
        <span style={{ fontWeight: z.t.font.agirlik_baslik, fontSize: b, lineHeight: 1.05, letterSpacing: `${z.t.font.izleme}em`, color: m.renk ?? z.t.renk.yazi }}><Parcali s={baslik} vurgu={renk} /></span>
      </div>
      <div style={{ position: "absolute", inset: 0, borderRadius: z.kose * 1.4, background: renk, clipPath: `inset(0 ${(1 - serit) * 100}% 0 ${acil * 100}%)` }} />
    </Yer>
  );
};

// El çizimi iz: dalgalı yarıçaplı 1,1 tur elips, taşan köşeli kutu ya da kavisli alt çizgi.
const vurguYolu = (bicim: string, x: number, y: number, w: number, h: number, u: number) => {
  if (bicim === "daire") {
    const cx = x + w / 2, cy = y + h / 2, rx = w / 2 + 22 * u, ry = h / 2 + 22 * u;
    const n = 56, d: string[] = [];
    for (let i = 0; i <= n; i++) {
      const a = -1.9 + (i / n) * Math.PI * 2 * 1.08, r = 1 + 0.03 * Math.sin(2 * a + 0.7) + 0.012 * i / n;
      d.push(`${i ? "L" : "M"} ${(cx + Math.cos(a) * rx * r).toFixed(1)} ${(cy + Math.sin(a) * ry * r).toFixed(1)}`);
    }
    return d.join(" ");
  }
  if (bicim === "alt_cizgi") return `M ${x - 6 * u} ${y + h + 12 * u} Q ${x + w * 0.55} ${y + h + 26 * u} ${x + w + 8 * u} ${y + h + 6 * u}`;
  const p = 12 * u, x0 = x - p, y0 = y - p, x1 = x + w + p, y1 = y + h + p;
  return `M ${x0 + 10 * u} ${y0 + 2 * u} L ${x1 - 4 * u} ${y0 - 2 * u} Q ${x1 + 2 * u} ${y0} ${x1 + 1 * u} ${y0 + 8 * u} L ${x1 + 3 * u} ${y1 - 6 * u}`
    + ` Q ${x1} ${y1 + 2 * u} ${x1 - 8 * u} ${y1 + 1 * u} L ${x0 + 4 * u} ${y1 + 3 * u} Q ${x0 - 3 * u} ${y1} ${x0 - 2 * u} ${y1 - 8 * u}`
    + ` L ${x0 - 1 * u} ${y0 + 10 * u} Q ${x0} ${y0 - 1 * u} ${x0 + 14 * u} ${y0 + 1 * u} L ${x0 + 0.18 * (x1 - x0)} ${y0 - 1 * u}`;
};

// Görsel klibinde kutu görselin çizildiği alana göredir (objectFit contain); metin klibinde kareye göre.
export const Vurgu: React.FC<P & { kaynak?: Kaynak }> = ({ k, m, kaynak }) => {
  const z = useZarf(k);
  let ax = 0, ay = 0, aw = z.W, ah = z.H;
  if (kaynak?.w && kaynak.h) {
    const s = Math.min(z.W / kaynak.w, z.H / kaynak.h);
    aw = kaynak.w * s; ah = kaynak.h * s; ax = (z.W - aw) / 2; ay = (z.H - ah) / 2;
  }
  const q = m.kutu ?? { x: 0.3, y: 0.4, w: 0.4, h: 0.1 };
  const d = vurguYolu(m.bicim ?? "kutu", ax + q.x * aw, ay + q.y * ah, q.w * aw, q.h * ah, z.u);
  const ciz = ez(z.f, 2, 2 + Math.min(18, z.D * 0.4), z.e.gir);
  const renk = m.renk ?? vurguOf(m, z.t);
  const kare = z.t.sekil.kose === 0;
  return (
    <svg width={z.W} height={z.H} style={{ position: "absolute", inset: 0, overflow: "visible", opacity: z.cik * z.tit, filter: z.g.filtre, transform: z.ek || undefined }}>
      <path d={d} pathLength={1} fill="none" stroke={renk} strokeWidth={(m.kalinlik ?? Math.max(8, z.t.sekil.cizgi * 2)) * z.u} strokeLinecap={kare ? "square" : "round"} strokeLinejoin={kare ? "miter" : "round"}
        strokeDasharray="1 2" strokeDashoffset={1 - ciz} />
    </svg>
  );
};

const TIPLER: Record<string, React.FC<P>> = { anahtar: Anahtar, altbant: Altbant, etiket: Etiket, cagri: Cagri, daktilo: Daktilo, sayac: Sayac, ilerleme: Ilerleme, bolum: Bolum, vurgu: Vurgu };
export const METIN_TIPLERI = Object.keys(TIPLER);

export const MetinGrafik: React.FC<P> = ({ k, m }) => {
  const C = TIPLER[m.tip ?? ""];
  return C ? <C k={k} m={m} /> : null;
};
