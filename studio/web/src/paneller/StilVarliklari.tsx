// Stile özel varlık deposu, sürükle-bırak yükleme, kategori filtreleme, tekil/temalı-native .webm indirme ve timeline'a ekleme.
import {
  Check,
  Download,
  Film,
  Image as ImageIcon,
  Loader2,
  Pause,
  Play,
  Plus,
  Sparkles,
  Trash2,
  Upload,
  User,
  Volume2,
} from "lucide-react";
import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { istek, sor, sureYaz, yukle } from "../api";
import { useDepo } from "../depo";
import { Bos, DosyaSec, Dugme, IkonDugme, Iskelet, useDinle } from "../ortak";
import { useKurgu } from "../zaman/depo";
import * as K from "../zaman/komutlar";

export type StilVarlikTuru = "motion" | "animasyon" | "karakter" | "gorsel" | "ses";
export type EnBoy = "1:1" | "9:16" | "16:9";

export interface StilVarlikOge {
  id: string;
  ad: string;
  tur: StilVarlikTuru;
  dosya: string;
  orijinal: string;
  poster?: string | null;
  yontem: string;
  sure?: number | null;
  w?: number | null;
  h?: number | null;
  ne_zaman: string;
  etiketler: string[];
  lisans: string;
  kaynak_url: string;
  atif: string;
  eklenme: string;
  kurgu_yolu: string;
  onizleme_url: string;
  indir_url: string;
}

export interface StilVarlikDeposu {
  surum: number;
  yalniz_bunlar: boolean;
  secili_native: string[];
  secili_kutuphane: string[];
  yuklenenler: StilVarlikOge[];
}

export interface NativeOge {
  ad: string;
  tur: string;
  ne_zaman: string;
  sure: number;
  etiketler: string[];
}

export interface KarakterOge {
  ad: string;
  baslik: string;
  ne_zaman: string;
}

export interface KutuphaneMotionOge {
  id: string;
  title: string;
  kind: string;
  file: string;
}

export interface StilVarliklarYanit {
  depo: StilVarlikDeposu;
  katalog: {
    native: NativeOge[];
    karakterler: KarakterOge[];
    motionlar: KutuphaneMotionOge[];
  };
}

interface YuklemeDurum {
  ad: string;
  oran: number;
}

const UZANTILAR: Record<StilVarlikTuru, string> = {
  motion: ".webm,.mov,.mp4,.mkv,.json,.lottie,.gif,.apng,.png,.svg",
  animasyon: ".webm,.mov,.mp4,.mkv,.json,.lottie,.gif,.apng,.png,.svg",
  karakter: ".json,.png,.webp,.jpg,.jpeg,.svg,.webm,.mov,.mp4",
  gorsel: ".png,.jpg,.jpeg,.webp,.svg",
  ses: ".wav,.mp3,.ogg,.m4a,.flac",
};

const TUM_UZANTILAR = [...new Set(Object.values(UZANTILAR).join(",").split(","))].join(",");

const TUR_AD: Record<StilVarlikTuru, string> = {
  motion: "Motion",
  animasyon: "Animasyon",
  karakter: "Karakter",
  gorsel: "Görsel",
  ses: "Ses",
};

const YONTEM_AD: Record<string, string> = {
  alfa: "alfa",
  yesil: "yeşil",
  siyah: "siyah",
  lottie: "lottie",
  gif: "gif",
  svg: "svg",
  karakter_json: "karakter_json",
  ham: "ham",
};

const KATEGORI_CIPLER: [string, string][] = [
  ["", "Tümü"],
  ["motion-animasyon", "Motion / Animasyon"],
  ["karakter", "Karakter"],
  ["gorsel", "Görsel"],
  ["ses", "Ses"],
];

const AILE_CIPLER: [string, string][] = [
  ["", "Hepsi"],
  ["tipografi", "tipografi"],
  ["kart", "kart"],
  ["ikon", "ikon"],
  ["veri", "veri"],
  ["cizim", "cizim"],
  ["parcacik", "parcacik"],
  ["cerceve", "cerceve"],
  ["zemin", "zemin"],
  ["karakter", "karakter"],
  ["motion", "kütüphane"],
];

const GORSEL_UZANTI = /\.(png|jpe?g|webp|svg)$/i;

// Saf yardımcılar (StilPaneli.test.ts bunları doğrudan test eder).
export const kabulUzantilari = (tur: string): string => {
  const temiz = tur.trim().toLocaleLowerCase("tr");
  if (temiz in UZANTILAR) return UZANTILAR[temiz as StilVarlikTuru];
  return TUM_UZANTILAR;
};

export const varlikFiltrele = (liste: StilVarlikOge[], tur: string, arama: string): StilVarlikOge[] => {
  const t = tur.trim().toLocaleLowerCase("tr");
  const kelimeler = arama.toLocaleLowerCase("tr").split(/\s+/).filter(Boolean);
  return liste.filter((v) => {
    if (t && t !== "tumu" && t !== "tümü") {
      if (t === "motion-animasyon" || t === "motion_animasyon" || t === "motion/animasyon") {
        if (v.tur !== "motion" && v.tur !== "animasyon") return false;
      } else if (v.tur !== t) {
        return false;
      }
    }
    if (!kelimeler.length) return true;
    const metin = [v.id, v.ad, v.tur, v.yontem, v.ne_zaman, v.lisans, ...(v.etiketler ?? [])]
      .filter(Boolean)
      .join(" ")
      .toLocaleLowerCase("tr");
    return kelimeler.every((k) => metin.includes(k));
  });
};

export const nativeAile = (o: Pick<NativeOge, "ad" | "tur">): string => {
  const on = o.ad.includes("/") ? o.ad.split("/")[0] : "";
  if (on && on !== "dis") return on;
  return o.tur || on;
};

export const nativeGrupla = (liste: NativeOge[], aile: string, arama: string): NativeOge[] => {
  const a = aile.trim().toLocaleLowerCase("tr");
  const kelimeler = arama.toLocaleLowerCase("tr").split(/\s+/).filter(Boolean);
  return liste.filter((o) => {
    if (a && a !== "hepsi" && a !== "tumu" && a !== "tümü") {
      const oAile = nativeAile(o).toLocaleLowerCase("tr");
      const oTur = (o.tur ?? "").toLocaleLowerCase("tr");
      if (oAile !== a && oTur !== a) return false;
    }
    if (!kelimeler.length) return true;
    const metin = [o.ad, o.tur, o.ne_zaman, ...(o.etiketler ?? [])]
      .filter(Boolean)
      .join(" ")
      .toLocaleLowerCase("tr");
    return kelimeler.every((k) => metin.includes(k));
  });
};

const bicimUrl = (url: string, bicim: "normalize" | "orijinal") =>
  `${url}${url.includes("?") ? "&" : "?"}bicim=${bicim}`;

const VarlikOnizleme: React.FC<{
  v: StilVarlikOge;
  calan: string | null;
  cal: (url: string) => void;
}> = ({ v, calan, cal }) => {
  const [hata, setHata] = useState(false);
  useEffect(() => { setHata(false); }, [v.onizleme_url]);

  if (v.tur === "ses") {
    const aktif = calan === v.onizleme_url;
    return (
      <div className="sv-kart-onizleme">
        <div className="sv-kart-ikon">
          <Volume2 size={20} />
          <Dugme
            onClick={() => cal(v.onizleme_url)}
            title={aktif ? "Sesi durdur" : "Sesi dinle"}
            style={{ minHeight: 22, padding: "2px 7px", fontSize: 11 }}
          >
            {aktif ? <Pause size={12} /> : <Play size={12} />} {aktif ? "Durdur" : "Dinle"}
          </Dugme>
        </div>
      </div>
    );
  }

  if (v.yontem === "karakter_json") {
    return (
      <div className="sv-kart-onizleme">
        <div className="sv-kart-ikon">
          <User size={22} />
          <span>Karakter JSON</span>
        </div>
      </div>
    );
  }

  if (v.yontem === "lottie" && !v.poster) {
    return (
      <div className="sv-kart-onizleme">
        <div className="sv-kart-ikon">
          <Sparkles size={22} />
          <span>Lottie</span>
        </div>
      </div>
    );
  }

  const gorselGoster = !hata && (Boolean(v.poster) || v.tur === "gorsel" || v.yontem === "svg" || GORSEL_UZANTI.test(v.dosya));
  return (
    <div className="sv-kart-onizleme">
      {gorselGoster ? (
        <img src={v.onizleme_url} alt={v.ad} loading="lazy" onError={() => setHata(true)} />
      ) : (
        <div className="sv-kart-ikon">
          {v.tur === "karakter" ? <User size={22} /> : v.tur === "gorsel" ? <ImageIcon size={22} /> : <Film size={22} />}
          <span>{TUR_AD[v.tur]}</span>
        </div>
      )}
    </div>
  );
};

export const StilVarliklari: React.FC<{
  studyo: string;
  stilAd: string;
  degisti?: () => void;
}> = ({ studyo, stilAd, degisti }) => {
  const aktif = useDepo((d) => d.aktif);
  const kurguVar = useKurgu((d) => !!d.kurgu);
  const { bildir, hata, onayla } = useDepo();
  const { calan, cal } = useDinle();

  const [veri, setVeri] = useState<StilVarliklarYanit | null>(null);
  const [yukleniyor, setYukleniyor] = useState(true);
  const [altSekme, setAltSekme] = useState<"yuklu" | "secki">("yuklu");

  // Sekme 1: Yüklü varlıklar durumları
  const [kategori, setKategori] = useState("");
  const [varlikAra, setVarlikAra] = useState("");
  const [yukleTur, setYukleTur] = useState<StilVarlikTuru>("motion");
  const [neZaman, setNeZaman] = useState("");
  const [disKaynak, setDisKaynak] = useState(false);
  const [lisans, setLisans] = useState("");
  const [kaynakUrl, setKaynakUrl] = useState("");
  const [atif, setAtif] = useState("");
  const [yuklemeler, setYuklemeler] = useState<YuklemeDurum[]>([]);
  const [birakUzerinde, setBirakUzerinde] = useState(false);

  // Sekme 2: Native & kütüphane seçkisi durumları
  const [aile, setAile] = useState("");
  const [seckiAra, setSeckiAra] = useState("");
  const [enBoy, setEnBoy] = useState<EnBoy>("1:1");
  const [indirilen, setIndirilen] = useState<Record<string, boolean>>({});
  const [seckiKaydediliyor, setSeckiKaydediliyor] = useState(false);

  const istekNoRef = useRef(0);
  const seckiNoRef = useRef(0);

  const al = useCallback(async () => {
    const no = ++istekNoRef.current;
    try {
      const r: StilVarliklarYanit = await istek(`/api/stil/${studyo}/${encodeURIComponent(stilAd)}/varliklar`);
      if (istekNoRef.current !== no) return;
      setVeri(r);
    } catch (e) {
      if (istekNoRef.current === no) hata(e);
    } finally {
      if (istekNoRef.current === no) setYukleniyor(false);
    }
  }, [studyo, stilAd]);

  useEffect(() => {
    setYukleniyor(true);
    setVeri(null);
    setYuklemeler([]);
    setBirakUzerinde(false);
    al();
  }, [al]);

  const depo = veri?.depo ?? { surum: 1, yalniz_bunlar: false, secili_native: [], secili_kutuphane: [], yuklenenler: [] };
  const katalog = veri?.katalog ?? { native: [], karakterler: [], motionlar: [] };

  const suzulmusVarliklar = useMemo(
    () => varlikFiltrele(depo.yuklenenler, kategori, varlikAra),
    [depo.yuklenenler, kategori, varlikAra],
  );

  const suzulmusNative = useMemo(
    () => (aile === "karakter" || aile === "motion" ? [] : nativeGrupla(katalog.native, aile, seckiAra)),
    [katalog.native, aile, seckiAra],
  );

  const suzulmusKarakter = useMemo(() => {
    if (aile && aile !== "karakter") return [];
    const kelimeler = seckiAra.toLocaleLowerCase("tr").split(/\s+/).filter(Boolean);
    return katalog.karakterler.filter((k) => {
      if (!kelimeler.length) return true;
      const metin = [k.ad, k.baslik, k.ne_zaman].filter(Boolean).join(" ").toLocaleLowerCase("tr");
      return kelimeler.every((w) => metin.includes(w));
    });
  }, [katalog.karakterler, aile, seckiAra]);

  const suzulmusMotion = useMemo(() => {
    if (aile && aile !== "motion") return [];
    const kelimeler = seckiAra.toLocaleLowerCase("tr").split(/\s+/).filter(Boolean);
    return katalog.motionlar.filter((m) => {
      if (!kelimeler.length) return true;
      const metin = [m.id, m.title, m.kind].filter(Boolean).join(" ").toLocaleLowerCase("tr");
      return kelimeler.every((w) => metin.includes(w));
    });
  }, [katalog.motionlar, aile, seckiAra]);

  const dosyalariYukle = async (dosyalar: File[]) => {
    if (!dosyalar.length) return;
    if (disKaynak && !lisans.trim()) {
      bildir("Dış kaynak seçiliyken lisans alanı boş bırakılamaz", true);
      return;
    }
    const etkinLisans = disKaynak ? lisans.trim() : "Kendi üretimim";
    const etkinKaynakUrl = disKaynak ? kaynakUrl.trim() : "";
    const etkinAtif = disKaynak ? atif.trim() : "";

    setYuklemeler(dosyalar.map((d) => ({ ad: d.name, oran: 0 })));
    let basarili = 0;
    for (const [i, d] of dosyalar.entries()) {
      try {
        const q = sor({
          dosya: d.name,
          tur: yukleTur,
          ne_zaman: neZaman.trim(),
          lisans: etkinLisans,
          kaynak_url: etkinKaynakUrl,
          atif: etkinAtif,
        });
        await yukle(`/api/stil/${studyo}/${encodeURIComponent(stilAd)}/varlik?${q}`, d, (oran) =>
          setYuklemeler((l) => l.map((y, k) => (k === i ? { ...y, oran } : y))),
        );
        basarili++;
      } catch (e) {
        hata(new Error(`${d.name}: ${(e as Error).message}`));
      }
    }
    setYuklemeler([]);
    if (basarili) {
      bildir(`${basarili} stil varlığı yüklendi`);
      setNeZaman("");
      await al();
      degisti?.();
    }
  };

  const varlikSil = async (v: StilVarlikOge) => {
    const onay = await onayla({
      baslik: "Stil varlığını sil",
      metin: `${v.ad}\n\nBu varlık '${stilAd}' stilinden kalıcı olarak silinecek.`,
      onay: "Sil",
      tehlike: true,
    });
    if (!onay) return;
    try {
      await istek(`/api/stil/${studyo}/${encodeURIComponent(stilAd)}/varlik/${encodeURIComponent(v.id)}`, { method: "DELETE" });
      bildir(`Varlık silindi: ${v.ad}`);
      await al();
      degisti?.();
    } catch (e) {
      hata(e);
    }
  };

  const timelineUygun = aktif?.studyo === studyo && kurguVar;

  const izHazirla = (tur: "video" | "ses", tercih: "V2" | "A2"): string | null => {
    const k = useKurgu.getState();
    if (!k.kurgu) return null;
    const mevcut = k.kurgu.izler.find((i) => i.id === tercih && i.tur === tur && !i.kilit);
    if (mevcut) return mevcut.id;
    if (!k.kurgu.izler.some((i) => i.id === tercih)) {
      let yeniIz = "";
      k.duzenle(`${tercih} izi ekle`, (f) => { yeniIz = K.izEkle(f, tur); });
      return yeniIz || null;
    }
    return null;
  };

  const timelineaEkle = async (v: StilVarlikOge) => {
    const k = useKurgu.getState();
    if (!aktif || aktif.studyo !== studyo || !k.kurgu) {
      bildir("Önce bu stüdyoda kurgusu olan bir proje aç", true);
      return;
    }
    if (v.tur === "karakter" && v.yontem === "karakter_json") {
      const sure = Math.max(1, v.sure ?? 4);
      let yeniId = "";
      k.duzenle(`${v.ad} ekle`, (f) => {
        const iz = K.bosIz(f, k.zaman, k.zaman + sure);
        yeniId = K.klipEkle(f, {
          tur: "sahne",
          iz,
          bas: k.zaman,
          sure,
          sahne: { kind: "karakter", karakter: v.id, layout: "full", bg: "saydam" },
        })?.id ?? "";
      });
      if (yeniId) k.sec([yeniId]);
      bildir(`${v.ad} karakter sahnesi eklendi`);
      return;
    }
    if (v.yontem === "lottie") {
      const sure = Math.min(6, Math.max(0.8, v.sure ?? 1.5));
      const izId = izHazirla("video", "V2");
      let yeniId = "";
      k.duzenle(`${v.ad} ekle`, (f) => {
        const hedef = izId ?? K.bosIz(f, k.zaman, k.zaman + sure);
        yeniId = K.klipEkle(f, {
          tur: "motion",
          iz: hedef,
          bas: k.zaman,
          sure,
          bilesen: { ad: "dis/lottie", param: { dosya: v.kurgu_yolu, renk: "tema" } },
        })?.id ?? "";
      });
      if (yeniId) k.sec([yeniId]);
      bildir(`${v.ad} timeline'a eklendi`);
      return;
    }
    if (v.tur === "ses") {
      const iz = izHazirla("ses", "A2");
      await k.kaynaktanEkle({ yol: v.kurgu_yolu, ad: v.ad, tur: "ses", sfx: true }, k.zaman, iz, false);
      bildir(`${v.ad} A2 izine eklendi`);
      return;
    }
    const gorselMi = v.tur === "gorsel" || v.yontem === "svg" || (v.tur === "karakter" && GORSEL_UZANTI.test(v.dosya));
    const iz = izHazirla("video", "V2");
    await k.kaynaktanEkle(
      { yol: v.kurgu_yolu, ad: v.ad, tur: gorselMi ? "gorsel" : "motion" },
      k.zaman,
      iz,
      false,
    );
    bildir(`${v.ad} V2 izine eklendi`);
  };

  const seckiKaydet = async (guncel: Partial<Pick<StilVarlikDeposu, "yalniz_bunlar" | "secili_native" | "secili_kutuphane">>) => {
    const no = ++seckiNoRef.current;
    const onceki = veri;
    if (veri) {
      setVeri({ ...veri, depo: { ...veri.depo, ...guncel } });
    }
    setSeckiKaydediliyor(true);
    try {
      const r: { depo: Partial<StilVarlikDeposu> } = await istek(
        `/api/stil/${studyo}/${encodeURIComponent(stilAd)}/secki`,
        { method: "PUT", json: guncel },
      );
      if (seckiNoRef.current !== no) return;
      // WHY: PUT /secki depo.model_dump() döner; yuklenenler içindeki onizleme_url/indir_url alanlarını koru.
      setVeri((mevcut) =>
        mevcut
          ? {
              ...mevcut,
              depo: {
                ...mevcut.depo,
                yalniz_bunlar: r.depo.yalniz_bunlar ?? mevcut.depo.yalniz_bunlar,
                secili_native: r.depo.secili_native ?? mevcut.depo.secili_native,
                secili_kutuphane: r.depo.secili_kutuphane ?? mevcut.depo.secili_kutuphane,
              },
            }
          : mevcut,
      );
    } catch (e) {
      if (seckiNoRef.current === no) setVeri(onceki);
      hata(e);
    } finally {
      if (seckiNoRef.current === no) setSeckiKaydediliyor(false);
    }
  };

  const nativeSecDegis = (bilesenAd: string) => {
    const varMi = depo.secili_native.includes(bilesenAd);
    const yeni = varMi
      ? depo.secili_native.filter((x) => x !== bilesenAd)
      : [...depo.secili_native, bilesenAd];
    seckiKaydet({ secili_native: yeni });
  };

  const kutuphaneSecDegis = (anahtar: string) => {
    const varMi = depo.secili_kutuphane.includes(anahtar);
    const yeni = varMi
      ? depo.secili_kutuphane.filter((x) => x !== anahtar)
      : [...depo.secili_kutuphane, anahtar];
    seckiKaydet({ secili_kutuphane: yeni });
  };

  const nativeIndir = async (o: NativeOge) => {
    setIndirilen((m) => ({ ...m, [o.ad]: true }));
    try {
      const r = await fetch(`/api/stil/${studyo}/${encodeURIComponent(stilAd)}/native-indir`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ad: o.ad, param: {}, en_boy: enBoy }),
      });
      if (!r.ok) {
        const d = await r.json().catch(() => ({}));
        const mesaj = typeof d.detail === "string" ? d.detail : `Native indirme hatası (${r.status})`;
        throw new Error(mesaj);
      }
      const blob = await r.blob();
      const url = URL.createObjectURL(blob);
      const dosyaAdi = `${stilAd}-${o.ad.replace(/\//g, "-")}.webm`;
      const a = document.createElement("a");
      a.href = url;
      a.download = dosyaAdi;
      document.body.appendChild(a);
      a.click();
      a.remove();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
      bildir(`İndirildi: ${dosyaAdi}`);
    } catch (e) {
      hata(e);
    } finally {
      setIndirilen((m) => {
        const k = { ...m };
        delete k[o.ad];
        return k;
      });
    }
  };

  const birak = {
    onDragOver: (e: React.DragEvent) => {
      if (e.dataTransfer.types.includes("Files")) {
        e.preventDefault();
        e.stopPropagation();
        setBirakUzerinde(true);
      }
    },
    onDragLeave: (e: React.DragEvent) => {
      e.stopPropagation();
      if (!e.currentTarget.contains(e.relatedTarget as Node)) setBirakUzerinde(false);
    },
    onDrop: (e: React.DragEvent) => {
      if (e.dataTransfer.files.length) {
        e.preventDefault();
        e.stopPropagation();
        setBirakUzerinde(false);
        dosyalariYukle([...e.dataTransfer.files]);
      }
    },
  };

  if (yukleniyor && !veri) {
    return <Iskelet n={3} />;
  }

  const seciliToplam = depo.secili_native.length + depo.secili_kutuphane.length;

  return (
    <div className="sv-kok">
      <div className="sv-sekmeler" role="tablist" aria-label="Stil varlıkları sekmeleri">
        <button
          type="button"
          role="tab"
          className="sekme"
          aria-selected={altSekme === "yuklu"}
          onClick={() => setAltSekme("yuklu")}
        >
          Yüklü Varlıklar<span className="sayi">{depo.yuklenenler.length}</span>
        </button>
        <button
          type="button"
          role="tab"
          className="sekme"
          aria-selected={altSekme === "secki"}
          onClick={() => setAltSekme("secki")}
        >
          Native &amp; Kütüphane Seçkisi<span className="sayi">{seciliToplam}</span>
        </button>
      </div>

      {altSekme === "yuklu" && (
        <>
          <div className={`sv-yukle ${birakUzerinde ? "uzerinde" : ""}`} {...birak}>
            <div className="sv-yukle-satir">
              <select
                aria-label="Yüklenecek varlık türü"
                value={yukleTur}
                onChange={(e) => setYukleTur(e.target.value as StilVarlikTuru)}
              >
                <option value="motion">Motion</option>
                <option value="animasyon">Animasyon</option>
                <option value="karakter">Karakter</option>
                <option value="gorsel">Görsel</option>
                <option value="ses">Ses</option>
              </select>
              <input
                aria-label="Ne zaman kullanılır?"
                placeholder="Ne zaman kullanılır? (isteğe bağlı)"
                value={neZaman}
                onChange={(e) => setNeZaman(e.target.value)}
                style={{ flex: 1, minWidth: 140 }}
              />
              <DosyaSec kabul={kabulUzantilari(yukleTur)} sec={dosyalariYukle} disabled={!!yuklemeler.length}>
                <Upload size={14} /> Varlık yükle
              </DosyaSec>
            </div>
            <div className="sv-yukle-satir" style={{ justifyContent: "space-between" }}>
              <label className="sv-lisans-onay">
                <input
                  type="checkbox"
                  checked={disKaynak}
                  onChange={(e) => setDisKaynak(e.target.checked)}
                />
                Dış kaynak / lisans ekle
              </label>
              <span className="ipucu">
                {disKaynak ? "Dış kaynak lisansını onayla" : "Varsayılan lisans: Kendi üretimim · sürükleyip bırak"}
              </span>
            </div>
            {disKaynak && (
              <div className="sv-lisans-alan">
                <input
                  aria-label="Lisans"
                  placeholder="Lisans (ör. CC0, Pixabay Content License, MIT)"
                  value={lisans}
                  onChange={(e) => setLisans(e.target.value)}
                />
                <input
                  aria-label="Kaynak adresi"
                  placeholder="Kaynak URL (https://...)"
                  value={kaynakUrl}
                  onChange={(e) => setKaynakUrl(e.target.value)}
                />
                <input
                  aria-label="Atıf metni"
                  placeholder="Atıf metni (gerekirse)"
                  value={atif}
                  onChange={(e) => setAtif(e.target.value)}
                />
              </div>
            )}
            {!!yuklemeler.length && (
              <div style={{ display: "grid", gap: 5 }}>
                {yuklemeler.map((y, i) => (
                  <div key={i}>
                    <div className="ipucu" style={{ display: "flex", justifyContent: "space-between" }}>
                      <span>{y.ad}</span>
                      <span>%{Math.round(y.oran * 100)}</span>
                    </div>
                    <div className="ilerleme"><i style={{ width: `${y.oran * 100}%` }} /></div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="sv-arac">
            <div className="sv-cipler" role="tablist" aria-label="Varlık kategorisi">
              {KATEGORI_CIPLER.map(([kod, etiket]) => {
                const n = varlikFiltrele(depo.yuklenenler, kod, "").length;
                return (
                  <button
                    key={kod || "tumu"}
                    type="button"
                    role="tab"
                    className="sekme"
                    aria-selected={kategori === kod}
                    onClick={() => setKategori(kod)}
                  >
                    {etiket}<span className="sayi">{n}</span>
                  </button>
                );
              })}
            </div>
            <input
              type="search"
              aria-label="Stil varlıklarında ara"
              placeholder="Ara…"
              value={varlikAra}
              onChange={(e) => setVarlikAra(e.target.value)}
              style={{ flex: "1 1 120px", minWidth: 96 }}
            />
          </div>

          {!depo.yuklenenler.length ? (
            <Bos
              baslik="Henüz stile özel varlık yok"
              metin="Yukarıdan motion, animasyon, karakter, görsel veya ses yükleyip bu stile kilitleyebilirsin."
            />
          ) : !suzulmusVarliklar.length ? (
            <Bos baslik="Eşleşen varlık yok" metin="Kategori çipini ya da aramayı değiştir." />
          ) : (
            <div className="sv-izgara">
              {suzulmusVarliklar.map((v) => {
                const boyut = [v.sure != null ? sureYaz(v.sure) : "", v.w && v.h ? `${v.w}×${v.h}` : ""]
                  .filter(Boolean)
                  .join(" · ");
                const ozgunFarkli = Boolean(v.orijinal && v.orijinal !== v.dosya);
                return (
                  <div key={v.id} className="sv-kart">
                    <VarlikOnizleme v={v} calan={calan} cal={cal} />
                    <div className="sv-kart-govde">
                      <span className="sv-kart-ad" title={v.ne_zaman || v.ad}>{v.ad}</span>
                      <div className="sv-kart-rozetler">
                        <span className="rozet">{TUR_AD[v.tur] ?? v.tur}</span>
                        {v.yontem && <span className="rozet vurgu">{YONTEM_AD[v.yontem] ?? v.yontem}</span>}
                        {boyut && <span className="ipucu">{boyut}</span>}
                      </div>
                      {v.ne_zaman && (
                        <span className="sv-secki-alt" title={v.ne_zaman}>{v.ne_zaman}</span>
                      )}
                    </div>
                    <div className="sv-kart-eylemler">
                      <a
                        className="dugme ikon"
                        href={v.indir_url}
                        download
                        title="İndir"
                        aria-label={`${v.ad} varlığını indir`}
                      >
                        <Download size={14} />
                      </a>
                      {ozgunFarkli && (
                        <a
                          className="dugme"
                          href={bicimUrl(v.indir_url, "orijinal")}
                          download
                          title="Özgün yüklenen dosyayı indir"
                          style={{ minHeight: 22, padding: "1px 6px", fontSize: 11 }}
                        >
                          özgün
                        </a>
                      )}
                      <Dugme
                        onClick={() => timelineaEkle(v)}
                        disabled={!timelineUygun}
                        title={timelineUygun ? "Oynatma kafasına ekle" : "Önce bu stüdyoda kurgusu olan bir proje aç"}
                        style={{ flex: 1, minHeight: 24, padding: "2px 6px", fontSize: 11 }}
                      >
                        <Plus size={13} /> Timeline&apos;a ekle
                      </Dugme>
                      <IkonDugme ad={`${v.ad} varlığını sil`} onClick={() => varlikSil(v)}>
                        <Trash2 size={14} />
                      </IkonDugme>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </>
      )}

      {altSekme === "secki" && (
        <>
          <div className={`sv-kural-kutu ${depo.yalniz_bunlar ? "aktif" : ""}`}>
            <label className="sv-lisans-onay" style={{ color: "var(--y1)", fontWeight: 550 }}>
              <input
                type="checkbox"
                checked={depo.yalniz_bunlar}
                disabled={seckiKaydediliyor}
                onChange={(e) => seckiKaydet({ yalniz_bunlar: e.target.checked })}
              />
              Yalnız bu stile seçili/yüklü varlıkları kullan
            </label>
            <span className="ipucu">Açıksa AI edit yalnız işaretli ve yüklü varlıkları kullanır</span>
          </div>

          <div className="sv-arac">
            <input
              type="search"
              aria-label="Native ve kütüphane seçkisinde ara"
              placeholder="Bileşen, karakter, etiket ara…"
              value={seckiAra}
              onChange={(e) => setSeckiAra(e.target.value)}
              style={{ flex: 1, minWidth: 120 }}
            />
            <label style={{ display: "inline-flex", alignItems: "center", gap: 4, fontSize: 12 }}>
              En-boy
              <select
                aria-label="İndirilecek en-boy oranı"
                value={enBoy}
                onChange={(e) => setEnBoy(e.target.value as EnBoy)}
              >
                <option value="1:1">1:1</option>
                <option value="9:16">9:16</option>
                <option value="16:9">16:9</option>
              </select>
            </label>
          </div>

          <div className="sv-cipler" role="tablist" aria-label="Bileşen ailesi">
            {AILE_CIPLER.map(([kod, etiket]) => {
              const n =
                kod === ""
                  ? katalog.native.length + katalog.karakterler.length + katalog.motionlar.length
                  : kod === "karakter"
                    ? katalog.karakterler.length
                    : kod === "motion"
                      ? katalog.motionlar.length
                      : nativeGrupla(katalog.native, kod, "").length;
              if (kod === "zemin" && n === 0) return null;
              return (
                <button
                  key={kod || "hepsi"}
                  type="button"
                  role="tab"
                  className="sekme"
                  aria-selected={aile === kod}
                  onClick={() => setAile(kod)}
                >
                  {etiket}<span className="sayi">{n}</span>
                </button>
              );
            })}
          </div>

          {!suzulmusNative.length && !suzulmusKarakter.length && !suzulmusMotion.length ? (
            <Bos baslik="Eşleşen öğe yok" metin="Aile çipini ya da aramayı değiştir." />
          ) : (
            <div className="sv-secki-liste">
              {!!suzulmusNative.length && (
                <>
                  {!aile && <div className="baslik">Native bileşenler ({suzulmusNative.length})</div>}
                  {suzulmusNative.map((o) => {
                    const secili = depo.secili_native.includes(o.ad);
                    const iniyor = Boolean(indirilen[o.ad]);
                    return (
                      <div key={o.ad} className={`sv-secki-satir ${secili ? "secili" : ""}`}>
                        <input
                          type="checkbox"
                          checked={secili}
                          aria-label={`${o.ad} bileşenini bu stile ekle`}
                          onChange={() => nativeSecDegis(o.ad)}
                        />
                        <div className="sv-secki-bilgi">
                          <span className="sv-secki-ad">
                            {o.ad}
                            {secili && (
                              <span className="rozet vurgu" style={{ marginLeft: 6 }}>
                                <Check size={10} /> seçili
                              </span>
                            )}
                          </span>
                          <span className="sv-secki-alt" title={o.ne_zaman}>
                            {o.tur ? `${o.tur} · ` : ""}{o.sure ? `${o.sure} sn · ` : ""}{o.ne_zaman}
                          </span>
                        </div>
                        <Dugme
                          disabled={iniyor}
                          onClick={() => nativeIndir(o)}
                          title={`${stilAd} temasıyla saydam .webm (${enBoy}) indir`}
                          style={{ minHeight: 24, padding: "2px 7px", fontSize: 11 }}
                        >
                          {iniyor ? <Loader2 size={13} className="sv-donen" /> : <Download size={13} />}
                          {iniyor ? "İndiriliyor…" : "İndir (.webm)"}
                        </Dugme>
                      </div>
                    );
                  })}
                </>
              )}

              {!!suzulmusKarakter.length && (
                <>
                  {!aile && <div className="baslik">Global karakterler ({suzulmusKarakter.length})</div>}
                  {suzulmusKarakter.map((k) => {
                    const anahtar = `karakter:${k.ad}`;
                    const secili = depo.secili_kutuphane.includes(anahtar);
                    return (
                      <div key={anahtar} className={`sv-secki-satir ${secili ? "secili" : ""}`}>
                        <input
                          type="checkbox"
                          checked={secili}
                          aria-label={`${k.baslik || k.ad} karakterini bu stile bağla`}
                          onChange={() => kutuphaneSecDegis(anahtar)}
                        />
                        <div className="sv-secki-bilgi">
                          <span className="sv-secki-ad">
                            {k.baslik || k.ad} <span className="ipucu">({anahtar})</span>
                          </span>
                          {k.ne_zaman && <span className="sv-secki-alt" title={k.ne_zaman}>{k.ne_zaman}</span>}
                        </div>
                        <span className="rozet">karakter</span>
                      </div>
                    );
                  })}
                </>
              )}

              {!!suzulmusMotion.length && (
                <>
                  {!aile && <div className="baslik">Kütüphane motion&apos;ları ({suzulmusMotion.length})</div>}
                  {suzulmusMotion.map((m) => {
                    const anahtar = `motion:${m.id}`;
                    const secili = depo.secili_kutuphane.includes(anahtar);
                    return (
                      <div key={anahtar} className={`sv-secki-satir ${secili ? "secili" : ""}`}>
                        <input
                          type="checkbox"
                          checked={secili}
                          aria-label={`${m.title || m.id} kütüphane varlığını bu stile bağla`}
                          onChange={() => kutuphaneSecDegis(anahtar)}
                        />
                        <div className="sv-secki-bilgi">
                          <span className="sv-secki-ad">
                            {m.title || m.id} <span className="ipucu">({anahtar})</span>
                          </span>
                          {m.kind && <span className="sv-secki-alt">{m.kind}</span>}
                        </div>
                        <span className="rozet">motion</span>
                      </div>
                    );
                  })}
                </>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
};
