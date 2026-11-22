"""Hazır stil kataloğu: sözleşme, paket üretimi, stüdyoya ekleme ve API (ADR 0042)."""
import json
import shutil

import pytest
from fastapi.testclient import TestClient

from vedit import motion, paths, stil, stil_katalog
from vedit.hizli import Proje


def test_gercek_katalog_gecerli():
    assert stil_katalog.dogrula() == []
    ids = [e["id"] for e in stil_katalog.stiller()]
    assert len(ids) >= 25 and "anime-sulu-boya" in ids
    kategoriler = {e["kategori"] for e in stil_katalog.stiller()}
    assert {"Anime", "Çizgi film", "Sanat akımı"} <= kategoriler


def test_hicbir_stil_turuncu_varsayilan_temaya_dusmez():
    for e in stil_katalog.stiller():
        assert stil_katalog.tema_adi(e) not in ("varsayilan", "turuncu"), e["id"]


@pytest.fixture
def ortam(tmp_path, monkeypatch):
    tema = tmp_path / "motion" / "tema"
    shutil.copytree(paths.MOTION_DIR / "tema", tema)
    monkeypatch.setattr(paths, "MOTION_DIR", tmp_path / "motion")
    for ad in ("STUDIOS", "REFERENCES", "INPUTS", "OUTPUTS"):
        monkeypatch.setattr(paths, ad, tmp_path / ad.lower())
    (tema / "anime-sulu-boya.css").unlink(missing_ok=True)
    return tmp_path


def test_paket_ve_ekle(ortam):
    e = stil_katalog.bul("anime-sulu-boya")
    pk = stil_katalog.paket(e)
    tok = json.loads(pk["tokens.json"])
    assert tok["motion_tema"] == "anime-sulu-boya" and tok["colors"]["accent"] == e["palet"]["vurgu"]
    assert "ADR 0043" in pk["STYLE.md"], "altyazı kuralı pakette yazılı kalır (stilin token'ı)"

    p = Proje("instagram", "deneme")
    hedef = stil_katalog.ekle("instagram", "anime-sulu-boya", p)
    assert all((hedef / d).is_file() for d in stil.PAKET_DOSYALARI)
    assert motion.tema_yolu("anime-sulu-boya"), "kendi paleti olan stil için tema CSS yazılır"
    assert stil.secili_adi(p) == "anime-sulu-boya"
    assert stil.motion_temasi(hedef) == "anime-sulu-boya"
    with pytest.raises(SystemExit, match="zaten var"):
        stil_katalog.ekle("instagram", "anime-sulu-boya")
    with pytest.raises(SystemExit, match="Katalogda stil yok"):
        stil_katalog.ekle("instagram", "olmayan")


def test_api_katalog_ve_ekle(ortam):
    from vedit.studio.app import create_app
    host = "127.0.0.1:8765"
    o = {"origin": f"http://{host}"}
    c = TestClient(create_app("t", izinli_hostlar={host}), base_url=f"http://{host}", follow_redirects=False)
    c.get("/?token=t")
    r = c.get("/api/stil-katalog")
    assert r.status_code == 200 and r.json()["stiller"][0]["palet"]["vurgu"].startswith("#")
    assert c.post("/api/stil/instagram/katalogdan", json={"id": "vaporwave"}, headers=o).status_code == 200
    assert c.post("/api/stil/instagram/katalogdan", json={"id": "vaporwave"}, headers=o).status_code == 409
    assert any(s["ad"] == "vaporwave" and s["hazir"] for s in c.get("/api/stil/instagram").json()["stiller"])
    assert c.delete("/api/stil/instagram/vaporwave", headers=o).status_code == 200
    assert c.delete("/api/stil/instagram/vaporwave", headers=o).status_code == 404
