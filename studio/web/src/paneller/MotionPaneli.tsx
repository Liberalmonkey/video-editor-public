// WHY: bkz. wiki/decisions/0036-motion-kutuphanesi-ve-ajanlar.md. Motion kütüphanesi: poster ızgarası, tür süzgeci, tema, şablon parametreleri.
// ADR 0061: Kasam (kullanıcının kaydettikleri, varsayılan) · Keşif (hazır paket) · Arşiv (eski kayıtlar); toplu seçim ve silme.
import { CheckSquare, Lock, Plus, Trash2, Upload } from "lucide-react";
import React, { useMemo, useState } from "react";
import { istek } from "../api";
import { useDepo } from "../depo";
import { Bos, DosyaSec, Dugme } from "../ortak";
import { useKurgu, type KaynakOge } from "../zaman/depo";
import * as K from "../zaman/komutlar";
import { SURUKLE_TUR } from "../zaman/Timeline";

const TURLER: [string, string][] = [["kasa", "Kasam"], ["", "Keşif"], ["sablon", "Şablon"], ["overlay", "İşaret"], ["icon", "İkon"], ["transition", "Geçiş"],
  ["lower-third", "Alt bant"], ["background", "Zemin"], ["broll", "Ara görüntü"], ["dis", "Dış varlık"], ["arsiv", "Arşiv"]];
const YONTEM_AD: Record<string, string> = { alfa: "Alfa", yesil: "Yeşil perde", siyah: "Siyah (screen)", lottie: "Lottie", gif: "GIF", svg: "SVG" };

export interface MotionKayit {
  id: string; title: string; kind: string; file: string; url: string; poster_url?: string; tags?: string[]; ne_zaman?: string;
  duration_s?: number; width?: number; height?: number; kilitli?: boolean; license?: string;
  // ADR 0046: içe aktarılmış dış varlık
  arsiv?: string; eski?: boolean; onizleme_url?: string; dis?: boolean; site?: string; alfa_yontemi?: "alfa" | "yesil" | "siyah" | "lottie" | "gif" | "svg"; atif_gerekli?: boolean; kisitlar?: string[]; source_url?: string;
  param?: Record<string, { vars: string | number; min?: number; max?: number; secenek?: string[] }>;
}

/** Videodan kaydedilen kasa kaydı (ADR 0061). Niyet saklanır: şablon, kompozisyon ya da bileşen parametresiyle. */
export interface KasaKayit {
  id: string; title: string; tur: "motion" | "sablon" | "hf" | "bilesen" | "sfx" | "gorsel"; file?: string; url?: string;
  poster_url?: string; onizleme_url?: string; sure: number; license?: string; kaynak?: { proje: string; klip: string };
  sablon?: { ad: string; param?: Record<string, any>; tema?: string }; hf?: { ad: string; param?: Record<string, any>; tema?: string };
  bilesen?: { ad: string; param?: Record<string, any> };
}
const KASA_TUR: Record<KasaKayit["tur"], string> = { motion: "motion", sablon: "şablon", hf: "kompozisyon", bilesen: "bileşen", sfx: "ses efekti", gorsel: "görsel" };

// Saf süzgeç: test edilir (MotionPaneli.test.ts).
export const suz = (kayitlar: MotionKayit[], tur: string, ara: string, kaynak = "", yontem = "") => {
  const kelimeler = ara.toLocaleLowerCase("tr").split(/\s+/).filter(Boolean);
  return kayitlar.filter((e) => {
    // ADR 0045: native karşılığı olan eski kayıt yalnız Arşiv sekmesinde görünür. ADR 0061: eski custom kayıtlar da.
    const arsivde = !!e.arsiv || !!e.eski;
    if (tur === "arsiv" ? !arsivde : arsivde) return false;
    if (tur === "arsiv") { /* arşivde tür süzgeci yok */ } else if (tur === "sablon" ? !e.param : tur === "dis" ? !e.dis : tur ? e.kind !== tur || !!e.param : false) return false;
    if (kaynak && e.site !== kaynak) return false;
    if (yontem && e.alfa_yontemi !== yontem) return false;
    const metin = [e.id, e.title, e.kind, e.ne_zaman, e.site, e.license, ...(e.tags ?? [])].filter(Boolean).join(" ").toLocaleLowerCase("tr");
    return kelimeler.every((k) => metin.includes(k));
  });
};

const kaynak = (e: MotionKayit): KaynakOge => ({ yol: `library:${e.file.replace(/^library\//, "")}`, ad: e.title, tur: e.alfa_yontemi === "svg" ? "gorsel" : "motion" });
const kendiKanal = (e: MotionKayit) => (e.kisitlar ?? []).includes("yalniz-kendi-kanalin");

const Kart: React.FC<{ e: MotionKayit; secili: boolean; sec: () => void; isaretli?: boolean }> = ({ e, secili, sec, isaretli }) => {
  const [oynat, setOynat] = useState(false);
  return (
    <button type="button" className={`motion-kart ${secili || isaretli ? "secili" : ""}`} aria-pressed={isaretli} title={e.ne_zaman || e.title} onClick={sec}
      onMouseEnter={() => setOynat(true)} onMouseLeave={() => setOynat(false)} onFocus={() => setOynat(true)} onBlur={() => setOynat(false)}
      draggable={!e.param && e.alfa_yontemi !== "lottie"} onDragStart={(k) => { k.dataTransfer.setData(SURUKLE_TUR, JSON.stringify(kaynak(e))); k.dataTransfer.effectAllowed = "copy"; }}>
      <span className="motion-kare">
        {/* Poster altta kalır, video üstüne biner: öğe değişimi tıklamayı yutmasın, video yüklenene dek kare boş kalmasın. */}
        {e.poster_url && <img src={e.poster_url} alt="" loading="lazy" />}
        {oynat && <video src={e.onizleme_url ?? e.url} autoPlay loop muted playsInline />}
        {isaretli && <CheckSquare size={14} aria-label="Seçili" style={{ position: "absolute", right: 4, bottom: 4, color: "var(--vurgu)" }} />}
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

/** Kasa kaydı ızgarada motion kartıyla aynı görünür; dosyasız bileşen yalnız poster gösterir. */
const kasaKarti = (e: KasaKayit): MotionKayit => ({ id: e.id, title: e.title, kind: KASA_TUR[e.tur], file: e.file ?? "", url: e.url ?? "",
  poster_url: e.poster_url, onizleme_url: e.onizleme_url, duration_s: e.sure, license: e.license, ne_zaman: e.kaynak ? `Kaynak: ${e.kaynak.proje}` : undefined });

export const MotionPaneli: React.FC<{
  kayitlar: MotionKayit[]; kasa?: KasaKayit[]; temalar: string[]; tazele: () => void; sil: (e: MotionKayit, tur?: "motion" | "kasa") => void;
  topluSil?: (tur: "motion" | "kasa", idler: string[]) => void; yukle: (d: File[]) => void;
}> = ({ kayitlar, kasa = [], temalar, sil, topluSil, yukle }) => {
  const { bildir, hata, aktif } = useDepo();
  const [tur, setTur] = useState("kasa");
  const [toplu, setToplu] = useState<Set<string> | null>(null);
  const [ara, setAra] = useState("");
  const [seciliId, setSeciliId] = useState<string | null>(null);
  const [param, setParam] = useState<Record<string, string | number>>({});
  const [tema, setTema] = useState("");
  const [is, setIs] = useState(false);
  const [kaynakSuz, setKaynakSuz] = useState("");
  const [yontemSuz, setYontemSuz] = useState("");
  const kasaKartlari = useMemo(() => kasa.map(kasaKarti), [kasa]);
  const kasada = tur === "kasa";
  const liste = useMemo(() => kasada
    ? kasaKartlari.filter((e) => ara.toLocaleLowerCase("tr").split(/\s+/).filter(Boolean).every((k) => `${e.title} ${e.kind}`.toLocaleLowerCase("tr").includes(k)))
    : suz(kayitlar, tur, ara, kaynakSuz, yontemSuz), [kayitlar, kasaKartlari, kasada, tur, ara, kaynakSuz, yontemSuz]);
  const siteler = useMemo(() => [...new Set(kayitlar.filter((e) => e.dis).map((e) => e.site).filter(Boolean))].sort() as string[], [kayitlar]);
  const secili = kasada ? null : kayitlar.find((e) => e.id === seciliId) ?? null;
  const kasaSecili = kasada ? kasa.find((e) => e.id === seciliId) ?? null : null;

  const sec = (e: MotionKayit) => {
    if (toplu) { const y = new Set(toplu); if (y.has(e.id)) y.delete(e.id); else y.add(e.id); setToplu(y); return; }
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

  const kasaEkle = async (e: KasaKayit) => {
    const k = useKurgu.getState();
    if (!k.kurgu) { bildir("Önce kurgusu olan bir proje aç", true); return; }
    if (e.tur === "bilesen" && e.bilesen) {
      const b = e.bilesen;
      k.duzenle("Bileşen ekle", (f) => { K.bilesenEkle(f, k.zaman, { ad: b.ad, param: b.param ?? {} } as any, e.sure); });
      return;
    }
    if (!e.file) return;
    const yol = `library:${e.file.replace(/^library\//, "")}`;
    await k.kaynaktanEkle({ yol, ad: e.title, tur: e.tur === "sfx" ? "ses" : e.tur === "gorsel" ? "gorsel" : "motion", ...(e.tur === "sfx" ? { sfx: true } : {}) }, k.zaman, null, false);
    if (e.sablon || e.hf) {
      // Niyet klipte kalır: tema ya da parametre değişince vedit webm'i yeniden üretir (kurgu.motion_bagla).
      const d = useKurgu.getState();
      const id = d.secim[0];
      if (id) d.duzenle("Kasa niyeti", (f) => { const c = f.klipler.find((x) => x.id === id); if (c) { if (e.sablon) c.sablon = e.sablon; if (e.hf) c.hf = e.hf; } });
    }
  };

  const topluBitir = () => {
    if (!toplu?.size || !topluSil) return;
    topluSil(kasada ? "kasa" : "motion", [...toplu]);
    setToplu(null);
  };

  return (
    <>
      <div className="arac">
        <input type="search" aria-label="Motion kütüphanesinde ara" placeholder="Ara: ok, geçiş, grafik" value={ara} onChange={(e) => setAra(e.target.value)} style={{ flex: 1, minWidth: 0 }} />
        {topluSil && <Dugme aria-pressed={!!toplu} title="Birden çok kaydı seçip sil" onClick={() => { setToplu(toplu ? null : new Set()); setSeciliId(null); }}><CheckSquare size={14} /> {toplu ? "Seçimi bitir" : "Seç"}</Dugme>}
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
          const n = k === "kasa" ? kasa.length : suz(kayitlar, k, "").length;
          return n || !k || k === "kasa" ? <button key={k} type="button" role="tab" className="sekme" aria-selected={tur === k} onClick={() => { setTur(k); setSeciliId(null); setToplu(null); }}>{et}<span className="sayi">{n}</span></button> : null;
        })}
      </div>
      <div className="icerik">
        {kasada && !kasa.length && <Bos baslik="Kasan boş" metin="Timeline'da beğendiğin motion, şablon, bileşen ya da ses efekti klibine sağ tıkla, 'Kütüphaneye kaydet' seç. Hazır paket Keşif'te." />}
        {!kasada && !kayitlar.length && <Bos baslik="Motion kütüphanesi boş" metin="Ekle ile dosya yükle. Lisans bilgisi zorunludur." />}
        {!!(kasada ? kasa.length : kayitlar.length) && !liste.length && <Bos baslik="Eşleşen kayıt yok" metin="Aramayı ya da türü değiştir." />}
        <div className="motion-izgara">{liste.map((e) => <Kart key={e.id} e={e} secili={e.id === seciliId} isaretli={toplu?.has(e.id)} sec={() => sec(e)} />)}</div>
      </div>
      {toplu && (
        <div className="alt" style={{ display: "flex", gap: 6, alignItems: "center" }} data-toplu>
          <span className="ipucu">{toplu.size} seçili</span>
          <Dugme onClick={() => setToplu(new Set(liste.map((e) => e.id)))}>Görünenlerin hepsi</Dugme>
          <span style={{ flex: 1 }} />
          <Dugme tur="tehlike" disabled={!toplu.size} onClick={topluBitir}><Trash2 size={14} /> Sil</Dugme>
        </div>
      )}
      {kasaSecili && !toplu && (
        <div className="alt">
          <div style={{ fontWeight: 550, marginBottom: 2 }}>{kasaSecili.title}</div>
          <p className="ipucu" style={{ margin: "0 0 8px" }}>{KASA_TUR[kasaSecili.tur]} · {kasaSecili.sure} sn{kasaSecili.license ? ` · ${kasaSecili.license}` : ""}{kasaSecili.kaynak ? ` · ${kasaSecili.kaynak.proje}` : ""}</p>
          <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
            <Dugme tur="birincil" onClick={() => kasaEkle(kasaSecili).catch(hata)}><Plus size={14} /> Oynatma kafasına ekle</Dugme>
            <span style={{ flex: 1 }} />
            <Dugme tur="tehlike" title="Kasadan sil" onClick={() => sil(kasaKarti(kasaSecili), "kasa")}><Trash2 size={14} /></Dugme>
          </div>
        </div>
      )}
      {secili && !toplu && (
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
            <Dugme tur="tehlike" title={secili.kilitli ? "Kilitli: silmeden önce kilidi kaldırmanı ister" : "Kütüphaneden sil"} onClick={() => sil(secili)}>
              {secili.kilitli ? <Lock size={14} /> : <Trash2 size={14} />}
            </Dugme>
          </div>
        </div>
      )}
    </>
  );
};
