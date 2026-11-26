"""Tema kilidi denetimi (ADR 0043, 0058): ajanın ürettiği kompozisyon ve parametrede sabit renk ve font reddedilir."""
from pathlib import Path

from vedit import ekip_v3, paths, tema_denetim
from vedit.ekip_sema import Yama

KOMP = ('<div id="__KOK__" data-composition-id="__KOK__" data-width="__W__" data-height="__H__">'
        '<style>#__KOK__{{position:absolute;inset:0;background:none}} .b{{{stil}}}</style></div>')


def test_sabit_renk_ve_font_yakalanir():
    v = tema_denetim.ihlaller(".a{color:#E8B84B} .b{background:rgb(232,184,75)} .c{font-family:'Roboto'} .d{font-family:Inter, sans-serif}")
    assert any("#E8B84B" in x for x in v) and any("rgb(232" in x for x in v)
    assert any("Roboto" in x for x in v) and any("Inter" in x for x in v)


def test_token_ve_notr_serbest():
    metin = (".a{color:var(--vurgu);font-family:var(--font);background:rgba(0,0,0,.45);border-color:#fff}"
             " x = rgba(t.renk.zemin, .9); y = {fontFamily: H.yigin(t.font.baslik)}; z = hsl(0, 0%, 40%)"
             " .k{font-family:inherit} #__KOK__{background:none}")
    assert tema_denetim.ihlaller(metin) == []


def test_kutuphane_kompozisyonlari_temiz():
    """Kütüphane kayıtları sözleşmeye uyar; denetim onlarda yanlış alarm vermez (175 dosyada ölçüldü)."""
    kirli = {str(f): v for f in (paths.LIBRARY / "motion").rglob("*.html")
             if (v := tema_denetim.ihlaller(f.read_text(encoding="utf-8", errors="replace")))}
    assert kirli == {}


def test_param_ihlali():
    assert tema_denetim.param_ihlalleri({"renk": "#ff3300", "metin": "A"}) and not tema_denetim.param_ihlalleri({"renk": "var(--vurgu)"})


def test_kapi_sabit_renkli_kompozisyonu_reddeder():
    temiz = Yama(hf={"baslik": KOMP.format(stil="color:var(--vurgu);font-family:var(--font)")})
    kirli = Yama(hf={"baslik": KOMP.format(stil="color:#12ab34")})
    assert ekip_v3.hf_hatalari("E2", temiz) == []
    h = ekip_v3.hf_hatalari("E2", kirli)
    assert h and "tema kilidi" in h[0] and "var(--vurgu)" in h[0]
    p = Yama(ekle=[{"id": "m1", "iz": "V2", "tur": "motion", "hf": {"ad": "baslik", "param": {"renk": "#ff0000"}}}])
    assert any("tema kilidi" in x for x in ekip_v3.hf_hatalari("E2", p))


def test_tek_ajan_tema_hatalari(tmp_path):
    from types import SimpleNamespace

    from vedit import aiedit, hf_grafik
    p = SimpleNamespace(work=tmp_path)
    f = hf_grafik.proje_kok(tmp_path) / "kart" / "index.html"
    f.parent.mkdir(parents=True)
    f.write_text(KOMP.format(stil="font-family:'Comic Sans MS'"), encoding="utf-8")
    k = SimpleNamespace(klipler=[SimpleNamespace(id="m1", hf={"ad": "kart", "param": {}}, sablon=None)])
    h = aiedit.tema_hatalari(p, k)
    assert len(h) == 1 and "Comic Sans" in h[0]
    f.write_text(KOMP.format(stil="font-family:var(--font)"), encoding="utf-8")
    assert aiedit.tema_hatalari(p, k) == []
    assert Path(f).is_file()
