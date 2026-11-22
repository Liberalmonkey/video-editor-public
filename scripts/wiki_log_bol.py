"""wiki/log.md 150 satırı aşınca en eski girdileri wiki/log.partN.md olarak arşivler. İçerik eksilmez.

Arşiv bölümleri değiştirilmez; her çalıştırma yeni numarayla yeni bölüm açar. Yeni girdi her zaman log.md sonuna eklenir.

Kullanım:
  python scripts/wiki_log_bol.py            # gerekirse böl
  python scripts/wiki_log_bol.py --denetle  # bölme gerekiyorsa çıkış kodu 1
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

WIKI = Path(__file__).resolve().parents[1] / "wiki"
SINIR = 150   # .md dosyası satır sınırı
KALAN = 90    # bölmeden sonra log.md'de kalacak girdi satırı; yeni girdilere yer bırakır
ARSIV_SATIRI = "Arşiv: "


def girdiler(satirlar: list[str]) -> tuple[list[str], list[list[str]]]:
    """Baş kısım ve `## [` ile başlayan girdi blokları."""
    ilk = next((i for i, s in enumerate(satirlar) if s.startswith("## [")), len(satirlar))
    bloklar: list[list[str]] = []
    for s in satirlar[ilk:]:
        if s.startswith("## [") or not bloklar:
            bloklar.append([])
        bloklar[-1].append(s)
    return satirlar[:ilk], bloklar


def bol(bloklar: list[list[str]]) -> tuple[list[list[str]], list[list[str]]]:
    """(arşive gidecek en eski bloklar, log.md'de kalanlar). En az bir girdi kalır."""
    kalan = list(bloklar)
    arsiv: list[list[str]] = []
    while len(kalan) > 1 and sum(map(len, kalan)) > KALAN and sum(map(len, arsiv)) + len(kalan[0]) <= SINIR - 15:
        arsiv.append(kalan.pop(0))
    return arsiv, kalan


def main() -> int:
    log = WIKI / "log.md"
    satirlar = log.read_text(encoding="utf-8").split("\n")
    if len(satirlar) <= SINIR:
        print(f"wiki/log.md {len(satirlar)} satır, bölme gerekmiyor.")
        return 0
    if "--denetle" in sys.argv:
        print(f"wiki/log.md {len(satirlar)} satır (sınır {SINIR}): python scripts/wiki_log_bol.py")
        return 1
    bas, bloklar = girdiler(satirlar)
    arsiv, kalan = bol(bloklar)
    if not arsiv:
        print("Bölünecek girdi yok (tek girdi sınırı aşıyor).")
        return 1
    n = 1 + max((int(m.group(1)) for p in WIKI.glob("log.part*.md") if (m := re.fullmatch(r"log\.part(\d+)", p.stem))), default=0)
    tarih = lambda b: re.match(r"## \[(\d{4}-\d{2}-\d{2})\]", b[0]).group(1)
    a, b = tarih(arsiv[0]), tarih(arsiv[-1])
    govde = "\n".join(s for blok in arsiv for s in blok).rstrip("\n") + "\n"
    (WIKI / f"log.part{n}.md").write_text(
        f"---\ntype: overview\ntitle: İşlem Günlüğü, bölüm {n} ({a} - {b})\ntags: [meta]\ncreated: {a}\nupdated: {b}\n---\n\n"
        f"# İşlem Günlüğü, bölüm {n}\n\nArşiv: {a} - {b}. Değiştirilmez; yeni girdi [[log]] sonuna eklenir.\n\n" + govde,
        encoding="utf-8", newline="")
    bag = f"[[log.part{n}]] ({a} - {b})"
    if any(s.startswith(ARSIV_SATIRI) for s in bas):
        bas = [s + ", " + bag if s.startswith(ARSIV_SATIRI) else s for s in bas]
    else:
        bas = [*bas, ARSIV_SATIRI + bag, ""]
    log.write_text("\n".join(bas + [s for blok in kalan for s in blok]), encoding="utf-8", newline="")
    once, sonra = sum(map(len, bloklar)), sum(map(len, arsiv)) + sum(map(len, kalan))
    assert once == sonra, "girdi satırı kayboldu"
    print(f"log.part{n}.md: {len(arsiv)} girdi ({a} - {b}); log.md'de {len(kalan)} girdi kaldı.")
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
