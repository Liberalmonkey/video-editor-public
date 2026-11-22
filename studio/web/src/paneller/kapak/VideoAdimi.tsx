// 1. adım: kapağın videosu, karesi ve referansları. Kaydırıcıyla tam an seçilip kare olarak eklenir (POST /kare, agy'siz).
import { Film, ImagePlus, Plus, Trash2 } from "lucide-react";
import React, { useRef, useState } from "react";
import { istek, sor, yukle } from "../../api";
import { useDepo } from "../../depo";
import { DosyaSec, Dugme } from "../../ortak";
import type { Durum } from "./tipler";
import { dosyaUrl, videoUrl } from "./yardimci";

const TUR_ADI: Record<string, string> = { girdi: "girdi", kurgu: "kurgu", teslim: "teslim" };

export const VideoAdimi: React.FC<{
  d: Durum; video: string | null; setVideo: (v: string | null) => void;
  seciliKare: number | null; setSeciliKare: (n: number | null) => void; yenile: () => void;
}> = ({ d, video, setVideo, seciliKare, setSeciliKare, yenile }) => {
  const aktif = useDepo((s) => s.aktif)!;
  const { hata, bildir } = useDepo();
  const oynatici = useRef<HTMLVideoElement>(null);
  const [ekleniyor, setEkleniyor] = useState(false);
  const dikey = d.h > d.w;

  const kareEkle = async () => {
    const v = oynatici.current;
    if (!v || !video) return;
    setEkleniyor(true);
    try {
      const r = await istek(`/api/kapak/${aktif.studyo}/${aktif.ad}/kare`, { method: "POST", json: { video, t: v.currentTime } });
      setSeciliKare(r.n);
      yenile();
    } catch (e) { hata(e); } finally { setEkleniyor(false); }
  };
  const refYukle = async (tur: "yuz" | "stil", dosyalar: File[]) => {
    for (const f of dosyalar) {
      try {
        await yukle(`/api/kapak/${aktif.studyo}/${aktif.ad}/referans?${sor({ tur, dosya: f.name })}`, f, () => {});
      } catch (e) { hata(e); return; }
    }
    bildir(`${dosyalar.length} referans eklendi`);
    yenile();
  };
  const refSil = async (ad: string) => {
    try { await istek(`/api/kapak/${aktif.studyo}/${aktif.ad}/referans/${encodeURIComponent(ad)}`, { method: "DELETE" }); yenile(); } catch (e) { hata(e); }
  };

  return (
    <div className="kapak-adim-ic">
      <div className="kapak-videolar" role="radiogroup" aria-label="Kapak videosu">
        <button type="button" role="radio" aria-checked={video === null} className={`kapak-video${video === null ? " secili" : ""}`}
          onClick={() => { setVideo(null); setSeciliKare(null); }} title="Projedeki bütün girdi videolarından kare alır">
          <Film size={14} /> Bütün girdi videoları
        </button>
        {d.videolar.map((v) => (
          <button key={v.yol} type="button" role="radio" aria-checked={video === v.yol} className={`kapak-video${video === v.yol ? " secili" : ""}`}
            onClick={() => { setVideo(v.yol); setSeciliKare(null); }} title={v.yol}>
            <Film size={14} /> {v.ad} <span className="rozet">{TUR_ADI[v.tur] ?? v.tur}</span>
          </button>
        ))}
        {!d.videolar.length && <span className="ipucu">Projede video yok: girdi klasörüne video koy ya da önce Final al.</span>}
      </div>

      {video && (
        <div className="kapak-an">
          <video ref={oynatici} src={videoUrl(aktif, video)} controls preload="metadata" muted
            style={{ maxHeight: dikey ? 260 : 200, maxWidth: "100%" }} aria-label="Kapak anı seçimi" />
          <Dugme onClick={kareEkle} disabled={ekleniyor} title="Videonun duraklattığın anını kare listesine ekler; kapak bu kareden kurulur">
            <Plus size={14} /> {ekleniyor ? "Ekleniyor…" : "Bu anı kare olarak ekle"}
          </Dugme>
        </div>
      )}

      <div className="ipucu">Kareler {seciliKare !== null ? `(Kare #${seciliKare} seçili; kapak bu kareden kurulur)` : "(seçmezsen brief seçer)"}</div>
      {d.kareler.length ? (
        <div className="kapak-kareler">
          {d.kareler.map((k) => {
            const sec = seciliKare === k.n;
            return (
              <button key={k.n} type="button" onClick={() => setSeciliKare(sec ? null : k.n)} title={`Kare ${k.n}${k.el ? " (elle eklendi)" : ""}`}
                aria-pressed={sec} className={`kapak-kare${sec ? " secili" : ""}`} style={{ width: dikey ? 56 : 96, aspectRatio: dikey ? "9 / 16" : "16 / 9" }}>
                <img src={dosyaUrl(aktif, "outputs", k.yol)} alt={`Kare ${k.n}`} />
                <i>{k.n}{k.el ? " ✎" : ""}</i>
              </button>
            );
          })}
        </div>
      ) : (
        <p className="ipucu" style={{ margin: 0 }}>Videodan kare alınamadı; önce girdi videosu ya da Final gerekli.</p>
      )}

      <div className="ipucu" style={{ marginTop: 8 }}>Referanslar: yüz fotoğrafı yüzü korur; stil referansı yalnız düzen ve rengi verir, içeriği kopyalanmaz.</div>
      <div className="kapak-referanslar">
        {d.referanslar.map((r) => (
          <figure key={`${r.kok}/${r.yol}`} className="kapak-ref" title={r.ad}>
            <img src={dosyaUrl(aktif, r.kok, r.yol)} alt={r.ad} />
            <figcaption><span className="rozet">{r.tur === "yuz" ? "yüz" : "stil"}</span>
              {r.silinir && <Dugme tur="ikon" onClick={() => refSil(r.ad)} title="Referansı kaldır" aria-label={`${r.ad} referansını kaldır`}><Trash2 size={12} /></Dugme>}
            </figcaption>
          </figure>
        ))}
        <DosyaSec kabul="image/png,image/jpeg,image/webp" sec={(f) => refYukle("yuz", f)}><ImagePlus size={14} /> Yüz fotoğrafı</DosyaSec>
        <DosyaSec kabul="image/png,image/jpeg,image/webp" sec={(f) => refYukle("stil", f)}><ImagePlus size={14} /> Stil referansı</DosyaSec>
      </div>
    </div>
  );
};
