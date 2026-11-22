"""Faz 2 motion grafik: shot görsel bağlama, tür denetimi, saydam pano kodlayıcısı, AI edit motion kataloğu (ADR 0031)."""
import json
from pathlib import Path

import pytest

from vedit import aiedit, kurgu, pano, paths
from vedit.hizli import Proje
from vedit.schemas import Kurgu


@pytest.fixture
def p(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "OUTPUTS", tmp_path / "out")
    monkeypatch.setattr(paths, "INPUTS", tmp_path / "in")
    monkeypatch.setattr(kurgu.ff, "probe", lambda f: {"video": {"width": 640, "height": 360}})
    pr = Proje("instagram", "x")
    pr.girdi.mkdir(parents=True)
    (pr.girdi / "5.png").write_bytes(b"png")
    (pr.work / "public").mkdir(parents=True)
    (pr.work / "public" / "s.mp4").write_bytes(b"v")
    return pr


def kur(*klipler) -> Kurgu:
    return Kurgu.model_validate({
        "kaynaklar": {"V01": {"yol": "public:s.mp4", "sure": 20}, "G5": {"yol": "inputs:5.png", "sure": 0}},
        "izler": [{"id": "V2", "tur": "video"}, {"id": "V1", "tur": "video"}],
        "klipler": [{"id": "c1", "iz": "V1", "tur": "video", "kaynak": "V01", "bas": 0, "sure": 8}, *klipler],
    })


def test_hazirla_shot_gorselini_inputs_ten_baglar(p):
    sahne = {"layout": "split", "kind": "shot", "img": "inputs:5.png"}
    ic = {"layout": "split", "kind": "stat", "value": 3, "shot": {"img": "G5"}}
    kurgu.yaz(p.work, kur({"id": "s1", "iz": "V2", "tur": "sahne", "bas": 0, "sure": 2, "sahne": sahne},
                          {"id": "s2", "iz": "V2", "tur": "sahne", "bas": 2, "sure": 2, "sahne": ic}))
    r = json.loads(kurgu.hazirla(p).read_text(encoding="utf-8"))
    s = {c["id"]: c["sahne"] for c in r["klipler"] if c["tur"] == "sahne"}
    assert s["s1"]["img"] == "shot/5.png" and s["s1"]["iw"] == 640 and s["s1"]["ih"] == 360
    assert s["s1"]["focus"] == {"x": 0, "y": 0, "w": 640}, "odaksız shot SplitReel'de düşerdi"
    assert s["s2"]["shot"]["img"] == "shot/5.png", "kaynak kimliği de çözülür"
    assert (p.work / "public" / "shot" / "5.png").samefile(p.girdi / "5.png")
    assert kurgu.oku(p.work).klipler[1].sahne["img"] == "inputs:5.png", "kurgu.json değişmez, yalnız render kopyası"


def test_denetle_motion_mesajlari(p):
    k = kur({"id": "s1", "iz": "V2", "tur": "sahne", "bas": 0, "sure": 2, "sahne": {"layout": "split", "kind": "pasta"}},
            {"id": "s2", "iz": "V2", "tur": "sahne", "bas": 2, "sure": 2, "sahne": {"layout": "split", "kind": "shot", "img": "inputs:yok.png", "bg": "saydam"}},
            {"id": "m1", "iz": "V2", "tur": "metin", "bas": 4, "sure": 1, "metin": "a", "metin_stil": {"tip": "zipla"}},
            {"id": "m2", "iz": "V2", "tur": "metin", "bas": 5, "sure": 1, "metin": "a", "metin_stil": {"tip": "vurgu", "bicim": "yildiz"}},
            {"id": "m3", "iz": "V2", "tur": "metin", "bas": 6, "sure": 1, "metin": "a", "metin_stil": {"tip": "sayac", "deger": "çok"}})
    h = "\n".join(kurgu.denetle(p, k))
    assert "s1: bilinmeyen sahne türü 'pasta'" in h
    assert "s2: sahne görseli: görsel dosyası yok: inputs:yok.png" in h
    assert "s2: saydam zemin yalnız tam ekran" in h
    assert "m1: bilinmeyen metin grafik türü 'zipla'" in h
    assert "m2: vurgu için kutu" in h and "m2: vurgu biçimi 'yildiz' geçersiz" in h
    assert "m3: sayaç için sayı" in h


def test_denetle_gecerli_motion_temiz(p):
    k = kur({"id": "m1", "iz": "V2", "tur": "metin", "bas": 0, "sure": 2, "metin": "Ad\nUnvan", "metin_stil": {"tip": "altbant"}},
            {"id": "g1", "iz": "V2", "tur": "gorsel", "kaynak": "G5", "bas": 2, "sure": 2,
             "metin_stil": {"tip": "vurgu", "bicim": "daire", "kutu": {"x": 0.1, "y": 0.1, "w": 0.2, "h": 0.1}}},
            {"id": "s1", "iz": "V2", "tur": "sahne", "bas": 4, "sure": 2, "sahne": {"layout": "full", "bg": "saydam", "kind": "steps", "items": []}})
    assert kurgu.denetle(p, k) == []


def test_pano_webm_saydam_kodlayici():
    w = pano.kodlayici(Path("a.webm"))
    assert w[w.index("-c:v") + 1] == "libvpx-vp9" and w[w.index("-pix_fmt") + 1] == "yuva420p"
    assert pano.kodlayici(Path("a.mp4"))[1] == "libx264", "mp4 davranışı aynı"


def test_eski_kurgu_aynen_yuklenir():
    f = paths.ROOT / "Projeler/outputs/instagram/avatar-reel/work/edit/kurgu.json"
    if not f.exists():
        pytest.skip("örnek proje yok")
    k = Kurgu.model_validate_json(f.read_text(encoding="utf-8"))
    assert all(not kurgu._motion_hatalari(c) for c in k.klipler)


def test_ai_edit_motion_katalogu_manifestten(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "LIBRARY", tmp_path / "library")
    monkeypatch.setattr(paths, "ROOT", tmp_path)
    m = tmp_path / "library" / "motion"
    (m / "custom" / "ok").mkdir(parents=True)
    (m / "custom" / "ok" / "ok.webm").write_bytes(b"w")
    girdi = {"id": "ok", "file": "library/motion/custom/ok/ok.webm", "kind": "overlay", "duration_s": 2, "width": 1080, "height": 1080, "alpha": True, "license": "project-made", "title": "Ok"}
    (m / "ok.webm").write_bytes(b"w")
    gecis = {**girdi, "kind": "transition", "file": "library/motion/ok.webm"}
    (m / "manifest.json").write_text(json.dumps({"entries": [
        girdi, {**girdi, "id": "dosyasiz", "file": "library/motion/yok.webm"},
        {**gecis, "id": "g-dikey", "width": 1080, "height": 1920}, {**gecis, "id": "g-yatay", "width": 1920, "height": 1080}]}), encoding="utf-8")
    metin = aiedit._motion_katalogu((1080, 1920))
    # ADR 0036: kendi klasöründeki kaydın yolu kalıptan okunur, başka yerdeki dosyanın yolu yazılır
    assert "`ok`" in metin and "library:motion/custom/<kimlik>/<kimlik>.webm" in metin and "library:motion/ok.webm" in metin
    assert "dosyasiz" not in metin, "diskte olmayan dosya önerilmez"
    assert "g-dikey" in metin and "g-yatay" not in metin, "geçiş yalnız sekans oranında listelenir"
    assert "g-yatay" in aiedit._motion_katalogu((1920, 1080)) and "g-yatay" in aiedit._motion_katalogu()


# --- ADR 0036: motion kütüphanesi, şablon, yoğunluk ---
from vedit import motion


@pytest.fixture
def kutuphane(tmp_path, monkeypatch):
    m = tmp_path / "library" / "motion"
    (m / "custom" / "kart").mkdir(parents=True)
    (m / "tema").mkdir()
    (m / "tema" / "acik.css").write_text(":root{--zemin:#fff}", encoding="utf-8")
    (m / "custom" / "kart" / "kart.html").write_text("<html></html>", encoding="utf-8")
    (m / "custom" / "kart" / "meta.json").write_text(json.dumps({
        "title": "Kart", "kind": "lower-third", "sure": 3, "w": 1080, "h": 1920, "tam": True, "ne_zaman": "Alıntıda",
        "param": {"metin": {"vars": "Merhaba", "max": 10}, "deger": {"vars": 5, "min": 0, "max": 9}}}), encoding="utf-8")
    (m / "manifest.json").write_text(json.dumps({"entries": [{"id": "elle", "file": "x.mp4"}, {"id": "kart", "file": "eski"}]}), encoding="utf-8")
    (tmp_path / "library" / "kit.json").write_text('{"locked": []}', encoding="utf-8")
    monkeypatch.setattr(paths, "MOTION_DIR", m)
    monkeypatch.setattr(paths, "LIBRARY", tmp_path / "library")
    cagri = []

    def sahte(html, out, **kw):
        cagri.append(kw)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(b"webm")
    monkeypatch.setattr(motion.hf_motion, "render", sahte)  # ADR 0051: üretim HyperFrames
    monkeypatch.setattr(motion, "_onizleme", lambda *a: None)
    return cagri


def test_motion_kur_manifesti_meta_dan_yazar_digerlerine_dokunmaz(kutuphane):
    motion.kur()
    e = json.loads((paths.MOTION_DIR / "manifest.json").read_text(encoding="utf-8"))["entries"]
    assert [x["id"] for x in e] == ["elle", "kart"] and e[0] == {"id": "elle", "file": "x.mp4"}
    assert e[1]["file"] == "library/motion/custom/kart/kart.webm" and e[1]["param"]["metin"]["max"] == 10 and e[1]["tam"] is True
    assert kutuphane[0]["param"] == {"metin": "Merhaba", "deger": 5}


def test_motion_param_hatalari(kutuphane):
    h = motion.param_hatalari(motion.meta("kart"), {"metin": "çok uzun bir metin", "deger": 12, "yok": 1})
    assert len(h) == 3 and "en çok 10" in h[0] and "0-9" in h[1] and "bilinmeyen" in h[2]
    assert motion.param_hatalari(motion.meta("kart"), {"metin": "kısa", "deger": 3}) == []


def test_sablon_onbellegi_ozetle_calisir(kutuphane, tmp_path):
    a, bilgi = motion.sablon_uret("kart", {"metin": "bir"}, None, tmp_path / "o", sekans=(1920, 1080))
    b, _ = motion.sablon_uret("kart", {"metin": "bir"}, None, tmp_path / "o", sekans=(1920, 1080))
    c, _ = motion.sablon_uret("kart", {"metin": "iki"}, None, tmp_path / "o", sekans=(1920, 1080))
    d, _ = motion.sablon_uret("kart", {"metin": "bir"}, "acik", tmp_path / "o", sekans=(1920, 1080))
    assert a == b and len({a, c, d}) == 3 and len(kutuphane) == 3
    assert bilgi == {"sure": 3, "w": 1920, "h": 1080}  # tam kare şablon sekans boyutunda


def test_motion_bagla_ve_denetle_sablon(p, kutuphane):
    k = kur({"id": "m1", "iz": "V2", "tur": "motion", "bas": 1, "sure": 3, "sablon": {"ad": "kart", "param": {"metin": "selam"}}},
            {"id": "m2", "iz": "V2", "tur": "motion", "bas": 5, "sure": 3, "sablon": {"ad": "yok"}},
            {"id": "m3", "iz": "V2", "tur": "motion", "bas": 9, "sure": 3, "sablon": {"ad": "kart", "param": {"deger": 99}, "tema": "olmayan"}})
    h = kurgu.denetle(p, k)
    assert any("m2" in x and "bilinmeyen motion şablonu" in x for x in h) and any("m3" in x and "0-9" in x for x in h)
    assert any("m3" in x and "tema" in x for x in h) and not any(x.startswith("m1") for x in h)
    k.klipler = [c for c in k.klipler if c.id in ("c1", "m1")]
    assert kurgu.motion_bagla(p, k) is True and kurgu.motion_bagla(p, k) is False
    m1 = next(c for c in k.klipler if c.id == "m1")
    assert k.kaynaklar[m1.kaynak].yol.startswith("public:motion/kart-") and kurgu.denetle(p, k) == []


def test_motion_yogunlugu():
    bos = kur()
    u = kurgu.motion_yogunlugu(bos, 3.0)
    assert len(u) == 2 and "yoğunluğu düşük" in u[0] and "0.0-8.0" in u[1]
    dolu = kur({"id": "t1", "iz": "V2", "tur": "metin", "bas": 2, "sure": 1, "metin": "a", "metin_stil": {"tip": "anahtar"}},
               {"id": "t2", "iz": "V2", "tur": "sahne", "bas": 5, "sure": 2, "sahne": {"layout": "full", "kind": "text", "lines": []}})
    assert kurgu.motion_yogunlugu(dolu, 3.0) == []
