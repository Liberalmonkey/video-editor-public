"""kurgu.json: oku, atomik yaz, eski projeden al, render girdilerini üret.

WHY: bkz. wiki/decisions/0021-video-studyo-nle.md. Kurgu tek doğruluk kaynağıdır; final kuyruğu
(olaysesi, teslim, denetim) değişmesin diye render için props ve olaylar dosyaları buradan üretilir.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import tempfile
import time
import uuid
from pathlib import Path

from . import ff, fizik, hazir_efekt, hf_grafik, karakter, motion, native_motion, paths
from . import stil as stil_mod
from .schemas import METIN_TIPLERI, SAHNE_TURLERI, SAHNE_ZEMINLERI, VURGU_BICIMLERI, Kurgu, KurguKaynak

GECMIS = 20
GORSEL = {".png", ".jpg", ".jpeg", ".webp"}  # hizli.GORSEL ile aynı; hizli bu modülü içe aldığı için burada
ORTA_GECIS = ("sil", "kay", "saat", "iris", "kirbac", "isik", "piksel", "zoom_kirbac", "film_yanigi", "bolunme", "bozulma", "yirtma",
              "tikla_iris", "buton_zoom", "kart_dunyaya", "bulanik_takas", "dip_kesim")
GUCLU_GECIS = {"kirbac", "kay", "zoom_kirbac", "bozulma", "buton_zoom", "kart_dunyaya"}


class RevCakismasi(Exception):
    """Dosya, istemcinin okuduğu sürümden sonra değişti."""


def yol(work: Path) -> Path:
    return work / "edit" / "kurgu.json"


def etag(work: Path) -> str:
    """Dosya içeriğinin özeti; dosya yoksa boş."""
    f = yol(work)
    return hashlib.sha1(f.read_bytes()).hexdigest() if f.exists() else ""


def kaynak_kelimeleri(p, f: Path) -> list[dict]:
    """vedit hazirla transkripti varsa kaynağın kelimeleri; yoksa boş."""
    t = p.work / "analysis" / "transcript.json"
    if not t.exists():
        return []
    d = json.loads(t.read_text(encoding="utf-8")).get("files", {}).get(f.stem)
    return [{"w": w["w"], "s": w["s"], "e": w["e"]} for g in d["segments"] for w in g["words"]] if d else []


def oku(work: Path) -> Kurgu:
    return Kurgu.model_validate_json(yol(work).read_text(encoding="utf-8"))


def _atomik(hedef: Path, metin: str) -> None:
    hedef.parent.mkdir(parents=True, exist_ok=True)
    gecici = hedef.with_name(f".{hedef.name}.{uuid.uuid4().hex[:8]}.tmp")
    gecici.write_text(metin, encoding="utf-8")
    # WHY: Windows'ta hedefi o an okuyan süreç varsa (Stüdyo durum.json ve kurgu.json'u yoklar) os.replace
    # PermissionError verir; ekip akışı bu yüzden düşmesin, okuma bitene kadar kısa aralıkla yeniden denenir.
    for deneme in range(40):
        try:
            os.replace(gecici, hedef)
            return
        except PermissionError:
            if deneme == 39:
                gecici.unlink(missing_ok=True)
                raise
            time.sleep(0.05)


def yaz(work: Path, k: Kurgu, *, beklenen_rev: int | None = None) -> Kurgu:
    """Rev denetimli atomik yazma. Önceki sürüm kurgu-gecmis/ altına alınır (son 20)."""
    f = yol(work)
    if f.exists():
        eski = oku(work)
        if beklenen_rev is not None and eski.rev != beklenen_rev:
            raise RevCakismasi(f"dosya rev {eski.rev}, istemci {beklenen_rev}")
        gecmis = work / "edit" / "kurgu-gecmis"
        gecmis.mkdir(exist_ok=True)
        shutil.copy2(f, gecmis / f"{eski.rev:06}.json")
        for fazla in sorted(gecmis.glob("*.json"))[:-GECMIS]:
            fazla.unlink()
        k = k.model_copy(update={"rev": eski.rev + 1})
    _atomik(f, k.model_dump_json(indent=1, exclude_defaults=False))
    return k


def izdusum(k: Kurgu) -> list[dict]:
    """Altyazı izindeki kliplerden sekans zamanlı kelimeler. Studio Kurgu.tsx izdusum ile aynı kuraldır."""
    if not k.altyazi.acik:
        return []
    cikti = []
    # WHY: altyazı sesi izler; bkz. wiki/decisions/0022-av-ayirma-metre-yatay.md
    klipler = (c for c in k.klipler if c.kaynak and ((c.olay or {}).get("konusma") or (c.iz == k.altyazi.iz and not c.ses_kapali)))
    for c in sorted(klipler, key=lambda c: c.bas):
        bit = c.giris + c.sure * c.hiz
        for w in k.kelimeler.get(c.kaynak, []):
            if c.giris <= w.s < bit:
                cikti.append({"w": w.w, "s": round(c.bas + (w.s - c.giris) / c.hiz, 3),
                              "e": round(c.bas + (min(w.e, bit) - c.giris) / c.hiz, 3)})
    return cikti


def _zarf(c) -> list | None:
    """Kazanç keyframe'leri olaysesi için: sabit kazanca göre dB farkı, klip başından."""
    return [[round(f.t, 3), round(f.v - c.ses.gain_db, 2)] for f in sorted(c.ses.kf, key=lambda f: f.t)] if c.ses.kf else None


def olaylar_uret(k: Kurgu, p) -> dict:
    """Ses izleri → olaysesi girdisi. Ayrık ses yoksa `ses` alanı yok: konuşma ham.mp4'ten gelir."""
    izler = {i.id: i for i in k.izler}
    olaylar, muzik, ses = [], [], []
    for c in sorted((c for c in k.klipler if c.tur == "ses" and not izler[c.iz].sessiz), key=lambda c: c.bas):
        yer = _ses_yolu(p, k.kaynaklar[c.kaynak].yol) if c.kaynak else None
        o = c.olay or {}
        gain = c.ses.gain_db + izler[c.iz].gain_db
        if o.get("konusma") and yer:
            ses.append({"src": yer, "start": round(c.bas, 3), "in": round(c.giris, 3), "dur": round(c.sure, 3), "gain_db": gain,
                        "fade_in": c.ses.fade_in, "fade_out": c.ses.fade_out, **({"zarf": _zarf(c)} if c.ses.kf else {})})
            continue
        if o.get("muzik"):
            muzik.append({"src": yer, "gain_db": gain, "duck": c.ses.duck,
                          "fade_in": c.ses.fade_in, "fade_out": c.ses.fade_out,
                          "start": round(c.bas, 3), "in": round(c.giris, 3), "dur": round(c.sure, 3), **({"zarf": _zarf(c)} if c.ses.kf else {})})
            continue
        kayit = {"t": round(c.bas, 3), "tur": o.get("tur", "sfx")}
        if yer:
            # WHY: kaynaklı klip timeline'daki yerinde, kırpımıyla çalar. Slop olay ölçümü için olay olarak kalır.
            kayit.update(dosya=yer, gain_db=gain, kesin=True, dur=round(c.sure, 3), fade_in=c.ses.fade_in, fade_out=c.ses.fade_out)
            kayit["in"] = round(c.giris, 3)
            if c.ses.kf:
                kayit["zarf"] = _zarf(c)
        elif gain:  # dosyası olmayan olayın gücünü olaysesi seçer; 0 yazmak sesi tam güce çıkarırdı
            kayit["gain_db"] = gain
        for ek in ("sure", "not", "guc"):
            if o.get(ek) is not None:
                kayit[ek] = o[ek]
        olaylar.append(kayit)
    # WHY: bkz. wiki/decisions/0033-hazir-efektler.md. Hazır efektin sesi ses izinde klip olmadan rol olayı olarak gelir.
    # WHY: bkz. wiki/decisions/0039-fizik-ritim-galeri.md. Fizik temasının sesi bake'teki temas karesinden gelir.
    # WHY: bkz. wiki/decisions/0062-modern-hyperframes-motion-mimarisi.md. HF kompozisyon ses ipuçları +1 kare senkron.
    olaylar = sorted(olaylar + hazir_efekt.ses_olaylari(k) + fizik.ses_olaylari(p, k) + hf_grafik.ses_olaylari(p, k), key=lambda o: o["t"])
    # WHY: bkz. wiki/decisions/0045-native-motion.md. Orta noktalı geçişin sesi orta noktada (kesimde) çalar;
    # editör aynı yere geçiş sesi koyduysa ikinci kez eklenmez. Ses dosyasını ve seviyeyi olaysesi seçer (ADR 0032).
    orta = set(ORTA_GECIS)
    for c in k.klipler:
        g = c.gecis_giris
        if c.iz in izler and not izler[c.iz].gizli and g and g.tur in orta:
            if not any(o["tur"].startswith("gecis") and abs(o["t"] - c.bas) < 0.25 for o in olaylar):
                guclu = g.tur in GUCLU_GECIS
                olaylar.append({"t": round(c.bas, 3), "tur": "gecis_guclu" if guclu else "gecis",
                                "guc": "orta" if guclu else "yumusak"})
    olaylar.sort(key=lambda o: o["t"])
    video = "../renders/ham.mp4"
    cikti = {"video": video, "fps": k.sekans.fps, "studyo": p.studyo, "olaylar": olaylar, "muzik": muzik}
    # Konuşma temizliği sekans aralığıdır: ham.mp4'teki ses de ayrık ses de aynı konuşma busunda temizlenir.
    temiz = [[round(c.bas, 3), round(c.bas + c.sure, 3)] for c in k.klipler if c.ses.temizle and c.kaynak and not izler[c.iz].sessiz
             and ((c.tur == "video" and not c.ses_kapali) or (c.olay or {}).get("konusma"))]
    if temiz:
        cikti["temizle"] = temiz
    if ses:
        # WHY: `ses` verilince olaysesi ham.mp4'ü kendi almaz; ayrılmamış klipler varsa ham da konuşma busına girer.
        bagli = any(c.tur == "video" and c.kaynak and not c.ses_kapali and not izler[c.iz].sessiz and k.kaynaklar[c.kaynak].ses for c in k.klipler)
        cikti["ses"] = ([{"src": video}] if bagli else []) + ses
    return cikti


def _ses_yolu(p, y: str) -> str:
    """olaysesi `_bul`: kök göreli ya da mutlak yol kabul eder. Proje kökleri mutlak gider."""
    kok, _, ic = y.partition(":")
    return f"library/{ic}" if kok == "library" else str(dosya(p, y))


def hazirla(p, *, mod: str = "final") -> Path:
    """kurgu.json → edit/kurgu.render.json + edit/olaylar.json + work/public/_k hardlink'leri.

    `mod`: "taslak" ağır kaynakta hazır proxy'yi bağlar; "final" ve "master" orijinali (HDR'de SDR kopyası) bağlar ve
    conform kapısını çalıştırır; "master" HDR kopyasını yüksek kalitede üretir. WHY: ADR 0060.
    """
    k = oku(p.work)
    hatalar = denetle(p, k)
    if hatalar:
        raise SystemExit("Kurgu render edilemez:\n  " + "\n  ".join(hatalar))
    from . import hf_kurgu
    canli_hf = k.motor != "remotion" and (k.motor == "hf" or bool(hf_kurgu.ayar().get("oto_hf")))
    motion_bagla(p, k, canli_hf=canli_hf)  # bellekte: elle değişen şablon parametresi render'da da güncel olsun
    fizik.bagla(p, k)  # fizik sahnesi bake JSON'u; parametre değiştiyse yeniden hesaplanır (ADR 0039)
    karakter.bagla(p, k)  # konuşan karakterin ağız ve jest verisi; ses değiştiyse yeniden yazılır
    ses_izleri = {i.id for i in k.izler if i.tur == "ses"}
    gizli = {i.id for i in k.izler if i.gizli}
    gorunen = [c for c in k.klipler if c.iz not in ses_izleri and c.iz not in gizli and c.tur != "ses"]
    if not gorunen:
        raise SystemExit("Kurguda görüntü klibi yok.")
    bitis = max(c.bas + c.sure for c in k.klipler if c.iz not in gizli)
    beklenen: dict[str, Path] = {}
    vekiller: list[str] = []
    for ad, kaynak in k.kaynaklar.items():
        if any(c.kaynak == ad for c in gorunen):
            bag = _public_bagla(p, ad, kaynak.yol, mod=mod)
            if bag:
                beklenen[bag[0]] = bag[1]
                if bag[2]:
                    vekiller.append(ad)
    _conform_yaz(p, mod, beklenen, vekiller)
    stil = k.altyazi.stil
    if stil and stil.dosya:
        # WHY: özel font render'da da bulunsun; yol kök içinde kalır (dosya()).
        hedef = p.work / "public" / "fonts" / Path(stil.dosya).name
        if not hedef.exists():
            hedef.parent.mkdir(parents=True, exist_ok=True)
            hedef.hardlink_to(dosya(p, f"library:fonts/{Path(stil.dosya).name}"))
    render = k.model_dump()
    render.pop("rev")  # WHY: rev değişimi tek başına görüntü render'ı tetiklemesin (ham_imzasi)
    render.pop("kelimeler")
    render.pop("isaretler")  # görüntüyü etkilemez
    render.pop("motion_tema")  # etkisi şablon kaynağının özetinde; tek başına render tetiklemesin
    for iz in render["izler"]:  # WHY: kilit ve ad görüntüyü değiştirmez, render tetiklemesin
        iz.pop("kilit"), iz.pop("ad")
    render["klipler"] = [c.model_dump() for c in gorunen]
    for c in render["klipler"]:
        for s in _gorselli_sahneler(c):
            _sahne_gorseli(p, k, s)
        b = c.get("bilesen") or {}
        if b.get("ad") == "dis/lottie" and str((b.get("param") or {}).get("dosya", "")).startswith(("library:", "stil:")):
            # WHY: ADR 0046. Render tarayıcısı yalnız public'i görür; Lottie JSON'u oraya bağlanır, param yolu çevrilir.
            kay = dosya(p, b["param"]["dosya"])
            hedef = p.work / "public" / "dis" / f"{kay.parent.name}{kay.suffix}"
            if not hedef.exists():
                hedef.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(kay, hedef)
            b["param"]["dosya"] = f"public:dis/{hedef.name}"
    render["tema"] = tema_tokeni(p, k)  # WHY: ADR 0043, bileşenler sabit renk yerine stilin token'ını okur
    if (bol := yuz_bolgeleri(p, k)) is not None:
        render["bolgeler"] = bol
    render["words"] = izdusum(k)
    render["bitis"] = bitis
    cikti = p.work / "edit" / "kurgu.render.json"
    _atomik(cikti, json.dumps(render, ensure_ascii=False))
    _atomik(p.work / "edit" / "olaylar.json", json.dumps(olaylar_uret(k, p), ensure_ascii=False, indent=1))
    return cikti


def yuz_bolgeleri(p, k: Kurgu) -> dict | None:
    """Native grafiklerin kaçınacağı yüz kutuları; native klip yoksa ya da model kurulu değilse None.

    WHY: ADR 0045. Render ve Stüdyo önizlemesi aynı yerleşimi seçsin: önizleme eskiden bölgesiz çalışıyor, ikon yüzün
    üstüne konuyordu (instagram/1, 24,8 sn); render'da yüzden kaçıyordu. Ölçüm önbelleklidir.
    """
    from . import yuz_bolge
    if not any(c.bilesen for c in k.klipler) or not yuz_bolge.model_var():
        return None
    return {"yuzler": yuz_bolge.hesapla(p, k)}


def dosya(p, y: str) -> Path:
    """Kaynak yolunu diske çöz. Kök dışı yolu reddeder."""
    kok, _, ic = y.partition(":")
    if kok == "stil":
        norm = ic.replace("\\", "/")
        if ".." in Path(norm).parts or norm.startswith("/"):
            raise ValueError(f"Kök dışı yol: {y}")
        parcalar = [x for x in norm.split("/") if x and x != "."]
        if len(parcalar) < 3:
            raise ValueError(f"Geçersiz stil yolu (stil:<stüdyo>/<stil>/<alt_yol> bekleniyor): {y}")
        studios_taban = paths.STUDIOS.resolve()
        stil_taban = (paths.STUDIOS / parcalar[0] / "styles" / parcalar[1]).resolve()
        if not stil_taban.is_relative_to(studios_taban):
            raise ValueError(f"Kök dışı yol: {y}")
        hedef = (stil_taban / "/".join(parcalar[2:])).resolve()
        if not hedef.is_relative_to(stil_taban):
            raise ValueError(f"Kök dışı yol: {y}")
        return hedef
    koks = {"public": p.work / "public", "inputs": p.girdi, "library": paths.LIBRARY}
    if kok not in koks:
        raise ValueError(f"Bilinmeyen kök: {kok}")
    taban = koks[kok].resolve()
    hedef = (taban / ic).resolve()
    if not hedef.is_relative_to(taban):
        raise ValueError(f"Kök dışı yol: {y}")
    return hedef


def shot_bagla(p, f: Path) -> dict:
    """Sahne görseli: dosyayı work/public/shot altına bağlar (sahne staticFile ile okur). Stüdyo API'si ve hazirla kullanır."""
    hedef = p.work / "public" / "shot" / f.name
    hedef.parent.mkdir(parents=True, exist_ok=True)
    if not (hedef.exists() and hedef.samefile(f)):
        hedef.unlink(missing_ok=True)
        hedef.hardlink_to(f)
    v = ff.probe(f).get("video") or {}
    return {"img": f"shot/{f.name}", "iw": v.get("width"), "ih": v.get("height")}


# WHY: bkz. wiki/decisions/0042-stil-katalogu-ve-video-temasi.md. "varsayilan" (şema varsayılanı) "otomatik" demektir;
# turuncu her videoya düşmesin. Açık turuncu isteyen `turuncu` temasını yazar.
OTOMATIK_TEMA = {"", "varsayilan"}
PROJE_TEMASI = "proje"


def etkin_tema(p, ad: str | None) -> str | Path:
    """Motion teması: açık tema > seçili stilin `tokens.json → motion_tema` > proje teması (`tema-cikar`) > varsayilan."""
    proje_css = p.work / "edit" / "motion_tema.css"
    if ad == PROJE_TEMASI:
        return proje_css if proje_css.is_file() else "varsayilan"
    if ad and ad not in OTOMATIK_TEMA:
        return ad
    try:
        k = stil_mod.secili(p)
    except SystemExit:
        k = None
    if k and (t := stil_mod.motion_temasi(k)) and motion.tema_yolu(t):
        return t
    return proje_css if proje_css.is_file() else "varsayilan"


def tema_tokeni(p, k: Kurgu) -> dict:
    """Render ve önizlemenin okuduğu stil token'ı (ADR 0043): etkin temanın token'ı, font dosyaları, altyazı kipi.

    Stil seçilmemişse altyazı ADR 0014 standardında kalır (`altyazi_stilli` False); seçiliyse stilin altyazı token'ı.
    """
    from . import tema_token
    t = tema_token.oku(etkin_tema(p, k.motion_tema)) or tema_token.oku("varsayilan")
    d = t.model_dump()
    try:
        stilli = stil_mod.secili(p) is not None
    except SystemExit:
        stilli = False
    kayit = tema_token.font_kayitlari()
    adlar = {t.font.baslik, t.font.govde, t.font.mono, t.font.rakam or t.font.baslik, t.altyazi.font}
    d["dosyalar"] = {a: kayit[a]["file"] for a in adlar if a in kayit}
    d["altyazi_stilli"] = stilli
    # WHY: bkz. wiki/decisions/0046-dis-varlik-ve-lisans.md. Siyah zeminli dış varlık (light leak, film yanığı) screen ile
    # karışır; harita render ve önizlemeye aynı yoldan gider (Kurgu.tsx Video).
    from . import motion_ice
    d["karisim"] = motion_ice.karisim_haritasi(k)
    return d


_SABIT_MOTION = (re.compile(r"library:motion/custom/([\w-]+)/\1\.webm"), re.compile(r"public:motion/([\w-]+)-[0-9a-f]{10}\.webm"))


def _sabit_kimlik(k: Kurgu, c) -> str | None:
    """Kütüphanedeki parametresiz motion klibinin kimliği (ham ya da temalı kopya); değilse None."""
    kay = k.kaynaklar.get(c.kaynak or "")
    if not kay:
        return None
    for d in _SABIT_MOTION:
        if (m := d.fullmatch(kay.yol)) and m.group(1) in motion.kimlikler():
            return m.group(1)
    return None


def motion_bagla(p, k: Kurgu, *, canli_hf: bool = False) -> bool:
    """Şablonlu motion kliplerinin webm'ini üretir, kaynağı kurguya bağlar. Kurgu değiştiyse True.

    WHY: bkz. wiki/decisions/0036-motion-kutuphanesi-ve-ajanlar.md ve ADR 0062. `canli_hf=True` iken (HyperFrames motoru)
    özel tema ezmesi olmayan `hf` klipleri çevrimdışı WebM üretmeden doğrudan `data-composition-src` ile gömülür.
    """
    degisti = False
    if not any(c.tur == "motion" for c in k.klipler):
        return False
    tema = etkin_tema(p, k.motion_tema)
    try:
        kilitli = set(json.loads((paths.LIBRARY / "kit.json").read_text(encoding="utf-8")).get("locked", []))
    except (OSError, ValueError):
        kilitli = set()
    for c in k.klipler:
        if c.tur != "motion":
            continue
        if c.hf:  # HyperFrames kompozisyonu (ADR 0050, 0062): canlı gömülebilirse WebM ön-render atlanır
            ht = c.hf.get("tema")
            hk = hf_grafik.bul(c.hf["ad"], p.work)
            # WHY: bkz. wiki/specs/hf-canli-gomme-ve-dikey-duzen.md. Yönü sekansla uyuşmayan kompozisyon (16:9 şablon, 9:16
            # Reels) canlı gömmede dikey düzenini kuramıyor; sekans boyutunda WebM'i kontak render'ıyla birebir aynıdır.
            if canli_hf and not ht and hk and hf_grafik.canli_mi(hk) and hf_grafik.ayni_yon(hk, (k.sekans.w, k.sekans.h)):
                continue
            f, bilgi = hf_grafik.uret(c.hf["ad"], c.hf.get("param"), etkin_tema(p, ht) if ht else tema, p.work,
                                      p.work / "public" / "motion", sekans=(k.sekans.w, k.sekans.h))
            kid = "M_" + f.stem.replace("-", "_")
            if kid not in k.kaynaklar:
                k.kaynaklar[kid] = KurguKaynak(yol=f"public:motion/{f.name}", ses=False, **bilgi)
            if c.kaynak != kid:
                c.kaynak, degisti = kid, True
            continue
        if not c.sablon:
            # Sabit klip de videonun temasını alır: aynı animasyon, videoya göre renk (ADR 0042). Kilitli kayda dokunulmaz.
            kimlik = _sabit_kimlik(k, c)
            if not kimlik or kimlik in kilitli:
                continue
            if tema == "varsayilan":
                kid, yol, bilgi = "M_" + kimlik.replace("-", "_"), f"library:motion/custom/{kimlik}/{kimlik}.webm", None
            else:
                f, bilgi = motion.sablon_uret(kimlik, None, tema, p.work / "public" / "motion", sekans=(k.sekans.w, k.sekans.h))
                kid, yol = "M_" + f.stem.replace("-", "_"), f"public:motion/{f.name}"
            if kid not in k.kaynaklar:
                m = motion.meta(kimlik)
                k.kaynaklar[kid] = KurguKaynak(yol=yol, ses=False, **(bilgi or {"sure": m["sure"], "w": m["w"], "h": m["h"]}))
            if c.kaynak != kid:
                c.kaynak, degisti = kid, True
            continue
        t = c.sablon.get("tema")
        f, bilgi = motion.sablon_uret(c.sablon["ad"], c.sablon.get("param"), etkin_tema(p, t) if t else tema,
                                      p.work / "public" / "motion", sekans=(k.sekans.w, k.sekans.h))
        kid = "M_" + f.stem.replace("-", "_")
        if kid not in k.kaynaklar:
            k.kaynaklar[kid] = KurguKaynak(yol=f"public:motion/{f.name}", ses=False, **bilgi)
        if c.kaynak != kid:
            c.kaynak, degisti = kid, True
    return degisti


# Grafik olayı aralığı hedefi (sn): (dikey stüdyolar, youtube). WHY: ADR 0036, kullanıcı "sık sık kullansın" dedi.
YOGUNLUK = {"yogun": (4.0, 8.0), "orta": (6.5, 12.0), "az": None}
# WHY: bkz. wiki/decisions/0064-yaratici-yon.md. Enerji seviyesine (1 sakin, 5 doruk) göre grafiksiz aralık ve hedef çarpanı.
ENERJI_CARPAN: dict[int, float] = {1: 2.0, 2: 1.5, 3: 1.0, 4: 0.85, 5: 0.7}


def _enerji_carpani(t: float, enerji: list[tuple[float, float, int]] | None) -> float:
    """t anının düştüğü enerji diliminin yoğunluk çarpanı; dilim yoksa 1.0."""
    if not enerji:
        return 1.0
    for bas, son, seviye in enerji:
        if bas <= t < son:
            return ENERJI_CARPAN.get(seviye, 1.0)
    for bas, son, seviye in reversed(enerji):
        if bas <= t <= son:
            return ENERJI_CARPAN.get(seviye, 1.0)
    return 1.0


def _agirlikli_hedef(hedef: float, bitis: float, enerji: list[tuple[float, float, int]] | None) -> float:
    """Brif enerji dilimlerinin süresine göre ağırlıklı ortalama yoğunluk hedefi."""
    if not enerji or bitis <= 0:
        return hedef
    dilimler = [
        (max(0.0, a), min(bitis, b), ENERJI_CARPAN.get(sev, 1.0))
        for a, b, sev in enerji
        if b > 0 and a < bitis and min(bitis, b) > max(0.0, a)
    ]
    if not dilimler:
        return hedef
    toplam_d = sum(b - a for a, b, _ in dilimler)
    payda = max(bitis, toplam_d)
    kalan = max(0.0, bitis - toplam_d)
    ort_carpan = (sum((b - a) * c for a, b, c in dilimler) + kalan) / payda
    return round(hedef * ort_carpan, 4)


def motion_yogunlugu(k: Kurgu, hedef: float, enerji: list[tuple[float, float, int]] | None = None) -> list[str]:
    """Grafik olayları (sahne, motion metin, motion klip, hazır efekt) arasındaki boşluk hedefi aşıyorsa uyarılar.

    WHY: bkz. wiki/decisions/0064-yaratici-yon.md. `enerji` verilirse ([(bas, son, seviye 1-5)]) her boşluğun eşiği
    orta noktasının düştüğü enerji dilimine, ortalama yoğunluk uyarısı da ağırlıklı hedefe göre ölçeklenir.
    """
    gizli = {i.id for i in k.izler if i.gizli}
    bitis = max((c.bas + c.sure for c in k.klipler if c.iz not in gizli), default=0.0)
    etkin_hedef = _agirlikli_hedef(hedef, bitis, enerji)
    if bitis < etkin_hedef:
        return []
    anlar = []
    for c in k.klipler:
        if c.iz in gizli:
            continue
        if c.tur == "motion" or (c.tur == "sahne" and (c.sahne or {}).get("kind")) or (c.metin_stil or {}).get("tip"):
            anlar.append(c.bas)
        anlar += [c.bas + (e.get("t") or 0) for e in c.hazir]
    sinir = [0.0, *sorted(anlar), bitis]
    uyari = []
    ort = bitis / (len(anlar) + 1)
    if ort > etkin_hedef:
        uyari.append(
            f"motion yoğunluğu düşük: {len(anlar)} grafik olayı, ortalama {ort:.1f} sn'de bir "
            f"(hedef {round(etkin_hedef, 2):g} sn)"
        )
    taban = hedef * 2
    bos = [(a, b) for a, b in zip(sinir, sinir[1:]) if b - a > taban * _enerji_carpani((a + b) / 2, enerji)]
    if bos:
        uyari.append("grafiksiz uzun aralıklar: " + ", ".join(f"{a:.1f}-{b:.1f} sn" for a, b in bos[:8]))
    return uyari


def _gorselli_sahneler(c: dict) -> list[dict]:
    """Klibin `img` taşıyan sahne nesneleri: shot sahnesi ve stat içindeki shot."""
    s = c.get("sahne") or {}
    return [x for x in (s, s.get("shot")) if isinstance(x, dict) and x.get("img")]


def _gorsel_yolu(k: Kurgu, img: str) -> str | None:
    """`img`: shot/<ad> (zaten bağlı) → None; kaynak kimliği → kaynağın yolu; inputs:/library: yolu aynen."""
    if img.startswith("shot/"):
        return None
    return k.kaynaklar[img].yol if img in k.kaynaklar else img


def _sahne_gorseli(p, k: Kurgu, s: dict) -> None:
    """Render kopyasında img'yi shot/<ad> yapar, iw/ih ve odak eksikse görselden doldurur."""
    y = _gorsel_yolu(k, s["img"])
    if y is None:
        bilgi = {"img": s["img"]}
        if not (s.get("iw") and s.get("ih")):
            v = ff.probe(p.work / "public" / s["img"]).get("video") or {}
            bilgi.update(iw=v.get("width"), ih=v.get("height"))
    else:
        bilgi = shot_bagla(p, dosya(p, y))
    s["img"] = bilgi["img"]
    s["iw"] = s.get("iw") or bilgi.get("iw")
    s["ih"] = s.get("ih") or bilgi.get("ih")
    s.setdefault("focus", {"x": 0, "y": 0, "w": s["iw"]})  # SplitReel Shot odaksız çizemez


def _gorsel_hatasi(p, k: Kurgu, img) -> str | None:
    if not isinstance(img, str):
        return "img metin olmalı"
    try:
        y = _gorsel_yolu(k, img)
        f = p.work / "public" / img if y is None else dosya(p, y)
    except ValueError as e:
        return str(e)
    if not f.is_file():
        return f"görsel dosyası yok: {img}"
    if f.suffix.lower() not in GORSEL:
        return f"görsel değil: {img} (png, jpg, webp)"
    return None


def _motion_hatalari(c) -> list[str]:
    """Sahne türü ve metin grafik türü: render'da sessizce boş kalmasın diye adıyla reddedilir."""
    h = []
    s = c.sahne or {}
    if c.tur == "sahne":
        if s.get("kind") and s["kind"] not in SAHNE_TURLERI:
            h.append(f"{c.id}: bilinmeyen sahne türü '{s['kind']}' (geçerli: {', '.join(SAHNE_TURLERI)})")
        if s.get("layout", "split") not in ("split", "full"):
            h.append(f"{c.id}: sahne yerleşimi 'split' ya da 'full' olmalı, '{s['layout']}' yazılmış")
        if s.get("bg") and s["bg"] not in SAHNE_ZEMINLERI:
            h.append(f"{c.id}: sahne zemini '{s['bg']}' geçersiz (geçerli: {', '.join(SAHNE_ZEMINLERI)})")
        if s.get("bg") == "saydam" and s.get("layout") != "full":
            h.append(f"{c.id}: saydam zemin yalnız tam ekran (layout: full) sahnede olur")
    if c.sablon is not None:
        ad, sablonlar = c.sablon.get("ad"), motion.sablonlar()
        if c.tur != "motion":
            h.append(f"{c.id}: sablon yalnız motion klibinde olur")
        elif ad not in sablonlar:
            h.append(f"{c.id}: bilinmeyen motion şablonu '{ad}' (geçerli: {', '.join(sablonlar) or 'yok'})")
        else:
            h += [f"{c.id}: şablon {ad}: {e}" for e in motion.param_hatalari(sablonlar[ad], c.sablon.get("param") or {})]
            if (t := c.sablon.get("tema")) and t != PROJE_TEMASI and not motion.tema_yolu(t):
                h.append(f"{c.id}: bilinmeyen motion teması '{t}' (geçerli: {', '.join(motion.temalar())})")
    m = c.metin_stil or {}
    tip = m.get("tip")
    if tip is None:
        return h
    if tip not in METIN_TIPLERI:
        return h + [f"{c.id}: bilinmeyen metin grafik türü '{tip}' (geçerli: {', '.join(METIN_TIPLERI)})"]
    if c.tur not in ("metin", "gorsel") or (c.tur == "gorsel" and tip != "vurgu"):
        h.append(f"{c.id}: metin_stil.tip '{tip}' {c.tur} klibinde çalışmaz (metin klibi; görselde yalnız 'vurgu')")
    if tip == "vurgu":
        kutu = m.get("kutu")
        if not (isinstance(kutu, dict) and all(isinstance(kutu.get(a), (int, float)) for a in "xywh")):
            h.append(f"{c.id}: vurgu için kutu {{x, y, w, h}} gerekli (0..1 oranı)")
        if m.get("bicim", "kutu") not in VURGU_BICIMLERI:
            h.append(f"{c.id}: vurgu biçimi '{m['bicim']}' geçersiz (geçerli: {', '.join(VURGU_BICIMLERI)})")
    if tip == "sayac" and not isinstance(m.get("deger"), (int, float)):
        h.append(f"{c.id}: sayaç için sayı türünde deger gerekli")
    if tip == "cagri" and not (isinstance(m.get("hedef"), dict) and all(isinstance(m["hedef"].get(a), (int, float)) for a in "xy")):
        h.append(f"{c.id}: çağrı için hedef {{x, y}} gerekli (0..1 oranı)")
    if tip == "ilerleme" and not (isinstance(m.get("adim"), int) and isinstance(m.get("toplam"), int) and 1 <= m["adim"] <= m["toplam"]):
        h.append(f"{c.id}: ilerleme için 1 <= adim <= toplam tam sayıları gerekli")
    return h


def _public_bagla(p, ad: str, y: str, *, mod: str = "final") -> tuple[str, Path, bool] | None:
    """Kaynağı `work/public/_k/<ad><uzantı>` olarak bağlar. (bağlantı adı, bağlanan dosya, proxy mi) ya da None.

    WHY: bkz. wiki/decisions/0060-proxy-master-conform.md. Bağlantı adı moddan bağımsızdır: derleyici aynı adresi okur,
    taslakta proxy, finalde master görür. Final ve master modunda proxy asla bağlanmaz.
    """
    from . import vekil
    if y.startswith("public:"):
        return None
    kaynak = dosya(p, y)
    hedef = p.work / "public" / "_k" / f"{ad}{kaynak.suffix.lower()}"
    hedef.parent.mkdir(parents=True, exist_ok=True)
    proxy = False
    baglanabilir = kaynak.suffix.lower() in vekil.BAGLANABILIR
    if mod == "taslak" and baglanabilir and (px := vekil.hazir(p.work, kaynak, "taslak")):
        kaynak, proxy = px, True
    elif baglanabilir and ff.hdr_mi(ff.probe_ob(kaynak)):
        # WHY: ADR 0040. HDR kaynak render'a bağlantıyla değil SDR kopyayla girer; kurgu, kaynak yolu ve uzantı
        # (Kurgu.tsx _k/<id><uzantı> okur) değişmez. H.264 mp4 ve mov kapsayıcısına sığar. Master modunda
        # kopya yüksek kalitededir (ADR 0060), ayrı adla önbelleklenir.
        yuksek = mod == "master"
        sdr = p.work / "sdr" / f"{kaynak.stem}-{kaynak.stat().st_size}{'-m' if yuksek else ''}{kaynak.suffix.lower()}"
        if not sdr.exists():
            print(f"  HDR kaynak SDR'ye çevriliyor{' (master kalite)' if yuksek else ''}: {kaynak.name}")
            ff.sdr_cevir(kaynak, sdr, master=yuksek)
        kaynak = sdr
    if not (hedef.exists() and hedef.stat().st_size == kaynak.stat().st_size and hedef.samefile(kaynak)):
        hedef.unlink(missing_ok=True)
        hedef.hardlink_to(kaynak)
    return hedef.name, kaynak, proxy


def _conform_yaz(p, mod: str, beklenen: dict[str, Path], vekiller: list[str]) -> None:
    """Bağlama sonucunu `work/edit/conform.json`'a yazar; final ve master modunda proxy sızıntısında durur. WHY: ADR 0060."""
    from . import vekil
    hatalar = [] if mod == "taslak" else vekil.conform_denetle(p.work / "public", beklenen)
    if mod != "taslak" and vekiller:
        hatalar += [f"{ad}: proxy bağlı" for ad in vekiller]
    (p.work / "edit").mkdir(parents=True, exist_ok=True)
    (p.work / "edit" / "conform.json").write_text(json.dumps(
        {"mod": mod, "klip": len(beklenen), "proxy": vekiller, "master": len(beklenen) - len(vekiller),
         "hatalar": hatalar}, ensure_ascii=False), encoding="utf-8")
    if hatalar:
        raise SystemExit("Master conform kapısı: " + "; ".join(hatalar))


def _olay_hatalari(c) -> list[str]:
    """Kaynaksız ses olayı rol adıyla çalar (ADR 0032). Bilinmeyen rol ya da güç `olaysesi`ni render bittikten sonra durdururdu."""
    o = c.olay or {}
    if c.tur != "ses" or c.kaynak or o.get("muzik") or o.get("konusma"):
        return []
    from . import olaysesi  # yerel: numpy ve soundfile yalnız ses olayı varken yüklenir
    hatalar = []
    tur = o.get("tur", "sfx")
    if tur not in olaysesi.ROLLER and tur not in olaysesi.KOMBOLAR:
        hatalar.append(f"{c.id}: bilinmeyen ses olayı türü '{tur}' ({c.bas:.2f} sn). Roller: {', '.join(olaysesi.ROLLER)}; kombolar: {', '.join(olaysesi.KOMBOLAR)}")
    guc = o.get("guc")
    if guc is not None and guc not in olaysesi.GUC_ADI and guc not in olaysesi.GUC_DB:
        hatalar.append(f"{c.id}: bilinmeyen ses olayı gücü '{guc}'. Güçler: {', '.join(olaysesi.GUC_ADI)}")
    return hatalar


def denetle(p, k: Kurgu) -> list[str]:
    """Render ve terminal yazımı öncesi: kurgunun render'da patlayacak ya da yanlış çıkacak yerleri."""
    hatalar = []
    stil_k = karakter._stil_klasoru(p)
    t = k.motion_tema or ""
    if t not in OTOMATIK_TEMA and t != PROJE_TEMASI and not motion.tema_yolu(t):
        hatalar.append(f"bilinmeyen motion_tema '{t}' (geçerli: {', '.join(motion.temalar())}, {PROJE_TEMASI})")
    for iz in k.izler:
        sira = sorted((c for c in k.klipler if c.iz == iz.id), key=lambda c: c.bas)
        for a_, b_ in zip(sira, sira[1:]):
            if b_.bas < a_.bas + a_.sure - 1e-3:
                hatalar.append(f"{iz.id}: {a_.id} ile {b_.id} çakışıyor ({b_.bas:.3f} sn)")
    for c in k.klipler:
        if c.kaynak:
            try:
                if not dosya(p, k.kaynaklar[c.kaynak].yol).is_file():
                    hatalar.append(f"{c.id}: dosya yok: {k.kaynaklar[c.kaynak].yol}")
            except ValueError as e:
                hatalar.append(f"{c.id}: {e}")
        elif c.tur in ("video", "gorsel", "motion") and not c.sablon and not c.bilesen and not c.hf:  # şablonun kaynağını motion_bagla üretir; native bileşen kaynaksızdır
            hatalar.append(f"{c.id}: {c.tur} klibinin kaynağı yok")
        if c.hf is not None:
            if c.tur != "motion":
                hatalar.append(f"{c.id}: hf yalnız motion klibinde olur")
            else:
                hatalar += [f"{c.id}: {e}" for e in hf_grafik.denetle(c.hf.get("ad"), c.hf.get("param"), p.work)]
                if (ht := c.hf.get("tema")) and ht != PROJE_TEMASI and not motion.tema_yolu(ht):
                    hatalar.append(f"{c.id}: bilinmeyen motion teması '{ht}' (geçerli: {', '.join(motion.temalar())})")
        if c.tur == "sahne" and (c.sahne or {}).get("kind") == "shot" and not c.sahne.get("img"):
            hatalar.append(f"{c.id}: ekran görüntüsü sahnesinde görsel seçilmedi ({c.bas:.2f} sn)")
        if c.tur == "sahne":
            for s in _gorselli_sahneler({"sahne": c.sahne}):
                if e := _gorsel_hatasi(p, k, s["img"]):
                    hatalar.append(f"{c.id}: sahne görseli: {e}")
        hatalar += _motion_hatalari(c) + native_motion.hatalar(c) + hazir_efekt.hatalar(c) + _olay_hatalari(c) + fizik.hatalar(c) + karakter.hatalar(c, stil_k=stil_k)
    return list(dict.fromkeys(hatalar))


def bos(studyo: str) -> Kurgu:
    """Yeni proje: stüdyoya göre sekans, standart izler."""
    w, h = (1920, 1080) if studyo.startswith("youtube") else (1080, 1920)
    return Kurgu.model_validate({
        "sekans": {"w": w, "h": h, "fps": 30},
        "izler": [{"id": "V2", "tur": "video", "ad": "Üst"}, {"id": "V1", "tur": "video", "ad": "Ana"},
                  {"id": "A2", "tur": "ses", "ad": "SFX"}, {"id": "A3", "tur": "ses", "ad": "Müzik"}],
    })


def _ses_yeri(o: dict, fps: float) -> tuple[float, float, float | None]:
    """Eski olay zamanı sesin tepesini gösterir; timeline sesin başlangıcını. (başlangıç, giriş, süre).

    WHY: içe alma kayıpsız olsun: tepe ve kırpım olaysesi'nin kendi hesabıyla bulunur, eski miksle aynı yere düşer.
    """
    import numpy as np
    from . import audio, olaysesi
    rol = olaysesi.ROLLER.get(o.get("tur"), {"capa": "bas"})
    t = olaysesi.tepe_ani(o, rol, fps)
    f = paths.ROOT / o["dosya"]
    if not f.exists():
        return t, 0.0, None
    with tempfile.TemporaryDirectory() as gecici:
        data = audio._decode(f, Path(gecici))
    tepe = int(np.argmax(np.abs(data).mean(axis=1)))
    a, b = olaysesi.uydur_aralik(tepe, len(data), float(o.get("sure") or 0)) if rol.get("uydur") else (0, len(data))
    sr = olaysesi.SR
    bas = t if rol["capa"] == "ilk" else t - (tepe - a) / sr
    return max(0.0, bas), a / sr, (b - a) / sr


def eski_projeden(p) -> Kurgu:
    """props.json + speaker.mp4 + olaylar.json → kurgu. Word zamanları speaker.mp4 zamanıdır, kayıp olmaz."""
    props_yol = p.work / "edit" / "props.json"
    if not props_yol.exists():
        raise SystemExit(f"Props yok: {paths.rel(props_yol)}")
    props = json.loads(props_yol.read_text(encoding="utf-8"))
    konusmaci = p.work / "public" / props["speaker"]
    info = ff.probe(konusmaci)
    sure, v = info["duration"], info["video"]
    sahneler = props.get("scenes") or []
    toplam = max(sure, sahneler[-1]["end"] if sahneler else 0)
    kaynaklar = {"V01": {"yol": f"public:{props['speaker']}", "sure": sure, "w": v["width"], "h": v["height"], "ses": bool(info.get("audio"))}}
    klipler = [{"id": "v1", "iz": "V1", "tur": "video", "kaynak": "V01", "bas": 0, "sure": toplam, "konusmaci": True,
                "zoom": props.get("speakerZoom", 1.0), "punches": props.get("punches", [])}]
    for i, s in enumerate(sahneler):
        alan = {a: d for a, d in s.items() if a not in ("start", "end")}
        klipler.append({"id": f"s{i + 1}", "iz": "V2", "tur": "sahne", "bas": s["start"], "sure": s["end"] - s["start"], "sahne": alan})
    izler = [{"id": "V2", "tur": "video", "ad": "Sahneler"}, {"id": "V1", "tur": "video", "ad": "Konuşmacı"},
             {"id": "A2", "tur": "ses", "ad": "SFX"}, {"id": "A3", "tur": "ses", "ad": "Müzik"}]
    olaylar_yol = p.work / "edit" / "olaylar.json"
    if olaylar_yol.exists():
        spec = json.loads(olaylar_yol.read_text(encoding="utf-8"))
        n = 0
        def ses_klibi(src, iz, bas, gain, ek, olay, giris=0.0, sure=None):
            nonlocal n
            n += 1
            kid = f"K{n:03}"
            yolu = paths.ROOT / src
            tam = ff.probe(yolu)["duration"] if yolu.exists() else 1.0
            kaynaklar[kid] = {"yol": "library:" + Path(src).as_posix().removeprefix("library/"), "sure": tam}
            return {"id": f"a{n}", "iz": iz, "tur": "ses", "kaynak": kid, "bas": bas, "giris": giris, "sure": sure or tam, "ses": {"gain_db": gain, **ek}, "olay": olay}
        fps = float(spec.get("fps") or 30)
        for o in spec.get("olaylar", []):
            if not o.get("dosya"):
                # WHY: dosyası olmayan olayı kit ya da aday seçer (olaysesi); kaynak klibi yok, kısa işaret kalır.
                klipler.append({"id": f"o{len(klipler)}", "iz": "A2", "tur": "ses", "bas": o["t"], "sure": max(float(o.get("sure") or 0), 0.2),
                                "ses": {"gain_db": o.get("gain_db") or 0}, "olay": {a: o[a] for a in ("tur", "sure", "not") if a in o}})
                continue
            bas, giris, sure = _ses_yeri(o, fps)
            klipler.append(ses_klibi(o["dosya"], "A2", bas, o.get("gain_db") or 0, {},
                                     {a: o[a] for a in ("tur", "sure", "not") if a in o}, giris, sure))
        for m in spec.get("muzik", []):
            c = ses_klibi(m["src"], "A3", m.get("start", 0), m.get("gain_db", -14),
                          {"duck": m.get("duck", True), "fade_in": m.get("fade_in", 1.0), "fade_out": m.get("fade_out", 2.0)}, {"muzik": True})
            c["sure"] = min(c["sure"], toplam)
            klipler.append(c)
    return Kurgu.model_validate({
        "sekans": {"w": 1080, "h": 1920, "fps": 30}, "kaynaklar": kaynaklar,
        "kelimeler": {"V01": props.get("words", [])}, "izler": izler, "klipler": klipler,
    })
