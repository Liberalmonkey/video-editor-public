"""Ekip motoru (ADR 0044): sahiplik reddi, birleştirme, bulgu şeması, zaman bölüşü, yedek motor ve tur döngüsü.

Ajanlar, hazirla, taslak ve izleme taklit edilir; gerçek motor çağrılmaz.
"""
import json
import re
from pathlib import Path

import pytest

from vedit import aiedit, ekip, ff, hizli, kurgu, paths
from vedit.ekip_sema import EkipAyar, Parca, Slot


@pytest.fixture
def proje(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "INPUTS", tmp_path / "inputs")
    monkeypatch.setattr(paths, "OUTPUTS", tmp_path / "outputs")
    monkeypatch.setattr(paths, "STUDIOS", tmp_path / "studios")
    p = hizli.Proje("instagram", "deneme")
    p.girdi.mkdir(parents=True)
    (p.girdi / "1.mp4").write_bytes(b"video")
    monkeypatch.setattr(ff, "probe", lambda f: {"file": Path(f).name, "duration": 9.0, "video": {"width": 1080, "height": 1920, "fps": 30},
                                                "audio": {"codec": "aac", "sample_rate": 48000, "channels": 2}})

    def sahte_hazirla(prj, **k):
        for d in ("analysis", "edit", "renders", "qa", "public"):
            (prj.work / d).mkdir(parents=True, exist_ok=True)
        kel = [{"w": w, "s": s, "e": e} for w, s, e in (("Bir", 0.0, 0.8), ("iki", 1.0, 2.6), ("üç", 3.4, 4.2), ("dört", 4.5, 5.6),
                                                         ("beş", 6.2, 7.0), ("altı", 7.2, 8.6))]
        tr = {"files": {"1": {"segments": [{"start": 0.0, "end": 8.6, "text": "Bir iki üç dört beş altı", "words": kel}]}}}
        (prj.work / "analysis" / "transcript.json").write_text(json.dumps(tr), encoding="utf-8")
        (prj.work / "analysis" / "digest.txt").write_text("# 1.mp4\n[0.00-8.60] Bir iki üç dört beş altı\n", encoding="utf-8")

    def sahte_taslak(prj, **k):
        f = prj.work / "renders" / "taslak.mp4"
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_bytes(b"taslak")
        return f

    monkeypatch.setattr(hizli, "hazirla", sahte_hazirla)
    monkeypatch.setattr(hizli, "taslak", sahte_taslak)

    def sahte_izle(prj, video, kok):
        (kok / "izle").mkdir(parents=True, exist_ok=True)
        (kok / "izle" / "kare_0003.0.jpg").write_bytes(b"jpg")
        return {"_kok": kok, "taslak video": video}

    monkeypatch.setattr(ekip, "izle", sahte_izle)
    return p


def _ayar(**ek):
    sl = {s: Slot(motor="claude", model="m", yedek_motor="antigravity", yedek_model="y") for s in ("E1", "E2", "E3", "K1", "K2", "K3")}
    return EkipAyar(slotlar=sl, **ek)


def _hazir(proje):
    hizli.hazirla(proje)
    return aiedit._kurgu_hazirla(proje)


def test_sahiplik_disi_klip_reddedilir(proje):
    k = _hazir(proje)
    kap = ekip.kapsamlar(k, _ayar(), None)
    yabanci = Parca(klipler=[{"id": "x1", "iz": "V2", "bas": 1, "sure": 1, "tur": "metin", "metin": "a"}])
    assert ekip.sahiplik_hatalari("E1", yabanci, kap["E1"])
    assert ekip.sahiplik_hatalari("E2", Parca(altyazi={"acik": False}), kap["E2"])
    with pytest.raises(SystemExit, match="sahipliğin dışında"):
        ekip.birlestir(k, {"E1": yabanci}, kap)


def test_birlestirme_parcalari_uygular_ve_kaynagi_korur(proje):
    k = _hazir(proje)
    kap = ekip.kapsamlar(k, _ayar(), None)
    e2 = Parca(klipler=[{"id": "g1", "iz": "V2", "bas": 1.0, "sure": 1.5, "tur": "metin", "metin": "Merhaba"}])
    e3 = Parca(motion_tema="varsayilan")
    yeni = ekip.birlestir(k, {"E2": e2, "E3": e3}, kap)
    assert any(c.id == "g1" for c in yeni.klipler) and [c.id for c in yeni.klipler if c.iz == "V1"] == [c.id for c in k.klipler if c.iz == "V1"]
    kid = next(iter(k.kaynaklar))
    with pytest.raises(SystemExit, match="mevcut kaynak"):
        ekip.birlestir(k, {"E2": Parca(kaynaklar={kid: {"yol": "inputs:baska.mp4", "sure": 1, "ses": False}})}, kap)


def test_zaman_bolusu_kelime_arasina_duser(proje):
    k = _hazir(proje)
    araliklar = ekip.zaman_araliklari(k)
    assert len(araliklar) == 3 and araliklar[0][0] == 0 and araliklar[-1][1] == pytest.approx(9.0)
    kel = [(w["s"], w["e"]) for w in kurgu.izdusum(k)]
    for _, b in araliklar[:-1]:
        assert not any(s < b < e for s, e in kel), f"{b} bir kelimenin ortasında"


def test_json_cikar_ve_bulgu_dogrulama(tmp_path):
    kare = tmp_path / "k.jpg"
    kare.write_bytes(b"x")
    metin = ("Açıklama\n```json\n" + json.dumps({"bulgular": [
        {"id": "K2-001", "hedef": "E2", "onem": "P1", "zaman": [1, 2], "katman": "V2", "kategori": "stil", "kanit": str(kare), "sorun": "s", "beklenen": "b"},
        {"id": "K2-002", "hedef": "E2", "onem": "P0", "zaman": [3, 4], "katman": "V2", "kategori": "stil", "kanit": "yok.jpg", "sorun": "s", "beklenen": "b"}],
        "brif": "# Brif"}) + "\n```")
    o = ekip.json_cikar(metin)
    c, dus = ekip.bulgu_dogrula(o, "K2")
    assert [b.id for b in c.bulgular] == ["K2-001"] and dus and c.brif == "# Brif"
    assert ekip.bulgu_dogrula({"bulgular": [{"id": "X"}]}, "K2")[0] is None


def test_ayar_katmanlari(proje, tmp_path, monkeypatch):
    g = tmp_path / "ekip.json"
    g.write_text(json.dumps({"varsayilan": "a", "onayarlar": {"a": {"tur": 2}}}), encoding="utf-8")
    monkeypatch.setattr(ekip, "GLOBAL", g)
    (proje.work / "edit").mkdir(parents=True, exist_ok=True)
    (proje.work / "edit" / "ekip.json").write_text(json.dumps({"bolus": "zaman"}), encoding="utf-8")
    a = ekip.ayar_yukle(proje, tur=4)
    assert (a.tur, a.bolus) == (4, "zaman")
    with pytest.raises(Exception):
        EkipAyar(slotlar={"E1": Slot(motor="claude")})


def _sahte_ekip(proje, kayit: list, *, bozuk_e2_ilk: bool = False, k_turu: dict | None = None):
    """Rolü istem dosyasından bulan sahte ajan. Editör parça yazar, K turuna göre bulgu döner."""
    def ajan(slot, istem, mod, yol, *, yedek=False):
        f = Path(re.search(r"Read the file (.+?\.istem\.md)", istem).group(1))
        rol = f.name.split(".")[0]
        tur = int(f.parent.name.split("-")[1])
        kayit.append((tur, rol, yedek))
        meta = {"motor": slot.yedek_motor if yedek else slot.motor, "sure": 0.1}
        if rol.startswith("E"):
            cikti = f.with_name(f"{rol}.json")
            k = kurgu.oku(proje.work)
            if rol == "E1":
                pr = {"klipler": [c.model_dump() for c in k.klipler if c.iz == "V1"], "isaretler": [{"t": 0, "ad": "Giriş"}]}
            elif rol == "E2":
                if bozuk_e2_ilk and not yedek:
                    cikti.write_text("{bozuk", encoding="utf-8")
                    return True, "", meta
                pr = {"klipler": [{"id": f"g{tur}", "iz": "V2", "bas": 1.0, "sure": 2.0, "tur": "metin", "metin": "Merhaba"}]}
            else:
                pr = {"klipler": [], "motion_tema": "varsayilan"}
            cikti.write_text(json.dumps(pr), encoding="utf-8")
            return True, "", meta
        kare = next((f.parent / "izle").glob("*.jpg"))
        bl = (k_turu or {}).get((tur, rol), [])
        return True, "```json\n" + json.dumps({"bulgular": [{"id": f"{rol}-001", "hedef": "E2", "onem": o, "zaman": [1, 2], "katman": "V2",
                                                            "kategori": "stil", "kanit": str(kare), "sorun": "renk", "beklenen": "token"} for o in bl],
                                               "brif": "brif"}) + "\n```", meta
    return ajan


def test_tur_dongusu_p1_kapaninca_durur(proje, monkeypatch):
    kayit = []
    monkeypatch.setattr(ekip, "ajan", _sahte_ekip(proje, kayit, k_turu={(1, "K2"): ["P1"]}))
    s = ekip.calistir(proje, _ayar(tur=3))
    assert len(s["turlar"]) == 2 and not s["acik"] and len(s["kapanan"]) == 1
    tur2 = {r for t, r, _ in kayit if t == 2}
    assert "E2" in tur2 and "E1" not in tur2, "düzeltme turunda yalnız bulgusu olan editör çalışır"
    # E1, E2/E3'ten önce çalışır
    tur1 = [r for t, r, _ in kayit if t == 1]
    assert tur1.index("E1") < tur1.index("E2") and tur1.index("E1") < tur1.index("E3")
    rapor = (proje.work / "edit" / "ai-edit.rapor.md").read_text(encoding="utf-8")
    assert "## Turlar" in rapor and "Kapanan bulgular (1)" in rapor
    d = json.loads((proje.work / "edit" / "ekip" / "durum.json").read_text(encoding="utf-8"))
    assert d["bitti"] and d["acik"]["P1"] == 0


def test_bozuk_parca_yedek_motora_gecer(proje, monkeypatch):
    kayit = []
    monkeypatch.setattr(ekip, "ajan", _sahte_ekip(proje, kayit, bozuk_e2_ilk=True))
    ekip.calistir(proje, _ayar(tur=1))
    e2 = [y for t, r, y in kayit if r == "E2"]
    assert e2 == [False, False, True], "bir yeniden deneme, sonra yedek motor"
    assert any(c.id == "g1" for c in kurgu.oku(proje.work).klipler)


def test_hic_birlesmeyen_parca_kurguyu_bozmaz(proje, monkeypatch):
    kayit = []
    ajan = _sahte_ekip(proje, kayit, bozuk_e2_ilk=True)

    def hep_bozuk(slot, istem, mod, yol, *, yedek=False):
        if "E2.istem" in istem:
            Path(re.search(r"Read the file (.+?)E2\.istem\.md", istem).group(1) + "E2.json").write_text("{bozuk", encoding="utf-8")
            return True, "", {"sure": 0}
        return ajan(slot, istem, mod, yol, yedek=yedek)

    monkeypatch.setattr(ekip, "ajan", hep_bozuk)
    s = ekip.calistir(proje, _ayar(tur=1))
    assert any("E2 birleşmedi" in n for n in s["turlar"][0]["notlar"])
    k = kurgu.oku(proje.work)
    assert not any(c.iz == "V2" for c in k.klipler) and k.isaretler, "E1 birleşti, bozuk E2 birleşmedi"


def test_yanit_vermeyen_denetci_bulgusu_kapanmaz(proje, monkeypatch):
    kayit = []
    temel = _sahte_ekip(proje, kayit, k_turu={(1, "K2"): ["P1"]})

    def ajan(slot, istem, mod, yol, *, yedek=False):
        if "tur-2" in istem and "K2.istem" in istem:
            return False, "", {"hata": "kota", "sure": 0}
        return temel(slot, istem, mod, yol, yedek=yedek)

    monkeypatch.setattr(ekip, "ajan", ajan)
    s = ekip.calistir(proje, _ayar(tur=2))
    assert not s["kapanan"] and s["acik"] and s["acik"][0]["denetlenmedi"]
    assert "denetlenmedi" in (proje.work / "edit" / "ai-edit.rapor.md").read_text(encoding="utf-8")
