import { ScanText, Scissors } from "lucide-react";
import React, { useState } from "react";
import { istek } from "../api";
import { useDepo } from "../depo";
import { Bos, Dugme } from "../ortak";
import { useKurgu } from "../zaman/depo";
import * as K from "../zaman/komutlar";
import { git } from "../zaman/oynatici";

// WHY: bkz. wiki/decisions/0024-oneri-araclari.md. Sessizlik ve dolgu yalnız adaydır; kullanıcı seçer, tek geri alma adımıyla kesilir.
interface Oneri { bas: number; bit: number; tur: "sessizlik" | "dolgu"; klip: string; neden: string }

export const OnerilerPaneli: React.FC<{ gomulu?: boolean }> = ({ gomulu }) => {
  const var_ = useKurgu((d) => !!d.kurgu);
  const { hata, bildir } = useDepo();
  const [liste, setListe] = useState<Oneri[] | null>(null);
  const [secili, setSecili] = useState<Set<number>>(new Set());
  const [yuk, setYuk] = useState(false);
  const isaretle = (l: Oneri[]) => useKurgu.getState().ayarla({ bulgular: l.map((o) => ({ kod: o.tur, seviye: "P2", bas: o.bas, bit: o.bit, kanit: o.neden, oneri: "Kes" })) });

  const bul = async () => {
    const d = useKurgu.getState();
    if (!d.anahtar) return;
    setYuk(true);
    try {
      await d.kaydet();
      const r: { oneriler: Oneri[] } = await istek(`/api/oneri/${d.anahtar}`);
      setListe(r.oneriler);
      setSecili(new Set(r.oneriler.map((_, i) => i)));
      isaretle(r.oneriler);
    } catch (e) { hata(e); } finally { setYuk(false); }
  };
  const uygula = () => {
    if (!liste) return;
    const ar = liste.filter((_, i) => secili.has(i)).map((o) => [o.bas, o.bit] as [number, number]);
    let toplam = 0;
    useKurgu.getState().duzenle("Önerileri kes", (d) => { toplam = K.araliklariCikar(d, ar); });
    setListe(null);
    useKurgu.getState().ayarla({ bulgular: [] });
    bildir(`${ar.length} aralık kesildi, video ${toplam.toFixed(1)} sn kısaldı. Geri almak için Ctrl+Z.`);
  };

  if (!var_) return <div className={gomulu ? undefined : "panel"}><Bos baslik="Kurgu yok" metin="Öneriler için bir proje aç." /></div>;
  const secSure = liste?.reduce((n, o, i) => n + (secili.has(i) ? o.bit - o.bas : 0), 0) ?? 0;
  return (
    <div className={gomulu ? undefined : "panel"}>
      <div className="arac" style={{ flexWrap: "wrap" }}>
        <Dugme disabled={yuk} onClick={bul} title="Konuşmadaki uzun sessizlikleri ve ıı, ee gibi dolguları bulur"><ScanText size={14} /> {yuk ? "Aranıyor" : "Sessizlik ve dolgu bul"}</Dugme>
        {liste && liste.length > 0 && <Dugme tur="birincil" disabled={!secili.size} onClick={uygula}><Scissors size={14} /> Seçilenleri kes ({secili.size}, {secSure.toFixed(1)} sn)</Dugme>}
      </div>
      <div className="icerik">
        {!liste && <p className="ipucu" style={{ padding: 8 }}>Kurgu değişmez: önce adaylar listelenir ve timeline cetvelinde gri işaretlenir. Seçtiğini kesersin.</p>}
        {liste && !liste.length && <Bos baslik="Aday yok" metin="Kesilecek uzun sessizlik ya da dolgu bulunmadı." />}
        {liste?.map((o, i) => (
          <label key={`${o.bas}-${o.klip}`} className="satir" style={{ gap: 6 }}>
            <input type="checkbox" checked={secili.has(i)} style={{ minHeight: 0 }} onChange={(e) => { const s = new Set(secili); if (e.target.checked) s.add(i); else s.delete(i); setSecili(s); }} />
            <button type="button" className="kelime-t" title="Buraya git" onClick={() => git(Math.max(0, o.bas - 0.5))}>{o.bas.toFixed(2)}</button>
            <span className={`rozet ${o.tur === "dolgu" ? "uyari" : ""}`}>{o.tur}</span>
            <span className="ad">{o.neden}</span>
          </label>
        ))}
      </div>
    </div>
  );
};
