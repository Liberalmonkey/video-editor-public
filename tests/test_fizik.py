"""Fizik sahnesi: denetim, bake bağlama, temas sesleri ve galeri API'si (ADR 0039)."""
import json
import shutil

import pytest

from vedit import fizik, karakter, kurgu, paths
from vedit.hizli import Proje
from vedit.schemas import Kurgu

pytestmark = pytest.mark.skipif(not shutil.which("node"), reason="fizik bake Node.js ister")


@pytest.fixture
def p(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "INPUTS", tmp_path / "in")
    monkeypatch.setattr(paths, "OUTPUTS", tmp_path / "out")
    pr = Proje("youtube-animasyon", "x")
    pr.girdi.mkdir(parents=True)
    return pr


def kur(*sahneler):
    return Kurgu.model_validate({
        "sekans": {"w": 1920, "h": 1080, "fps": 30},
        "izler": [{"id": "V1", "tur": "video"}, {"id": "A2", "tur": "ses"}],
        "klipler": [{"id": f"f{i}", "iz": "V1", "tur": "sahne", "bas": i * 4, "sure": 4, "sahne": {"kind": "fizik", "layout": "full", **s}}
                    for i, s in enumerate(sahneler)]})


def test_denetim_bilinmeyen_ve_aralik_disi(p):
    k = kur({"preset": "yok"}, {"preset": "top-dusme", "param": {"yukseklik": 99}}, {"preset": "domino", "param": {"renk": 1}},
            {"preset": "araba-ivme", "param": {"kamera": "ustten"}}, {"preset": "sarkac", "isik": {"preset": "disko"}})
    h = " | ".join(kurgu.denetle(p, k))
    assert "bilinmeyen fizik preseti 'yok'" in h and "yukseklik = 99" in h and "'renk' parametresi yok" in h
    assert "seçenekler: takip, yan, sabit" in h and "bilinmeyen ışık preseti 'disko'" in h


def test_bagla_onbellek_ve_temas_sesi(p):
    k = kur({"preset": "top-dusme", "param": {"yukseklik": 3, "sekme": 0.7}})
    assert fizik.bagla(p, k) is True
    yol = kurgu.dosya(p, k.kaynaklar[k.klipler[0].kaynak].yol)
    veri = json.loads(yol.read_text(encoding="utf-8"))
    assert veri["kare"] == 120 and veri["renk"]["vurgu"]
    zaman = yol.stat().st_mtime_ns
    assert fizik.bagla(p, k) is False and yol.stat().st_mtime_ns == zaman  # aynı girdi: yeniden bake yok
    k.klipler[0].bas = 10
    olay = fizik.ses_olaylari(p, k)
    assert olay[0]["t"] == pytest.approx(10 + veri["temas"][0]["t"], abs=1e-3) and olay[0]["tur"] == "vurgu"
    assert sum(o["guc"] == "sert" for o in olay) <= fizik.EN_COK_SERT
    # Parametre değişince yeni kaynak.
    eski = k.klipler[0].kaynak
    k.klipler[0].sahne["param"]["yukseklik"] = 5
    assert fizik.bagla(p, k) is True and k.klipler[0].kaynak != eski


def test_olaylar_json_temas_sesini_tasir(p):
    k = kur({"preset": "domino", "param": {"adet": 8}})
    fizik.bagla(p, k)
    kurgu.yaz(p.work, k)
    kurgu.hazirla(p)
    o = json.loads((p.work / "edit" / "olaylar.json").read_text(encoding="utf-8"))["olaylar"]
    assert o and all("fizik teması" in x["not"] for x in o) and {x["tur"] for x in o} <= {"tik", "vurgu"}


def test_ses_kalabaligi_sinirlanir(p):
    k = kur({"preset": "kule-cokus", "param": {"kat": 10, "top_hizi": 20}})
    fizik.bagla(p, k)
    o = fizik.ses_olaylari(p, k)
    darbe = [x for x in o if x["tur"] == "vurgu"]
    assert len(darbe) <= fizik.EN_COK_DARBE
    assert all(b["t"] - a["t"] >= fizik.DARBE_ARALIK - 1e-6 for a, b in zip(darbe, darbe[1:]))


def test_karakter_denetimi(p):
    k = Kurgu.model_validate({"izler": [{"id": "V1", "tur": "video"}],
                              "klipler": [{"id": "c", "iz": "V1", "tur": "sahne", "bas": 0, "sure": 2, "sahne": {"kind": "karakter", "karakter": "yok"}}]})
    assert any("bilinmeyen karakter" in h for h in kurgu.denetle(p, k))
    assert karakter.katalog_metni().startswith("### Konuşan karakter")


def test_galeri_api(p, tmp_path):
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient
    from vedit.studio.app import create_app

    host = "127.0.0.1:8765"
    kurgu.yaz(p.work, kur())
    c = TestClient(create_app("t", izinli_hostlar={host}), base_url=f"http://{host}", follow_redirects=False)
    c.get("/?token=t")
    og = c.get("/api/galeri").json()["ogeler"]
    turler = {o["tur"] for o in og}
    assert {"tema", "motion", "fizik", "isik", "karakter", "hazir"} <= turler
    org = {"origin": f"http://{host}"}
    r = c.post("/api/sahne-bagla/youtube-animasyon/x", json={"sahne": {"kind": "fizik", "preset": "sarkac"}, "bas": 0, "sure": 2}, headers=org)
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["yol"].startswith("public:fizik/sarkac-") and j["url"].startswith("/dosya/youtube-animasyon/x/public/fizik/")
    r = c.post("/api/sahne-bagla/youtube-animasyon/x", json={"sahne": {"kind": "fizik", "preset": "yok"}, "bas": 0, "sure": 2}, headers=org)
    assert r.status_code == 422
