// WHY: bkz. wiki/decisions/0035-teslim-ayarlari.md. Seçenekler sunucudan gelir (teslim.py tabloları), burada kopyası tutulmaz.
import { CircleAlert, Download, Hammer, TriangleAlert } from "lucide-react";
import React, { useEffect, useRef, useState } from "react";
import { istek, sor } from "../api";
import { useDepo } from "../depo";
import { Bos, Dugme } from "../ortak";
import { useKurgu } from "../zaman/depo";

interface Secenekler {
  cozunurluk: { deger: number; ad: string; rehber_mbps: number }[];
  kalite: { deger: string; ad: string; crf: Record<string, number> }[];
  kodek: { deger: string; ad: string; rehber: number }[];
  fps: number[]; preset: string; ses_kbps: number;
}
interface Durum {
  secenekler: Secenekler; sekans: { w: number; h: number; fps: number } | null; kaynak_kisa: number | null; platform: string | null;
  son: { dosya: string; w: number; h: number; kodek: string; profil: string; fps: string; mbps: number; pix_fmt: string; renk: string; ses: string | null; mb: number } | null;
  hatalar: string[];
}
export interface Ayar { cozunurluk: number | null; kalite: string; kodek: string; fps: number | null; platform: string; ad: string; yenile: boolean }

const ILK: Ayar = { cozunurluk: null, kalite: "yayin", kodek: "h264", fps: null, platform: "", ad: "", yenile: false };
const cift = (x: number) => Math.round(x / 2) * 2;

/** Sekans yönünü koruyarak kısa kenarı hedefe getirir; teslim.hedef_boyut ile aynı kural. */
export const hedefBoyut = (w: number, h: number, kisa: number | null): [number, number] => {
  if (!kisa) return [w, h];
  const k = kisa / Math.min(w, h);
  return [cift(w * k), cift(h * k)];
};

/** Arayüz ayarı → iş isteği alanları. Varsayılanlar gönderilmez: sunucu ve CLI kendi varsayılanını kullanır. */
export const isAlanlari = (a: Ayar) => ({
  cozunurluk: a.cozunurluk ?? undefined, kalite: a.kalite, kodek: a.kodek, fps: a.fps ?? undefined,
  platform: a.platform || undefined, cikti_adi: a.ad || undefined, yenile: a.yenile,
});

export const TeslimPaneli: React.FC = () => {
  const anahtar = useKurgu((d) => d.anahtar);
  const canliSekans = useKurgu((d) => d.kurgu?.sekans);
  const surum = useDepo((d) => d.surum);
  const etag = useKurgu((d) => d.etag); // her kurgu kaydında değişir
  const { isBaslat, bildir } = useDepo();
  // Bu projenin süren export'u: final ya da final'li ai-edit
  const suren = useDepo((d) => d.isler.some((x) => (x.komut === "final" || x.komut === "ai-edit") && (x.durum === "calisiyor" || x.durum === "sirada")));
  const [v, setV] = useState<Durum | null>(null);
  const [sorun, setSorun] = useState<string | null>(null);
  const [a, setA] = useState<Ayar>(ILK);
  const depoAnahtari = `studio.teslim.${anahtar}`;
  const oncekiSuren = useRef(false);

  const al = () => {
    if (!anahtar) return;
    istek(`/api/teslim/${anahtar}`).then((d) => { setV(d); setSorun(null); }).catch((e) => setSorun((e as Error).message || String(e)));
  };
  useEffect(() => {
    setV(null); setSorun(null);
    if (!anahtar) return;
    try { setA({ ...ILK, ...JSON.parse(localStorage.getItem(depoAnahtari) ?? "{}") }); } catch { setA(ILK); }
    al();
  }, [anahtar]);
  useEffect(() => { al(); }, [surum, etag]); // kurgu kaydı ya da yeni dosya: hatalar ve son export yenilensin, seçimler korunur
  useEffect(() => {
    if (oncekiSuren.current && !suren) { al(); bildir("Export bitti. Sonuç Çıktı ayarlarında, günlük İşler'de."); }
    oncekiSuren.current = suren;
  }, [suren]);

  const degis = (yama: Partial<Ayar>) => {
    const yeni = { ...a, ...yama };
    setA(yeni);
    try { localStorage.setItem(depoAnahtari, JSON.stringify(yeni)); } catch { /* özel pencere: yalnız hatırlanmaz */ }
  };

  if (!anahtar) return <div className="panel"><Bos baslik="Proje seçilmedi" /></div>;
  if (sorun && !v) return (
    <div className="panel" role="alert">
      <Bos baslik="Çıktı ayarları alınamadı" metin={`${sorun}. Stüdyo güncellendiyse pencereyi kapatıp yeniden aç: sunucu eski sürümle çalışıyor olabilir.`}>
        <Dugme onClick={al}>Yeniden dene</Dugme>
      </Bos>
    </div>
  );
  if (!v) return <div className="panel"><Bos baslik="Çıktı ayarları yükleniyor" /></div>;

  const s = v.secenekler;
  const sekans = canliSekans ?? v.sekans ?? { w: 1080, h: 1920, fps: 30 };
  const [w, h] = hedefBoyut(sekans.w, sekans.h, a.cozunurluk);
  const kisa = Math.min(w, h);
  const fps = a.fps ?? sekans.fps;
  const kodek = s.kodek.find((k) => k.deger === a.kodek) ?? s.kodek[0];
  const kalite = s.kalite.find((k) => k.deger === a.kalite) ?? s.kalite[0];
  const kademe = [...s.cozunurluk].reverse().find((c) => kisa >= c.deger);
  const rehber = kademe ? kademe.rehber_mbps * (fps > 40 ? 1.5 : 1) * kodek.rehber : null;
  const platform = a.platform || v.platform;
  const uyarilar = [
    v.kaynak_kisa && v.kaynak_kisa < kisa && `Klip görüntüsü %${Math.round((kisa / v.kaynak_kisa) * 100)} büyütülür (kaynak ${v.kaynak_kisa}p). Yazı, grafik ve altyazı gerçek ${kisa}p çizilir.`,
    platform === "reels" && (w !== 1080 || h !== 1920) && `Reels 1080x1920 bekler; Instagram ${w}x${h} yüklemeyi 1080p'ye indirir.`,
    a.kodek === "h265" && "H.265: Instagram ve eski oynatıcılarda uyum riski. YouTube kabul eder.",
    fps !== sekans.fps && !v.sekans && "Kare hızı yalnız kurgu.json projelerinde değişir; bu projede render durur.",
    fps > sekans.fps && `${fps} fps yalnız grafik ve hareketi akıcılaştırır; klipler ${sekans.fps} fps kalır. Render süresi yaklaşık ${Math.round(fps / sekans.fps)} kat.`,
  ].filter(Boolean) as string[];

  const engel = v.hatalar ?? [];
  const sonFps = v.son ? Number(v.son.fps) : 0;
  const sonKodek = v.son?.kodek === "hevc" ? "h265" : v.son?.kodek;
  const eslesir = !!v.son && v.son.w === w && v.son.h === h && sonKodek === a.kodek && Math.abs(sonFps - fps) < 0.5;
  const [studyo, projeAdi] = anahtar.split("/");

  const baslat = () => {
    const ek = isAlanlari(a);
    // WHY: bkz. wiki/decisions/0035-teslim-ayarlari.md. Export asla ajan çağırmaz; AI edit ayrı iştir (İşler > Diğer).
    isBaslat("final", ek);
    window.dispatchEvent(new CustomEvent("studio-panel", { detail: "isler" })); // ilerleme ve günlük görünsün
  };

  return (
    <div className="panel">
      <div className="icerik" style={{ padding: 10 }}>
        {!!engel.length && (
          <div role="alert" data-engel style={{ marginBottom: 10, padding: 8, borderRadius: 4, background: "var(--hata-zemin)", color: "var(--hata)", fontSize: 12 }}>
            <b style={{ display: "flex", gap: 6, alignItems: "center" }}><CircleAlert size={14} /> Kurgu render edilemez, export başlamaz</b>
            <ul style={{ margin: "6px 0 0", paddingLeft: 18 }}>{engel.map((e) => <li key={e}>{e}</li>)}</ul>
            <span style={{ color: "var(--y2)" }}>Kurgu alanında düzelt; kaydedince bu uyarı kendiliğinden kalkar.</span>
          </div>
        )}
        <div className="form" style={{ gridTemplateColumns: "1fr 1fr" }}>
          <label>Çözünürlük
            <select value={a.cozunurluk ?? ""} onChange={(e) => degis({ cozunurluk: e.target.value ? Number(e.target.value) : null })}>
              <option value="">Sekans ({sekans.w}x{sekans.h})</option>
              {s.cozunurluk.map((c) => { const [cw, ch] = hedefBoyut(sekans.w, sekans.h, c.deger); return <option key={c.deger} value={c.deger}>{c.ad} · {cw}x{ch}</option>; })}
            </select>
          </label>
          <label>Kare hızı
            <select value={a.fps ?? ""} onChange={(e) => degis({ fps: e.target.value ? Number(e.target.value) : null })}>
              <option value="">Sekans ({sekans.fps} fps)</option>
              {s.fps.map((f) => <option key={f} value={f}>{f} fps</option>)}
            </select>
          </label>
          <label>Kodek
            <select value={a.kodek} onChange={(e) => degis({ kodek: e.target.value })}>
              {s.kodek.map((k) => <option key={k.deger} value={k.deger}>{k.ad}</option>)}
            </select>
          </label>
          <label>Kalite
            <select value={a.kalite} onChange={(e) => degis({ kalite: e.target.value })}>
              {s.kalite.map((k) => <option key={k.deger} value={k.deger}>{k.ad} · CRF {k.crf[a.kodek]}</option>)}
            </select>
          </label>
          <label>Platform
            <select value={a.platform} onChange={(e) => degis({ platform: e.target.value })}>
              <option value="">Stüdyoya göre{v.platform ? ` (${v.platform})` : ""}</option><option value="reels">Reels</option><option value="youtube">YouTube</option><option value="ugc">UGC</option>
            </select>
          </label>
          <label>Teslim adı (boşsa proje adı)
            <input value={a.ad} pattern="[\w\-]{1,80}" onChange={(e) => degis({ ad: e.target.value })} />
          </label>
        </div>

        <dl className="tani" aria-label="Çıktı özeti">
          <dt>Çıktı</dt><dd data-ozet="boyut">{w}x{h} · {fps} fps{a.cozunurluk && kisa !== Math.min(sekans.w, sekans.h) ? ` · motor ölçeği ×${(kisa / Math.min(sekans.w, sekans.h)).toFixed(3)}` : ""}</dd>
          <dt>Video</dt><dd>{kodek.ad} · CRF {kalite.crf[a.kodek]} · preset {s.preset} · yuv420p 8 bit</dd>
          <dt>Renk</dt><dd>BT.709 · sınırlı aralık (tv) · SDR</dd>
          <dt>Ses</dt><dd>AAC-LC {s.ses_kbps} kbps · 48 kHz · stereo</dd>
          <dt>Kap</dt><dd>MP4 · faststart</dd>
          {rehber && <><dt>Rehber</dt><dd>en az {rehber.toFixed(1)} Mbps (YouTube SDR önerisi; sade grafikte altı normal)</dd></>}
        </dl>

        {uyarilar.map((u) => (
          <p key={u} className="ipucu" role="note" style={{ display: "flex", gap: 6, margin: "0 0 6px", color: "var(--uyari)" }}>
            <TriangleAlert size={13} style={{ flex: "none", marginTop: 2 }} /><span>{u}</span>
          </p>
        ))}

        <div className="form" style={{ marginTop: 10 }}>
          <label style={{ display: "flex", gap: 6, alignItems: "center" }}>
            <input type="checkbox" checked={a.yenile} style={{ minHeight: 0 }} onChange={(e) => degis({ yenile: e.target.checked })} />
            Görüntü değişmese de yeniden render et
          </label>
        </div>

        {v.son && (
          <>
            <h3 style={{ margin: "16px 0 6px", fontSize: 12, color: "var(--y2)" }}>Son export (ölçülen)</h3>
            <dl className="tani" aria-label="Son export">
              <dt>Dosya</dt><dd>{v.son.dosya} · {v.son.mb} MB</dd>
              <dt>Video</dt><dd>{v.son.w}x{v.son.h} · {v.son.kodek} {v.son.profil} · {v.son.fps} fps · {v.son.mbps} Mbps · {v.son.pix_fmt}</dd>
              <dt>Renk</dt><dd>{v.son.renk}</dd>
              {v.son.ses && <><dt>Ses</dt><dd>{v.son.ses}</dd></>}
            </dl>
            <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
              <a className="dugme birincil" data-indir download={v.son.dosya} href={`/api/indir/${studyo}/${projeAdi}?${sor({ yol: v.son.dosya })}`}><Download size={14} /> İndir</a>
              <span className="ipucu" data-eslesme={eslesir} style={{ color: eslesir ? "var(--iyi)" : "var(--uyari)" }}>
                {eslesir ? "Seçili ayarla üretildi." : "Seçili ayar farklı: EXPORT ile yeniden üret, sonra indir."}
              </span>
            </div>
          </>
        )}
      </div>
      <div className="alt" style={{ display: "flex", gap: 8, alignItems: "center" }}>
        <Dugme tur="birincil" disabled={!!engel.length || suren} onClick={baslat}><Hammer size={14} /> EXPORT</Dugme>
        {suren
          ? <span className="ipucu" role="status">Export sürüyor. <button type="button" className="baglanti" onClick={() => window.dispatchEvent(new CustomEvent("studio-panel", { detail: "isler" }))}>İlerlemeyi gör</button></span>
          : <span className="ipucu">Yapay zekâ kullanılmaz: kurgu olduğu gibi, seçili ayarla render edilir. Bitince buradan indirilir.</span>}
      </div>
    </div>
  );
};
