import { Lock, Pause, Play, Plus, Trash2, Upload } from "lucide-react";
import React, { useEffect, useMemo, useState } from "react";
import { ApiHata, istek, kutuphaneAl, sor, sureYaz, yukle } from "../api";
import { useDepo } from "../depo";
import { Bos, Diyalog, DosyaSec, Dugme, IkonDugme, Iskelet, useDinle } from "../ortak";
import type { KaynakOge } from "../zaman/depo";
import { GaleriPaneli } from "./GaleriPaneli";
import { GrafikPaneli } from "./GrafikPaneli";
import { MotionPaneli } from "./MotionPaneli";
import { SURUKLE_TUR } from "../zaman/Timeline";

export type Sekme = "galeri" | "sfx" | "muzik" | "motion" | "pano" | "grafik" | "font" | "kit";
// WHY: Galeri sekmesi eklenince sayaç veri["galeri"].length okuyup paneli düşürüyordu (2026-11-16). Liste ve sayaç
// yalnız /api/kutuphane yanıtındaki sekmelerden gelir.
const LISTELI = new Set<Sekme>(["sfx", "muzik", "motion", "pano", "font"]);
// Saf: test edilir (KutuphanePaneli.test.ts). Listesi olmayan sekme null, eksik anahtar boş liste.
export const sekmeKayitlari = (veri: Record<string, any> | null, k: Sekme): any[] | null =>
  LISTELI.has(k) ? (Array.isArray(veri?.[k]) ? veri![k] : []) : null;
// WHY: 409 yanıtı düz metin veya eksik alanlı JSON gelirse korumasız JSON.parse/dizi erişimi yakalanmamış hata atmasın.
export const cakismaMetni = (mesaj: string): string => {
  try {
    const d = JSON.parse(mesaj);
    const yuva = Array.isArray(d?.yuva) ? d.yuva : [];
    const projeler = Array.isArray(d?.projeler) ? d.projeler : [];
    const parca = [yuva.length && `Kit yuvası: ${yuva.join(", ")}`, projeler.length && `Kullanan projeler: ${projeler.join(", ")}`].filter(Boolean).join("\n");
    return parca || mesaj;
  } catch {
    return mesaj;
  }
};
const SEKMELER: [Sekme, string][] = [["galeri", "Galeri"], ["sfx", "SFX"], ["muzik", "Müzik"], ["motion", "Motion"], ["pano", "Pano"], ["grafik", "Grafik"], ["font", "Font"], ["kit", "Kit"]];
const KABUL: Partial<Record<Sekme, string>> = { sfx: "audio/*", muzik: "audio/*", motion: ".mp4,.mov,.webm,.mkv,.json,.lottie,.gif,.apng,.png,.svg", font: ".ttf,.otf,.woff2" };
const ALAN: Partial<Record<Sekme, [string, string, boolean?][]>> = {
  sfx: [["lisans", "Lisans", true], ["kategori", "Kategori (boşsa addan bulunur)"], ["url", "Kaynak adresi"], ["atif", "Atıf metni"]],
  muzik: [["lisans", "Lisans", true], ["baslik", "Başlık"], ["sanatci", "Sanatçı"], ["site", "Site"], ["duygu", "Duygu (virgülle)"], ["tur", "Tür"], ["url", "Kaynak adresi"], ["atif", "Atıf metni"]],
  // ADR 0046: kaynak zorunlu; lisans ve adres boşsa kaynağın doğrulanmış varsayılanı (mixkit, pixabay, lottiefiles, uppbeat, github).
  motion: [["site", "Kaynak (mixkit, pixabay, lottiefiles, uppbeat, github)", true], ["url", "Varlığın sayfa adresi"], ["lisans", "Lisans (boşsa kaynağın varsayılanı)"], ["atif", "Atıf metni (Uppbeat Free için zorunlu)"], ["kisit", "Kısıtlar (virgülle, ör. yalniz-kendi-kanalin)"], ["baslik", "Başlık"], ["kind", "Tür (overlay, icon, transition, lower-third, background, cta, reaction, light-leak, texture)"], ["ne_zaman", "Ne zaman kullanılır (AI edit için)"], ["etiket", "Etiketler (virgülle)"]],
  font: [["ad", "Font adı", true], ["lisans", "Lisans", true], ["rol", "Rol (display, body)"]],
};

const ad = (e: any) => e.title && !e.title.startsWith("(") ? e.title : e.id;
const arama = (e: any) => [e.id, e.title, e.category, e.artist, e.genre, e.kind, ...(e.tags ?? []), ...(e.mood ?? [])].filter(Boolean).join(" ").toLocaleLowerCase("tr");

const kaynakOgesi = (sekme: Sekme, e: any): KaynakOge | undefined => {
  const yol = `library:${String(e.file ?? "").replace(/^library\//, "")}`;
  if (sekme === "sfx") return { yol, ad: e.id, tur: "ses", sfx: true };
  if (sekme === "muzik") return { yol, ad: ad(e), tur: "ses", muzik: true };
  if (sekme === "motion") return { yol, ad: ad(e), tur: "motion" };
  return undefined;
};

const YuklemeDiyalog: React.FC<{ tur: Sekme | null; dosyalar: File[]; kapat: () => void; bitti: () => void }> = ({ tur, dosyalar, kapat, bitti }) => {
  const { hata, bildir } = useDepo();
  const [alan, setAlan] = useState<Record<string, string>>({});
  const [is, setIs] = useState<{ i: number; oran: number } | null>(null);
  const gonder = async (e: React.FormEvent) => {
    e.preventDefault();
    let n = 0;
    for (const [i, d] of dosyalar.entries()) {
      try {
        await yukle(`/api/kutuphane/${tur}?${sor({ dosya: d.name, ...alan })}`, d, (oran) => setIs({ i, oran }));
        n++;
      } catch (er) { hata(new Error(`${d.name}: ${(er as Error).message}`)); }
    }
    setIs(null);
    if (n) bildir(`${n} dosya kütüphaneye eklendi`);
    bitti(); kapat();
  };
  return (
    <Diyalog acik={!!tur} kapat={() => !is && kapat()}>
      <h2>Kütüphaneye ekle</h2>
      <p>{dosyalar.length === 1 ? dosyalar[0].name : `${dosyalar.length} dosya`}{dosyalar.length > 1 ? ". Bilgiler hepsine uygulanır." : ""}</p>
      <form onSubmit={gonder}>
        <div className="form">
          {tur && ALAN[tur]?.map(([k, etiket, zorunlu]) => (
            <label key={k} className={zorunlu ? "zorunlu" : ""}>{etiket}
              <input required={zorunlu} value={alan[k] ?? ""} onChange={(e) => setAlan({ ...alan, [k]: e.target.value })} placeholder={k === "lisans" ? "ör. Pixabay Content License, CC0" : undefined} />
            </label>
          ))}
        </div>
        {is && <div className="ilerleme" style={{ marginBottom: 12 }}><i style={{ width: `${((is.i + is.oran) / dosyalar.length) * 100}%` }} /></div>}
        <div className="eylemler">
          <Dugme disabled={!!is} onClick={kapat}>Vazgeç</Dugme>
          <Dugme tur="birincil" type="submit" disabled={!!is}>{is ? "Yükleniyor" : "Ekle"}</Dugme>
        </div>
      </form>
    </Diyalog>
  );
};

const KitGorunumu: React.FC<{ kit: any; sfx: any[]; tazele: () => void }> = ({ kit, sfx, tazele }) => {
  const { hata } = useDepo();
  const ata = async (studyo: string, rol: string, id: string | null) => {
    try { await istek("/api/kit", { method: "PUT", json: { studyo, rol, id } }); tazele(); } catch (e) { hata(e); }
  };
  const kategoriler = useMemo(() => [...sfx].sort((a, b) => a.id.localeCompare(b.id)), [sfx]);
  return (
    <>
      <p className="ipucu" style={{ padding: "8px 8px 0", margin: 0 }}>Yuvadaki ses o rolde her videoda kullanılır. Boş yuvayı sistem seçer.</p>
      {Object.entries<Record<string, string | null>>(kit.always).map(([s, roller]) => (
        <section key={s}>
          <div className="baslik">{s === "*" ? "Tüm stüdyolar" : s}</div>
          {Object.entries(roller).map(([rol, id]) => {
            const kilitli = !!id && kit.locked.includes(id);
            return (
              <div key={rol} className="satir">
                <span style={{ width: 96, flex: "none", color: "var(--y2)" }}>{rol}</span>
                {kilitli
                  ? <span className="ad" title={id!}><Lock size={12} color="var(--y3)" /> {id}</span>
                  : <select aria-label={`${s} ${rol} yuvası`} style={{ flex: 1, minWidth: 0 }} value={id ?? ""} onChange={(e) => ata(s, rol, e.target.value || null)}>
                      <option value="">Boş: sistem seçer</option>
                      {kategoriler.map((e) => <option key={e.id} value={e.id}>{e.id}</option>)}
                    </select>}
              </div>
            );
          })}
        </section>
      ))}
    </>
  );
};

export const KutuphanePaneli: React.FC = () => {
  const { goster, onayla, bildir, hata, panoEkle } = useDepo();
  const [panoSure, setPanoSure] = useState(8);
  const [veri, setVeri] = useState<any>(null);
  const [sekme, setSekme] = useState<Sekme>("sfx");
  const [ara, setAra] = useState("");
  const [kategori, setKategori] = useState("");
  const [secili, setSecili] = useState<any>(null);
  const [bekleyen, setBekleyen] = useState<File[]>([]);
  const { calan, cal } = useDinle();

  // İlk açılış oturum önbelleğinden; sonraki her çağrı (yükleme, silme, kilit) sunucudan tazeler.
  const al = async (yenile: unknown = true) => { try { setVeri(await kutuphaneAl(!!yenile)); } catch (e) { hata(e); } };
  useEffect(() => { al(false); }, []);
  useEffect(() => { setSecili(null); setKategori(""); setAra(""); }, [sekme]);

  // Kendi verisini getiren sekmeler (galeri, grafik) ve kit /api/kutuphane listesinde yoktur.
  const hepsi: any[] = sekmeKayitlari(veri, sekme) ?? [];
  const kategoriler = useMemo(() => [...new Set(hepsi.map((e) => e.category).filter(Boolean))].sort() as string[], [hepsi]);
  const liste = useMemo(() => {
    const kelimeler = ara.toLocaleLowerCase("tr").split(/\s+/).filter(Boolean);
    return hepsi.filter((e) => (!kategori || e.category === kategori) && kelimeler.every((k) => arama(e).includes(k)));
  }, [hepsi, ara, kategori]);

  const sec = (e: any) => {
    setSecili(e);
    if (sekme === "motion") goster({ tur: "video", url: e.url, ad: ad(e), kaynak: kaynakOgesi(sekme, e) });
    if (sekme === "sfx" || sekme === "muzik") goster({ tur: "ses", url: e.url, ad: ad(e), kaynak: kaynakOgesi(sekme, e) });
    if (sekme === "pano") goster({ tur: "pano", url: e.url, ad: e.title });
  };

  // WHY: bkz. wiki/decisions/0061-kasa-ve-kesif.md. Kilitli varlık çıkmaz 403 yerine onaylı "Kilidi kaldır ve sil" yolu (423).
  const sil = async (e: any, zorla = false, tur: string = sekme, kilitAc = false): Promise<void> => {
    if (!zorla && !kilitAc && !(await onayla({ baslik: "Kütüphaneden sil", onay: "Sil", tehlike: true, metin: `${e.id}\n\nDosya geri dönüşüm kutusuna gider, manifest kaydı kaldırılır.` }))) return;
    try {
      const r = await istek(`/api/kutuphane/${tur}/${encodeURIComponent(e.id)}?${sor({ zorla: zorla || undefined, kilit_ac: kilitAc || undefined })}`, { method: "DELETE" });
      bildir(r.mesaj);
      setSecili(null);
      await al();
    } catch (er) {
      if (er instanceof ApiHata && er.durum === 423) {
        if (await onayla({ baslik: "Kilitli varlık", onay: "Kilidi kaldır ve sil", tehlike: true, metin: `${e.id}\n\nBu varlık kit.json'da kilitli (ADR 0012). Kilidi kaldırılır, atandığı yuvalar boşalır, sonra silinir.` })) return sil(e, zorla, tur, true);
      } else if (er instanceof ApiHata && er.durum === 409) {
        const metin = cakismaMetni(er.message);
        if (await onayla({ baslik: "Bu varlık kullanımda", onay: "Yine de sil", tehlike: true, metin: `${e.id}\n\n${metin}\n\nSilinirse bu projeler render'da dosyayı bulamaz.` })) return sil(e, true, tur, kilitAc);
      } else hata(er);
    }
  };

  const topluSil = async (tur: string, idler: string[]) => {
    if (!(await onayla({ baslik: `${idler.length} kaydı sil`, onay: "Sil", tehlike: true, metin: "Dosyalar geri dönüşüm kutusuna gider. Kilitli ya da kullanımdaki kayıtlar atlanır; onları tek tek silebilirsin." }))) return;
    try {
      const r = await istek("/api/kutuphane/toplu-sil", { method: "POST", json: { tur, idler } });
      bildir(r.mesaj);
      await al();
    } catch (er) { hata(er); }
  };
  // Timeline'dan kasaya kayıt: liste tazelensin (ADR 0061)
  useEffect(() => { const f = () => { al(); }; window.addEventListener("studio-kutuphane-tazele", f); return () => window.removeEventListener("studio-kutuphane-tazele", f); }, []);

  const yukleme = !!KABUL[sekme];
  const ses = sekme === "sfx" || sekme === "muzik";

  return (
    <div className="panel">
      <div className="arac" style={{ padding: "3px 6px" }}>
        <div className="sekmeler" role="tablist">
          {SEKMELER.map(([k, et]) => (
            <button key={k} type="button" role="tab" className="sekme" aria-selected={sekme === k} onClick={() => setSekme(k)}>
              {et}{veri && LISTELI.has(k) && <span className="sayi">{sekmeKayitlari(veri, k)!.length}</span>}
            </button>
          ))}
        </div>
      </div>
      {sekme === "galeri" ? <GaleriPaneli />
        : sekme === "grafik" ? <div className="icerik"><GrafikPaneli /></div>
        : sekme === "motion" && veri ? <MotionPaneli kayitlar={veri.motion} kasa={veri.kasa ?? []} temalar={veri.temalar ?? []} tazele={al} sil={(e, tur) => sil(e, false, tur ?? "motion")} topluSil={topluSil} yukle={setBekleyen} />
        : <>
      {sekme !== "kit" && (
        <div className="arac">
          <input type="search" aria-label="Kütüphanede ara" placeholder="Ara: ad, etiket, duygu" value={ara} onChange={(e) => setAra(e.target.value)} style={{ flex: 1, minWidth: 0 }} />
          {kategoriler.length > 1 && (
            <select aria-label="Kategori" value={kategori} onChange={(e) => setKategori(e.target.value)} style={{ maxWidth: 120 }}>
              <option value="">Tümü</option>{kategoriler.map((c) => <option key={c}>{c}</option>)}
            </select>
          )}
          {yukleme && <DosyaSec kabul={KABUL[sekme]} sec={setBekleyen}><Upload size={14} /> Ekle</DosyaSec>}
        </div>
      )}
      <div className="icerik">
        {!veri && <Iskelet />}
        {veri && sekme === "kit" && <KitGorunumu kit={veri.kit} sfx={veri.sfx} tazele={al} />}
        {veri && sekme !== "kit" && !hepsi.length && <Bos baslik={sekme === "motion" ? "Motion kütüphanesi boş" : "Kayıt yok"} metin={yukleme ? "Ekle ile dosya yükle. Lisans bilgisi zorunludur." : undefined} />}
        {veri && !!hepsi.length && !liste.length && <Bos baslik="Eşleşen kayıt yok" metin="Aramayı ya da kategoriyi değiştir." />}
        {sekme !== "kit" && liste.map((e) => (
          <div key={e.id} className={`satir ${secili?.id === e.id ? "secili" : ""}`} role="button" tabIndex={0} onClick={() => sec(e)} onKeyDown={(k) => k.key === "Enter" && k.target === k.currentTarget && sec(e)} title={e.id}
            draggable={!!kaynakOgesi(sekme, e)} onDragStart={(k) => { const o = kaynakOgesi(sekme, e); if (o) { k.dataTransfer.setData(SURUKLE_TUR, JSON.stringify(o)); k.dataTransfer.effectAllowed = "copy"; } }}>
            {ses && <IkonDugme ad={calan === e.url ? "Durdur" : "Dinle"} acik={calan === e.url} onClick={(k) => { k.stopPropagation(); cal(e.url); }}>{calan === e.url ? <Pause size={14} /> : <Play size={14} />}</IkonDugme>}
            <span className="ad">{ad(e)}</span>
            {e.category === "aday" && <span className="rozet uyari">aday</span>}
            {e.yuvada && <span className="rozet vurgu">kit</span>}
            {e.kilitli && <Lock size={12} color="var(--y3)" aria-label="Kilitli" />}
            {e.category && e.category !== "aday" && <span className="bilgi">{e.category}</span>}
            {e.duration_s != null && <span className="bilgi">{sureYaz(e.duration_s)}</span>}
          </div>
        ))}
      </div>
      {secili && sekme !== "kit" && (
        <div className="alt">
          <dl className="tani" style={{ margin: "0 0 8px" }}>
            <dt>Kimlik</dt><dd>{secili.id}</dd>
            {secili.license && <><dt>Lisans</dt><dd>{secili.license}</dd></>}
            {secili.lufs != null && <><dt>Yükseklik</dt><dd>{secili.lufs} LUFS</dd></>}
            {secili.bpm != null && <><dt>Tempo</dt><dd>{secili.bpm} BPM</dd></>}
            {secili.mood?.length > 0 && <><dt>Duygu</dt><dd>{secili.mood.join(", ")}</dd></>}
            {secili.role && <><dt>Rol</dt><dd>{secili.role}</dd></>}
            {secili.attribution && <><dt>Atıf</dt><dd>{secili.attribution}</dd></>}
          </dl>
          {sekme === "font" && <div style={{ fontSize: 22, marginBottom: 8 }}><FontOrnek ad={secili.id} url={secili.url} /></div>}
          {sekme === "pano" && (
            <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <label style={{ display: "flex", alignItems: "center", gap: 5 }}>Süre
                <input type="number" min={1} max={120} step={0.5} value={panoSure} aria-label="Pano süresi" onChange={(e) => setPanoSure(Number(e.target.value))} style={{ width: 64 }} />
              </label>
              <Dugme tur="birincil" disabled={!(panoSure >= 0.5 && panoSure <= 120)} onClick={() => panoEkle(secili.id, secili.title, panoSure)}><Plus size={14} /> Timeline'a ekle</Dugme>
            </div>
          )}
          {sekme !== "pano" && (
            <Dugme tur="tehlike" title={secili.kilitli ? "Kilitli: silmeden önce kilidi kaldırmanı ister" : undefined} onClick={() => sil(secili)}>
              {secili.kilitli ? <Lock size={14} /> : <Trash2 size={14} />} Sil
            </Dugme>
          )}
        </div>
      )}
      <YuklemeDiyalog tur={bekleyen.length ? sekme : null} dosyalar={bekleyen} kapat={() => setBekleyen([])} bitti={al} />
      </>}
    </div>
  );
};

const FontOrnek: React.FC<{ ad: string; url: string }> = ({ ad, url }) => {
  const aile = `onizleme-${ad}`;
  useEffect(() => {
    // WHY: unmount veya font değişiminde FontFace silinmezse document.fonts birikerek bellek sızdırır.
    let iptal = false;
    let yuklu: FontFace | null = null;
    new FontFace(aile, `url(${url})`, { weight: "100 900" }).load().then((f) => {
      if (iptal) return;
      yuklu = f;
      document.fonts.add(f);
    }).catch(() => {});
    return () => { iptal = true; if (yuklu) document.fonts.delete(yuklu); };
  }, [aile, url]);
  return <span style={{ fontFamily: `"${aile}"` }}>Şğİıöç Hızlı kurgu 0123</span>;
};
