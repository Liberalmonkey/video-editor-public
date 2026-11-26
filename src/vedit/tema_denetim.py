"""Tema kilidi: üretilen varlıkta sabit renk ve yazı tipi yasaktır; renk ve font seçili stilin token'ından gelir.

WHY: bkz. wiki/decisions/0043-stile-bagli-tema-tokenlari.md ve 0058-hizli-ve-kaliteli-edit.md. Ajanlar kendi HyperFrames
kompozisyonlarını (`work/edit/hf/<ad>/index.html`) ve şablon parametrelerini yazar; sabit renk ya da font stili deler.
Nötr siyah ve beyaz (gölge, karartma) her stilde serbesttir (`kurgu_kalite` ile aynı kural).
`tests/test_sabit_renk.py` repo kodunu aynı desenle (`sabit_desen`) tarar.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache

from . import paths

HEX = re.compile(r"(?<![\w&])#([0-9A-Fa-f]{3}|[0-9A-Fa-f]{4}|[0-9A-Fa-f]{6}|[0-9A-Fa-f]{8})\b")
RENK_FONK = re.compile(r"\b(rgba?|hsla?)\(\s*([^()]*)\)", re.I)
FONT_BILDIRIM = re.compile(r"(?:font-family|fontFamily)\s*[:=]\s*([^;}\n]+)", re.I)
NOTR_HEX = {"000", "fff", "0000", "ffff", "000000", "ffffff", "00000000", "ffffffff"}
GENEL_FONT = {"inherit", "initial", "unset", "sans-serif", "serif", "monospace", "cursive", "system-ui"}


@lru_cache(maxsize=1)
def font_adlari() -> tuple[str, ...]:
    """Kütüphanedeki font adları (library/fonts/fonts.json)."""
    try:
        d = json.loads((paths.FONTS_DIR / "fonts.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return ()
    return tuple(k for k in d if not k.startswith("_"))


def sabit_desen() -> re.Pattern:
    """Repo kodu için sayım deseni: altı haneli hex ya da tırnaklı kütüphane font adı (ADR 0043 beyaz listesiyle)."""
    adlar = "|".join(re.escape(f) for f in font_adlari()) or "(?!)"
    return re.compile(rf"#[0-9A-Fa-f]{{6}}\b|['\"]({adlar})['\"]")


def _notr_fonk(ad: str, arg: str) -> bool:
    if "var(" in arg or not re.match(r"\s*[\d.]", arg):
        return True  # token'dan türetilmiş: rgb(var(--vurgu-rgb) / .5) ya da JS yardımcısı rgba(t.renk.zemin, .9)
    sayilar = re.findall(r"[\d.]+%?", arg)
    if ad.lower().startswith("hsl"):
        return len(sayilar) >= 3 and sayilar[1].rstrip("%") in ("0", "0.0")  # doygunluk 0: gri ton
    kanal = [s for s in sayilar[:3]]
    return len(kanal) == 3 and all(k in ("0", "255") for k in kanal) and len(set(kanal)) == 1


def ihlaller(metin: str, *, kaynak: str = "") -> list[str]:
    """Sabit renk ve font bulguları (tekrarsız, okunur). Boş liste: tema kilidi korunuyor."""
    out: list[str] = []
    on = f"{kaynak}: " if kaynak else ""
    for m in HEX.finditer(metin):
        if m.group(1).lower() not in NOTR_HEX:
            out.append(f"{on}sabit renk {m.group(0)}")
    for m in RENK_FONK.finditer(metin):
        if not _notr_fonk(m.group(1), m.group(2)):
            out.append(f"{on}sabit renk {m.group(0)}")
    for m in FONT_BILDIRIM.finditer(metin):
        deger = m.group(1).strip().strip(",")
        if "var(--" in deger:
            continue
        tirnakli = re.findall(r"['\"`]([^'\"`]+)['\"`]", deger)
        # Tırnaksız değer yalnız CSS ad listesiyse sabittir; `H.yigin(t.font.baslik)` gibi JS ifadesi token'dan gelir.
        ciplak = [] if re.search(r"[().]", deger) else [x.strip() for x in deger.split(",")]
        if any(x and x.strip().lower() not in GENEL_FONT for x in [*tirnakli, *ciplak]):
            out.append(f"{on}sabit yazı tipi {deger[:60]}")
    for ad in font_adlari():
        if re.search(rf"['\"]{re.escape(ad)}['\"]", metin) and not any(ad in x for x in out):
            out.append(f"{on}sabit yazı tipi '{ad}'")
    return list(dict.fromkeys(out))


def param_ihlalleri(param: dict | None, *, kaynak: str = "") -> list[str]:
    """Şablon ve kompozisyon parametrelerinde sabit renk ya da font (ör. renk parametresine yazılmış altı haneli hex)."""
    if not param:
        return []
    return ihlaller(json.dumps(param, ensure_ascii=False), kaynak=kaynak)


def mesaj(bulgular: list[str]) -> str:
    """Editöre giden düzeltme cümlesi."""
    return ("tema kilidi: " + "; ".join(bulgular[:6])
            + ". Renk ve yazı tipini yalnız tema.css token'ından al: var(--vurgu), var(--ikincil), var(--zemin), var(--yazi), "
              "var(--soluk), var(--font), var(--font-govde), var(--agirlik), var(--ease) (library/motion/hf/SOZLESME.md).")
