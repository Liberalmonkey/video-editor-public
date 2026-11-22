"""Videoya göre motion teması: palet çıkarma, tema sırası, sabit klibin temayla yeniden renklenmesi (ADR 0042)."""
import colorsys
import json

import pytest

from vedit import kurgu, motion, paths, stil, tema
from vedit.hizli import Proje
from vedit.schemas import Kurgu


def _ton(hex_: str) -> float:
    r, g, b = (int(hex_[i:i + 2], 16) / 255 for i in (1, 3, 5))
    return colorsys.rgb_to_hsv(r, g, b)[0] * 360


def test_palet_doygun_rengi_vurgu_yapar_ve_okunur():
    mavi = [((30, 90, 220), 0.3), ((12, 14, 20), 0.5), ((200, 200, 200), 0.2)]
    r = tema.palet_kur(mavi)
    assert 200 <= _ton(r["vurgu"]) <= 240
    hx = lambda h: tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))  # noqa: E731
    assert tema.kontrast(hx(r["vurgu"]), hx(r["zemin"])) >= 3
    assert tema.kontrast(hx(r["yazi"]), hx(r["zemin"])) >= 4.5


def test_soluk_video_turuncuya_dusmez():
    # Yeşil-kahve, düşük doygun çekim (gerçek reel-video ölçümü): karşıt ton seçilir, turuncu bandı atlanır.
    kumeler = [((51, 59, 47), .21), ((32, 36, 30), .16), ((129, 113, 98), .14), ((66, 82, 72), .12),
               ((103, 81, 61), .12), ((15, 18, 15), .11), ((177, 151, 128), .1)]
    r = tema.palet_kur(kumeler)
    for a in ("vurgu", "ikincil"):
        assert not 20 <= _ton(r[a]) <= 45, f"{a} turuncu: {r[a]}"
    mavi_gri = [((60, 70, 90), 1.0)]  # karşıtı turuncu bandına düşen gri-mavi
    assert not 20 <= _ton(tema.palet_kur(mavi_gri)["vurgu"]) <= 45
    assert tema.palet_kur([])["zemin"].startswith("#")


@pytest.fixture
def ortam(tmp_path, monkeypatch):
    lib = tmp_path / "library"
    m = lib / "motion"
    (m / "custom" / "kutu").mkdir(parents=True)
    (m / "custom" / "kutu" / "kutu.html").write_text("<html></html>", encoding="utf-8")
    (m / "custom" / "kutu" / "meta.json").write_text(json.dumps({"title": "Kutu", "kind": "overlay", "sure": 2, "w": 800, "h": 400}),
                                                     encoding="utf-8")
    (m / "custom" / "kutu" / "kutu.webm").write_bytes(b"w")
    (m / "tema").mkdir()
    for t in ("varsayilan", "acik", "anime"):
        (m / "tema" / f"{t}.css").write_text(f":root{{--vurgu:#{abs(hash(t)) % 0xFFFFFF:06X}}}", encoding="utf-8")
    (lib / "kit.json").write_text('{"locked": []}', encoding="utf-8")
    for ad, deger in (("MOTION_DIR", m), ("LIBRARY", lib), ("OUTPUTS", tmp_path / "out"), ("INPUTS", tmp_path / "in"),
                      ("STUDIOS", tmp_path / "studios"), ("REFERENCES", tmp_path / "refs")):
        monkeypatch.setattr(paths, ad, deger)
    cagri = []

    def sahte(html, out, **kw):
        cagri.append(kw["css"])
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(b"webm")
    monkeypatch.setattr(motion.hf_motion, "render", sahte)  # ADR 0051: üretim HyperFrames
    p = Proje("instagram", "x")
    (p.work / "public").mkdir(parents=True)
    (p.work / "public" / "s.mp4").write_bytes(b"v")
    return p, cagri


def test_etkin_tema_sirasi(ortam):
    p, _ = ortam
    assert kurgu.etkin_tema(p, "varsayilan") == "varsayilan"
    css = p.work / "edit" / "motion_tema.css"
    css.parent.mkdir(parents=True)
    css.write_text(":root{--vurgu:#123456}", encoding="utf-8")
    assert kurgu.etkin_tema(p, "varsayilan") == css, "stil yoksa proje teması"
    assert kurgu.etkin_tema(p, "proje") == css
    stil.kaydet("instagram", "anim", "# Anim")
    (stil.klasor("instagram", "anim") / "tokens.json").write_text('{"motion_tema": "anime"}', encoding="utf-8")
    stil.sec(p, "anim")
    assert kurgu.etkin_tema(p, None) == "anime", "seçili stilin teması proje temasından önce gelir"
    assert kurgu.etkin_tema(p, "acik") == "acik", "açık tema her şeyi ezer"


def _kurgu(tema_ad: str) -> Kurgu:
    return Kurgu.model_validate({
        "motion_tema": tema_ad,
        "kaynaklar": {"V01": {"yol": "public:s.mp4", "sure": 20}, "K": {"yol": "library:motion/custom/kutu/kutu.webm", "sure": 2}},
        "izler": [{"id": "V2", "tur": "video"}, {"id": "V1", "tur": "video"}],
        "klipler": [{"id": "c1", "iz": "V1", "tur": "video", "kaynak": "V01", "bas": 0, "sure": 8},
                    {"id": "m1", "iz": "V2", "tur": "motion", "kaynak": "K", "bas": 1, "sure": 2}],
    })


def test_sabit_klip_temayla_yeniden_renklenir_ve_geri_doner(ortam):
    p, cagri = ortam
    k = _kurgu("acik")
    assert kurgu.motion_bagla(p, k) is True
    m1 = k.klipler[1]
    assert k.kaynaklar[m1.kaynak].yol.startswith("public:motion/kutu-") and cagri[-1].name == "acik.css"
    assert kurgu.motion_bagla(p, k) is False, "önbellek: aynı tema yeniden üretilmez"
    k.motion_tema = "varsayilan"
    assert kurgu.motion_bagla(p, k) is True
    assert k.kaynaklar[m1.kaynak].yol == "library:motion/custom/kutu/kutu.webm", "otomatik ve stilsiz: kütüphane dosyası"
    assert len(cagri) == 1 and kurgu.denetle(p, k) == []


def test_kilitli_klip_ve_bilinmeyen_tema(ortam):
    p, cagri = ortam
    (paths.LIBRARY / "kit.json").write_text('{"locked": ["kutu"]}', encoding="utf-8")
    k = _kurgu("acik")
    assert kurgu.motion_bagla(p, k) is False and not cagri
    k.motion_tema = "olmayan"
    assert any("bilinmeyen motion_tema" in h for h in kurgu.denetle(p, k))


def test_tema_cikar_tam_token_yazar(ortam, monkeypatch):
    # WHY: ADR 0051. Proje teması yalnız 5 renk yazıyordu; tema.css'in öteki değişkenleri grafiklerde turuncu yedeğe düşerdi.
    import numpy as np

    from vedit import tema_token
    p, _ = ortam
    p.girdi.mkdir(parents=True, exist_ok=True)
    (p.girdi / "a.mp4").write_bytes(b"v")
    px = np.array([[20, 60, 90]] * 50 + [[40, 200, 220]] * 30 + [[230, 230, 230]] * 20, dtype=float)
    monkeypatch.setattr(tema, "_kareler", lambda f: px)
    css = tema.cikar(p)
    v = css.read_text(encoding="utf-8")
    varsayilan = motion.tema_yolu("varsayilan").read_text(encoding="utf-8")
    import re
    eksik = set(re.findall(r"--([a-z0-9-]+)\s*:", varsayilan)) - set(re.findall(r"--([a-z0-9-]+)\s*:", v))
    assert not eksik, f"proje temasında eksik değişken: {eksik}"
    t = tema_token.oku(css)
    assert css.with_suffix(".json").is_file() and t.renk.vurgu.upper() != "#FF7A00"
