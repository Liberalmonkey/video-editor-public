import json

import pytest

from vedit import kurgu, paths
from vedit.hizli import Proje
from vedit.schemas import Kurgu


def ornek(**ek) -> Kurgu:
    return Kurgu.model_validate({
        "kaynaklar": {"V01": {"yol": "public:s.mp4", "sure": 20}},
        "kelimeler": {"V01": [{"w": "a", "s": 1, "e": 2}, {"w": "b", "s": 5, "e": 7}, {"w": "c", "s": 11, "e": 12}]},
        "izler": [{"id": "V1", "tur": "video"}, {"id": "A2", "tur": "ses"}],
        "klipler": [{"id": "c1", "iz": "V1", "tur": "video", "kaynak": "V01", "bas": 10, "sure": 4, "giris": 4, "hiz": 1}],
        **ek,
    })


def test_izdusum_kesimi_izler():
    # kaynak 4-8 sn, sekans 10-14 sn: yalnız "b" kalır, kesim sınırı e'yi kırpar.
    assert kurgu.izdusum(ornek()) == [{"w": "b", "s": 11.0, "e": 13.0}]


def test_izdusum_hiz():
    k = ornek()
    k.klipler[0].hiz = 2.0  # kaynak 4-12 sn sekans 10-14 sn'ye sıkışır
    assert kurgu.izdusum(k) == [{"w": "b", "s": 10.5, "e": 11.5}, {"w": "c", "s": 13.5, "e": 14.0}]


def test_izdusum_altyazi_kapali():
    assert kurgu.izdusum(ornek(altyazi={"acik": False})) == []


def test_sema_bag_denetimi():
    with pytest.raises(ValueError, match="iz yok"):
        ornek(klipler=[{"id": "x", "iz": "YOK", "tur": "metin", "bas": 0, "sure": 1}])
    with pytest.raises(ValueError, match="benzersiz"):
        ornek(klipler=[{"id": "x", "iz": "V1", "tur": "metin", "bas": 0, "sure": 1}] * 2)


def test_yaz_rev_ve_gecmis(tmp_path):
    k = kurgu.yaz(tmp_path, ornek())
    assert k.rev == 0
    k = kurgu.yaz(tmp_path, k, beklenen_rev=0)
    assert k.rev == 1 and (tmp_path / "edit" / "kurgu-gecmis" / "000000.json").exists()
    with pytest.raises(kurgu.RevCakismasi):
        kurgu.yaz(tmp_path, k, beklenen_rev=0)
    assert kurgu.oku(tmp_path).rev == 1  # reddedilen yazma dosyayı bozmaz


def test_dosya_kok_disi_reddedilir(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "INPUTS", tmp_path / "in")
    monkeypatch.setattr(paths, "OUTPUTS", tmp_path / "out")
    p = Proje("instagram", "x")
    with pytest.raises(ValueError, match="Kök dışı"):
        kurgu.dosya(p, "inputs:../../sir.txt")
    with pytest.raises(ValueError, match="Bilinmeyen"):
        kurgu.dosya(p, "c:/windows/x")


def test_olaylar_uret_ses_izleri():
    k = ornek(kaynaklar={"V01": {"yol": "public:s.mp4", "sure": 20}, "K1": {"yol": "library:sfx/a.wav", "sure": 1}, "M": {"yol": "library:music/m.mp3", "sure": 60}},
              klipler=[{"id": "a", "iz": "A2", "tur": "ses", "kaynak": "K1", "bas": 2.5, "sure": 1, "ses": {"gain_db": -20}, "olay": {"tur": "slayt", "sure": 0.3, "not": "n"}},
                       {"id": "m", "iz": "A2", "tur": "ses", "kaynak": "M", "bas": 0, "sure": 20, "ses": {"gain_db": -12, "duck": True, "fade_in": 0.3, "fade_out": 1.5}, "olay": {"muzik": True}}])
    o = kurgu.olaylar_uret(k, Proje("instagram", "x"))
    assert o["olaylar"] == [{"t": 2.5, "tur": "slayt", "dosya": "library/sfx/a.wav", "gain_db": -20, "kesin": True, "dur": 1, "fade_in": 0.012, "fade_out": 0.012, "in": 0, "sure": 0.3, "not": "n"}]
    assert o["muzik"] == [{"src": "library/music/m.mp3", "gain_db": -12, "duck": True, "fade_in": 0.3, "fade_out": 1.5, "start": 0, "in": 0, "dur": 20}]


def test_hazirla_ses_degisimi_render_girdisini_degistirmez(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "OUTPUTS", tmp_path / "out")
    monkeypatch.setattr(paths, "INPUTS", tmp_path / "in")
    p = Proje("instagram", "x")
    k = ornek(klipler=[{"id": "c1", "iz": "V1", "tur": "video", "kaynak": "V01", "bas": 0, "sure": 8},
                       {"id": "a", "iz": "A2", "tur": "ses", "bas": 2, "sure": 1, "olay": {"tur": "slayt"}}])
    (p.work / "public").mkdir(parents=True)
    (p.work / "public" / "s.mp4").write_bytes(b"v")
    kurgu.yaz(p.work, k)
    ilk = kurgu.hazirla(p).read_bytes()
    k2 = kurgu.oku(p.work)
    k2.klipler[1].bas = 3
    kurgu.yaz(p.work, k2, beklenen_rev=k2.rev)
    assert kurgu.hazirla(p).read_bytes() == ilk
    assert json.loads((p.work / "edit" / "olaylar.json").read_text(encoding="utf-8"))["olaylar"][0]["t"] == 3


def test_altyazi_stili_srt_ve_font(tmp_path, monkeypatch):
    from vedit import hizli
    monkeypatch.setattr(paths, "OUTPUTS", tmp_path / "out")
    monkeypatch.setattr(paths, "INPUTS", tmp_path / "in")
    monkeypatch.setattr(paths, "LIBRARY", tmp_path / "lib")
    (tmp_path / "lib" / "fonts").mkdir(parents=True)
    (tmp_path / "lib" / "fonts" / "Y.ttf").write_bytes(b"f")
    p = Proje("instagram", "x")
    stil = {"en_kelime": 1, "en_karakter": 18, "dosya": "../fonts/Y.ttf"}
    k = ornek(klipler=[{"id": "c1", "iz": "V1", "tur": "video", "kaynak": "V01", "bas": 0, "sure": 8}], altyazi={"stil": stil})
    (p.work / "public").mkdir(parents=True)
    (p.work / "public" / "s.mp4").write_bytes(b"v")
    kurgu.yaz(p.work, k)
    r = json.loads(kurgu.hazirla(p).read_text(encoding="utf-8"))
    assert (p.work / "public/fonts/Y.ttf").read_bytes() == b"f", "yol parçası atılır, font kütüphaneden gelir"
    w = [{"w": "a", "s": 0, "e": 1}, {"w": "b", "s": 1, "e": 2}]
    assert hizli.srt_yaz(w, r["altyazi"]["stil"]).count("-->") == 2
    assert hizli.srt_yaz(w, None).count("-->") == 1, "varsayılan: ADR 0014 sayfalama"


def test_sayfalama_ornek_python(tmp_path):
    """tests/sayfala_ornek.json: TS buildPages ile aynı örnek."""
    from pathlib import Path
    from vedit import hizli
    d = json.loads((Path(__file__).parent / "sayfala_ornek.json").read_text(encoding="utf-8"))
    for o in d:
        assert [[x["w"] for x in s] for s in hizli.sayfala(o["kelimeler"], en_kelime=o["en_kelime"], en_karakter=o["en_karakter"])] == o["sayfalar"], o


def test_denetle_bilinmeyen_ses_olayi():
    """Kaynaksız ses olayında geçersiz rol ya da güç render'dan önce yakalanır; geçerli rol ve kaynaklı klip geçer."""
    def hatalar(olay, **ek):
        k = ornek(klipler=[{"id": "a", "iz": "A2", "tur": "ses", "bas": 1, "sure": 0.3, "olay": olay, **ek}])
        return [h for h in kurgu.denetle(Proje("instagram", "x"), k) if "ses olayı" in h]

    assert hatalar({"tur": "gecis", "guc": "orta"}) == []
    assert hatalar({"tur": "gecis_guclu"}) == []
    assert hatalar({"muzik": True}) == []
    assert "'whoosh'" in hatalar({"tur": "whoosh"})[0]
    assert "'sfx'" in hatalar({})[0]
    assert "'cok-sert'" in hatalar({"tur": "pop", "guc": "cok-sert"})[0]
