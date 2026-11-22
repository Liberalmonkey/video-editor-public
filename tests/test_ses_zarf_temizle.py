"""Kazanç keyframe'i ve konuşma temizliği render miksinde gerçekten uygulanmalı."""
import json
import subprocess

import numpy as np
import soundfile as sf

from vedit import audio, kurgu, olaysesi, paths
from vedit.hizli import Proje
from vedit.schemas import Kurgu

SR = 48000


def _video(yol, sure):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"color=c=black:s=64x64:r=30:d={sure}", "-c:v", "libx264", "-preset", "ultrafast", str(yol)], check=True)


def test_zarf_dogrusal_db():
    d = np.ones((SR * 2, 2), dtype=np.float32)
    z = audio.zarf(d, [[0, 0], [2, -20]])
    assert abs(20 * np.log10(z[SR, 0]) + 10) < 0.05
    assert audio.zarf(d, None) is d


def test_olaylar_uret_zarf_ve_temizle(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "INPUTS", tmp_path / "in")
    monkeypatch.setattr(paths, "OUTPUTS", tmp_path / "out")
    k = Kurgu.model_validate({
        "kaynaklar": {"V": {"yol": "inputs:v.mp4", "sure": 9, "ses": True}, "M": {"yol": "inputs:m.wav", "sure": 9}},
        "izler": [{"id": "V1", "tur": "video"}, {"id": "A3", "tur": "ses"}],
        "klipler": [{"id": "v", "iz": "V1", "tur": "video", "kaynak": "V", "bas": 1, "sure": 4, "ses": {"temizle": True}},
                    {"id": "m", "iz": "A3", "tur": "ses", "kaynak": "M", "bas": 0, "sure": 6, "olay": {"muzik": True},
                     "ses": {"gain_db": -14, "kf": [{"t": 4, "v": -30}, {"t": 0, "v": -14}]}}],
    })
    o = kurgu.olaylar_uret(k, Proje("instagram", "x"))
    assert o["temizle"] == [[1, 5]]
    assert o["muzik"][0]["zarf"] == [[0, 0], [4, -16]], "sabit kazanca göre fark, sıralı"
    k.klipler[0].ses.temizle = False
    k.klipler[1].ses.kf = []
    o = kurgu.olaylar_uret(k, Proje("instagram", "x"))
    assert "temizle" not in o and "zarf" not in o["muzik"][0], "eski çıktı aynı"


def test_miks_zarfi_uygular(tmp_path):
    v, m = tmp_path / "v.mp4", tmp_path / "m.wav"
    _video(v, 4)
    t = np.arange(4 * SR) / SR
    x = 0.3 * np.sin(2 * np.pi * 300 * t)
    sf.write(m, np.stack([x, x], 1).astype(np.float32), SR)
    spec = {"video": str(v), "fps": 30, "sure": 4, "olaylar": [],
            "muzik": [{"src": str(m), "start": 0, "dur": 4, "gain_db": 0, "duck": False, "fade_in": 0.001, "fade_out": 0.001, "zarf": [[0, 0], [2, 0], [2.01, -20], [4, -20]]}]}
    y = tmp_path / "o.json"
    y.write_text(json.dumps(spec), encoding="utf-8")
    olaysesi.calistir(y, tmp_path / "c.mp4")
    wav = tmp_path / "c.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(tmp_path / "c.mp4"), "-vn", "-ac", "1", "-ar", str(SR), str(wav)], check=True)
    d, _ = sf.read(wav)
    rms = lambda a, b: np.sqrt(np.mean(d[int(a * SR):int(b * SR)] ** 2))
    fark = 20 * np.log10(rms(0.5, 1.8) / rms(2.3, 3.6))
    assert abs(fark - 20) < 1.5, fark


def test_temizlik_gurultuyu_azaltir():
    rng = np.random.default_rng(1)
    n = 3 * SR
    t = np.arange(n) / SR
    konusma = 0.3 * np.sin(2 * np.pi * 220 * t) * (t < 1.5)
    gurultu = 0.02 * rng.standard_normal(n)
    buf = np.stack([konusma + gurultu] * 2, 1).astype(np.float32)
    once = np.sqrt(np.mean(buf[int(2 * SR):int(2.9 * SR), 0] ** 2))
    temiz = audio.temizle(buf.copy(), [[0, 3]])
    sonra = np.sqrt(np.mean(temiz[int(2 * SR):int(2.9 * SR), 0] ** 2))
    ton_once = np.sqrt(np.mean(buf[int(0.3 * SR):int(1.2 * SR), 0] ** 2))
    ton_sonra = np.sqrt(np.mean(temiz[int(0.3 * SR):int(1.2 * SR), 0] ** 2))
    assert 20 * np.log10(once / sonra) > 6, "fon gürültüsü en az 6 dB iner"
    assert abs(20 * np.log10(ton_once / ton_sonra)) < 1.5, "konuşma seviyesi korunur"
    assert temiz.shape == buf.shape
