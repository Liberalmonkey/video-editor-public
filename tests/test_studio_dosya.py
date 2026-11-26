import json
import os
import shutil
import sys
import time

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from vedit import paths, sfx
from vedit.studio import isler, ortak
from vedit.studio.app import create_app

HOST = "127.0.0.1:8765"
ORIGIN = {"origin": f"http://{HOST}"}


@pytest.fixture
def ortam(tmp_path, monkeypatch):
    lib = tmp_path / "library"
    for a, b in {"INPUTS": tmp_path / "in", "OUTPUTS": tmp_path / "out", "LIBRARY": lib, "ROOT": tmp_path,
                 "SFX_DIR": lib / "sfx", "MUSIC_DIR": lib / "music", "MOTION_DIR": lib / "motion", "FONTS_DIR": lib / "fonts"}.items():
        monkeypatch.setattr(paths, a, b)
    monkeypatch.setattr(sfx, "RAW", lib / "sfx" / "raw")
    monkeypatch.setattr(sfx, "PROC", lib / "sfx" / "processed")
    monkeypatch.setattr(sfx, "MANIFEST", lib / "sfx" / "manifest.json")
    for d in ("sfx/raw", "sfx/processed", "music/x", "motion", "fonts", "boards"):
        (lib / d).mkdir(parents=True)
    for ad in ("m", "kilitli", "yuva"):
        (lib / "music" / "x" / f"{ad}.mp3").write_bytes(b"m")
    kayit = lambda i: {"id": i, "file": f"library/music/x/{i}.mp3"}
    (lib / "music" / "manifest.json").write_text(json.dumps({"_note": "n", "entries": [kayit("m"), kayit("kilitli"), kayit("yuva")]}))
    (lib / "motion" / "manifest.json").write_text(json.dumps({"_note": "n", "entries": []}))
    (lib / "sfx" / "manifest.json").write_text(json.dumps({"version": 1, "entries": []}))
    (lib / "fonts" / "fonts.json").write_text(json.dumps({"_note": "n", "Montserrat": {"file": "M.ttf"}}))
    (lib / "boards" / "catalog.json").write_text("[]")
    (lib / "kit.json").write_text(json.dumps({"locked": ["kilitli"], "always": {"*": {"zoom_in": "yuva", "keyboard": "kilitli"}}}))
    (tmp_path / "in" / "instagram").mkdir(parents=True)
    silinen = []

    def sahte_cop(y):
        silinen.append(y)
        os.remove(y) if os.path.isfile(y) else shutil.rmtree(y)

    monkeypatch.setattr(ortak, "send2trash", sahte_cop)
    c = TestClient(create_app("t", izinli_hostlar={HOST}), base_url=f"http://{HOST}", follow_redirects=False)
    c.get("/?token=t")
    return c, tmp_path, silinen


def test_proje_olustur_ve_cakisma(ortam):
    c, t, _ = ortam
    r = c.post("/api/projeler", json={"studyo": "instagram", "ad": "Yeni Video!"}, headers=ORIGIN)
    assert r.json()["ad"] == "yeni-video" and (t / "in/instagram/yeni-video").is_dir()
    assert c.post("/api/projeler", json={"studyo": "instagram", "ad": "yeni video"}, headers=ORIGIN).status_code == 409
    assert c.post("/api/projeler", json={"studyo": "evil", "ad": "x"}, headers=ORIGIN).status_code == 400


def test_yukleme_ad_temizler_uzerine_yazmaz(ortam):
    c, t, _ = ortam
    (t / "in/instagram/x").mkdir()
    u = "/api/yukle/instagram/x"
    assert c.put(u, params={"dosya": "../../kac.mp4"}, content=b"a", headers=ORIGIN).status_code == 200
    assert (t / "in/instagram/x/kac.mp4").read_bytes() == b"a" and not (t / "kac.mp4").exists()
    assert c.put(u, params={"dosya": "kac.mp4"}, content=b"b", headers=ORIGIN).json() == {"boyut": 1, "ad": "kac-2.mp4"}
    assert (t / "in/instagram/x/kac.mp4").read_bytes() == b"a" and (t / "in/instagram/x/kac-2.mp4").read_bytes() == b"b"
    assert c.put(u, params={"dosya": "z.html"}, content=b"<x>", headers=ORIGIN).status_code == 415
    assert c.put(u, params={"dosya": "z.exe"}, content=b"x", headers=ORIGIN).status_code == 415
    assert c.put(u, params={"dosya": "bos.mp4"}, content=b"", headers=ORIGIN).status_code == 400
    assert not list((t / "in/instagram/x").glob(".*")), "yarım dosya kalmamalı"


def test_dosya_sil_work_ve_kok_disi(ortam):
    c, t, silinen = ortam
    (t / "out/instagram/x/work").mkdir(parents=True)
    (t / "out/instagram/x/work/g.json").write_text("{}")
    (t / "out/instagram/x/t.txt").write_bytes(b"t")
    (t / "out/instagram/dis.txt").write_bytes(b"d")
    u = "/api/dosya/instagram/x/outputs"
    assert c.delete(u, params={"yol": "work/g.json"}, headers=ORIGIN).status_code == 403
    assert c.delete(u, params={"yol": "../dis.txt"}, headers=ORIGIN).status_code == 404
    assert [d["ad"] for d in c.get("/api/dosyalar/instagram/x/outputs").json()] == ["t.txt"], "work listelenmez"
    assert c.delete(u, params={"yol": "t.txt"}, headers=ORIGIN).status_code == 200
    assert len(silinen) == 1 and (t / "out/instagram/dis.txt").exists()


def test_buyuk_silme_kaliciya_gitmez(ortam, monkeypatch):
    c, t, silinen = ortam
    monkeypatch.setattr(ortak, "GERI_DONUSUM_SINIRI", 1)
    (t / "in/instagram/x").mkdir()
    (t / "in/instagram/x/b.txt").write_bytes(b"12345")
    r = c.delete("/api/dosya/instagram/x/inputs", params={"yol": "b.txt"}, headers=ORIGIN)
    assert ".cop" in r.json()["mesaj"] and not silinen
    assert [f.read_bytes() for f in (t / "Projeler/.cop").rglob("b.txt")] == [b"12345"]


def test_kilitli_ve_yuvadaki_varlik(ortam):
    c, t, silinen = ortam
    k = "/api/kutuphane/muzik/"
    assert c.delete(k + "kilitli", headers=ORIGIN).status_code == 423
    assert c.delete(k + "kilitli", params={"zorla": True}, headers=ORIGIN).status_code == 423, "zorla kilidi aşamaz"
    r = c.delete(k + "yuva", headers=ORIGIN)
    assert r.status_code == 409 and "*.zoom_in" in r.json()["detail"]
    assert c.delete(k + "yuva", params={"zorla": True}, headers=ORIGIN).status_code == 200
    assert c.delete(k + "m", headers=ORIGIN).status_code == 200
    kalan = json.loads((t / "library/music/manifest.json").read_text())
    assert [e["id"] for e in kalan["entries"]] == ["kilitli"] and kalan["_note"] == "n" and len(silinen) == 2
    # ADR 0061: onaylı yol, kilit kaldırılır ve silinir
    assert c.delete(k + "kilitli", params={"kilit_ac": True}, headers=ORIGIN).status_code == 200
    assert "kilitli" not in json.loads((t / "library/kit.json").read_text())["locked"]


def test_toplu_sil_kilit_ve_kasa(ortam):
    c, t, silinen = ortam
    r = c.post("/api/kutuphane/toplu-sil", json={"tur": "muzik", "idler": ["m", "kilitli", "yuva", "yok"]}, headers=ORIGIN).json()
    assert r["silinen"] == ["m"] and {a["id"]: a["durum"] for a in r["atlanan"]} == {"kilitli": 423, "yuva": 409, "yok": 404}
    # Kilit aç / kilitle ucu: yuvadaki kimlik boşalır
    r = c.put("/api/kit/kilit", json={"id": "yuva", "kilitli": False}, headers=ORIGIN).json()
    assert r["bos_yuva"] == ["*.zoom_in"]
    assert c.put("/api/kit/kilit", json={"id": "m2", "kilitli": True}, headers=ORIGIN).status_code == 200
    assert "m2" in json.loads((t / "library/kit.json").read_text())["locked"]
    # Kasa listesi, silme ve galeri gizleme
    (t / "library/kasa/a").mkdir(parents=True)
    (t / "library/kasa/a/a.webm").write_bytes(b"w")
    (t / "library/kasa/manifest.json").write_text(json.dumps({"entries": [{"id": "a", "title": "A", "tur": "motion", "file": "library/kasa/a/a.webm", "sure": 1}]}))
    assert [e["id"] for e in c.get("/api/kutuphane").json()["kasa"]] == ["a"]
    assert c.delete("/api/kutuphane/kasa/a", headers=ORIGIN).status_code == 200
    assert c.get("/api/kutuphane").json()["kasa"] == [] and not (t / "library/kasa/a").exists()
    assert c.post("/api/galeri/gizle", json={"anahtar": "fizik:domino"}, headers=ORIGIN).json()["gizli"] == ["fizik:domino"]
    assert c.post("/api/galeri/gizle", json={"anahtar": "../x"}, headers=ORIGIN).status_code == 422


def test_kullanimdaki_varlik_uyarilir(ortam):
    c, t, _ = ortam
    e = t / "out/instagram/p/work/edit"
    e.mkdir(parents=True)
    (e / "kurgu.json").write_text('{"yol": "library:music/x/m.mp3"}')
    r = c.delete("/api/kutuphane/muzik/m", headers=ORIGIN)
    assert r.status_code == 409 and "instagram/p" in r.json()["detail"]


def test_korunan_font_ve_kit_kilidi(ortam):
    c, t, _ = ortam
    assert c.delete("/api/kutuphane/font/Montserrat", headers=ORIGIN).status_code == 403
    assert c.put("/api/kit", json={"studyo": "*", "rol": "keyboard", "id": "m"}, headers=ORIGIN).status_code == 403
    assert c.put("/api/kit", json={"studyo": "*", "rol": "zoom_in", "id": "m"}, headers=ORIGIN).status_code == 200
    assert json.loads((t / "library/kit.json").read_text())["always"]["*"]["zoom_in"] == "m"


def test_kutuphane_yukleme_lisans_ister(ortam):
    c, t, _ = ortam
    r = c.put("/api/kutuphane/muzik", params={"dosya": "a.mp3", "lisans": " "}, content=b"x", headers=ORIGIN)
    assert r.status_code == 422 and not (t / "library/music/kullanici").exists()


def test_kullanici_html_i_sandbox_ile_gelir(ortam):
    c, t, _ = ortam
    (t / "in/instagram/x").mkdir()
    (t / "in/instagram/x/k.html").write_text("<script>")
    r = c.get("/dosya/instagram/x/inputs/k.html")
    assert r.headers["content-security-policy"] == "sandbox" and r.headers["x-content-type-options"] == "nosniff"


def test_is_beyaz_liste():
    A = lambda **k: isler.arguman(isler.Istek(**k))
    assert A(komut="taslak", studyo="instagram", ad="x", aralik=(1, 2)) == ["taslak", "instagram/x", "--aralik", "1.000", "2.000"]
    assert A(komut="final", studyo="instagram", ad="x", yenile=True) == ["final", "instagram/x", "--yenile"]
    assert A(komut="final", studyo="instagram", ad="x", cozunurluk=1440, kalite="arsiv", kodek="h265", fps=60) == [
        "final", "instagram/x", "--cozunurluk", "1440", "--kalite", "arsiv", "--kodek", "h265", "--fps", "60"]
    for kotu in (dict(cozunurluk=1441), dict(kalite="--yenile"), dict(kodek="vp9"), dict(fps=24)):
        with pytest.raises(Exception):
            A(komut="final", studyo="instagram", ad="x", **kotu)
    for kotu in (dict(komut="pano", studyo="instagram", ad="x"), dict(komut="hazirla && calc", studyo="instagram", ad="x"),
                 dict(komut="final", studyo="instagram", ad="x", cikti_adi="a;b"), dict(komut="final", studyo="instagram", ad="x", platform="--yenile"),
                 dict(komut="final", studyo="instagram", ad="../x"), dict(komut="hazirla", studyo="instagram", ad="x", dil="--x")):
        with pytest.raises(Exception) as e:
            A(**kotu)
        assert getattr(e.value, "status_code", 0) == 400, kotu


def test_kuyruk_sirali_ve_iptal():
    k = isler.Kuyruk(exe=sys.executable)
    uzun = k.ekle("x", "uzun", ["-c", "import time;print('bas',flush=True);time.sleep(30)"])
    bekleyen = k.ekle("x", "sirada", ["-c", "print('hic')"])
    kotu = k.ekle("x", "kotu", ["-c", "import sys;sys.exit(3)"])
    for _ in range(200):
        if uzun.satirlar:
            break
        time.sleep(0.05)
    assert uzun.durum == "calisiyor" and bekleyen.durum == "sirada", "aynı anda tek iş"
    k.iptal(bekleyen)
    k.iptal(uzun)
    for _ in range(200):
        if kotu.bitis:
            break
        time.sleep(0.05)
    assert (uzun.durum, bekleyen.durum, kotu.durum, kotu.kod) == ("iptal", "iptal", "hata", 3)
    assert not bekleyen.satirlar


def test_gorsel_kucuk_resmi_dosyanin_kendisi(ortam):
    c, t, _ = ortam
    (t / "out/instagram/x").mkdir(parents=True)
    (t / "out/instagram/x/k.jpg").write_bytes(b"\xff\xd8ham")
    r = c.get("/api/kucuk/instagram/x/outputs", params={"yol": "k.jpg"})
    assert r.status_code == 200 and r.content == b"\xff\xd8ham"


def test_kapak_komutu_kaldirildi():
    """ADR 0056: kapak işi kuyruğa giremez."""
    with pytest.raises(Exception) as e:
        isler.arguman(isler.Istek(komut="kapak", studyo="instagram", ad="x"))
    assert getattr(e.value, "status_code", 0) == 400


def test_ai_edit_ve_stil_beyaz_liste(monkeypatch):
    from vedit.studio import ajan
    monkeypatch.setattr(ajan, "_durum", lambda: {"claude": {"kurulu": True, "modeller": [{"id": "opus"}]}})
    A = lambda **k: isler.arguman(isler.Istek(**{"komut": "ai-edit", "studyo": "instagram", "ad": "x", **k}))
    assert A() == ["ai-edit", "instagram/x"]
    assert A(motor="claude", model="opus", stil="ai-reels", notu="-hızlı\nkes", final=True, platform="reels", yenile=True) == \
        ["ai-edit", "instagram/x", "--motor", "claude", "--model", "opus", "--stil", "ai-reels", "--not=-hızlı kes", "--final",
         "--platform", "reels", "--yenile"]
    assert A(platform="reels") == ["ai-edit", "instagram/x"], "final bayrakları yalnız --final ile"
    assert A(aralik=(2, 5.5)) == ["ai-edit", "instagram/x", "--aralik", "2.000", "5.500"]
    assert A(komut="stil-uret", ad=None, stil="yeni", motor="claude") == ["stil-uret", "instagram", "yeni", "--motor", "claude"]
    for kotu in (dict(motor="bash"), dict(model="opus"), dict(motor="claude", model="x; calc"), dict(stil="../x"),
                 dict(notu="x" * 2001), dict(komut="stil-uret", stil="a/b"), dict(komut="stil-uret", studyo="yok", stil="a")):
        with pytest.raises(Exception) as e:
            A(**kotu)
        assert getattr(e.value, "status_code", 0) == 400, kotu


def test_ses_araclari_beyaz_liste(ortam, monkeypatch):
    c, t, _ = ortam
    (t / "in/instagram/x").mkdir()
    (t / "in/instagram/x/1.mp4").write_bytes(b"v")
    A = lambda **k: isler.arguman(isler.Istek(**{"komut": "ayristir", "studyo": "instagram", "ad": "x", **k}))
    assert A(yol="inputs:1.mp4") == ["ayristir", "instagram/x", "inputs:1.mp4", "--stem", "2"]
    assert A(yol="inputs:1.mp4", stem=4) == ["ayristir", "instagram/x", "inputs:1.mp4", "--stem", "4"]
    assert A(hepsi=True, stem=4) == ["ayristir", "instagram/x", "--hepsi", "--stem", "4"]
    assert A(komut="ses-cikar", yol="inputs:1.mp4", bicim="mp3") == ["ses-cikar", "instagram/x", "inputs:1.mp4", "--bicim", "mp3"]
    assert A(komut="ses-cikar", hepsi=True) == ["ses-cikar", "instagram/x", "--hepsi", "--bicim", "wav"]
    for kotu in (dict(), dict(yol="inputs:../../x.mp4"), dict(yol="inputs:yok.mp4"), dict(yol="library:x.mp3"), dict(yol="C:/x.mp4"),
                 dict(yol="inputs:1.mp4", stem=3), dict(komut="ses-cikar", yol="inputs:1.mp4", bicim="ogg; calc")):
        with pytest.raises(Exception) as e:
            A(**kotu)
        assert getattr(e.value, "status_code", 0) in (400, 404), kotu
    gelen = {"yol": "inputs:1.mp4", "stem": 2}
    assert c.get("/api/ayristir/instagram/x", params=gelen).json() == {"hazir": False}
    monkeypatch.setattr("vedit.ayristir.hazir", lambda: False)
    r = c.post("/api/ayristir/instagram/x", json=gelen, headers=ORIGIN)
    assert r.status_code == 503 and "Demucs" in r.json()["detail"]


def test_indir_ek_olarak_verir_work_ve_kok_disi_yok(ortam):
    c, t, _ = ortam
    (t / "out/instagram/x/work").mkdir(parents=True)
    (t / "out/instagram/x/work/ham.mp4").write_bytes(b"h")
    (t / "out/instagram/x/video-v2.mp4").write_bytes(b"video")
    (t / "out/instagram/dis.txt").write_bytes(b"d")
    u = "/api/indir/instagram/x"
    r = c.get(u, params={"yol": "video-v2.mp4"})
    assert r.status_code == 200 and r.content == b"video"
    assert r.headers["content-disposition"].startswith("attachment") and "video-v2.mp4" in r.headers["content-disposition"]
    assert c.get(u, params={"yol": "work/ham.mp4"}).status_code == 404
    assert c.get(u, params={"yol": "../dis.txt"}).status_code == 404
    assert c.get(u, params={"yol": "yok.mp4"}).status_code == 404


def test_teslim_ozeti_kurgu_hatasini_bildirir(ortam):
    from vedit import hizli, kurgu
    from vedit.studio.app import teslim_ozeti
    c, t, _ = ortam
    (t / "in/instagram/x").mkdir(parents=True, exist_ok=True)
    p = hizli.Proje("instagram", "x")
    k = kurgu.bos("instagram")
    kurgu.yaz(p.work, k)
    assert teslim_ozeti(p)["hatalar"] == []
    veri = k.model_dump() if hasattr(k, "model_dump") else dict(k)
    veri["klipler"].append({"id": "s1", "iz": "V2", "bas": 0, "sure": 2, "tur": "sahne", "sahne": {"layout": "split", "kind": "text", "bg": "saydam", "lines": [{"t": "a"}]}})
    kurgu.yaz(p.work, kurgu.Kurgu.model_validate(veri))
    assert any("saydam" in h for h in c.get("/api/teslim/instagram/x").json()["hatalar"])
