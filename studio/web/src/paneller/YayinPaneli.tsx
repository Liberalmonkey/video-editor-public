// WHY: bkz. wiki/decisions/0055-teslimde-yayin-metni.md. Teslim edilen her video için platforma göre başlık, açıklama ve
// hashtag. Üretim düğmeyle iş kuyruğunda (`vedit yayin`); sınırlar sunucudaki reçeteden gelir, burada kopyası tutulmaz.
import { Copy, FileText, Save, Sparkles } from "lucide-react";
import React, { useEffect, useRef, useState } from "react";
import { istek } from "../api";
import { useDepo, varsayilanModel, type MotorDurum } from "../depo";
import { Bos, Dugme } from "../ortak";
import { useKurgu } from "../zaman/depo";
import { ModelSecici, MotorSec, SeviyeSec, modelAdi, motorSebebi } from "./ai/MotorModel";

export interface Bolum { t: string; baslik: string }
export interface Paket { baslik: string; aciklama: string; hashtagler: string[]; etiketler: string[]; bolumler: Bolum[]; notlar: string }
interface Recete {
  ad: string; arastirildi: boolean; baslik_ad: string; baslik_max: number; baslik_oneri: number; aciklama_max: number;
  hashtag_min: number; hashtag_max: number; etiket_max: number; bolumler: boolean;
}
interface Uretim { motor?: string; model?: string | null; seviye?: string | null; zaman?: string; duzenlendi?: string }
interface Video { ad: string; stem: string; sure: number | null; srt: boolean; eski: boolean; paket: { platformlar: Record<string, Paket>; _uretim?: Uretim } | null }
interface Durum { platformlar: Record<string, Recete>; varsayilan: string[]; varsayilan_motor: string; varsayilan_model: string; dil: string; videolar: Video[] }
interface Secim { motor: string; model: string; seviye: string | null; platformlar: string[] | null; dil: string }

const DEPO = "studio.yayin.motor";

/** Platforma yapıştırılacak metin: açıklama, bölümler, hashtag satırı. Sunucudaki yayin.kopya_metni ile aynı biçim. */
export const kopyaMetni = (p: Pick<Paket, "aciklama" | "bolumler" | "hashtagler">) =>
  [p.aciklama.trim(), (p.bolumler ?? []).map((b) => `${b.t} ${b.baslik}`).join("\n"), (p.hashtagler ?? []).join(" ")].filter(Boolean).join("\n\n");

/** YouTube etiket sayımı: virgüller sayılır, boşluklu etiket tırnakla (+2). */
export const etiketUzunlugu = (e: string[]) => e.reduce((n, x) => n + x.length + (x.includes(" ") ? 2 : 0), 0) + Math.max(0, e.length - 1);

/** Sayaç rengi: sert sınırı aşan hata, önerilen görünür uzunluğu aşan uyarı. */
export const sayacDurumu = (n: number, max: number, oneri?: number): "iyi" | "uyari" | "hata" =>
  n > max ? "hata" : oneri && n > oneri ? "uyari" : "iyi";

export const hashtagAyir = (s: string) => s.split(/[\s,]+/).map((x) => x.trim()).filter(Boolean).map((x) => `#${x.replace(/^#+/, "")}`);
export const bolumAyir = (s: string): Bolum[] =>
  s.split("\n").map((x) => x.trim().match(/^(\d{1,2}:\d{2}(?::\d{2})?)\s+(.+)$/)).filter(Boolean).map((m) => ({ t: m![1], baslik: m![2].trim() }));

const sureYaz = (sn: number | null) => (sn == null ? "?" : `${Math.floor(sn / 60)}:${String(Math.round(sn % 60)).padStart(2, "0")}`);

const Sayac: React.FC<{ n: number; max: number; oneri?: number; birim?: string }> = ({ n, max, oneri, birim = "" }) => (
  <span className={`rozet ${sayacDurumu(n, max, oneri)}`} title={oneri ? `Görünen yaklaşık ${oneri}, sınır ${max}` : `Sınır ${max}`}>{n}/{max}{birim}</span>
);

export const YayinPaneli: React.FC = () => {
  const anahtar = useKurgu((d) => d.anahtar);
  const surum = useDepo((d) => d.surum);
  const { ajanDurum, ajanDurumAl, isBaslat, bildir, hata } = useDepo();
  const suren = useDepo((d) => d.isler.some((x) => x.komut === "yayin" && (x.durum === "calisiyor" || x.durum === "sirada")));
  const [v, setV] = useState<Durum | null>(null);
  const [sorun, setSorun] = useState<string | null>(null);
  const [s, setS] = useState<Secim>(() => {
    try { const d = JSON.parse(localStorage.getItem(DEPO) ?? ""); if (d?.motor) return { platformlar: null, dil: "", seviye: null, ...d }; } catch { /* yok */ }
    return { motor: "claude", model: "claude-opus-5-5", seviye: null, platformlar: null, dil: "" };
  });
  const [acik, setAcik] = useState<string | null>(null);
  const [sekme, setSekme] = useState<string | null>(null);
  const [taslak, setTaslak] = useState<Record<string, Paket> | null>(null);
  const [kaydediliyor, setKaydediliyor] = useState(false);
  const oncekiSuren = useRef(false);

  const al = () => {
    if (!anahtar) return;
    istek(`/api/yayin/${anahtar}`).then((d: Durum) => { setV(d); setSorun(null); }).catch((e) => setSorun((e as Error).message || String(e)));
  };
  useEffect(() => { setV(null); setAcik(null); setTaslak(null); al(); }, [anahtar]);
  useEffect(() => { al(); }, [surum]);
  useEffect(() => { if (!ajanDurum) ajanDurumAl(); }, []);
  useEffect(() => {
    if (oncekiSuren.current && !suren) { al(); setTaslak(null); bildir("Yayın metni hazır. Sonuç Yayın metni panelinde, ayrıca yayin.md'de."); }
    oncekiSuren.current = suren;
  }, [suren]);

  const sec = (yama: Partial<Secim>) => {
    const yeni = { ...s, ...yama };
    if (yama.motor && yama.motor !== s.motor) {
      const m = ajanDurum?.[yama.motor];
      yeni.model = yama.motor === "claude" ? "claude-opus-5-5" : m ? varsayilanModel(m) : "";
      if (!m?.seviyeler?.includes(yeni.seviye ?? "")) yeni.seviye = null;
    }
    setS(yeni);
    try { localStorage.setItem(DEPO, JSON.stringify(yeni)); } catch { /* özel pencere */ }
  };

  if (!anahtar) return <div className="panel"><Bos baslik="Proje seçilmedi" /></div>;
  if (sorun && !v) return (
    <div className="panel" role="alert">
      <Bos baslik="Yayın metni alınamadı" metin={`${sorun}. Stüdyo güncellendiyse pencereyi kapatıp yeniden aç.`}><Dugme onClick={al}>Yeniden dene</Dugme></Bos>
    </div>
  );
  if (!v) return <div className="panel"><Bos baslik="Yayın metni yükleniyor" /></div>;

  const motor: MotorDurum | undefined = ajanDurum?.[s.motor];
  const sebep = motorSebebi(motor);
  const platformlar = s.platformlar ?? v.varsayilan;
  const hazir = !sebep && platformlar.length > 0 && !suren;
  const ek = (video: Record<string, unknown>) => ({
    ...video, motor: s.motor, model: s.model || undefined, seviye: s.seviye || undefined, platformlar, dil: s.dil || undefined,
  });
  const uret = (video: Record<string, unknown>) => {
    isBaslat("yayin", ek(video));
    window.dispatchEvent(new CustomEvent("studio-panel", { detail: "isler" }));
  };

  const video = v.videolar.find((x) => x.stem === acik) ?? null;
  const paketler = taslak ?? video?.paket?.platformlar ?? null;
  const aktifSekme = paketler && sekme && paketler[sekme] ? sekme : paketler ? Object.keys(paketler)[0] : null;
  const pk = aktifSekme && paketler ? paketler[aktifSekme] : null;
  const r = aktifSekme ? v.platformlar[aktifSekme] : null;
  const degis = (yama: Partial<Paket>) => {
    if (!paketler || !aktifSekme) return;
    setTaslak({ ...paketler, [aktifSekme]: { ...paketler[aktifSekme], ...yama } });
  };
  const kopyala = async (metin: string, ne: string) => {
    try { await navigator.clipboard.writeText(metin); bildir(`${ne} kopyalandı.`); } catch { bildir("Pano erişimi yok: metni seçip kopyala.", true); }
  };
  const kaydet = async () => {
    if (!video || !taslak) return;
    setKaydediliyor(true);
    try {
      const d = await istek(`/api/yayin/${anahtar}/${encodeURIComponent(video.ad)}`, { method: "PUT", json: { platformlar: taslak } });
      setTaslak(null); al();
      bildir(d.uyarilar?.length ? `Kaydedildi. Uyarı: ${d.uyarilar.join("; ")}` : "Kaydedildi; yayin.md güncellendi.");
    } catch (e) { hata(e); } finally { setKaydediliyor(false); }
  };

  return (
    <div className="panel">
      <div className="icerik" style={{ padding: 10 }}>
        <div className="form" style={{ gridTemplateColumns: "1fr 1fr" }}>
          <label>Motor<MotorSec deger={s.motor} sec={(m) => sec({ motor: m })} durum={ajanDurum} etiket="Yayın metni motoru" /></label>
          <label>Model<ModelSecici motor={motor} secili={s.model} sec={(m) => sec({ model: m })} etiket="Yayın metni modeli" /></label>
          <label>Akıl yürütme<SeviyeSec m={motor} deger={s.seviye} sec={(x) => sec({ seviye: x })} etiket="Yayın metni seviyesi" /></label>
          <label>Dil
            <select value={s.dil} onChange={(e) => sec({ dil: e.target.value })}>
              <option value="">Videonun dili ({v.dil})</option><option value="tr">Türkçe</option><option value="en">English</option>
            </select>
          </label>
        </div>
        {sebep && <p className="ipucu" role="note" style={{ color: "var(--uyari)" }}>{motor?.ad ?? s.motor}: {sebep}</p>}

        <fieldset style={{ border: 0, padding: 0, margin: "10px 0" }}>
          <legend className="ipucu">Platformlar (stüdyo varsayılanı: {v.varsayilan.map((k) => v.platformlar[k]?.ad ?? k).join(", ")})</legend>
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
            {Object.entries(v.platformlar).map(([k, p]) => (
              <label key={k} style={{ display: "flex", gap: 4, alignItems: "center" }}>
                <input type="checkbox" style={{ minHeight: 0 }} checked={platformlar.includes(k)}
                  onChange={(e) => sec({ platformlar: e.target.checked ? [...platformlar, k] : platformlar.filter((x) => x !== k) })} />
                {p.ad}{!p.arastirildi && <span className="rozet uyari" title="Bu platformun kuralları araştırılmadı; metin genel kurallarla yazılır">genel kurallar</span>}
              </label>
            ))}
          </div>
        </fieldset>

        {!v.videolar.length && <Bos baslik="Teslim videosu yok" metin="Önce Çıktı ayarlarından EXPORT al; her teslim videosu burada listelenir." />}
        <ul className="liste" aria-label="Teslim videoları" style={{ listStyle: "none", margin: 0, padding: 0 }}>
          {v.videolar.map((x) => (
            <li key={x.stem} style={{ display: "flex", gap: 6, alignItems: "center", padding: "4px 0", borderBottom: "1px solid var(--z3)" }}>
              <button type="button" className="baglanti" aria-expanded={acik === x.stem} style={{ flex: 1, textAlign: "left", minWidth: 0 }}
                onClick={() => { setAcik(acik === x.stem ? null : x.stem); setTaslak(null); setSekme(null); }}>
                <FileText size={13} /> {x.ad} <span className="ipucu">· {sureYaz(x.sure)}</span>
              </button>
              {!x.srt && <span className="rozet" title="Yanında .srt yok; digest ya da senaryo kullanılır">SRT yok</span>}
              <span className={`rozet ${x.paket ? (x.eski ? "uyari" : "iyi") : ""}`}>{x.paket ? (x.eski ? "eski" : "hazır") : "yok"}</span>
              <Dugme disabled={!hazir} onClick={() => uret({ video: x.ad })} title={sebep || "Bu video için yayın metni üret"}><Sparkles size={13} /> Üret</Dugme>
            </li>
          ))}
        </ul>

        {video && !paketler && <p className="ipucu" style={{ marginTop: 10 }}>{video.ad} için henüz yayın metni yok. Üret'e bas.</p>}
        {video && paketler && aktifSekme && pk && r && (
          <section aria-label={`${video.ad} yayın metni`} style={{ marginTop: 12 }}>
            <div className="sekmeler" role="tablist">
              {Object.keys(paketler).map((k) => (
                <button key={k} type="button" role="tab" className="sekme" aria-selected={k === aktifSekme} onClick={() => setSekme(k)}>{v.platformlar[k]?.ad ?? k}</button>
              ))}
            </div>
            <div className="form" style={{ marginTop: 8 }}>
              <label>
                <span style={{ display: "flex", gap: 6, alignItems: "center" }}>{r.baslik_ad} <Sayac n={pk.baslik.length} max={r.baslik_max} oneri={r.baslik_oneri} />
                  <Dugme tur="ikon" aria-label={`${r.baslik_ad} kopyala`} onClick={() => kopyala(pk.baslik, r.baslik_ad)}><Copy size={12} /></Dugme></span>
                <input value={pk.baslik} onChange={(e) => degis({ baslik: e.target.value })} />
              </label>
              <label>
                <span style={{ display: "flex", gap: 6, alignItems: "center" }}>Açıklama <Sayac n={kopyaMetni(pk).length} max={r.aciklama_max} /></span>
                <textarea rows={8} value={pk.aciklama} onChange={(e) => degis({ aciklama: e.target.value })} />
              </label>
              <label>
                <span style={{ display: "flex", gap: 6, alignItems: "center" }}>Hashtag
                  <span className={`rozet ${pk.hashtagler.length < r.hashtag_min || pk.hashtagler.length > r.hashtag_max ? "hata" : "iyi"}`}>{pk.hashtagler.length} · {r.hashtag_min}-{r.hashtag_max}</span></span>
                <input value={pk.hashtagler.join(" ")} onChange={(e) => degis({ hashtagler: hashtagAyir(e.target.value) })} />
              </label>
              {r.etiket_max > 0 && (
                <label>
                  <span style={{ display: "flex", gap: 6, alignItems: "center" }}>Etiketler (virgülle) <Sayac n={etiketUzunlugu(pk.etiketler)} max={r.etiket_max} />
                    <Dugme tur="ikon" aria-label="Etiketleri kopyala" onClick={() => kopyala(pk.etiketler.join(", "), "Etiketler")}><Copy size={12} /></Dugme></span>
                  <input value={pk.etiketler.join(", ")} onChange={(e) => degis({ etiketler: e.target.value.split(",").map((x) => x.trim()).filter(Boolean) })} />
                </label>
              )}
              {r.bolumler && (
                <label>Bölümler (satır başına "0:00 Başlık")
                  <textarea rows={4} defaultValue={pk.bolumler.map((b) => `${b.t} ${b.baslik}`).join("\n")} key={`${video.stem}-${aktifSekme}-${video.paket?._uretim?.zaman}`}
                    onBlur={(e) => degis({ bolumler: bolumAyir(e.target.value) })} />
                </label>
              )}
            </div>
            {pk.notlar && <p className="ipucu" role="note" style={{ color: "var(--uyari)" }}>Not: {pk.notlar}</p>}
            <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap", marginTop: 8 }}>
              <Dugme tur="birincil" onClick={() => kopyala(kopyaMetni(pk), "Açıklama ve hashtag")}><Copy size={13} /> Tümünü kopyala</Dugme>
              <Dugme disabled={!taslak || kaydediliyor} onClick={kaydet}><Save size={13} /> Kaydet</Dugme>
              {taslak && <Dugme onClick={() => setTaslak(null)}>Vazgeç</Dugme>}
              {video.paket?._uretim && (
                <span className="ipucu">{video.paket._uretim.motor} · {video.paket._uretim.model ?? "varsayılan"}{video.paket._uretim.duzenlendi ? " · elle düzenlendi" : ""}</span>
              )}
            </div>
          </section>
        )}
      </div>
      <div className="alt" style={{ display: "flex", gap: 8, alignItems: "center" }}>
        <Dugme tur="birincil" disabled={!hazir || !v.videolar.length} onClick={() => uret({ hepsi: true })}><Sparkles size={14} /> Hepsini üret</Dugme>
        {suren
          ? <span className="ipucu" role="status">Yayın metni yazılıyor. <button type="button" className="baglanti" onClick={() => window.dispatchEvent(new CustomEvent("studio-panel", { detail: "isler" }))}>İlerlemeyi gör</button></span>
          : <span className="ipucu">{motor?.ad ?? s.motor} · {s.model ? modelAdi(motor, s.model) : "varsayılan"} ile her video için platforma göre başlık, açıklama ve hashtag yazar.</span>}
      </div>
    </div>
  );
};
