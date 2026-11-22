"""Stil paketleri: referanstan STYLE.md üretimi ve projeye stil seçimi. WHY: bkz. wiki/decisions/0029-stil-paneli.md

Paket: studios/<stüdyo>/styles/<ad>/{STYLE.md, MOTION.md, tokens.json}. Referans: Projeler/inputs/_referanslar/<stüdyo>/<ad>/.
Proje seçimi work/edit/stil.txt; yoksa studio.yaml → style.
"""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

from . import ajan_cagri, hizli, motion, paths, reference

AD = re.compile(r"[\w\-]{1,40}")
ATLA = {"images", "analysis"}
PAKET_DOSYALARI = ("STYLE.md", "MOTION.md", "tokens.json")


def ad_denetle(ad: str) -> str:
    if not AD.fullmatch(ad or ""):
        raise SystemExit("Stil adı yalnız harf, rakam, tire, alt çizgi; en çok 40 karakter")
    return ad


def klasor(studyo: str, ad: str) -> Path:
    return paths.STUDIOS / studyo / "styles" / ad_denetle(ad)


def referans_klasoru(studyo: str, ad: str) -> Path:
    return paths.REFERENCES / studyo / ad_denetle(ad)


def secili_adi(p) -> str | None:
    """Projenin stili: work/edit/stil.txt, yoksa stüdyo varsayılanı."""
    f = p.work / "edit" / "stil.txt"
    if f.exists() and (ad := f.read_text(encoding="utf-8").strip()):
        return ad
    y = paths.STUDIOS / p.studyo / "studio.yaml"
    m = re.search(r"^style:\s*([\w\-]+)", y.read_text(encoding="utf-8"), re.M) if y.exists() else None
    return m.group(1) if m else None


def secili(p, ad: str | None = None) -> Path | None:
    """Edit'in uyacağı stil klasörü; STYLE.md yoksa None. Açıkça istenen stil yoksa hata."""
    acik = bool(ad) or (p.work / "edit" / "stil.txt").exists()
    ad = ad or secili_adi(p)
    if not ad:
        return None
    k = klasor(p.studyo, ad)
    if (k / "STYLE.md").exists():
        return k
    if acik:  # stüdyo varsayılanı eksikse sessizce stilsiz edit; seçilmiş stil eksikse dur
        raise SystemExit(f"Stil yok: {paths.rel(k)}/STYLE.md. Önce `vedit stil-uret {p.studyo} {ad}`.")
    return None


def motion_temasi(k: Path) -> str | None:
    """Stil paketinin motion teması (`tokens.json → motion_tema`); yoksa None. WHY: bkz. wiki/decisions/0042-stil-katalogu-ve-video-temasi.md"""
    try:
        t = json.loads((k / "tokens.json").read_text(encoding="utf-8")).get("motion_tema")
    except (OSError, ValueError, AttributeError):
        return None
    return t if isinstance(t, str) and AD.fullmatch(t) else None


def sec(p, ad: str) -> None:
    if not (klasor(p.studyo, ad) / "STYLE.md").exists():
        raise SystemExit(f"Stil hazır değil: {ad}")
    f = p.work / "edit" / "stil.txt"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(ad, encoding="utf-8")


def liste(studyo: str) -> list[dict]:
    """Stüdyonun hazır ve referans bekleyen tüm stilleri."""
    s_kok = paths.STUDIOS / studyo / "styles"
    r_kok = paths.REFERENCES / studyo
    adlar: set[str] = set()
    for kok in (s_kok, r_kok):
        if kok.exists():
            for d in kok.iterdir():
                if d.is_dir() and d.name not in ATLA and AD.fullmatch(d.name):
                    adlar.add(d.name)
    cikti: list[dict] = []
    for ad in sorted(adlar, key=hizli.dogal):
        k, r = klasor(studyo, ad), referans_klasoru(studyo, ad)
        sf, mf = k / "STYLE.md", k / "MOTION.md"
        hazir = sf.exists()
        refler = sorted((f.name for f in r.iterdir() if f.is_file() and not f.name.startswith(".")), key=hizli.dogal) if r.exists() else []
        oge: dict = {
            "ad": ad,
            "hazir": hazir,
            "style_md": sf.read_text(encoding="utf-8") if hazir else "",
            "motion_md": mf.read_text(encoding="utf-8") if mf.exists() else "",
            "referanslar": refler,
        }
        if hazir or (k / "varliklar.json").exists():
            from . import stil_varlik
            oz = stil_varlik.ozet(studyo, ad)
            oge["varlik_sayisi"] = oz["toplam"]
            oge["varliklar_ozet"] = oz
        cikti.append(oge)
    return cikti


def sil(studyo: str, ad: str) -> list[str]:
    """Stil paketini ve referanslarını siler; bu stili seçmiş projelerin seçimini kaldırır. Silinen göreli yolları döner."""
    silinen = []
    for k in (klasor(studyo, ad), referans_klasoru(studyo, ad)):
        if k.is_dir():
            shutil.rmtree(k)
            silinen.append(paths.rel(k))
    if not silinen:
        raise SystemExit(f"Stil yok: {ad}")
    kok = paths.OUTPUTS / studyo
    for f in kok.glob("*/work/edit/stil.txt") if kok.exists() else []:
        if f.read_text(encoding="utf-8").strip() == ad:
            f.unlink()
            silinen.append(paths.rel(f))
    return silinen


def kaydet(studyo: str, ad: str, style_md: str) -> None:
    k = klasor(studyo, ad)
    k.mkdir(parents=True, exist_ok=True)
    (k / "STYLE.md").write_text(style_md, encoding="utf-8")


def uret(studyo: str, ad: str, *, motor: str = "claude", model: str | None = None) -> Path:
    """Referansları ölçer ve ajana STYLE.md, MOTION.md, tokens.json yazdırır."""
    ref = referans_klasoru(studyo, ad)
    dosyalar = sorted((f for f in ref.iterdir() if f.is_file() and not f.name.startswith(".")), key=lambda f: hizli.dogal(f.name)) if ref.exists() else []
    videolar = [f for f in dosyalar if f.suffix.lower() in hizli.VIDEO]
    gorseller = [f for f in dosyalar if f.suffix.lower() in hizli.GORSEL]
    if not videolar and not gorseller:
        raise SystemExit(f"Referans yok: {paths.rel(ref)} altına video ya da görsel koy.")
    analiz = ref / "analysis"
    reference.run(analiz, [], gorseller, videos=videolar)
    analiz.mkdir(parents=True, exist_ok=True)
    hedef = klasor(studyo, ad)
    hedef.mkdir(parents=True, exist_ok=True)
    skill = paths.ROOT / ".claude" / "skills" / "style-pack"
    mevcut = [hedef / d for d in PAKET_DOSYALARI if (hedef / d).exists()]
    okunacaklar = [
        (analiz / "digest.md").resolve(),
        *(p.resolve() for p in sorted(analiz.glob("*/*.jpg"))),
        *([(analiz / "images-grid.jpg").resolve()] if gorseller or (analiz / "images-grid.jpg").exists() else []),
        (skill / "SKILL.md").resolve(),
        (skill / "references" / "STYLE.template.md").resolve(),
        (skill / "references" / "MOTION.template.md").resolve(),
        (skill / "references" / "stil-arketipleri.md").resolve(),
        (paths.LIBRARY / "styles" / "default" / "tokens.json").resolve(),
        *(p.resolve() for p in mevcut),
    ]
    yazilacaklar = [(hedef / d).resolve() for d in PAKET_DOSYALARI]
    istek = analiz / "stil.istek.md"
    istek.write_text(
        f"# Stil paketi üretimi: {studyo}/{ad}\n\n"
        "## Okunacak dosyalar\n" + "\n".join(f"- {p}" for p in okunacaklar) + "\n\n"
        "## Yazılacak dosyalar (tam üç dosya)\n" + "\n".join(f"- {p}" for p in yazilacaklar) + "\n\n"
        "## Kurallar\n"
        "- Türkçe tam düzyazı kullan.\n"
        "- Her dosya en çok 80 satır olmalı.\n"
        "- Her kural ölçülmüş olmalı; ölçülemeyen yerler `(çıkarım)` ile işaretlenir.\n"
        "- Palet hex'leri kontak sayfasından (`sheet.jpg` / `hook.jpg` / `images-grid.jpg`) okunur.\n"
        "- Tempo sayıları `digest.md` içinden alınır.\n"
        "- Referansın içeriği değil grameri alınır (kesim temposu, metin yoğunluğu, kadraj, renk).\n"
        "- Altyazı stilin token'ını alır (ADR 0043): okunan kelime stilin vurgusu, gövde beyaz, koyu kontur; kutu, pop ve solma yok.\n"
        "- `tokens.json` yalnız varsayılandan (`library/styles/default/tokens.json`) farklı alanları içerir ve geçerli JSON nesnesidir.\n"
        "- `tokens.json` içinde `colors.accent`, `colors.bg`, `colors.fg` (hex) ve `fonts.display` bulunur; `motion_tema` yazılmaz: "
        "vedit paketin kendi paletinden tema üretir (ADR 0043).\n"
        "- Mevcut paket dosyaları varsa eski kural silinmez, `Dersler` bölümüne tarihli not eklenir.\n"
        "- Kabuk komutu çalıştırılmaz; yalnız dosya okunur ve yazılır.\n",
        encoding="utf-8",
    )
    ajan_cagri.dosyadan(istek, motor=motor, model=model)
    eksik = [d for d in PAKET_DOSYALARI if not (hedef / d).exists()]
    if eksik:
        raise SystemExit(f"Stil paketi eksik ({', '.join(eksik)}): {paths.rel(hedef)}")
    try:
        veri = json.loads((hedef / "tokens.json").read_text(encoding="utf-8"))
    except ValueError as e:
        raise SystemExit(f"tokens.json geçersiz JSON: {e}") from e
    if not isinstance(veri, dict):
        raise SystemExit("tokens.json bir JSON nesnesi (dict) olmalı")
    if not veri.get("motion_tema"):
        from . import tema_token  # WHY: ADR 0043, paket kendi paletiyle temalanır, başka temaya düşmez
        print(f"Tema: {tema_token.paketten_yaz(hedef)}")
    for d in PAKET_DOSYALARI:
        print(f"Yazıldı: {paths.rel(hedef / d)}")
    return hedef
