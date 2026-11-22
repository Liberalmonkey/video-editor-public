"""Native motion bileşenlerinde yasak kalıplar (ADR 0045, studio/remotion/motion/SOZLESME.md).

WHY: Remotion kareyi tek tek çizer; CSS animasyonu ve geçişi karelere bağlı değildir, render'da titrer ya da hiç oynamaz.
Doğrusal eğri hareketi mekanik gösterir (instagram/1: her grafik aynı scale-pop).
"""

import re

from vedit import paths

KOK = paths.ROOT / "studio" / "remotion" / "motion"
YASAK = [
    (re.compile(r"@keyframes"), "CSS @keyframes"),
    (re.compile(r"\banimation\s*:"), "CSS animation"),
    (re.compile(r"\btransition\s*:"), "CSS transition"),
    (re.compile(r"\banimation[A-Z]\w*\s*:"), "CSS animation* özelliği"),
    (re.compile(r"Easing\.linear"), "doğrusal eğri"),
    (re.compile(r"z\.object\("), "z.object yerine z.strictObject"),
    # ADR 0041 kapısı (R1 ve R2'de iki kez): elle anticipation formülü işareti ters ve hazırlıkta öğeyi gizli bırakıyordu.
    (re.compile(r"\ba\.f\s*[<>]=?\s*\d"), "elle anticipation (a.f < N); a.ters ve a.belir kullan"),
]
# Yazı boyu alt sınırı: 1080 kısa kenarda 28 px (Kadraj kuralı K0006). `xBoy = Math.max(N * u, ...)` ya da fontSize'da N >= 28.
YAZI_BOY = re.compile(r"(fontSize|\w*[Bb]oy\w*)\s*[:=]\s*Math\.max\(\s*(\d+(?:\.\d+)?)\s*\*\s*u\b")


def test_yazi_boyu_alt_siniri():
    hatalar = []
    for f in KOK.rglob("*.tsx"):
        for i, satir in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            for m in YAZI_BOY.finditer(satir):
                if float(m.group(2)) < 28:
                    hatalar.append(f"{f.relative_to(paths.ROOT)}:{i}: {m.group(1)} alt sınırı {m.group(2)}*u < 28*u")
    assert not hatalar, "\n".join(hatalar)


def test_motion_bilesenlerinde_yasak_kalip_yok():
    hatalar = []
    for f in KOK.rglob("*.ts*"):
        if f.name.endswith(".test.ts"):
            continue
        for i, satir in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            if satir.lstrip().startswith("//"):
                continue
            for d, ad in YASAK:
                if d.search(satir):
                    hatalar.append(f"{f.relative_to(paths.ROOT)}:{i}: {ad}")
    assert not hatalar, "\n".join(hatalar)
