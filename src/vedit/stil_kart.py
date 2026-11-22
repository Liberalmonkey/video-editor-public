"""Stil kartı: her stil için sabit örnek set tek görselde; taşma ve kontrast ölçülür (regresyon).

WHY: bkz. wiki/decisions/0043-stile-bagli-tema-tokenlari.md. Stil seçince her katmanın stile uyduğunu tek bakışta görmek
ve bir şablon ya da tema değişince taşma/kontrast bozulmasını yakalamak için. Set: altyazı satırı, alt bant, 3 ikon, ok,
sayaç, çubuk grafik, karşılaştırma, geçiş karesi. Her parça kütüphanedeki gerçek şablondan stilin temasıyla çizilir.
Çıktı `library/stiller/onizleme/<id>/kart.jpg` + `kart.json` (ölçüm).
"""

from __future__ import annotations

import io
import json
from pathlib import Path

from . import motion, paths, tema_token

W, H = 1080, 1920
# (ad, şablon, an oranı, hücre: x, y, w, h). Yerleşim 9:16; hücre içinde parça oranı korunarak sığdırılır.
PARCALAR = [
    ("alt bant", "altbant-konu", 0.55, (40, 250, 1000, 230)),
    ("ikon", "ikon-kalp", 0.7, (60, 500, 300, 300)),
    ("ikon", "ikon-zil", 0.7, (390, 500, 300, 300)),
    ("ikon", "onay-tik", 0.7, (720, 500, 300, 300)),
    ("ok", "ok-ciz", 0.75, (40, 830, 480, 330)),
    ("sayaç", "odometre-sayac", 0.85, (560, 830, 480, 330)),
    ("çubuk grafik", "grafik-cubuk", 0.85, (40, 1190, 480, 400)),
    ("karşılaştırma", "karsilastirma", 0.8, (560, 1190, 480, 400)),
]
GECIS = (40, 1620, 1000, 260)
ALTYAZI = (40, 60, 1000, 170)

# Taşma: yazı yaprağı görünür alanın ya da arka planı olan kabının dışına çıkıyor mu?
OLC_JS = """() => {
  const W = innerWidth, H = innerHeight, out = new Set();
  // Kırpan atalar (overflow) görünür alanı daraltır: kırpılıp gizlenen öge (odometre şeridi) taşma sayılmaz.
  const gorunur = e => { let r = e.getBoundingClientRect(), x0 = r.left, y0 = r.top, x1 = r.right, y1 = r.bottom;
    for (let p = e.parentElement; p && p !== document.body; p = p.parentElement) {
      const s = getComputedStyle(p); if (s.overflow === 'visible' && s.clipPath === 'none') continue;
      const q = p.getBoundingClientRect(); x0 = Math.max(x0, q.left); y0 = Math.max(y0, q.top); x1 = Math.min(x1, q.right); y1 = Math.min(y1, q.bottom); }
    return x1 - x0 > 1 && y1 - y0 > 1 ? { x0, y0, x1, y1 } : null; };
  const kap = e => { for (let p = e.parentElement; p && p !== document.body; p = p.parentElement) {
    const s = getComputedStyle(p); if (s.backgroundColor !== 'rgba(0, 0, 0, 0)' || s.backgroundImage !== 'none') return p; } return null; };
  for (const e of document.querySelectorAll('body *')) {
    if (e.childElementCount || !e.textContent.trim()) continue;
    const s = getComputedStyle(e); if (s.visibility === 'hidden' || s.display === 'none' || +s.opacity === 0) continue;
    const g = gorunur(e); if (!g) continue;
    const ad = e.textContent.trim().slice(0, 24);
    if (g.x0 < -1 || g.x1 > W + 1 || g.y0 < -1 || g.y1 > H + 1) out.add('kadraj dışı: ' + ad);
    if (e.scrollWidth > e.clientWidth + 2 && s.overflow !== 'visible') out.add('kırpılmış yazı: ' + ad);
    const k = kap(e); if (k) { const q = k.getBoundingClientRect();
      if (g.x1 > q.right + 2 || g.x0 < q.left - 2) out.add('kabından taşıyor: ' + ad); }
  }
  return [...out];
}"""


def kart_yolu(kimlik: str) -> Path:
    return paths.LIBRARY / "stiller" / "onizleme" / kimlik / "kart.jpg"


def olcum_yolu(kimlik: str) -> Path:
    return kart_yolu(kimlik).with_suffix(".json")


def _sigdir(im, kutu):
    x, y, w, h = kutu
    if bb := im.getbbox():
        im = im.crop(bb)
    o = min(w / im.width, h / im.height, 1.0)
    im = im.resize((max(1, round(im.width * o)), max(1, round(im.height * o))))
    return im, (x + (w - im.width) // 2, y + (h - im.height) // 2)


def _zemin(t):
    from PIL import Image, ImageDraw
    hx = tema_token._rgb
    a, b = hx(t.renk.zemin), hx(t.renk.vurgu)
    im = Image.new("RGB", (W, H), a)
    d = ImageDraw.Draw(im)
    for y in range(H):
        k = (y / H) ** 2 * 0.18
        d.line([(0, y), (W, y)], fill=tuple(round(a[i] * (1 - k) + b[i] * k) for i in range(3)))
    return im.convert("RGBA")


def _altyazi_html(t) -> str:
    a = t.altyazi
    kelime = ["Her", "katman", "bu", "stilde"]
    sp = "".join(f'<span style="color:{a.aktif_renk if i == 1 else a.renk}">{w}</span> ' for i, w in enumerate(kelime))
    return (f"<!doctype html><html><head><meta charset='utf-8'></head><body style='margin:0;background:transparent'>"
            f"<div style=\"position:absolute;left:0;right:0;top:40px;text-align:center;font-family:'{a.font}';font-weight:{a.agirlik};"
            f"font-size:72px;line-height:1.1;letter-spacing:{a.kontur / 2}px;-webkit-text-stroke:{a.kontur}px {a.kontur_renk};paint-order:stroke fill\">{sp}</div></body></html>")


def uret(kimlik: str, p) -> dict:
    """Tek stilin kartı; `p` açık playwright. Ölçüm sözlüğü döner ve yazılır."""
    from PIL import Image

    from . import pano
    t = tema_token.oku(kimlik)
    if t is None:
        raise SystemExit(f"Tema yok: {kimlik}")
    css = motion.tema_yolu(kimlik)
    kart = _zemin(t)
    tasma: list[str] = []

    def ciz(html: Path, w: int, h: int, an: float, param: dict | None, kutu):
        b, pg = pano.ac(p, html, w, h, css, param)
        pg.add_style_tag(content=pano.SAYDAM_CSS)
        pg.evaluate(pano.SEEK, an)
        tasma.extend(f"{html.stem}: {x}" for x in pg.evaluate(OLC_JS))
        im = Image.open(io.BytesIO(pg.screenshot(type="png", omit_background=True))).convert("RGBA")
        b.close()
        im, yer = _sigdir(im, kutu)
        kart.alpha_composite(im, yer)

    gecici = kart_yolu(kimlik).parent / "_altyazi.html"
    gecici.parent.mkdir(parents=True, exist_ok=True)
    gecici.write_text(_altyazi_html(t), encoding="utf-8")
    ciz(gecici, W, 260, 0, None, ALTYAZI)
    gecici.unlink()
    for _, ad, oran, kutu in PARCALAR:
        m = motion.meta(ad)
        param = {k: pr["vars"] for k, pr in (m.get("param") or {}).items()} or None
        w, h = (W, H) if m.get("tam") else (m["w"], m["h"])
        ciz(motion.kok() / ad / f"{ad}.html", w, h, m["sure"] * oran, param, kutu)
    # Geçiş: yatay sürümün ilk çeyreği (kapanma sürerken aile ve renk görünür), hücreye ortadan kırpılır.
    g = next((f"gecis-{x}-yatay" for x in t.gecis if f"gecis-{x}-yatay" in motion.kimlikler()), "gecis-sil-yatay")
    gm = motion.meta(g)
    b, pg = pano.ac(p, motion.kok() / g / f"{g}.html", 1920, 1080, css)
    pg.add_style_tag(content=pano.SAYDAM_CSS)
    pg.evaluate(pano.SEEK, gm["sure"] * 0.3)
    gim = Image.open(io.BytesIO(pg.screenshot(type="png", omit_background=True))).convert("RGBA")
    b.close()
    x, y, w, h = GECIS
    gim = gim.resize((w, round(1080 * w / 1920)))
    ust = (gim.height - h) // 2
    kart.alpha_composite(gim.crop((0, ust, w, ust + h)), (x, y))
    kart.convert("RGB").save(kart_yolu(kimlik), quality=88)
    olcum = {"stil": kimlik, "gecis": g, "tasma": tasma, "kontrast": tema_token.denetle(t)}
    olcum_yolu(kimlik).write_text(json.dumps(olcum, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return olcum


def kur(hedefler: list[str] | None = None) -> list[dict]:
    from playwright.sync_api import sync_playwright

    from .stil_katalog import stiller
    secilen = hedefler or [e["id"] for e in stiller()]
    sonuc = []
    with sync_playwright() as p:
        for k in secilen:
            o = uret(k, p)
            durum = "temiz" if not (o["tasma"] or o["kontrast"]) else f"{len(o['tasma'])} taşma, {len(o['kontrast'])} kontrast"
            print(f"  kart: {paths.rel(kart_yolu(k))} · {durum}")
            sonuc.append(o)
    return sonuc
