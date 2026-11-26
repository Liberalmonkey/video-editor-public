// Hazır stil kataloğu: kurulu skill ve repolardaki video stilleri (anime, çizgi film, editoryal...). Seçilen stil
// stüdyonun stil klasörüne paket olarak eklenir; istenirse o projede seçilir ve motion grafikleri stilin temasını alır.
// WHY: bkz. wiki/decisions/0042-stil-katalogu-ve-video-temasi.md
import { Check, Plus } from "lucide-react";
import React, { useEffect, useMemo, useState } from "react";
import { istek } from "../api";
import { useDepo } from "../depo";
import { Bos, Dugme, Iskelet } from "../ortak";

export interface KatalogStil {
  id: string;
  ad: string;
  kategori: string;
  kaynak: string;
  lisans: string;
  ozet: string;
  uygun: string;
  tempo: "yavas" | "orta" | "hizli";
  gecis: string[];
  kacin: string[];
  palet: Record<string, string>;
  motion_tema: string;
  font: { baslik?: string; govde?: string };
  onizleme: boolean;
  kart?: boolean; // ADR 0043: örnek setli stil kartı
}

interface KatalogYanit {
  kategoriler: string[];
  stiller: KatalogStil[];
}

const TEMPO = { yavas: "yavaş", orta: "orta", hizli: "hızlı" } as const;
export const RENK_SIRA = ["vurgu", "ikincil", "zemin", "yazi", "soluk"];

export const HazirStiller: React.FC<{
  studyo: string;
  proje: string | null;
  mevcut: string[];
  eklendi: (ad: string) => void;
}> = ({ studyo, proje, mevcut, eklendi }) => {
  const { hata, bildir } = useDepo();
  const [veri, setVeri] = useState<KatalogYanit | null>(null);
  const [kategori, setKategori] = useState<string>("");
  const [seciliId, setSeciliId] = useState<string | null>(null);
  const [mesgul, setMesgul] = useState(false);

  useEffect(() => {
    istek<KatalogYanit>("/api/stil-katalog").then(setVeri).catch(hata);
  }, []);

  const liste = useMemo(() => (veri?.stiller ?? []).filter((s) => !kategori || s.kategori === kategori), [veri, kategori]);
  const secili = veri?.stiller.find((s) => s.id === seciliId) ?? null;

  const ekle = async (projede: boolean) => {
    if (!secili) return;
    setMesgul(true);
    try {
      await istek(`/api/stil/${studyo}/katalogdan`, { method: "POST", json: { id: secili.id, proje: projede ? proje : null } });
      bildir(projede ? `${secili.ad} eklendi ve bu projede seçildi; grafikler ${secili.motion_tema} temasıyla gelir` : `${secili.ad} stillerine eklendi`);
      eklendi(secili.id);
    } catch (e) {
      hata(e);
    } finally {
      setMesgul(false);
    }
  };

  if (!veri) return <div className="icerik"><Iskelet /></div>;
  const sayi = (k: string) => veri.stiller.filter((s) => !k || s.kategori === k).length;

  return (
    <>
      <div className="motion-cipler" role="tablist" aria-label="Stil kategorisi">
        {["", ...veri.kategoriler].map((k) => (
          <button key={k || "hepsi"} type="button" role="tab" className="sekme" aria-selected={kategori === k} onClick={() => setKategori(k)}>
            {k || "Hepsi"}<span className="sayi">{sayi(k)}</span>
          </button>
        ))}
      </div>
      <div className="icerik">
        {!liste.length && <Bos baslik="Bu kategoride stil yok" />}
        <div className="motion-izgara stil-izgara">
          {liste.map((s) => (
            <div
              key={s.id}
              className={`motion-kart ${s.id === seciliId ? "secili" : ""}`}
              role="button"
              tabIndex={0}
              title={s.ozet}
              onClick={() => setSeciliId(s.id)}
              onKeyDown={(e) => e.key === "Enter" && setSeciliId(s.id)}
            >
              <span className="motion-kare dikey">
                {s.onizleme
                  ? <img src={`/api/stil-katalog/${s.id}/onizleme`} alt="" loading="lazy" />
                  : <span className="galeri-yer" style={{ background: s.palet.zemin }}>
                      <span className="galeri-palet">{RENK_SIRA.map((r) => <i key={r} style={{ background: s.palet[r] }} />)}</span>
                      <span className="galeri-yer-ad" style={{ color: s.palet.yazi }}>{s.ad}</span>
                    </span>}
                {mevcut.includes(s.id) && <span className="rozet iyi"><Check size={11} /> eklendi</span>}
              </span>
              <span className="motion-ad">{s.ad}</span>
            </div>
          ))}
        </div>
      </div>
      {secili && (
        <div className="alt" style={{ display: "grid", gap: 6 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
            <b>{secili.ad}</b>
            <span className="rozet">{secili.kategori}</span>
            <span className="rozet">tempo {TEMPO[secili.tempo]}</span>
            <span className="galeri-palet" title={`Motion teması: ${secili.motion_tema}`}>
              {RENK_SIRA.map((r) => <i key={r} style={{ background: secili.palet[r] }} title={`${r} ${secili.palet[r]}`} />)}
            </span>
          </div>
          <p className="ipucu" style={{ margin: 0 }}>{secili.ozet}</p>
          {secili.kart && (
            <a href={`/api/stil-katalog/${secili.id}/kart`} target="_blank" rel="noreferrer" title="Stil kartı: her katman bu stilde">
              <img src={`/api/stil-katalog/${secili.id}/kart`} alt={`${secili.ad} stil kartı`} loading="lazy" style={{ width: 160, borderRadius: 6, display: "block" }} />
            </a>
          )}
          <p className="ipucu" style={{ margin: 0 }}><b>Uygun:</b> {secili.uygun}</p>
          <p className="ipucu" style={{ margin: 0 }}><b>Kaçın:</b> {secili.kacin.join("; ")}</p>
          <p className="ipucu" style={{ margin: 0 }}>
            <b>Yazı:</b> {[secili.font.baslik, secili.font.govde].filter(Boolean).join(" + ")} · <b>Geçiş:</b> {secili.gecis.join(", ") || "düz kesim"} ·{" "}
            <b>Kaynak:</b> {secili.kaynak} ({secili.lisans})
          </p>
          <div className="eylemler">
            {mevcut.includes(secili.id) ? (
              <span className="ipucu">Stillerimde var; Stillerim sekmesinden seç ya da düzenle.</span>
            ) : (
              <>
                <Dugme disabled={mesgul} onClick={() => ekle(false)}><Plus size={14} /> Stillerime ekle</Dugme>
                {proje && (
                  <Dugme tur="birincil" disabled={mesgul} onClick={() => ekle(true)}>
                    <Check size={14} /> Ekle ve bu projede kullan
                  </Dugme>
                )}
              </>
            )}
          </div>
        </div>
      )}
    </>
  );
};
