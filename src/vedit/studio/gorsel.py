"""Timeline görselleri: dalga formu tepeleri ve film şeridi. Önbellekli, kaynak değişirse yenilenir.

WHY: tarayıcıda çözmek uzun videoda belleği doldurur; ffmpeg + numpy sunucuda bir kez üretir (Eyeline Edit yöntemi).
"""

from __future__ import annotations

import json
import os
import subprocess
import threading
from pathlib import Path
from urllib.parse import quote


from ..tembel import Tembel

# WHY: Stüdyo açılışında yüklenmesin (ADR 0050)
np = Tembel("numpy")

from .. import ff, hizli

HZ = 50
SR = 8000
SERIT_YUKSEKLIK = 54
SERIT_EN_COK = 240
_sinir = threading.BoundedSemaphore(2)  # WHY: proxy ve render ile yarışıp makineyi kilitlemesin


def _anahtar(f: Path) -> str:
    return f"{f.stem[:40]}-{hizli._ozet(f)}"


def peaks(pcm: np.ndarray, sr: int = SR, hz: int = HZ) -> list[int]:
    """İşaretli 16 bit örneklerden pencere başına 0-255 tepe."""
    adim = max(1, sr // hz)
    n = len(pcm) // adim
    if not n:
        return []
    tepe = np.abs(pcm[:n * adim].astype(np.int32)).reshape(n, adim).max(axis=1)
    return (tepe * 255 // 32768).clip(0, 255).astype(int).tolist()


def peak(p: hizli.Proje, f: Path) -> Path:
    hedef = p.work / "gorsel" / f"{_anahtar(f)}.peak.json"
    if hedef.exists():
        return hedef
    hedef.parent.mkdir(parents=True, exist_ok=True)
    with _sinir:
        r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(f), "-vn", "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"], capture_output=True)
    # WHY: sesi olmayan dosya hata değil, boş dalga formudur.
    veri = peaks(np.frombuffer(r.stdout, dtype=np.int16)) if r.returncode == 0 else []
    gecici = hedef.with_suffix(".tmp")
    gecici.write_text(json.dumps({"hz": HZ, "tepe": veri}), encoding="utf-8")
    os.replace(gecici, hedef)
    return hedef


def serit(p: hizli.Proje, f: Path) -> dict:
    """Yatay kare şeridi. Kısa videoda saniyede bir, uzunda en çok 240 kare."""
    if f.suffix.lower() not in hizli.VIDEO:
        return {"n": 0}
    sure = ff.probe_ob(f).get("duration") or 0
    k = max(1.0, sure / SERIT_EN_COK)
    n = max(1, int(sure / k))
    ad = f"{_anahtar(f)}.serit.jpg"
    hedef = p.work / "proxy" / ad
    if not hedef.exists():
        hedef.parent.mkdir(parents=True, exist_ok=True)
        gecici = hedef.with_name(f".{hedef.stem}.tmp.jpg")
        with _sinir:
            ff.ffmpeg("-i", str(f), "-vf", f"fps=1/{k:.3f},scale=-2:{SERIT_YUKSEKLIK},tile={n}x1", "-frames:v", "1", "-q:v", "6", str(gecici))
        os.replace(gecici, hedef)
    return {"n": n, "k": k, "url": f"/dosya/{p.studyo}/{p.ad}/proxy/{quote(ad)}"}
