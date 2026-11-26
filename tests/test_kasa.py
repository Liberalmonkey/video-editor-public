"""Kasa ve önizleme (ADR 0061): videodan kaydetme niyeti saklar; poster anlamlı kareyi alfa kırpımıyla gösterir."""
import json
import subprocess

import numpy as np
import pytest

from vedit import ff, kasa, kurgu, onizleme, paths
from vedit.hizli import Proje
from vedit.schemas import Kurgu


def alfa_webm(hedef, w=640, h=360, sure=1.0, kutu=(400, 40, 160, 80)):
    """Saydam zeminde ikinci yarıda beliren turuncu kutu (giriş animasyonu gibi)."""
    x, y, kw, kh = kutu
    # drawbox alfa kanalına yazmaz; opak kutu overlay ile gelir
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", f"color=c=black@0:s={w}x{h}:d={sure}:r=30,format=yuva420p",
                    "-f", "lavfi", "-i", f"color=c=0xFF7A00:s={kw}x{kh}:d={sure}:r=30,format=yuva420p", "-filter_complex",
                    f"[0][1]overlay={x}:{y}:enable='gte(t,{sure / 3})':format=auto,format=yuva420p",
                    "-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p", "-auto-alt-ref", "0", str(hedef)], check=True)
    return hedef


def test_kare_secimi():
    giris = np.array([0, 0, 0.1, 0.2, 0.3, 0.3, 0.3, 0.1])
    assert 4 <= onizleme.kare_sec(giris) <= 6  # oturmuş hâl, çıkış değil
    silme = np.array([0, 0.2, 0.45, 0.8, 1.0, 1.0, 0.6, 0.1])
    assert onizleme.kare_sec(silme, "transition") == 2  # yarıda, tam kaplama değil
    assert onizleme.kare_sec(np.zeros(6)) == 3  # boşsa orta kare
    tam = np.array([0.2, 0.5, 0.95, 0.99, 0.4])
    assert onizleme.kare_sec(tam) == 1  # tam ekran düz renk poster olmaz


def test_kirpim_payli_ve_en_az():
    x, y, cw, ch = onizleme.kirpim([None, (60, 4, 76, 12), None], 640, 360, 54)
    assert x > 300 and cw < 320 and ch < 200  # sağ üstteki kutuya oturur
    assert onizleme.kirpim([None], 640, 360, 54) == (0, 0, 640, 360)
    assert onizleme.kirpim([(10, 10, 20, 20)], 640, 360, 54, "transition") == (0, 0, 640, 360)


def test_uret_poster_kirpimli(tmp_path):
    webm = alfa_webm(tmp_path / "a.webm")
    r = onizleme.uret(webm, tmp_path / "o", w=640, h=360, sure=1.0)
    assert (tmp_path / "o/poster.jpg").is_file() and (tmp_path / "o/onizleme.mp4").is_file()
    v = ff.probe(tmp_path / "o/poster.jpg")["video"]
    assert (v["width"], v["height"]) == (onizleme.POSTER, onizleme.POSTER)
    assert r["an"] >= 0.33 and r["kirpim"][0] >= 300  # kutu belirdikten sonra, kutuya kırpılmış


@pytest.fixture
def proje(tmp_path, monkeypatch):
    lib = tmp_path / "library"
    for a, b in {"INPUTS": tmp_path / "in", "OUTPUTS": tmp_path / "out", "LIBRARY": lib, "ROOT": tmp_path,
                 "SFX_DIR": lib / "sfx", "MUSIC_DIR": lib / "music", "MOTION_DIR": lib / "motion"}.items():
        monkeypatch.setattr(paths, a, b)
    p = Proje("instagram", "x")
    p.girdi.mkdir(parents=True)
    alfa_webm(p.girdi / "m.webm")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "sine=d=0.5", str(p.girdi / "s.wav")], check=True)
    k = Kurgu.model_validate({
        "sekans": {"w": 1080, "h": 1920, "fps": 30},
        "kaynaklar": {"M": {"yol": "inputs:m.webm", "sure": 1}, "S": {"yol": "inputs:s.wav", "sure": 0.5}},
        "izler": [{"id": "V1", "tur": "video"}, {"id": "V2", "tur": "video"}, {"id": "A2", "tur": "ses"}],
        "klipler": [{"id": "c1", "iz": "V2", "tur": "motion", "kaynak": "M", "bas": 0, "sure": 1,
                     "sablon": {"ad": "sayi-rozeti", "param": {"sayi": 7}}},
                    {"id": "s1", "iz": "A2", "tur": "ses", "kaynak": "S", "bas": 0, "sure": 0.5},
                    {"id": "b1", "iz": "V1", "tur": "motion", "bas": 1, "sure": 2, "bilesen": {"ad": "ikon/zil", "param": {}}},
                    {"id": "t1", "iz": "V1", "tur": "metin", "bas": 3, "sure": 1, "metin": "x"}]})
    kurgu.yaz(p.work, k)
    return p


def test_kaydet_sablon_ses_bilesen(proje):
    e = kasa.kaydet(proje, "c1")
    assert e["tur"] == "sablon" and e["sablon"]["param"] == {"sayi": 7} and e["title"] == "sayi-rozeti"
    assert (paths.ROOT / e["file"]).is_file() and e["poster"].endswith("poster.jpg") and e["kaynak"] == {"proje": "instagram/x", "klip": "c1"}
    s = kasa.kaydet(proje, "s1", ad="Vuruş")
    assert s["tur"] == "sfx" and s["license"] == "kullanici" and s["id"] == "vurus" and s["file"].endswith(".wav")
    b = kasa.kaydet(proje, "b1")
    assert b["tur"] == "bilesen" and b["bilesen"]["ad"] == "ikon/zil" and "file" not in b
    assert kasa.kaydet(proje, "c1")["id"] == "sayi-rozeti-2"  # aynı ad yeni kimlik alır
    with pytest.raises(ValueError, match="metin"):
        kasa.kaydet(proje, "t1")
    assert [x["id"] for x in kasa.oku()] == ["sayi-rozeti", "vurus", "ikon-zil", "sayi-rozeti-2"]


def test_sil_ve_gizle(proje, monkeypatch):
    silinen = []
    from vedit.studio import ortak
    monkeypatch.setattr(ortak, "sil", lambda y: silinen.append(y))
    e = kasa.kaydet(proje, "s1")
    kasa.sil(e["id"])
    assert kasa.oku() == [] and silinen == [kasa.kok() / e["id"]]
    with pytest.raises(KeyError):
        kasa.sil("yok")
    assert kasa.gizle("fizik:domino") == {"fizik:domino"} and kasa.gizle("fizik:domino", False) == set()
