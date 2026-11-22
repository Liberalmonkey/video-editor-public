"""Timeline'daki ses render'da aynı yerde, aynı kırpımla çalmalı."""
import json
import subprocess

import numpy as np
import pytest
import soundfile as sf

from vedit import ff, hizli, kurgu, olaysesi, paths
from vedit.hizli import Proje
from vedit.schemas import Kurgu
from vedit.studio import app as sunucu

SR = 48000


def tik(yol, t_tepe, sure=1.0):
    x = np.zeros(int(sure * SR), dtype=np.float32)
    i = int(t_tepe * SR)
    x[i:i + 480] = 0.9
    sf.write(yol, np.stack([x, x], axis=1), SR)


def tepe_ani(video, tmp):
    wav = tmp / "cik.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-vn", "-ac", "1", "-ar", str(SR), str(wav)], check=True)
    d, _ = sf.read(wav)
    return np.argmax(np.abs(d)) / SR


def test_planla_kesin_olay_dusmez():
    spec = {"fps": 30, "olaylar": [
        {"t": 1.0, "tur": "sfx", "dosya": "a.wav", "kesin": True, "gain_db": -6},
        {"t": 1.1, "tur": "sfx", "dosya": "b.wav", "kesin": True, "gain_db": -6},
        {"t": 5.0, "tur": "sfx", "dosya": "c.wav", "gain_db": -6}, {"t": 5.1, "tur": "sfx", "dosya": "d.wav", "gain_db": -6},
    ]}
    p = olaysesi.planla(spec, [], {})
    assert sorted(y["dosya"] for y in p["yerler"]) == ["a.wav", "b.wav", "c.wav"], "eski olay kuralı sürer"
    assert len(p["dusen"]) == 1


def test_kesin_olayda_capa_uygulanmaz():
    # slayt orta çapalıdır: eski olay t + sure/2'ye gider, kesin olay t'de kalır.
    spec = {"fps": 30, "olaylar": [{"t": 5.5, "tur": "slayt", "sure": 0.3, "dosya": "a.wav", "kesin": True, "gain_db": -6}, {"t": 9, "tur": "slayt", "sure": 0.3, "dosya": "b.wav", "gain_db": -6}]}
    y = {o["dosya"]: o["tepe"] for o in olaysesi.planla(spec, [], {})["yerler"]}
    assert y["a.wav"] == 5.5 and y["b.wav"] == 9.15


def test_kesin_klip_kirpimla_yerinde_calar(tmp_path):
    v, s = tmp_path / "v.mp4", tmp_path / "s.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=black:s=64x64:r=30:d=4", "-c:v", "libx264", "-preset", "ultrafast", str(v)], check=True)
    tik(s, 0.5)  # dosyada tepe 0,5 sn; klip 0,4'ten başlar, tepe klibin 0,1'inde
    spec = {"video": str(v), "fps": 30, "sure": 4, "olaylar": [{"t": 2.0, "tur": "sfx", "dosya": str(s), "gain_db": -6, "kesin": True, "in": 0.4, "dur": 0.5}], "muzik": []}
    y = tmp_path / "olaylar.json"
    y.write_text(json.dumps(spec), encoding="utf-8")
    r = olaysesi.calistir(y, tmp_path / "c.mp4")
    assert r["yerlesen"] == 1 and r["yerler"][0]["baslangic"] == 2.0
    # Tepe 2,1 sn'de olmalı. AAC ön dolgusu ve loudnorm birkaç ms kaydırabilir.
    assert abs(tepe_ani(tmp_path / "c.mp4", tmp_path) - 2.1) < 0.06


def test_olaylar_uret_kesin_iz_gain_ve_kirpim(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "INPUTS", tmp_path / "in")
    monkeypatch.setattr(paths, "OUTPUTS", tmp_path / "out")
    p = Proje("instagram", "x")
    k = Kurgu.model_validate({
        "kaynaklar": {"K": {"yol": "library:sfx/a.wav", "sure": 2}, "S": {"yol": "inputs:ses.wav", "sure": 9}},
        "izler": [{"id": "A2", "tur": "ses", "gain_db": -3}, {"id": "A3", "tur": "ses", "sessiz": True}, {"id": "A4", "tur": "ses"}],
        "klipler": [{"id": "a", "iz": "A2", "tur": "ses", "kaynak": "K", "bas": 1, "sure": 0.5, "giris": 0.2, "ses": {"gain_db": -6, "fade_in": 0.1}, "olay": {"tur": "sfx"}},
                    {"id": "b", "iz": "A3", "tur": "ses", "kaynak": "K", "bas": 2, "sure": 1},
                    {"id": "c", "iz": "A4", "tur": "ses", "kaynak": "S", "bas": 3, "sure": 4, "giris": 1, "olay": {"muzik": True}}],
    })
    o = kurgu.olaylar_uret(k, p)
    assert o["olaylar"] == [{"t": 1, "tur": "sfx", "dosya": "library/sfx/a.wav", "gain_db": -9, "kesin": True, "dur": 0.5, "fade_in": 0.1, "fade_out": 0.012, "in": 0.2}]
    assert len(o["muzik"]) == 1 and o["muzik"][0]["src"].endswith("ses.wav") and o["muzik"][0]["start"] == 3 and o["muzik"][0]["in"] == 1


def _ayrik_kurgu():
    return Kurgu.model_validate({
        "kaynaklar": {"V": {"yol": "inputs:v.mp4", "sure": 9, "ses": True}, "U": {"yol": "inputs:u.mp4", "sure": 9, "ses": True}},
        "kelimeler": {"V": [{"w": "a", "s": 1, "e": 2}]},
        "izler": [{"id": "V1", "tur": "video"}, {"id": "A1", "tur": "ses", "gain_db": -2}],
        "klipler": [{"id": "v", "iz": "V1", "tur": "video", "kaynak": "V", "bas": 0, "sure": 5, "ses_kapali": True, "bag": "b"},
                    {"id": "s", "iz": "A1", "tur": "ses", "kaynak": "V", "bas": 0.4, "sure": 5, "giris": 0.5, "bag": "b", "ses": {"gain_db": -1, "fade_in": 0.1}, "olay": {"konusma": True}}],
    })


def test_ayrik_ses_konusma_busina_gider(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "INPUTS", tmp_path / "in")
    monkeypatch.setattr(paths, "OUTPUTS", tmp_path / "out")
    p = Proje("instagram", "x")
    k = _ayrik_kurgu()
    o = kurgu.olaylar_uret(k, p)
    assert o["olaylar"] == [], "konuşma SFX olayı olmaz"
    assert [s["src"].endswith("v.mp4") for s in o["ses"]] == [True], "bağlı video yok, ham eklenmez"
    assert {a: o["ses"][0][a] for a in ("start", "in", "dur", "gain_db", "fade_in")} == {"start": 0.4, "in": 0.5, "dur": 5, "gain_db": -3, "fade_in": 0.1}
    # Altyazı görüntüden değil sesten gelir: 0,5 sn kaynak kırpımı, 0,4 sn kayma.
    assert kurgu.izdusum(k) == [{"w": "a", "s": 0.9, "e": 1.9}]
    k.klipler.append(k.klipler[0].model_copy(update={"id": "u", "kaynak": "U", "bas": 6, "ses_kapali": False, "bag": None}))
    assert kurgu.olaylar_uret(k, p)["ses"][0] == {"src": "../renders/ham.mp4"}, "ayrılmamış klip ham.mp4'te kalır"
    # Ayrık ses yoksa çıktı eskisiyle aynı.
    k.klipler = [c for c in k.klipler if c.id == "u"]
    assert "ses" not in kurgu.olaylar_uret(k, p)


def test_ayrik_ses_kirpimla_yerinde_calar(tmp_path):
    v, s = tmp_path / "v.mp4", tmp_path / "s.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=black:s=64x64:r=30:d=4", "-c:v", "libx264", "-preset", "ultrafast", str(v)], check=True)
    tik(s, 0.5)
    spec = {"video": str(v), "fps": 30, "sure": 4, "olaylar": [], "muzik": [], "ses": [{"src": str(s), "start": 2.0, "in": 0.4, "dur": 0.5, "gain_db": 0}]}
    y = tmp_path / "olaylar.json"
    y.write_text(json.dumps(spec), encoding="utf-8")
    olaysesi.calistir(y, tmp_path / "c.mp4")
    assert abs(tepe_ani(tmp_path / "c.mp4", tmp_path) - 2.1) < 0.06


def test_ayrik_ses_ham_ile_ayni_yukseklik(tmp_path):
    """Aynı ses videonun içindeyken ve ayrık klip olarak aynı miksi vermeli."""
    v = tmp_path / "v.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=black:s=64x64:r=30:d=6", "-f", "lavfi", "-i", "sine=frequency=300:duration=6:sample_rate=48000",
                    "-c:v", "libx264", "-preset", "ultrafast", "-c:a", "aac", "-b:a", "192k", "-shortest", str(v)], check=True)
    sessiz = tmp_path / "sessiz.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(v), "-an", "-c:v", "copy", str(sessiz)], check=True)
    ana = {"fps": 30, "sure": 6, "olaylar": [], "muzik": []}
    (tmp_path / "bagli.json").write_text(json.dumps({**ana, "video": str(v)}), encoding="utf-8")
    (tmp_path / "ayrik.json").write_text(json.dumps({**ana, "video": str(sessiz), "ses": [{"src": str(v), "start": 0, "in": 0, "dur": 6, "gain_db": 0}]}), encoding="utf-8")
    a = olaysesi.calistir(tmp_path / "bagli.json", tmp_path / "bagli.mp4")
    b = olaysesi.calistir(tmp_path / "ayrik.json", tmp_path / "ayrik.mp4")
    assert abs(a["loudness"]["I"] - b["loudness"]["I"]) <= 0.1, (a["loudness"], b["loudness"])


def test_ses_yeri_eski_miksle_ayni(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "ROOT", tmp_path)
    tik(tmp_path / "a.wav", 0.25)
    # bas çapası: tepe olay anına oturur, ses tepenin payı kadar önce başlar
    bas, giris, sure = kurgu._ses_yeri({"t": 5, "tur": "sayac", "dosya": "a.wav"}, 30)
    assert bas == pytest.approx(4.75, abs=0.02) and giris == 0 and sure == pytest.approx(1.0, abs=0.01)
    assert kurgu._ses_yeri({"t": 0.1, "tur": "sayac", "dosya": "a.wav"}, 30)[0] == 0, "eksiye düşmez"
    assert kurgu._ses_yeri({"t": 5, "tur": "sayac", "dosya": "yok.wav"}, 30) == (5, 0.0, None)


def test_ses_yeri_uydur_kirpimi(tmp_path, monkeypatch):
    # 2 sn ses, tepe 1,5'te (yükselen): sure 0,3 ile 0,45 sn kalır, tepe korunur, orta çapası
    monkeypatch.setattr(paths, "ROOT", tmp_path)
    tik(tmp_path / "s.wav", 1.5, sure=2.0)
    bas, giris, sure = kurgu._ses_yeri({"t": 10, "tur": "slayt", "sure": 0.3, "dosya": "s.wav"}, 30)
    assert sure == pytest.approx(0.45, abs=0.01)
    assert giris == pytest.approx(1.5 + 0.15 - 0.45, abs=0.01)
    assert bas == pytest.approx(10.15 - (1.5 - giris), abs=0.02), "tepe eski miksteki yerde"


def test_denetle_render_oncesi(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "INPUTS", tmp_path / "in")
    monkeypatch.setattr(paths, "OUTPUTS", tmp_path / "out")
    p = Proje("instagram", "x")
    p.girdi.mkdir(parents=True)
    (p.girdi / "var.mp4").write_bytes(b"x")
    k = Kurgu.model_validate({
        "kaynaklar": {"A": {"yol": "inputs:var.mp4"}, "B": {"yol": "inputs:yok.mp4"}, "C": {"yol": "inputs:../../x.mp4"}},
        "izler": [{"id": "V1", "tur": "video"}],
        "klipler": [{"id": "a", "iz": "V1", "tur": "video", "kaynak": "A", "bas": 0, "sure": 5},
                    {"id": "b", "iz": "V1", "tur": "video", "kaynak": "B", "bas": 4, "sure": 2},
                    {"id": "c", "iz": "V1", "tur": "video", "kaynak": "C", "bas": 9, "sure": 2},
                    {"id": "d", "iz": "V1", "tur": "sahne", "bas": 20, "sure": 2, "sahne": {"kind": "shot", "img": None}},
                    {"id": "e", "iz": "V1", "tur": "video", "bas": 30, "sure": 2}],
    })
    h = "\n".join(kurgu.denetle(p, k))
    for parca in ("çakışıyor", "yok.mp4", "Kök dışı", "görsel seçilmedi", "kaynağı yok"):
        assert parca in h, parca
    kurgu.yaz(p.work, k)
    with pytest.raises(SystemExit, match="render edilemez"):
        kurgu.hazirla(p)


def test_miks_ham_yoksa_anlasilir(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "INPUTS", tmp_path / "in")
    monkeypatch.setattr(paths, "OUTPUTS", tmp_path / "out")
    with pytest.raises(SystemExit, match="önce bir kez final"):
        hizli.miks(Proje("instagram", "x"))


@pytest.mark.parametrize("bulgular,ses,beklenen", [
    ([], True, "YAYINLANABILIR"), ([{"seviye": "P1"}, {"seviye": "P2"}], True, "YAYINLANABILIR"),
    ([{"seviye": "P0"}], True, "YAYINLANAMAZ"), ([], False, "YAYINLANAMAZ"),
])
def test_hukum(bulgular, ses, beklenen):
    assert sunucu.hukum_ver(bulgular, ses) == beklenen
