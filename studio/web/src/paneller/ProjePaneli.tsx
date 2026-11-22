import { Clapperboard, FolderPlus, Trash2 } from "lucide-react";
import React, { useMemo, useState } from "react";
import { istek } from "../api";
import { useDepo, type Proje } from "../depo";
import { Bos, Diyalog, Dugme, IkonDugme, Iskelet } from "../ortak";

const YeniProjeDiyalog: React.FC<{ acik: boolean; kapat: () => void }> = ({ acik, kapat }) => {
  const { studyolar, projeleriAl, projeAc, hata } = useDepo();
  const [studyo, setStudyo] = useState("instagram");
  const [ad, setAd] = useState("");
  const gonder = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const v = await istek("/api/projeler", { method: "POST", json: { studyo, ad } });
      await projeleriAl();
      const p = useDepo.getState().projeler.find((x) => x.studyo === v.studyo && x.ad === v.ad);
      if (p) await projeAc(p);
      setAd(""); kapat();
    } catch (er) { hata(er); }
  };
  return (
    <Diyalog acik={acik} kapat={kapat}>
      <h2>Yeni proje</h2>
      <form onSubmit={gonder}>
        <div className="form">
          <label>Stüdyo
            <select value={studyo} onChange={(e) => setStudyo(e.target.value)}>{studyolar.map((s) => <option key={s}>{s}</option>)}</select>
          </label>
          <label className="zorunlu">Proje adı
            <input value={ad} onChange={(e) => setAd(e.target.value)} required autoFocus placeholder="ör. 12-reels-fiyat" />
          </label>
        </div>
        <div className="eylemler">
          <Dugme onClick={kapat}>Vazgeç</Dugme>
          <Dugme tur="birincil" type="submit" disabled={!ad.trim()}>Oluştur</Dugme>
        </div>
      </form>
    </Diyalog>
  );
};

export const ProjePaneli: React.FC = () => {
  const { projeler, aktif, projeAc, projeleriAl, onayla, bildir, hata } = useDepo();
  const [yeni, setYeni] = useState(false);
  const [yuklendi, setYuklendi] = useState(false);
  const [ara, setAra] = useState("");
  React.useEffect(() => { projeleriAl().then(() => setYuklendi(true)); }, []);

  const gruplar = useMemo(() => {
    const m = new Map<string, Proje[]>();
    for (const p of projeler) if (p.ad.toLocaleLowerCase("tr").includes(ara.toLocaleLowerCase("tr"))) m.set(p.studyo, [...(m.get(p.studyo) ?? []), p]);
    return [...m];
  }, [projeler, ara]);

  const sil = async (p: Proje) => {
    const tamam = await onayla({
      baslik: "Projeyi sil", onay: "Projeyi sil", tehlike: true,
      metin: `${p.studyo}/${p.ad}\n\nGirdi ve çıktı klasörlerinin tamamı silinir: teslimler ve kurgu dahil. Dosyalar geri dönüşüm kutusuna gider, çok büyükse Projeler/.cop altına taşınır.`,
    });
    if (!tamam) return;
    try {
      const r = await istek(`/api/projeler/${p.studyo}/${p.ad}`, { method: "DELETE" });
      bildir(r.mesaj);
      if (aktif === p) await projeAc(null);
      await projeleriAl();
    } catch (e) { hata(e); }
  };

  return (
    <div className="panel">
      <div className="arac">
        <input type="search" placeholder="Proje ara" aria-label="Proje ara" value={ara} onChange={(e) => setAra(e.target.value)} style={{ flex: 1, minWidth: 0 }} />
        <Dugme onClick={() => setYeni(true)}><FolderPlus size={14} /> Yeni</Dugme>
      </div>
      <div className="icerik">
        {!yuklendi && <Iskelet n={4} />}
        {yuklendi && !projeler.length && <Bos baslik="Henüz proje yok" metin="Yeni proje oluştur, videolarını Medya paneline bırak."><Dugme tur="birincil" onClick={() => setYeni(true)}>Yeni proje</Dugme></Bos>}
        {yuklendi && !!projeler.length && !gruplar.length && <Bos baslik="Eşleşen proje yok" />}
        {gruplar.map(([s, liste]) => (
          <section key={s}>
            <div className="baslik">{s}</div>
            {liste.map((p) => {
              const secili = aktif?.studyo === p.studyo && aktif.ad === p.ad;
              return (
                <div key={p.ad} className={`satir ${secili ? "secili" : ""}`} role="button" tabIndex={0} aria-pressed={secili}
                  onClick={() => projeAc(p)} onKeyDown={(e) => e.key === "Enter" && e.target === e.currentTarget && projeAc(p)}>
                  <Clapperboard size={14} color="var(--y3)" />
                  <span className="ad">{p.ad}</span>
                  {p.kurgu && <span className="rozet vurgu">kurgu</span>}
                  <IkonDugme ad={`${p.ad} projesini sil`} className="eylem" onClick={(e) => { e.stopPropagation(); sil(p); }}><Trash2 size={14} /></IkonDugme>
                </div>
              );
            })}
          </section>
        ))}
      </div>
      <YeniProjeDiyalog acik={yeni} kapat={() => setYeni(false)} />
    </div>
  );
};
