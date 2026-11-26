// Stil paneli: referans görsel/video yükleme, stile özel varlıklar, paket aktarımı, STYLE.md + MOTION.md ve projeye stil seçimi.
// WHY: bkz. wiki/decisions/0029-stil-paneli.md
import { Check, Download, Plus, Save, Sparkles, Trash2, Upload } from "lucide-react";
import React, { useCallback, useEffect, useState } from "react";
import { ApiHata, istek, sor, yukle } from "../api";
import { useDepo } from "../depo";
import { Bos, DosyaSec, Dugme, IkonDugme } from "../ortak";
import { Bolum, Secim } from "./alanlar";
import { HazirStiller, RENK_SIRA } from "./HazirStiller";
import { StilVarliklari } from "./StilVarliklari";

interface StilOge {
  ad: string;
  hazir: boolean;
  style_md: string;
  motion_md: string;
  referanslar: string[];
  varlik_sayisi?: number;
  kapak?: boolean;
  palet?: Record<string, string>;
}

interface StilYanit {
  stiller: StilOge[];
  secili: string | null;
}

interface PaketYukleYanit {
  tamam: boolean;
  studyo: string;
  ad: string;
  varlik_sayisi?: number;
}

interface Yukleme {
  ad: string;
  oran: number;
}

const KABUL = "video/*,image/*";
const AD_DESEN = /^[\w-]{1,40}$/;
const VARSAYILAN_STUDYOLAR = ["instagram", "ugc", "youtube-animasyon"];

const paketPut = (url: string, dosya: File, ilerleme: (oran: number) => void) =>
  new Promise<PaketYukleYanit>((coz, reddet) => {
    const x = new XMLHttpRequest();
    x.open("PUT", url);
    x.upload.onprogress = (e) => e.lengthComputable && ilerleme(e.loaded / e.total);
    x.onload = () => {
      let veri: any = {};
      try { veri = JSON.parse(x.responseText); } catch { /* metin değil */ }
      if (x.status < 300) return coz(veri as PaketYukleYanit);
      const mesaj = typeof veri.detail === "string" ? veri.detail : `Sunucu hatası (${x.status})`;
      reddet(new ApiHata(x.status, mesaj));
    };
    x.onerror = () => reddet(new ApiHata(0, "Paket yükleme kesildi. Dosya kaydedilmedi."));
    x.send(dosya);
  });

export const StilPaneli: React.FC = () => {
  const aktif = useDepo((d) => d.aktif);
  const studyolar = useDepo((d) => d.studyolar);
  const surum = useDepo((d) => d.surum);
  const ajan = useDepo((d) => d.ajan);
  const biten = useDepo((d) => d.isler.filter((x) => x.komut === "stil-uret" && x.bitis).length);
  const calisiyor = useDepo((d) => d.isler.some((x) => x.komut === "stil-uret" && !x.bitis));
  const { isBaslat, hata, bildir, onayla } = useDepo();

  const [seciliStudyo, setSeciliStudyo] = useState(aktif?.studyo ?? "instagram");
  const [stiller, setStiller] = useState<StilOge[]>([]);
  const [projeSecili, setProjeSecili] = useState<string | null>(null);
  const [seciliAd, setSeciliAd] = useState<string | null>(null);
  const [yeniAd, setYeniAd] = useState("");
  const [styleMd, setStyleMd] = useState("");
  const [yuklemeler, setYuklemeler] = useState<Yukleme[]>([]);
  const [uzerinde, setUzerinde] = useState(false);
  const [silinecek, setSilinecek] = useState<string | null>(null);
  const [sekme, setSekme] = useState<"benim" | "hazir">("benim");

  useEffect(() => {
    if (aktif) setSeciliStudyo(aktif.studyo);
  }, [aktif?.studyo]);

  useEffect(() => {
    setStiller([]);
    setSeciliAd(null);
    setSilinecek(null);
  }, [seciliStudyo]);

  const al = useCallback(async (tercihAd?: string) => {
    const q = aktif?.studyo === seciliStudyo ? `?${sor({ proje: aktif.ad })}` : "";
    try {
      const v: StilYanit = await istek(`/api/stil/${seciliStudyo}${q}`);
      setStiller((onceki) => {
        const taslaklar = onceki.filter(
          (o) => !o.hazir && !o.referanslar.length && !(o.varlik_sayisi ?? 0) && !v.stiller.some((s) => s.ad === o.ad),
        );
        return [...v.stiller, ...taslaklar];
      });
      setProjeSecili(v.secili);
      setSeciliAd((mevcut) => {
        if (tercihAd && v.stiller.some((s) => s.ad === tercihAd)) return tercihAd;
        if (mevcut && v.stiller.some((s) => s.ad === mevcut)) return mevcut;
        if (v.secili && v.stiller.some((s) => s.ad === v.secili)) return v.secili;
        return v.stiller[0]?.ad ?? mevcut;
      });
    } catch (e) {
      hata(e);
    }
  }, [seciliStudyo, aktif?.studyo, aktif?.ad]);

  useEffect(() => {
    al();
  }, [al, surum, biten]);

  const secili = stiller.find((s) => s.ad === seciliAd) ?? null;

  useEffect(() => {
    setStyleMd(secili?.style_md ?? "");
  }, [secili?.ad, secili?.style_md]);

  const yeniEkle = (e: React.FormEvent) => {
    e.preventDefault();
    const temiz = yeniAd.trim();
    if (!AD_DESEN.test(temiz)) {
      bildir("Stil adı yalnız harf, rakam, tire ve alt çizgi içerebilir (en çok 40 karakter)", true);
      return;
    }
    if (!stiller.some((s) => s.ad === temiz)) {
      setStiller((l) => [...l, { ad: temiz, hazir: false, style_md: "", motion_md: "", referanslar: [], varlik_sayisi: 0 }]);
    }
    setSeciliAd(temiz);
    setYeniAd("");
  };

  const paketYukle = async (dosyalar: File[]) => {
    const d = dosyalar[0];
    if (!d) return;
    const gonder = async (uzerineYaz: boolean): Promise<PaketYukleYanit | null> => {
      setYuklemeler([{ ad: d.name, oran: 0 }]);
      try {
        const q = sor({ dosya: d.name, uzerine_yaz: uzerineYaz });
        return await paketPut(`/api/stil/${seciliStudyo}/paket-yukle?${q}`, d, (oran) =>
          setYuklemeler([{ ad: d.name, oran }]),
        );
      } finally {
        setYuklemeler([]);
      }
    };
    try {
      let sonuc: PaketYukleYanit | null = null;
      try {
        sonuc = await gonder(false);
      } catch (e) {
        if (e instanceof ApiHata && e.durum === 409) {
          const onay = await onayla({
            baslik: "Stil zaten var",
            metin: `${d.name} paketi mevcut bir stille çakışıyor.\n\nÜzerine yazılsın mı?`,
            onay: "Üzerine yaz",
            tehlike: true,
          });
          if (!onay) return;
          sonuc = await gonder(true);
        } else {
          throw e;
        }
      }
      if (sonuc?.ad) {
        await al(sonuc.ad);
        setSeciliAd(sonuc.ad);
        bildir(`Stil paketi yüklendi: ${sonuc.ad}`);
      } else {
        await al();
      }
    } catch (e) {
      hata(e);
    }
  };

  const yukleHepsi = async (dosyalar: File[]) => {
    if (!secili || !dosyalar.length) return;
    setYuklemeler(dosyalar.map((d) => ({ ad: d.name, oran: 0 })));
    let basarili = 0;
    for (const [i, d] of dosyalar.entries()) {
      try {
        await yukle(`/api/stil/${seciliStudyo}/${secili.ad}/referans?${sor({ dosya: d.name })}`, d, (oran) =>
          setYuklemeler((l) => l.map((y, k) => (k === i ? { ...y, oran } : y))));
        basarili++;
      } catch (e) {
        hata(new Error(`${d.name}: ${(e as Error).message}`));
      }
    }
    setYuklemeler([]);
    if (basarili) bildir(`${basarili} referans yüklendi`);
    await al();
  };

  const referansSil = async (dosya: string) => {
    if (!secili) return;
    try {
      await istek(`/api/stil/${seciliStudyo}/${secili.ad}/referans?${sor({ dosya })}`, { method: "DELETE" });
      bildir(`Referans silindi: ${dosya}`);
      await al();
    } catch (e) {
      hata(e);
    }
  };

  const stilSil = async (ad: string) => {
    setSilinecek(null);
    const yalnizTaslak = stiller.some((s) => s.ad === ad && !s.hazir && !s.referanslar.length && !(s.varlik_sayisi ?? 0));
    try {
      if (!yalnizTaslak) await istek(`/api/stil/${seciliStudyo}/${ad}`, { method: "DELETE" });
      setStiller((l) => l.filter((s) => s.ad !== ad));
      if (seciliAd === ad) setSeciliAd(null);
      bildir(`Stil silindi: ${ad}`);
      await al();
    } catch (e) {
      hata(e);
    }
  };

  const uret = () => {
    if (!secili) return;
    isBaslat("stil-uret", { studyo: seciliStudyo, stil: secili.ad, motor: ajan.motor, model: ajan.model });
  };

  const kaydet = async () => {
    if (!secili) return;
    try {
      await istek(`/api/stil/${seciliStudyo}/${secili.ad}`, { method: "PUT", json: { style_md: styleMd } });
      bildir("STYLE.md kaydedildi");
      await al();
    } catch (e) {
      hata(e);
    }
  };

  const projeyeSec = async () => {
    if (!aktif || !secili) return;
    try {
      await istek(`/api/stil/${seciliStudyo}/sec`, { method: "POST", json: { proje: aktif.ad, stil: secili.ad } });
      bildir(`Stil seçildi: ${secili.ad}; AI edit bu stile uyar`);
      await al();
    } catch (e) {
      hata(e);
    }
  };

  const birak = secili ? {
    onDragOver: (e: React.DragEvent) => {
      if ((e.target as HTMLElement | null)?.closest?.(".sv-yukle")) { setUzerinde(false); return; }
      if (e.dataTransfer.types.includes("Files")) { e.preventDefault(); setUzerinde(true); }
    },
    onDragLeave: (e: React.DragEvent) => { if (!e.currentTarget.contains(e.relatedTarget as Node)) setUzerinde(false); },
    onDrop: (e: React.DragEvent) => {
      if ((e.target as HTMLElement | null)?.closest?.(".sv-yukle")) { setUzerinde(false); return; }
      if (e.dataTransfer.files.length) { e.preventDefault(); setUzerinde(false); yukleHepsi([...e.dataTransfer.files]); }
    },
  } : {};

  const studyoSecenekler: [string, string][] = (studyolar.length ? studyolar : VARSAYILAN_STUDYOLAR).map((s) => [s, s]);
  const aktifBuStudyoda = aktif?.studyo === seciliStudyo;

  const sekmeler = (
    <div className="sekmeler" role="tablist" aria-label="Stil kaynağı">
      <button type="button" role="tab" className="sekme" aria-selected={sekme === "benim"} onClick={() => setSekme("benim")}>
        Stillerim<span className="sayi">{stiller.length}</span>
      </button>
      <button type="button" role="tab" className="sekme" aria-selected={sekme === "hazir"} onClick={() => setSekme("hazir")}>
        Hazır stiller
      </button>
    </div>
  );

  if (sekme === "hazir") {
    return (
      <div className="panel">
        <div className="arac" style={{ flexWrap: "wrap" }}>
          <Secim etiket="Stüdyo" deger={seciliStudyo} degis={setSeciliStudyo} secenekler={studyoSecenekler} />
          {sekmeler}
        </div>
        <HazirStiller
          studyo={seciliStudyo}
          proje={aktifBuStudyoda ? aktif!.ad : null}
          mevcut={stiller.map((s) => s.ad)}
          eklendi={async (ad) => { await al(); setSeciliAd(ad); setSekme("benim"); }}
        />
      </div>
    );
  }

  return (
    <div className={`panel birakma ${uzerinde ? "uzerinde" : ""}`} {...birak}>
      <div className="arac" style={{ flexWrap: "wrap" }}>
        <Secim etiket="Stüdyo" deger={seciliStudyo} degis={setSeciliStudyo} secenekler={studyoSecenekler} />
        {sekmeler}
        <form onSubmit={yeniEkle} style={{ display: "inline-flex", gap: 4, flex: 1, minWidth: 140 }}>
          <input
            aria-label="Yeni stil adı"
            placeholder="Yeni stil (ör. vox-koyu)"
            pattern="[\w\-]{1,40}"
            value={yeniAd}
            onChange={(e) => setYeniAd(e.target.value)}
            style={{ flex: 1, minWidth: 0 }}
          />
          <Dugme type="submit" disabled={!yeniAd.trim()} title="Yeni stil ekle">
            <Plus size={14} /> Yeni stil
          </Dugme>
        </form>
        <DosyaSec kabul=".zip" sec={paketYukle} disabled={!!yuklemeler.length}>
          <Upload size={14} /> Paket yükle (.zip)
        </DosyaSec>
      </div>
      {!!yuklemeler.length && (
        <div className="alt" style={{ borderTop: 0, borderBottom: "1px solid var(--cizgi)", display: "grid", gap: 6 }}>
          {yuklemeler.map((y, i) => (
            <div key={i}>
              <div className="ipucu" style={{ display: "flex", justifyContent: "space-between" }}>
                <span>{y.ad}</span><span>%{Math.round(y.oran * 100)}</span>
              </div>
              <div className="ilerleme"><i style={{ width: `${y.oran * 100}%` }} /></div>
            </div>
          ))}
        </div>
      )}
      <div className="icerik">
        {!stiller.length && (
          <Bos baslik="Henüz stil yok" metin="Yukarıdan yeni bir stil adı oluşturup referans video veya görsellerini yükle." />
        )}
        <div className="motion-izgara stil-izgara">
          {stiller.map((s) => {
            const projedeKullaniliyor = aktifBuStudyoda && projeSecili === s.ad;
            const renk = s.palet ?? {};
            return (
              <div
                key={s.ad}
                className={`motion-kart ${s.ad === seciliAd ? "secili" : ""}`}
                role="button"
                tabIndex={0}
                title={s.hazir ? s.ad : `${s.ad}: referans bekliyor`}
                onClick={() => { setSeciliAd(s.ad); setSilinecek(null); }}
                onKeyDown={(e) => e.key === "Enter" && e.target === e.currentTarget && setSeciliAd(s.ad)}
              >
                <span className="motion-kare dikey">
                  {s.kapak
                    ? <img src={`/api/stil/${seciliStudyo}/${encodeURIComponent(s.ad)}/kapak?v=${surum}-${s.referanslar.length}`} alt="" loading="lazy" />
                    : <span className="galeri-yer" style={{ background: renk.zemin }}>
                        {Object.keys(renk).length > 0 && (
                          <span className="galeri-palet">{RENK_SIRA.map((r) => renk[r] && <i key={r} style={{ background: renk[r] }} />)}</span>
                        )}
                        <span className="galeri-yer-ad" style={{ color: renk.yazi }}>{s.ad}</span>
                      </span>}
                  {projedeKullaniliyor
                    ? <span className="rozet vurgu"><Check size={11} /> seçili</span>
                    : !s.hazir && <span className="rozet uyari">referans bekliyor</span>}
                </span>
                <span className="motion-ad">
                  {s.ad}
                  {(s.varlik_sayisi ?? 0) > 0 && <span className="ipucu"> · {s.varlik_sayisi} varlık</span>}
                </span>
              </div>
            );
          })}
        </div>

        {secili && (
          <div style={{ borderTop: "1px solid var(--cizgi)", marginTop: 6 }}>
            <div className="arac" style={{ flexWrap: "wrap" }}>
              <b>{secili.ad}</b>
              <span className="bosluk" />
              {(secili.hazir || (secili.varlik_sayisi ?? 0) > 0) && (
                <a
                  className="dugme"
                  href={`/api/stil/${seciliStudyo}/${encodeURIComponent(secili.ad)}/paket.zip`}
                  download={`${seciliStudyo}-${secili.ad}.zip`}
                  title="Stili, referansları ve özel varlıkları tek .zip paketi olarak indir"
                >
                  <Download size={14} /> Paketi indir (.zip)
                </a>
              )}
              {silinecek === secili.ad ? (
                <span style={{ display: "inline-flex", gap: 4, alignItems: "center" }}>
                  <span className="ipucu">Paket ve referanslar silinsin mi?</span>
                  <Dugme tur="tehlike" onClick={() => stilSil(secili.ad)}>Sil</Dugme>
                  <Dugme onClick={() => setSilinecek(null)}>Vazgeç</Dugme>
                </span>
              ) : (
                <IkonDugme ad={`${secili.ad} stilini sil`} onClick={() => setSilinecek(secili.ad)}>
                  <Trash2 size={14} />
                </IkonDugme>
              )}
              {aktifBuStudyoda && secili.hazir && (
                <Dugme
                  tur={projeSecili === secili.ad ? undefined : "birincil"}
                  disabled={projeSecili === secili.ad}
                  onClick={projeyeSec}
                >
                  <Check size={14} /> {projeSecili === secili.ad ? "Bu projede seçili" : "Bu projede kullan"}
                </Dugme>
              )}
              <Dugme
                tur="birincil"
                disabled={calisiyor || !secili.referanslar.length}
                onClick={uret}
                title="Referansları analiz eder ve seçili AI motoruyla STYLE.md, MOTION.md, tokens.json üretir"
              >
                <Sparkles size={14} /> {calisiyor ? "Üretiliyor…" : "Stil üret"}
              </Dugme>
            </div>

            <Bolum ad={`Referanslar (${secili.referanslar.length})`} acik>
              <div className="arac" style={{ padding: "2px 0", borderBottom: 0 }}>
                <DosyaSec kabul={KABUL} sec={yukleHepsi} disabled={!!yuklemeler.length}>
                  <Upload size={14} /> Referans yükle
                </DosyaSec>
                <span className="ipucu">Video veya görsel sürükleyip bırak</span>
              </div>
              {!secili.referanslar.length && (
                <p className="ipucu" style={{ margin: "4px 0" }}>
                  Henüz referans dosya yok. Stil üretmek için örnek video veya görsel yükle.
                </p>
              )}
              {secili.referanslar.map((dosya) => (
                <div key={dosya} className="satir" style={{ padding: "2px 4px" }}>
                  <span className="ad">{dosya}</span>
                  <a
                    className="dugme ikon eylem"
                    href={`/api/stil/${seciliStudyo}/${encodeURIComponent(secili.ad)}/referans/indir?${sor({ dosya })}`}
                    download={dosya}
                    title={`${dosya} referansını indir`}
                    aria-label={`${dosya} referansını indir`}
                  >
                    <Download size={14} />
                  </a>
                  <IkonDugme ad={`${dosya} referansını sil`} className="eylem" onClick={() => referansSil(dosya)}>
                    <Trash2 size={14} />
                  </IkonDugme>
                </div>
              ))}
            </Bolum>

            <Bolum ad="Stile özel varlıklar" acik>
              <StilVarliklari studyo={seciliStudyo} stilAd={secili.ad} degisti={() => al()} />
            </Bolum>

            <Bolum ad="STYLE.md" acik>
              <textarea
                aria-label="STYLE.md içeriği"
                rows={12}
                value={styleMd}
                placeholder="Stil üretildiğinde burada görünür; doğrudan da yazıp kaydedebilirsin."
                onChange={(e) => setStyleMd(e.target.value)}
                style={{ width: "100%", fontFamily: "var(--mono)", fontSize: 12 }}
              />
              <div className="arac" style={{ padding: "4px 0 0", borderBottom: 0, justifyContent: "flex-end" }}>
                <Dugme onClick={kaydet} disabled={styleMd === secili.style_md && secili.hazir}>
                  <Save size={14} /> Kaydet
                </Dugme>
              </div>
            </Bolum>

            <Bolum ad="MOTION.md" acik={false}>
              {secili.motion_md ? (
                <pre className="gunluk" style={{ margin: 0, maxHeight: 260 }}>{secili.motion_md}</pre>
              ) : (
                <p className="ipucu" style={{ margin: 0 }}>MOTION.md henüz üretilmedi.</p>
              )}
            </Bolum>
          </div>
        )}
      </div>
    </div>
  );
};
