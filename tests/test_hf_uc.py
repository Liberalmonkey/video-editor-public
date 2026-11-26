"""GSAP eklentileri, three.js çekirdeği (uc.js) ve yeni şablonlar (ADR 0063)."""

from __future__ import annotations

import re

import pytest

from vedit import hf_grafik, kurgu_kalite, paths, stil_katalog, tema_denetim
from vedit.schemas import Kurgu

UC_SABLONLAR = (
    "uc-logo-ekstrude", "uc-urun-dalis", "uc-parcacik-kelime", "uc-kure-ag", "uc-veri-sutun",
    "uc-cam-kart", "uc-dalga-zemin", "uc-patlatilmis-katman", "uc-portal-gecis", "uc-sonsuz-tunel",
)
GSAP_SABLONLAR = (
    "tipografi-maske-acilis", "tipografi-kontur-dolum", "tipografi-kelime-rolesi", "tipografi-on-kelime-zoom",
    "tipografi-karisik-cozum", "gecis-cizgi-tasima", "gecis-mozaik-cerceve", "gecis-daire-eslesme",
    "kart-deste-dagit", "kamera-crash-zoom", "ritim-hiz-rampasi", "kapanis-logo-kucult",
)
EKLENTILER = ("CustomEase", "SplitText", "DrawSVGPlugin", "MorphSVGPlugin", "MotionPathPlugin", "Physics2DPlugin")


def _html(ad: str) -> str:
    d = hf_grafik.bul(ad)
    assert d is not None, f"{ad} yok"
    return (d / "index.html").read_text(encoding="utf-8")


def test_gsap_paketi_eklentileri_ve_tema_egrilerini_tasir():
    paket = (paths.LIBRARY / "vendor" / "gsap.min.js").read_text(encoding="utf-8")
    cekirdek = (paths.LIBRARY / "vendor" / "gsap" / "gsap.min.js").read_text(encoding="utf-8")
    assert paket.startswith(cekirdek[:200]), "paket çekirdekle başlamalı (scripts/gsap_paketle.py)"
    surum = re.search(r"GSAP (\d+\.\d+\.\d+)", cekirdek).group(1)
    for ad in EKLENTILER:
        assert re.search(rf"\b{ad.replace('Plugin', '')}\w* {re.escape(surum)}", paket), f"{ad} {surum} pakette yok"
    for egri in ("giris", "cikis", "vurgu", "oturma"):
        assert f"{egri}:" in paket
    # Tohumsuz rastgele kullanan eklentiler bilerek dışarıda.
    assert "ScrambleText" not in paket and "CustomWiggle" not in paket


def test_uc_paketi_var_ve_kopyaya_girer(tmp_path):
    uc = paths.LIBRARY / "vendor" / "uc.js"
    assert uc.is_file() and "HFUC" in uc.read_text(encoding="utf-8")
    hf_grafik._hazirla(hf_grafik.bul("uc-logo-ekstrude"), tmp_path / "k", None)
    assert (tmp_path / "k" / "uc.js").is_file() and (tmp_path / "k" / "gsap.min.js").is_file()


@pytest.mark.parametrize("ad", UC_SABLONLAR)
def test_uc_sablonu_canli_gomulmez_ve_kurallara_uyar(ad):
    html = _html(ad)
    d = hf_grafik.bul(ad)
    assert not hf_grafik.canli_mi(d)
    assert ad not in hf_grafik.grafik_harita()
    assert 'src="uc.js"' in html and ("HFUC.sur" in html or ".sur(ctx" in html)
    assert tema_denetim.ihlaller(html, kaynak=ad) == []
    assert kurgu_kalite.hf_determinizm_hatalari(html) == []
    meta = hf_grafik.meta_bilgi(d)
    assert meta.get("aile") == "uc" and meta.get("canli") is False and isinstance(meta.get("kart"), dict)


@pytest.mark.parametrize("ad", GSAP_SABLONLAR)
def test_gsap_sablonu_canli_ve_kurallara_uyar(ad):
    html = _html(ad)
    d = hf_grafik.bul(ad)
    assert hf_grafik.canli_mi(d) and "uc.js" not in html
    assert tema_denetim.ihlaller(html, kaynak=ad) == []
    assert kurgu_kalite.hf_determinizm_hatalari(html) == []
    o = hf_grafik.olcu(d)
    assert 0.8 <= o["sure"] <= 6
    assert isinstance(hf_grafik.meta_bilgi(d).get("kart"), dict)


def test_determinizm_kapisi_threejs_saatini_reddeder():
    for kod in ("const c = new THREE.Clock();", "renderer.setAnimationLoop(f);", "const t = performance.now();",
                "gsap.to(el, {scrambleText: 'x'}); ScrambleTextPlugin"):
        html = f'<div data-composition-id="main"></div><script>{kod} window.__timelines = {{}};</script>'
        assert kurgu_kalite.hf_determinizm_hatalari(html), kod
    assert kurgu_kalite.hf_determinizm_hatalari("<script>HFUC.sur(ctx, tl);</script>")


def _kurgu(*uc: tuple[str, float]) -> Kurgu:
    return Kurgu.model_validate({
        "sekans": {"w": 1920, "h": 1080, "fps": 30},
        "kaynaklar": {"v1": {"yol": "inputs:a.mp4", "sure": 60.0}},
        "izler": [{"id": "V1", "tur": "video"}, {"id": "V2", "tur": "video"}],
        "klipler": [{"id": "s1", "tur": "video", "iz": "V1", "bas": 0.0, "sure": 60.0, "kaynak": "v1"}]
        + [{"id": f"u{i}", "tur": "motion", "iz": "V2", "bas": bas, "sure": 3.0, "hf": {"ad": ad}} for i, (ad, bas) in enumerate(uc)],
    })


def test_uc_tavan_ve_art_arda_uyarisi():
    kodlar = {u["kod"] for u in kurgu_kalite.uyarilar(_kurgu(("uc-logo-ekstrude", 1), ("uc-kure-ag", 20), ("uc-veri-sutun", 40)))}
    assert "UC_FAZLA" in kodlar
    kodlar = {u["kod"] for u in kurgu_kalite.uyarilar(_kurgu(("uc-logo-ekstrude", 1), ("uc-kure-ag", 6)))}
    assert "UC_ART_ARDA" in kodlar
    kodlar = {u["kod"] for u in kurgu_kalite.uyarilar(_kurgu(("uc-logo-ekstrude", 1), ("uc-kure-ag", 30)))}
    assert not {"UC_FAZLA", "UC_ART_ARDA"} & kodlar


def test_her_stilin_hareket_kisiligi_var():
    for s in stil_katalog.yukle()["stiller"]:
        assert s.get("motion_kisilik") in stil_katalog.KISILIK, s["id"]
