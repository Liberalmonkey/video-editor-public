"""Stil token'ları: 31 tema, kontrast, font, piksel kabulü, altyazı ve stil dışı renk (ADR 0043)."""
import io
import json
import shutil

import pytest
from PIL import Image

from vedit import kurgu_kalite, motion, pano, paths, stil_katalog, tema_token
from vedit.tema import kontrast


def test_her_katalog_stilinin_kendi_temasi_var():
    assert tema_token.eksik_temalar() == []
    for e in stil_katalog.stiller():
        assert stil_katalog.tema_adi(e) == e["id"]
        assert motion.tema_yolu(e["id"]) is not None


def test_eksik_tema_kontrolu_kirar(tmp_path, monkeypatch):
    tema = tmp_path / "motion" / "tema"
    shutil.copytree(paths.MOTION_DIR / "tema", tema)
    monkeypatch.setattr(paths, "MOTION_DIR", tmp_path / "motion")
    (tema / "piksel-8bit.css").unlink()
    assert any(h.startswith("piksel-8bit:") for h in tema_token.eksik_temalar())


def test_kontrast_ve_font_denetimi_temiz():
    for e in stil_katalog.stiller():
        t = tema_token.karttan(e)
        assert tema_token.denetle(t) == [], e["id"]
        z = tema_token._rgb(t.renk.zemin)
        assert kontrast(tema_token._rgb(t.renk.yazi), z) >= 4.5
        assert kontrast(tema_token._rgb(t.renk.vurgu), z) >= 3.0


def test_turkce_glif_eksik_font_reddedilir(monkeypatch):
    t = tema_token.karttan(stil_katalog.bul("temiz-kurumsal"))
    t.font.baslik = "Yok Boyle Font"
    assert any("kayıtlı değil" in h for h in tema_token.denetle(t))


def test_piksel_8bit_kabul():
    t = tema_token.oku("piksel-8bit")
    assert t.font.baslik == t.font.govde == "Pixelify Sans" and t.altyazi.font == "Pixelify Sans"
    assert t.sekil.kose == 0 and t.sekil.kontur >= 4 and t.sekil.golge == "sert" and t.sekil.doku == "piksel"
    assert t.hareket.easing == "basamak" and t.hareket.adim_fps and t.sekil.piksel > 1
    assert "piksel-cozunme" in t.gecis
    css = (paths.MOTION_DIR / "tema" / "piksel-8bit.css").read_text(encoding="utf-8")
    assert "Montserrat" not in css and "blur" not in css and "gradient" not in css
    assert "crispEdges" in css and "steps(" in css


def test_eski_ad_kanonik_temaya_gider():
    assert motion.tema_yolu("editorial-acik") == motion.tema_yolu("editoryal-acik") is not None
    assert tema_token.oku("editorial-acik").ad == "editoryal-acik"


def test_stilli_altyazi_tokeni():
    for e in stil_katalog.stiller():
        a = tema_token.karttan(e).altyazi
        assert not (a.kutu or a.pop or a.solma), e["id"]
        assert kontrast(tema_token._rgb(a.aktif_renk), tema_token._rgb(a.kontur_renk)) >= 4.5
    v = tema_token.oku("varsayilan").altyazi
    assert (v.font, v.aktif_renk, v.renk, v.kontur_renk) == ("Montserrat", "#FF7A00", "#FFFFFF", "#000000")  # ADR 0014


def test_css_ve_json_ayni_tokeni_tasir():
    t = tema_token.oku("temiz-kurumsal")
    css = (paths.MOTION_DIR / "tema" / "temiz-kurumsal.css").read_text(encoding="utf-8")
    for ad in ("vurgu", "zemin", "yazi", "olumlu"):
        assert f"--{ad}:{getattr(t.renk, ad)}" in css
    assert f"--kose:{t.sekil.kose}px" in css


def test_pikselle_alfayi_ikiye_ayirir():
    im = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    for x in range(10, 50):
        for y in range(10, 50):
            im.putpixel((x, y), (255, 100, 0, 255 if x < 30 else 90))
    b = io.BytesIO()
    im.save(b, "PNG")
    out = Image.open(io.BytesIO(pano.pikselle(b.getvalue(), 4)))
    assert out.size == (64, 64)
    assert set(out.getchannel("A").tobytes()) <= {0, 255}


def test_stil_disi_renk_uyarisi():
    from vedit.schemas import Kurgu
    k = Kurgu.model_validate({"izler": [{"id": "V1", "tur": "video", "ad": "V1"}, {"id": "V2", "tur": "video", "ad": "V2"}],
                              "klipler": [{"id": "m1", "iz": "V2", "bas": 0, "sure": 3, "tur": "metin", "metin": "Merhaba dünya",
                                           "metin_stil": {"tip": "anahtar", "vurgu": "#10B981"}}]})
    t = tema_token.oku("piksel-8bit")
    assert any(u["kod"] == "STIL_DISI_RENK" for u in kurgu_kalite.uyarilar(k, t))
    k.klipler[0].metin_stil["vurgu"] = t.renk.vurgu
    assert not any(u["kod"] == "STIL_DISI_RENK" for u in kurgu_kalite.uyarilar(k, t))


def test_pano_css_ebs_degiskenlerini_ezer():
    css = tema_token.pano_css(tema_token.oku("piksel-8bit"))
    assert "--paper:#000000" in css and "Pixelify Sans" in css and "border-radius:0px" in css


@pytest.mark.parametrize("ad", ["varsayilan", "turuncu"])
def test_kartsiz_temalarin_json_u_var(ad):
    assert json.loads((paths.MOTION_DIR / "tema" / f"{ad}.json").read_text(encoding="utf-8"))["ad"] == ad
