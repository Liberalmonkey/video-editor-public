import json
import subprocess

import numpy as np
import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from vedit import kurgu, paths
from vedit.hizli import Proje
from vedit.schemas import Kurgu
from vedit.studio import gorsel
from vedit.studio.app import create_app

HOST = "127.0.0.1:8765"
ORIGIN = {"origin": f"http://{HOST}"}


@pytest.fixture
def ortam(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "INPUTS", tmp_path / "in")
    monkeypatch.setattr(paths, "OUTPUTS", tmp_path / "out")
    monkeypatch.setattr(paths, "LIBRARY", tmp_path / "lib")
    p = Proje("instagram", "x")
    p.girdi.mkdir(parents=True)
    kurgu.yaz(p.work, Kurgu.model_validate({"izler": [{"id": "V1", "tur": "video"}]}))
    c = TestClient(create_app("t", izinli_hostlar={HOST}), base_url=f"http://{HOST}", follow_redirects=False)
    c.get("/?token=t")
    return c, p


def test_hf_onizleme_native_ve_sahne(ortam):
    # WHY: ADR 0051. Önizleme derleyicisi taşınmış native bileşenleri ve bağlama kopyasını sunucudan alır.
    c, _ = ortam
    hf = paths.LIBRARY / "motion" / "hf" / "ikon-tik"
    hf.mkdir(parents=True)
    (hf / "sahne.html").write_text('<template><div id="__KOK__" data-width="__W__" data-height="__H__"></div></template>', encoding="utf-8")
    sema = {"bilesenler": {"ikon/tik": {"meta": {"ad": "ikon/tik", "giris_sn": 0.35}, "sema": {"properties": {"renk": {"default": "olumlu"}}}}}}
    (paths.LIBRARY / "motion" / "native").mkdir(parents=True)
    (paths.LIBRARY / "motion" / "native" / "sema.json").write_text(json.dumps(sema), encoding="utf-8")
    v = c.get("/api/hf/onizleme").json()
    assert v["native"]["ikon/tik"]["varsayilan"] == {"renk": "olumlu"} and v["oto_hf"] is False
    r = c.get("/hfs/ikon-tik/n-a1/1080x1920.html")
    assert r.status_code == 200 and 'id="n-a1" data-width="1080" data-height="1920"' in r.text
    for kotu in ("/hfs/ikon-tik/n%20a/1080x1920.html", "/hfs/..%2Fx/n-a/1080x1920.html", "/hfs/ikon-tik/n-a/1080.html"):
        r = c.get(kotu)  # yol kaçışı sahne ucuna ulaşmaz (normalleşip arayüze düşebilir); sahne içeriği asla dönmez
        assert r.status_code in (400, 404) or 'id="n-a"' not in r.text
    assert c.get("/hfs/ikon-yok/n-a/1080x1920.html").status_code == 404


def test_yanit_onizleme_bolgelerini_tasir(ortam):
    # WHY: ADR 0045. Önizleme render'la aynı yerleşimi seçsin; native klip yoksa bölge yok (None).
    c, _ = ortam
    v = c.get("/api/kurgu/instagram/x").json()
    assert "bolgeler" in v and v["bolgeler"] is None


def test_etag_terminal_yazimini_yakalar(ortam):
    c, p = ortam
    v = c.get("/api/kurgu/instagram/x").json()
    # rev artmadan dış yazım: agent dosyayı elle değiştirdi
    d = json.loads(kurgu.yol(p.work).read_text(encoding="utf-8"))
    d["klipler"] = [{"id": "dis", "iz": "V1", "tur": "metin", "bas": 0, "sure": 1}]
    kurgu.yol(p.work).write_text(json.dumps(d), encoding="utf-8")
    r = c.put("/api/kurgu/instagram/x", content=json.dumps(v["kurgu"]), headers={**ORIGIN, "if-match": v["etag"]})
    assert r.status_code == 409
    assert kurgu.oku(p.work).klipler[0].id == "dis", "dış yazım ezilmemeli"


def test_kaydet_etag_doner_ve_gecersiz_reddedilir(ortam):
    c, p = ortam
    v = c.get("/api/kurgu/instagram/x").json()
    r = c.put("/api/kurgu/instagram/x", content=json.dumps(v["kurgu"]), headers={**ORIGIN, "if-match": v["etag"]})
    assert r.status_code == 200 and r.json()["rev"] == 1 and r.json()["etag"] == kurgu.etag(p.work)
    kotu = {**v["kurgu"], "klipler": [{"id": "x", "iz": "YOK", "tur": "metin", "bas": 0, "sure": 1}]}
    assert c.put("/api/kurgu/instagram/x", content=json.dumps(kotu), headers={**ORIGIN, "if-match": r.json()["etag"]}).status_code == 422


def test_bozuk_kurgu_sunucuyu_dusurmez(ortam):
    c, p = ortam
    kurgu.yol(p.work).write_text("{bozuk", encoding="utf-8")
    r = c.get("/api/kurgu/instagram/x")
    assert r.status_code == 422 and "geçersiz" in r.json()["detail"]


def test_kaynak_kok_disi(ortam):
    c, _ = ortam
    assert c.post("/api/kaynak/instagram/x", json={"yol": "inputs:../../sir.mp4"}, headers=ORIGIN).status_code == 400
    assert c.post("/api/kaynak/instagram/x", json={"yol": "c:/windows/x.mp4"}, headers=ORIGIN).status_code == 400
    assert c.get("/api/peak/instagram/x", params={"yol": "inputs:../../sir.mp4"}).status_code == 400
    assert c.get("/api/peak/instagram/x", params={"yol": "inputs:yok.wav"}).status_code == 404


def test_kaynak_kelimeleri(ortam):
    _, p = ortam
    t = p.work / "analysis" / "transcript.json"
    t.parent.mkdir(parents=True)
    t.write_text(json.dumps({"files": {"a": {"segments": [{"words": [{"w": "x", "s": 1, "e": 2, "p": 0.9}]}]}}}), encoding="utf-8")
    assert kurgu.kaynak_kelimeleri(p, p.girdi / "a.mp4") == [{"w": "x", "s": 1, "e": 2}]
    assert kurgu.kaynak_kelimeleri(p, p.girdi / "b.mp4") == []


def test_peaks():
    # 8000 Hz'de 160 örnek = 1 pencere: tam ölçek 255'e, sessizlik 0'a gider, artan örnek atılır.
    pcm = np.array([0] * 160 + [32767] + [0] * 159 + [-32768] + [0] * 159 + [5] * 10, dtype=np.int16)
    assert gorsel.peaks(pcm) == [0, 254, 255]
    assert gorsel.peaks(np.array([], dtype=np.int16)) == []


def test_peak_serit_gercek_dosya(ortam, tmp_path):
    c, p = ortam
    v = p.girdi / "v.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc2=s=320x180:r=30:d=3", "-f", "lavfi", "-i", "sine=f=440:d=3",
                    "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(v)], check=True)
    d = c.get("/api/peak/instagram/x", params={"yol": "inputs:v.mp4"}).json()
    assert d["hz"] == 50 and 140 <= len(d["tepe"]) <= 160 and max(d["tepe"]) > 0
    s = c.get("/api/serit/instagram/x", params={"yol": "inputs:v.mp4"}).json()
    assert s["n"] == 3 and s["k"] == 1
    assert c.get(s["url"]).status_code == 200
    b = c.post("/api/kaynak/instagram/x", json={"yol": "inputs:v.mp4"}, headers=ORIGIN).json()
    assert (b["w"], b["ses"]) == (320, True) and 2.9 < b["sure"] < 3.2


def test_kapak_durum_ve_sec(ortam):
    c, p = ortam
    k = p.work / "gorsel" / "kapak" / "instagram"
    k.mkdir(parents=True)
    (k / "kapak-1.jpg").write_bytes(b"x")
    d = c.get("/api/kapak/instagram/x").json()
    a = d["adaylar"][0]
    assert (a["n"], a["yol"], a["aci"], a["yerlesim"], a["olcek"]) == (1, "work/gorsel/kapak/instagram/kapak-1.jpg", None, "ust", 1.0)
    assert len(d["adaylar"]) == 1 and d["secim"] is None and d["yerlesimler"] == ["ust", "alt"]
    assert c.post("/api/kapak/instagram/x/sec", json={"n": 1}, headers=ORIGIN).json() == {"dosya": "kapak-reels.jpg"}
    assert c.post("/api/kapak/instagram/x/sec", json={"n": 7}, headers=ORIGIN).status_code == 422
    assert c.get("/api/kapak/ugc/x").status_code == 422
    # önizleme: zemini olan adayda şablon döner; zeminsiz aday ve platformda olmayan yerleşim reddedilir
    assert c.post("/api/kapak/instagram/x/onizle", json={"n": 1}, headers=ORIGIN).status_code == 422
    (k / "zemin-1.jpg").write_bytes(b"z")
    (k / "kapak-1.json").write_text('{"zemin": "zemin-1.jpg"}', encoding="utf-8")
    r = c.post("/api/kapak/instagram/x/onizle", json={"n": 1, "metin": "A|<b>B</b>", "yerlesim": "alt"}, headers=ORIGIN)
    assert r.status_code == 200 and "&lt;b&gt;B&lt;/b&gt;" in r.json()["html"] and 'data-yerlesim="alt"' in r.json()["html"]
    assert c.post("/api/kapak/instagram/x/onizle", json={"n": 1, "yerlesim": "sol"}, headers=ORIGIN).status_code == 422


def test_kapak_v2_uclari(ortam, tmp_path):
    """ADR 0052: referans yükle/sil, dış görsel yükle, öneri kaydet, master prompt, elle kare; agy çağrılmaz."""
    c, p = ortam
    q = "/api/kapak/instagram/x"
    assert c.put(f"{q}/referans?tur=yuz&dosya=ben.png", content=b"g", headers=ORIGIN).json() == {"ad": "yuz-ben.png"}
    assert c.put(f"{q}/referans?tur=kotu&dosya=a.png", content=b"g", headers=ORIGIN).status_code == 400
    assert c.put(f"{q}/referans?tur=stil&dosya=a.exe", content=b"g", headers=ORIGIN).status_code == 415
    d = c.get(q).json()
    assert d["referanslar"] == [{"tur": "yuz", "ad": "yuz-ben.png", "kok": "outputs", "silinir": True,
                                 "yol": "work/gorsel/kapak/referans/yuz-ben.png"}]
    assert {h["id"] for h in d["hedefler"]} >= {"nano-banana-pro", "nano-banana-21", "midjourney"} and "gorsel_motor" in d
    assert c.delete(f"{q}/referans/yuz-ben.png", headers=ORIGIN).json() == {"tamam": True}
    assert c.delete(f"{q}/referans/yuz-ben.png", headers=ORIGIN).status_code == 404
    assert c.put(f"{q}/ice-al?platform=instagram&dosya=dis.png", content=b"g", headers=ORIGIN).json() == {"ad": "dis.png"}
    assert (p.work / "gorsel" / "kapak" / "instagram" / "disari" / "dis.png").read_bytes() == b"g"
    assert c.put(f"{q}/ice-al?platform=tiktok&dosya=dis.png", content=b"g", headers=ORIGIN).status_code == 400
    assert c.get(f"{q}/master").status_code == 422  # öneri ya da aday yok
    brief = {"sahne": "A desk", "satir1": "A", "satir2": "B", "kalip": "klasik"}
    r = c.post(f"{q}/oneri", json={"platform": "instagram", "fikir": "fikir", "briefler": [brief]}, headers=ORIGIN).json()
    assert r["briefler"][0]["sahne"] == "A desk"
    m = c.get(f"{q}/master?platform=instagram").json()
    assert m["kaynak"] == "öneri" and '"A"' in m["hedefler"]["nano-banana-pro"]["yazili"]["prompt"] and "# Kapak master" in m["md"]
    assert c.get(q).json()["oneri"]["briefler"][0]["govde"].startswith("A desk.")
    assert c.post(f"{q}/kare", json={"video": "inputs:../x.mp4", "t": 1}, headers=ORIGIN).status_code == 422
    subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "color=c=red:s=160x284:d=2", "-pix_fmt", "yuv420p",
                    str(p.girdi / "1.mp4")], check=True)
    r = c.post(f"{q}/kare", json={"video": "inputs:1.mp4", "t": 0.5}, headers=ORIGIN).json()
    assert r == {"n": 7, "yol": "work/gorsel/kapak/kareler/inputs-1.mp4/el-00000500.jpg"}
    d = c.get(f"{q}?video=inputs:1.mp4").json()
    assert d["video"] == "inputs:1.mp4" and d["kareler"][-1] == {"n": 7, "yol": r["yol"], "el": True}
    assert [v["yol"] for v in d["videolar"]] == ["inputs:1.mp4"]


def test_kurgu_okuyan_uclar_kurgu_yokken_ve_bozukken_500_vermez(ortam):
    c, p = ortam
    kurgu.yol(p.work).write_text("{bozuk", encoding="utf-8")
    assert c.get("/api/oneri/instagram/x").status_code == 422
    assert c.post("/api/disa/instagram/x", headers=ORIGIN).status_code == 422
    kurgu.yol(p.work).unlink()
    assert c.get("/api/oneri/instagram/x").status_code == 404
    assert c.post("/api/disa/instagram/x", headers=ORIGIN).status_code == 404
    assert c.post("/api/reframe/instagram/x", json={"klip": "a"}, headers=ORIGIN).status_code == 404


def test_ai_ozet_ve_geri_al(ortam):
    c, p = ortam
    assert c.get("/api/kurgu/instagram/x/ai-ozet").json() is None
    d = kurgu.oku(p.work).model_dump()
    d["klipler"] = [{"id": "ai", "iz": "V1", "tur": "metin", "bas": 0, "sure": 1}]
    kurgu.yaz(p.work, Kurgu.model_validate(d))  # rev 0 geçmişe girer
    (p.work / "edit" / "ai-edit.ozet.json").write_text(json.dumps({"once_rev": 0, "rev": 1, "klip": [0, 1], "sure": [0, 1]}), encoding="utf-8")
    o = c.get("/api/kurgu/instagram/x/ai-ozet").json()
    assert o["geri_alinabilir"] and o["rapor"] == []
    r = c.post("/api/kurgu/instagram/x/geri/0", headers=ORIGIN)
    assert r.status_code == 200 and r.json()["rev"] == 2 and kurgu.oku(p.work).klipler == []
    assert c.post("/api/kurgu/instagram/x/geri/99", headers=ORIGIN).status_code == 404
