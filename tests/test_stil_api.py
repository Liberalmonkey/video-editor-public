"""Stile özel varlık deposu, seçki, temalı native indirme, .zip stil paketi ve /dosya/.../stil/... API testleri."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from vedit import hizli, kurgu, native_motion, paths, stil, stil_varlik
from vedit.schemas import Kurgu
from vedit.studio import app as studio_app
from vedit.studio.app import create_app

HOST = "127.0.0.1:8765"
ORIGIN = {"origin": f"http://{HOST}"}


@pytest.fixture
def ortam(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "STUDIOS", tmp_path / "studios")
    monkeypatch.setattr(paths, "REFERENCES", tmp_path / "refs")
    monkeypatch.setattr(paths, "INPUTS", tmp_path / "inputs")
    monkeypatch.setattr(paths, "OUTPUTS", tmp_path / "outputs")
    for s in ("instagram", "ugc", "youtube-animasyon"):
        d = tmp_path / "studios" / s
        d.mkdir(parents=True, exist_ok=True)
        (d / "studio.yaml").write_text("style: varsayilan\n", encoding="utf-8")
        stil.kaydet(s, "stil-a", "# Stil A\n")
        stil.kaydet(s, "stil-b", "# Stil B\n")
    c = TestClient(create_app("t0k", izinli_hostlar={HOST}), base_url=f"http://{HOST}", follow_redirects=False)
    c.get("/?token=t0k")
    return c, tmp_path


def test_varlik_yukle_listele_onizleme_indir_sil_ve_izolasyon(ortam):
    c, _ = ortam

    # 1) Görsel (SVG) yükle
    svg_icerik = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><circle cx="16" cy="16" r="12"/></svg>'
    r_svg = c.put(
        "/api/stil/instagram/stil-a/varlik",
        params={
            "dosya": "Parlak Rozet.svg",
            "tur": "gorsel",
            "baslik": "Parlak Rozet",
            "ne_zaman": "Fiyat vurgusunda",
            "etiket": "rozet, fiyat",
        },
        content=svg_icerik,
        headers=ORIGIN,
    )
    assert r_svg.status_code == 200
    v_svg = r_svg.json()["varlik"]
    assert v_svg["id"] == "parlak-rozet"
    assert v_svg["kurgu_yolu"].startswith("stil:instagram/stil-a/varliklar/gorsel/parlak-rozet/")
    assert v_svg["onizleme_url"] == "/api/stil/instagram/stil-a/varlik/parlak-rozet/onizleme"
    assert v_svg["indir_url"] == "/api/stil/instagram/stil-a/varlik/parlak-rozet/indir"

    # 2) Karakter (.json) yükle
    kar_icerik = json.dumps({"title": "A Maskotu", "ne_zaman": "Girişte"}).encode("utf-8")
    r_kar = c.put(
        "/api/stil/instagram/stil-a/varlik",
        params={"dosya": "maskot.json", "tur": "karakter", "baslik": "Maskot"},
        content=kar_icerik,
        headers=ORIGIN,
    )
    assert r_kar.status_code == 200
    assert r_kar.json()["varlik"]["yontem"] == "karakter_json"

    # 3) Motion (.webm) yükle
    webm_icerik = b"WEBM-ALFA-DUMMY"
    r_mot = c.put(
        "/api/stil/instagram/stil-a/varlik",
        params={"dosya": "isik.webm", "tur": "motion", "baslik": "Işık", "yontem": "alfa"},
        content=webm_icerik,
        headers=ORIGIN,
    )
    assert r_mot.status_code == 200
    v_mot = r_mot.json()["varlik"]
    assert v_mot["id"] == "isik" and v_mot["yontem"] == "alfa"

    # Geçersiz tür -> 400, uyumsuz uzantı -> 415
    assert c.put(
        "/api/stil/instagram/stil-a/varlik",
        params={"dosya": "a.png", "tur": "gecersiz"},
        content=b"x",
        headers=ORIGIN,
    ).status_code == 400
    assert c.put(
        "/api/stil/instagram/stil-a/varlik",
        params={"dosya": "ses.wav", "tur": "gorsel"},
        content=b"x",
        headers=ORIGIN,
    ).status_code == 415

    # Listeleme ve katalog kontrolü
    r_liste = c.get("/api/stil/instagram/stil-a/varliklar")
    assert r_liste.status_code == 200
    veri = r_liste.json()
    yuklenen_idler = [x["id"] for x in veri["depo"]["yuklenenler"]]
    assert yuklenen_idler == ["parlak-rozet", "maskot", "isik"]
    assert all("kurgu_yolu" in x and "onizleme_url" in x and "indir_url" in x for x in veri["depo"]["yuklenenler"])
    assert len(veri["katalog"]["native"]) > 0
    assert isinstance(veri["katalog"]["karakterler"], list)
    assert isinstance(veri["katalog"]["motionlar"], list)

    # Tam stil izolasyonu: stil-a'ya yüklenen hiçbir varlık stil-b'de görünmez!
    r_liste_b = c.get("/api/stil/instagram/stil-b/varliklar")
    assert r_liste_b.status_code == 200
    assert r_liste_b.json()["depo"]["yuklenenler"] == []
    assert c.get("/api/stil/instagram/stil-b/varlik/parlak-rozet/onizleme").status_code == 404

    # Önizleme (SVG için Content-Security-Policy: sandbox ve Cache-Control: no-cache)
    r_oniz = c.get(v_svg["onizleme_url"])
    assert r_oniz.status_code == 200 and r_oniz.content == svg_icerik
    assert r_oniz.headers.get("cache-control") == "no-cache"
    assert r_oniz.headers.get("content-security-policy") == "sandbox"

    # İndirme (Content-Disposition: attachment + stil-id dosya adı)
    r_ind = c.get(v_mot["indir_url"], params={"bicim": "orijinal"})
    assert r_ind.status_code == 200 and r_ind.content == webm_icerik
    cd = r_ind.headers.get("content-disposition", "")
    assert "attachment" in cd and "stil-a-isik.webm" in cd
    assert r_ind.headers.get("x-content-type-options") == "nosniff"
    assert c.get(v_mot["indir_url"], params={"bicim": "gecersiz"}).status_code == 400

    # Silme
    r_sil = c.delete("/api/stil/instagram/stil-a/varlik/parlak-rozet", headers=ORIGIN)
    assert r_sil.status_code == 200 and r_sil.json()["silinen"]["id"] == "parlak-rozet"
    assert c.delete("/api/stil/instagram/stil-a/varlik/parlak-rozet", headers=ORIGIN).status_code == 404
    assert c.get(v_svg["onizleme_url"]).status_code == 404


def test_secki_kaydetme_ve_dogrulama(ortam):
    c, _ = ortam
    tum_native = sorted(native_motion.kayitlar())
    assert len(tum_native) >= 2
    secilen = [tum_native[0], tum_native[1]]

    r = c.put(
        "/api/stil/instagram/stil-a/secki",
        json={
            "secili_native": secilen,
            "secili_kutuphane": ["karakter: anlatimci"],
            "yalniz_bunlar": True,
        },
        headers=ORIGIN,
    )
    assert r.status_code == 200
    depo = r.json()["depo"]
    assert depo["secili_native"] == secilen
    assert depo["secili_kutuphane"] == ["karakter: anlatimci"]
    assert depo["yalniz_bunlar"] is True

    # Bilinmeyen native bileşen 422 döner
    r_hatali = c.put(
        "/api/stil/instagram/stil-a/secki",
        json={"secili_native": ["olmayan/bilesen"]},
        headers=ORIGIN,
    )
    assert r_hatali.status_code == 422


def test_referans_indir_ve_paket_zip_dongusu(ortam):
    c, _ = ortam

    # Referans yükle ve indir
    r_ref = c.put(
        "/api/stil/instagram/stil-a/referans",
        params={"dosya": "ornek-kare.png"},
        content=b"PNG-REF-VERI",
        headers=ORIGIN,
    )
    assert r_ref.status_code == 200

    r_ref_indir = c.get("/api/stil/instagram/stil-a/referans/indir", params={"dosya": "ornek-kare.png"})
    assert r_ref_indir.status_code == 200 and r_ref_indir.content == b"PNG-REF-VERI"
    assert "attachment" in r_ref_indir.headers.get("content-disposition", "")
    assert c.get("/api/stil/instagram/stil-a/referans/indir", params={"dosya": "../gizli.png"}).status_code == 404

    # Stile özel bir varlık yükle
    c.put(
        "/api/stil/instagram/stil-a/varlik",
        params={"dosya": "parlama.webm", "tur": "motion", "baslik": "Parlama", "yontem": "alfa"},
        content=b"WEBM-PAKET",
        headers=ORIGIN,
    )

    # .zip paketi indir
    r_zip = c.get("/api/stil/instagram/stil-a/paket.zip")
    assert r_zip.status_code == 200
    assert r_zip.headers.get("content-type") == "application/zip"
    assert "instagram-stil-a.zip" in r_zip.headers.get("content-disposition", "")
    zip_bayt = r_zip.content
    assert len(zip_bayt) > 100

    # Başka bir isimle geri yükle ve varlıkların korunduğunu doğrula
    r_yukle = c.put(
        "/api/stil/instagram/paket-yukle",
        params={"dosya": "stil-a.zip", "yeni_ad": "klon-stil"},
        content=zip_bayt,
        headers=ORIGIN,
    )
    assert r_yukle.status_code == 200
    sonuc = r_yukle.json()
    assert sonuc["tamam"] is True and sonuc["ad"] == "klon-stil" and sonuc["varlik_sayisi"] == 1

    # Aynı isimle uzerine_yaz=False iken 409 döner
    r_cakis = c.put(
        "/api/stil/instagram/paket-yukle",
        params={"dosya": "stil-a.zip", "yeni_ad": "klon-stil", "uzerine_yaz": False},
        content=zip_bayt,
        headers=ORIGIN,
    )
    assert r_cakis.status_code == 409

    # Klonlanan stilin varlıkları ve referansı tam korunmuş olmalı
    r_klon_varliklar = c.get("/api/stil/instagram/klon-stil/varliklar")
    assert r_klon_varliklar.status_code == 200
    klon_yuklenenler = r_klon_varliklar.json()["depo"]["yuklenenler"]
    assert len(klon_yuklenenler) == 1 and klon_yuklenenler[0]["id"] == "parlama"
    assert c.get("/api/stil/instagram/klon-stil/varlik/parlama/indir").content == b"WEBM-PAKET"
    assert c.get("/api/stil/instagram/klon-stil/referans/indir", params={"dosya": "ornek-kare.png"}).content == b"PNG-REF-VERI"


def test_native_indir_uc_noktasi(ortam, tmp_path, monkeypatch):
    c, _ = ortam

    # Geçersiz en_boy -> 400
    r_gecersiz = c.post(
        "/api/stil/instagram/stil-a/native-indir",
        json={"ad": "kart/alt-bant", "en_boy": "4:3"},
        headers=ORIGIN,
    )
    assert r_gecersiz.status_code == 400

    sahte_webm = tmp_path / "render.webm"
    sahte_webm.write_bytes(b"VP9-ALPHA-WEBM")
    cagrilar = []

    def sahte_disa_aktar(studyo, ad, bilesen_ad, *, param=None, en_boy="1:1", sure=None):
        cagrilar.append((studyo, ad, bilesen_ad, param, en_boy, sure))
        return sahte_webm

    monkeypatch.setattr(stil_varlik, "native_disa_aktar", sahte_disa_aktar)
    r_ok = c.post(
        "/api/stil/instagram/stil-a/native-indir",
        json={"ad": "kart/alt-bant", "param": {"baslik": "Test"}, "en_boy": "9:16", "sure": 2.5},
        headers=ORIGIN,
    )
    assert r_ok.status_code == 200
    assert r_ok.content == b"VP9-ALPHA-WEBM"
    assert r_ok.headers["content-type"].startswith("video/webm")
    assert "stil-a-kart-alt-bant.webm" in r_ok.headers.get("content-disposition", "")
    assert cagrilar == [("instagram", "stil-a", "kart/alt-bant", {"baslik": "Test"}, "9:16", 2.5)]


def test_dosya_stil_koku_erisim_proxy_korumasi_ve_path_traversal_reddi(ortam, monkeypatch):
    c, t = ortam
    (t / "studios" / "gizli.txt").write_text("cok-gizli", encoding="utf-8")

    p = hizli.Proje("instagram", "p1")
    p.girdi.mkdir(parents=True, exist_ok=True)

    r_mot = c.put(
        "/api/stil/instagram/stil-a/varlik",
        params={"dosya": "parlama.webm", "tur": "motion", "baslik": "Parlama", "yontem": "alfa"},
        content=b"STIL-WEBM-ALFA",
        headers=ORIGIN,
    )
    v = r_mot.json()["varlik"]
    kurgu_yolu = v["kurgu_yolu"]  # stil:instagram/stil-a/varliklar/motion/parlama/parlama.webm

    k = Kurgu.model_validate({
        "kaynaklar": {"S1": {"yol": kurgu_yolu, "sure": 2.0, "ses": False}},
        "izler": [{"id": "V1", "tur": "video"}],
        "klipler": [{"id": "c1", "iz": "V1", "tur": "video", "kaynak": "S1", "bas": 0, "sure": 2.0}],
    })

    # medya_eslemesi stil: kaynağını ASLA H.264 proxy'ye çevirmez ve /dosya/.../stil/... adresi üretir
    baslayan_proxyler = []
    monkeypatch.setattr(
        studio_app.threading,
        "Thread",
        lambda target, args, daemon: baslayan_proxyler.append(args) or type("T", (), {"start": lambda s: None})(),
    )
    es = studio_app.medya_eslemesi(p, k)
    assert es["S1"].startswith("/dosya/instagram/p1/stil/instagram/stil-a/varliklar/motion/parlama/")
    assert baslayan_proxyler == [], "stil: kökü asla H.264 proxy'ye çevrilmemeli"

    # Hem kurgu_yolu biçimi (/dosya/.../stil/instagram/stil-a/...) hem STUDIOS göreli biçim çalışır
    r_dosya1 = c.get(es["S1"])
    assert r_dosya1.status_code == 200 and r_dosya1.content == b"STIL-WEBM-ALFA"

    r_dosya2 = c.get(f"/dosya/instagram/p1/stil/instagram/styles/stil-a/{v['dosya']}")
    assert r_dosya2.status_code == 200 and r_dosya2.content == b"STIL-WEBM-ALFA"

    # Path traversal (..) saldırıları reddedilir
    for saldiri in (
        "/dosya/instagram/p1/stil/..%2Fgizli.txt",
        "/dosya/instagram/p1/stil/instagram/stil-a/..%2F..%2F..%2Fgizli.txt",
        "/dosya/instagram/p1/stil/instagram/styles/stil-a/..%2F..%2F..%2Fgizli.txt",
    ):
        r_saldiri = c.get(saldiri)
        assert r_saldiri.status_code != 200 or b"cok-gizli" not in r_saldiri.content
