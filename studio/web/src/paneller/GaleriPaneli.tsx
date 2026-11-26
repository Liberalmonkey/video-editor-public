// WHY: bkz. wiki/decisions/0039-fizik-ritim-galeri.md. Stil ve motion galerisi: stil paketi, tema, motion, fizik ve ışık
// presetleri, konuşan karakter ve hazır efektler tek ızgarada; yan yana karşılaştırma ve tek tıkla kurguya ekleme.
import { Columns2, Eye, EyeOff, Plus, X } from "lucide-react";
import React, { useEffect, useMemo, useState } from "react";
import { istek } from "../api";
import { useDepo } from "../depo";
import { Bos, Dugme, Iskelet } from "../ortak";
import * as K from "../zaman/komutlar";
import { useKurgu } from "../zaman/depo";

export interface GaleriOge {
  tur: string; id: string; title: string; ne_zaman?: string; poster_url?: string | null; video_url?: string | null;
  palet?: string[]; font?: string | null; studyo?: string; kind?: string; sablon?: boolean; file?: string; amac?: string;
  sure?: number; tags?: string[]; eski?: boolean; gizli?: boolean;
  param?: Record<string, { tip: string; vars: any; min?: number; max?: number; secenek?: string[]; birim?: string }>;
}

const TURLER: [string, string][] = [["", "Tümü"], ["stil", "Stil paketi"], ["tema", "Tema"], ["fizik", "Fizik"], ["isik", "Işık"],
  ["karakter", "Karakter"], ["motion", "Motion"], ["hazir", "Hazır efekt"]];
const GENIS = new Set(["tema", "fizik", "isik", "karakter"]); // 16:9 önizleme
const EN_COK_KARSILASTIR = 4;

// Saf süzgeç: test edilir. ADR 0061: gizlenen öğe ve eski (Arşiv) motion yalnız "Gizlenenleri göster" açıkken.
export const galeriSuz = (ogeler: GaleriOge[], tur: string, ara: string, hepsi = false) => {
  const kelimeler = ara.toLocaleLowerCase("tr").split(/\s+/).filter(Boolean);
  return ogeler.filter((o) => (hepsi || (!o.gizli && !o.eski)) && (!tur || o.tur === tur) && kelimeler.every((k) =>
    [o.id, o.title, o.ne_zaman, o.kind, o.amac, ...(o.tags ?? [])].filter(Boolean).join(" ").toLocaleLowerCase("tr").includes(k)));
};

const Onizleme: React.FC<{ o: GaleriOge; oynat: boolean }> = ({ o, oynat }) => (
  <span className={`motion-kare ${GENIS.has(o.tur) ? "genis" : ""}`}>
    {o.poster_url ? <img src={o.poster_url} alt="" loading="lazy" />
      : <span className="galeri-yer">
        {o.palet?.length ? <span className="galeri-palet">{o.palet.slice(0, 5).map((r, i) => <i key={i} style={{ background: r }} />)}</span> : null}
        <span className="galeri-yer-ad">{o.title}</span>
      </span>}
    {oynat && o.video_url && <video src={o.video_url} autoPlay loop muted playsInline />}
    {o.sablon && <span className="rozet vurgu">şablon</span>}
  </span>
);

const Kart: React.FC<{ o: GaleriOge; secili: boolean; karsi: boolean; sec: () => void; karsiDegis: () => void }> = ({ o, secili, karsi, sec, karsiDegis }) => {
  const [oynat, setOynat] = useState(false);
  return (
    <div className={`motion-kart ${secili ? "secili" : ""}`} role="button" tabIndex={0} title={o.ne_zaman || o.title} onClick={sec}
      onKeyDown={(k) => k.key === "Enter" && sec()} onMouseEnter={() => setOynat(true)} onMouseLeave={() => setOynat(false)}>
      <Onizleme o={o} oynat={oynat} />
      <span className="motion-ad" style={{ display: "flex", gap: 4, alignItems: "center" }}>
        <span style={{ flex: 1, minWidth: 0, overflow: "hidden", textOverflow: "ellipsis" }}>{o.title}</span>
        <input type="checkbox" aria-label={`${o.title} karşılaştırmaya ekle`} checked={karsi} onClick={(k) => k.stopPropagation()} onChange={karsiDegis} />
      </span>
    </div>
  );
};

const Karsilastir: React.FC<{ ogeler: GaleriOge[]; kapat: () => void; cikar: (o: GaleriOge) => void }> = ({ ogeler, kapat, cikar }) => {
  const [tur, setTur] = useState(0); // aynı anda yeniden başlatmak için anahtar
  return (
    <div className="galeri-karsi" role="dialog" aria-label="Karşılaştır">
      <div className="arac">
        <strong style={{ flex: 1 }}>Karşılaştır ({ogeler.length})</strong>
        <Dugme onClick={() => setTur(tur + 1)}>Baştan oynat</Dugme>
        <Dugme onClick={kapat}><X size={14} /> Kapat</Dugme>
      </div>
      <div className="galeri-karsi-izgara" style={{ gridTemplateColumns: `repeat(${Math.min(2, ogeler.length)}, 1fr)` }}>
        {ogeler.map((o) => (
          <figure key={`${o.tur}/${o.id}/${tur}`}>
            <span className={`motion-kare ${GENIS.has(o.tur) ? "genis" : ""}`}>
              {o.video_url ? <video src={o.video_url} autoPlay loop muted playsInline poster={o.poster_url ?? undefined} />
                : o.poster_url ? <img src={o.poster_url} alt="" /> : <span className="galeri-yer"><span className="galeri-palet">{o.palet?.map((r, i) => <i key={i} style={{ background: r }} />)}</span></span>}
            </span>
            <figcaption><b>{o.title}</b> <span className="ipucu">{o.tur}</span> <button type="button" className="bag" onClick={() => cikar(o)}>çıkar</button><br /><span className="ipucu">{o.ne_zaman}</span></figcaption>
          </figure>
        ))}
      </div>
    </div>
  );
};

const ParamFormu: React.FC<{ o: GaleriOge; deger: Record<string, any>; degis: (d: Record<string, any>) => void }> = ({ o, deger, degis }) => (
  <div className="form" style={{ marginBottom: 8 }}>
    {Object.entries(o.param ?? {}).map(([a, t]) => (
      <label key={a}>{a}{t.birim ? ` (${t.birim})` : ""}
        {t.tip === "secim"
          ? <select value={String(deger[a] ?? t.vars)} onChange={(e) => degis({ ...deger, [a]: e.target.value })}>{t.secenek!.map((s) => <option key={s}>{s}</option>)}</select>
          : t.tip === "sayi"
            ? <input type="number" min={t.min} max={t.max} step="any" value={deger[a] ?? t.vars} onChange={(e) => degis({ ...deger, [a]: Number(e.target.value) })} />
            : <input value={String(deger[a] ?? "")} maxLength={60} onChange={(e) => degis({ ...deger, [a]: e.target.value })} />}
      </label>
    ))}
  </div>
);

export const GaleriPaneli: React.FC = () => {
  const { aktif, bildir, hata } = useDepo();
  const [ogeler, setOgeler] = useState<GaleriOge[] | null>(null);
  const [tur, setTur] = useState("");
  const [ara, setAra] = useState("");
  const [secili, setSecili] = useState<GaleriOge | null>(null);
  const [karsi, setKarsi] = useState<GaleriOge[]>([]);
  const [acik, setAcik] = useState(false);
  const [param, setParam] = useState<Record<string, any>>({});
  const [isik, setIsik] = useState("studyo");
  const [sure, setSure] = useState(4);
  const [saydam, setSaydam] = useState(true);
  const [is, setIs] = useState(false);
  const [hepsi, setHepsi] = useState(false);

  const al = () => istek("/api/galeri").then((r) => setOgeler(r.ogeler)).catch(hata);
  useEffect(() => { al(); }, []);
  const liste = useMemo(() => galeriSuz(ogeler ?? [], tur, ara, hepsi), [ogeler, tur, ara, hepsi]);
  // Kodla tanımlı öğe silinemez, gizlenir; motion dosyası Motion sekmesinden silinir (ADR 0061).
  const gizle = async (o: GaleriOge, g: boolean) => {
    try {
      await istek("/api/galeri/gizle", { method: "POST", json: { anahtar: `${o.tur}:${o.id}`, gizle: g } });
      bildir(g ? `${o.title} gizlendi. "Gizlenenleri göster" ile geri alınır.` : `${o.title} yeniden görünür`);
      setSecili(null);
      await al();
    } catch (e) { hata(e); }
  };
  const isiklar = useMemo(() => (ogeler ?? []).filter((o) => o.tur === "isik"), [ogeler]);
  const anahtar = (o: GaleriOge) => `${o.tur}/${o.id}`;
  const karsiVar = (o: GaleriOge) => karsi.some((x) => anahtar(x) === anahtar(o));
  const karsiDegis = (o: GaleriOge) => setKarsi(karsiVar(o) ? karsi.filter((x) => anahtar(x) !== anahtar(o))
    : karsi.length >= EN_COK_KARSILASTIR ? (bildir(`En çok ${EN_COK_KARSILASTIR} seçenek karşılaştırılır`, true), karsi) : [...karsi, o]);

  const sec = (o: GaleriOge) => {
    setSecili(o);
    setParam(Object.fromEntries(Object.entries(o.param ?? {}).map(([a, t]) => [a, t.vars])));
    if (o.sure) setSure(o.sure);
  };

  const kurguVar = () => {
    const d = useKurgu.getState();
    if (!d.kurgu || !aktif) { bildir("Önce kurgusu olan bir proje aç", true); return null; }
    return d;
  };

  // Fizik ve karakter: sunucu veriyi üretir (bake ya da viseme), klip kaynağıyla oynatma kafasına eklenir.
  const sahneEkle = async (sahne: Record<string, any>, ad: string) => {
    const d = kurguVar();
    if (!d) return;
    setIs(true);
    try {
      await d.kaydet(); // karakterin ağzı diskteki kurgunun konuşmasından gelir
      const t = d.zaman;
      const r = await istek(`/api/sahne-bagla/${aktif!.studyo}/${aktif!.ad}`, { method: "POST", json: { sahne, bas: t, sure } });
      useKurgu.setState({ medya: { ...useKurgu.getState().medya, [r.id]: r.url } });
      let yeni = "";
      useKurgu.getState().duzenle(`${ad} ekle`, (f) => {
        f.kaynaklar[r.id] = { yol: r.yol, sure: r.sure, ses: false } as any;
        const iz = K.bosIz(f, t, t + sure);
        yeni = K.klipEkle(f, { tur: "sahne", iz, bas: t, sure, kaynak: r.id, sahne: { layout: "full", ...sahne } })?.id ?? "";
      });
      if (yeni) useKurgu.getState().sec([yeni]);
      bildir(`${ad} eklendi`);
    } catch (e) { hata(e); } finally { setIs(false); }
  };

  const eylem = async () => {
    if (!secili) return;
    const o = secili;
    if (o.tur === "fizik") return sahneEkle({ kind: "fizik", preset: o.id, param, isik: { preset: isik }, olcum: true }, o.title);
    if (o.tur === "karakter") return sahneEkle({ kind: "karakter", karakter: o.id, ...(saydam ? { bg: "saydam", olcek: 0.55 } : {}) }, o.title);
    const d = kurguVar();
    if (!d) return;
    if (o.tur === "tema") { d.duzenle(`Tema: ${o.id}`, (f) => { f.motion_tema = o.id; }); bildir(`Proje teması ${o.id}. Şablonlar bir sonraki önizlemede yenilenir.`); return; }
    if (o.tur === "stil") {
      if (o.studyo !== aktif!.studyo) { bildir(`Bu stil ${o.studyo} stüdyosunun`, true); return; }
      try { await istek(`/api/stil/${o.studyo}/sec`, { method: "POST", json: { proje: aktif!.ad, stil: o.title } }); bildir(`Stil seçildi: ${o.title}. AI edit bu stile uyar.`); } catch (e) { hata(e); }
      return;
    }
    if (o.tur === "motion" && o.file && !o.sablon) { await d.kaynaktanEkle({ yol: `library:${o.file.replace(/^library\//, "")}`, ad: o.title, tur: "motion" }, d.zaman, null, false); return; }
    if (o.tur === "motion") { bildir("Şablonu Motion sekmesinden parametreleriyle ekle", true); return; }
    const c = d.kurgu!.klipler.find((x) => x.id === d.secim[0]);
    if (o.tur === "isik") {
      if (!c || c.sahne?.kind !== "fizik") { bildir("Önce timeline'da bir fizik sahnesi seç", true); return; }
      try {
        const r = await istek(`/api/sahne-bagla/${aktif!.studyo}/${aktif!.ad}`, { method: "POST", json: { sahne: { ...c.sahne, isik: { preset: o.id } }, bas: c.bas, sure: c.sure } });
        useKurgu.setState({ medya: { ...useKurgu.getState().medya, [r.id]: r.url } });
        d.duzenle(`Işık: ${o.title}`, (f) => { const x = f.klipler.find((y) => y.id === c.id); if (x) { x.sahne = { ...x.sahne, isik: { preset: o.id } }; f.kaynaklar[r.id] = { yol: r.yol, sure: r.sure, ses: false } as any; x.kaynak = r.id; } });
      } catch (e) { hata(e); }
      return;
    }
    if (o.tur === "hazir") {
      if (!c || !["video", "gorsel", "motion", "sahne", "metin"].includes(c.tur)) { bildir("Önce görüntü klibi seç", true); return; }
      const t = Math.max(0, Math.min(c.sure - 0.1, d.zaman - c.bas));
      d.duzenle(`Hazır efekt: ${o.id}`, (f) => { const x = f.klipler.find((y) => y.id === c.id); if (x) x.hazir = [...(x.hazir ?? []), { ad: o.id, t: Math.round(t * 100) / 100 }]; });
      bildir(`${o.title} klibin ${t.toFixed(2)}. saniyesine eklendi`);
    }
  };

  const eylemAdi: Record<string, string> = { fizik: "Oynatma kafasına ekle", karakter: "Oynatma kafasına ekle", tema: "Proje teması yap", stil: "Projeye seç",
    motion: "Oynatma kafasına ekle", isik: "Seçili fizik sahnesine uygula", hazir: "Seçili klibe ekle" };

  if (!ogeler) return <div className="icerik"><Iskelet /></div>;
  return (
    <>
      <div className="arac">
        <input type="search" aria-label="Galeride ara" placeholder="Ara: domino, gün batımı, finans" value={ara} onChange={(e) => setAra(e.target.value)} style={{ flex: 1, minWidth: 0 }} />
        <Dugme disabled={karsi.length < 2} title="İşaretlenen seçenekleri yan yana oynat" onClick={() => setAcik(true)}><Columns2 size={14} /> Karşılaştır{karsi.length ? ` (${karsi.length})` : ""}</Dugme>
        <Dugme aria-pressed={hepsi} title="Gizlenen öğeleri ve Arşiv'deki eski motion kayıtlarını da göster" onClick={() => setHepsi(!hepsi)}>{hepsi ? <EyeOff size={14} /> : <Eye size={14} />} {hepsi ? "Gizlenenleri sakla" : "Gizlenenleri göster"}</Dugme>
      </div>
      <div className="motion-cipler" role="tablist" aria-label="Galeri türü">
        {TURLER.map(([k, et]) => {
          const n = galeriSuz(ogeler, k, "", hepsi).length;
          return n || !k ? <button key={k} type="button" role="tab" className="sekme" aria-selected={tur === k} onClick={() => setTur(k)}>{et}<span className="sayi">{n}</span></button> : null;
        })}
      </div>
      <div className="icerik">
        {!liste.length && <Bos baslik="Eşleşen seçenek yok" metin="Aramayı ya da türü değiştir." />}
        <div className="motion-izgara galeri-izgara">{liste.map((o) => <Kart key={anahtar(o)} o={o} secili={!!secili && anahtar(secili) === anahtar(o)} karsi={karsiVar(o)} sec={() => sec(o)} karsiDegis={() => karsiDegis(o)} />)}</div>
      </div>
      {secili && (
        <div className="alt">
          <div style={{ fontWeight: 550, marginBottom: 2 }}>{secili.title} <span className="ipucu">{secili.tur}{secili.font ? ` · ${secili.font}` : ""}</span></div>
          {(secili.amac || secili.ne_zaman) && <p className="ipucu" style={{ margin: "0 0 8px" }}>{secili.amac ? `${secili.amac} ` : ""}{secili.ne_zaman}</p>}
          {secili.tur === "fizik" && <>
            <ParamFormu o={secili} deger={param} degis={setParam} />
            <div className="form" style={{ marginBottom: 8 }}>
              <label>Işık<select value={isik} onChange={(e) => setIsik(e.target.value)}>{isiklar.map((i) => <option key={i.id} value={i.id}>{i.title}</option>)}</select></label>
              <label>Süre (sn)<input type="number" min={1} max={30} step={0.5} value={sure} onChange={(e) => setSure(Number(e.target.value))} /></label>
            </div>
          </>}
          {secili.tur === "karakter" && (
            <div className="form" style={{ marginBottom: 8 }}>
              <label>Süre (sn)<input type="number" min={1} max={120} step={0.5} value={sure} onChange={(e) => setSure(Number(e.target.value))} /></label>
              <label style={{ flexDirection: "row", alignItems: "center", gap: 6 }}><input type="checkbox" checked={saydam} onChange={(e) => setSaydam(e.target.checked)} /> Saydam zemin (üst izde)</label>
            </div>
          )}
          <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
            <Dugme tur="birincil" disabled={is} onClick={eylem}><Plus size={14} /> {is ? "Hazırlanıyor" : eylemAdi[secili.tur]}</Dugme>
            <span style={{ flex: 1 }} />
            <Dugme title={secili.gizli ? "Galeride yeniden göster" : "Galeriden gizle (silinmez)"} onClick={() => gizle(secili, !secili.gizli)}>
              {secili.gizli ? <Eye size={14} /> : <EyeOff size={14} />} {secili.gizli ? "Göster" : "Gizle"}
            </Dugme>
          </div>
        </div>
      )}
      {acik && karsi.length > 1 && <Karsilastir ogeler={karsi} kapat={() => setAcik(false)} cikar={(o) => setKarsi(karsi.filter((x) => anahtar(x) !== anahtar(o)))} />}
    </>
  );
};
