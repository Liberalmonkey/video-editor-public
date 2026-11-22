"""İkonda yalnız ikonun kendisi boyanır: arka disk, halka, rozet ya da kutu yok (ADR 0043, görev B).

Her ikon iki kez çizilir: normal (tema, kontur ve gölge filtresiyle) ve maske (filtre kapalı, `.ikon` dışı gizli). Normal
karede alfası 0'dan büyük her piksel, maskenin kontur + gölge payı kadar genişletilmiş alanında kalmalı. Ayrıca kaynakta
arka şekil sınıfı (disk, halka, rozet) ve büyük dolu daire aranır.
"""
import io
import re

import pytest
from PIL import Image, ImageFilter

from vedit import motion

IKONLAR = sorted(k for k in motion.kimlikler() if k.startswith("ikon-")) + ["onay-tik"]
ANLAR = (0.2, 0.55, 0.95, 1.3)
PAY = 36  # px: dış kontur (5) + gölge bulanıklığı ve kayması (~30)
MASKE_CSS = (".ikon{filter:none!important} svg>:not(defs):not(.ikon){display:none!important}"
             ":root{--ikon-golge:transparent}")


def _alfa(png: bytes) -> Image.Image:
    return Image.open(io.BytesIO(png)).convert("RGBA").getchannel("A")


def _genislet(a: Image.Image, pay: int) -> Image.Image:
    k = 4
    kucuk = a.point(lambda v: 255 if v else 0).resize((a.width // k, a.height // k), Image.BOX).point(lambda v: 255 if v else 0)
    n = 2 * (pay // k) + 1
    return kucuk.filter(ImageFilter.MaxFilter(n)).resize(a.size, Image.NEAREST)


@pytest.mark.parametrize("kimlik", IKONLAR)
def test_kaynakta_arka_sekil_yok(kimlik):
    html = (motion.kok() / kimlik / f"{kimlik}.html").read_text(encoding="utf-8")
    assert not re.search(r'class="[^"]*\b(disk|halka|rozet|badge)\b', html), "arka şekil sınıfı"
    assert 'class="ikon"' in html, "çizim .ikon grubunda olmalı"
    for r in re.findall(r'<circle class="[^"]*\bd2?\b[^"]*"[^>]*\br="(\d+)"', html):
        assert int(r) < 120, f"büyük dolu daire (r={r}) arka şekil sayılır"


@pytest.fixture(scope="module")
def tarayici():
    sync = pytest.importorskip("playwright.sync_api")
    with sync.sync_playwright() as p:
        yield p


@pytest.mark.parametrize("kimlik", IKONLAR)
def test_ikon_disinda_alfa_sifir(tarayici, kimlik):
    from vedit import pano
    html = motion.kok() / kimlik / f"{kimlik}.html"
    css = motion.tema_yolu("varsayilan")
    b, pg = pano.ac(tarayici, html, 1080, 1080, css)
    pg.add_style_tag(content=pano.SAYDAM_CSS)
    try:
        for t in ANLAR:
            pg.evaluate(pano.SEEK, t)
            normal = _alfa(pg.screenshot(type="png", omit_background=True))
            st = pg.add_style_tag(content=MASKE_CSS)
            pg.evaluate(pano.SEEK, t)
            maske = _alfa(pg.screenshot(type="png", omit_background=True))
            st.evaluate("e => e.remove()")
            if not maske.getbbox():
                continue  # o anda ikon görünmüyor (giriş öncesi ya da çıkış sonrası)
            disari = Image.composite(normal, Image.new("L", normal.size, 0), _genislet(maske, PAY).point(lambda v: 0 if v else 255))
            assert disari.getbbox() is None, f"{kimlik} t={t}: ikon şeklinin dışında boyalı piksel var {disari.getbbox()}"
    finally:
        b.close()
