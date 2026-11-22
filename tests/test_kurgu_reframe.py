"""Otomatik yeniden çerçeve: 16:9 klip 9:16 kareyi doldurur, yüzü yatayda izler."""
import cv2
import numpy as np
import pytest

from vedit import kurgu_reframe as kr, paths
from vedit.hizli import Proje
from vedit.schemas import Kurgu


def _kurgu(giris=0.0, hiz=1.0, sure=4.0, w=1920, h=1080):
    return Kurgu.model_validate({
        "kaynaklar": {"A": {"yol": "inputs:a.mp4", "sure": 20, "w": w, "h": h}},
        "izler": [{"id": "V1", "tur": "video"}],
        "klipler": [{"id": "k1", "iz": "V1", "bas": 0, "sure": sure, "tur": "video", "kaynak": "A",
                     "giris": giris, "hiz": hiz, "donus": {"opaklik": [{"t": 0, "v": 1}], "anim": ["opaklik"]}}],
    })


@pytest.fixture
def p(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "INPUTS", tmp_path / "in")
    monkeypatch.setattr(paths, "OUTPUTS", tmp_path / "out")
    return Proje("instagram", "x")


def test_olcek_ve_merkez(p):
    s = kr.donus_hesapla(p, _kurgu(), "k1", bul=lambda y, z: [0.5] * len(z))
    assert s["olcek"][0]["v"] == pytest.approx(3.1605, abs=1e-4)
    assert [k["v"] for k in s["x"]] == [0.0] and s["yuz_orani"] == 1.0 and s["anim"] == ["x"]


def test_x_siniri_ve_yon(p):
    sinir = (1080 * 1920 / 607.5 - 1080) / 2
    sol = kr.donus_hesapla(p, _kurgu(), "k1", bul=lambda y, z: [0.0] * len(z))
    sag = kr.donus_hesapla(p, _kurgu(), "k1", bul=lambda y, z: [1.0] * len(z))
    assert sol["x"][0]["v"] == pytest.approx(sinir, abs=0.1), "sol yüz için görüntü sağa kayar, bant açmadan"
    assert sag["x"][0]["v"] == pytest.approx(-sinir, abs=0.1)
    # 0.4: sınır içinde, tam formül
    orta = kr.donus_hesapla(p, _kurgu(), "k1", bul=lambda y, z: [0.4] * len(z))
    assert orta["x"][0]["v"] == pytest.approx(0.1 * 1920 / 607.5 * 1080, abs=0.1)


def test_zaman_eslemesi_giris_hiz(p):
    gorulen = []

    def bul(y, z):
        gorulen.extend(z)
        # yüz kaynak 12'de görünür (solda), 15'te sağa sıçrar
        return [None if t < 12 else 0.1 if t < 15 else 0.9 for t in z]

    s = kr.donus_hesapla(p, _kurgu(giris=10, hiz=2, sure=4), "k1", bul=bul)
    assert gorulen[0] == 10 and gorulen[-1] == 18, "kaynak aralığı giris..giris+sure*hiz"
    ts = [k["t"] for k in s["x"]]
    assert ts[0] == 0 and ts[-1] == 4
    assert all(2.0 <= t <= 3.0 for t in ts[1:-1]), "sıçrama klip zamanı (15-10)/2 = 2.5 civarı"
    assert s["x"][0]["v"] > 0 > s["x"][-1]["v"], "boşluk ilk bilinen yüzü (sol) tutar"
    assert 0 < s["yuz_orani"] < 1


def test_hareket_az_kare(p):
    def bul(y, z):
        return [0.2 + 0.6 * (t / 8) for t in z]  # 8 sn'de soldan sağa
    s = kr.donus_hesapla(p, _kurgu(sure=8), "k1", bul=bul)
    v = [k["v"] for k in s["x"]]
    assert 2 < len(v) < 33 and v == sorted(v, reverse=True), "yüz sağa gittikçe x azalır, az anahtar kare"


def test_uygula_saf(p):
    k = _kurgu()
    s = kr.donus_hesapla(p, k, "k1", bul=lambda y, z: [0.3] * len(z))
    yeni = kr.uygula(k, "k1", s)
    assert k.klipler[0].donus.x == [] and k.klipler[0].donus.anim == ["opaklik"]
    d = yeni.klipler[0].donus
    assert d.anim == ["opaklik", "x"] and d.olcek[0].v == s["olcek"][0]["v"] and len(d.opaklik) == 1


def test_cv2_yolu_yuzsuz_merkez(p):
    p.girdi.mkdir(parents=True)
    yol = p.girdi / "a.mp4"
    vw = cv2.VideoWriter(str(yol), cv2.VideoWriter_fourcc(*"mp4v"), 10, (320, 180))
    for i in range(20):
        vw.write(np.full((180, 320, 3), i * 10, np.uint8))
    vw.release()
    k = _kurgu(sure=1.5, w=None, h=None)
    s = kr.donus_hesapla(p, k, "k1", adim=0.5)
    assert s["yuz_orani"] == 0 and [x["v"] for x in s["x"]] == [0.0]
    assert s["olcek"][0]["v"] == pytest.approx(3.1605, abs=1e-4)
