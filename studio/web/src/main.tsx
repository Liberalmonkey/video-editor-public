import { DockviewReact, type DockviewApi, type DockviewReadyEvent, type IDockviewPanelProps } from "dockview-react";
import "dockview-react/dist/styles/dockview.css";
import { Keyboard, RotateCcw } from "lucide-react";
import React, { useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import { istek } from "./api";
import { isAkisiBaglan, useDepo } from "./depo";
import { Bildirimler, Bos, Diyalog, Dugme, IkonDugme, OnayKatmani } from "./ortak";
import { AjanPaneli, AjanRozeti } from "./paneller/AjanPaneli";
import { AltyaziPaneli } from "./paneller/AltyaziPaneli";
import { DosyaPaneli } from "./paneller/DosyaPaneli";
import { MikserPaneli } from "./paneller/MikserPaneli";
import { EfektPaneli } from "./paneller/EfektPaneli";
import { IslerPaneli } from "./paneller/IslerPaneli";
import { KaynakMonitor, ProgramMonitor } from "./paneller/Monitorler";
import { ProjePaneli } from "./paneller/ProjePaneli";
import { useKurgu } from "./zaman/depo";
import { kisayollariBagla } from "./zaman/kisayol";
import { KisayolDiyalog } from "./zaman/KisayolDiyalog";
import { Timeline } from "./zaman/Timeline";
import "./stil.css";

// Açılışta görünmeyen paneller ayrı parçada; ilk açılışta yüklenir (ADR 0050).
const DenetimPaneli = React.lazy(() => import("./paneller/DenetimPaneli").then((m) => ({ default: m.DenetimPaneli })));
const KapakPaneli = React.lazy(() => import("./paneller/kapak/KapakPaneli").then((m) => ({ default: m.KapakPaneli })));
const KutuphanePaneli = React.lazy(() => import("./paneller/KutuphanePaneli").then((m) => ({ default: m.KutuphanePaneli })));
const StilPaneli = React.lazy(() => import("./paneller/StilPaneli").then((m) => ({ default: m.StilPaneli })));
const KurallarPaneli = React.lazy(() => import("./paneller/KurallarPaneli").then((m) => ({ default: m.KurallarPaneli })));
const TeslimPaneli = React.lazy(() => import("./paneller/TeslimPaneli").then((m) => ({ default: m.TeslimPaneli })));

// HyperFrames sürümü ve son güncelleme denemesi (ADR 0051). Güncelleme arka planda olur; rozet yalnız bilgi verir.
const HfRozeti: React.FC = () => {
  const [d, setD] = useState<any>(null);
  useEffect(() => {
    const al = () => istek("/api/hf/durum").then(setD).catch(() => {});
    al();
    const t = setInterval(al, 600_000);
    return () => clearInterval(t);
  }, []);
  if (!d) return null;
  const son = d.son_deneme;
  const kaldi = son && son.gecti === false;
  const baslik = `HyperFrames ${d.mevcut}` + (d.en_yeni && d.yeni_var ? ` · yeni sürüm ${d.en_yeni}` : "")
    + (son?.surum ? ` · son deneme ${son.surum}: ${son.gecti ? "geçti" : "kaldı"}${son.rapor ? ` (${son.rapor})` : ""}` : "");
  return <span className={`rozet${kaldi ? " uyari" : ""}`} title={baslik}>HF {d.mevcut}{kaldi ? " !" : ""}</span>;
};

const CakismaDiyalog: React.FC = () => {
  const c = useKurgu((d) => d.cakisma);
  const { diskiAl, benimkiniYaz } = useKurgu.getState();
  return (
    <Diyalog acik={c} kapat={() => {}}>
      <h2>Kurgu başka yerden değişti</h2>
      <p>kurgu.json terminalden ya da başka bir pencereden yazıldı, burada da kaydedilmemiş düzenlemeler var. Hangisi kalsın?</p>
      <div className="eylemler">
        <Dugme onClick={() => diskiAl()}>Diskteki sürümü al</Dugme>
        <Dugme tur="tehlike" onClick={() => benimkiniYaz()}>Benimkini yaz</Dugme>
      </div>
    </Diyalog>
  );
};

// Bir panelin hatası uygulamayı düşürmesin: düzenleme ve kayıt diğer panellerde sürer.
class PanelKoruma extends React.Component<{ ad: string; children: React.ReactNode }, { hata: string | null }> {
  state = { hata: null as string | null };
  static getDerivedStateFromError(e: Error) { return { hata: e.message || String(e) }; }
  render() {
    if (!this.state.hata) return this.props.children;
    return (
      <div className="panel" role="alert">
        <Bos baslik={`${this.props.ad} paneli hata verdi`} metin={`${this.state.hata} Kurgun kayıtlı, diğer paneller çalışıyor.`}>
          <Dugme onClick={() => this.setState({ hata: null })}>Yeniden dene</Dugme>
          <Dugme onClick={() => window.location.reload()}>Sayfayı yenile</Dugme>
        </Bos>
      </div>
    );
  }
}

const sar = (ad: string, C: React.ComponentType<any>, ek?: any): React.FC<IDockviewPanelProps> => () => (
  <PanelKoruma ad={ad}><React.Suspense fallback={<div className="panel" />}><C {...ek} /></React.Suspense></PanelKoruma>
);
const bilesenler: Record<string, React.FC<IDockviewPanelProps>> = {
  proje: sar("Proje", ProjePaneli),
  medya: sar("Medya", DosyaPaneli, { bolge: "inputs" }),
  cikti: sar("Çıktılar", DosyaPaneli, { bolge: "outputs" }),
  kutuphane: sar("Kütüphane", KutuphanePaneli),
  kaynak: sar("Kaynak", KaynakMonitor),
  program: sar("Program", ProgramMonitor),
  isler: sar("İşler", IslerPaneli),
  timeline: sar("Timeline", Timeline),
  efekt: sar("Klip", EfektPaneli),
  altyazi: sar("Altyazı", AltyaziPaneli),
  mikser: sar("Ses", MikserPaneli),
  denetim: sar("Denetim", DenetimPaneli),
  teslim: sar("Çıktı ayarları", TeslimPaneli),
  ajan: sar("AI", AjanPaneli),
  kapak: sar("Kapak", KapakPaneli),
  stil: sar("Video stili", StilPaneli),
  kurallar: sar("Kurallar", KurallarPaneli),
};
const BASLIK: Record<string, string> = { proje: "Proje", medya: "Medya", cikti: "Çıktılar", kutuphane: "Kütüphane", kaynak: "Kaynak", program: "Program", isler: "İşler", timeline: "Timeline", efekt: "Klip", altyazi: "Altyazı", mikser: "Ses", denetim: "Denetim", teslim: "Çıktı ayarları", ajan: "AI", kapak: "Kapak", stil: "Video stili", kurallar: "Kurallar" };

const ekleyici = (api: DockviewApi) => (id: string, position?: any) => api.addPanel({ id, component: id, title: BASLIK[id], position });
const yan = (referencePanel: string, direction: string) => ({ referencePanel, direction });
const ic = (referencePanel: string) => ({ referencePanel, direction: "within" });

// WHY: bkz. wiki/decisions/0030-sade-arayuz.md
// `paneller`: varsayılan yerleşimin panelleri. Kayıtlı yerleşimde biri eksikse varsayılana dönülür; sonradan eklenen panel gizli kalmaz.
const ALANLAR: Record<string, { ad: string; paneller: string[]; kur: (api: DockviewApi) => void }> = {
  kurgu: { ad: "Kurgu", paneller: ["proje", "timeline", "kaynak", "program", "efekt", "mikser", "altyazi", "isler", "ajan", "medya", "kutuphane"], kur: (api) => {
    const e = ekleyici(api);
    const proje = e("proje");
    const tl = e("timeline", yan("proje", "right"));
    const kaynak = e("kaynak", yan("timeline", "above"));
    e("program", yan("kaynak", "right"));
    const efekt = e("efekt", yan("program", "right"));
    for (const id of ["mikser", "altyazi", "isler", "ajan"]) e(id, ic("efekt"));
    // WHY: medya en son eklenir; önce eklenirse kök dikey bölünür ve alt şerit tüm genişliği kaplar.
    const medya = e("medya", yan("proje", "below"));
    e("kutuphane", ic("medya"));
    efekt.api.setActive(); medya.api.setActive();
    proje.api.setSize({ width: Math.round(api.width * 0.25), height: Math.round(api.height * 0.3) });
    kaynak.api.setSize({ height: Math.round(api.height * 0.66) });
    efekt.api.setSize({ width: Math.round(api.width * 0.24) });
    tl.api.setActive();
  } },
  teslim: { ad: "Teslim", paneller: ["teslim", "isler", "denetim", "program", "cikti"], kur: (api) => {
    const e = ekleyici(api);
    const t = e("teslim");
    const i = e("isler", ic("teslim"));
    const d = e("denetim", yan("teslim", "right"));
    const p = e("program", yan("denetim", "right"));
    const c = e("cikti", yan("teslim", "below"));
    i.api.setSize({ width: Math.round(api.width * 0.3), height: Math.round(api.height * 0.55) });
    d.api.setSize({ width: Math.round(api.width * 0.3) });
    p.api.setActive(); c.api.setActive(); t.api.setActive();
  } },
  kutuphane: { ad: "Kütüphane", paneller: ["kutuphane", "stil", "kurallar"], kur: (api) => {
    const e = ekleyici(api);
    const k = e("kutuphane");
    e("stil", yan("kutuphane", "right"));
    e("kurallar", ic("stil"));
    k.api.setSize({ width: Math.round(api.width * 0.5) });
    k.api.setActive();
  } },
  // WHY: Kapak, Teslim alanında Çıktılar'ın arkasında gizli sekmeydi ve bulunamıyordu; kendi alanı var (ADR 0027).
  kapak: { ad: "Kapak", paneller: ["kapak", "program", "isler"], kur: (api) => {
    const e = ekleyici(api);
    const k = e("kapak");
    e("program", yan("kapak", "right"));
    e("isler", yan("program", "below"));
    k.api.setSize({ width: Math.round(api.width * 0.62) });
    k.api.setActive();
  } },
};
// Teslim yerleşimine Çıktı ayarları paneli eklendi (ADR 0035): yalnız onun kayıtlı yerleşimi yenilenir, diğer alanlar korunur.
const alanAnahtari = (ad: string) => `studio.alan.${ad === "teslim" ? "v3" : "v2"}.${ad}`;

const App: React.FC = () => {
  const aktif = useDepo((d) => d.aktif);
  const baglanti = useDepo((d) => d.baglanti);
  const api = useRef<DockviewApi | null>(null);
  const [kisayol, setKisayol] = useState(false);
  const [alan, setAlan] = useState(() => { try { const k = localStorage.getItem("studio.alan") ?? "kurgu"; return k in ALANLAR ? k : "kurgu"; } catch { return "kurgu"; } });
  const alanRef = useRef(alan);
  const yukleniyor = useRef(false); // geçişteki ara durum kaydedilmesin

  const yukle = (ad: string, sifirla = false) => {
    const a = api.current;
    if (!a) return;
    yukleniyor.current = true;
    a.clear();
    let tamam = false;
    if (!sifirla) {
      try {
        const k = localStorage.getItem(alanAnahtari(ad));
        if (k) { a.fromJSON(JSON.parse(k)); tamam = ALANLAR[ad].paneller.every((id) => a.getPanel(id)); if (!tamam) a.clear(); }
      } catch { a.clear(); /* bozuk ya da bilinmeyen panelli yerleşim: varsayılana dön */ }
    }
    if (!tamam) ALANLAR[ad].kur(a);
    yukleniyor.current = false;
    try { localStorage.setItem(alanAnahtari(ad), JSON.stringify(a.toJSON())); } catch { /* kota */ }
  };
  const gec = (ad: string) => {
    if (ad === alanRef.current) return;
    alanRef.current = ad;
    setAlan(ad);
    try { localStorage.setItem("studio.alan", ad); } catch { /* özel pencere */ }
    yukle(ad);
  };

  useEffect(() => {
    useDepo.getState().projeleriAl().then(() => {
      let son = "";
      try { son = localStorage.getItem("studio.aktif") ?? ""; } catch { /* özel pencere */ }
      const d = useDepo.getState();
      const p = d.projeler.find((x) => `${x.studyo}/${x.ad}` === son);
      if (p) d.projeAc(p);
    });
    const a = isAkisiBaglan(), b = kisayollariBagla();
    const alanTusu = (e: Event) => gec((e as CustomEvent).detail);
    const panelOne = (e: Event) => api.current?.getPanel((e as CustomEvent).detail)?.api.setActive();
    window.addEventListener("studio-alan", alanTusu);
    window.addEventListener("studio-panel", panelOne);
    return () => { a(); b(); window.removeEventListener("studio-alan", alanTusu); window.removeEventListener("studio-panel", panelOne); };
  }, []);

  // AI panelini öne getirir; bu alanda yoksa Kurgu alanına geçer.
  const ajanAc = () => {
    if (!api.current?.getPanel("ajan")) gec("kurgu");
    api.current?.getPanel("ajan")?.api.setActive();
  };

  const hazir = (e: DockviewReadyEvent) => {
    api.current = e.api;
    yukle(alanRef.current);
    e.api.onDidLayoutChange(() => {
      if (yukleniyor.current) return;
      try { localStorage.setItem(alanAnahtari(alanRef.current), JSON.stringify(e.api.toJSON())); } catch { /* kota */ }
    });
  };

  return (
    <div className="uygulama">
      <header className="ust">
        <span className="marka"><img src="/logo.svg" alt="" width={20} height={20} />Video Stüdyo</span>
        <span className="proje-adi">{aktif ? <>{aktif.studyo} / <b>{aktif.ad}</b></> : "Proje seçilmedi"}</span>
        <span className="bosluk" />
        {!baglanti && <span className="rozet hata" role="alert">Sunucu bağlantısı yok. Düzenlemeler bağlantı dönünce kaydedilir.</span>}
        <nav className="sekmeler" aria-label="Çalışma alanı">
          {Object.entries(ALANLAR).map(([k, v], i) => <button key={k} type="button" className="sekme" aria-current={alan === k ? "page" : undefined} data-secili={alan === k} title={`${v.ad} (Alt+${i + 1})`} onClick={() => gec(k)}>{v.ad}</button>)}
        </nav>
        <span className="bosluk" />
        <HfRozeti />
        <AjanRozeti ac={ajanAc} />
        <IkonDugme ad="Klavye kısayolları" onClick={() => setKisayol(true)}><Keyboard size={15} /></IkonDugme>
        <IkonDugme ad="Bu çalışma alanını sıfırla" onClick={() => yukle(alanRef.current, true)}><RotateCcw size={14} /></IkonDugme>
      </header>
      <main className="dock">
        <DockviewReact components={bilesenler} onReady={hazir} theme={{ name: "studio", className: "dockview-theme-dark studio-dv" }} />
      </main>
      <OnayKatmani />
      <CakismaDiyalog />
      <KisayolDiyalog acik={kisayol} kapat={() => setKisayol(false)} />
      <Bildirimler />
    </div>
  );
};

createRoot(document.getElementById("kok")!).render(<App />);
