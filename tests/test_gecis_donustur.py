"""Eski gecis-* bindirmesi V1 kesim geçişine döner (ADR 0045)."""

from vedit import gecis_donustur, kurgu_kalite
from vedit.schemas import Kurgu


def _k():
    return Kurgu.model_validate({
        "kaynaklar": {"a": {"yol": "inputs:a.mp4"}, "b": {"yol": "inputs:b.mp4"},
                      "g": {"yol": "public:motion/gecis-yukari-it-dikey-d873fe5dd3.webm"}, "t": {"yol": "public:motion/onay-tik-10421c0a1d.webm"}},
        "izler": [{"id": "V2", "tur": "video"}, {"id": "V1", "tur": "video"}],
        "klipler": [{"id": "a", "iz": "V1", "tur": "video", "bas": 0, "sure": 2, "kaynak": "a"},
                    {"id": "b", "iz": "V1", "tur": "video", "bas": 2, "sure": 2, "kaynak": "b"},
                    {"id": "g", "iz": "V2", "tur": "motion", "bas": 1.7, "sure": 0.7, "kaynak": "g"},
                    {"id": "t", "iz": "V2", "tur": "motion", "bas": 3.0, "sure": 1.0, "kaynak": "t"}],
    })


def test_uyari_ve_donusum():
    k = _k()
    assert [u["kod"] for u in kurgu_kalite.uyarilar(k)].count("ESKI_GECIS") == 1
    rapor = gecis_donustur.donustur(k)
    assert len(rapor) == 1 and "kay/yukari" in rapor[0]
    assert [c.id for c in k.klipler] == ["a", "b", "t"], "yalnız geçiş bindirmesi silinir, ikon kalır"
    g = next(c for c in k.klipler if c.id == "b").gecis_giris
    assert g.tur == "kay" and g.yon == "yukari"
