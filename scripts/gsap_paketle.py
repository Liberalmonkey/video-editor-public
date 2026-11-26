"""GSAP çekirdeği ile seçili eklentileri tek `library/vendor/gsap.min.js` dosyasında birleştirir.

WHY: bkz. wiki/decisions/0063-gsap-eklentileri-ve-threejs-hf.md. Render, Stüdyo önizlemesi, tek kompozisyon kopyası ve
motion kayıtları hep `library/vendor/gsap.min.js` dosyasını yükler. Eklentiler aynı dosyaya girince her yol onları
kendiliğinden alır; ek `<script>` bağlamak gerekmez (canlı gömme `<script src>` etiketlerini zaten atar).

Kaynaklar `library/vendor/gsap/` altındadır (npm `gsap`, sürüm HyperFrames'in çekirdeğiyle aynı). Dışarıda kalanlar:
ScrambleText, CustomWiggle ve EasePack içinde tohumsuz `Math.random` var; kare yeniden çizilince sonuç değişir.

Kullanım: python -X utf8 scripts/gsap_paketle.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
KAYNAK = KOK / "library" / "vendor" / "gsap"
HEDEF = KOK / "library" / "vendor" / "gsap.min.js"

# Sıra önemli: CustomEase, CustomBounce'tan önce gelir.
EKLENTILER = [
    "CustomEase", "CustomBounce", "SplitText", "DrawSVGPlugin", "MorphSVGPlugin",
    "MotionPathPlugin", "Physics2DPlugin", "PhysicsPropsPlugin", "TextPlugin",
]

# Tema easing token'ı (ADR 0062) → adlı GSAP eğrisi. Token yoksa yedek eğri kaydedilir.
KAYIT = r"""
;(function () {
  var g = window.gsap;
  if (!g) return;
  var adlar = %s;
  var ps = [];
  for (var i = 0; i < adlar.length; i++) if (window[adlar[i]]) ps.push(window[adlar[i]]);
  g.registerPlugin.apply(g, ps);
  var egriler = { giris: ["--ease-enter", "expo.out"], cikis: ["--ease-exit", "power2.in"],
    vurgu: ["--ease-emphasis", "back.out(1.7)"], oturma: ["--ease-settle", "power3.out"] };
  function yol(v) {
    var m = /cubic-bezier\(([^)]+)\)/.exec(v || "");
    if (!m) return null;
    var n = m[1].split(",").map(parseFloat);
    if (n.length !== 4 || n.some(isNaN)) return null;
    return "M0,0 C" + n[0] + "," + n[1] + " " + n[2] + "," + n[3] + " 1,1";
  }
  var cs = null;
  try { cs = getComputedStyle(document.documentElement); } catch (e) { cs = null; }
  for (var ad in egriler) {
    var d = yol(cs && cs.getPropertyValue(egriler[ad][0]));
    if (d && window.CustomEase) window.CustomEase.create(ad, d);
    else g.registerEase(ad, g.parseEase(egriler[ad][1]));
  }
})();
"""


def surum(metin: str) -> str | None:
    m = re.search(r"\b(?:GSAP|\w+)\s+(\d+\.\d+\.\d+)", metin[:300])
    return m.group(1) if m else None


def paketle() -> Path:
    cekirdek = (KAYNAK / "gsap.min.js").read_text(encoding="utf-8")
    ana = surum(cekirdek)
    parcalar = [cekirdek]
    for ad in EKLENTILER:
        metin = (KAYNAK / f"{ad}.min.js").read_text(encoding="utf-8")
        if surum(metin) != ana:
            raise SystemExit(f"{ad} sürümü ({surum(metin)}) çekirdekle ({ana}) aynı değil")
        parcalar.append(metin)
    parcalar.append(KAYIT % ("[" + ", ".join(f'"{a}"' for a in EKLENTILER) + "]"))
    HEDEF.write_text("\n;\n".join(parcalar), encoding="utf-8", newline="\n")
    return HEDEF


if __name__ == "__main__":
    yol = paketle()
    print(f"{yol.relative_to(KOK)}: {yol.stat().st_size // 1024} KB, eklenti {len(EKLENTILER)}", file=sys.stdout)
