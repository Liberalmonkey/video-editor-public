"""HyperFrames grafik yolu (ADR 0050): kompozisyon bulma, ölçü, önbellek anahtarı, kurgu bağlama ve denetim."""

from pathlib import Path

import pytest

from vedit import ff, hf, hf_grafik, kurgu
from vedit.schemas import Kurgu

HTML = """<!doctype html>
<html lang="tr" data-composition-variables='[{"id":"baslik","type":"string","label":"B","default":"x"}]'>
<head><link rel="stylesheet" href="tema.css"><style>html,body,#root{background:none}</style></head>
<body><div id="root" data-composition-id="main" data-start="0" data-duration="3" data-width="1080" data-height="1920" data-fps="30">
<div data-var-text="baslik">x</div></div></body></html>"""


def _komp(kok: Path, ad: str, html: str = HTML) -> Path:
    d = kok / ad
    d.mkdir(parents=True)
    (d / "index.html").write_text(html, encoding="utf-8")
    return d


@pytest.fixture
def ortam(tmp_path, monkeypatch):
    lib = tmp_path / "lib"
    monkeypatch.setattr(hf_grafik, "KUTUPHANE", lib)
    work = tmp_path / "work"
    return lib, work


def test_proje_kompozisyonu_kutuphaneyi_ezer(ortam):
    lib, work = ortam
    _komp(lib, "bant")
    proje = _komp(hf_grafik.proje_kok(work), "bant")
    assert hf_grafik.bul("bant", work) == proje
    assert hf_grafik.bul("bant") == lib / "bant"
    assert hf_grafik.bul("../kacak", work) is None
    assert hf_grafik.adlar(work) == ["bant"]


def test_olcu_ve_degiskenler(ortam):
    lib, _ = ortam
    d = _komp(lib, "bant")
    assert hf_grafik.olcu(d) == {"w": 1080, "h": 1920, "sure": 3.0}
    assert hf_grafik.degisken_adlari(d) == {"baslik"}
    eksik = _komp(lib, "eksik", HTML.replace(' data-duration="3"', ""))
    with pytest.raises(ValueError):
        hf_grafik.olcu(eksik)


def test_ozet_param_ve_kaynakla_degisir(ortam):
    lib, _ = ortam
    d = _komp(lib, "bant")
    a = hf_grafik.ozet(d, {"baslik": "A"}, "varsayilan")
    assert a == hf_grafik.ozet(d, {"baslik": "A"}, "varsayilan")
    assert a != hf_grafik.ozet(d, {"baslik": "B"}, "varsayilan")
    (d / "index.html").write_text(HTML + " ", encoding="utf-8")
    assert a != hf_grafik.ozet(d, {"baslik": "A"}, "varsayilan")


def test_denetle_bilinmeyen_ve_bildirilmemis_param(ortam):
    lib, work = ortam
    _komp(lib, "bant")
    assert hf_grafik.denetle("bant", {"baslik": "x"}, work) == []
    assert "bildirilmemiş parametre: renk" in hf_grafik.denetle("bant", {"renk": "x"}, work)[0]
    assert "bilinmeyen HyperFrames kompozisyonu" in hf_grafik.denetle("yok", None, work)[0]


def test_uret_render_kopyasina_tema_ve_font_koyar_ve_onbellekler(ortam, monkeypatch):
    lib, work = ortam
    _komp(lib, "bant")
    cagri = []

    def sahte_render(klasor, hedef, *, degiskenler=None, **_):
        assert (klasor / "tema.css").read_text(encoding="utf-8")  # token kopyaya girdi
        assert (klasor / "fonts").is_dir()
        cagri.append(degiskenler)
        hedef.parent.mkdir(parents=True, exist_ok=True)
        hedef.write_bytes(b"webm")
        return hedef

    monkeypatch.setattr(hf, "render_saydam", sahte_render)
    f, bilgi = hf_grafik.uret("bant", {"baslik": "Ş"}, "varsayilan", work, work / "public" / "motion")
    assert f.name.startswith("hf-bant-") and f.suffix == ".webm"
    assert bilgi == {"w": 1080, "h": 1920, "sure": 3.0}
    hf_grafik.uret("bant", {"baslik": "Ş"}, "varsayilan", work, work / "public" / "motion")
    assert cagri == [{"baslik": "Ş"}]  # ikinci çağrı önbellekten
    assert not (lib / "bant" / "tema.css").exists()  # kaynak kompozisyon değişmez


def test_motion_bagla_hf_klibine_kaynak_baglar(ortam, monkeypatch, tmp_path):
    lib, work = ortam
    _komp(lib, "bant")
    hedef = work / "public" / "motion" / "hf-bant-abc.webm"
    monkeypatch.setattr(hf_grafik, "uret", lambda *a, **k: (hedef, {"sure": 3.0, "w": 1080, "h": 1920}))
    monkeypatch.setattr(kurgu, "etkin_tema", lambda p, ad: "varsayilan")

    class P:
        pass

    p = P()
    p.work = work
    k = Kurgu.model_validate({"sekans": {"w": 1080, "h": 1920, "fps": 30}, "izler": [{"id": "V2", "tur": "video"}],
                              "klipler": [{"id": "c1", "tur": "motion", "iz": "V2", "bas": 0, "sure": 3,
                                           "hf": {"ad": "bant", "param": {"baslik": "x"}}}]})
    assert kurgu.motion_bagla(p, k) is True
    c = k.klipler[0]
    assert c.kaynak == "M_hf_bant_abc"
    assert k.kaynaklar[c.kaynak].yol == "public:motion/hf-bant-abc.webm"


def test_alfa_etiketi_buyuk_harfle_de_taninir():
    assert ff._alfa_mi({"tags": {"ALPHA_MODE": "1"}, "pix_fmt": "yuv420p"})
    assert ff._alfa_mi({"tags": {"alpha_mode": "1"}, "pix_fmt": "yuv420p"})
    assert not ff._alfa_mi({"tags": {}, "pix_fmt": "yuv420p"})


def test_timeline_anahtari_koke_eslenir():
    # WHY: ornek-proje 2026-11-27. Kök `gosterge-yak`, timeline `main`: render "data-no-timeline" ile düşüyordu.
    from vedit import hf_grafik
    js = "window.__timelines=window.__timelines||{};window.__timelines['main']=tl;"
    assert 'window.__timelines["gosterge-yak"]=tl' in hf_grafik.timeline_esle(js, "gosterge-yak")
    tek = "window.__timelines['baska']=tl;"
    assert 'window.__timelines["k"]' in hf_grafik.timeline_esle(tek, "k")
    iki = "window.__timelines['a']=x;window.__timelines['b']=y;"
    assert hf_grafik.timeline_esle(iki, "k") == iki
    dogru = 'window.__timelines["k"]=tl;'
    assert hf_grafik.timeline_esle(dogru, "k") == dogru
