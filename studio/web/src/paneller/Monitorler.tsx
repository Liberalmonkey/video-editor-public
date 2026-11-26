import type { PlayerRef } from "@remotion/player";
import { yokla } from "../yokla";
import { CornerDownLeft, FastForward, Pause, Play, Replace, Rewind, SkipBack, SkipForward, StepBack, StepForward, Volume2 } from "lucide-react";
import React, { Suspense, useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { KurguProps } from "../../../remotion/tipler";
import { useDepo } from "../depo";
import { Bos, Dugme, IkonDugme } from "../ortak";
import { useKurgu, zamanKodu } from "../zaman/depo";
import { bitisi, degistir, git, kareGit, kesimeGit, oyuncuBagla } from "../zaman/oynatici";
import { motorSec, onizlemeHtml, onizlemeVerisi, oynaticiYukle, type MotorSecimi, type OnizlemeVerisi } from "../zaman/hfOnizleme";
import { bitisHesapla } from "../zaman";
import * as K from "../zaman/komutlar";
import { dinlemeAl, dinlemeYaz, metreBagla } from "../zaman/metre";

// WHY: bkz. wiki/decisions/0057-her-makinede-hiz.md. Remotion oynatıcısı ve kurgusu (three.js dahil ~1,1 MB) yalnız HyperFrames
// yapamadığında gerekir; statik içe aktarma her açılışta indiriyordu.
const RemotionMonitor = React.lazy(() => import("./RemotionMonitor"));

const ZamanKodu: React.FC = () => {
  const t = useKurgu((d) => d.zaman);
  const fps = useKurgu((d) => d.kurgu?.sekans.fps ?? 30);
  return <span className="zaman-kodu" data-zaman={t}>{zamanKodu(t, fps)}</span>;
};
const ToplamSure: React.FC = () => {
  const b = useKurgu((d) => (d.kurgu ? bitisHesapla(d.kurgu.klipler) : 0));
  const fps = useKurgu((d) => d.kurgu?.sekans.fps ?? 30);
  return <span className="ipucu zaman-toplam">{zamanKodu(b, fps)}</span>;
};
const Aralik: React.FC<{ a: number | null; b: number | null }> = ({ a, b }) => {
  const fps = useKurgu((d) => d.kurgu?.sekans.fps ?? 30);
  if (a === null && b === null) return null;
  return <span className="rozet vurgu" title="Giriş ve çıkış">{a !== null ? zamanKodu(a, fps) : "başlangıç"} → {b !== null ? zamanKodu(b, fps) : "son"}</span>;
};

// Dinleme sesi yalnız bu bilgisayarda duyulanı değiştirir; render'a ve metreye girmez.
const DinlemeSesi: React.FC = () => {
  const [v, setV] = useState(dinlemeAl);
  return (
    <span className="dinleme" title={`Dinleme sesi %${Math.round(v * 100)}. Render'a girmez.`}>
      <Volume2 size={14} aria-hidden />
      <input type="range" aria-label="Dinleme sesi" min={0} max={1} step={0.01} value={v} onChange={(e) => { const n = Number(e.target.value); setV(n); dinlemeYaz(n); }} />
    </span>
  );
};

const SekansSecimi: React.FC = () => {
  const oran = useKurgu((d) => (d.kurgu ? K.sekansOrani(d.kurgu) : "9:16"));
  const duzenle = useKurgu((d) => d.duzenle);
  return (
    <select aria-label="Sekans oranı" title="Sekans oranı. Sahne şablonları ve altyazı buna uyar." value={oran} onChange={(e) => duzenle("Sekans oranı", (f) => K.sekansAyarla(f, e.target.value as K.Oran))} style={{ minHeight: 0, height: 24, width: 74 }}>
      <option value="9:16">9:16</option>
      <option value="16:9">16:9</option>
    </select>
  );
};

export const KaynakMonitor: React.FC = () => {
  const g = useDepo((d) => d.goruntu);
  const giris = useKurgu((d) => d.kaynakGiris);
  const fps = useKurgu((d) => d.kurgu?.sekans.fps ?? 30);
  const cikis = useKurgu((d) => d.kaynakCikis);
  const ayarla = useKurgu((d) => d.ayarla);
  const [metin, setMetin] = useState("");
  const video = useRef<HTMLVideoElement>(null);
  const [t, setT] = useState(0);

  useEffect(() => {
    setMetin("");
    setT(0);
    ayarla({ kaynakGiris: null, kaynakCikis: null, odak: g?.kaynak ? "kaynak" : "program" });
    if (g?.tur === "metin") fetch(g.url).then((r) => r.text()).then(setMetin).catch(() => setMetin("Dosya okunamadı."));
  }, [g]);

  // `,` `.` kısayolu ve düğmeler aynı yerden geçer.
  const ekle = (insert: boolean) => {
    const o = useDepo.getState().goruntu?.kaynak;
    const d = useKurgu.getState();
    if (!o) return;
    if (!d.kurgu) { useDepo.getState().bildir("Önce kurgu oluştur", true); return; }
    const m = document.querySelector<HTMLMediaElement>("[data-kaynak-video]");
    const son = m?.duration && Number.isFinite(m.duration) ? m.duration : null;
    const a = d.kaynakGiris, b = d.kaynakCikis;
    const aralik = a !== null || b !== null ? ([a ?? 0, b ?? son ?? 0] as [number, number]) : null;
    if (aralik && aralik[1] <= aralik[0]) { useDepo.getState().bildir("Çıkış işareti girişten sonra olmalı", true); return; }
    d.kaynaktanEkle(o, d.zaman, null, insert, aralik);
  };
  useEffect(() => {
    const f = (e: Event) => ekle((e as CustomEvent).detail);
    window.addEventListener("studio-kaynak-ekle", f);
    return () => window.removeEventListener("studio-kaynak-ekle", f);
  }, []);

  return (
    <div className="panel" onPointerDownCapture={() => g?.kaynak && ayarla({ odak: "kaynak" })}>
      <div className="monitor">
        {!g && <Bos baslik="Kaynak boş" metin="Medya, Çıktılar ya da Kütüphane'den bir öğe seç." />}
        {g?.tur === "video" && <video key={g.url} ref={video} data-kaynak-video src={g.url} controls onTimeUpdate={(e) => setT(e.currentTarget.currentTime)} />}
        {g?.tur === "ses" && <audio key={g.url} data-kaynak-video src={g.url} controls onTimeUpdate={(e) => setT(e.currentTarget.currentTime)} />}
        {g?.tur === "gorsel" && <img src={g.url} alt={g.ad} />}
        {g?.tur === "metin" && <pre>{metin}</pre>}
        {/* WHY: pano betik çalıştırır; allow-same-origin yok, API ve çerez erişilemez. */}
        {g?.tur === "pano" && <iframe key={g.url} src={g.url} title={g.ad} sandbox="allow-scripts" />}
        {g?.tur === "diger" && <Bos baslik="Önizleme yok" metin={g.ad} />}
      </div>
      {g?.kaynak && (
        <div className="tasima">
          <span className="zaman-kodu">{zamanKodu(t, fps)}</span>
          <span className="bosluk" />
          <Aralik a={giris} b={cikis} />
          {(g.tur === "video" || g.tur === "ses") && <>
            <Dugme title="Giriş işareti (I)" onClick={() => { const m = document.querySelector<HTMLMediaElement>("[data-kaynak-video]"); if (m) ayarla({ kaynakGiris: m.currentTime }); }}>I</Dugme>
            <Dugme title="Çıkış işareti (O)" onClick={() => { const m = document.querySelector<HTMLMediaElement>("[data-kaynak-video]"); if (m) ayarla({ kaynakCikis: m.currentTime }); }}>O</Dugme>
          </>}
          <IkonDugme ad="Araya ekle (,)" onClick={() => ekle(true)}><CornerDownLeft size={15} /></IkonDugme>
          <IkonDugme ad="Üzerine yaz (.)" onClick={() => ekle(false)}><Replace size={15} /></IkonDugme>
        </div>
      )}
    </div>
  );
};

// HyperFrames oynatıcısı (ADR 0051). Kurgu değişince 150 ms sonra yeniden derlenir; yeniden yüklemede oynatma kafası korunur.
// Geri oynatma (J) yok: HyperFrames hızı 0,1-5; negatif hızda duraklar.
const HfMonitor: React.FC<{ girdi: KurguProps & { medya?: Record<string, string> }; veri: OnizlemeVerisi; studyo: string; ad: string; hiz: number; stil: React.CSSProperties }> = ({ girdi, veri, studyo, ad, hiz, stil }) => {
  const kap = useRef<HTMLDivElement>(null);
  const el = useRef<any>(null);
  const [hata, setHata] = useState<string | null>(null);
  const fps = girdi.sekans.fps;
  // Oynatıcı bir kez kurulur; srcdoc ve hız öznitelikle güncellenir.
  useEffect(() => {
    let iptal = false;
    oynaticiYukle().then(() => {
      if (iptal || !kap.current) return;
      const p = document.createElement("hyperframes-player") as any;
      p.setAttribute("runtime-src", "/hf/hyperframe.runtime.iife.js");
      p.style.width = "100%"; p.style.height = "100%"; p.style.display = "block";
      kap.current.appendChild(p);
      el.current = p;
      const zaman = (t: number) => useKurgu.setState({ zaman: Math.round(t * fps) / fps });
      p.addEventListener("timeupdate", (e: CustomEvent) => zaman(e.detail.currentTime));
      p.addEventListener("play", () => useKurgu.setState({ oynuyor: true }));
      p.addEventListener("pause", () => useKurgu.setState({ oynuyor: false }));
      p.addEventListener("ended", () => useKurgu.setState({ oynuyor: false }));
      p.addEventListener("ready", () => { p.currentTime = useKurgu.getState().zaman; setHata(null); });
      p.addEventListener("playbackerror", (e: CustomEvent) => setHata(String(e.detail?.message ?? e.detail ?? "oynatma hatası")));
      p.addEventListener("runtimeprotocolerror", (e: CustomEvent) => setHata(String(e.detail?.message ?? "çalışma zamanı hatası")));
      oyuncuBagla({ seekTo: (k) => { p.currentTime = k / fps; }, play: () => p.play(), pause: () => p.pause() });
      setDerle((n) => n + 1);
    }).catch((e) => setHata(String(e.message ?? e)));
    return () => { iptal = true; oyuncuBagla(null); el.current?.remove(); el.current = null; };
  }, [fps]);
  const [derleSayac, setDerle] = useState(0);
  useEffect(() => {
    const t = setTimeout(() => {
      if (!el.current) return;
      try { el.current.setAttribute("srcdoc", onizlemeHtml(girdi, veri, studyo, ad)); setHata(null); } catch (e: any) { setHata(`Derleyici: ${e.message ?? e}`); }
    }, 150);
    return () => clearTimeout(t);
  }, [girdi, veri, studyo, ad, derleSayac]);
  useEffect(() => { if (el.current) { if (hiz > 0) el.current.setAttribute("playback-rate", String(Math.min(5, hiz))); else el.current.pause(); } }, [hiz]);
  return (
    <>
      <div ref={kap} style={stil} />
      {hata && <div className="ipucu" style={{ position: "absolute", bottom: 8, left: 8, right: 8, color: "var(--hata)" }}>HyperFrames: {hata}</div>}
    </>
  );
};

const MotorRozeti: React.FC<{ s: MotorSecimi }> = ({ s }) => (
  <span className={`rozet ${s.motor === "hf" ? "iyi" : "uyari"}`} title={`Önizleme ve render motoru: ${s.neden}`}>{s.motor === "hf" ? "HF" : "Remotion"}</span>
);

export const ProgramMonitor: React.FC = () => {
  const aktif = useDepo((d) => d.aktif);
  const kurguDurum = useDepo((d) => d.kurguDurum);
  const kurguOlustur = useDepo((d) => d.kurguOlustur);
  const kurguAl = useDepo((d) => d.kurguAl);
  const kurgu = useKurgu((d) => d.kurgu);
  const medya = useKurgu((d) => d.medya);
  const tema = useKurgu((d) => d.tema);
  const bolgeler = useKurgu((d) => d.bolgeler);
  const hiz = useKurgu((d) => d.hiz);
  const oynuyor = useKurgu((d) => d.oynuyor);
  const giris = useKurgu((d) => d.giris);
  const cikis = useKurgu((d) => d.cikis);
  const ayarla = useKurgu((d) => d.ayarla);
  const player = useRef<PlayerRef | null>(null);
  const [oyuncu, setOyuncu] = useState<PlayerRef | null>(null);
  const oyuncuRef = useCallback((r: PlayerRef | null) => { player.current = r; setOyuncu(r); }, []);
  const solo = useKurgu((d) => d.solo);
  // Solo yalnız önizlemeyi etkiler, kurguya yazılmaz.
  const girdi = useMemo(() => kurgu && ({ ...kurgu, medya, tema, bolgeler: bolgeler ?? undefined, onizleme: true, metreBagla, izler: solo.length ? kurgu.izler.map((i) => ({ ...i, sessiz: i.sessiz || !solo.includes(i.id) })) : kurgu.izler }), [kurgu, medya, tema, bolgeler, solo]);
  const sure = kurgu ? bitisHesapla(kurgu.klipler) : 0;
  // undefined: yükleniyor (motor henüz seçilmez; eskiden bu arada Remotion kurulup sonra HF'ye geçiliyordu), null: veri yok.
  const [veri, setVeri] = useState<OnizlemeVerisi | null | undefined>(undefined);
  useEffect(() => {
    setVeri(undefined);
    onizlemeVerisi(true).then(setVeri).catch(() => setVeri(null));
  }, [aktif?.studyo, aktif?.ad]);
  const secim = useMemo(() => (kurgu && veri !== undefined ? motorSec(kurgu, veri) : null), [kurgu, veri]);
  const hfMi = secim?.motor === "hf" && !!veri;

  // Test köprüsü: ölçüm betikleri kullanır.
  useEffect(() => { (window as any).__studio = { player: player.current, depo: useKurgu }; });

  useEffect(() => {
    const p = oyuncu;
    oyuncuBagla(p);
    if (!p) return;
    const fpsAl = () => useKurgu.getState().kurgu?.sekans.fps ?? 30;
    const kare = (e: { detail: { frame: number } }) => useKurgu.setState({ zaman: e.detail.frame / fpsAl() });
    const oyna = () => useKurgu.setState({ oynuyor: true });
    const dur = () => useKurgu.setState({ oynuyor: false });
    p.addEventListener("frameupdate", kare);
    p.addEventListener("seeked", kare);
    p.addEventListener("play", oyna);
    p.addEventListener("pause", dur);
    p.addEventListener("ended", dur);
    return () => {
      p.removeEventListener("frameupdate", kare);
      p.removeEventListener("seeked", kare);
      p.removeEventListener("play", oyna);
      p.removeEventListener("pause", dur);
      p.removeEventListener("ended", dur);
      oyuncuBagla(null);
    };
  }, [oyuncu]);

  // Proxy arka planda üretilir; hazır olunca adresler değişir.
  // Kütüphane, stil ve motion (saydam) kaynakları proxy'ye hiç girmez (app.py medya_eslemesi); onları beklemek sonsuz yoklama olur.
  const proxyBekliyor = !!kurgu && Object.entries(medya).some(([id, url]) => {
    const yol = kurgu.kaynaklar[id]?.yol ?? "";
    return /\.(mp4|mov|mkv|webm|avi|m4v)$/i.test(yol) && !/^(library|stil):|^public:motion\//.test(yol) && !url.includes("/proxy/");
  });
  useEffect(() => {
    if (!proxyBekliyor) return;
    return yokla(kurguAl, 4000);
  }, [proxyBekliyor, kurguAl]);

  if (!aktif) return <div className="panel"><Bos baslik="Proje seçilmedi" metin="Soldaki Proje panelinden bir proje aç ya da yeni proje oluştur." /></div>;
  if (kurguDurum === "bos") {
    const eski = useDepo.getState().projeler.find((p) => p.studyo === aktif.studyo && p.ad === aktif.ad)?.props;
    return <div className="panel"><Bos baslik="Bu projede kurgu yok" metin={eski ? "Mevcut sahne planı ve ses olayları kurguya aktarılır. Eski dosyalar silinmez." : "Boş bir kurgu oluştur, sonra Medya'dan timeline'a sürükle."}><Dugme tur="birincil" onClick={kurguOlustur}>{eski ? "Kurguya aktar" : "Boş kurgu oluştur"}</Dugme></Bos></div>;
  }
  if (!girdi) return <div className="panel"><div className="monitor"><div className="ipucu">Kurgu yükleniyor</div></div></div>;

  const fps = girdi.sekans.fps;
  const dikey = girdi.sekans.h > girdi.sekans.w;
  return (
    <div className="panel" onPointerDownCapture={() => ayarla({ odak: "program" })}>
      {proxyBekliyor && <div className="arac" style={{ minHeight: 26, padding: "2px 8px" }}><span className="rozet uyari">Proxy hazırlanıyor</span><span className="ipucu">Oynatma akıcı olmayabilir</span></div>}
      <div className="monitor">
        {hfMi ? <HfMonitor key={`hf:${aktif.studyo}/${aktif.ad}`} girdi={girdi} veri={veri!} studyo={aktif.studyo} ad={aktif.ad} hiz={hiz}
          stil={dikey ? { height: "100%", aspectRatio: `${girdi.sekans.w} / ${girdi.sekans.h}` } : { width: "100%", aspectRatio: `${girdi.sekans.w} / ${girdi.sekans.h}`, maxHeight: "100%" }} />
          : !secim ? <div className="ipucu">Önizleme hazırlanıyor</div>
          : <Suspense fallback={<div className="ipucu">Önizleme hazırlanıyor</div>}><RemotionMonitor
          key={`${aktif.studyo}/${aktif.ad}`} ref={oyuncuRef} girdi={girdi} fps={fps} hiz={hiz}
          sureKare={Math.max(fps, Math.ceil(sure * fps))}
          ilkKare={Math.min(Math.max(fps, Math.ceil(sure * fps)) - 1, Math.round(useKurgu.getState().zaman * fps))}
          stil={dikey ? { height: "100%", aspectRatio: `${girdi.sekans.w} / ${girdi.sekans.h}` } : { width: "100%", aspectRatio: `${girdi.sekans.w} / ${girdi.sekans.h}`, maxHeight: "100%" }}
        /></Suspense>}
      </div>
      <div className="tasima">
        <ZamanKodu />
        <SekansSecimi />
        {secim && <MotorRozeti s={secim} />}
        <span className="bosluk" />
        <IkonDugme ad="Başa git (Home)" onClick={() => git(0)}><SkipBack size={15} /></IkonDugme>
        <IkonDugme ad="Önceki kesim" onClick={() => kesimeGit(-1)}><StepBack size={15} /></IkonDugme>
        <IkonDugme ad="Bir kare geri (←)" onClick={() => kareGit(-1)}><Rewind size={15} /></IkonDugme>
        <IkonDugme ad={oynuyor ? "Durdur (Boşluk)" : "Oynat (Boşluk)"} className="oynat" onClick={degistir}>{oynuyor ? <Pause size={17} /> : <Play size={17} />}</IkonDugme>
        <IkonDugme ad="Bir kare ileri (→)" onClick={() => kareGit(1)}><FastForward size={15} /></IkonDugme>
        <IkonDugme ad="Sonraki kesim" onClick={() => kesimeGit(1)}><StepForward size={15} /></IkonDugme>
        <IkonDugme ad="Sona git (End)" onClick={() => git(bitisi())}><SkipForward size={15} /></IkonDugme>
        {Math.abs(hiz) !== 1 && <span className="rozet vurgu">{hiz}x</span>}
        <span className="bosluk" />
        <Aralik a={giris} b={cikis} />
        <ToplamSure />
        <DinlemeSesi />
      </div>
    </div>
  );
};

