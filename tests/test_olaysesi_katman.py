"""Olay sesi katmanı: Türkçe güç adları, kombolar, çeşitleme, müzik çekme ve kısa fade."""
from types import SimpleNamespace as E

import numpy as np
import pytest

from vedit import olaysesi

ENTRIES = [E(id=f"w{n}", file=f"w{n}.wav", category="whoosh", tags=["transition"], duration_s=0.5 + n / 10, peak_offset_s=0.2) for n in range(4)] + [
    E(id="i-light", file="il.wav", category="impact", tags=["light"], duration_s=0.2, peak_offset_s=0.0),
    E(id="i-sub", file="is.wav", category="impact", tags=["sub"], duration_s=2.0, peak_offset_s=0.05),
    E(id="i-orta", file="io.wav", category="impact", tags=[], duration_s=0.6, peak_offset_s=0.0),
    E(id="r-ters", file="rt.wav", category="riser", tags=["reverse"], duration_s=0.7, peak_offset_s=0.65),
    E(id="r-uzun", file="ru.wav", category="riser", tags=[], duration_s=1.8, peak_offset_s=1.7),
    E(id="zayif", file="zayif.wav", category="aday", tags=["whoosh", "transition"], duration_s=0.5, peak_offset_s=0.2),
]


def plan(olaylar, **kw):
    return olaysesi.planla({"fps": 30, "olaylar": olaylar}, ENTRIES, {}, **kw)


def test_turkce_guc_adi_ingilizceyle_ayni():
    for tr, en in (("yumusak", "soft"), ("orta", "medium"), ("sert", "hard")):
        a = plan([{"t": 1, "tur": "vurgu", "guc": tr}])["yerler"][0]
        b = plan([{"t": 1, "tur": "vurgu", "guc": en}])["yerler"][0]
        assert a["guc"] == en and a["gain_db"] == b["gain_db"] and a["dosya"] == b["dosya"]
    # kesme varsayılan sessizdir; Türkçe "orta" onu duyurur
    assert plan([{"t": 1, "tur": "kesme", "guc": "yumusak"}])["sessiz"]
    assert not plan([{"t": 1, "tur": "punch_in", "guc": "orta"}])["sessiz"]


def test_kombo_katmanlara_acilir_ve_tek_olay_sayilir():
    p = plan([{"t": 2.0, "tur": "gecis_guclu", "sure": 0.4}, {"t": 2.1, "tur": "tik"}])
    katman = [y for y in p["yerler"] if y["tur"] == "gecis_guclu"]
    assert [y["rol"] for y in katman] == ["gecis", "vurgu"]
    assert len(p["dusen"]) == 1 and p["dusen"][0]["tur"] == "tik"  # kombo katmanları birbirini düşürmez, yakındaki tik düşer
    assert p["adet"] == {"gecis_guclu": 1}
    whoosh, darbe = katman
    assert darbe["tepe"] == 2.2 and abs(whoosh["tepe"] - 2.17) < 1e-6  # darbe kesme karesinde, whoosh biraz önce
    assert darbe["dosya"] == "is.wav" and darbe["gain_db"] < whoosh["gain_db"] - 4  # alt katman hafif ve alçak
    assert darbe["en_uzun"] == 0.5
    a = plan([{"t": 5, "tur": "acilis"}])["yerler"]
    assert a[0]["dosya"] in ("ru.wav", "rt.wav") and a[1]["dosya"] == "is.wav" and all(y["tepe"] == 5 for y in a)
    v = plan([{"t": 5, "tur": "vurgu_guclu", "guc": "sert"}])["yerler"]
    assert {y["dosya"] for y in v} == {"io.wav", "rt.wav"} and all(y["guc"] == "hard" for y in v)


def test_aday_kategorisi_secilmez_ve_art_arda_ayni_dosya_yok():
    p = plan([{"t": t, "tur": "gecis", "sure": 0.4} for t in range(1, 12)])
    dosyalar = [y["dosya"] for y in p["yerler"]]
    assert "zayif.wav" not in dosyalar
    assert all(a != b for a, b in zip(dosyalar, dosyalar[1:]))


def test_perde_ve_seviye_tohumlu_deterministik():
    olaylar = [{"t": t, "tur": "vurgu"} for t in range(1, 9)]
    a, b = plan(olaylar)["yerler"], plan(olaylar)["yerler"]
    assert [y["gain_db"] for y in a] == [y["gain_db"] for y in b]
    taban = olaysesi.GUC_DB["medium"] + olaysesi.ROLLER["vurgu"]["db"]
    farklar = {round(y["gain_db"] - taban, 2) for y in a}
    assert all(abs(f) <= 1.0 for f in farklar) and len(farklar) > 1
    d = np.zeros((4800, 2), dtype=np.float32)
    d[100] = 1
    boylar = {len(olaysesi._sekillendir(d.copy(), {"yon": None, "uydur": False, "sure": 0, "tur": "vurgu", "sira": s})[0]) for s in range(20)}
    assert len(boylar) > 1 and all(4800 / 1.04 < n < 4800 / 0.96 for n in boylar)
    y = {"yon": None, "uydur": False, "sure": 0, "tur": "vurgu", "sira": 3}
    assert np.array_equal(olaysesi._sekillendir(d.copy(), y)[0], olaysesi._sekillendir(d.copy(), y)[0])


def test_dosyasiz_olayda_gain_db_fark():
    taban = plan([{"t": 1, "tur": "vurgu"}])["yerler"][0]["gain_db"]
    assert plan([{"t": 1, "tur": "vurgu", "gain_db": -3}])["yerler"][0]["gain_db"] == round(taban - 3, 2)
    assert plan([{"t": 1, "tur": "sfx", "dosya": "x.wav", "gain_db": -20}])["yerler"][0]["gain_db"] == -20


def test_en_uzun_tepeyi_koruyup_kirpar():
    d = np.zeros((olaysesi.SR * 2, 2), dtype=np.float32)
    d[olaysesi.SR // 10] = 1
    out, tepe = olaysesi._sekillendir(d, {"yon": None, "uydur": False, "sure": 0, "tur": "x", "sira": 0, "en_uzun": 0.5})
    assert len(out) <= 0.52 * olaysesi.SR and out[tepe].any()


def test_muzik_vurustan_once_iner_vurusta_acilir():
    sr = olaysesi.SR
    a, egri = olaysesi.dip_egrisi(10 * sr, 5 * sr, "hard")
    at = lambda t: egri[int(t * sr) - a]
    assert abs(20 * np.log10(at(4.9)) + 6) < 0.1 and egri[0] == pytest.approx(1, abs=0.01)
    assert egri[-1] == pytest.approx(1, abs=0.01) and at(5.0) == pytest.approx(at(4.9))  # vuruşta açılmaya başlar
    a, egri = olaysesi.dip_egrisi(10 * sr, 5 * sr, "medium")
    assert abs(20 * np.log10(egri[int(4.9 * sr) - a]) + 3) < 0.1 and egri[0] == pytest.approx(1, abs=0.01)


def test_bilinmeyen_tur_kombolari_da_listeler():
    with pytest.raises(SystemExit, match="Kombolar: gecis_guclu, vurgu_guclu, acilis"):
        plan([{"t": 1, "tur": "uydurma"}])


def test_gercek_kayit_varken_synth_secilmez():
    k = [E(id=f"whoosh-synth-whoosh-0{i}", category="whoosh", tags=[], duration_s=0.5) for i in range(3)]
    g = E(id="whoosh-mixkit-a", category="whoosh", tags=[], duration_s=2.0)
    rol = {"kat": ["whoosh"]}
    assert all(olaysesi._aday(k + [g], rol, "medium", 0.5, str(i), None) is g for i in range(8))
    assert olaysesi._aday(k, rol, "medium", 0.5, "0", None) in k
