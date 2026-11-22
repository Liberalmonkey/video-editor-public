import { ClipboardCheck, Download, FileText, FolderOpen, Music2, RefreshCw, Trash2, Upload } from "lucide-react";
import React, { useCallback, useEffect, useState } from "react";
import { boyutYaz, istek, sor, sureYaz, yukle } from "../api";
import { useDepo } from "../depo";
import { Bos, DosyaSec, IkonDugme, Iskelet } from "../ortak";
import { useKurgu, type KaynakOge } from "../zaman/depo";
import { SURUKLE_TUR } from "../zaman/Timeline";

interface Dosya { yol: string; ad: string; tur: string; boyut: number; sure: number | null; url: string }
interface Yukleme { ad: string; oran: number }

const YUKLENEBILIR = "video/*,audio/*,image/*,.md,.txt,.srt,.json";

// Yalnız girdiler kaynak olabilir: çıktı dosyası yeniden kurguya girmez, work dışıdır.
const kaynakOgesi = (d: Dosya, girdi: boolean): KaynakOge | undefined =>
  girdi && (d.tur === "video" || d.tur === "ses" || d.tur === "gorsel") ? { yol: `inputs:${d.yol}`, ad: d.ad, tur: d.tur } : undefined;

export const DosyaPaneli: React.FC<{ bolge: "inputs" | "outputs" }> = ({ bolge }) => {
  const { aktif, surum, goster, goruntu, onayla, bildir, hata, tazele, isBaslat } = useDepo();
  const [liste, setListe] = useState<Dosya[] | null>(null);
  const [yuklemeler, setYuklemeler] = useState<Yukleme[]>([]);
  const [uzerinde, setUzerinde] = useState(false);
  const girdi = bolge === "inputs";

  const al = useCallback(async () => {
    if (!aktif) return setListe(null);
    try { setListe(await istek(`/api/dosyalar/${aktif.studyo}/${aktif.ad}/${bolge}`)); }
    catch (e) { hata(e); setListe([]); }
  }, [aktif, bolge]);
  useEffect(() => { al(); }, [al, surum]);

  const yukleHepsi = async (dosyalar: File[]) => {
    if (!aktif || !dosyalar.length) return;
    setYuklemeler(dosyalar.map((d) => ({ ad: d.name, oran: 0 })));
    let basarili = 0;
    // Sırayla: disk tek, eşzamanlı büyük yazma yavaşlatır.
    for (const [i, d] of dosyalar.entries()) {
      try {
        await yukle(`/api/yukle/${aktif.studyo}/${aktif.ad}?${sor({ dosya: d.name })}`, d, (oran) =>
          setYuklemeler((l) => l.map((y, k) => (k === i ? { ...y, oran } : y))));
        basarili++;
      } catch (e) { hata(new Error(`${d.name}: ${(e as Error).message}`)); }
    }
    setYuklemeler([]);
    if (basarili) bildir(`${basarili} dosya yüklendi`);
    tazele();
    useDepo.getState().projeleriAl();
  };

  const sil = async (d: Dosya) => {
    const k = useKurgu.getState().kurgu;
    const kullanan = girdi && k ? k.klipler.filter((c) => c.kaynak && k.kaynaklar[c.kaynak]?.yol === `inputs:${d.yol}`).length : 0;
    const tamam = await onayla({ baslik: "Dosyayı sil", onay: "Sil", tehlike: true, metin: `${d.yol}\n\n${kullanan ? `Timeline'da ${kullanan} klip bu dosyayı kullanıyor. Silinirse render durur.\n\n` : ""}Dosya geri dönüşüm kutusuna gider.` });
    if (!tamam || !aktif) return;
    try {
      const r = await istek(`/api/dosya/${aktif.studyo}/${aktif.ad}/${bolge}?${sor({ yol: d.yol })}`, { method: "DELETE" });
      bildir(r.mesaj);
      if (goruntu?.url === d.url) goster(null);
      tazele();
      useDepo.getState().kurguAl(); // silinen kaynak timeline'da işaretlensin
    } catch (e) { hata(e); }
  };

  const klasor = () => aktif && istek(`/api/klasor-ac/${aktif.studyo}/${aktif.ad}/${bolge}`, { method: "POST" }).catch(hata);

  if (!aktif) return <div className="panel"><Bos baslik="Proje seçilmedi" metin="Soldaki Proje panelinden bir proje aç." /></div>;

  const birak = girdi ? {
    onDragOver: (e: React.DragEvent) => { if (e.dataTransfer.types.includes("Files")) { e.preventDefault(); setUzerinde(true); } },
    onDragLeave: (e: React.DragEvent) => { if (!e.currentTarget.contains(e.relatedTarget as Node)) setUzerinde(false); },
    onDrop: (e: React.DragEvent) => { if (e.dataTransfer.files.length) { e.preventDefault(); setUzerinde(false); yukleHepsi([...e.dataTransfer.files]); } },
  } : {};

  return (
    <div className={`panel birakma ${uzerinde ? "uzerinde" : ""}`} {...birak}>
      <div className="arac">
        {girdi && <DosyaSec kabul={YUKLENEBILIR} sec={yukleHepsi} disabled={!!yuklemeler.length}><Upload size={14} /> Yükle</DosyaSec>}
        <span className="ipucu">{liste ? `${liste.length} dosya` : ""}</span>
        <span className="bosluk" />
        <IkonDugme ad="Listeyi yenile" onClick={al}><RefreshCw size={14} /></IkonDugme>
        <IkonDugme ad="Klasörde aç" onClick={klasor}><FolderOpen size={14} /></IkonDugme>
      </div>
      {!!yuklemeler.length && (
        <div className="alt" style={{ borderTop: 0, borderBottom: "1px solid var(--cizgi)", display: "grid", gap: 6 }}>
          {yuklemeler.map((y, i) => (
            <div key={i}>
              <div className="ipucu" style={{ display: "flex", justifyContent: "space-between" }}><span>{y.ad}</span><span>%{Math.round(y.oran * 100)}</span></div>
              <div className="ilerleme"><i style={{ width: `${y.oran * 100}%` }} /></div>
            </div>
          ))}
        </div>
      )}
      <div className="icerik">
        {!liste && <Iskelet />}
        {liste && !liste.length && (girdi
          ? <Bos baslik="Girdi klasörü boş" metin="Videoları, görselleri ve senaryoyu buraya sürükleyip bırak. Birden çok videoda sıra doğal ada göredir." />
          : <Bos baslik="Henüz teslim yok" metin="Çıktı ayarlarından EXPORT'a bas, teslim dosyaları burada görünür." />)}
        {liste?.map((d) => {
          const secili = goruntu?.url === d.url;
          const gorunum = d.tur === "video" || d.tur === "gorsel";
          const kaynak = kaynakOgesi(d, girdi);
          const ac = () => goster({ tur: d.tur, url: d.url, ad: d.ad, kaynak });
          return (
            <div key={d.yol} className={`satir ${secili ? "secili" : ""}`} role="button" tabIndex={0} title={d.yol} draggable={!!kaynak}
              onDragStart={(e) => { if (kaynak) { e.dataTransfer.setData(SURUKLE_TUR, JSON.stringify(kaynak)); e.dataTransfer.effectAllowed = "copy"; } }}
              onClick={ac} onKeyDown={(e) => e.key === "Enter" && e.target === e.currentTarget && ac()}>
              {gorunum
                ? <img className="kucuk" loading="lazy" alt="" src={`/api/kucuk/${aktif.studyo}/${aktif.ad}/${bolge}?${sor({ yol: d.yol })}`} />
                : <span className="kucuk-ikon">{d.tur === "ses" ? <Music2 size={15} /> : <FileText size={15} />}</span>}
              <span className="ad">{d.yol}</span>
              <span className="bilgi">{sureYaz(d.sure)}</span>
              <span className="bilgi" style={{ width: 62, textAlign: "right" }}>{boyutYaz(d.boyut)}</span>
              {!girdi && <a className="dugme ikon eylem" title={`${d.ad} dosyasını indir`} aria-label={`${d.ad} dosyasını indir`} download={d.ad} href={`/api/indir/${aktif.studyo}/${aktif.ad}?${sor({ yol: d.yol })}`} onClick={(e) => e.stopPropagation()}><Download size={14} /></a>}
              {!girdi && d.tur === "video" && <IkonDugme ad="Denetim çalıştır" className="eylem" onClick={(e) => { e.stopPropagation(); isBaslat("denetim", { video: d.yol }); }}><ClipboardCheck size={14} /></IkonDugme>}
              <IkonDugme ad={`${d.ad} dosyasını sil`} className="eylem" onClick={(e) => { e.stopPropagation(); sil(d); }}><Trash2 size={14} /></IkonDugme>
            </div>
          );
        })}
      </div>
    </div>
  );
};
