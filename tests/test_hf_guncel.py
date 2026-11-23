"""HyperFrames güncelleme (ADR 0051): sürüm karşılaştırma, günlük kontrol, kalan adayın sabitlenmemesi."""

import json

import pytest

from vedit import hf, hf_guncel


@pytest.fixture
def ortam(tmp_path, monkeypatch):
    aday = tmp_path / "hf-aday"
    monkeypatch.setattr(hf_guncel, "ADAY", aday)
    monkeypatch.setattr(hf_guncel, "DURUM", aday / "durum.json")
    monkeypatch.setattr(hf_guncel, "ONCEKI", aday / "onceki.json")
    monkeypatch.setattr(hf, "surum", lambda: "0.9.77")
    monkeypatch.setattr(hf_guncel, "KILIT", aday / "kuruluyor.kilit")
    monkeypatch.setattr(hf_guncel, "DENEME", aday / "deneme.kilit")
    monkeypatch.setattr(hf_guncel, "mesgul", lambda: [])
    return aday


def test_surum_siralamasi():
    k = hf_guncel._surum_anahtari
    assert k("0.9.78") > k("0.9.77")
    assert k("0.10.0") > k("0.9.99")


def test_pencere_cuma_13():
    from datetime import datetime
    sp = hf_guncel.son_pencere
    assert sp(datetime(2026, 11, 23, 10, 0)) == datetime(2026, 11, 20, 13, 0)  # Pazartesi: geçen Cuma
    assert sp(datetime(2026, 11, 27, 12, 59)) == datetime(2026, 11, 20, 13, 0)  # Cuma 12:59: henüz değil
    assert sp(datetime(2026, 11, 27, 13, 0)) == datetime(2026, 11, 27, 13, 0)
    assert hf_guncel.sonraki_pencere(datetime(2026, 11, 23, 10, 0)) == datetime(2026, 11, 27, 13, 0)
    son = datetime(2026, 11, 20, 13, 5).timestamp()
    assert not hf_guncel.vakti_geldi({"son_kontrol_ts": son}, datetime(2026, 11, 27, 12, 0))
    assert hf_guncel.vakti_geldi({"son_kontrol_ts": son}, datetime(2026, 11, 27, 13, 1))


def test_is_varken_haftalik_kontrol_ertelenir(ortam, monkeypatch):
    sayac = []
    monkeypatch.setattr(hf_guncel, "en_yeni", lambda: sayac.append(1) or "0.9.80")
    monkeypatch.setattr(hf_guncel, "mesgul", lambda: ["vedit.exe 123"])
    d = hf_guncel.bir_tur()
    assert sayac == [] and "çalışan iş" in d["bekliyor"]
    monkeypatch.setattr(hf_guncel, "mesgul", lambda: [])
    kur = []
    monkeypatch.setattr(hf_guncel, "kur", lambda: kur.append(1) or {})
    hf_guncel.bir_tur()
    assert sayac == [1] and kur == [1]


def test_is_varken_sabitlenmez(ortam, monkeypatch):
    monkeypatch.setattr(hf_guncel, "en_yeni", lambda: "0.9.80")
    monkeypatch.setattr(hf_guncel, "_aday_kur", lambda v: ortam / v)
    monkeypatch.setattr(hf_guncel, "duman", lambda kok, cikti=None: [{"ad": "x", "gecti": True, "sorun": []}])
    monkeypatch.setattr(hf_guncel, "mesgul", lambda: ["ffmpeg.exe 9"])
    sabit = []
    monkeypatch.setattr(hf_guncel, "_sabitle", lambda v: sabit.append(v))
    d = hf_guncel.kur(skill=False, bekle=0)
    assert sabit == [] and "son_deneme" not in d and "sabitlenecek" in d["bekliyor"]
    assert not hf_guncel.kilitli()


def test_is_sureci_ayirimi():
    f = hf_guncel._is_sureci_mi
    assert f("python.exe", r'"C:\x\.venv\Scripts\vedit.exe" ai-edit instagram/reel-video --ekip')
    assert not f("python.exe", '".venv\\Scripts\\python.exe" -m vedit.studio.baslat')
    assert not f("python.exe", r'"C:\x\.venv\Scripts\vedit.exe" hf-guncelle')
    assert f("node.exe", r"node C:\x\node_modules\hyperframes\dist\cli.js render")
    assert not f("node.exe", r"node C:\x\rea.mjs mcp")
    assert f("ffmpeg.exe", "ffmpeg -i a.mp4")


def test_kontrol_haftada_bir_kez_sorar(ortam, monkeypatch):
    sayac = []
    monkeypatch.setattr(hf_guncel, "en_yeni", lambda: sayac.append(1) or "0.9.80")
    d = hf_guncel.kontrol()
    assert d["yeni_var"] is True and d["en_yeni"] == "0.9.80"
    hf_guncel.kontrol()
    assert len(sayac) == 1
    hf_guncel.kontrol(zorla=True)
    assert len(sayac) == 2


def test_duman_kalirsa_surum_sabitlenmez(ortam, monkeypatch):
    monkeypatch.setattr(hf_guncel, "en_yeni", lambda: "0.9.80")
    monkeypatch.setattr(hf_guncel, "_aday_kur", lambda v: ortam / v)
    monkeypatch.setattr(hf_guncel, "duman", lambda kok, cikti=None: [{"ad": "x", "gecti": False, "sorun": ["fark 40"]}])
    sabit = []
    monkeypatch.setattr(hf_guncel, "_sabitle", lambda v: sabit.append(v))
    d = hf_guncel.kur()
    assert sabit == [] and d["son_deneme"]["gecti"] is False
    assert "KALDI" in (ortam / "0.9.80" / "rapor.md").read_text(encoding="utf-8")


def test_duman_gecerse_sabitler_ve_kaydeder(ortam, monkeypatch):
    monkeypatch.setattr(hf_guncel, "en_yeni", lambda: "0.9.80")
    monkeypatch.setattr(hf_guncel, "_aday_kur", lambda v: ortam / v)
    monkeypatch.setattr(hf_guncel, "duman", lambda kok, cikti=None: [{"ad": "x", "gecti": True, "sorun": [], "fark": 0.0}])
    sabit = []
    monkeypatch.setattr(hf_guncel, "_sabitle", lambda v: sabit.append(v))
    monkeypatch.setattr(hf_guncel, "_log", lambda s: None)
    d = hf_guncel.kur(skill=False)
    assert sabit == ["0.9.80"] and d["son_deneme"]["gecti"] is True


def test_geri_kaydi_yoksa_durur(ortam):
    with pytest.raises(SystemExit):
        hf_guncel.geri()


def test_ikinci_deneme_baslamaz(ortam, monkeypatch):
    ortam.mkdir(parents=True, exist_ok=True)
    (ortam / "deneme.kilit").write_text("1", encoding="utf-8")
    monkeypatch.setattr(hf_guncel, "en_yeni", lambda: (_ for _ in ()).throw(AssertionError("sormamalı")))
    d = hf_guncel.kur()
    assert "sürüyor" in d["bekliyor"]
