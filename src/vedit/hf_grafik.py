"""HyperFrames grafikleri: kompozisyon → saydam webm → kurguda motion klibi.

WHY: bkz. wiki/decisions/0050-hyperframes-birincil-motor.md. Yeni animasyon, motion grafik, metin grafiği ve tam ekran
sahne HyperFrames'te yazılır; Stüdyo timeline'ı ve gerçek çekim birleştirmesi Remotion'da kalır. Klipte
`hf: {ad, param, tema}` niyeti yazılır, webm'i vedit üretir (sablon ile aynı kalıp, ADR 0036).

Kompozisyon yerleri (ilk bulunan geçerli):
  1. proje: `work/edit/hf/<ad>/index.html` (tek seferlik grafik ya da sahne; E2 ve ai-edit yazar)
  2. kütüphane: `library/motion/hf/<ad>/index.html` (tekrar kullanılan şablon)
Render, kompozisyonun bir kopyasında yapılır: kopyaya seçili stilin token'ı `tema.css`, yazı tipleri `fonts/` olarak
girer. Kompozisyon `<link rel="stylesheet" href="tema.css">` ile token'ı okur; sabit renk ve font yazılmaz (ADR 0043).
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
from html import unescape
from pathlib import Path

from . import hf, motion, paths

KUTUPHANE = paths.MOTION_DIR / "hf"
GSAP = paths.LIBRARY / "vendor" / "gsap.min.js"
_KOK_OZ = re.compile(r'data-(width|height|duration)\s*=\s*"([\d.]+)"')
ATLA = {"renders", ".thumbnails", "node_modules", ".hyperframes"}


def proje_kok(work: Path) -> Path:
    return work / "edit" / "hf"


def bul(ad: str, work: Path | None = None) -> Path | None:
    """Kompozisyon klasörü: önce proje, sonra kütüphane. Ad yalnız harf, rakam, tire ve alt çizgi olabilir."""
    if not re.fullmatch(r"[A-Za-z0-9_-]+", ad or ""):
        return None
    adaylar = ([proje_kok(work) / ad] if work else []) + [KUTUPHANE / ad]
    return next((d for d in adaylar if (d / "index.html").is_file()), None)


def adlar(work: Path | None = None) -> list[str]:
    kokler = ([proje_kok(work)] if work else []) + [KUTUPHANE]
    return sorted({d.name for k in kokler if k.is_dir() for d in k.iterdir() if (d / "index.html").is_file()})


def olcu_metin(html: str, ad: str = "kompozisyon") -> dict:
    """Kök öğenin boyutu ve süresi (`data-width`, `data-height`, `data-duration`): {w, h, sure}."""
    kok = re.search(r"<[^>]*data-composition-id[^>]*>", html)
    oz = dict(_KOK_OZ.findall(kok.group(0) if kok else html))
    if not {"width", "height", "duration"} <= oz.keys():
        raise ValueError(f"{ad}: kök öğede data-width, data-height ve data-duration olmalı")
    return {"w": int(float(oz["width"])), "h": int(float(oz["height"])), "sure": float(oz["duration"])}


def olcu(klasor: Path) -> dict:
    return olcu_metin((klasor / "index.html").read_text(encoding="utf-8"), klasor.name)


def degisken_adlari(klasor: Path) -> set[str] | None:
    """`data-composition-variables` içindeki değişken kimlikleri; bildirilmemişse None."""
    html = (klasor / "index.html").read_text(encoding="utf-8")
    m = re.search(r"""data-composition-variables\s*=\s*(?:'([^']*)'|"([^"]*)")""", html)
    if not m:
        return None
    try:
        return {d["id"] for d in json.loads(unescape(m.group(1) if m.group(1) is not None else m.group(2)))}
    except (ValueError, KeyError, TypeError):
        return set()


def _dosyalar(klasor: Path) -> list[Path]:
    return sorted(f for f in klasor.rglob("*") if f.is_file() and not (ATLA & set(f.relative_to(klasor).parts)))


def ozet(klasor: Path, param: dict | None, tema: str | Path | None) -> str:
    """Önbellek anahtarı: kompozisyon dosyaları, tema token'ı ya da parametre değişince değişir."""
    s = hashlib.sha1()
    for f in _dosyalar(klasor):
        s.update(f.relative_to(klasor).as_posix().encode())
        s.update(f.read_bytes())
    t = motion.tema_yolu(tema) or motion.tema_yolu("varsayilan")
    s.update(t.read_bytes() if t else b"")
    # Render kopyasına giren ortak dosyalar da anahtarda: yazı tipi ya da GSAP değişince eski webm dönmesin.
    for f in (paths.FONTS_DIR / "fonts.json", GSAP):
        s.update(f.read_bytes() if f.is_file() else b"")
    s.update(json.dumps(param or {}, sort_keys=True, ensure_ascii=False).encode())
    return s.hexdigest()[:10]


def _fontlar() -> dict[str, dict]:
    try:
        d = json.loads((paths.FONTS_DIR / "fonts.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return {ad: b for ad, b in d.items() if isinstance(b, dict) and b.get("file") and (paths.FONTS_DIR / b["file"]).is_file()}


def _font_dosyalari() -> list[Path]:
    return [paths.FONTS_DIR / b["file"] for b in _fontlar().values()]


def _font_css() -> str:
    return "".join(f'@font-face{{font-family:"{ad}";font-weight:{b.get("weight", "100 900")};src:url("fonts/{b["file"]}")}}'
                   for ad, b in _fontlar().items())


def _hazirla(klasor: Path, hedef: Path, tema: str | Path | None) -> None:
    """Render kopyası: kompozisyon + tema.css + yazı tipleri. HyperFrames proje dışındaki dosyayı okumaz (0.9.58+)."""
    if hedef.exists():
        shutil.rmtree(hedef)
    shutil.copytree(klasor, hedef, ignore=shutil.ignore_patterns(*ATLA))
    t = motion.tema_yolu(tema) or motion.tema_yolu("varsayilan")
    (hedef / "tema.css").write_text(_font_css() + "\n" + (t.read_text(encoding="utf-8") if t else ""), encoding="utf-8")
    # Ajan kompozisyonu GSAP'sız yazabilir; HyperFrames'in kendi kopyası konur (dış adres yok).
    if not (hedef / "gsap.min.js").exists() and "gsap.min.js" in (hedef / "index.html").read_text(encoding="utf-8"):
        if GSAP.is_file():
            shutil.copy2(GSAP, hedef / "gsap.min.js")
    fonts = hedef / "fonts"
    fonts.mkdir(exist_ok=True)
    for f in _font_dosyalari():
        if not (fonts / f.name).exists():
            shutil.copy2(f, fonts / f.name)


def uret(ad: str, param: dict | None, tema: str | Path | None, work: Path, klasor: Path) -> tuple[Path, dict]:
    """Kompozisyonu `klasor` altına saydam webm olarak üretir (varsa yeniden üretmez). (dosya, {sure, w, h}) döner."""
    kaynak = bul(ad, work)
    if not kaynak:
        raise ValueError(f"HyperFrames kompozisyonu yok: {ad} (work/edit/hf/{ad}/ ya da library/motion/hf/{ad}/)")
    bilgi = olcu(kaynak)
    hedef = klasor / f"hf-{ad}-{ozet(kaynak, param, tema)}.webm"
    if not hedef.exists():
        kopya = work / "hf-render" / hedef.stem
        try:
            _hazirla(kaynak, kopya, tema)
            hf.render_saydam(kopya, hedef, degiskenler=param or None)
        finally:
            shutil.rmtree(kopya, ignore_errors=True)
    return hedef, bilgi


def denetle(ad: str | None, param: dict | None, work: Path) -> list[str]:
    """Kurgu denetimi için hata listesi: kompozisyon var mı, ölçüsü okunuyor mu, parametreler bildirilmiş mi."""
    kaynak = bul(ad or "", work)
    if not kaynak:
        return [f"bilinmeyen HyperFrames kompozisyonu '{ad}' (geçerli: {', '.join(adlar(work)) or 'yok'})"]
    try:
        olcu(kaynak)
    except ValueError as e:
        return [str(e)]
    if param is not None and not isinstance(param, dict):
        return [f"{ad}: param bir nesne olmalı"]
    bildirilen = degisken_adlari(kaynak)
    fazla = sorted(set(param or {}) - (bildirilen or set()))
    return [f"{ad}: bildirilmemiş parametre: {', '.join(fazla)} (data-composition-variables)"] if fazla else []
