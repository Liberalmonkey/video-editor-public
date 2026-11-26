"""Render yollarında sabit renk ve font yok; istisnalar gerekçeli beyaz listede (ADR 0043).

Kapsam: kendi render kodumuz (studio/remotion, library/motion/custom HTML, reel_kit.mjs), SplitReel giriş katmanı ve
src/vedit. Vendor panolar (library/boards) ve composer'ın diğer dosyaları giriş katmanından temalanır, burada taranmaz.
"""
import json
import re
from pathlib import Path

from vedit import paths

KOK = paths.ROOT
BEYAZ = KOK / "scripts" / "renk_beyaz_liste.json"
KAPSAM = [("studio/remotion", ("*.ts", "*.tsx")), ("library/motion/custom", ("*.html",)), ("library/motion/hf", ("*.html",)), ("src/vedit", ("*.py",)),
          ("openmontage/remotion-composer", ("reel_kit.mjs",)), ("openmontage/remotion-composer/src", ("SplitReel.tsx",))]


def _desen() -> re.Pattern:
    from vedit import tema_denetim
    return tema_denetim.sabit_desen()  # üretilen varlık denetimiyle aynı font listesi (ADR 0058)


def bulgular() -> dict[str, int]:
    d = _desen()
    sayim: dict[str, int] = {}
    for klasor, desenler in KAPSAM:
        k = KOK / klasor
        if not k.exists():
            continue
        for desen in desenler:
            for f in k.rglob(desen) if klasor != "openmontage/remotion-composer" else k.glob(desen):
                if "node_modules" in f.parts or f.name.endswith((".test.ts", ".test.tsx")):
                    continue
                n = len(d.findall(f.read_text(encoding="utf-8", errors="replace")))
                if n:
                    sayim[f.relative_to(KOK).as_posix()] = n
    return sayim


def test_beyaz_liste_disinda_sabit_renk_ve_font_yok():
    beyaz = json.loads(BEYAZ.read_text(encoding="utf-8"))["dosyalar"]
    for yol, b in beyaz.items():
        assert b.get("neden"), f"{yol}: beyaz liste girdisi gerekçesiz"
    asan = {y: n for y, n in bulgular().items() if n > beyaz.get(y, {}).get("en_cok", 0)}
    assert asan == {}, f"sabit renk/font (token kullan ya da gerekçeyle beyaz listeye ekle): {asan}"


def test_motion_htmlde_hic_sabit_renk_yok():
    assert not any(y.startswith("library/motion/custom/") for y in bulgular())
