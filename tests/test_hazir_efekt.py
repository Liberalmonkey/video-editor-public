"""Hazır efektler: ad ve parametre denetimi kurgu.denetle'den geçer; sesli efektler olaylar.json'a rol olayı verir."""
from vedit import hazir_efekt, kurgu
from vedit.hizli import Proje
from vedit.schemas import Kurgu


def ornek(hazir, **klip) -> Kurgu:
    return Kurgu.model_validate({
        "kaynaklar": {"V01": {"yol": "public:s.mp4", "sure": 20}},
        "izler": [{"id": "V1", "tur": "video"}, {"id": "A2", "tur": "ses"}],
        "klipler": [{"id": "c1", "iz": "V1", "tur": "video", "kaynak": "V01", "bas": 10, "sure": 4, "hazir": hazir, **klip}],
    })


def hatalar(hazir, **klip):
    k = ornek(hazir, **klip)
    return hazir_efekt.hatalar(k.klipler[0])


def test_gecerli_kayit_hatasiz():
    assert hatalar([{"ad": "punch", "t": 1, "s": 1.14}, {"ad": "odak_zoom", "x": 0.2, "geri_don": True},
                    {"ad": "ken_burns", "yon": "sol"}, {"ad": "zoom_in", "sure": 0}]) == []


def test_denetim_hatalari():
    h = hatalar([{"ad": "uc"}, {"ad": "punch", "s": 1.5}, {"ad": "ken_burns", "yon": "capraz"},
                 {"ad": "odak_zoom", "geri_don": "evet", "renk": 1}, {"ad": "punch", "t": 9}])
    assert any("bilinmeyen hazır efekt 'uc'" in x for x in h)
    assert any("s 1.1 ile 1.18 arasında olmalı, 1.5" in x for x in h)
    assert any("yon 'capraz' geçersiz" in x for x in h)
    assert any("geri_don true ya da false" in x for x in h)
    assert any("bilinmeyen parametre 'renk'" in x for x in h)
    assert any("t klibin içinde olmalı" in x for x in h)
    assert len(h) == 6


def test_denetle_hazir_hatasini_toplar():
    k = Kurgu.model_validate({"izler": [{"id": "V1", "tur": "video"}],
                              "klipler": [{"id": "m1", "iz": "V1", "tur": "metin", "metin": "a", "bas": 0, "sure": 2, "hazir": [{"ad": "uc"}]}]})
    assert any("bilinmeyen hazır efekt" in x for x in kurgu.denetle(None, k))


def test_ses_kanalinda_hazir_reddedilir():
    k = Kurgu.model_validate({"izler": [{"id": "A2", "tur": "ses"}],
                              "klipler": [{"id": "s1", "iz": "A2", "tur": "ses", "bas": 0, "sure": 1, "hazir": [{"ad": "punch"}]}]})
    assert "yalnız görüntü klibinde" in hazir_efekt.hatalar(k.klipler[0])[0]


def test_ses_olayi_uretimi():
    # punch ve odak_zoom sesli; zoom_in sessiz; ses: false olan atlanır; cikis yok.
    k = ornek([{"ad": "punch", "t": 1.2}, {"ad": "zoom_in"}, {"ad": "odak_zoom", "t": 2, "ses": False}, {"ad": "sarsinti"}])
    o = kurgu.olaylar_uret(k, Proje("instagram", "x"))["olaylar"]
    assert o == [{"t": 10.0, "tur": "vurgu", "sure": 0.4, "not": "hazır sarsinti (c1)"},
                 {"t": 11.2, "tur": "punch_in", "sure": 0.8, "not": "hazır punch (c1)", "guc": "orta"}]


def test_cozum_varsayilanlari():
    c = ornek([]).klipler[0]
    assert hazir_efekt.cozumle(c, {"ad": "zoom_in"}) == (0.0, 4)            # sure 0: klibin sonuna kadar
    assert hazir_efekt.cozumle(c, {"ad": "cikis_kay"}) == (4 - 0.35, 0.35)  # son: klip sonuna dayanır
    assert hazir_efekt.cozumle(c, {"ad": "punch", "t": 1, "sure": 99}) == (1, 10)  # sınırlanır


def test_gizli_izde_ses_yok():
    k = ornek([{"ad": "punch"}])
    k.izler[0].gizli = True
    assert hazir_efekt.ses_olaylari(k) == []
