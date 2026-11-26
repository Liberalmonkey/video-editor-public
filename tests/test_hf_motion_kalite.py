"""Modern HyperFrames motion mimarisi (ADR 0062): 24 şablon sözleşmesi, canlı gömme, Tema v2, ses ipuçları, 4-düzen ve Swarm v4."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from vedit import ekip_v3, hazir_efekt, hf_grafik, kurgu, kurgu_kalite, paths, ritim, stil_katalog, tema_denetim, tema_token
from vedit.ekip_sema import Yama
from vedit.schemas import Kurgu

YENI_SABLONLAR = (
    # SaaS UI + Efekt
    "arayuz-imlec-odak",
    "arayuz-pencere-sahne",
    "arayuz-sohbet-akisi",
    "arayuz-kod-farki",
    "arayuz-tost-yigini",
    "efekt-hayalet-iz",
    # İş Akışı + 3B Derinlik
    "akis-ajan-agi",
    "akis-karar-agaci",
    "akis-istek-yanit",
    "derinlik-3b-kart-sahne",
    "derinlik-izometrik-katman",
    "derinlik-kure-baglanti",
    "derinlik-cam-doku-katman",
    # Editoryal Tipografi
    "tipografi-satir-fosfor",
    "tipografi-donen-kelime",
    "tipografi-kod-cozulme",
    "tipografi-bolum-kapsul",
    "tipografi-basamak-sayac",
    # Veri Hikâyeciliği
    "veri-once-sonra-perde",
    "veri-bento-izgara",
    "veri-huni",
    "veri-yaris-cubuk",
    "veri-kontrol-matrisi",
    "veri-zaman-seridi",
)

REFERANS_STILLER = ("saas-izgara", "kod-hud", "beyaz-tahta-pro", "editoryal-belgesel", "urun-lansman")


def test_24_modern_hf_sablonu_mevcut_ve_sozlesmeye_uygun():
    mevcut = set(hf_grafik.adlar())
    eksik = [ad for ad in YENI_SABLONLAR if ad not in mevcut]
    assert eksik == [], f"eksik HF şablonları: {eksik}"
    for ad in YENI_SABLONLAR:
        d = hf_grafik.bul(ad)
        assert d is not None
        html = (d / "index.html").read_text(encoding="utf-8")
        assert tema_denetim.ihlaller(html, kaynak=ad) == [], f"{ad}: tema kilidi ihlali"
        assert kurgu_kalite.hf_determinizm_hatalari(html) == [], f"{ad}: determinizm ihlali"
        o = hf_grafik.olcu(d)
        assert o["w"] > 0 and o["h"] > 0 and o["sure"] >= 1.5
        deg = hf_grafik.degisken_adlari(d)
        assert deg, f"{ad}: data-composition-variables boş"
        cakisan = deg & {"vurgu", "ikincil", "zemin", "yazi", "soluk", "olumlu", "olumsuz", "font", "kose", "cizgi", "kontur", "golge", "doku", "ease", "harf", "izleme", "agirlik"}
        assert not cakisan, f"{ad}: değişken adı tema.css token'ıyla çakışıyor: {cakisan}"
        assert hf_grafik.meta_bilgi(d).get("ne_zaman"), f"{ad}: data-hf-meta.ne_zaman eksik"
        assert 'href="tema.css"' in html
        assert "background: none" in html or "background:none" in html
        sablon = hf_grafik.grafik_kopyasi(ad, "g-test", 1920, 1080)
        assert sablon and "<template>" in sablon and 'id="g-test"' in sablon and 'window.__timelines["g-test"]' in sablon


def test_hf_ses_ipuclari_arti_bir_kare_senkron(tmp_path):
    p = SimpleNamespace(work=tmp_path)
    k = Kurgu.model_validate({
        "sekans": {"w": 1920, "h": 1080, "fps": 30},
        "izler": [{"id": "V2", "tur": "video"}],
        "klipler": [{"id": "c1", "tur": "motion", "iz": "V2", "bas": 2.0, "sure": 4.5,
                     "hf": {"ad": "akis-ajan-agi", "param": {}}}],
    })
    olaylar = hf_grafik.ses_olaylari(p, k)
    assert len(olaylar) >= 3
    ipucu = hf_grafik.ses_ipuclari(hf_grafik.bul("akis-ajan-agi"))
    assert abs(olaylar[0]["t"] - round(2.0 + ipucu[0]["t"] + 1 / 30, 3)) < 1e-6


def test_canli_hf_motion_bagla_webm_atlar(tmp_path):
    p = SimpleNamespace(work=tmp_path, studyo="instagram")
    k = Kurgu.model_validate({
        "sekans": {"w": 1920, "h": 1080, "fps": 30},
        "izler": [{"id": "V2", "tur": "video"}],
        "klipler": [{"id": "c1", "tur": "motion", "iz": "V2", "bas": 0.0, "sure": 4.0,
                     "hf": {"ad": "veri-bento-izgara", "param": {"odakIndeks": 1}}}],
    })
    assert kurgu.motion_bagla(p, k, canli_hf=True) is False
    assert k.klipler[0].kaynak is None


def test_tema_v2_tokenlari_ve_piksel_uyumu():
    t = tema_token.oku("saas-izgara")
    assert t is not None
    css = (paths.MOTION_DIR / "tema" / "saas-izgara.css").read_text(encoding="utf-8")
    for var_ad in ("--vurgu-rgb:", "--yuzey-cam:", "--kenar-ince:", "--yukselti-golge:", "--izgara-desen:", "--ease-enter:", "--ease-exit:"):
        assert var_ad in css
    piksel_css = (paths.MOTION_DIR / "tema" / "piksel-8bit.css").read_text(encoding="utf-8")
    assert "gradient" not in piksel_css and "blur" not in piksel_css


def test_referans_stiller_ve_optik_gecisler_ve_kamera():
    assert stil_katalog.dogrula() == []
    assert tema_token.eksik_temalar() == []
    for sid in REFERANS_STILLER:
        assert stil_katalog.bul(sid)["id"] == sid
    kat = hazir_efekt.katalog()
    assert "ekran_odak" in kat and "dunya_kaydir" in kat
    for g in ("tikla_iris", "buton_zoom", "kart_dunyaya", "bulanik_takas", "dip_kesim"):
        assert g in kurgu.ORTA_GECIS


def test_bpm_izgara_ve_kalite_kapilari():
    izg = ritim.bpm_izgara(120, 2.0, fps=30)
    assert izg == [0.0, 0.5, 1.0, 1.5, 2.0]
    assert ritim.en_yakin_vurus(0.47, izg) == 0.5

    k = Kurgu.model_validate({
        "sekans": {"w": 1920, "h": 1080, "fps": 30},
        "kaynaklar": {"v1": {"yol": "inputs:a.mp4", "sure": 20.0}},
        "izler": [{"id": "V1", "tur": "video"}, {"id": "V2", "tur": "video"}],
        "klipler": [
            {"id": "s1", "tur": "video", "iz": "V1", "bas": 0.0, "sure": 10.0, "kaynak": "v1", "konusmaci": True},
            {"id": "m1", "tur": "motion", "iz": "V2", "bas": 1.0, "sure": 2.0, "hf": {"ad": "veri-bento-izgara"}},
            {"id": "m2", "tur": "motion", "iz": "V2", "bas": 3.0, "sure": 2.0, "hf": {"ad": "veri-bento-izgara"}},
            {"id": "m3", "tur": "motion", "iz": "V2", "bas": 5.0, "sure": 2.0, "hf": {"ad": "akis-ajan-agi"}},
        ],
    })
    uy = kurgu_kalite.uyarilar(k)
    kodlar = {u["kod"] for u in uy}
    assert "MOTION_ART_ARDA" in kodlar
    assert "YUZ_USTU_KART" in kodlar


def test_swarm_v4_determinizm_kapisi():
    kirli = Yama(hf={"bozuk": '<div data-composition-id="main"><script>const x = Math.random();</script></div>'})
    h = ekip_v3.hf_hatalari("E2", kirli)
    assert any("determinizm" in x for x in h)


def test_canli_gommede_kok_sorgusu_klibe_cevrilir():
    """Spec hf-canli-gomme-ve-dikey-duzen (A): `getElementById("root")` ve `__HF_PARAM.main` canlı gömmede klibe döner."""
    from vedit import hf_grafik
    js = ('const a = document.getElementById("root"); const b = document.querySelector(\'#root\');'
          ' const p = window.__HF_PARAM.main || window.__HF_PARAM["main"];')
    out = hf_grafik.kok_sorgusu_cevir(js, "hf_k1")
    assert "getElementById" not in out and "#root" not in out and out.count("__kok") == 2
    assert out.count('window.__HF_PARAM["hf_k1"]') == 2 and "main" not in out
    # Kütüphanedeki her kompozisyonun canlı kopyası kök sorgusu taşımaz.
    for ad in hf_grafik.adlar(None):
        kopya = hf_grafik.grafik_kopyasi(ad, "hf_x", 1080, 1920) or ""
        assert not hf_grafik.KOK_SORGU.search(kopya), ad


def test_uret_sekans_boyutunu_ezer():
    from vedit import hf_grafik
    html = '<div id="root" data-composition-id="main" data-width="1920" data-height="1080" data-duration="2"><i data-width="5"></i></div>'
    out = hf_grafik.boyut_ez(html, 1080, 1920)
    assert 'data-width="1080" data-height="1920"' in out and 'data-width="5"' in out, "yalnız kök öğe değişir"


def test_canli_gomme_yalniz_ayni_yonde(tmp_path):
    """Spec hf-canli-gomme-ve-dikey-duzen: 16:9 kompozisyon 9:16 sekansta canlı gömülmez (WebM'i sekans boyutunda gelir)."""
    from vedit import hf_grafik
    d = tmp_path / "x"
    d.mkdir()
    (d / "index.html").write_text('<div id="root" data-composition-id="main" data-width="1920" data-height="1080" data-duration="2"></div>',
                                  encoding="utf-8")
    assert hf_grafik.ayni_yon(d, (1920, 1080)) and not hf_grafik.ayni_yon(d, (1080, 1920))
    # Canlı kopyada bileşenin kök kuralını ezen kaplama kuralı stillerden sonra gelir.
    kopya = hf_grafik.grafik_kopyasi("kamera-crash-zoom", "hf_k", 1920, 1080) or ""
    assert kopya.rindex("height:100% !important") > kopya.index("container-type")


def test_yatay_kompozisyonun_dikey_kurali_var():
    """Spec hf-canli-gomme-ve-dikey-duzen (E): yeni 16:9 kompozisyon dikey kuralı olmadan ya da `yalniz_yatay` demeden girmez."""
    import re
    from vedit import hf_grafik
    dikey = re.compile(r"max-aspect-ratio|is-portrait|isPortrait|dikey|portrait|ch\s*>\s*cw|h\s*>\s*w")
    eksik = []
    for ad in hf_grafik.adlar(None):
        d = hf_grafik.bul(ad, None)
        o = hf_grafik.olcu(d)
        if o["w"] > o["h"] and not dikey.search((d / "index.html").read_text(encoding="utf-8")) \
                and not hf_grafik.meta_bilgi(d).get("yalniz_yatay"):
            eksik.append(ad)
    assert not eksik, f"dikey kuralı yok: {eksik}"
