import React, { useContext, useEffect, useMemo, useState } from "react";
import {
  AbsoluteFill, Audio, Easing, Img, Internals, OffthreadVideo, Sequence, continueRender, delayRender,
  staticFile, useCurrentFrame, useVideoConfig,
} from "remotion";
import { CAP_SPLIT_Y, CAP_Y, Captions, FONTS, FullTitle, STAGE_H, StageScene, T, buildPages, buildTokens, ez, layoutP, rgbaOf, temaUygula } from "../../openmontage/remotion-composer/src/SplitReel";
import { genislet, deger, YON, type Izler } from "./hazirEfekt";
import { GecisSarici, ortaMi } from "./gecisler";
import { izdusum, sesEgrisi } from "./izdusum";
import { MetinGrafik, Vurgu } from "./MotionMetin";
import { FizikSahne } from "./fizik/FizikSahne";
import { KarakterSahne } from "./karakter/Karakter";
import { BolgeSaglayici, MotionKatman } from "./motion/cekirdek/Katman";
import { altyaziBandi, yuzPayi } from "./motion/cekirdek/yerlesim";
import { TemaSaglayici, golge, rgba, useTema, yigin, type TemaToken } from "./tema";
import type { AltyaziStil, Gecis, Kelime, Klip, KurguProps } from "./tipler";

// WHY: bkz. wiki/decisions/0021-video-studyo-nle.md. Önizleme ve render aynı bileşeni çalıştırır.

// WHY: bkz. wiki/decisions/0022-av-ayirma-metre-yatay.md. Yatayda sahne solda, konuşmacı sağda. SplitReel git dışıdır ve
// sahneler 1080x998 için çizilmiştir: yeniden yazmak yerine kutu ölçeklenir, dikey kod yolu değişmez.
const yatayDuzen = (width: number, height: number) => {
  const olcek = height / STAGE_H;
  return { olcek, sahneG: Math.round(1080 * olcek) };
};
const YATAY_ALTYAZI_Y = 945; // alt güvenli alan, 1080 yüksekliğin %87'si
const YATAY_BASLIK_KAYMA = -530; // FullTitle dikeyde 1010'dan başlar; yatayda alt üçte bire iner

// Önizlemede ana ses düğümüne metre takılır. Internals iç API'dir: Remotion sürümü package.json'da birebir sabittir.
const MetreKoprusu: React.FC<{ bagla: NonNullable<KurguProps["metreBagla"]> }> = ({ bagla }) => {
  const c = useContext(Internals.SharedAudioContext);
  const ctx = c?.audioContext, ana = c?.gainNode;
  useEffect(() => (ctx && ana ? bagla(ctx as AudioContext, ana) : undefined), [ctx, ana, bagla]);
  return null;
};

const kaynakAdresi = (p: KurguProps, id: string): string => {
  const onizleme = p.medya?.[id];
  if (onizleme) return onizleme;
  const y = p.kaynaklar[id].yol;
  if (y.startsWith("public:")) return staticFile(y.slice(7));
  const uzanti = y.slice(y.lastIndexOf(".")).toLowerCase();
  return staticFile(`_k/${id}${uzanti}`);
};

// WHY: tarayıcı currentTime tam kare sınırına düşünce yuvarlama yüzünden önceki kareyi gösterebilir (ölçüldü, ADR 0021).
// Önizlemede kare ortasına bakılır; render zaten kareyi tam çıkarır.
// on: orta noktalı geçişte klibin kesimden önce başladığı ön pay (sn); kaynakta o kadar geriden okunur.
const kirpBas = (p: KurguProps, k: Klip, fps: number, on = 0) => {
  const kare = Math.round((k.giris - on * k.hiz) * fps);
  return p.onizleme ? kare + 0.5 : kare || undefined;
};

// Çapraz geçişte önceki klip kuyruğu altta sürer: kaynakta kalan kadar. Orta noktalı geçişte yarısı (ADR 0045).
const kuyrukPayi = (p: KurguProps, k: Klip, sonra: Klip | undefined) => {
  const g = sonra?.gecis_giris;
  if (!g || g.tur === "kararma" || Math.abs(k.bas + k.sure - sonra.bas) > 1e-3) return 0;
  const istek = ortaMi(g) ? g.sure / 2 : g.sure;
  const s = k.kaynak ? p.kaynaklar[k.kaynak]?.sure : 0;
  // Süresiz içerik (görsel, metin) tam sürer; video kaynağı bitince geçiş boşluğa açılmasın diye kısılır.
  return s && s > 0 ? Math.max(0, Math.min(istek, (s - k.giris) / k.hiz - k.sure)) : istek;
};

// Orta noktalı geçişte giren klibin ön payı: sürenin yarısı, kaynakta giriş öncesi kalan kadar.
// Görselin kaynağı süresizdir: ön pay her zaman tam yarı.
const onPayi = (k: Klip) => (!ortaMi(k.gecis_giris) ? 0 : k.tur === "gorsel" ? k.gecis_giris.sure / 2 : Math.max(0, Math.min(k.gecis_giris.sure / 2, k.giris / k.hiz)));

// WHY: bkz. wiki/decisions/0033-hazir-efektler.md. El keyframe'i taban, hazır efekt izleri (hz) üstüne biner.
// on: ön pay (sn); keyframe ve hazır efekt klibin kesimdeki başına göre okunur. cikis: sonraki klibin orta noktalı geçişi.
const Donusum: React.FC<{ k: Klip; hz?: Izler[]; style?: React.CSSProperties; on?: number; cikis?: Gecis | null; children: React.ReactNode }> = ({ k, hz, style, on = 0, cikis, children }) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const tSeq = frame / fps;
  const t = tSeq - on;
  const d = k.donus, e = k.efekt;
  let opak = deger(d.opaklik, hz, "opaklik", t, 1);
  let kay = 0, kayY = 0, gs = 1, gbul = 0;
  const gg = ortaMi(k.gecis_giris) ? null : k.gecis_giris, gc = k.gecis_cikis;
  if (gg && t < gg.sure) {
    const a = Math.min(1, t / gg.sure), kalan = 1 - Easing.bezier(0.16, 1, 0.3, 1)(a);
    // shortcut: giren klip hareket eder, çıkan klibin kuyruğu altta sabit kalır; itme hissi yetmezse kuyruğu da kaydır.
    if (gg.tur === "kaydir") kay = kalan * width;
    else if (gg.tur === "it" || gg.tur === "savur") {
      const [vx, vy] = YON[gg.yon ?? "sol"]; // yon görüntünün gittiği yön: giren karşı kenardan gelir
      kay = -vx * kalan * width; kayY = -vy * kalan * height;
      if (gg.tur === "savur") gbul = Math.sin(Math.PI * a) * 24;
    } else {
      opak *= a;
      if (gg.tur === "zoom") gs = 1 + 0.25 * kalan;
      if (gg.tur === "bulanik") gbul = (1 - a) * 20;
    }
  }
  // Çıkış geçişi yalnız kararma: çapraz geçiş sonraki klibin girişindedir.
  if (gc) opak *= Math.min(1, Math.max(0, (k.sure - t) / gc.sure));
  const bul = deger(e.bulanik_kf?.length ? e.bulanik_kf : undefined, hz, "bulanik", t, e.bulanik) + gbul;
  const parl = deger(e.parlaklik_kf?.length ? e.parlaklik_kf : undefined, hz, "parlaklik", t, e.parlaklik);
  const filtre = [
    Math.abs(parl - 1) > 1e-4 && `brightness(${parl})`,
    e.kontrast !== 1 && `contrast(${e.kontrast})`,
    e.doygunluk !== 1 && `saturate(${e.doygunluk})`,
    bul > 0 && `blur(${bul}px)`,
  ].filter(Boolean).join(" ");
  const r = e.kirp;
  const x = deger(d.x, hz, "x", t, 0) + kay, y = deger(d.y, hz, "y", t, 0) + kayY, s = deger(d.olcek, hz, "olcek", t, 1) * gs, a = deger(d.aci, hz, "aci", t, 0);
  let ic = (
    <AbsoluteFill style={{
      opacity: opak === 1 ? undefined : opak, filter: filtre || undefined,
      clipPath: r ? `inset(${(r.ust ?? 0) * height}px ${(r.sag ?? 0) * width}px ${(r.alt ?? 0) * height}px ${(r.sol ?? 0) * width}px)` : undefined,
      // Etkisiz dönüşüm yeni katman açmasın.
      transform: x || y || s !== 1 || a ? `translate(${x}px, ${y}px) scale(${s})${a ? ` rotate(${a}deg)` : ""}` : undefined,
      transformOrigin: d.capa ? `${d.capa.x * 100}% ${d.capa.y * 100}%` : undefined,
      ...style,
    }}>{children}</AbsoluteFill>
  );
  // ADR 0045: orta noktalı geçiş. Giren klip ön paydan başlayarak sunumla açılır; çıkan klip kuyruğunda sunumla ayrılır.
  const og = k.gecis_giris;
  if (ortaMi(og) && tSeq < og.sure) {
    ic = <GecisSarici g={og} ilerleme={tSeq / og.sure} yon="entering" w={width} h={height} sureKare={Math.round(og.sure * fps)}>{ic}</GecisSarici>;
  }
  if (ortaMi(cikis) && t > k.sure - cikis.sure / 2) {
    const ilerleme = (t - (k.sure - cikis.sure / 2)) / cikis.sure;
    ic = <GecisSarici g={cikis} ilerleme={ilerleme} yon="exiting" w={width} h={height} sureKare={Math.round(cikis.sure * fps)}>{ic}</GecisSarici>;
  }
  return ic;
};

// ADR 0046: siyah zeminli dış varlık (light leak, film yanığı) screen ile karışır; siyah kaybolur, ışık kalır.
const karisimStil = (p: KurguProps, k: Klip): React.CSSProperties | undefined =>
  (p.tema as { karisim?: Record<string, string> } | undefined)?.karisim?.[k.kaynak ?? ""] === "screen" ? { mixBlendMode: "screen" } : undefined;

// Ön payda ses kapalı: giren çekimin sesi kesimde başlar; eğri klibin kesimdeki başına göre okunur.
const onluSes = (egri: (f: number) => number, onKare: number) => (onKare ? (f: number) => (f < onKare ? 0 : egri(f - onKare)) : egri);

const Video: React.FC<{ p: KurguProps; k: Klip; izDb: number; sessiz: boolean; kuyruk: number; on?: number }> = ({ p, k, izDb, sessiz, kuyruk, on = 0 }) => {
  const { fps } = useVideoConfig();
  const seffaf = k.tur === "motion" && /\.(webm|mov)$/i.test(p.kaynaklar[k.kaynak!]?.yol ?? "");
  return (
    <OffthreadVideo
      src={kaynakAdresi(p, k.kaynak!)} trimBefore={kirpBas(p, k, fps, on)} transparent={seffaf} useWebAudioApi={!!p.onizleme}
      playbackRate={k.hiz} volume={onluSes(sesEgrisi(k, izDb, fps, kuyruk), Math.round(on * fps))} muted={sessiz}
      style={{ width: "100%", height: "100%", objectFit: "contain" }}
    />
  );
};

// SplitReel Speaker davranışı: bölünmüş sahnede panel iner, punch ve taban zoom.
const Konusmaci: React.FC<{ p: KurguProps; k: Klip; izDb: number; sessiz: boolean; sahneler: any[]; from: number; kuyruk: number; on?: number }> = ({ p, k, izDb, sessiz, sahneler, from, kuyruk, on = 0 }) => {
  const frame = useCurrentFrame() + from;
  const { fps, width, height } = useVideoConfig();
  const lp = layoutP(frame, fps, sahneler);
  const top = STAGE_H * lp;
  let punch = 1, odak: string | undefined;
  for (const pt of k.punches) {
    // Sayı biçimi: +%10, 30. karede bırakır. Nesne: olcek hedef, sure tutma, x/y odak (ADR 0033).
    const n = typeof pt === "number" ? { t: pt } : pt;
    const a = (k.bas + (n.t - k.giris) / k.hiz) * fps;
    const b = typeof pt === "number" ? a + 30 : a + 8 + (n.sure ?? 1) * fps;
    const v = ez(frame, a, a + 8, Easing.bezier(0.34, 1.4, 0.64, 1)) - ez(frame, b, b + 10, Easing.bezier(0.45, 0, 0.55, 1));
    punch += ((n.olcek ?? 1.1) - 1) * v;
    if (v > 0 && (n.x != null || n.y != null)) odak = `${(n.x ?? 0.5) * 100}% ${(n.y ?? 0.5) * 100}%`;
  }
  // Odaklı punch ayrı katmanda kendi noktasına büyür; katman hep çizilir ki video yeniden yüklenmesin.
  const z = (k.zoom + (1 - k.zoom) * lp) * (odak ? 1 : punch);
  const odakStil: React.CSSProperties = { position: "absolute", inset: 0, transformOrigin: odak, transform: odak ? `scale(${punch})` : undefined };
  if (width > height) {
    const sol = yatayDuzen(width, height).sahneG * lp;
    return (
      <div style={{ position: "absolute", left: sol, top: 0, width: width - sol, height, overflow: "hidden", borderRadius: `${40 * lp}px 0 0 ${40 * lp}px`, background: T.bg }}>
        <div style={odakStil}><OffthreadVideo
          src={kaynakAdresi(p, k.kaynak!)} trimBefore={kirpBas(p, k, fps, on)} useWebAudioApi={!!p.onizleme}
          playbackRate={k.hiz} volume={onluSes(sesEgrisi(k, izDb, fps, kuyruk), Math.round(on * fps))} muted={sessiz}
          style={{ position: "absolute", left: -sol / 2, top: 0, width, height, objectFit: "cover", transform: `scale(${z})` }}
        /></div>
      </div>
    );
  }
  return (
    <div style={{ position: "absolute", left: 0, top, width, height: height - top, overflow: "hidden", borderRadius: `${40 * lp}px ${40 * lp}px 0 0`, background: T.bg }}>
      <div style={odakStil}><OffthreadVideo
        src={kaynakAdresi(p, k.kaynak!)} trimBefore={kirpBas(p, k, fps, on)} useWebAudioApi={!!p.onizleme}
        playbackRate={k.hiz} volume={onluSes(sesEgrisi(k, izDb, fps, kuyruk), Math.round(on * fps))} muted={sessiz}
        style={{ position: "absolute", left: 0, top: 0, width, height, transformOrigin: "50% 0%", transform: `translateY(${-273 * lp}px) scale(${z})` }}
      /></div>
    </div>
  );
};

// Standart dışı altyazı. Varsayılan (stil yok) SplitReel Captions'tır: ADR 0014 orada sabittir.
const StilliAltyazi: React.FC<{ stil: AltyaziStil; words: Kelime[]; sahneler: any[] }> = ({ stil, words, sahneler }) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const t = frame / fps;
  const pages = useMemo(() => buildPages(buildTokens(words), stil.en_kelime, stil.en_karakter), [words, stil.en_kelime, stil.en_karakter]);
  const idx = pages.findIndex((pg, i) => t >= pg[0].s - 0.04 && t < (pages[i + 1] ? pages[i + 1][0].s - 0.04 : pg[pg.length - 1].e + 0.5));
  if (idx < 0) return null;
  const pg = pages[idx];
  if (t > pg[pg.length - 1].e + 0.45) return null;
  const lp = layoutP(frame, fps, sahneler);
  const yatay = width > height;
  const y = stil.konum != null ? stil.konum * height : yatay ? YATAY_ALTYAZI_Y : CAP_Y + (CAP_SPLIT_Y - CAP_Y) * lp;
  const sol = yatay ? yatayDuzen(width, height).sahneG * lp : 0;
  return (
    <div style={{ position: "absolute", left: sol + 40, width: width - sol - 80, top: y - stil.boyut, minHeight: stil.boyut * 2, display: "flex", flexWrap: "wrap", justifyContent: "center", alignItems: "center", columnGap: stil.boyut * 0.28 }}>
      {pg.map((tok, i) => {
        const next = pg[i + 1];
        const aktif = stil.kip === "kelime" && t >= tok.s && (next ? t < next.s : t < tok.e + 0.3);
        return (
          <span key={i} style={{ fontFamily: yigin(stil.font), fontWeight: stil.agirlik ?? 800, fontSize: stil.boyut, letterSpacing: stil.kontur / 2 /* konturun dışa taşan yarısı harfleri yapıştırmasın */, lineHeight: 1.1, color: aktif ? stil.aktif_renk : stil.renk,
            WebkitTextStroke: stil.kontur ? `${stil.kontur}px ${stil.kontur_renk}` : undefined, paintOrder: "stroke fill" as any }}>{tok.text}</span>
        );
      })}
    </div>
  );
};

const FontYukle: React.FC<{ ad: string; dosya: string; p: KurguProps }> = ({ ad, dosya, p }) => {
  const [h] = useState(() => delayRender(`font ${ad}`));
  useEffect(() => {
    const url = p.onizleme ? `/lib/fonts/${encodeURIComponent(dosya)}` : staticFile(`fonts/${dosya}`);
    // WHY: eksik veya bozuk font dosyasında load() reddi yakalanmazsa unhandled rejection üretir.
    new FontFace(ad, `url(${url})`, { weight: "100 900" }).load().then((f) => document.fonts.add(f)).catch(() => {}).finally(() => continueRender(h));
  }, [h]);
  return null;
};

// WHY: bkz. wiki/decisions/0043-stile-bagli-tema-tokenlari.md. Stil seçiliyse altyazı stilin token'ından kurulur
// (kurgu.json'daki elle stil önceliklidir); seçili değilse ADR 0014 standardı (Captions) çalışır.
const temaAltyazisi = (t: TemaToken): AltyaziStil => ({
  font: t.altyazi.font, agirlik: t.altyazi.agirlik, boyut: 72, renk: t.altyazi.renk, aktif_renk: t.altyazi.aktif_renk,
  kontur: t.altyazi.kontur, kontur_renk: t.altyazi.kontur_renk, kip: "kelime", en_kelime: 3, en_karakter: 18, konum: null, dosya: null,
});

// Formdan gelen eksik sahne önizlemeyi düşürmesin. Render'da hata saklanmaz, iş durur.
class SahneKoruma extends React.Component<{ etkin: boolean; etiket: string; children: React.ReactNode }, { hata: string | null }> {
  state = { hata: null as string | null };
  static getDerivedStateFromError(e: Error) { return { hata: e.message }; }
  componentDidUpdate(o: { children: React.ReactNode }) { if (o.children !== this.props.children && this.state.hata) this.setState({ hata: null }); }
  render() {
    if (!this.state.hata) return this.props.children;
    if (!this.props.etkin) throw new Error(`${this.props.etiket} sahnesi: ${this.state.hata}`);
    // Yalnız önizlemede görünen hata kutusu; videoya girmez (beyaz listede).
    return <AbsoluteFill style={{ background: "#3a1416", color: "#ffb4b4", font: "600 40px sans-serif", padding: 60, justifyContent: "center" }}>{this.props.etiket}: alanlar eksik. {this.state.hata}</AbsoluteFill>;
  }
}

// Yatay: SplitReel Captions aynen çalışır (ADR 0014), kutusu taşınır. Bölünmüşte konuşmacı sütununa ortalanır, sütuna sığsın diye küçülür.
const YatayAltyazi: React.FC<{ sahneler: any[]; children: React.ReactNode }> = ({ sahneler, children }) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const lp = layoutP(frame, fps, sahneler);
  const cx = width / 2 + (yatayDuzen(width, height).sahneG / 2) * lp;
  return <div style={{ position: "absolute", left: 0, top: 0, width: 1080, transformOrigin: `540px ${CAP_Y}px`, transform: `translate(${cx - 540}px, ${YATAY_ALTYAZI_Y - CAP_Y}px) scale(${1 - 0.2 * lp})` }}>{children}</div>;
};

const sahneAlani = (k: Klip) => ({ ...k.sahne, start: k.bas, end: k.bas + k.sure }) as any;

// WHY: bkz. wiki/decisions/0031-motion-grafik.md. Tam ekran içerik sahnesi: SplitReel'in 1080x998 sahne kutusu aynen çizilir.
// Dikeyde üst güvenli alanın altına, yatayda ortaya ölçeklenir; `saydam` zemin alttaki videoyu karartıp üstüne biner.
const TamSahne: React.FC<{ s: any }> = ({ s }) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const D = Math.round((s.end - s.start) * fps);
  const olcek = width > height ? (height * 0.92) / STAGE_H : 1;
  const ust = width > height ? (height - STAGE_H * olcek) / 2 : 190;
  const zemin = s.bg === "saydam" ? rgbaOf(T.bg, 0.62) : s.bg === "light" ? T.light : T.bg;
  return (
    <AbsoluteFill style={{ background: zemin, opacity: Math.min(ez(frame, 0, 6), 1 - ez(frame, D - 6, D)) }}>
      <div style={{ position: "absolute", left: (width - 1080 * olcek) / 2, top: ust, width: 1080, height: STAGE_H, transformOrigin: "0 0", transform: `scale(${olcek})` }}>
        <StageScene s={s} />
      </div>
    </AbsoluteFill>
  );
};

export const Kurgu: React.FC<KurguProps> = (p) => {
  const tema = (p.tema as TemaToken | undefined) ?? null;
  temaUygula(tema); // SplitReel sahneleri (T, F) stilin paletini ve fontunu alır; giriş katmanı
  return <TemaSaglayici tema={tema}><KurguIc {...p} /></TemaSaglayici>;
};

// Düz metin klibi (tip yok): font ve renk klipte verilmediyse stilin başlık fontu ve yazısı.
const DuzMetin: React.FC<{ k: Klip }> = ({ k }) => {
  const t = useTema();
  const m = k.metin_stil ?? {};
  return <div style={{ fontFamily: m.font ? yigin(m.font) : yigin(t.font.baslik), fontWeight: t.font.agirlik_baslik, fontSize: m.boyut ?? 96, color: m.renk ?? t.altyazi.renk,
    WebkitTextStroke: `${(m.boyut ?? 96) * 0.05}px ${t.altyazi.kontur_renk}`, paintOrder: "stroke fill" as any, textShadow: golge(t).yazi, lineHeight: 1.1, textAlign: "center", padding: 60, whiteSpace: "pre-wrap" }}>{k.metin}</div>;
};

const KurguIc: React.FC<KurguProps> = (p) => {
  const t = useTema();
  const { fps, width, height } = useVideoConfig();
  const yatay = width > height;
  const [handle] = useState(() => delayRender("reel fontları"));
  useEffect(() => {
    Promise.all(FONTS.map(([ad, yol]) => new FontFace(ad, `url(${staticFile(yol)})`, { weight: "100 900" }).load().then((f) => document.fonts.add(f))))
      .then(() => continueRender(handle)).catch(() => continueRender(handle));
  }, [handle]);

  const izler = useMemo(() => Object.fromEntries(p.izler.map((i) => [i.id, i])), [p.izler]);
  const sahneler = useMemo(
    () => p.klipler.filter((c) => c.tur === "sahne").sort((a, b) => a.bas - b.bas).map(sahneAlani),
    [p.klipler],
  );
  const words = useMemo(() => p.words ?? izdusum(p), [p.words, p.klipler, p.kelimeler, p.altyazi]);
  // İz listesi Premiere gibi üstten alta; çizim alttan üste.
  const katmanlar = useMemo(() => [...p.izler].reverse().filter((i) => i.tur === "video" && !i.gizli), [p.izler]);
  const sirali = useMemo(() => {
    const m = new Map<string, Klip[]>();
    for (const c of p.klipler) m.set(c.iz, [...(m.get(c.iz) ?? []), c]);
    for (const l of m.values()) l.sort((a, b) => a.bas - b.bas);
    return m;
  }, [p.klipler]);

  // Önizleme ve render aynı açılımı kullanır; değişim sayacı izdeki sırayla yürür.
  const hazirIzler = useMemo(() => genislet(p.klipler, { w: width, h: height, fps }), [p.klipler, width, height, fps]);
  const seq = (k: Klip, ek = 0, on = 0) => ({ from: Math.round((k.bas - on) * fps), durationInFrames: Math.max(1, Math.round((k.sure + on) * fps) + Math.round(ek * fps)), premountFor: Math.round(fps) });
  const koruma = !!p.onizleme;

  const klipCiz = (k: Klip, i: number, l: Klip[]) => {
    const iz = izler[k.iz];
    // Önizlemede silinmiş dosya oynatıcıyı düşürmesin; render'ı kurgu.denetle zaten durdurur.
    if (p.medya && k.kaynak && !p.medya[k.kaynak] && !p.kaynaklar[k.kaynak]?.yol.startsWith("public:")) return null;
    const kuyruk = kuyrukPayi(p, k, l[i + 1]);
    const on = onPayi(k);
    const sonra = l[i + 1];
    const cikis = kuyruk > 0 && sonra && ortaMi(sonra.gecis_giris) ? sonra.gecis_giris : null;
    const hz = hazirIzler.get(k.id);
    if (k.tur === "sahne") {
      const s = sahneAlani(k);
      // WHY: bkz. wiki/decisions/0039-fizik-ritim-galeri.md. Fizik sahnesinin kaynağı bake JSON'udur (vedit fizik.bagla).
      if (s.kind === "fizik" || s.kind === "karakter") {
        if (!k.kaynak) return null;
        const url = kaynakAdresi(p, k.kaynak);
        return <Sequence key={k.id} {...seq(k)} name={k.id}><SahneKoruma etkin={koruma} etiket={s.kind}><Donusum k={k} hz={hz}>{s.kind === "fizik" ? <FizikSahne url={url} s={s} /> : <KarakterSahne url={url} s={s} />}</Donusum></SahneKoruma></Sequence>;
      }
      if (s.layout === "full" && (s.kind === "hook" || s.kind === "cta")) {
        return <Sequence key={k.id} {...seq(k)} name={k.id}><SahneKoruma etkin={koruma} etiket={String(s.kind)}>{yatay ? <AbsoluteFill style={{ transform: `translateY(${YATAY_BASLIK_KAYMA}px)` }}><FullTitle s={s} /></AbsoluteFill> : <FullTitle s={s} />}</SahneKoruma></Sequence>;
      }
      if (s.layout === "full" && s.kind) {
        return <Sequence key={k.id} {...seq(k)} name={k.id}><SahneKoruma etkin={koruma} etiket={String(s.kind)}><TamSahne s={s} /></SahneKoruma></Sequence>;
      }
      return null; // bölünmüş sahneler en altta çizilir
    }
    if (k.tur === "video" && k.konusmaci) {
      const f = seq(k, kuyruk, on);
      return <Sequence key={k.id} {...f} name={k.id}><Donusum k={k} hz={hz} on={on} cikis={cikis}><Konusmaci p={p} k={k} izDb={iz.gain_db} sessiz={iz.sessiz || !!k.ses_kapali} sahneler={sahneler} from={f.from} kuyruk={kuyruk} on={on} /></Donusum></Sequence>;
    }
    if (k.tur === "motion" && k.bilesen) {
      const f = seq(k);
      return <Sequence key={k.id} {...f} name={k.id}><Donusum k={k} hz={hz}><MotionKatman b={k.bilesen} sureKare={f.durationInFrames} basKare={f.from} /></Donusum></Sequence>;
    }
    if (k.tur === "video" || k.tur === "motion") {
      return <Sequence key={k.id} {...seq(k, kuyruk, on)} name={k.id}><Donusum k={k} hz={hz} on={on} cikis={cikis} style={karisimStil(p, k)}><Video p={p} k={k} izDb={iz.gain_db} sessiz={iz.sessiz || k.tur === "motion" || !!k.ses_kapali} kuyruk={kuyruk} on={on} /></Donusum></Sequence>;
    }
    if (k.tur === "gorsel") {
      const vurgu = k.metin_stil?.tip === "vurgu";
      return <Sequence key={k.id} {...seq(k, kuyruk, on)} name={k.id}><Donusum k={k} hz={hz} on={on} cikis={cikis}><Img src={kaynakAdresi(p, k.kaynak!)} style={{ width: "100%", height: "100%", objectFit: "contain" }} />{vurgu && <Vurgu k={k} m={k.metin_stil!} kaynak={p.kaynaklar[k.kaynak!]} />}</Donusum></Sequence>;
    }
    if (k.tur === "metin") {
      const m = k.metin_stil ?? {};
      if (m.tip) {
        return <Sequence key={k.id} {...seq(k, kuyruk)} name={k.id}><SahneKoruma etkin={koruma} etiket={`metin ${m.tip}`}><Donusum k={k} hz={hz}><MetinGrafik k={k} m={m} /></Donusum></SahneKoruma></Sequence>;
      }
      return (
        <Sequence key={k.id} {...seq(k, kuyruk)} name={k.id}>
          <Donusum k={k} hz={hz} style={{ justifyContent: "center", alignItems: "center" }}>
            <DuzMetin k={k} />
          </Donusum>
        </Sequence>
      );
    }
    return null;
  };

  // ADR 0045: native grafiklerin kaçınacağı bölgeler (altyazı bandı, klip aralığındaki yüzler). Yerleşim klip başında bir kez okunur.
  const altyaziStil = p.altyazi.stil;
  const bolgeKaynagi = useMemo(() => (kare: number, sonKare?: number) => {
    const t0 = kare / fps, t1 = (sonKare ?? kare) / fps;
    const yuzler = (p.bolgeler?.yuzler ?? []).filter((a) => a.son > t0 && a.bas <= t1)
      .flatMap((a) => a.kutular.map((b) => yuzPayi({ x: b.x * width, y: b.y * height, w: b.w * width, h: b.h * height })));
    const y = altyaziStil?.konum != null ? altyaziStil.konum * height : yatay ? YATAY_ALTYAZI_Y : CAP_Y;
    return { yuzler, altyazi: p.altyazi.acik ? altyaziBandi(width, y, altyaziStil?.boyut ?? 84) : null };
  }, [p.bolgeler, p.altyazi.acik, altyaziStil, fps, width, height, yatay]);

  const temaDosya = (p.tema as { dosyalar?: Record<string, string>; altyazi_stilli?: boolean } | undefined);
  const stil = p.altyazi.stil ?? (temaDosya?.altyazi_stilli ? temaAltyazisi(t) : null);
  const fontlar = Object.entries(temaDosya?.dosyalar ?? {});
  const bolunmus = p.klipler.filter((c) => c.tur === "sahne" && c.sahne?.layout === "split" && !izler[c.iz]?.gizli).sort((a, b) => a.bas - b.bas);

  return (
    <AbsoluteFill style={{ background: T.bg }}>
      {bolunmus.map((k) => {
        // SplitReel: tam ekrana dönüşte 10 kare daha kalır, panel kapanırken arkası boş görünmez.
        const sonra = sahneler.find((s) => s.start >= k.bas + k.sure - 0.001);
        const f = seq(k);
        return <Sequence key={`st${k.id}`} {...f} durationInFrames={f.durationInFrames + (sonra?.layout === "full" ? 10 : 0)}><SahneKoruma etkin={koruma} etiket={String(k.sahne?.kind ?? "sahne")}>{yatay
          ? <div style={{ position: "absolute", left: 0, top: 0, width: 1080, height: STAGE_H, overflow: "hidden", transformOrigin: "0 0", transform: `scale(${yatayDuzen(width, height).olcek})` }}><StageScene s={sahneAlani(k)} /></div>
          : <StageScene s={sahneAlani(k)} />}</SahneKoruma></Sequence>;
      })}
      <BolgeSaglayici value={bolgeKaynagi}>{katmanlar.map((iz) => (sirali.get(iz.id) ?? []).map(klipCiz))}</BolgeSaglayici>
      {p.onizleme && p.izler.filter((i) => i.tur === "ses" && !i.sessiz).map((iz) => (sirali.get(iz.id) ?? []).filter((k) => k.tur === "ses" && k.kaynak && p.medya?.[k.kaynak]).map((k) => (
        <Sequence key={k.id} {...seq(k)} name={k.id}>
          <Audio src={kaynakAdresi(p, k.kaynak!)} volume={sesEgrisi(k, iz.gain_db, fps)} trimBefore={Math.round(k.giris * fps) || undefined} playbackRate={k.hiz} useWebAudioApi />
        </Sequence>
      )))}
      {p.altyazi.stil?.dosya && <FontYukle key={p.altyazi.stil.dosya} ad={p.altyazi.stil.font} dosya={p.altyazi.stil.dosya} p={p} />}
      {fontlar.map(([ad, dosya]) => <FontYukle key={`t${dosya}`} ad={ad} dosya={dosya} p={p} />)}
      {p.altyazi.acik && words.length > 0 && (stil
        ? <StilliAltyazi stil={stil} words={words} sahneler={sahneler} />
        : yatay
          ? <YatayAltyazi sahneler={sahneler}><Captions p={{ speaker: "", words, scenes: [], punches: [], emphasis: [], speakerZoom: 1 }} /></YatayAltyazi>
          : <Captions p={{ speaker: "", words, scenes: sahneler, punches: [], emphasis: [], speakerZoom: 1 }} />)}
      {p.onizleme && p.metreBagla && <MetreKoprusu bagla={p.metreBagla} />}
    </AbsoluteFill>
  );
};
