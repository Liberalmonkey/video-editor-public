import { ChevronDown, CircleStop, FileOutput, FolderCheck, Hammer, Play, ScanSearch, Scissors, Sparkles, Wand2 } from "lucide-react";
import React, { useEffect, useRef, useState } from "react";
import { istek } from "../api";
import { useDepo, type IsOzet } from "../depo";
import { Bos, Dugme, IkonDugme } from "../ortak";

const ROZET: Record<string, [string, string]> = {
  sirada: ["", "Sırada"], calisiyor: ["vurgu", "Çalışıyor"], bitti: ["iyi", "Bitti"], hata: ["hata", "Hata"], iptal: ["uyari", "İptal"],
};

const sureMetni = (x: IsOzet, simdi: number) => {
  if (!x.baslangic) return "";
  const s = Math.round((x.bitis ?? simdi / 1000) - x.baslangic);
  return s >= 60 ? `${Math.floor(s / 60)} dk ${s % 60} sn` : `${s} sn`;
};

// WHY: bkz. wiki/decisions/0030-sade-arayuz.md. Seyrek işler tek menüde; bir öğeye basınca menü kapanır.
const DigerMenu: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [acik, setAcik] = useState(false);
  const kok = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!acik) return;
    const disari = (e: MouseEvent) => { if (!kok.current?.contains(e.target as Node)) setAcik(false); };
    const esc = (e: KeyboardEvent) => { if (e.key === "Escape") setAcik(false); };
    document.addEventListener("mousedown", disari);
    document.addEventListener("keydown", esc);
    return () => { document.removeEventListener("mousedown", disari); document.removeEventListener("keydown", esc); };
  }, [acik]);
  return (
    <div className="diger-menu" ref={kok}>
      <Dugme aria-expanded={acik} aria-haspopup="true" onClick={() => setAcik(!acik)}>Diğer <ChevronDown size={13} /></Dugme>
      {acik && <div className="diger-liste" onClick={() => setAcik(false)}>{children}</div>}
    </div>
  );
};

const disaAktar = async () => {
  const { anahtar, kaydet } = (await import("../zaman/depo")).useKurgu.getState();
  if (!anahtar) return;
  try {
    await kaydet();
    const r = await istek(`/api/disa/${anahtar}`, { method: "POST" });
    useDepo.getState().bildir(`Dışa aktarıldı: ${r.dosyalar.join(", ")}${r.uyarilar.length ? `. ${r.uyarilar.length} sahne ve metin klibi işaret olarak geçti, ayrı render gerekir.` : ""}`);
  } catch (e) { useDepo.getState().hata(e); }
};

export const IslerPaneli: React.FC = () => {
  const { aktif, isler, gunlukler, isBaslat, hata } = useDepo();
  const [secili, setSecili] = useState<number | null>(null);
  const [simdi, setSimdi] = useState(Date.now());
  const gunlukKutu = useRef<HTMLDivElement>(null);
  const aktifIs = isler.find((x) => x.id === secili) ?? isler[0];
  const satirlar = aktifIs ? gunlukler[aktifIs.id] ?? [] : [];
  const calisan = isler.some((x) => x.durum === "calisiyor");

  useEffect(() => {
    if (!calisan) return;
    const t = setInterval(() => setSimdi(Date.now()), 1000);
    return () => clearInterval(t);
  }, [calisan]);
  useEffect(() => {
    const k = gunlukKutu.current;
    if (k && k.scrollHeight - k.scrollTop - k.clientHeight < 80) k.scrollTop = k.scrollHeight;
  }, [satirlar.length]);

  return (
    <div className="panel">
      <div className="arac" style={{ flexWrap: "wrap" }}>
        <Dugme disabled={!aktif} title="Transkript, digest, kontak sayfası" onClick={() => isBaslat("hazirla")}><ScanSearch size={14} /> Hazırla</Dugme>
        <Dugme disabled={!aktif} title="Hızlı önizleme render'ı" onClick={() => isBaslat("taslak")}><Play size={14} /> Taslak</Dugme>
        <Dugme tur="birincil" disabled={!aktif} title="Çıktı ayarları: çözünürlük, kodek, kalite (Teslim alanı)" onClick={() => window.dispatchEvent(new CustomEvent("studio-alan", { detail: "teslim" }))}><Hammer size={14} /> Export</Dugme>
        <DigerMenu>
          <Dugme disabled={!aktif} title="AI panelini açar: isteği yaz, stili seç, AI ile editle" onClick={() => { for (const [olay, detail] of [["studio-alan", "kurgu"], ["studio-panel", "ajan"]]) window.dispatchEvent(new CustomEvent(olay, { detail })); }}><Wand2 size={14} /> AI Edit</Dugme>
          <Dugme disabled={!aktif} title="kesim.json ile konuşmacı videosu" onClick={() => isBaslat("kes")}><Scissors size={14} /> Konuşmacıyı birleştir (kes)</Dugme>
          <Dugme disabled={!aktif} title="Süre tablosu, kaizen satırı" onClick={() => isBaslat("kaizen")}><Sparkles size={14} /> Kaizen</Dugme>
          <Dugme title="Dosya düzeni denetimi" onClick={() => isBaslat("duzen")}><FolderCheck size={14} /> Düzen</Dugme>
          <Dugme disabled={!aktif} title="Kurguyu Premiere (XML), DaVinci Resolve ve Final Cut (FCPXML) için çıktılar klasörüne yazar" onClick={disaAktar}><FileOutput size={14} /> XML</Dugme>
        </DigerMenu>
      </div>
      {!isler.length && <Bos baslik="Çalışan iş yok" metin="Yukarıdan bir adım başlat. İşler sırayla çalışır, günlük burada akar." />}
      {!!isler.length && (
        <>
          <div style={{ maxHeight: "40%", overflow: "auto", flex: "none", borderBottom: "1px solid var(--cizgi)" }}>
            {isler.map((x) => {
              const [renk, et] = ROZET[x.durum] ?? ["", x.durum];
              return (
                <div key={x.id} className={`satir ${aktifIs?.id === x.id ? "secili" : ""}`} role="button" tabIndex={0} onClick={() => setSecili(x.id)} onKeyDown={(e) => e.key === "Enter" && setSecili(x.id)}>
                  <span className={`rozet ${renk}`}>{et}</span>
                  <span className="ad" title={x.baslik}>{x.baslik}</span>
                  <span className="bilgi">{sureMetni(x, simdi)}</span>
                  {(x.durum === "calisiyor" || x.durum === "sirada") && (
                    <IkonDugme ad="İptal et" onClick={(e) => { e.stopPropagation(); istek(`/api/isler/${x.id}/iptal`, { method: "POST" }).catch(hata); }}><CircleStop size={14} /></IkonDugme>
                  )}
                </div>
              );
            })}
          </div>
          <div ref={gunlukKutu} className="gunluk" tabIndex={0} aria-label="İş günlüğü">
            {satirlar.length ? satirlar.map((l, i) => <div key={i} className={/^\s*!/.test(l) ? "uyar" : undefined}>{l || " "}</div>) : <span className="ipucu">Henüz çıktı yok.</span>}
          </div>
        </>
      )}
    </div>
  );
};
