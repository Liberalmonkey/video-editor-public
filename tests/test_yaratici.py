"""G0.5 yaratıcı brif (ADR 0064): şema gevşekliği, yeniden kullanım, kilit, istem bölümleri ve plan çıktısı."""

import json
from pathlib import Path

from vedit import ekip_v3, yaratici
from vedit.ekip_sema import EkipAyar, Plan, YaraticiBrif
from vedit.schemas import Kurgu

BRIF = {
    "tez": "Bir haftalık işi bir öğleden sonraya indirmek mümkün.",
    "metafor": "Eriyen kum saati",
    "iplik": "İnce vurgu çizgisi",
    "enerji": [{"aralik": [0, 3], "seviye": 5, "neden": "hook"}, {"aralik": [3, 20], "seviye": 2}],
    "imza_anlari": [{"t": 12.4, "soz": "bir öğleden sonra", "ne": "kum saati tek vuruşla boşalır"}],
    "ses": "Sessizlik ve tek vuruş",
    "riskler": ["Doruğu yavaşlat: rakam tek başına dursun"],
    "yasak": ["her kesimde whoosh"],
}


def _p(tmp_path: Path):
    (tmp_path / "edit").mkdir(parents=True, exist_ok=True)
    return type("P", (), {"work": tmp_path, "studyo": "instagram", "ad": "x"})()


def test_brif_gevsek_ama_tezsiz_gecersiz():
    b = YaraticiBrif.model_validate({**BRIF, "bilinmeyen": 1, "imza_anlari": BRIF["imza_anlari"] * 5, "yasak": ["a"] * 9})
    assert len(b.imza_anlari) == 3 and len(b.yasak) == 5, "fazla öğe kırpılır, reddedilmez"
    assert yaratici.dogrula({**BRIF, "tez": ""}) is None
    assert yaratici.dogrula({**BRIF, "enerji": [{"aralik": [0, 3], "seviye": 9}]}) is None
    assert yaratici.dogrula({**BRIF, "enerji": [{"aralik": [5, 3], "seviye": 3}]}) is None
    assert yaratici.dogrula("metin") is None


def test_istek_degisince_yenilenir_kilit_korunur(tmp_path):
    p = _p(tmp_path)
    assert yaratici.yaz(p.work, BRIF, "  hızlı   bir edit ") is not None
    assert yaratici.gecerli(p.work, "hızlı bir edit") is not None, "boşluk farkı aynı istek"
    assert yaratici.gecerli(p.work, "başka istek") is None
    # kullanıcı brifi kilitlerse ne istek değişimi ne de yeni ajan brifi üzerine yazar
    veri = json.loads(yaratici.yol(p.work).read_text(encoding="utf-8"))
    yaratici.yol(p.work).write_text(json.dumps({**veri, "kilit": True}), encoding="utf-8")
    assert yaratici.gecerli(p.work, "başka istek") is not None
    assert yaratici.yaz(p.work, {**BRIF, "tez": "yeni tez yeni"}, "x").tez == BRIF["tez"]


def test_gecersiz_brif_dosyaya_dokunmaz(tmp_path):
    p = _p(tmp_path)
    assert yaratici.yaz(p.work, {"tez": ""}, None) is None
    assert not yaratici.yol(p.work).exists()
    yaratici.yol(p.work).write_text("{bozuk", encoding="utf-8")
    assert yaratici.oku(p.work) is None and yaratici.damgala(p.work, None) is None


def test_damgala_tek_ajan_brifine_istegi_yazar(tmp_path):
    p = _p(tmp_path)
    yaratici.yol(p.work).write_text(json.dumps(BRIF), encoding="utf-8")
    assert yaratici.damgala(p.work, "kısa reels").istek == "kısa reels"
    assert yaratici.gecerli(p.work, "kısa reels") is not None


def test_metin_imza_ani_ve_enerji_tasir():
    m = yaratici.metin(YaraticiBrif.model_validate(BRIF))
    assert "İmza anı 1" in m and "12.4" in m and "bir öğleden sonra" in m
    assert "0-3 sn **5**" in m and "her kesimde whoosh" in m


def test_tek_ajan_bolumu(tmp_path):
    p = _p(tmp_path)
    yaz = yaratici.tek_ajan_bolumu(p.work, None, yazabilir=True)
    assert "önce bunu yaz" in yaz and str(yaratici.yol(p.work).resolve()) in yaz
    assert yaratici.tek_ajan_bolumu(p.work, None, yazabilir=False) == "", "aralık düzeltmesinde yeni brif istenmez"
    yaratici.yaz(p.work, BRIF, None)
    uy = yaratici.tek_ajan_bolumu(p.work, None, yazabilir=False)
    assert "önce bunu yaz" not in uy and BRIF["tez"] in uy, "var olan brif aralık düzeltmesinde de görülür"


def test_plan_brifi_plani_dusurmez():
    plan = Plan.model_validate({"gorevler": [{"slot": "E1", "katmanlar": ["kurgu"]}], "yaratici_brif": {"tez": ""}})
    assert plan.gorevler and yaratici.dogrula(plan.yaratici_brif) is None


def _k():
    return Kurgu.model_validate({
        "sekans": {"w": 1080, "h": 1920, "fps": 30},
        "kaynaklar": {"a": {"yol": "inputs:a.mp4", "sure": 10}},
        "izler": [{"id": "V2", "tur": "video"}, {"id": "V1", "tur": "video"}],
        "klipler": [{"id": "v", "iz": "V1", "tur": "video", "bas": 0, "sure": 10, "kaynak": "a"}],
    })


def test_plan_paketi_brifi_yalniz_gerekince_ister(tmp_path, monkeypatch):
    p = _p(tmp_path)
    k = _k()
    monkeypatch.setattr(ekip_v3.kural, "yukle", lambda: ekip_v3.kural.Depo())
    v = ekip_v3.varsayilan_dagitim("medium", k)
    assert "yaratici_brif" not in ekip_v3.plan_paketi(p, k, EkipAyar(), None, v)
    m = ekip_v3.plan_paketi(p, k, EkipAyar(), None, v, brif_iste=True)
    assert '"yaratici_brif":' in m and "G0.5 Yaratıcı yön" in m


def test_hizli_brif_paketi_skill_ya_da_kilavuz_tasir():
    m = yaratici.paket("enerjik", "(transkript yok)", sure=30, studyo="instagram", stil="")
    assert "imza_anlari" in m and "(transkript yok)" in m and "enerjik" in m
    assert "Dosya okuma" in m.split("## Kullanıcı isteği")[0], "orkestratör dosya okumaya yollanmaz"
