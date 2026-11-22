// 5. adım: master thumbnail prompt'u ve dış görsel. Her platform için yazılı ve boş zemin sürümü kopyalanır (GET /master, agy'siz);
// başka platformda üretilen görsel geri yüklenir: yazısızsa zemin olur ve yazı kodla eklenir, yazılıysa bitmiş aday olur.
// WHY: bkz. wiki/decisions/0052-kapak-is-akisi-v2.md
import { Copy, Download, FileDown, Upload } from "lucide-react";
import React, { useEffect, useRef, useState } from "react";
import { istek, sor, yukle } from "../../api";
import { useDepo } from "../../depo";
import { Dugme } from "../../ortak";
import type { Durum, Master } from "./tipler";
import { dosyaUrl } from "./yardimci";

const ROL_ADI: Record<string, string> = { kare: "video karesi", yuz: "yüz", stil: "stil" };

export const MasterPrompt: React.FC<{
  d: Durum; platform: string; n: number | null; video: string | null; seciliKare: number | null; calisiyor: boolean; bekle: () => void;
}> = ({ d, platform, n, video, seciliKare, calisiyor, bekle }) => {
  const aktif = useDepo((s) => s.aktif)!;
  const { isBaslat, hata, bildir } = useDepo();
  const [m, setM] = useState<Master | null>(null);
  const [neden, setNeden] = useState("");
  const [hedef, setHedef] = useState(d.hedefler[0]?.id ?? "nano-banana-pro");
  const [yazili, setYazili] = useState(true);
  const [disYazili, setDisYazili] = useState(false);
  const [yuzde, setYuzde] = useState<number | null>(null);
  const alan = useRef<HTMLTextAreaElement>(null);
  const kaynakImza = JSON.stringify([n, d.oneri?.briefler, d.adaylar.find((a) => a.n === n)?.v]);

  useEffect(() => {
    let gecerli = true;
    istek(`/api/kapak/${aktif.studyo}/${aktif.ad}/master?${sor({ platform, n: n ?? undefined, kare: seciliKare ?? undefined, video: video ?? undefined })}`)
      .then((r) => { if (gecerli) { setM(r); setNeden(""); } })
      .catch((e) => { if (gecerli) { setM(null); setNeden(e instanceof Error ? e.message : String(e)); } });
    return () => { gecerli = false; };
  }, [aktif.studyo, aktif.ad, platform, seciliKare, video, kaynakImza]);

  const h = m?.hedefler[hedef]?.[yazili ? "yazili" : "bos"];
  const kopyala = async () => {
    if (!h) return;
    try {
      await navigator.clipboard.writeText(h.prompt);
      bildir(`${h.ad} prompt'u kopyalandı`);
    } catch {
      alan.current?.select(); // pano izni yoksa metin seçili kalır, Ctrl+C ile alınır
      bildir("Pano erişimi yok: metin seçildi, Ctrl+C ile kopyala", true);
    }
  };
  const mdIndir = () => {
    if (!m) return;
    const url = URL.createObjectURL(new Blob([m.md], { type: "text/markdown;charset=utf-8" }));
    const a = Object.assign(document.createElement("a"), { href: url, download: `kapak-${platform}-master-prompt.md` });
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  };
  const iceAl = async (dosyalar: File[]) => {
    const f = dosyalar[0];
    if (!f) return;
    try {
      setYuzde(0);
      await yukle(`/api/kapak/${aktif.studyo}/${aktif.ad}/ice-al?${sor({ platform, dosya: f.name })}`, f, (o) => setYuzde(Math.round(o * 100)));
      bekle();
      await isBaslat("kapak", { platform, ice_al: f.name, yazili: disYazili });
    } catch (e) { hata(e); } finally { setYuzde(null); }
  };
  const secici = useRef<HTMLInputElement>(null);

  return (
    <div className="kapak-adim-ic">
      {!m ? (
        <p className="ipucu" style={{ margin: 0 }}>{neden || "Master prompt hazırlanıyor…"}</p>
      ) : (
        <>
          <p className="ipucu" style={{ margin: 0 }}>
            Kaynak: {m.kaynak}{n === null && " (bir adayın kalemine basarsan o adaydan yazılır)"}. Yazılı sürüm kapağı yazıyla çizdirir;
            boş zemin sürümünü üretip aşağıdan içe alırsan yazı kodla eklenir ve Türkçe harf bozulmaz.
          </p>
          <div className="sekmeler" role="tablist" aria-label="Platform">
            {d.hedefler.map((x) => (
              <button key={x.id} role="tab" type="button" className="sekme" aria-selected={hedef === x.id} onClick={() => setHedef(x.id)}
                title={`${x.nerede} · yazı: ${x.yazi}`}>{x.ad}</button>
            ))}
          </div>
          <div className="arac" style={{ borderBottom: 0, padding: "4px 0", flexWrap: "wrap" }}>
            <div className="arac-grup" role="radiogroup" aria-label="Sürüm">
              <button type="button" role="radio" aria-checked={yazili} className={`dugme${yazili ? " birincil" : ""}`} onClick={() => setYazili(true)}>Yazılı</button>
              <button type="button" role="radio" aria-checked={!yazili} className={`dugme${!yazili ? " birincil" : ""}`} onClick={() => setYazili(false)}>Boş zemin</button>
            </div>
            <Dugme onClick={kopyala} disabled={!h}><Copy size={14} /> Kopyala</Dugme>
            <Dugme onClick={mdIndir} title="Bütün platformlar, iki sürüm, tek dosya"><FileDown size={14} /> Hepsini .md indir</Dugme>
            {h && <span className="ipucu">{h.nerede}</span>}
          </div>
          {h && (
            <>
              <textarea ref={alan} className="kapak-master" readOnly value={h.prompt} rows={Math.min(16, Math.max(5, Math.ceil(h.prompt.length / 110)))}
                aria-label={`${h.ad} prompt'u`} onFocus={(e) => e.currentTarget.select()} />
              <ul className="kapak-ayar">
                {h.ayar.map(([ad, deger]) => <li key={ad}><b>{ad}:</b> {deger}</li>)}
                {h.notlar.map((not) => <li key={not} className="ipucu">{not}</li>)}
              </ul>
            </>
          )}
          {!!m.ekler.length && (
            <>
              <div className="ipucu">Bu sırayla ekle (prompt'taki Image 1, 2, 3):</div>
              <div className="kapak-referanslar">
                {m.ekler.map((e) => (
                  <figure key={e.no} className="kapak-ref" title={e.dosya}>
                    {e.kok && e.yol && <img src={dosyaUrl(aktif, e.kok, e.yol)} alt={e.dosya} />}
                    <figcaption>
                      <span className="rozet vurgu">{e.no}</span> {ROL_ADI[e.rol] ?? e.rol}
                      {e.kok && e.yol && <a className="dugme ikon" href={dosyaUrl(aktif, e.kok, e.yol)} download={`${e.no}-${e.dosya}`} title="İndir" aria-label={`${e.dosya} indir`}><Download size={12} /></a>}
                    </figcaption>
                  </figure>
                ))}
              </div>
            </>
          )}
        </>
      )}
      <div className="kapak-ice-al">
        <strong>Dış görseli içe al</strong>
        <label className="ipucu"><input type="checkbox" checked={disYazili} onChange={(e) => setDisYazili(e.target.checked)} style={{ minHeight: 0 }} /> Görselde yazı var (yazı eklenmez)</label>
        <input ref={secici} type="file" hidden accept="image/png,image/jpeg,image/webp" onChange={(e) => { void iceAl([...(e.target.files ?? [])]); e.target.value = ""; }} />
        <Dugme onClick={() => secici.current?.click()} disabled={calisiyor || yuzde !== null}>
          <Upload size={14} /> {yuzde !== null ? `Yükleniyor %${yuzde}` : "Görsel seç"}
        </Dugme>
        <span className="ipucu">{d.w}×{d.h} oranına ortadan kırpılır; yazısızsa yazı öneriden ya da brief'ten eklenir.</span>
      </div>
    </div>
  );
};
