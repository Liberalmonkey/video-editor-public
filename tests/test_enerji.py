"""Enerji eğrisine bağlı motion yoğunluğu ve tek ajan brif entegrasyonu testleri (ADR 0064)."""

import json

import pytest

from vedit import aiedit, ajan_cagri, ff, hizli, kurgu, paths, yaratici
from vedit.schemas import Kurgu


def _kur(*klipler, sure: float = 12.0) -> Kurgu:
    return Kurgu.model_validate({
        "kaynaklar": {"V01": {"yol": "public:s.mp4", "sure": sure}},
        "izler": [{"id": "V2", "tur": "video"}, {"id": "V1", "tur": "video"}],
        "klipler": [{"id": "c1", "iz": "V1", "tur": "video", "kaynak": "V01", "bas": 0, "sure": sure}, *klipler],
    })


def test_enerji_yokken_eski_sonuc():
    bos = _kur(sure=8.0)
    u = kurgu.motion_yogunlugu(bos, 3.0)
    assert kurgu.motion_yogunlugu(bos, 3.0, enerji=None) == u
    assert len(u) == 2 and "yoğunluğu düşük" in u[0] and "0.0-8.0" in u[1]

    dolu = _kur(
        {"id": "t1", "iz": "V2", "tur": "metin", "bas": 2, "sure": 1, "metin": "a", "metin_stil": {"tip": "anahtar"}},
        {"id": "t2", "iz": "V2", "tur": "sahne", "bas": 5, "sure": 2, "sahne": {"layout": "full", "kind": "text", "lines": []}},
        sure=8.0,
    )
    assert kurgu.motion_yogunlugu(dolu, 3.0, enerji=None) == []


def test_sakin_dilimde_bosluk_uyarmaz_yuksek_dilimde_uyarir():
    # 0.0 sn'de tek grafik, sonrasında 12 sn sonuna kadar boşluk (12 sn boşluk; hedef=4.0 -> taban 8.0 sn)
    k = _kur({"id": "t1", "iz": "V2", "tur": "metin", "bas": 0.0, "sure": 1.0, "metin": "a", "metin_stil": {"tip": "anahtar"}}, sure=12.0)

    # Sakin dilim (seviye 1): eşik 4*2*2.0 = 16.0 sn ve ağırlıklı hedef 8.0 sn -> uyarı yok
    assert kurgu.motion_yogunlugu(k, 4.0, enerji=[(0.0, 12.0, 1)]) == []

    # Yüksek dilim (seviye 5): eşik 4*2*0.7 = 5.6 sn ve ağırlıklı hedef 2.8 sn -> uyarı üretir
    yuksek = kurgu.motion_yogunlugu(k, 4.0, enerji=[(0.0, 12.0, 5)])
    assert len(yuksek) == 2 and "hedef 2.8 sn" in yuksek[0] and "0.0-12.0 sn" in yuksek[1]


def test_karisik_enerji_egri_esigi_aralik_ortasina_gore_olcekler():
    # 0-6 (seviye 5), 6-16 (seviye 1, 10 sn boşluk), 16-20 (seviye 5)
    # 4.0-16.0 arası orta nokta 10.0 sn -> seviye 1 (eşik 16.0 sn) içine düşer, uyarı üretmez.
    k = _kur(
        {"id": "t1", "iz": "V2", "tur": "metin", "bas": 0.0, "sure": 1.0, "metin": "a", "metin_stil": {"tip": "anahtar"}},
        {"id": "t2", "iz": "V2", "tur": "metin", "bas": 2.0, "sure": 1.0, "metin": "b", "metin_stil": {"tip": "anahtar"}},
        {"id": "t3", "iz": "V2", "tur": "metin", "bas": 4.0, "sure": 1.0, "metin": "c", "metin_stil": {"tip": "anahtar"}},
        {"id": "t4", "iz": "V2", "tur": "metin", "bas": 16.0, "sure": 1.0, "metin": "d", "metin_stil": {"tip": "anahtar"}},
        {"id": "t5", "iz": "V2", "tur": "metin", "bas": 18.0, "sure": 1.0, "metin": "e", "metin_stil": {"tip": "anahtar"}},
        sure=20.0,
    )
    assert kurgu.motion_yogunlugu(k, 4.0, enerji=[(0.0, 6.0, 5), (6.0, 16.0, 1), (16.0, 20.0, 5)]) == []
    # Enerji yoksa aynı 4.0-16.0 boşluğu (12 sn > 8 sn) grafiksiz aralık uyarısı verir
    uyari = kurgu.motion_yogunlugu(k, 4.0)
    assert len(uyari) == 1 and "4.0-16.0 sn" in uyari[0]


def test_aiedit_calistir_brif_enerjisini_ve_seyreklik_mesajini_kullanir(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "INPUTS", tmp_path / "inputs")
    monkeypatch.setattr(paths, "OUTPUTS", tmp_path / "outputs")
    p = hizli.Proje("instagram", "enerji-deneme")
    p.girdi.mkdir(parents=True)
    (p.girdi / "1.mp4").write_bytes(b"video")

    monkeypatch.setattr(ff, "probe", lambda f: {
        "file": f.name, "duration": 12.0,
        "video": {"width": 1080, "height": 1920, "fps": 30},
        "audio": {"codec": "aac", "sample_rate": 48000, "channels": 2},
    })

    def sahte_hazirla(prj, **kw):
        for d in ("analysis", "edit", "renders", "qa", "public"):
            (prj.work / d).mkdir(parents=True, exist_ok=True)
        tr = {"files": {"1": {"segments": [{"start": 0.0, "end": 4.0, "text": "Merhaba", "words": [
            {"w": "Merhaba", "s": 0.0, "e": 1.5},
        ]}]}}}
        (prj.work / "analysis" / "transcript.json").write_text(json.dumps(tr), encoding="utf-8")
        (prj.work / "analysis" / "digest.txt").write_text("# 1.mp4\n[0.00-4.00] Merhaba\n", encoding="utf-8")

    monkeypatch.setattr(hizli, "hazirla", sahte_hazirla)
    monkeypatch.setattr(hizli, "taslak", lambda prj, **kw: prj.work / "renders" / "taslak.mp4")

    cagrilar: list[str] = []

    def sahte_ajan(istek, **kw):
        cagrilar.append(istek)
        k = kurgu.oku(p.work)
        k.klipler[0].konusmaci = True
        if not any(c.id == "m1" for c in k.klipler):
            k.klipler.append(aiedit.Klip(id="m1", iz="V2", bas=0.0, sure=1.5, tur="metin", metin="Açılış", metin_stil={"tip": "anahtar"}))
        kurgu.yol(p.work).write_text(k.model_dump_json(indent=1), encoding="utf-8")
        if not yaratici.yol(p.work).exists():
            yaratici.yol(p.work).write_text(json.dumps({
                "tez": "Sakin bölüm boş kalabilir.",
                "enerji": [{"aralik": [0, 12], "seviye": 5, "neden": "yüksek"}],
            }), encoding="utf-8")
        return "tamam", "oturum-1"

    monkeypatch.setattr(ajan_cagri, "calistir", sahte_ajan)
    aiedit.calistir(p, motion_seviye="yogun")
    assert len(cagrilar) == 2
    assert "dolgu grafik koyma" in cagrilar[1]
    assert "sakin bölümse raporda gerekçelendir" in cagrilar[1]

    # Aynı kurgu seviye 1 sakin brifle ek tur açmaz
    cagrilar.clear()
    k = kurgu.oku(p.work)
    k.klipler = [c for c in k.klipler if c.id != "m1"]
    kurgu.yol(p.work).write_text(k.model_dump_json(indent=1), encoding="utf-8")
    yaratici.yol(p.work).write_text(json.dumps({
        "tez": "Tamamen sakin anlatım.",
        "enerji": [{"aralik": [0, 12], "seviye": 1, "neden": "sakin"}],
        "kilit": True,
    }), encoding="utf-8")
    aiedit.calistir(p, motion_seviye="yogun")
    assert len(cagrilar) == 1
