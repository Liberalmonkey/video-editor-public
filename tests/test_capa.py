"""Çapa eşleme (ADR 0048): E1 kesimi değişince çapalı grafik ve ses olayları kelimeyle birlikte taşınır."""

from vedit import capa
from vedit.schemas import Kurgu


def _k(v1):
    kel = [{"w": f"k{i}", "s": i * 0.5, "e": i * 0.5 + 0.4} for i in range(20)]  # 0.0, 0.5, ... 9.5 sn
    return Kurgu.model_validate({
        "sekans": {"w": 1080, "h": 1920, "fps": 30},
        "kaynaklar": {"a": {"yol": "inputs:a.mp4", "sure": 10}},
        "kelimeler": {"a": kel},
        "izler": [{"id": "V2", "tur": "video"}, {"id": "V1", "tur": "video"}, {"id": "A2", "tur": "ses"}],
        "klipler": [*v1,
                    {"id": "g", "iz": "V2", "tur": "metin", "bas": 2.9, "sure": 1, "metin": "x", "capa": {"kaynak": "a", "kelime": 6}},
                    {"id": "s", "iz": "A2", "tur": "ses", "bas": 7.0, "sure": 0.5, "olay": {"tur": "vurgu"},
                     "capa": {"kaynak": "a", "kelime": 14, "once_kare": 0}}],
    })


def test_kesim_kayinca_capali_olaylar_kelimeyle_gider():
    # Başlangıç: tek parça, kelime 6 (3.0 sn) → grafik 3.0 - 3/30 = 2.9.
    k = _k([{"id": "v", "iz": "V1", "tur": "video", "bas": 0, "sure": 10, "kaynak": "a"}])
    assert capa.esle(k) == ([], [])
    # E1 ilk 1 sn'yi kesti ve 4-5 sn arasını attı: kaynak 1-4 → sekans 0-3, kaynak 5-10 → sekans 3-8.
    k = _k([{"id": "v1", "iz": "V1", "tur": "video", "bas": 0, "sure": 3, "kaynak": "a", "giris": 1},
            {"id": "v2", "iz": "V1", "tur": "video", "bas": 3, "sure": 5, "kaynak": "a", "giris": 5}])
    tasinan, bulgu = capa.esle(k)
    g = next(c for c in k.klipler if c.id == "g")
    s = next(c for c in k.klipler if c.id == "s")
    assert abs(g.bas - (3.0 - 1 - 0.1)) < 1e-6, "kelime 6: kaynak 3.0 → sekans 2.0, 3 kare önce"
    assert abs(s.bas - (7.0 - 5 + 3)) < 1e-6, "kelime 14: kaynak 7.0 → sekans 5.0"
    assert set(tasinan) == {"g", "s"} and bulgu == []


def test_kesilen_kelime_bulgu_olur_olay_dusmez():
    k = _k([{"id": "v1", "iz": "V1", "tur": "video", "bas": 0, "sure": 2, "kaynak": "a", "giris": 0},
            {"id": "v2", "iz": "V1", "tur": "video", "bas": 2, "sure": 5, "kaynak": "a", "giris": 5}])
    tasinan, bulgu = capa.esle(k)
    assert [b["klip"] for b in bulgu] == ["g"] and "düştü" in bulgu[0]["sorun"]
    assert any(c.id == "g" for c in k.klipler), "olay silinmez, sahibine bulgu"


def test_hiz_degisimi_ve_capala():
    k = _k([{"id": "v", "iz": "V1", "tur": "video", "bas": 0, "sure": 5, "kaynak": "a", "hiz": 2}])  # 2x: kaynak 0-10 → sekans 0-5
    capa.esle(k)
    assert abs(next(c for c in k.klipler if c.id == "g").bas - (1.5 - 0.1)) < 1e-6
    yeni = k.klipler[-2].model_copy(update={"capa": None, "bas": 2.4})
    capa.capala(k, yeni, "a")
    assert yeni.capa is not None and yeni.capa.kelime == 10  # 5.0 sn kaynak → 2.5 sn sekans, 2.4+0.1'e en yakın
