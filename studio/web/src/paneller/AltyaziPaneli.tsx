import { ChevronLeft, ChevronRight, RotateCcw, ScanSearch, Scissors, Trash2 } from "lucide-react";
import React, { useEffect, useMemo, useRef, useState } from "react";
import type { AltyaziStil } from "../../../remotion/tipler";
import { istek } from "../api";
import { useDepo } from "../depo";
import { Bos, Dugme, IkonDugme } from "../ortak";
import { useKurgu } from "../zaman/depo";
import * as K from "../zaman/komutlar";
import { git } from "../zaman/oynatici";
import { OnerilerPaneli } from "./OnerilerPaneli";
import { Bolum, Metin, Satir, Sayi, Secim } from "./alanlar";

// ADR 0014: başlangıç noktası. Stil boşken SplitReel Captions çalışır, bu değerler yalnız özel stilin ilk hâlidir.
const STANDART: AltyaziStil = { font: "Montserrat", boyut: 72, renk: "#FFFFFF", aktif_renk: "#FF7A00", kontur: 12, kontur_renk: "#000000", kip: "kelime", en_kelime: 3, en_karakter: 18, konum: null, dosya: null };

const StilFormu: React.FC = () => {
  const altyazi = useKurgu((d) => d.kurgu?.altyazi);
  const duzenle = useKurgu((d) => d.duzenle);
  const hata = useDepo((d) => d.hata);
  const [fontlar, setFontlar] = useState<{ id: string; file: string }[]>([]);
  useEffect(() => { istek("/api/kutuphane").then((v) => setFontlar(v.font)).catch(hata); }, []);
  if (!altyazi) return null;
  const stil = altyazi.stil;
  const degis = (p: Partial<AltyaziStil>, b?: string) => duzenle("Altyazı stili", (d) => { d.altyazi.stil = { ...(d.altyazi.stil ?? STANDART), ...p }; }, b && `altyazi.${b}`);
  const s = stil ?? STANDART;
  return (
    <Bolum ad="Altyazı görünümü">
      <div className="ef-baslik" style={{ padding: "0 0 6px" }}>
        {stil ? <span className="rozet uyari">Standart dışı</span> : <span className="rozet iyi">Standart (ADR 0014)</span>}
        {stil && <Dugme onClick={() => duzenle("Altyazı standardı", (d) => { d.altyazi.stil = null; })}><RotateCcw size={13} /> Standarda dön</Dugme>}
      </div>
      <Satir ad="Kip"><Secim etiket="Altyazı kipi" deger={s.kip} secenekler={[["kelime", "Okunan kelime renkli"], ["tam", "Tek renk"]]} degis={(v) => degis({ kip: v as any })} /></Satir>
      <Satir ad="Font"><Secim etiket="Altyazı fontu" deger={s.font} secenekler={fontlar.map((f) => [f.id, f.id])} degis={(v) => degis({ font: v, dosya: fontlar.find((f) => f.id === v)?.file ?? null })} /></Satir>
      <Satir ad="Boyut"><Sayi etiket="Altyazı boyutu" deger={s.boyut} min={20} max={240} birim="px" degis={(v) => degis({ boyut: v }, "boyut")} /></Satir>
      <Satir ad="Renk"><input type="color" aria-label="Altyazı rengi" value={s.renk} onChange={(e) => degis({ renk: e.target.value }, "renk")} /></Satir>
      <Satir ad="Okunan kelime"><input type="color" aria-label="Okunan kelime rengi" value={s.aktif_renk} onChange={(e) => degis({ aktif_renk: e.target.value }, "aktif")} /></Satir>
      <Satir ad="Kontur"><Sayi etiket="Kontur kalınlığı" deger={s.kontur} min={0} max={40} birim="px" degis={(v) => degis({ kontur: v }, "kontur")} /></Satir>
      <Satir ad="Kontur rengi"><input type="color" aria-label="Kontur rengi" value={s.kontur_renk} onChange={(e) => degis({ kontur_renk: e.target.value }, "kr")} /></Satir>
      <Satir ad="Sayfa kelime"><Sayi etiket="Sayfa başına kelime" deger={s.en_kelime} min={1} max={12} degis={(v) => degis({ en_kelime: v }, "ek")} /></Satir>
      <Satir ad="Sayfa harf"><Sayi etiket="Sayfa başına harf" deger={s.en_karakter} min={4} max={80} degis={(v) => degis({ en_karakter: v }, "eh")} /></Satir>
      <Satir ad="Konum"><Secim etiket="Altyazı konumu" deger={s.konum == null ? "" : String(s.konum)} secenekler={[["", "Otomatik"], ["0.15", "Üst"], ["0.5", "Orta"], ["0.73", "Alt"], ["0.88", "En alt"]]} degis={(v) => degis({ konum: v === "" ? null : Number(v) })} /></Satir>
    </Bolum>
  );
};

export const AltyaziPaneli: React.FC = () => {
  const kurgu = useKurgu((d) => d.kurgu);
  const duzenle = useKurgu((d) => d.duzenle);
  const anahtar = useKurgu((d) => d.anahtar);
  const { isBaslat, bildir, hata } = useDepo();
  const [ara, setAra] = useState("");
  const bekle = useRef(false);
  const biten = useDepo((d) => d.isler.filter((x) => x.komut === "hazirla" && x.bitis).length);
  const kutu = useRef<HTMLDivElement>(null);
  const satirlar = useMemo(() => (kurgu ? K.kelimeSatirlari(kurgu) : []), [kurgu?.klipler, kurgu?.kelimeler, kurgu?.altyazi.iz]);
  const gorunen = useMemo(() => {
    const q = ara.toLocaleLowerCase("tr").trim();
    return q ? satirlar.filter((s) => s.w.toLocaleLowerCase("tr").includes(q)) : satirlar;
  }, [satirlar, ara]);

  // Okunan kelime: yeniden çizim yerine sınıf değiştirilir, satır sayısı binlere çıkabilir.
  useEffect(() => useKurgu.subscribe((s, o) => {
    if (s.zaman === o.zaman || !kutu.current) return;
    const eski = kutu.current.querySelector(".kelime.aktif");
    let i = -1;
    for (let lo = 0, hi = gorunen.length - 1; lo <= hi;) {
      const m = (lo + hi) >> 1;
      if (gorunen[m].s <= s.zaman + 1e-3) { i = m; lo = m + 1; } else hi = m - 1;
    }
    const yeni = i >= 0 && s.zaman <= gorunen[i].e + 0.3 ? kutu.current.querySelector(`[data-i="${i}"]`) : null;
    if (eski !== yeni) {
      eski?.classList.remove("aktif");
      yeni?.classList.add("aktif");
      if (yeni && s.oynuyor) yeni.scrollIntoView({ block: "nearest" });
    }
  }), [gorunen]);

  const kelimeleriAl = async (sessiz = false): Promise<number> => {
    const k = useKurgu.getState().kurgu;
    if (!k || !anahtar) return 0;
    try {
      const eksik = Object.entries(k.kaynaklar).filter(([id, v]) => !k.kelimeler?.[id]?.length && /\.(mp4|mov|mkv|webm|avi|m4v|wav|mp3|m4a|aac|flac|ogg)$/i.test(v.yol) && !v.yol.startsWith("library:"));
      const sonuc = await Promise.all(eksik.map(async ([id, v]) => [id, (await istek(`/api/kaynak/${anahtar}`, { method: "POST", json: { yol: v.yol } })).kelimeler] as const));
      const dolu = sonuc.filter(([, l]) => l.length);
      if (dolu.length) duzenle("Transkript al", (d) => { for (const [id, l] of dolu) (d.kelimeler ??= {})[id] = l; });
      const n = dolu.reduce((t, [, l]) => t + l.length, 0);
      if (n || !sessiz) bildir(n ? `${n} kelime alındı` : "Transkript bulunamadı.", !n);
      return n;
    } catch (e) { hata(e); return 0; }
  };
  // Transkript yoksa hazırla işini başlatır; iş bitince kelimeler kendiliğinden projeye alınır.
  const hazirla = async () => {
    if (await kelimeleriAl(true)) return;
    bekle.current = true;
    isBaslat("hazirla");
  };
  useEffect(() => { if (bekle.current) { bekle.current = false; kelimeleriAl(); } }, [biten]);

  if (!kurgu) return <div className="panel"><Bos baslik="Kurgu yok" metin="Altyazı için bir proje aç." /></div>;
  const izler = kurgu.izler.filter((i) => kurgu.klipler.some((c) => c.iz === i.id && c.kaynak)).map((i) => [i.id, i.id] as [string, string]);
  const kare = 1 / kurgu.sekans.fps;

  return (
    <div className="panel">
      <div className="arac" style={{ flexWrap: "wrap" }}>
        <label style={{ display: "flex", alignItems: "center", gap: 5 }}>
          <input type="checkbox" checked={kurgu.altyazi.acik} style={{ minHeight: 0 }} onChange={(e) => duzenle("Altyazı aç kapat", (d) => { d.altyazi.acik = e.target.checked; })} /> Altyazı
        </label>
        {izler.length > 0 && <Secim etiket="Altyazı izi" deger={kurgu.altyazi.iz} secenekler={izler.some(([i]) => i === kurgu.altyazi.iz) ? izler : [[kurgu.altyazi.iz, kurgu.altyazi.iz], ...izler]} degis={(v) => duzenle("Altyazı izi", (d) => { d.altyazi.iz = v; })} />}
        <input type="search" aria-label="Kelime ara" placeholder="Kelime ara" value={ara} onChange={(e) => setAra(e.target.value)} style={{ flex: 1, minWidth: 90 }} />
        <Dugme title="Transkript yoksa hazırlar, bitince projeye alır" onClick={hazirla}><ScanSearch size={14} /> Transkripti hazırla</Dugme>
        {ara.trim() && gorunen.length > 0 && <Dugme title="Aramada bulunan kelimeleri görüntü ve sesiyle kurgudan çıkarır" onClick={() => { const n = gorunen.length; duzenle("Bulunanları kes", (d) => K.araliklariCikar(d, gorunen.map((s) => [s.s, s.e]))); bildir(`${n} kelime kurgudan çıkarıldı`); }}><Scissors size={13} /> Bulunanları kes ({gorunen.length})</Dugme>}
      </div>
      <div className="alt-liste" ref={kutu}>
        {!satirlar.length && <Bos baslik="Bu izde kelime yok" metin="Transkripti hazırla konuşmayı yazıya döker ve bitince projeye alır."><Dugme onClick={hazirla}><ScanSearch size={14} /> Transkripti hazırla</Dugme></Bos>}
        {gorunen.map((s, i) => (
          <div key={`${s.kaynak}.${s.i}.${s.klip}`} data-i={i} className="kelime">
            <button type="button" className="kelime-t" title="Buraya git" onClick={() => git(s.s)}>{s.s.toFixed(2)}</button>
            <Metin etiket={`Kelime ${i + 1}`} deger={s.w} degis={(v) => { if (v.trim()) duzenle("Kelime", (d) => K.kelimeYaz(d, s.kaynak, s.i, v)); }} />
            <span className="kelime-d">
              <IkonDugme ad="Başı bir kare geri" onClick={() => duzenle("Kelime zamanı", (d) => K.kelimeZaman(d, s.kaynak, s.i, -kare, 0), `kz.${s.kaynak}.${s.i}`)}><ChevronLeft size={13} /></IkonDugme>
              <IkonDugme ad="Başı bir kare ileri" onClick={() => duzenle("Kelime zamanı", (d) => K.kelimeZaman(d, s.kaynak, s.i, kare, 0), `kz.${s.kaynak}.${s.i}`)}><ChevronRight size={13} /></IkonDugme>
              <IkonDugme ad="Kelimeyi kurgudan çıkar: görüntü ve sesiyle kesilir" onClick={() => duzenle("Kelimeyi kes", (d) => K.araliklariCikar(d, [[s.s, s.e]]))}><Scissors size={13} /></IkonDugme>
              <IkonDugme ad="Kelimeyi altyazıdan sil" onClick={() => duzenle("Kelime sil", (d) => K.kelimeSil(d, s.kaynak, s.i))}><Trash2 size={13} /></IkonDugme>
            </span>
          </div>
        ))}
      </div>
      <div className="alt-stil"><Bolum ad="Sessizlik ve dolgu" acik={false}><OnerilerPaneli gomulu /></Bolum><StilFormu /></div>
    </div>
  );
};
