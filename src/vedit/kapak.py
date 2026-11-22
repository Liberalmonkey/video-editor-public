"""Kapak adayları: brief, Antigravity zemini, şablon yazısı, tek kare. WHY: bkz. wiki/decisions/0027-kapak-sayfasi.md

Yalnız YouTube (16:9) ve Instagram Reels (9:16, ızgarada 3:4). Adaylar work/gorsel/kapak/<platform>/ altında birikir,
seçilen Projeler/outputs/<stüdyo>/<proje>/ altına kopyalanır.
"""

from __future__ import annotations

import html
import json
import os
import re
import shutil
from pathlib import Path
from urllib.parse import quote, unquote

from . import ff, gorsel, hizli, kapak_prompt, paths

EN_COK = 5
EN_COK_KARE = 40  # 6 otomatik + elle eklenen anlar
GORSEL_UZANTI = (".jpg", ".jpeg", ".png", ".webp")
DIS_SINIR = 15_000_000  # içe alınan dış görsel, bayt
REF_TURLERI = ("yuz", "stil")
FONTLAR = {"Montserrat": "Montserrat-Variable.ttf", "Playfair Display": "PlayfairDisplay-Variable.ttf"}  # library/fonts
SABLON = paths.LIBRARY / "kapak" / "sablon.html"
SKILL = paths.ROOT / ".claude" / "skills"
# platform: (oran, genişlik, yükseklik, teslim adı, skill)
PLATFORMLAR = {
    "youtube": ("16:9", 1280, 720, "kapak", "kapak-youtube"),
    "instagram": ("9:16", 1080, 1920, "kapak-reels", "kapak-instagram"),
}
VARSAYILAN = {"youtube-animasyon": "youtube", "instagram": "instagram"}
# Başlık yerleşimleri (library/kapak/sablon.html); ilki platform varsayılanı.
YERLESIM = {"youtube": ("sol", "sag", "ust", "alt"), "instagram": ("ust", "alt")}
# Kalıplar (library/kapak/sablon.html `data-kalip`); ilki varsayılan. Kaynak: wiki/sources/2026-11-15-kapak-kalip-analizi.md
KALIP = {"youtube": ("klasik", "dev-yazi", "alt-bant", "bolunmus", "rozet", "not", "yazisiz"),
         "instagram": ("klasik", "seri", "yazisiz")}
KESITLI = {"dev-yazi", "seri"}  # ek söz öznenin arkasına girer: zeminden özne kesiti gerekir
STILLER = paths.LIBRARY / "kapak" / "stiller"
KALIP_PROMPT = kapak_prompt.KALIP_PROMPT  # kalıbın zeminden istediği kompozisyon; tek kaynak kapak_prompt
# Küçük boyut eşiği: en büyük yazının harf yüksekliği / kare yüksekliği. YouTube akışta 168x94 px'e iner (mobilde en az %8),
# Reels ızgarada 360 px genişliğe.
HARF_ESIGI = {"youtube": 0.08, "instagram": 0.03}
KELIME_SINIRI = {"youtube": 5, "instagram": 7}
OLC_JS = """[...document.querySelectorAll('.baslik,.ek,.etiket')]
  .filter((e) => getComputedStyle(e).display !== 'none' && e.textContent.trim())
  .map((e) => { const r = e.getBoundingClientRect(), s = getComputedStyle(e);
    return { sinif: e.className.split(' ')[0], arka: s.zIndex === '1', punto: parseFloat(s.fontSize),
      kutu: [r.left / innerWidth, r.top / innerHeight, r.right / innerWidth, r.bottom / innerHeight].map((v) => v * 100) }; })"""
# Kırpma alanları, tuval yüzdesi [sol, üst, sağ, alt]. ic: başlık içinde kalır; dis: başlık girmez.
# Stüdyo bunları çizer, tests/test_kapak.py şablonu bunlara karşı ölçer. Kaynak: ADR 0027, 2026-11-14 notu.
GUVENLI = {
    "youtube": [{"ad": "Kenar payı", "kutu": [4, 5, 96, 95], "tur": "ic"},
                {"ad": "Süre rozeti", "kutu": [80, 82, 100, 100], "tur": "dis"}],
    "instagram": [{"ad": "Izgara 3:4", "kutu": [0, 12.5, 100, 87.5], "tur": "ic"},
                  {"ad": "Akış 4:5", "kutu": [0, 14.8, 100, 85.2], "tur": "ic"}],
}


def platform_sec(p: hizli.Proje, platform: str | None) -> str:
    platform = platform or VARSAYILAN.get(p.studyo)
    if platform not in PLATFORMLAR:
        raise SystemExit(f"Platform youtube ya da instagram olmalı ({p.studyo} stüdyosunda --platform zorunlu)")
    return platform


def klasor(p: hizli.Proje, platform: str) -> Path:
    return p.work / "gorsel" / "kapak" / platform


def adaylar(k: Path) -> list[int]:
    return sorted(int(m.group(1)) for f in k.glob("kapak-*.jpg") if (m := re.fullmatch(r"kapak-(\d+)\.jpg", f.name)))


def stiller() -> dict[str, dict]:
    """Yazı stil paketleri: {ad: {aciklama, kutu, css}}. `turuncu` şablonun kendi varsayılanıdır."""
    paketler = {"turuncu": {"aciklama": "", "kutu": False, "css": {}}}
    for f in sorted(STILLER.glob("*.json")) if STILLER.is_dir() else []:
        try:
            v = json.loads(f.read_text(encoding="utf-8"))
        except ValueError:
            continue
        css = {a: str(d) for a, d in (v.get("css") or {}).items() if re.fullmatch(r"--[\w-]+", a) and not re.search(r"[;{}<>]", str(d))}
        paketler[f.stem] = {"aciklama": str(v.get("aciklama") or ""), "kutu": bool(v.get("kutu")), "css": css}
    return paketler


def varsayilan_stil(studyo: str) -> str | None:
    """Stüdyonun kapak stili (studios/<stüdyo>/kapak.json): seri tutarlılığı için brief'in önerisini ezer."""
    f = paths.STUDIOS / studyo / "kapak.json"
    try:
        ad = json.loads(f.read_text(encoding="utf-8")).get("stil")
    except (OSError, ValueError):
        return None
    return ad if ad in stiller() else None


def kesit(zemin: Path) -> Path | None:
    """Zeminden özne kesiti (aynı ölçü, saydam). rembg yoksa ya da görsel açılmazsa None; agy kotası harcamaz."""
    out = zemin.with_name(f"{zemin.stem}-ozne.png")
    if out.exists() and out.stat().st_mtime >= zemin.stat().st_mtime:
        return out
    try:
        from rembg import new_session, remove
        # WHY: rembg'nin varsayılan modeli (bria-rmbg, 1 GB) ticari kullanıma kapalıdır; u2net Apache 2.0 ve 176 MB.
        out.write_bytes(remove(zemin.read_bytes(), session=new_session("u2net")))
    except Exception as e:  # kurulu değil, model inmedi ya da görsel bozuk: kalıp klasiğe düşer
        print(f"Özne kesiti alınamadı ({type(e).__name__}); kurulum: .venv/Scripts/python -m pip install -e \".[kapak]\"")
        return None
    return out


def _en_iyi_anlar(v: Path, k: int, sure: float) -> list[float] | None:
    """Yüzün büyük ve net olduğu k an (kapak için en iyi ifade adayı). Yüz bulunamazsa None: eşit aralığa dönülür."""
    try:
        import math

        import cv2

        from . import reframe
        cap = cv2.VideoCapture(str(v))
        if not cap.isOpened() or not reframe.YUNET.exists():
            return None
        sw, sh = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        dh = max(1, int(sh * 480 / max(sw, 1)))
        det = cv2.FaceDetectorYN.create(str(reframe.YUNET), "", (480, dh), score_threshold=0.75)
        puanli = []
        for j in range(k * 4):
            t = sure * (0.05 + 0.90 * (j + 0.5) / (k * 4))
            cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
            ok, kare = cap.read()
            yuzler = det.detect(cv2.resize(kare, (480, dh)))[1] if ok else None
            if yuzler is None:
                continue
            x, y, w, h = (int(a) for a in max(yuzler, key=lambda y_: y_[2] * y_[3])[:4])
            kirp = cv2.cvtColor(cv2.resize(kare, (480, dh))[max(y, 0):y + h, max(x, 0):x + w], cv2.COLOR_BGR2GRAY)
            if kirp.size:
                puanli.append((w * h / (480 * dh) * math.log1p(cv2.Laplacian(kirp, cv2.CV_64F).var()), t))
        cap.release()
        secilen: list[float] = []
        for _, t in sorted(puanli, reverse=True):  # birbirine yapışık kareler tek aday sayılır
            if all(abs(t - o) >= sure * 0.03 for o in secilen):
                secilen.append(t)
            if len(secilen) == k:
                return sorted(secilen)
    except Exception:
        pass
    return None


def videolar(p: hizli.Proje) -> list[dict]:
    """Kapak yapılabilecek videolar: girdi videoları (doğal sıra), kurgu ham render'ı, teslim videoları (yeniden eskiye).

    yol: "inputs:<ad>" ya da "outputs:<göreli>" (Stüdyo /dosya kökü ile aynı)."""
    sonuc = []
    if p.girdi.exists():
        for f in sorted((f for f in p.girdi.iterdir() if f.is_file() and f.suffix.lower() in hizli.VIDEO),
                        key=lambda f: hizli.dogal(f.name)):
            sonuc.append({"yol": f"inputs:{f.name}", "ad": f.name, "tur": "girdi"})
    if (p.work / "renders" / "ham.mp4").is_file():
        sonuc.append({"yol": "outputs:work/renders/ham.mp4", "ad": "ham.mp4", "tur": "kurgu"})
    if p.cikti.exists():
        for f in sorted((f for f in p.cikti.glob("*.mp4") if f.is_file()), key=lambda f: -f.stat().st_mtime):
            sonuc.append({"yol": f"outputs:{f.name}", "ad": f.name, "tur": "teslim"})
    return sonuc


def video_yolu(p: hizli.Proje, yol: str) -> Path:
    """"inputs:1.mp4" ya da "outputs:..." → dosya. Proje kökü dışı, olmayan dosya ya da video olmayan uzantı reddedilir."""
    kok, _, ic = str(yol or "").partition(":")
    taban = {"inputs": p.girdi, "outputs": p.cikti}.get(kok)
    if taban is None or not ic:
        raise SystemExit(f"Video yolu inputs: ya da outputs: ile başlamalı: {yol}")
    f = (taban / ic).resolve()
    if not f.is_relative_to(taban.resolve()) or not f.is_file() or f.suffix.lower() not in hizli.VIDEO:
        raise SystemExit(f"Video yok: {yol}")
    return f


def _slug(yol: str) -> str:
    return re.sub(r"[^\w.-]+", "-", yol).strip("-")[:80] or "video"


def kare_klasoru(p: hizli.Proje, video: str | None = None) -> Path:
    kok = p.work / "gorsel" / "kapak" / "kareler"
    return kok / _slug(video) if video else kok


def kareler(p: hizli.Proje, n: int = 6, video: str | None = None) -> list[Path]:
    """Videodan n kare çıkarır: yüz varsa yüzün en büyük ve net olduğu anlar, yoksa eşit aralık (ilk ve son %5 hariç).

    video ("inputs:1.mp4"): yalnız o videodan; elle eklenen anlar (kare_ekle) sona eklenir. Yoksa projenin girdi videoları.
    Önbellek güncelse yeniden çıkarmaz."""
    # WHY: kapak karesi temiz olmalı: teslim videosunda gömülü altyazı ve grafik vardır, girdi videosunda yoktur.
    if video:
        secilen = [video_yolu(p, video)]
    else:
        girdi = sorted((f for f in p.girdi.iterdir() if f.is_file() and f.suffix.lower() in hizli.VIDEO),
                       key=lambda f: hizli.dogal(f.name)) if p.girdi.exists() else []
        cikti_mp4 = [f for f in p.cikti.glob("*.mp4") if f.is_file()] if p.cikti.exists() else []
        ham = p.work / "renders" / "ham.mp4"
        if girdi:
            secilen = girdi
        elif ham.is_file():
            secilen = [ham]
        elif cikti_mp4:
            secilen = [max(cikti_mp4, key=lambda f: f.stat().st_mtime)]
        else:
            secilen = []
    if not secilen or n <= 0:
        return []
    hedef = kare_klasoru(p, video)
    el = sorted(hedef.glob("el-*.jpg")) if video else []
    dosyalar = [hedef / f"kare-{i}.jpg" for i in range(1, n + 1)]
    son_video = max(v.stat().st_mtime for v in secilen)
    # Kaynak imzası: kareler başka videodan (eski sürümde teslim videosundan) alınmışsa önbellek geçersizdir.
    isaret, imza = hedef / "kaynak.txt", "v2|" + "|".join(v.name for v in secilen)
    guncel = isaret.exists() and isaret.read_text(encoding="utf-8") == imza
    if guncel and all(f.exists() and f.stat().st_mtime >= son_video for f in dosyalar):
        return dosyalar + el
    videolar = secilen
    hedef.mkdir(parents=True, exist_ok=True)
    isaret.write_text(imza, encoding="utf-8")
    m, idx = len(videolar), 1
    for i, v in enumerate(videolar):
        k = (n // m) + (1 if i < n % m else 0)
        if k <= 0:
            continue
        sure = max(float(ff.probe(v).get("duration") or 0), 0.1)
        bas, aralik = sure * 0.05, sure * 0.90
        anlar = _en_iyi_anlar(v, k, sure) or [bas + aralik * (j / (k - 1) if k > 1 else 0.5) for j in range(k)]
        for t in anlar:
            ff.still(v, hedef / f"kare-{idx}.jpg", t)
            idx += 1
    return dosyalar + el


def kare_ekle(p: hizli.Proje, video: str, t: float) -> Path:
    """Videonun t. saniyesini elle kare olarak ekler (kareler/<video>/el-<ms>.jpg); kare listesinin sonuna girer."""
    v = video_yolu(p, video)
    sure = float(ff.probe(v).get("duration") or 0)
    if not 0 <= t <= max(sure, 0.0):
        raise SystemExit(f"Zaman videonun dışında: {t:.2f} sn (süre {sure:.2f} sn)")
    hedef = kare_klasoru(p, video)
    hedef.mkdir(parents=True, exist_ok=True)
    return ff.still(v, hedef / f"el-{round(t * 1000):08d}.jpg", t)


def _ref_klasoru(p: hizli.Proje) -> Path:
    return p.work / "gorsel" / "kapak" / "referans"


def referanslar(p: hizli.Proje) -> list[tuple[str, Path]]:
    """Kullanıcının eklediği referanslar (referans/yuz-*, referans/stil-*) ve girdideki karakter* görselleri (yuz)."""
    k = _ref_klasoru(p)
    sonuc: list[tuple[str, Path]] = []
    if k.is_dir():
        for f in sorted(k.iterdir(), key=lambda f: hizli.dogal(f.name)):
            tur = f.name.split("-", 1)[0]
            if f.is_file() and f.suffix.lower() in GORSEL_UZANTI and tur in REF_TURLERI:
                sonuc.append((tur, f))
    return sonuc + [("yuz", f) for f in _karakterler(p)]


def referans_sil(p: hizli.Proje, ad: str) -> None:
    f = _ref_klasoru(p) / Path(ad).name
    if not f.is_file():
        raise SystemExit(f"Referans yok: {ad}")
    f.unlink()


def _agy_refleri(p: hizli.Proje, kare: Path | None) -> list[tuple[str, Path]]:
    """agy'ye giden sıra: video karesi, en çok 3 yüz, en çok 1 stil (Nano Banana karakter sınırı 4)."""
    refs = referanslar(p)
    return ([("kare", kare)] if kare else []) + [r for r in refs if r[0] == "yuz"][:3] + [r for r in refs if r[0] == "stil"][:1]


def baglam(p: hizli.Proje) -> str:
    """Brief için videonun metni: senaryo, yoksa yayın metni, yoksa transkript özeti."""
    for f in (p.girdi / "senaryo.md", p.cikti / "yayin.md", p.work / "analysis" / "digest.txt"):
        if f.exists():
            return f.read_text(encoding="utf-8")[:6000]
    raise SystemExit("Brief için metin yok: senaryo.md, yayin.md ya da `vedit hazirla` digest'i gerekli; ya da --prompt ver")


def json_dizisi(metin: str, anahtar: str | tuple[str, ...] = "prompt") -> list[dict]:
    """agy yanıtındaki ilk JSON dizisini alır; kod bloğu ya da ön söz olabilir. Her nesnede `anahtar`lardan biri dolu olmalı."""
    anahtarlar = (anahtar,) if isinstance(anahtar, str) else anahtar
    bas, son = metin.find("["), metin.rfind("]")
    try:
        veri = json.loads(metin[bas:son + 1]) if 0 <= bas < son else None
    except json.JSONDecodeError:
        veri = None
    if not isinstance(veri, list) or not veri or not all(isinstance(b, dict) and any(b.get(a) for a in anahtarlar) for b in veri):
        raise SystemExit(f"agy brief'i JSON dizisi değil:\n{metin[:400]}")
    return veri


BRIEF_METIN = (*kapak_prompt.BRIEF_ALANLARI, "prompt", "satir1", "satir2", "vurgu", "aci", "kalip", "ek", "stil", "not_tr")


def brief_temizle(b: dict) -> dict:
    """Brief'ten yalnız bilinen alanlar; metin kısaltılır, satır sonu atılır. Kalıp ve stilin geçerliliğine uret bakar."""
    temiz = {a: " ".join(str(b[a]).split())[:800 if a == "prompt" else 400] for a in BRIEF_METIN if b.get(a) not in (None, "")}
    try:
        if b.get("kare") is not None:
            temiz["kare"] = int(b["kare"])
    except (TypeError, ValueError):
        pass
    return temiz


def _brief_istegi(p: hizli.Proje, platform: str, adet: int, kr: list[tuple[int, Path]], metin: str, fikir: str | None) -> str:
    skill = (SKILL / PLATFORMLAR[platform][4] / "SKILL.md").read_text(encoding="utf-8")
    kaliplar = SKILL / PLATFORMLAR[platform][4] / "references" / "kaliplar.md"
    if kaliplar.exists():
        skill += "\n\n" + kaliplar.read_text(encoding="utf-8")
    stil_listesi = "; ".join(f"{ad}: {v['aciklama']}" for ad, v in stiller().items())
    kare_metin = (
        "\n\n---\nLook at these frames from the video and pick the best one for each angle:\n"
        + "\n".join(f"{i}: {f.resolve()}" for i, f in kr)
    ) if kr else ""
    kare_alan = f", kare (one of {', '.join(str(i) for i, _ in kr)}: the selected frame)" if kr else ""
    fikir_metin = (f"\n\n---\nThe creator's own idea (keep its intent, make it a stronger thumbnail; fix only what weakens it):\n{fikir}"
                   if fikir else "")
    ref_metin = "".join(
        f"\nAlso attached: a {'face photo of the same person' if r == 'yuz' else 'style reference thumbnail (take layout and colour only)'}: "
        f"{f.resolve()}" for r, f in _agy_refleri(p, None))
    return (f"You write thumbnail briefs. Follow these rules exactly:\n{skill}\n\n---\nVideo text:\n{metin or '(none)'}"
            f"{kare_metin}{ref_metin}{fikir_metin}\n\n---\n"
            f"Return ONLY a JSON array of {adet} objects with keys: "
            "sahne (English, 1-2 sentences: the single subject, what it does, where), "
            "ifade (English: facial expression; empty if there is no person), "
            "kompozisyon (English: where the subject sits and how large), isik (English: lighting), "
            "palet (English: one main colour and one accent colour), "
            "yazi_alani (English: the area that stays empty for the headline, e.g. 'the left third'), "
            "satir1, satir2 (cover text in the video's language), vurgu (one word from satir2), aci (the angle), "
            f"kalip (one of: {', '.join(KALIP[platform])}; follow the pattern rules above for what each text field means), "
            f"ek (the extra text of that pattern, empty if the pattern has none), stil (one of: {stil_listesi}){kare_alan}"
            + (", not_tr (1-2 Turkish sentences: what you changed in the creator's idea and why)" if fikir else "")
            + ". No text is drawn into the picture; the headline is added later in code. "
            "Every object uses a different angle and, where it fits the video, a different kalip. Do not run any commands.")


def _agy_brief(p: hizli.Proje, platform: str, adet: int, *, fikir: str | None = None, model: str | None = None,
               video: str | None = None, kare: int | None = None) -> list[dict]:
    kr = list(enumerate(kareler(p, video=video), 1))
    if kare is not None:
        kr = [(i, f) for i, f in kr if i == kare] or kr
    try:
        metin = baglam(p)
    except SystemExit:
        if not fikir:
            raise
        metin = ""
    istek = _brief_istegi(p, platform, adet, kr, metin, fikir)
    dizinler = {str(f.resolve().parent) for _, f in kr} | {str(f.resolve().parent) for _, f in _agy_refleri(p, None)}
    ekler = [Path(d) for d in sorted(dizinler)]
    secenek = {"model": model} if model else {}
    yanit = gorsel.agy(istek, ekler=ekler, **secenek) if ekler else gorsel.agy(istek, **secenek)
    liste = [brief_temizle(b) for b in json_dizisi(yanit.get("response", ""), ("sahne", "prompt"))[:adet]]
    for b in liste:
        if video:
            b["video"] = video
        if kare is not None:
            b["kare"] = kare
    return liste


def brief_uret(p: hizli.Proje, platform: str, adet: int, *, model: str | None = None, video: str | None = None) -> list[dict]:
    liste = _agy_brief(p, platform, adet, model=model, video=video)
    (klasor(p, platform) / "brief.json").write_text(json.dumps(liste, ensure_ascii=False, indent=1), encoding="utf-8")
    return liste


def gelistir(p: hizli.Proje, platform: str | None, fikir: str, adet: int = 1, *, model: str | None = None,
             video: str | None = None, kare: int | None = None) -> list[dict]:
    """Kullanıcının fikrini (Türkçe) skill kurallarıyla yapılı brief'e çevirir; oneri.json'a yazar. `uret(oneri=True)` kullanır.

    Fikir boşsa öneri yalnız videodan yazılır (senaryo, yayın metni ya da digest gerekir); görsel üretilmez."""
    platform = platform_sec(p, platform)
    fikir = " ".join(str(fikir or "").split())
    if len(fikir) > 800:
        raise SystemExit("Fikir en çok 800 karakter")
    if not 1 <= adet <= EN_COK:
        raise SystemExit(f"Öneri sayısı 1 ile {EN_COK} arasında olmalı")
    k = klasor(p, platform)
    k.mkdir(parents=True, exist_ok=True)
    liste = _agy_brief(p, platform, adet, fikir=fikir or None, model=model, video=video, kare=kare)
    (k / "oneri.json").write_text(json.dumps({"fikir": fikir, "model": model, "video": video, "briefler": liste},
                                             ensure_ascii=False, indent=1), encoding="utf-8")
    for b in liste:
        print(f"- {b.get('satir1', '')} / {b.get('satir2', '')}  {b.get('kalip', '')}  {b.get('not_tr', '')}")
    return liste


def oneri_oku(p: hizli.Proje, platform: str) -> dict | None:
    f = klasor(p, platform) / "oneri.json"
    try:
        return json.loads(f.read_text(encoding="utf-8")) if f.exists() else None
    except ValueError:
        return None


def oneri_yaz(p: hizli.Proje, platform: str | None, liste: list[dict], fikir: str | None = None) -> dict:
    """Stüdyo'da düzenlenen öneri kartları. Alanlar temizlenir; fikir verilmezse eski fikir kalır."""
    platform = platform_sec(p, platform)
    if not 1 <= len(liste) <= EN_COK:
        raise SystemExit(f"Öneri sayısı 1 ile {EN_COK} arasında olmalı")
    eski = oneri_oku(p, platform) or {}
    temiz = []
    for b in liste:
        t = brief_temizle(b)
        if isinstance(b.get("video"), str):
            t["video"] = b["video"][:300]
        temiz.append(t)
    veri = {**eski, "fikir": " ".join(str(fikir if fikir is not None else eski.get("fikir") or "").split())[:800], "briefler": temiz}
    k = klasor(p, platform)
    k.mkdir(parents=True, exist_ok=True)
    (k / "oneri.json").write_text(json.dumps(veri, ensure_ascii=False, indent=1), encoding="utf-8")
    return veri


def briefler(p: hizli.Proje, platform: str, adet: int, *, metin: str | None, prompt: str | None, yeni: bool,
             oneri: bool = False, model: str | None = None, video: str | None = None) -> list[dict]:
    if prompt:
        liste = [{"prompt": prompt} for _ in range(adet)]
    elif oneri:
        liste = (oneri_oku(p, platform) or {}).get("briefler") or []
        if not liste:
            raise SystemExit("Öneri yok: önce fikrini yaz ve \"Prompt'u geliştir\" de (--gelistir)")
        liste = [liste[i % len(liste)] for i in range(adet)]  # tek öneriden çok aday: her çizim ayrı yorum
    else:
        f = klasor(p, platform) / "brief.json"
        liste = json.loads(f.read_text(encoding="utf-8")) if f.exists() and not yeni else []
        if len(liste) < adet:
            liste = brief_uret(p, platform, adet, model=model, video=video)
    return liste[:adet]


def yazi(platform: str, b: dict, *, metin: str | None = None, **alan) -> dict:
    """Adayın yazı alanlarını günceller ve stilini doğrular. None olan alan değişmez; eksik stil platform varsayılanıdır."""
    b = dict(b)
    if metin is not None:
        s1, _, s2 = metin.partition("|")
        b.update(satir1=s1.strip(), satir2=s2.strip(), vurgu="")
    b.update({ad: v for ad, v in alan.items() if v is not None})
    yerlesim = b.get("yerlesim") or YERLESIM[platform][0]
    if yerlesim not in YERLESIM[platform]:
        raise SystemExit(f"{platform} yerleşimi şunlardan biri olmalı: {', '.join(YERLESIM[platform])}")
    kalip, stil = b.get("kalip") or KALIP[platform][0], b.get("stil") or "turuncu"
    if kalip not in KALIP[platform]:
        raise SystemExit(f"{platform} kalıbı şunlardan biri olmalı: {', '.join(KALIP[platform])}")
    paketler = stiller()
    if stil not in paketler:
        raise SystemExit(f"Kapak stili şunlardan biri olmalı: {', '.join(paketler)}")
    try:
        olcek = 1.0 if b.get("olcek") is None else float(b["olcek"])
    except (TypeError, ValueError):
        olcek = 0
    if not 0.6 <= olcek <= 1.4:
        raise SystemExit("Ölçek 0.6 ile 1.4 arasında olmalı")
    kutu = paketler[stil]["kutu"] if b.get("kutu") is None else bool(b["kutu"])  # paket varsayılanı; açık seçim ezer
    return {**b, "yerlesim": yerlesim, "olcek": olcek, "karart": bool(b.get("karart")), "kutu": kutu,
            "kalip": kalip, "stil": stil, "ek": str(b.get("ek") or "")}


def baslik_html(b: dict) -> str:
    s1, s2, vurgu = (str(b.get(k) or "") for k in ("satir1", "satir2", "vurgu"))
    # Vurgu ham metinde aranır, parçalar sonra kaçırılır: kaçırılmış metinde arama &amp; gibi varlıkları bölerdi.
    # Yazı büyük harfle çizildiği için büyük/küçük harf ayrımı yapılmaz.
    m = re.search(re.escape(vurgu), s2, re.I) if vurgu else None
    if m:
        s2 = f"{html.escape(s2[:m.start()])}<em>{html.escape(m.group())}</em>{html.escape(s2[m.end():])}"
    elif s2:
        s2 = f"<em>{html.escape(s2)}</em>"
    return f'<div class="baslik">{html.escape(s1)}<br>{s2}</div>'


def yazilar_html(b: dict) -> str:
    """Kalıbın yazı öğeleri. bolunmus: iki satır iki yarının etiketi; ek: kalıba göre dev söz, yardımcı satır, not ya da marka."""
    kalip = b.get("kalip") or "klasik"
    if kalip == "yazisiz":
        return ""
    if kalip == "bolunmus":
        return "".join(f'<div class="etiket {yan}">{html.escape(str(b.get(alan) or ""))}</div>'
                       for yan, alan in (("sol", "satir1"), ("sag", "satir2")))
    ek = f'<div class="ek">{html.escape(str(b["ek"]))}</div>' if b.get("ek") and kalip != "klasik" else ""
    # seri: ikinci satırın tamamı vurgudur (referans şablonda bütün satır kutudadır)
    return ek + baslik_html({**b, "vurgu": ""} if kalip == "seri" else b)


def html_metni(platform: str, zemin_url: str, yuz_url: str | None, b: dict, ozne_url: str | None = None,
               logolar: tuple[str, ...] | list[str] = ()) -> str:
    """Şablonu doldurur. Render (dosya yolu) ve Stüdyo önizlemesi (/dosya adresi) aynı metni kullanır."""
    b = yazi(platform, b)
    s = SABLON.read_text(encoding="utf-8")
    s = s.replace('url("zemin.png")', f'url("{zemin_url}")')
    s = s.replace('url("yuz.png")', f'url("{yuz_url}")' if yuz_url else "none")
    sinif = " ".join([*(ad for ad in ("karart", "kutu") if b[ad]), *(f"logo-{i}" for i in range(1, len(logolar[:2]) + 1))])
    degiskenler = {"--olcek": f"{b['olcek']:g}", **stiller()[b["stil"]]["css"],
                   **({"--ozne": f"url('{ozne_url}')"} if ozne_url else {}),
                   **{f"--logo{i}": f"url('{u}')" for i, u in enumerate(logolar[:2], 1)}}
    stil = html.escape("; ".join(f"{a}: {d}" for a, d in degiskenler.items()))
    govde = f'<body data-kalip="{b["kalip"]}" data-yerlesim="{b["yerlesim"]}" class="{sinif}" style="{stil}">'
    s = re.sub(r"<body[^>]*>", lambda _: govde, s, count=1)
    return re.sub(r"<!--yazilar-->.*?<!--/yazilar-->", lambda _: yazilar_html(b), s, count=1, flags=re.S)


def _yuz(k: Path, b: dict | None = None) -> Path | None:
    """Şeffaf yüz/avatar katmanı. Dış platformdan gelen zemin kişiyi zaten taşır: ikinci yüz çizilmez."""
    if b and b.get("zemin_kaynagi") == "dis":
        return None
    return next((f for f in (k / "yuz.png", k.parent.parent / "yuz.png") if f.exists()), None)


def html_yaz(k: Path, n: int, platform: str, zemin: Path, b: dict, ozne: Path | None = None, logolar: list[Path] = ()) -> Path:
    goreli = lambda f: quote(Path(os.path.relpath(f, k)).as_posix())
    yuz = _yuz(k, b)
    out = k / f"kapak-{n}.html"
    out.write_text(html_metni(platform, goreli(zemin), goreli(yuz) if yuz else None, b,
                              goreli(ozne) if ozne else None, [goreli(l) for l in logolar]), encoding="utf-8")
    return out


def _tasan(kutu: list[float], alanlar: list[dict]) -> list[str]:
    """Kutunun (tuval yüzdesi) çiğnediği alanlar: `ic` alanın dışına taşma ya da `dis` alana girme."""
    sol, ust, sag, alt = kutu
    return [g["ad"] for g in alanlar
            if (sol < g["kutu"][0] or ust < g["kutu"][1] or sag > g["kutu"][2] or alt > g["kutu"][3] if g["tur"] == "ic"
                else not (sag <= g["kutu"][0] or alt <= g["kutu"][1] or sol >= g["kutu"][2] or ust >= g["kutu"][3]))]


def _parlaklik(renk: str) -> float | None:
    m = re.fullmatch(r"#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})", renk.strip())
    if not m:
        return None
    h = m.group(1) if len(m.group(1)) == 6 else "".join(c * 2 for c in m.group(1))
    kanal = [(v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4) for v in (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))]
    return 0.2126 * kanal[0] + 0.7152 * kanal[1] + 0.0722 * kanal[2]


def olc(platform: str, b: dict, jpg: Path, kutular: list[dict] | None) -> dict:
    """Küçük boyutta okunma denetimi: kelime sayısı, harf yüksekliği, güvenli alan, kontursuz yazıda zemin kontrastı.

    kutular: render sırasında tarayıcıda ölçülen yazı kutuları (OLC_JS); yoksa yalnız kelime sayısı denetlenir."""
    b = yazi(platform, b)
    sozler = [] if b["kalip"] == "yazisiz" else " ".join(str(b.get(a) or "") for a in ("satir1", "satir2", "ek")).split()
    notlar = []
    if len(sozler) > KELIME_SINIRI[platform]:
        notlar.append(f"{len(sozler)} kelime var; en çok {KELIME_SINIRI[platform]} (referans kapaklarda ortalama 3)")
    on = [ku for ku in kutular or [] if not ku.get("arka")]  # öznenin arkasındaki dev söz bilerek taşar
    for ku in on:
        if tasan := _tasan(ku["kutu"], GUVENLI[platform]):
            notlar.append(f"Yazı güvenli alanı aşıyor ({', '.join(tasan)}): kısalt ya da --olcek küçült")
    _, _, h, _, _ = PLATFORMLAR[platform]
    harf = max((ku["punto"] for ku in on), default=0) * 0.72 / h or None  # 0.72: Montserrat büyük harf yüksekliği / punto
    if harf and harf < HARF_ESIGI[platform]:
        notlar.append(f"Yazı küçük boyutta okunmaz: harf yüksekliği karenin %{harf * 100:.1f}'i, en az %{HARF_ESIGI[platform] * 100:g}")
    css = stiller()[b["stil"]]["css"]
    kontrast = None
    baslik = max(on, key=lambda ku: ku["punto"], default=None)
    yazi_l = _parlaklik(css.get("--yazi", "#fff"))
    if baslik and yazi_l is not None and css.get("--kontur-k") == "0" and not b["karart"]:
        try:  # kontursuz yazı zemine güvenir: kutunun ortanca parlaklığı zemin sayılır (yazı kutunun yarısından azını kaplar)
            import cv2
            import numpy as np
            g = cv2.imdecode(np.fromfile(str(jpg), dtype=np.uint8), cv2.IMREAD_GRAYSCALE)
            gh, gw = g.shape
            sol, ust, sag, alt = (int(v / 100 * o) for v, o in zip(baslik["kutu"], (gw, gh, gw, gh)))
            zemin_l = (float(np.median(g[max(ust, 0):alt, max(sol, 0):sag])) / 255) ** 2.2
            kontrast = round((max(yazi_l, zemin_l) + 0.05) / (min(yazi_l, zemin_l) + 0.05), 1)
            if kontrast < 3:
                notlar.append(f"Yazı zemine karışıyor (kontrast {kontrast}): --karart aç ya da konturlu bir stil seç")
        except Exception:
            pass
    return {"kelime": len(sozler), "harf": round(harf * 100, 1) if harf else None, "kontrast": kontrast,
            "notlar": list(dict.fromkeys(notlar)), "gecti": not notlar}


def _ciz(k: Path, n: int, platform: str, zemin: Path, b: dict, logolar: list[Path] = ()) -> Path:
    """Adayı çizer ve kapak-N.json'a yazı, stil, zemin yolu ve ölçümle kaydeder; sonradan düzenleme bu kayıttan yapılır."""
    from . import pano
    _, w, h, _, _ = PLATFORMLAR[platform]
    b = {**yazi(platform, b), "zemin": Path(os.path.relpath(zemin, k)).as_posix()}
    ozne = kesit(zemin) if b["kalip"] in KESITLI else None
    if b["kalip"] in KESITLI and not ozne:
        print(f"Aday {n}: {b['kalip']} kalıbı özne kesiti ister; klasik kalıpla çizildi")
        b["kalip"] = "klasik"
    jpg = k / f"kapak-{n}.jpg"
    kutular: list = []
    pano.render(html_yaz(k, n, platform, zemin, b, ozne, logolar), jpg, sure=0, w=w, h=h, js=OLC_JS, sonuc=kutular)
    b["olcum"] = olc(platform, b, jpg, kutular[0] if kutular else None)
    for uyari in b["olcum"]["notlar"]:
        print(f"  ! aday {n}: {uyari}")
    (k / f"kapak-{n}.json").write_text(json.dumps(b, ensure_ascii=False), encoding="utf-8")
    return jpg


def _proje_ici(p: hizli.Proje, f: Path) -> tuple[str, str] | None:
    """Dosya projenin çıktı ya da girdi klasöründeyse (/dosya kökü, göreli yol), değilse None."""
    for kok_adi, kok in (("outputs", p.cikti), ("inputs", p.girdi)):
        try:
            return kok_adi, f.resolve().relative_to(kok.resolve()).as_posix()
        except ValueError:
            continue
    return None


def aday(p: hizli.Proje, k: Path, n: int) -> tuple[dict, Path]:
    """Adayın kaydı ve zemini. Eski adayda (zemin alanı yok) zemin kapak-N.html'deki url'den bulunur.

    Zemin proje klasörlerinin dışını gösteriyorsa reddedilir: kayıt elle değiştirilip başka bir dosya kapağa çizdirilemesin."""
    if not (k / f"kapak-{n}.jpg").exists():
        raise SystemExit(f"Aday yok: {paths.rel(k / f'kapak-{n}.jpg')}")
    f, h = k / f"kapak-{n}.json", k / f"kapak-{n}.html"
    b = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
    yol = b.get("zemin")
    if not yol and h.exists():
        m = re.search(r'--zemin: url\("([^"]+)"\)', h.read_text(encoding="utf-8"))
        yol = unquote(m.group(1)) if m else None
    if not yol or not (k / yol).is_file() or not _proje_ici(p, k / yol):
        raise SystemExit(f"Aday {n} zemini bulunamadı; adayı yeniden üret")
    return b, k / yol


REF_KURALI = kapak_prompt.REF_KURALI


def _girdi_gorselleri(p: hizli.Proje, on_ek: str) -> list[Path]:
    if not p.girdi.exists():
        return []
    return sorted(
        (f for f in p.girdi.iterdir() if f.is_file() and f.suffix.lower() in hizli.GORSEL and f.stem.lower().startswith(on_ek)),
        key=lambda f: hizli.dogal(f.name),
    )


def _karakterler(p: hizli.Proje) -> list[Path]:
    return _girdi_gorselleri(p, "karakter")


def _logolar(p: hizli.Proje) -> list[Path]:
    """`seri` kalıbının iki simge kartı: kullanıcının girdi klasörüne koyduğu logo*.png (üretilmez, kopyalanmaz)."""
    return _girdi_gorselleri(p, "logo")[:2]


def uret(p: hizli.Proje, platform: str | None = None, adet: int = 1, *, metin: str | None = None, prompt: str | None = None,
         zemin: Path | None = None, yeni_brief: bool = False, kare: int | None = None, video: str | None = None,
         oneri: bool = False, model: str | None = None, gorsel_model: str | None = None, **stil) -> list[Path]:
    """Yeni adaylar ekler, eskilerin üzerine yazmaz. agy kotası dolarsa kare varsa kare zemin olur.

    video: kareler yalnız bu videodan ("inputs:1.mp4"). oneri: brief olarak oneri.json (gelistir). model: brief'i yazan
    agy modeli; gorsel_model: generate_image'ı çağıran agy modeli (görsel modelinin kendisi agy'de sabittir, ADR 0052).
    stil: vurgu, yerlesim, olcek, karart, kutu, kalip, stil, ek (bkz. yazi)."""
    if not 1 <= adet <= EN_COK:
        raise SystemExit(f"Aday sayısı 1 ile {EN_COK} arasında olmalı")
    platform = platform_sec(p, platform)
    oran = PLATFORMLAR[platform][0]
    yazi(platform, {}, **stil)  # geçersiz stil agy kotası harcanmadan dursun
    if zemin and not zemin.is_file():
        raise SystemExit(f"Zemin yok: {zemin}")
    k = klasor(p, platform)
    k.mkdir(parents=True, exist_ok=True)
    # eldeki kare + elle yazı: agy'ye hiç gidilmez
    liste = briefler(p, platform, adet, metin=metin, prompt=prompt or ("eldeki kare" if zemin and metin else None), yeni=yeni_brief,
                     oneri=oneri and not prompt, model=model, video=video)
    kr = [] if zemin else kareler(p, video=video)
    studyo_stili = varsayilan_stil(p.studyo)
    bas = max(adaylar(k), default=0) + 1
    cikti: list[Path] = []
    for i, b in enumerate(liste):
        n = bas + i
        # Brief'in önerdiği kalıp ve stil geçersizse düşer (aday yanmasın); stüdyo stili brief'i, açık seçim hepsini ezer.
        b = {a: v for a, v in b.items() if not ((a == "kalip" and v not in KALIP[platform]) or (a == "stil" and v not in stiller()))}
        if studyo_stili:
            b["stil"] = studyo_stili
        secilen_no: int | None = None
        kare_dosyasi: Path | None = None
        if zemin:
            z = k / f"zemin-{n}{zemin.suffix.lower()}"  # aday kendi klasöründe dursun: sonradan düzenleme ve önizleme
            if z.resolve() != zemin.resolve():
                shutil.copy2(zemin, z)
            zemin_kaynagi = "elle"
        else:
            if kr:
                try:
                    aday_no = int(kare if kare is not None else b.get("kare") or 1)
                except (TypeError, ValueError):
                    aday_no = 1
                secilen_no = min(max(1, aday_no), len(kr))
                kare_dosyasi = kr[secilen_no - 1]
            refs = _agy_refleri(p, kare_dosyasi)
            istem = kapak_prompt.agy_prompt(b, platform, stil.get("kalip") or b.get("kalip"), [(r, str(f)) for r, f in refs])
            secenek = {"model": gorsel_model} if gorsel_model else {}
            try:
                if refs:
                    z = gorsel.uret(istem, k / f"zemin-{n}", oran, log=p.work / "gorsel" / "log.md", refler=[f for _, f in refs],
                                    ref_metni=kapak_prompt.ref_metni([(r, str(f.resolve())) for r, f in refs]), **secenek)
                else:
                    z = gorsel.uret(istem, k / f"zemin-{n}", oran, log=p.work / "gorsel" / "log.md", **secenek)
                zemin_kaynagi = "agy"
            except SystemExit as e:
                if kare_dosyasi:
                    print("agy üretmedi, videodaki kare zemin yapıldı")
                    z = kare_dosyasi
                    zemin_kaynagi = "kare"
                else:
                    print(f"agy durdu ({e}); {len(liste) - i} aday üretilemedi. Eldeki kareyle devam: --zemin <dosya>")
                    break
        b = yazi(platform, {**b, "kare": secilen_no, "zemin_kaynagi": zemin_kaynagi, **({"video": video} if video else {})},
                 metin=metin or None, **stil)
        jpg = _ciz(k, n, platform, z, b, _logolar(p))
        cikti.append(jpg)
        print(f"- {paths.rel(jpg)}  {b['kalip']} · {b['stil']}  {b.get('aci') or ''}")
    return cikti


def duzenle(p: hizli.Proje, platform: str | None, n: int, *, kopya: bool = False, **alan) -> Path:
    """Adayın yazısını zemini yeniden üretmeden (agy'siz) yeniden çizer. kopya: yeni aday açar (yerleşim varyasyonu).

    alan: metin ("satır1|satır2"), vurgu, yerlesim, olcek, karart, kutu, kalip, stil, ek; None olan değişmez."""
    platform = platform_sec(p, platform)
    k = klasor(p, platform)
    b, zemin = aday(p, k, n)
    hedef = max(adaylar(k)) + 1 if kopya else n
    jpg = _ciz(k, hedef, platform, zemin, yazi(platform, b, **alan), _logolar(p))
    gorsel.log_yaz(p.work / "gorsel" / "log.md", "yazı", PLATFORMLAR[platform][0], f"{platform} aday {n}",
                   f"{'varyasyon' if kopya else 'güncellendi'}: {jpg.name}")
    return jpg


def onizleme_html(p: hizli.Proje, platform: str | None, n: int, **alan) -> str:
    """Stüdyo canlı önizlemesi: render'la aynı şablon, dosya yazmaz. Zemin /dosya, Montserrat /lib/fonts adresinden gelir."""
    platform = platform_sec(p, platform)
    k = klasor(p, platform)
    b, zemin = aday(p, k, n)

    def url(f: Path) -> str:
        kok, yol = _proje_ici(p, f)  # aday() zemini, _yuz çıktı klasörünü doğruladı
        return f"/dosya/{quote(p.studyo)}/{quote(p.ad)}/{kok}/{quote(yol)}"

    yuz = _yuz(k, b)
    b = yazi(platform, b, **alan)
    # Önizleme dosya yazmaz: kesit önceden alınmışsa kullanılır, yoksa yazı öznenin üstünde görünür ("Yazıyı uygula" kesiti alır).
    ozne = zemin.with_name(f"{zemin.stem}-ozne.png") if b["kalip"] in KESITLI else None
    s = html_metni(platform, url(zemin), url(yuz) if yuz else None, b,
                   url(ozne) if ozne and ozne.exists() and _proje_ici(p, ozne) else None, [url(l) for l in _logolar(p)])
    font = "<style>" + "".join(f'@font-face {{ font-family: "{ad}"; font-weight: 100 900; src: url("/lib/fonts/{dosya}"); }}'
                               for ad, dosya in FONTLAR.items()) + "</style>"
    return s.replace("</head>", font + "</head>", 1)


def elestir(p: hizli.Proje, platform: str | None, nler: list[int] | None = None) -> list[dict]:
    """Adayları agy'ye rubrikle puanlatır (1-10) ve tek cümle düzeltme notu alır; kapak-N.json'a yazar. Seçim kullanıcıdadır."""
    platform = platform_sec(p, platform)
    k = klasor(p, platform)
    nler = [n for n in (nler or adaylar(k)) if (k / f"kapak-{n}.jpg").exists()]
    if not nler:
        raise SystemExit("Eleştirilecek aday yok")
    kaliplar = SKILL / PLATFORMLAR[platform][4] / "references" / "kaliplar.md"
    kucuk = "168x94 px in the YouTube feed" if platform == "youtube" else "a 3:4 crop about 360 px wide in the Instagram profile grid"
    istek = ("You are a strict thumbnail critic. Open each image file and judge it as a viewer sees it: " + kucuk + ".\n"
             + "\n".join(f"{n}: {(k / f'kapak-{n}.jpg').resolve()}" for n in nler)
             + "\n\nRubric (score 1-10 overall): one clear focal point; text readable at small size and under 5 words; "
             "strong contrast between subject, text and background; the cover makes one specific promise and raises curiosity; "
             "no AI slop (plastic skin, broken hands, meaningless shapes, generic stock look); subject and text do not fight.\n"
             + (f"Pattern rules of this project:\n{kaliplar.read_text(encoding='utf-8')}\n" if kaliplar.exists() else "")
             + "Return ONLY a JSON array, one object per image: n (the number above), puan (integer 1-10), "
             "not (ONE Turkish sentence: the weakest point and the single fix). Do not run any commands, do not write files.")
    sonuc = json_dizisi(gorsel.agy(istek, ekler=[k]).get("response", ""), "puan")
    for s in sonuc:
        f = k / f"kapak-{s.get('n')}.json"
        if s.get("n") in nler and f.exists():
            b = json.loads(f.read_text(encoding="utf-8"))
            b.update(puan=max(1, min(10, int(s["puan"]))), elestiri=str(s.get("not") or "")[:300])
            f.write_text(json.dumps(b, ensure_ascii=False), encoding="utf-8")
            print(f"- aday {s['n']}: {b['puan']}/10  {b['elestiri']}")
    return sonuc


# ---------------------------------------------------------------- görsel düzeltme ve dış görsel (ADR 0052)

def _oku(f: Path):
    import cv2
    import numpy as np
    g = cv2.imdecode(np.fromfile(str(f), dtype=np.uint8), cv2.IMREAD_COLOR)
    if g is None:
        raise SystemExit(f"Görsel açılamadı: {f.name}")
    return g


def _yaz(g, f: Path) -> Path:
    import cv2
    uzanti = f.suffix.lower() if f.suffix.lower() in GORSEL_UZANTI else ".png"
    ok, buf = cv2.imencode(uzanti, g, [cv2.IMWRITE_JPEG_QUALITY, 95] if uzanti in (".jpg", ".jpeg") else [])
    if not ok:
        raise SystemExit(f"Görsel yazılamadı: {f.name}")
    f.parent.mkdir(parents=True, exist_ok=True)
    buf.tofile(str(f))
    return f


def _kirp_oran(g, oran: float):
    """Ortadan kırpar: görsel hedef orandan genişse yanlar, darsa üst ve alt kesilir."""
    h, w = g.shape[:2]
    if abs(w / h - oran) < 0.005:
        return g
    if w / h > oran:
        yeni = round(h * oran)
        x = (w - yeni) // 2
        return g[:, x:x + yeni]
    yeni = round(w / oran)
    y = (h - yeni) // 2
    return g[y:y + yeni, :]


def _olcekle(g, w: int, h: int):
    import cv2
    gh, gw = g.shape[:2]
    if (gw, gh) == (w, h):
        return g
    return cv2.resize(g, (w, h), interpolation=cv2.INTER_AREA if gw > w else cv2.INTER_CUBIC)


def bolge_px(bolge: list[float] | tuple[float, ...], w: int, h: int) -> tuple[int, int, int, int]:
    """Tuval yüzdesi [sol, üst, sağ, alt] → piksel. Ters çizilmiş kutu düzeltilir; en az %2 genişlik ve yükseklik."""
    if len(bolge) != 4:
        raise SystemExit("Bölge dört sayı olmalı: sol,üst,sağ,alt (yüzde)")
    try:
        s, u, sa, a = (float(v) for v in bolge)
    except (TypeError, ValueError):
        raise SystemExit("Bölge sayı olmalı")
    if not all(0 <= v <= 100 for v in (s, u, sa, a)):
        raise SystemExit("Bölge değerleri 0-100 arasında olmalı")
    s, sa = sorted((s, sa))
    u, a = sorted((u, a))
    if sa - s < 2 or a - u < 2:
        raise SystemExit("Bölge çok küçük: en az karenin %2'si")
    return round(s / 100 * w), round(u / 100 * h), round(sa / 100 * w), round(a / 100 * h)


def isaretle(g, kutu: tuple[int, int, int, int]):
    """Kırmızı kutu tekniği: model kutunun içini değiştirir (Nano Banana'nın maske girişi yok)."""
    import cv2
    x1, y1, x2, y2 = kutu
    kalinlik = max(4, round(min(g.shape[:2]) * 0.008))
    return cv2.rectangle(g.copy(), (x1, y1), (x2, y2), (0, 0, 255), kalinlik)


def geri_yapistir(orijinal, sonuc, kutu: tuple[int, int, int, int]):
    """Sonuçtan yalnız kutu bölgesini (yumuşak kenarla) orijinale koyar: kutu dışındaki piksel değişmez."""
    import cv2
    import numpy as np
    h, w = orijinal.shape[:2]
    sonuc = _olcekle(_kirp_oran(sonuc, w / h), w, h)
    x1, y1, x2, y2 = kutu
    pay = max(4, round(min(w, h) * 0.02))
    maske = np.zeros((h, w), np.float32)
    maske[max(y1 - pay, 0):min(y2 + pay, h), max(x1 - pay, 0):min(x2 + pay, w)] = 1
    maske = cv2.GaussianBlur(maske, (pay * 2 + 1, pay * 2 + 1), 0)[..., None]
    karisim = orijinal.astype(np.float32) * (1 - maske) + sonuc.astype(np.float32) * maske
    return np.clip(np.rint(karisim), 0, 255).astype(np.uint8)


DUZELT_KISI = "Image {i} ({yol}) is a photo of the same person: use it only to keep the face accurate."


def gorsel_duzelt(p: hizli.Proje, platform: str | None, n: int, istek: str, *, bolge: list[float] | None = None,
                  yalniz_bolge: bool = True, model: str | None = None) -> Path:
    """Adayın zeminini Nano Banana ile düzeltir ve sonucu yeni aday yapar (eski aday kalır, yazı alanları korunur).

    bolge: tuval yüzdesi kutu; verilirse kırmızı kutuyla işaretlenir ve yalniz_bolge açıkken sonuçtan yalnız o bölge alınır."""
    platform = platform_sec(p, platform)
    istek = " ".join(str(istek or "").split())
    if not istek:
        raise SystemExit("Düzeltme isteği boş")
    if len(istek) > 400:
        raise SystemExit("Düzeltme isteği en çok 400 karakter")
    k = klasor(p, platform)
    b, zemin = aday(p, k, n)
    orijinal = _oku(zemin)
    h, w = orijinal.shape[:2]
    kutu = bolge_px(bolge, w, h) if bolge else None
    yeni = max(adaylar(k)) + 1
    if kutu:
        kaynak = _yaz(isaretle(orijinal, kutu), k / f"duzelt-{yeni}-isaret.png")
        istem = (f"Edit Image 1. Change only what is inside the red rectangle: {istek}. Keep everything outside the rectangle "
                 "exactly the same: the person, face, pose, background, lighting, colours and framing. Remove the red rectangle "
                 "completely; no red line may remain.")
    else:
        kaynak = zemin
        istem = (f"Edit Image 1: {istek}. Keep everything else exactly the same: the person's face and identity, pose, framing, "
                 "composition and colours. Change only what is asked.")
    kisiler = [f for r, f in referanslar(p) if r == "yuz"][:2]
    ref_m = f"Image 1 ({kaynak.resolve()}) is the image to edit. " + " ".join(
        DUZELT_KISI.format(i=i, yol=f.resolve()) for i, f in enumerate(kisiler, 2)) + " "
    secenek = {"model": model} if model else {}
    z = gorsel.uret(istem, k / f"zemin-{yeni}", PLATFORMLAR[platform][0], log=p.work / "gorsel" / "log.md",
                    refler=[kaynak, *kisiler], ref_metni=ref_m, **secenek)
    sonuc = _oku(z)
    # WHY: kayıpsız PNG; JPEG yeniden kodlaması kutu dışındaki pikselleri de oynatırdı (ölçüldü: en çok 10 birim).
    png = z.with_suffix(".png")
    _yaz(geri_yapistir(orijinal, sonuc, kutu) if kutu and yalniz_bolge else _olcekle(_kirp_oran(sonuc, w / h), w, h), png)
    if png != z:
        z.unlink(missing_ok=True)
    z = png
    b2 = {a: v for a, v in b.items() if a not in ("olcum", "puan", "elestiri", "zemin")}
    b2.update(ebeveyn=n, duzeltme=istek[:200], zemin_kaynagi="duzeltme", bolge=[round(v, 2) for v in bolge] if bolge else None)
    jpg = _ciz(k, yeni, platform, z, b2, _logolar(p))
    gorsel.log_yaz(p.work / "gorsel" / "log.md", "düzelt", PLATFORMLAR[platform][0], istek, f"aday {n} → {jpg.name}")
    return jpg


def _ilk_brief(p: hizli.Proje, platform: str) -> dict:
    """Dış görselin yazısı ve master prompt için kaynak: önce öneri, sonra brief.json."""
    oneri = (oneri_oku(p, platform) or {}).get("briefler") or []
    if oneri:
        return dict(oneri[0])
    f = klasor(p, platform) / "brief.json"
    try:
        liste = json.loads(f.read_text(encoding="utf-8")) if f.exists() else []
    except ValueError:
        liste = []
    return dict(liste[0]) if liste else {}


def ice_al(p: hizli.Proje, platform: str | None, dosya: Path, *, yazili: bool = False, metin: str | None = None) -> Path:
    """Başka platformda üretilen görseli aday yapar. Ortadan platform oranına kırpılır ve ölçeklenir.

    yazili: görselde yazı var; yazısız kalıpla bitmiş aday olur. Değilse zemin olur, yazı öneriden ya da brief'ten kodla eklenir."""
    platform = platform_sec(p, platform)
    if dosya.suffix.lower() not in GORSEL_UZANTI:
        raise SystemExit("Yalnız jpg, png ya da webp içe alınır")
    if not dosya.is_file():
        raise SystemExit(f"Dosya yok: {dosya}")
    if dosya.stat().st_size > DIS_SINIR:
        raise SystemExit(f"Dosya {DIS_SINIR // 1_000_000} MB'tan büyük")
    _, w, h, _, _ = PLATFORMLAR[platform]
    g = _olcekle(_kirp_oran(_oku(dosya), w / h), w, h)
    k = klasor(p, platform)
    n = max(adaylar(k), default=0) + 1
    z = _yaz(g, k / f"zemin-{n}.jpg")
    if yazili:
        b = {"kalip": "yazisiz", "satir1": "", "satir2": ""}
    else:
        b = _ilk_brief(p, platform)
        b = {a: v for a, v in b.items() if not ((a == "kalip" and v not in KALIP[platform]) or (a == "stil" and v not in stiller()))}
        if varsayilan_stil(p.studyo):
            b["stil"] = varsayilan_stil(p.studyo)
    b = yazi(platform, {**b, "zemin_kaynagi": "dis", "dis_dosya": dosya.name[:120], "kare": None}, metin=metin or None)
    jpg = _ciz(k, n, platform, z, b, _logolar(p))
    gorsel.log_yaz(p.work / "gorsel" / "log.md", "dış", PLATFORMLAR[platform][0], dosya.name, f"içe alındı: {jpg.name}")
    return jpg


def yazi_css(stil: str) -> dict:
    """Şablonun gövde varsayılanları + stil paketi: master prompt yazının rengini ve konturunu buradan anlatır."""
    m = re.search(r"body\s*\{([^}]*)\}", SABLON.read_text(encoding="utf-8"))
    taban = {a: d.strip() for a, d in re.findall(r"(--[\w-]+):\s*([^;]+);", m.group(1))} if m else {}
    return {**taban, **stiller().get(stil, {}).get("css", {})}


def master(p: hizli.Proje, platform: str | None, n: int | None = None, *, kare: int | None = None,
           video: str | None = None) -> dict:
    """Dış platformlar için master prompt: adayın kaydı ya da ilk öneri/brief + referanslar. agy çağırmaz.

    Dönen: {kaynak, hedefler: {hedef: {yazili, bos}}, ekler: [{no, rol, dosya, kok, yol}], md}."""
    platform = platform_sec(p, platform)
    k = klasor(p, platform)
    if n:
        b, _ = aday(p, k, n)
        kaynak = f"aday {n}"
    else:
        b = _ilk_brief(p, platform)
        kaynak = "öneri" if (oneri_oku(p, platform) or {}).get("briefler") else "brief"
        if not b:
            raise SystemExit("Master prompt için önce fikrini geliştir, videodan öner ya da bir aday seç")
    try:
        b = yazi(platform, b)
    except SystemExit:
        b = yazi(platform, {**b, "yerlesim": None, "olcek": None, "kalip": None, "stil": None})
    video = video or b.get("video")
    kare_no = kare if kare is not None else b.get("kare")
    kare_f: Path | None = None
    if kare_no:
        try:
            kr = kareler(p, video=video)
            kare_f = kr[int(kare_no) - 1] if 1 <= int(kare_no) <= len(kr) else None
        except (SystemExit, ValueError, TypeError):
            kare_f = None
    refs = _agy_refleri(p, kare_f)
    adli = [(r, f.name) for r, f in refs]
    css = yazi_css(b["stil"])
    hedefler = {h: {"yazili": kapak_prompt.master(b, platform, h, True, adli, css, b["kutu"]),
                    "bos": kapak_prompt.master(b, platform, h, False, adli, css, b["kutu"])} for h in kapak_prompt.HEDEFLER}
    ekler = []
    for i, (r, f) in enumerate(refs, 1):
        yer = _proje_ici(p, f)
        ekler.append({"no": i, "rol": r, "dosya": f.name, "kok": yer[0] if yer else None, "yol": yer[1] if yer else None})
    md = kapak_prompt.master_md(b, platform, adli, css, b["kutu"], baslik=f"{p.studyo}/{p.ad} · {kaynak}")
    return {"kaynak": kaynak, "hedefler": hedefler, "ekler": ekler, "md": md}


def sec(p: hizli.Proje, platform: str | None, n: int) -> Path:
    platform = platform_sec(p, platform)
    k = klasor(p, platform)
    kaynak = k / f"kapak-{n}.jpg"
    if not kaynak.exists():
        raise SystemExit(f"Aday yok: {paths.rel(kaynak)}")
    ad = PLATFORMLAR[platform][3]
    hedef, v = p.cikti / f"{ad}.jpg", 2
    while hedef.exists():  # eski teslimin üzerine yazmaz
        hedef, v = p.cikti / f"{ad}-v{v}.jpg", v + 1
    shutil.copy2(kaynak, hedef)
    if platform == "youtube" and hedef.stat().st_size > 2_000_000:
        print(f"Uyarı: {hedef.name} 2 MB'ı aşıyor; YouTube mobil yüklemede reddedebilir")
    (k / "secim.json").write_text(json.dumps({"n": n, "dosya": hedef.name}, ensure_ascii=False), encoding="utf-8")
    gorsel.log_yaz(p.work / "gorsel" / "log.md", "seçim", PLATFORMLAR[platform][0], f"{platform} aday {n}", f"seçildi: {hedef.name}")
    try:  # WHY: kapak başka platformda yeniden üretilebilsin (ADR 0052); master yazılamazsa teslim yine geçerlidir
        (p.cikti / f"{hedef.stem}-master-prompt.md").write_text(master(p, platform, n)["md"], encoding="utf-8")
    except (SystemExit, OSError, ValueError) as e:
        print(f"Master prompt yazılamadı: {e}")
    return hedef


def durum(p: hizli.Proje, platform: str | None, video: str | None = None) -> dict:
    """Stüdyo Kapak sekmesi için: videolar, kareler, referanslar, öneri, adaylar (outputs köküne göre yol), seçim, görsel motoru."""
    platform = platform_sec(p, platform)
    k = klasor(p, platform)
    def oku(f: Path):
        try:
            return json.loads(f.read_text(encoding="utf-8")) if f.exists() else None
        except ValueError:
            return None
    try:
        kr = [{"n": i, "yol": Path(os.path.relpath(f, p.cikti)).as_posix(), "el": f.name.startswith("el-")}
              for i, f in enumerate(kareler(p, video=video), 1)]
    except Exception:
        kr = []
    def satir(n: int) -> dict:
        b, jpg = oku(k / f"kapak-{n}.json") or {}, k / f"kapak-{n}.jpg"
        try:
            b = yazi(platform, b)
        except SystemExit:  # elle bozulmuş kayıt listeyi düşürmesin
            b = yazi(platform, {**b, "yerlesim": None, "olcek": None})
        return {"n": n, "yol": jpg.relative_to(p.cikti).as_posix(), "aci": b.get("aci"), "v": int(jpg.stat().st_mtime * 1000),
                **{ad: b.get(ad) or "" for ad in ("satir1", "satir2", "vurgu", "ek", "elestiri", "duzeltme")},
                **{ad: b[ad] for ad in ("yerlesim", "olcek", "karart", "kutu", "kalip", "stil")},
                "olcum": b.get("olcum"), "puan": b.get("puan"), "ebeveyn": b.get("ebeveyn"),
                "zemin_kaynagi": b.get("zemin_kaynagi") or "", "kare": b.get("kare"), "video": b.get("video")}

    secim = oku(k / "secim.json")
    if secim:  # aday teslimden sonra düzenlendiyse teslim dosyası eskidir
        aday_jpg, teslim = k / f"kapak-{secim.get('n')}.jpg", p.cikti / str(secim.get("dosya"))
        secim["eski"] = aday_jpg.exists() and (not teslim.is_file() or aday_jpg.stat().st_mtime > teslim.stat().st_mtime)
    oneri = oneri_oku(p, platform)
    if oneri:
        for b in oneri.get("briefler") or []:
            b["govde"] = kapak_prompt.govde(b, platform)  # agy'ye gidecek sahne tarifi (elle prompt yoksa)
    refs = []
    for tur, f in referanslar(p):
        yer = _proje_ici(p, f)
        if yer:
            refs.append({"tur": tur, "ad": f.name, "kok": yer[0], "yol": yer[1], "silinir": f.parent == _ref_klasoru(p)})
    _, w, h, _, _ = PLATFORMLAR[platform]
    return {"platform": platform, "oran": PLATFORMLAR[platform][0], "w": w, "h": h, "en_cok": EN_COK,
            "yerlesimler": list(YERLESIM[platform]), "guvenli": GUVENLI[platform],
            "kaliplar": list(KALIP[platform]), "kesitli": sorted(KESITLI), "logo": len(_logolar(p)),
            "stiller": [{"ad": ad, "aciklama": v["aciklama"], "kutu": v["kutu"]} for ad, v in stiller().items()],
            "videolar": videolar(p), "video": video, "kareler": kr, "referanslar": refs,
            "adaylar": [satir(n) for n in adaylar(k)],
            "brief": oku(k / "brief.json") or [], "oneri": oneri, "secim": secim,
            "gorsel_motor": gorsel.kota(), "hedefler": kapak_prompt.hedef_listesi()}
