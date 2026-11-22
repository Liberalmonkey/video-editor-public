"""Ritim ve senkron: onsetler sekans zamanına doğru izdüşer, ses-görüntü kayması kare cinsinden bulunur (ADR 0039)."""
import subprocess

import cv2
import numpy as np
import pytest
import soundfile as sf

from vedit import paths, ritim, senkron
from vedit.hizli import Proje
from vedit.schemas import Kurgu

FPS = 30
OLAYLAR = [0.6, 1.3, 2.5, 3.1, 4.4]  # düzensiz: çapraz ilişkinin tek tepesi olsun


@pytest.fixture
def p(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "INPUTS", tmp_path / "in")
    monkeypatch.setattr(paths, "OUTPUTS", tmp_path / "out")
    pr = Proje("youtube-animasyon", "x")
    pr.girdi.mkdir(parents=True)
    return pr


def klip_yaz(hedef, kayma_kare: int, sure=5.0, olaylar=OLAYLAR):
    """Her olayda beyaz flaş (görüntü) ve kayma_kare sonra tık (ses)."""
    v = hedef.with_suffix(".v.mp4")
    w = cv2.VideoWriter(str(v), cv2.VideoWriter_fourcc(*"mp4v"), FPS, (320, 180))
    for n in range(int(sure * FPS)):
        t = n / FPS
        acik = any(0 <= t - o < 3 / FPS for o in olaylar)
        w.write(np.full((180, 320, 3), 255 if acik else 20, np.uint8))
    w.release()
    sr = 48000
    y = np.zeros(int(sure * sr), np.float32)
    for o in olaylar:
        i = int((o + kayma_kare / FPS) * sr)
        y[i:i + 2400] += (np.random.default_rng(1).standard_normal(2400) * np.exp(-np.arange(2400) / 300)).astype(np.float32) * 0.8
    a = hedef.with_suffix(".wav")
    sf.write(a, y, sr)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(v), "-i", str(a), "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-shortest", str(hedef)], check=True)
    return hedef


def kur(**klip):
    return Kurgu.model_validate({
        "sekans": {"w": 1920, "h": 1080, "fps": FPS},
        "kaynaklar": {"V": {"yol": "inputs:k.mp4", "sure": 5}},
        "izler": [{"id": "V1", "tur": "video"}, {"id": "A1", "tur": "ses"}],
        "klipler": [{"id": "c", "iz": "V1", "tur": "video", "kaynak": "V", "bas": 0, "sure": 5, **klip}],
    })


@pytest.mark.parametrize("kayma", [4, -3, 0])
def test_kayma_bulunur(p, kayma):
    klip_yaz(p.girdi / "k.mp4", kayma)
    o = senkron.olc(p, kur(), "c")
    assert abs(o.kayma_kare - kayma) <= 1, o.metin()
    assert not o.belirsiz


def test_uygula_ayrik_sesi_kaydirir(p):
    k = kur(bag="b1", ses_kapali=True)
    k.klipler.append(k.klipler[0].model_copy(update={"id": "s", "iz": "A1", "tur": "ses", "bag": "b1", "ses_kapali": False,
                                                     "olay": {"konusma": True}}))
    msg = senkron.uygula(k, senkron.Olcum("c", 3, 0.9, 0.4, FPS))
    assert k.klipler[1].giris == pytest.approx(0.1) and "1 ses klibi" in msg


def test_uygula_ayrilmamis_uyarir(p):
    with pytest.raises(SystemExit, match="Shift\\+A"):
        senkron.uygula(kur(), senkron.Olcum("c", 3, 0.9, 0.4, FPS))


def test_ritim_izdusum(p):
    klip_yaz(p.girdi / "k.mp4", 0)
    r = ritim.sekans(p, kur(bas=10, giris=1.0, sure=3.0))
    ts = [o["t"] for o in r["onsets"]]
    # Kaynakta 1,3 / 2,5 / 3,1 sn: sekansta 10 + (t - 1).
    for beklenen in (10.3, 11.5, 12.1):
        assert min(abs(t - beklenen) for t in ts) < 0.02, ts
    assert all(10 <= t < 13 for t in ts)
    assert r["vurgular"] and "Ses vurgu anları" in ritim.ozet(r)


def test_yakin():
    assert ritim.yakin(1.0, [0.5, 1.02, 3]) == pytest.approx(0.02)
    assert ritim.yakin(1.0, []) is None


def test_hareketsiz_klip_belirsiz(p):
    klip_yaz(p.girdi / "k.mp4", 0, olaylar=[])
    assert senkron.olc(p, kur(), "c").belirsiz


def test_viseme_sinif_ve_on_acilma(p):
    from vedit import viseme
    sr = 48000
    parca = [(0.5, 0), (0.5, 500), (0.5, 1600), (0.5, 3500), (0.5, 0)]  # (sn, Hz); 0 sessizlik
    y = np.concatenate([np.zeros(int(s * sr)) if hz == 0 else 0.5 * np.sin(2 * np.pi * hz * np.arange(int(s * sr)) / sr) for s, hz in parca])
    sf.write(p.girdi / "ses.wav", y.astype(np.float32), sr)
    k = Kurgu.model_validate({
        "sekans": {"w": 1920, "h": 1080, "fps": FPS}, "kaynaklar": {"S": {"yol": "inputs:ses.wav", "sure": 2.5}},
        "izler": [{"id": "V1", "tur": "video"}, {"id": "A1", "tur": "ses"}],
        "klipler": [{"id": "s", "iz": "A1", "tur": "ses", "kaynak": "S", "bas": 1.0, "sure": 2.5, "olay": {"konusma": True}}]})
    s = viseme.sekans(p, k)
    assert len(s) == int(3.5 * FPS)
    kare = lambda t: s[int(t * FPS)]
    assert kare(0.5) == "K" and kare(1.2) == "K"            # klipten önce ve klibin sessiz başında kapalı
    assert kare(1.75) == "O" and kare(2.25) == "A" and kare(2.75) == "E"
    assert kare(3.3) == "K"
    ilk = s.index(next(ch for ch in s if ch != "K"))
    assert abs(ilk - 1.5 * FPS) <= 2  # ses 1,5 sn'de başlar; ağız en çok 2 kare önce açılır


def test_vurgu_cevresinden_siyrilan_vurus(tmp_path):
    sr = 22050
    y = np.zeros(sr * 6, np.float32)
    rng = np.random.default_rng(3)
    for i, t in enumerate(np.arange(0.5, 5.5, 0.5)):
        g = 0.9 if abs(t - 3.0) < 1e-6 else 0.25  # 3. saniyede tek güçlü vuruş, gövdeli (bas)
        n = np.arange(2000)
        dalga = rng.standard_normal(2000) * 0.3 + np.sin(2 * np.pi * (80 if g > 0.5 else 2000) * n / sr)
        y[int(t * sr): int(t * sr) + 2000] += (dalga * np.exp(-n / 400) * g).astype(np.float32)
    sf.write(tmp_path / "v.wav", y, sr)
    a = ritim.analiz(tmp_path / "v.wav", tmp_path / "onb")
    en = max(a["onsets"], key=lambda o: o["guc"])
    assert abs(en["t"] - 3.0) < 0.05, a["onsets"]
