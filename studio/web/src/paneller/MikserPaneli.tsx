import { AudioLines, FileAudio, Gauge, Headphones, Layers, VolumeX } from "lucide-react";
import React, { useEffect, useState } from "react";
import { istek } from "../api";
import { useDepo } from "../depo";
import { Bos, Dugme } from "../ortak";
import { sesiAyirUygula, useKurgu } from "../zaman/depo";
import * as K from "../zaman/komutlar";
import { Secim } from "./alanlar";
import { SesMetresi } from "./SesMetresi";
import { BICIMLER, ayrilmisMi, konusmayiAyir, sesKlibi, sesiDosyayaCikar, stemleriEkle, type StemKipi } from "./sesAraclari";

interface Ses { olcum: { I: number; TP: number; LRA: number } | null; yerlesen?: number; uyarilar?: string[]; dusen?: { t: number; tur: string; neden: string }[]; eski?: boolean; dinle?: string | null }

const Kanal: React.FC<{ id: string }> = ({ id }) => {
  const iz = useKurgu((d) => d.kurgu?.izler.find((i) => i.id === id));
  const adet = useKurgu((d) => d.kurgu?.klipler.filter((c) => c.iz === id).length ?? 0);
  const solo = useKurgu((d) => d.solo.includes(id));
  const duzenle = useKurgu((d) => d.duzenle);
  if (!iz) return null;
  const gain = (v: number) => duzenle(`${id} seviye`, (d) => { d.izler.find((x) => x.id === id)!.gain_db = v; }, `iz.${id}.gain`);
  return (
    <div className="kanal">
      <div className="kanal-ad" title={iz.ad || id}>{id}{iz.ad ? ` ${iz.ad}` : ""}</div>
      <span className="ipucu" style={{ fontSize: 10 }}>{adet} klip</span>
      <div className="kanal-orta">
        <input className="fader" type="range" aria-label={`${id} seviyesi`} min={-40} max={12} step={0.5} value={iz.gain_db} onChange={(e) => gain(Number(e.target.value))} onDoubleClick={() => gain(0)} title="Çift tık: 0 dB" />
        <SesMetresi iz={id} genislik={10} yukseklik={150} />
      </div>
      <span className="kanal-db">{iz.gain_db > 0 ? "+" : ""}{iz.gain_db.toFixed(1)} dB</span>
      <div className="kanal-d">
        <Dugme className="m" aria-pressed={iz.sessiz} aria-label={`${id} sustur`} title="Sustur: render'ı da etkiler" onClick={() => duzenle(`${id} sustur`, (d) => { const x = d.izler.find((q) => q.id === id)!; x.sessiz = !x.sessiz; })}>M</Dugme>
        <Dugme className="s" aria-pressed={solo} aria-label={`${id} solo`} title="Solo: yalnız önizleme" onClick={() => { const d = useKurgu.getState(); d.ayarla({ solo: solo ? d.solo.filter((x) => x !== id) : [...d.solo, id] }); }}>S</Dugme>
      </div>
    </div>
  );
};

const STEM_SECENEK: [string, string][] = [["2", "2 kanal: konuşma + müzik"], ["4", "4 kanal: konuşma, davul, bas, diğer"]];

// Seçili klibin sesi için tek yer: ayır, dosyaya çıkar, konuşmayı müzikten ayır, ayrılanları kurguya koy. Mantık sesAraclari.ts'te.
const SesAraclari: React.FC = () => {
  const secim = useKurgu((d) => d.secim);
  const duzenle = useKurgu((d) => d.duzenle);
  useKurgu((d) => d.kurgu); // klip değişince düğme durumları yenilensin
  const surer = useDepo((d) => d.isler.some((x) => (x.komut === "ayristir" || x.komut === "ses-cikar") && !x.bitis));
  const hata = useDepo((d) => d.hata);
  const [mesgul, setMesgul] = useState<string | null>(null);
  const [bicim, setBicim] = useState("wav");
  const [stem, setStem] = useState<StemKipi>(2);
  const c = sesKlibi(secim);
  const k = useKurgu.getState().kurgu;
  const ayrik = !!k && K.baglilar(k, secim).some((x) => k.klipler.find((q) => q.id === x)?.ses_kapali || k.klipler.find((q) => q.id === x)?.olay?.konusma);
  const calis = async (ad: string, f: () => Promise<void>) => { setMesgul(ad); try { await f(); } catch (e) { hata(e); } finally { setMesgul(null); } };
  const mesgulMu = !!mesgul || surer;
  const ayrilamaz = !c || mesgulMu || ayrilmisMi(c);
  const etiket = (ad: string, metin: string) => (mesgul === ad ? "Ayrılıyor…" : metin);
  return (
    <aside className="olcum ses-araclar">
      <b style={{ fontSize: 12, fontWeight: 600 }}>Ses araçları</b>
      {!c && <p className="ipucu" style={{ margin: "6px 0" }}>Timeline'da sesi olan bir klip seç.</p>}
      <Dugme disabled={!secim.length} onClick={sesiAyirUygula} title="Görüntü ile sesi ayrı kliplere böler ya da geri birleştirir (Shift+A)"><AudioLines size={14} /> {ayrik ? "Sesi videoyla birleştir" : "Sesi videodan ayır"}</Dugme>
      <div className="sira">
        <Secim etiket="Ses dosyası biçimi" deger={bicim} degis={setBicim} secenekler={BICIMLER} />
        <Dugme disabled={!c || mesgulMu} onClick={() => calis("cikar", () => sesiDosyayaCikar(c!, bicim))} title="Klibin kaynağındaki sesi outputs/…/ses/ altına dosya olarak yazar"><FileAudio size={14} /> {etiket("cikar", "Sesi dosyaya çıkar")}</Dugme>
      </div>
      <div className="sira">
        <Secim etiket="Ayırma kanal sayısı" deger={String(stem)} degis={(v) => setStem(Number(v) as StemKipi)} secenekler={STEM_SECENEK} />
        <Dugme disabled={ayrilamaz} onClick={() => calis("ayir", () => konusmayiAyir(c!, stem, "Konuşmayı müzikten ayır"))} title="Demucs ile konuşmayı müzikten ayırır; konuşma klibe uygulanır"><AudioLines size={14} /> {etiket("ayir", "Konuşmayı müzikten ayır")}</Dugme>
      </div>
      <Dugme disabled={ayrilamaz} onClick={() => calis("muzik", () => konusmayiAyir(c!, 2, "Arka plan müziğini kaldır"))} title="Gerekirse sesi ayırır, 2 kanallı ayırmayla müziği atar ve klibi yalnız konuşmaya geçirir (tek geri alma)"><VolumeX size={14} /> {etiket("muzik", "Arka plan müziğini kaldır")}</Dugme>
      <Dugme disabled={!c || mesgulMu} onClick={() => calis("ekle", () => stemleriEkle(c!, stem))} title="Müziği (4 kanalda davul, bas, diğer sesleri de) kliple aynı yere, sessiz izlere koyar"><Layers size={14} /> {etiket("ekle", "Ayrılanları timeline'a ekle")}</Dugme>
      <label style={{ display: "flex", alignItems: "center", gap: 6 }} title="Uğultu ve fon gürültüsünü render'da azaltır. Önizlemede duyulmaz: Miks ölç, sonra Dinle.">
        <input type="checkbox" aria-label="Konuşmayı temizle" disabled={!c} checked={!!c?.ses.temizle} style={{ minHeight: 0 }}
          onChange={(e) => c && duzenle("Konuşma temizliği", (d) => { const x = d.klipler.find((q) => q.id === c.id); if (x) x.ses.temizle = e.target.checked; })} /> Konuşmayı temizle
      </label>
      <p className="ipucu" style={{ margin: "6px 0 0", fontSize: 11 }}>Ayırma CPU'da sesin yaklaşık 2,5 katı sürer; sonuç önbellekte kalır. Demucs kurulu değilse kurulum komutu görünür.</p>
    </aside>
  );
};

export const MikserPaneli: React.FC = () => {
  const izler = useKurgu((d) => d.kurgu?.izler.map((i) => i.id).join(","));
  const anahtar = useKurgu((d) => d.anahtar);
  const surum = useDepo((d) => d.surum);
  const { isBaslat, hata, goster } = useDepo();
  const [ses, setSes] = useState<Ses | null>(null);
  useEffect(() => {
    if (!anahtar) { setSes(null); return; }
    istek(`/api/ses/${anahtar}`).then(setSes).catch(hata);
  }, [anahtar, surum]);

  if (!izler) return <div className="panel"><Bos baslik="Kurgu yok" metin="Mikser için bir proje aç." /></div>;
  const L = ses?.olcum;
  const iyiI = L && L.I >= -15 && L.I <= -13, iyiT = L && L.TP <= -1;
  return (
    <div className="panel ses-panel">
      <div className="mikser">
        {izler.split(",").map((i) => <Kanal key={i} id={i} />)}
        <div className="kanal kanal-ana">
          <div className="kanal-ad">Çıkış</div>
          <span className="ipucu" style={{ fontSize: 10 }}>önizleme</span>
          <div className="kanal-orta"><SesMetresi genislik={22} yukseklik={150} /></div>
          <span className="kanal-db">dBFS</span>
        </div>
      </div>
      <aside className="olcum">
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <b style={{ fontSize: 12, fontWeight: 600 }}>Son miks</b>
          {L && ses?.eski && <span className="rozet uyari" title="Kurgu bu ölçümden sonra değişti">Eski</span>}
        </div>
        {!L && <p className="ipucu" style={{ margin: "6px 0" }}>Henüz ölçüm yok. Ses sayıları yalnız gerçek miksten gelir.</p>}
        {L && (
          <div className="olcum-sayi">
            <span>Yükseklik</span><b className={iyiI ? "iyi" : "kotu"} data-olcum="I">{L.I.toFixed(1)} LUFS</b>
            <span>Tepe</span><b className={iyiT ? "iyi" : "kotu"}>{L.TP.toFixed(1)} dBTP</b>
            <span>Dinamik</span><b>{L.LRA.toFixed(1)} LU</b>
            <span>Yerleşen ses</span><b>{ses?.yerlesen}</b>
          </div>
        )}
        <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
          <Dugme onClick={() => isBaslat("miks")} title="Görüntü render etmeden güncel sesi ölç"><Gauge size={14} /> Miks ölç</Dugme>
          {ses?.dinle && <Dugme onClick={() => goster({ tur: "video", url: ses.dinle!, ad: "Son miks" })}><Headphones size={14} /> Dinle</Dugme>}
        </div>
        {!!ses?.uyarilar?.length && <ul>{ses.uyarilar.map((u, i) => <li key={i}>{u}</li>)}</ul>}
        {!!ses?.dusen?.length && <ul>{ses.dusen.map((d, i) => <li key={i}>{d.t.toFixed(2)} sn {d.tur}: düştü, {d.neden}</li>)}</ul>}
        <p className="ipucu" style={{ margin: "8px 0 0", fontSize: 11 }}>Faderler dengeyi kurar; teslim yine -14 LUFS'a normalize edilir.</p>
      </aside>
      <SesAraclari />
    </div>
  );
};
