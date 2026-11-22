"""Kurallar API'si: ekle, düzenle, sil (mezar taşı), aç, toplu, içe ve dışa aktar; checks.md üretimi (ADR 0047)."""

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from vedit import kural, paths
from vedit.studio.app import create_app

HOST = "127.0.0.1:8765"
O = {"origin": f"http://{HOST}"}


@pytest.fixture
def c(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "LIBRARY", tmp_path / "lib")
    monkeypatch.setattr(paths, "OUTPUTS", tmp_path / "out")
    k = TestClient(create_app("t", izinli_hostlar={HOST}), base_url=f"http://{HOST}", follow_redirects=False)
    k.get("/?token=t")
    return k


def test_ekle_duzenle_sil_ac(c):
    r = c.post("/api/kurallar", json={"metin": "YAPMA: ikonu yüzün üstüne koyma", "kategori": "grafik", "hedef_rol": "E2"}, headers=O)
    assert r.status_code == 200
    kid = r.json()["kural"]["id"]
    assert c.post("/api/kurallar", json={"metin": "ikonu yüze koyma"}, headers=O).status_code == 422, "YAP/YAPMA zorunlu"
    r = c.patch(f"/api/kurallar/{kid}", json={"onem": "P0"}, headers=O)
    assert r.json()["kural"]["onem"] == "P0"
    assert "ikonu yüzün üstüne" in (paths.LIBRARY / "checks.md").read_text(encoding="utf-8")
    c.post("/api/kurallar/durum", json={"idler": [kid], "durum": "silinen"}, headers=O)
    assert "ikonu yüzün üstüne" not in (paths.LIBRARY / "checks.md").read_text(encoding="utf-8")
    # Mezar taşı: QC aynı kuralı yeniden öneremez.
    d = kural.yukle()
    k, sonuc = kural.aday_ekle(d, "YAPMA: ikonu yüzün üstüne koyma, göz hizasında olmasın", kaynak="kk:K2")
    assert k is None and sonuc == "mezar"
    c.post("/api/kurallar/durum", json={"idler": [kid], "durum": "aktif"}, headers=O)
    assert c.get("/api/kurallar").json()["kurallar"][0]["durum"] == "aktif"


def test_disa_ice_benzerini_atlar(c):
    c.post("/api/kurallar", json={"metin": "YAP: altyazı bandını boş bırak"}, headers=O)
    disa = c.get("/api/kurallar/disa").json()
    disa["kurallar"].append({**disa["kurallar"][0], "id": "X9", "metin": "YAPMA: geçişte düz renk blok kullanma"})
    r = c.post("/api/kurallar/ice", json=disa, headers=O)
    assert r.json()["eklenen"] == 1 and len(r.json()["kurallar"]) == 2


def test_onay_ayari_qc_adayini_bekletir(c):
    c.put("/api/kurallar/ayar", json={"onay_bekle": True, "butce_token": 1200}, headers=O)
    d = kural.yukle()
    k, sonuc = kural.aday_ekle(d, "YAP: alt bandı en az 2.5 sn ekranda tut", kaynak="kk:K2", kategori="grafik")
    assert sonuc == "yeni" and k.durum == "oneri"
    assert kural.paket(d, rol="E2") == "", "onay bekleyen kural editöre gitmez"


def test_kanit_karesi_koke_goreli_saklanir():
    # QC kanıtı mutlak yolla geliyordu; kural deposu kişisel yol taşıyordu.
    from vedit import kural, paths
    k = kural.Kanit(kare=str(paths.ROOT / "Projeler" / "outputs" / "x.jpg"))
    assert k.kare == "Projeler/outputs/x.jpg"
    assert kural.Kanit(kare="work/a.jpg").kare == "work/a.jpg"
