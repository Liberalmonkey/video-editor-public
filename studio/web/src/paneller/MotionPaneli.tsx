// WHY: bkz. wiki/decisions/0036-motion-kutuphanesi-ve-ajanlar.md. Motion kütüphanesi: poster ızgarası, tür süzgeci, tema, şablon parametreleri.
import { Lock, Plus, Trash2, Upload } from "lucide-react";
import React, { useMemo, useState } from "react";
import { istek } from "../api";
import { useDepo } from "../depo";
import { Bos, DosyaSec, Dugme } from "../ortak";
import { useKurgu, type KaynakOge } from "../zaman/depo";
import * as K from "../zaman/komutlar";
import { SURUKLE_TUR } from "../zaman/Timeline";

const TURLER: [string, string][] = [["", "Tümü"], ["sablon", "Şablon"], ["overlay", "İşaret"], ["icon", "İkon"], ["transition", "Geçiş"],
  ["lower-third", "Alt bant"], ["background", "Zemin"], ["broll", "Ara görüntü"], ["dis", "Dış varlık"], ["arsiv", "Arşiv"]];
const YONTEM_AD: Record<string, string> = { alfa: "Alfa", yesil: "Yeşil perde", siyah: "Siyah (screen)", lottie: "Lottie", gif: "GIF", svg: "SVG" };

export interface MotionKayit {
  id: string; title: string; kind: string; file: string; url: string; poster_url?: string; tags?: string[]; ne_zaman?: string;
  duration_s?: number; width?: number; height?: number; kilitli?: boolean; license?: string;
  // ADR 0046: içe aktarılmış dış varlık
  arsiv?: string; dis?: boolean; site?: string; alfa_yontemi?: "alfa" | "yesil" | "siyah" | "lottie" | "gif" | "svg"; atif_gerekli?: boolean; kisitlar?: string[]; source_url?: string;
  param?: Record<string, { vars: string | number; min?: number; max?: number; secenek?: string[] }>;
}

// Saf süzgeç: test edilir (MotionPaneli.test.ts).
export const suz = (kayitlar: MotionKayit[], tur: string, ara: string, kaynak = "", yontem = "") => {
  const kelimeler = ara.toLocaleLowerCase("tr").split(/\s+/).filter(Boolean);
  return kayitlar.filter((e) => {
    // ADR 0045: native karşılığı olan eski kayıt yalnız Arşiv sekmesinde görünür.
    if (tur === "arsiv" ? !e.arsiv : !!e.arsiv) return false;
    if (tur === "arsiv") { /* arşivde tür süzgeci yok */ } else if (tur === "sablon" ? !e.param : tur === "dis" ? !e.dis : tur ? e.kind !== tur || !!e.param : false) return false;
    if (kaynak && e.site !== kaynak) return false;
    if (yontem && e.alfa_yontemi !== yontem) return false;
    const metin = [e.id, e.title, e.kind, e.ne_zaman, e.site, e.license, ...(e.tags ?? [])].filter(Boolean).join(" ").toLocaleLowerCase("tr");
    return kelimeler.every((k) => metin.includes(k));
  });
};

const kaynak = (e: MotionKayit): KaynakOge => ({ yol: `library:${e.file.replace(/^library\//, "")}`, ad: e.title, tur: e.alfa_yontemi === "svg" ? "gorsel" : "motion" });
const kendiKanal = (e: MotionKayit) => (e.kisitlar ?? []).includes("yalniz-kendi-kanalin");

const Kart: React.FC<{ e: MotionKayit; secili: boolean; sec: () => void }> = ({ e, secili, sec }) => {
  const [oynat, setOynat] = useState(false);
  return (
    <button type="button" className={`motion-kart ${secili ? "secili" : ""}`} title={e.ne_zaman || e.title} onClick={sec}
      onMouseEnter={() => setOynat(true)} onMouseLeave={() => setOynat(false)} onFocus={() => setOynat(true)} onBlur={() => setOynat(false)}
      draggable={!e.param && e.alfa_yontemi !== "lottie"} onDragStart={(k) => { k.dataTransfer.setData(SURUKLE_TUR, JSON.stringify(kaynak(e))); k.dataTransfer.effectAllowed = "copy"; }}>
      <span className="motion-kare">
        {/* Poster altta kalır, video üstüne biner: öğe değişimi tıklamayı yutmasın, video yüklenene dek kare boş kalmasın. */}
        {e.poster_url && <img src={e.poster_url} alt="" loading="lazy" />}
        {oynat && <video src={e.url} autoPlay loop muted playsInline />}
        {e.param && <span className="rozet vurgu">şablon</span>}
        {e.arsiv && <span className="rozet" title={`Yerine: ${e.arsiv}`}>arşiv</span>}
        {e.kilitli && <Lock size={12} aria-label="Kilitli" />}
        {e.atif_gerekli && <span className="rozet uyari" title="Kullanılırsa yayin.md'ye atıf satırı yazılır">atıf gerekli</span>}
        {kendiKanal(e) && <span className="rozet hata" title="Yalnız kendi kanalların; ücretli reklam ve müşteri işi yok">yalnız kendi kanalın</span>}
      </span>
      <span className="motion-ad">{e.title.split(":")[0]}</span>
    </button>
  );
};

export const MotionPaneli: React.FC<{ kayitlar: MotionKayit[]; temalar: string[]; tazele: () => void; sil: (e: MotionKayit) => void; yukle: (d: File[]) => void }> = ({ kayitlar, temalar, sil, yukle }) => {
  const { bildir, hata, aktif } = useDepo();
  const [tur, setTur] = useState("");
  const [ara, setAra] = useState("");
  const [seciliId, setSeciliId] = useState<string | null>(null);
  const [param, setParam] = useState<Record<string, string | number>>({});
  const [tema, setTema] = useState("");
  const [is, setIs] = useState(false);
  const [kaynakSuz, setKaynakSuz] = useState("");
  const [yontemSuz, setYontemSuz] = useState("");
  const liste = useMemo(() => suz(kayitlar, tur, ara, kaynakSuz, yontemSuz), [kayitlar, tur, ara, kaynakSuz, yontemSuz]);
  const siteler = useMemo(() => [...new Set(kayitlar.filter((e) => e.dis).map((e) => e.site).filter(Boolean))].sort() as string[], [kayitlar]);
  const secili = kayitlar.find((e) => e.id === seciliId) ?? null;

  const sec = (e: MotionKayit) => {
    setSeciliId(e.id);
    setParam(Object.fromEntries(Object.entries(e.param ?? {}).map(([a, t]) => [a, t.vars])));
  };

  const ekle = async () => {
    const k = useKurgu.getState();
    if (!secili || !k.kurgu) { bildir("Önce kurgusu olan bir proje aç", true); return; }
    if (secili.alfa_yontemi === "lottie") {
      // ADR 0046: Lottie native bileşenle çizilir; renkler stile eşlenir.
      const sure = Math.min(6, Math.max(0.8, secili.duration_s ?? 1.5));
      k.duzenle("Lottie ekle", (f) => { K.bilesenEkle(f, k.zaman, { ad: "dis/lottie", param: { dosya: `library:${secili.file.replace(/^library\//, "")}`, renk: "tema" } }, sure); });
      return;
    }
    if (!secili.param) { await k.kaynaktanEkle(kaynak(secili), k.zaman, null, false); return; }
    if (!aktif) return;
    setIs(true);
    try {
      const kurguTema = tema || k.kurgu.motion_tema || "varsayilan";
      const r = await istek(`/api/motion-sablon/${aktif.studyo}/${aktif.ad}`, { method: "POST",
        json: { ad: secili.id, param, tema: kurguTema, w: k.kurgu.sekans.w, h: k.kurgu.sekans.h } });
      await k.kaynaktanEkle({ yol: r.yol, ad: secili.title.split(":")[0], tur: "motion" }, k.zaman, null, false);
      // Niyet klipte kalır: parametre değişince vedit webm'i yeniden üretir (kurgu.motion_bagla).
      const d = useKurgu.getState();
      const id = d.secim[0];
      if (id) d.duzenle("Şablon bilgisi", (f) => { const c = f.klipler.find((x) => x.id === id); if (c) c.sablon = { ad: secili.id, param, ...(tema ? { tema } : {}) }; });
    } catch (e) { hata(e); } finally { setIs(false); }
  };

  return (
    <>
      <div className="arac">
        <input type="search" aria-label="Motion kütüphanesinde ara" placeholder="Ara: ok, geçiş, grafik" value={ara} onChange={(e) => setAra(e.target.value)} style={{ flex: 1, minWidth: 0 }} />
        <DosyaSec kabul=".mp4,.mov,.webm,.mkv,.json,.lottie,.gif,.apng,.png,.svg" sec={yukle}><Upload size={14} /> İçe aktar</DosyaSec>
      </div>
      {tur === "dis" && (
        <div className="arac">
          <select aria-label="Kaynak" value={kaynakSuz} onChange={(e) => setKaynakSuz(e.target.value)}><option value="">Tüm kaynaklar</option>{siteler.map((s) => <option key={s}>{s}</option>)}</select>
          <select aria-label="Alfa yöntemi" value={yontemSuz} onChange={(e) => setYontemSuz(e.target.value)}><option value="">Tüm yöntemler</option>{Object.entries(YONTEM_AD).map(([v, a]) => <option key={v} value={v}>{a}</option>)}</select>
        </div>
      )}
      <div className="motion-cipler" role="tablist" aria-label="Motion türü">
        {TURLER.map(([k, et]) => {
          const n = suz(kayitlar, k, "").length;
          return n || !k ? <button key={k} type="button" role="tab" className="sekme" aria-selected={tur === k} onClick={() => setTur(k)}>{et}<span className="sayi">{n}</span></button> : null;
        })}
      </div>
      <div className="icerik">
        {!kayitlar.length && <Bos baslik="Motion kütüphanesi boş" metin="Ekle ile dosya yükle. Lisans bilgisi zorunludur." />}
        {!!kayitlar.length && !liste.length && <Bos baslik="Eşleşen kayıt yok" metin="Aramayı ya da türü değiştir." />}
        <div className="motion-izgara">{liste.map((e) => <Kart key={e.id} e={e} secili={e.id === seciliId} sec={() => sec(e)} />)}</div>
      </div>
      {secili && (
        <div className="alt">
          <div style={{ fontWeight: 550, marginBottom: 2 }}>{secili.title}</div>
          {secili.ne_zaman && <p className="ipucu" style={{ margin: "0 0 8px" }}>{secili.ne_zaman}</p>}
          {secili.dis && <p className="ipucu" style={{ margin: "0 0 8px" }}>
            {secili.site} · {secili.license} · {YONTEM_AD[secili.alfa_yontemi ?? ""] ?? ""}{secili.kisitlar?.length ? ` · ${secili.kisitlar.join(", ")}` : ""}
            {secili.source_url && <> · <a href={secili.source_url} target="_blank" rel="noreferrer">kaynak</a></>}
          </p>}
          {secili.param && (
            <div className="form" style={{ marginBottom: 8 }}>
              {Object.entries(secili.param).map(([a, t]) => (
                <label key={a}>{a}
                  {t.secenek
                    ? <select value={String(param[a] ?? t.vars)} onChange={(e) => setParam({ ...param, [a]: e.target.value })}>{t.secenek.map((s) => <option key={s}>{s}</option>)}</select>
                    : typeof t.vars === "number"
                      ? <input type="number" min={t.min} max={t.max} value={param[a] ?? t.vars} onChange={(e) => setParam({ ...param, [a]: Number(e.target.value) })} />
                      : <input value={String(param[a] ?? "")} maxLength={t.max} onChange={(e) => setParam({ ...param, [a]: e.target.value })} />}
                </label>
              ))}
              <label>Tema
                <select value={tema} onChange={(e) => setTema(e.target.value)}>
                  <option value="">Proje teması</option>
                  {temalar.map((t) => <option key={t}>{t}</option>)}
                </select>
              </label>
            </div>
          )}
          <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
            <Dugme tur="birincil" disabled={is} onClick={ekle}><Plus size={14} /> {is ? "Hazırlanıyor" : "Oynatma kafasına ekle"}</Dugme>
            <span className="ipucu">{secili.duration_s} sn</span>
            <span style={{ flex: 1 }} />
            <Dugme tur="tehlike" disabled={secili.kilitli} title={secili.kilitli ? "Kilitli varlık silinemez (ADR 0012)" : "Kütüphaneden sil"} onClick={() => sil(secili)}>
              {secili.kilitli ? <Lock size={14} /> : <Trash2 size={14} />}
            </Dugme>
          </div>
        </div>
      )}
    </>
  );
};
