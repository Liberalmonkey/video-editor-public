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
    return aday


def test_surum_siralamasi():
    k = hf_guncel._surum_anahtari
    assert k("0.9.78") > k("0.9.77")
    assert k("0.10.0") > k("0.9.99")


def test_kontrol_gunde_bir_kez_sorar(ortam, monkeypatch):
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
