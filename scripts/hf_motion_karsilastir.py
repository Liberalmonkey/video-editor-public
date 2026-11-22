"""Motion kütüphanesi kayıtlarının HyperFrames üretimini eski Playwright üretimiyle karşılaştırır (ADR 0051).

Kullanım:
    .venv/Scripts/python -X utf8 scripts/hf_motion_karsilastir.py --eksik --en-cok 12 [--tema varsayilan]
    .venv/Scripts/python -X utf8 scripts/hf_motion_karsilastir.py ok-ciz fiyat-etiketi

Etkin (arşivlenmemiş) her kaydı iki yolla üretir (`hf_motion.render`, `pano.render`), gri zemine bindirip kare kare
fark ölçer. Sonuç `work/hf-motion/sonuc.json` (kayıt HTML'i, tema ya da hf_motion değişince yeniden ölçülür).
WHY: üretim Playwright'tan HyperFrames'e geçti; kayıt HTML'i değişmediği için çıktı birebir aynı olmalı.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KOK / "src"))

from vedit import hf_motion, motion, pano  # noqa: E402

CIKTI = KOK / "work" / "hf-motion"
SONUC = CIKTI / "sonuc.json"


def etkin() -> list[str]:
    d = json.loads((KOK / "library" / "motion" / "manifest.json").read_text(encoding="utf-8"))
    return sorted(e["id"] for e in d["entries"] if e.get("site") == "custom" and not e.get("arsiv"))


def ozet(k: str, tema: str) -> str:
    s = hashlib.sha1()
    for f in (motion.kok() / k / f"{k}.html", Path(hf_motion.__file__), motion.tema_yolu(tema)):
        s.update(f.read_bytes() if f and f.is_file() else b"")
    return s.hexdigest()[:12]


def kareler(v: Path, w: int, h: int):
    import numpy as np
    ham = subprocess.run(["ffmpeg", "-v", "error", "-c:v", "libvpx-vp9", "-i", str(v), "-vf", f"scale={w // 2}:{h // 2}",
                          "-f", "rawvideo", "-pix_fmt", "rgba", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(ham, np.uint8).reshape(-1, h // 2, w // 2, 4)


def olc(k: str, tema: str) -> dict:
    import numpy as np
    m = motion.meta(k)
    html = motion.kok() / k / f"{k}.html"
    css = motion.tema_yolu(tema)
    pr = {a: p["vars"] for a, p in (m.get("param") or {}).items()} or None
    a, b = CIKTI / f"{k}.pw.webm", CIKTI / f"{k}.hf.webm"
    ortak = dict(sure=m["sure"], w=m["w"], h=m["h"], css=css, param=pr, son_tam=not m.get("loop"))
    hf_motion.render(html, b, **ortak)
    pano.render(html, a, **ortak)
    ka, kb = kareler(a, m["w"], m["h"]), kareler(b, m["w"], m["h"])
    n = min(len(ka), len(kb))
    toplam, ornek, gorunur = 0.0, [], 0
    for i in range(n):
        x, y = ka[i].astype(np.float32), kb[i].astype(np.float32)
        bx = x[..., :3] * (x[..., 3:4] / 255) + 40 * (1 - x[..., 3:4] / 255)
        by = y[..., :3] * (y[..., 3:4] / 255) + 40 * (1 - y[..., 3:4] / 255)
        f = np.abs(bx - by).max(axis=2)
        toplam += float(f.mean())
        ornek.append(f[::3, ::3].ravel())
        gorunur += int(x[..., 3].max() > 0)
    ort, p99 = toplam / max(1, n), float(np.percentile(np.concatenate(ornek), 99)) if ornek else 0.0
    iyi = len(ka) == len(kb) and gorunur > 0 and ort < 1.5 and p99 < 30
    return {"ort": round(ort, 2), "p99": round(p99, 1), "kare": [len(ka), len(kb)], "gorunur": gorunur,
            "sonuc": "TAMAM" if iyi else "FARK", "ozet": ozet(k, tema)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("adlar", nargs="*")
    ap.add_argument("--eksik", action="store_true")
    ap.add_argument("--en-cok", type=int, default=0)
    ap.add_argument("--tema", default="varsayilan")
    a = ap.parse_args()
    CIKTI.mkdir(parents=True, exist_ok=True)
    kayit = json.loads(SONUC.read_text(encoding="utf-8")) if SONUC.exists() else {}
    anahtar = lambda k: f"{k}@{a.tema}"
    adlar = a.adlar or [k for k in etkin() if not a.eksik or kayit.get(anahtar(k), {}).get("sonuc") != "TAMAM"
                        or kayit[anahtar(k)].get("ozet") != ozet(k, a.tema)]
    if a.en_cok:
        adlar = adlar[:a.en_cok]
    for k in adlar:
        r = olc(k, a.tema)
        kayit[anahtar(k)] = r
        SONUC.write_text(json.dumps(kayit, ensure_ascii=False, indent=1), encoding="utf-8")
        for f in CIKTI.glob(f"{k}.*.webm"):
            f.unlink()
        print(f"{k:28} ort {r['ort']:5.2f} %99 {r['p99']:5.1f} kare {r['kare']}  {r['sonuc']}", flush=True)
    tamam = sum(1 for k in etkin() if kayit.get(anahtar(k), {}).get("sonuc") == "TAMAM" and kayit[anahtar(k)].get("ozet") == ozet(k, a.tema))
    print(f"Toplam: {tamam}/{len(etkin())} TAMAM ({a.tema})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
