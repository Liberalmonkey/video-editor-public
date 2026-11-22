"""Sessizlik ve dolgu önerileri sekans zamanında, klibin görünen aralığında kalmalı."""
import subprocess

import numpy as np
import pytest
import soundfile as sf

from vedit import paths, sessizlik
from vedit.hizli import Proje
from vedit.schemas import Kurgu

SR = 48000


@pytest.fixture
def p(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "INPUTS", tmp_path / "in")
    monkeypatch.setattr(paths, "OUTPUTS", tmp_path / "out")
    return Proje("instagram", "x")


def kur(kelimeler, **klip):
    return Kurgu.model_validate({
        "kaynaklar": {"V": {"yol": "inputs:yok.mp4", "sure": 20}},  # dosya yok: yalnız kelime boşlukları
        "kelimeler": {"V": kelimeler},
        "izler": [{"id": "V1", "tur": "video"}],
        "klipler": [{"id": "c", "iz": "V1", "tur": "video", "kaynak": "V", "bas": 0, "sure": 4, **klip}],
    })


W = [{"w": "merhaba", "s": 0.0, "e": 1.0}, {"w": "dünya", "s": 2.5, "e": 3.0}, {"w": "Iıı,", "s": 3.0, "e": 3.4},
     {"w": "son", "s": 3.4, "e": 4.0}]


def test_bosluk_pay_ile(p):
    o = sessizlik.oneriler(p, kur(W))
    assert o[0] == {"bas": 1.12, "bit": 2.38, "tur": "sessizlik", "klip": "c", "neden": "1,5 sn sessizlik"}
    assert o[1] == {"bas": 3.0, "bit": 3.4, "tur": "dolgu", "klip": "c", "neden": "dolgu: ııı"}
    assert len(o) == 2


def test_dolgu_tutucu():
    assert sessizlik._dolgu("Hmm...") == "hmm" and sessizlik._dolgu("um") == "um"
    assert sessizlik._dolgu("şey") is None and sessizlik._dolgu("en") is None


def test_hiz_iki(p):
    o = sessizlik.oneriler(p, kur(W, bas=10, sure=2, hiz=2))
    assert o[0]["bas"] == 10.62 and o[0]["bit"] == 11.13 and o[0]["neden"] == "0,8 sn sessizlik"
    assert o[1]["tur"] == "dolgu" and (o[1]["bas"], o[1]["bit"]) == (11.5, 11.7)


def test_giris_ve_sinir(p):
    o = sessizlik.oneriler(p, kur(W, bas=5, sure=1.5, giris=2.0))
    # görünen kaynak 2,0–3,5: baştaki 0,5 sn boşluk eşiğin altında; dolgu 3,0'da → sekans 6,0
    assert o == [{"bas": 6.0, "bit": 6.4, "tur": "dolgu", "klip": "c", "neden": "dolgu: ııı"}]
    o = sessizlik.oneriler(p, kur(W, bas=0, sure=2.0, giris=0.5))
    assert all(0 <= a["bas"] < a["bit"] <= 2.0 for a in o)
    assert o == [{"bas": 0.62, "bit": 1.88, "tur": "sessizlik", "klip": "c", "neden": "1,5 sn sessizlik"}]


def test_enerji_yolu(p):
    p.girdi.mkdir(parents=True)
    t = np.arange(4 * SR) / SR
    x = (0.3 * np.sin(2 * np.pi * 220 * t)).astype(np.float32)
    x[int(1.0 * SR):int(2.5 * SR)] = 0  # gerçek sessizlik 1,0–2,5
    wav = p.girdi / "s.wav"
    sf.write(wav, np.stack([x, x], axis=1), SR)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=black:s=64x64:r=30:d=4", "-i", str(wav),
                    "-shortest", "-c:v", "libx264", "-preset", "ultrafast", "-c:a", "aac", str(p.girdi / "v.mp4")], check=True)
    k = Kurgu.model_validate({
        "kaynaklar": {"V": {"yol": "inputs:v.mp4", "sure": 4}},
        "kelimeler": {"V": [{"w": "a", "s": 0.0, "e": 0.5}, {"w": "b", "s": 3.0, "e": 4.0}]},  # boşluk 0,5–3,0; yarısı sesli
        "izler": [{"id": "V1", "tur": "video"}],
        "klipler": [{"id": "c", "iz": "V1", "tur": "video", "kaynak": "V", "bas": 0, "sure": 4}],
    })
    assert sessizlik.oneriler(p, k) == [], "boşlukta konuşma enerjisi varsa öneri yok"
    k.kelimeler = {}
    o = sessizlik.oneriler(p, k)
    assert len(o) == 1 and o[0]["tur"] == "sessizlik"
    assert abs(o[0]["bas"] - 1.12) < 0.05 and abs(o[0]["bit"] - 2.38) < 0.05
