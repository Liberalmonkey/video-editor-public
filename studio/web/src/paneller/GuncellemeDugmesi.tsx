// WHY: bkz. wiki/decisions/0065-uygulama-guncelleme.md
// Stüdyo üst çubuğunda uygulama güncelleme durumu, önizleme ve bitti diyalogları.
import { AlertTriangle, ArrowUpCircle, Check, Loader2, RotateCw } from "lucide-react";
import React, { useCallback, useEffect, useRef, useState } from "react";
import { ApiHata, istek } from "../api";
import { Diyalog, Dugme } from "../ortak";
import { useKurgu } from "../zaman/depo";

export interface YeniCommit {
  kisa: string;
  baslik: string;
  tarih?: string;
}

export interface GuncellemeSonuc {
  ts: string;
  durum: "basarili" | "uyari" | "hata";
  ozet: string;
  korunan?: string[];
  rapor?: string;
  geri_alinabilir?: boolean;
  yeniden_baslat?: boolean;
}

export interface GuncellemeDurum {
  destek: boolean;
  dal?: string;
  hedef?: string;
  mevcut?: string;
  uzak?: string;
  geride?: number;
  ileride?: number;
  yeni?: YeniCommit[];
  kirli?: string[];
  mesgul?: string[];
  son_kontrol?: string | null;
  hata?: string | null;
  calisiyor?: boolean;
  son_sonuc?: GuncellemeSonuc | null;
}

export type GorunumTuru = "gizli" | "guncel" | "yeni" | "calisiyor" | "hata" | "bitti";

export interface GuncellemeGorunum {
  tur: GorunumTuru;
  etiket: string;
  ipucu: string;
}

const zamanMetni = (iso?: string | null): string => {
  if (!iso) return "";
  return iso.replace("T", " ").slice(0, 16);
};

// WHY: bkz. wiki/decisions/0065-uygulama-guncelleme.md
// Saf görünüm hesabı: bileşenden bağımsız olarak birim testle doğrulanır.
export function gorunum(d: GuncellemeDurum | null | undefined): GuncellemeGorunum {
  if (!d || !d.destek) return { tur: "gizli", etiket: "", ipucu: "" };
  if (d.calisiyor) {
    return { tur: "calisiyor", etiket: "Güncelleniyor", ipucu: "Uygulama güncellemesi sürüyor" };
  }
  if (d.son_sonuc?.yeniden_baslat) {
    return {
      tur: "bitti",
      etiket: "Yeniden başlat",
      ipucu: d.son_sonuc.ozet || "Güncelleme tamamlandı; yeniden başlatma gerekiyor",
    };
  }
  const hata = d.hata?.trim();
  if (hata) {
    return { tur: "hata", etiket: "Güncelleme", ipucu: hata };
  }
  const geride = d.geride ?? 0;
  if (geride > 0) {
    const kontrol = zamanMetni(d.son_kontrol);
    return {
      tur: "yeni",
      etiket: "Güncelle",
      ipucu: `${geride} yeni değişiklik var${kontrol ? ` · Son kontrol: ${kontrol}` : ""}`,
    };
  }
  const kontrol = zamanMetni(d.son_kontrol);
  return {
    tur: "guncel",
    etiket: "Güncel",
    ipucu: kontrol ? `Son kontrol: ${kontrol}` : "Güncelleme kontrolü için tıkla",
  };
}

const hataYaz = (e: unknown): string => {
  if (e instanceof ApiHata) return e.message;
  if (e instanceof Error) return e.message;
  return String(e);
};

export const GuncellemeDugmesi: React.FC = () => {
  const [durum, setDurum] = useState<GuncellemeDurum | null>(null);
  const [diyalog, setDiyalog] = useState<null | "onizle" | "bitti">(null);
  const [kontrolEdiliyor, setKontrolEdiliyor] = useState(false);
  const [islemde, setIslemde] = useState(false);
  const [diyalogHata, setDiyalogHata] = useState<string | null>(null);
  const [yenidenBasliyor, setYenidenBasliyor] = useState(false);

  const kayit = useKurgu((s) => s.kayit);
  const kurguVar = useKurgu((s) => s.kurgu !== null);
  const oncekiCalisiyor = useRef(false);

  const durumAl = useCallback(async () => {
    try {
      const veri = await istek<GuncellemeDurum>("/api/guncelleme/durum");
      setDurum(veri);
    } catch {
      // Sunucu geçici erişilemezse düğme sessizce eski durumda kalır.
    }
  }, []);

  const kontrolEt = useCallback(async () => {
    setKontrolEdiliyor(true);
    try {
      const veri = await istek<GuncellemeDurum>("/api/guncelleme/kontrol", { method: "POST" });
      setDurum(veri);
    } catch {
      // Hata sunucudan durum.hata olarak döner; ağ hatasında sessiz kal.
    } finally {
      setKontrolEdiliyor(false);
    }
  }, []);

  // Açılışta durum oku, 10 dk'da bir tazele; açılıştan 5 sn sonra bir kez uzak kontrol yap.
  useEffect(() => {
    let iptal = false;
    const oku = () => {
      istek<GuncellemeDurum>("/api/guncelleme/durum")
        .then((veri) => { if (!iptal) setDurum(veri); })
        .catch(() => {});
    };
    oku();
    const aralik = window.setInterval(oku, 600_000);
    const ilkKontrol = window.setTimeout(() => {
      if (iptal) return;
      istek<GuncellemeDurum>("/api/guncelleme/kontrol", { method: "POST" })
        .then((veri) => { if (!iptal) setDurum(veri); })
        .catch(() => {});
    }, 5_000);
    return () => {
      iptal = true;
      window.clearInterval(aralik);
      window.clearTimeout(ilkKontrol);
    };
  }, []);

  // Güncelleme sürerken 3 sn'de bir durum yokla; bittiğinde durdur ve sonuç diyaloğunu aç.
  const calisiyor = Boolean(durum?.calisiyor);
  useEffect(() => {
    if (oncekiCalisiyor.current && !calisiyor && durum?.son_sonuc) {
      setDiyalogHata(null);
      setYenidenBasliyor(false);
      setDiyalog("bitti");
    }
    oncekiCalisiyor.current = calisiyor;
  }, [calisiyor, durum?.son_sonuc]);

  useEffect(() => {
    if (!calisiyor) return;
    let iptal = false;
    const t = window.setInterval(() => {
      istek<GuncellemeDurum>("/api/guncelleme/durum")
        .then((veri) => { if (!iptal) setDurum(veri); })
        .catch(() => {});
    }, 3_000);
    return () => {
      iptal = true;
      window.clearInterval(t);
    };
  }, [calisiyor]);

  const g = gorunum(durum);
  if (g.tur === "gizli") return null;

  const geride = durum?.geride ?? 0;
  const yeniListe = durum?.yeni ?? [];
  const kirli = durum?.kirli ?? [];
  const mesgul = durum?.mesgul ?? [];
  const sonSonuc = durum?.son_sonuc ?? null;
  const kaydedilmemisKurgu = kurguVar && kayit !== "kayitli";
  const guncelleEngelli = mesgul.length > 0 || kaydedilmemisKurgu;

  const dugmeTikla = () => {
    if (g.tur === "yeni") {
      setDiyalogHata(null);
      setDiyalog("onizle");
      void durumAl();
      return;
    }
    if (g.tur === "bitti") {
      setDiyalogHata(null);
      setYenidenBasliyor(false);
      setDiyalog("bitti");
      return;
    }
    if (g.tur === "calisiyor") {
      window.dispatchEvent(new CustomEvent("studio-panel", { detail: "isler" }));
      return;
    }
    if (!kontrolEdiliyor) void kontrolEt();
  };

  const uygula = async () => {
    setIslemde(true);
    setDiyalogHata(null);
    try {
      await istek("/api/guncelleme/uygula", { method: "POST" });
      setDiyalog(null);
      setDurum((onceki) => (onceki ? { ...onceki, calisiyor: true } : onceki));
    } catch (e) {
      setDiyalogHata(hataYaz(e));
    } finally {
      setIslemde(false);
    }
  };

  const yenidenBaslat = async () => {
    setIslemde(true);
    setDiyalogHata(null);
    try {
      await istek("/api/guncelleme/yeniden-baslat", { method: "POST" });
      setYenidenBasliyor(true);
      try {
        window.close();
      } catch {
        // Tarayıcı betikle pencere kapatmaya izin vermeyebilir.
      }
    } catch (e) {
      setDiyalogHata(hataYaz(e));
    } finally {
      setIslemde(false);
    }
  };

  const geriAl = async () => {
    if (!sonSonuc?.ts) return;
    setIslemde(true);
    setDiyalogHata(null);
    try {
      const veri = await istek<GuncellemeDurum>("/api/guncelleme/geri-al", {
        method: "POST",
        json: { ts: sonSonuc.ts },
      });
      setDurum(veri);
      setDiyalog(null);
    } catch (e) {
      setDiyalogHata(hataYaz(e));
    } finally {
      setIslemde(false);
    }
  };

  const ikon = () => {
    if (g.tur === "calisiyor" || kontrolEdiliyor) return <Loader2 size={13} className="guncelle-donen" aria-hidden="true" />;
    if (g.tur === "hata") return <AlertTriangle size={13} aria-hidden="true" />;
    if (g.tur === "yeni") return <ArrowUpCircle size={13} aria-hidden="true" />;
    if (g.tur === "bitti") return <RotateCw size={13} aria-hidden="true" />;
    return <Check size={12} aria-hidden="true" />;
  };

  const kapat = () => {
    if (islemde) return;
    setDiyalog(null);
    setDiyalogHata(null);
  };

  const ariaEtiket = g.ipucu ? `${g.etiket}: ${g.ipucu}` : g.etiket;

  return (
    <>
      <button
        type="button"
        className={`guncelle-dugme guncelle-${g.tur}`}
        title={g.ipucu}
        aria-label={ariaEtiket}
        aria-busy={g.tur === "calisiyor" || kontrolEdiliyor}
        disabled={kontrolEdiliyor}
        onClick={dugmeTikla}
      >
        {ikon()}
        <span>{g.etiket}</span>
      </button>

      <Diyalog acik={diyalog === "onizle"} kapat={kapat}>
        <h2>Yeni sürüm: {geride} değişiklik</h2>
        {yeniListe.length > 0 && (
          <ul className="guncelle-liste" aria-label="Yeni değişiklikler">
            {yeniListe.map((c) => (
              <li key={c.kisa} className="guncelle-commit">
                <code className="guncelle-kisa">{c.kisa}</code>
                <span className="guncelle-baslik">{c.baslik}</span>
                {c.tarih && <span className="guncelle-tarih">{c.tarih}</span>}
              </li>
            ))}
          </ul>
        )}
        <p className="guncelle-not">
          Projelerin (Projeler/) ve senin kural, kaizen, stil dosyaların korunur. Önce yedek alınır, istersen geri alabilirsin.
        </p>
        {kirli.length > 0 && (
          <div className="guncelle-bilgi-kutu">
            {kirli.length} yerel değişiklik saklanıp geri konacak
          </div>
        )}
        {kaydedilmemisKurgu && (
          <div className="guncelle-uyari" role="alert">
            Önce kurguyu kaydet
          </div>
        )}
        {mesgul.length > 0 && (
          <div className="guncelle-uyari" role="alert">
            <strong>Şu işler bitmeden güncelleme başlatılamaz:</strong>
            <ul className="guncelle-nedenler">
              {mesgul.map((m, i) => <li key={i}>{m}</li>)}
            </ul>
          </div>
        )}
        {diyalogHata && (
          <div className="guncelle-hata-kutu" role="alert">
            {diyalogHata}
          </div>
        )}
        <div className="eylemler">
          <Dugme onClick={kapat} disabled={islemde} autoFocus>Vazgeç</Dugme>
          <Dugme tur="birincil" disabled={guncelleEngelli || islemde} onClick={uygula}>
            {islemde ? "Başlatılıyor…" : "Güncelle"}
          </Dugme>
        </div>
      </Diyalog>

      <Diyalog acik={diyalog === "bitti" && Boolean(sonSonuc)} kapat={kapat}>
        {sonSonuc && (
          <>
            <h2>
              {sonSonuc.durum === "hata"
                ? "Güncelleme başarısız"
                : sonSonuc.durum === "uyari"
                  ? "Güncelleme uyarıyla tamamlandı"
                  : "Güncelleme tamamlandı"}
            </h2>
            <p>{sonSonuc.ozet}</p>
            {sonSonuc.durum === "uyari" && (
              <div className="guncelle-uyari" role="status">
                Güncelleme sırasında uyarı oluştu.{sonSonuc.rapor ? ` Ayrıntı: ${sonSonuc.rapor}` : ""}
              </div>
            )}
            {sonSonuc.durum === "hata" && (
              <div className="guncelle-hata-kutu" role="alert">
                Güncelleme hata ile sonlandı.{sonSonuc.rapor ? ` Ayrıntı: ${sonSonuc.rapor}` : ""}
              </div>
            )}
            {sonSonuc.korunan && sonSonuc.korunan.length > 0 && (
              <div className="guncelle-korunan-blok">
                <span className="guncelle-korunan-baslik">Korunan dosyalar</span>
                <ul className="guncelle-korunan">
                  {sonSonuc.korunan.map((dosya) => <li key={dosya}>{dosya}</li>)}
                </ul>
              </div>
            )}
            {yenidenBasliyor && (
              <div className="guncelle-bilgi-kutu" role="status">
                Yeni pencere açılıyor, bunu kapatabilirsin
              </div>
            )}
            {diyalogHata && (
              <div className="guncelle-hata-kutu" role="alert">
                {diyalogHata}
              </div>
            )}
            <div className="eylemler">
              <Dugme onClick={kapat} disabled={islemde}>Kapat</Dugme>
              {sonSonuc.geri_alinabilir !== false && sonSonuc.ts && (
                <Dugme tur="tehlike" disabled={islemde || yenidenBasliyor} onClick={geriAl}>
                  Geri al
                </Dugme>
              )}
              <Dugme tur="birincil" disabled={islemde || yenidenBasliyor} onClick={yenidenBaslat} autoFocus>
                Yeniden başlat
              </Dugme>
            </div>
          </>
        )}
      </Diyalog>
    </>
  );
};
