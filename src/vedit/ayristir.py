"""Ses ayırma: Demucs (htdemucs, 2 ya da 4 kanal) ile konuşmayı müzikten ayırır.

Torch ana .venv'e girmez; Demucs ayrı `.venv-ayristir` içinde alt süreç olarak çalışır.
Model ağırlıkları ilk kullanımda bir kez indirilir: ~/.cache/huggingface/hub/models--adefossez--HTDemucs (~81 MB, HF_HOME ile değişir).
"""

# WHY: bkz. wiki/decisions/0024-oneri-araclari.md

from __future__ import annotations

import json
import shutil
import subprocess
import time
from pathlib import Path

from . import ff, paths
from .hizli import _ozet

VENV = paths.ROOT / ".venv-ayristir"
PY = VENV / "Scripts" / "python.exe"


def hazir() -> bool:
    if not PY.exists():
        return False
    return subprocess.run([str(PY), "-c", "import demucs.separate"], capture_output=True).returncode == 0


def kurulum_komutu() -> str:
    return ("Ses ayırma (Demucs) kurulu değil. Proje kökünde şunları çalıştır:\n"
            "  py -3.12 -m venv .venv-ayristir\n"
            "  .venv-ayristir\\Scripts\\python -m pip install torch==2.15.0 torchaudio==2.11.1 "
            "--index-url https://download.pytorch.org/whl/cpu\n"
            "  .venv-ayristir\\Scripts\\python -m pip install demucs==4.1.0 soundfile==0.14.0\n"
            "İlk ayırmada htdemucs modeli (~81 MB, Hugging Face önbelleğine) bir kez indirilir.")


# WHY: bkz. wiki/decisions/0034-ses-araclari.md. 4 kanal aynı htdemucs ağırlığıdır; `muzik` konuşmasız toplam olarak her iki kipte de vardır.
DEMUCS_AD = {"vocals": "vokal", "no_vocals": "muzik", "drums": "davul", "bass": "bas", "other": "diger"}
KIPLER = {2: ("vokal", "muzik"), 4: ("vokal", "davul", "bas", "diger", "muzik")}


def _yollar(kaynak: Path, hedef: Path, stem: int) -> tuple[dict[str, Path], Path]:
    if stem not in KIPLER:
        raise ValueError("stem 2 ya da 4 olmalı")
    on = kaynak.stem if stem == 2 else f"{kaynak.stem}.s4"  # 4 kanallı vokal ayrı dosya: iki kipin önbelleği karışmaz
    return {ad: hedef / f"{on}.{ad}.wav" for ad in KIPLER[stem]}, hedef / f"{on}.ayristir.json"


def onbellekte(kaynak: Path, hedef_klasor: Path, stem: int = 2) -> dict | None:
    """Ayırma daha önce yapıldıysa tüm kanal yolları, yoksa None. Demucs çalıştırmaz."""
    yollar, iz = _yollar(kaynak, hedef_klasor, stem)
    if iz.exists() and all(y.exists() for y in yollar.values()) and json.loads(iz.read_text(encoding="utf-8")).get("ozet") == _ozet(kaynak):
        return yollar
    return None


def ayir(kaynak: Path, hedef_klasor: Path, *, stem: int = 2) -> dict:
    """kaynak'ın sesini ayırır (48 kHz stereo wav): stem=2 vokal+müzik, stem=4 vokal+davul+bas+diger+müzik. 'sure' bu çağrının süresidir (sn)."""
    t0 = time.time()
    hedef_klasor.mkdir(parents=True, exist_ok=True)
    yollar, iz = _yollar(kaynak, hedef_klasor, stem)
    if (hazir_yollar := onbellekte(kaynak, hedef_klasor, stem)):
        return {**hazir_yollar, "sure": round(time.time() - t0, 2), "onbellek": True}
    if not hazir():
        raise RuntimeError(kurulum_komutu())
    gecici = hedef_klasor / f"_ayristir_{kaynak.stem}"
    try:
        girdi = ff.extract_audio(kaynak, gecici / "girdi.wav", sr=44100, mono=False)  # htdemucs 44.1 kHz bekler
        komut = [str(PY), "-m", "demucs.separate", "-n", "htdemucs", *(["--two-stems", "vocals"] if stem == 2 else []), "-d", "cpu",
                 "-o", str(gecici), "--filename", "{stem}.{ext}", str(girdi)]
        r = subprocess.run(komut, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if r.returncode != 0:
            raise RuntimeError(f"Demucs başarısız ({r.returncode}):\n{(r.stderr or '')[-1500:]}")
        ham = gecici / "htdemucs"
        for dad, ad in DEMUCS_AD.items():
            if ad in yollar and (ham / f"{dad}.wav").exists():
                ff.ffmpeg("-i", str(ham / f"{dad}.wav"), "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le", str(yollar[ad]))
        if stem == 4:  # amix girişleri n'e böler; volume=3 toplamı geri getirir
            ff.ffmpeg(*[x for ad in ("davul", "bas", "diger") for x in ("-i", str(yollar[ad]))], "-filter_complex", "amix=inputs=3,volume=3",
                      "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le", str(yollar["muzik"]))
    finally:
        shutil.rmtree(gecici, ignore_errors=True)
    iz.write_text(json.dumps({"ozet": _ozet(kaynak), "kaynak": kaynak.name, "stem": stem}), encoding="utf-8")
    return {**yollar, "sure": round(time.time() - t0, 2), "onbellek": False}


BICIMLER = {"wav": ["-c:a", "pcm_s16le"], "mp3": ["-c:a", "libmp3lame", "-q:a", "2"], "m4a": ["-c:a", "aac", "-b:a", "192k"]}


def ses_cikar(kaynak: Path, hedef_klasor: Path, bicim: str = "wav") -> Path:
    """Videonun sesini 48 kHz stereo dosya olarak yazar; var olan dosyanın üzerine yazmaz (ad.wav, ad-2.wav …)."""
    if bicim not in BICIMLER:
        raise ValueError(f"Biçim {', '.join(BICIMLER)} olmalı")
    if not ff.probe(kaynak).get("audio"):
        raise RuntimeError(f"{kaynak.name}: ses yok")
    hedef_klasor.mkdir(parents=True, exist_ok=True)
    f, n = hedef_klasor / f"{kaynak.stem}.{bicim}", 2
    while f.exists():
        f, n = hedef_klasor / f"{kaynak.stem}-{n}.{bicim}", n + 1
    ff.ffmpeg("-i", str(kaynak), "-vn", "-ar", "48000", "-ac", "2", *BICIMLER[bicim], str(f))
    return f
