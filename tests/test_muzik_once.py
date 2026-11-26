"""Müzik öncülü yapı (ADR 0064, adım 8): parça seçimi, yükseliş tespiti, harita ve istem metni."""

from pathlib import Path

from vedit import muzik_once, ritim
from vedit.ekip_sema import YaraticiBrif

KAYIT = [
    {"id": "sakin", "mood": ["koyu", "gergin", "temiz"], "genre": "ambient", "energy": "orta", "duration_s": 120,
     "_yol": "a.mp3", "_kaynak": "library:music/a.mp3"},
    {"id": "enerjik", "mood": ["enerjik", "ileri giden"], "genre": "funk", "energy": "orta-yüksek", "duration_s": 120,
     "_yol": "b.mp3", "_kaynak": "library:music/b.mp3"},
    {"id": "kisa", "mood": ["enerjik"], "genre": "funk", "energy": "yüksek", "duration_s": 10,
     "_yol": "c.mp3", "_kaynak": "library:music/c.mp3"},
]


def _brif(seviye: int, ses: str) -> YaraticiBrif:
    return YaraticiBrif.model_validate({"tez": "test tezi", "ses": ses, "enerji": [{"aralik": [0, 30], "seviye": seviye}]})


def test_secim_brifin_ses_ve_enerjisine_uyar():
    assert muzik_once.sec(_brif(5, "enerjik ve ileri giden bir ritim"), None, 30, KAYIT)["id"] == "enerjik"
    assert muzik_once.sec(_brif(2, "koyu, gergin bir zemin"), None, 30, KAYIT)["id"] == "sakin"
    assert muzik_once.sec(None, "", 30, []) is None
    # süre yetmeyen parça cezalı: video 60 sn, "kisa" 10 sn
    assert muzik_once.sec(_brif(5, "enerjik"), None, 60, KAYIT)["id"] != "kisa"


def test_yukselis_tespiti():
    hz = 10
    enerji = [0.1] * 50 + [0.9] * 50 + [0.9] * 10
    y = muzik_once.yukselisler(enerji, hz)
    assert len(y) == 1 and 4.5 <= y[0] <= 7.0
    assert muzik_once.yukselisler([], hz) == [] and muzik_once.yukselisler([0.5] * 100, hz) == []


def test_harita_ve_metin(monkeypatch):
    monkeypatch.setattr(ritim, "analiz", lambda f, o: {"tempo": 120.0, "beats": [i * 0.5 for i in range(80)],
                                                        "enerji": [0.1] * 100 + [0.9] * 100, "enerji_hz": 10})
    h = muzik_once.harita({**KAYIT[1], "structure": "8 sn intro"}, sure=20)
    assert h["cumle_baslari"][:3] == [0.0, 4.0, 8.0] and max(h["cumle_baslari"]) <= 20
    assert h["yukselisler"] and h["kaynak"] == "library:music/b.mp3"
    m = muzik_once.metin(h)
    assert "120 BPM" in m and "Cümle başları" in m and "gerekçe" in m
    assert muzik_once.metin(None) == ""


def test_hazirla_hatada_none_doner(tmp_path, monkeypatch):
    p = type("P", (), {"work": Path(tmp_path)})()
    monkeypatch.setattr(muzik_once, "kayitlar", lambda: KAYIT)
    monkeypatch.setattr(ritim, "analiz", lambda f, o: (_ for _ in ()).throw(RuntimeError("bozuk")))
    assert muzik_once.hazirla(p, None, None, 20) is None
    monkeypatch.setattr(ritim, "analiz", lambda f, o: {"tempo": None, "beats": [], "enerji": [], "enerji_hz": 25})
    h = muzik_once.hazirla(p, None, "enerjik", 20)
    assert h["id"] == "enerjik" and (Path(tmp_path) / "edit" / muzik_once.DOSYA).is_file()
