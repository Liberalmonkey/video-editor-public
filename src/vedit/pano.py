"""HTML panoyu kare kare mp4'e çevirir (ekran kaydı değil, sanal saat).

Yöntem YouTube-AI-Motion-Graphics tools/export.py'den (MIT): her karede tüm animasyonlar duraklatılır,
tam zamana konumlanır, ekran görüntüsü alınır. WHY: bkz. wiki/decisions/0014-altyazi-standardi-ve-repo-entegrasyonu.md
"""

from __future__ import annotations

import json
import math
import subprocess
from pathlib import Path

# Tek kare (görsel) render'ında bağlanan yazı tipleri: html work/ altında durur, dosyalar library/fonts'tan gelir.
FONTLAR = {"Montserrat": "Montserrat-Variable.ttf", "Playfair Display": "PlayfairDisplay-Variable.ttf"}

# Geri sarmada da aynı kare çıkmalı: video kaynakları seek bitene kadar beklenir.
SEEK = """async t => {
  for (const a of document.getAnimations()) { a.pause(); a.currentTime = t * 1000; }
  if (window.seek) window.seek(t);
  if (window.gsap) { gsap.globalTimeline.pause(); gsap.globalTimeline.seek(t, false); }
  const vids = [...document.querySelectorAll('video')];
  await Promise.all(vids.map(v => new Promise(ok => {
    v.pause();
    if (!v.duration) return ok();
    const hedef = t % v.duration;
    if (Math.abs(v.currentTime - hedef) < 0.001) return ok();
    v.addEventListener('seeked', ok, { once: true });
    v.currentTime = hedef;
    setTimeout(ok, 2000);
  })));
}"""


# WHY: opaklık ve transform animasyonu bileşimci iş parçacığında koşar; sayfa yüklenirken ilerleyen animasyon, ana iş parçacığında
# duraklatılıp sarılsa da ekran görüntüsüne eski hâliyle girebiliyordu (ölçüm 2026-11-13: 16 denemede 4 yanlış kare, bayrakla 0).
BAYRAK = ["--disable-threaded-animation"]


def _tarayici(p):
    for kanal in ("chrome", "msedge"):
        try:
            return p.chromium.launch(channel=kanal, args=BAYRAK)
        except Exception:
            continue
    return p.chromium.launch(args=BAYRAK)  # Playwright'ın kendi Chromium'u kuruluysa


def ac(p, html: Path, w: int, h: int, css: Path | None, param: dict | None = None):
    """Tarayıcı ve panoya hazır sayfa döner. `param` sayfa betiklerinden önce window.PARAM olur (motion şablonu, ADR 0036)."""
    b = _tarayici(p)
    pg = b.new_page(viewport={"width": w, "height": h})
    if param is not None:
        pg.add_init_script("window.PARAM = " + json.dumps(param, ensure_ascii=False))
    pg.goto(html.resolve().as_uri())
    pg.wait_for_load_state("networkidle")
    if css:
        # WHY: bkz. wiki/decisions/0039-fizik-ritim-galeri.md. Tema `--font` ile kütüphanedeki herhangi bir yazı tipini seçer;
        # kayıt sayfaları yalnız Montserrat tanımlıyordu, tema fontu sessizce yedeğe düşüyordu.
        pg.add_style_tag(content=kutuphane_fontlari())
        pg.add_style_tag(path=str(css))
    pg.evaluate("document.fonts.ready")
    return b, pg


def kutuphane_fontlari() -> str:
    """library/fonts/fonts.json'daki her yazı tipi için @font-face (yerel dosya, ağ yok)."""
    from .paths import FONTS_DIR
    try:
        d = json.loads((FONTS_DIR / "fonts.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return ""
    return "".join(f'@font-face{{font-family:"{ad}";font-weight:{v.get("weight", "100 900")};src:url("{(FONTS_DIR / v["file"]).resolve().as_uri()}")}}'
                   for ad, v in d.items() if isinstance(v, dict) and (FONTS_DIR / v.get("file", "")).is_file())


SAYDAM_CSS = "html,body{background:transparent!important}"


def kodlayici(out: Path) -> list[str]:
    """ffmpeg çıkış ayarları. .webm: VP9 + alfa (saydam motion, ADR 0031); diğerleri opak H.264."""
    # WHY: bkz. wiki/decisions/0031-motion-grafik.md. Kurgu.tsx .webm motion klibini transparent oynatır.
    if out.suffix.lower() == ".webm":
        return ["-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p", "-b:v", "0", "-crf", "24", "-row-mt", "1", "-auto-alt-ref", "0"]
    return ["-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p", "-movflags", "+faststart"]


def render(html: Path, out: Path, *, sure: float, w: int = 1920, h: int = 1080, fps: int = 30,
           css: Path | None = None, param: dict | None = None, son_tam: bool = False) -> int:
    """Kare sayısını döner. shortcut: tek süreç, uzun panolarda yavaşlarsa parçalı render eklenir."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise SystemExit('playwright yok: .venv/Scripts/python -m pip install -e ".[boards]"')
    if not html.exists():
        raise SystemExit(f"Pano yok: {html}")
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.suffix.lower() in (".png", ".jpg", ".jpeg"):  # görsel: --sure anındaki tek kare
        with sync_playwright() as p:
            b, pg = ac(p, html, w, h, css)
            from .paths import FONTS_DIR
            pg.add_style_tag(content="".join(f'@font-face {{ font-family: "{ad}"; font-weight: 100 900; src: url("'
                                             + (FONTS_DIR / dosya).resolve().as_uri() + '"); }' for ad, dosya in FONTLAR.items()))
            # Kullanılan her yazı tipi yüklensin: fonts.ready tek başına henüz istenmemiş tipi beklemez
            pg.evaluate("Promise.all([...document.querySelectorAll('body *')].map((e) => { const s = getComputedStyle(e);"
                        " return document.fonts.load(`${s.fontStyle} ${s.fontWeight} 40px ${s.fontFamily}`, e.textContent || 'a'); }))"
                        ".then(() => document.fonts.ready)")
            pg.evaluate(SEEK, sure)
            tip = "png" if out.suffix.lower() == ".png" else "jpeg"
            pg.screenshot(path=str(out), type=tip, **({"quality": 95} if tip == "jpeg" else {}))
            b.close()
        return 1
    kare = round(sure * fps)
    saydam = out.suffix.lower() == ".webm"
    # WHY: bkz. wiki/decisions/0043-stile-bagli-tema-tokenlari.md. Stilin yapısı: adımlı stilde zaman tema kare hızına
    # yuvarlanır (12 fps lastik hortum, 8 fps piksel); piksel stilde kare küçültülüp en yakın komşuyla büyütülür.
    from .tema_token import yapi
    y = yapi(css)
    adim, piksel = y["adim_fps"], y["piksel"]
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "image2pipe", "-c:v", "png", "-framerate", str(fps),
                            "-i", "-", *kodlayici(out), str(out)], stdin=subprocess.PIPE)
    # WHY: Playwright ya da write hatasında stdin borusu ve ffmpeg süreci açık kalmasın.
    try:
        with sync_playwright() as p:
            b, pg = ac(p, html, w, h, css, param)
            if saydam:
                pg.add_style_tag(content=SAYDAM_CSS)
            for i in range(kare):
                # son_tam: son kare tam süre anında alınır; çıkışı süre sonunda biten motion klibi yarı saydam karede kalmasın (ADR 0036)
                t = sure if son_tam and i == kare - 1 else i / fps
                pg.evaluate(SEEK, math.floor(t * adim + 1e-6) / adim if adim and not (son_tam and i == kare - 1) else t)
                png = pg.screenshot(type="png", omit_background=saydam)
                enc.stdin.write(pikselle(png, piksel) if piksel > 1 else png)
            b.close()
        enc.stdin.close()
        if enc.wait() != 0:
            raise SystemExit("ffmpeg pano kodlaması başarısız")
    finally:
        if enc.stdin and not getattr(enc.stdin, "closed", False):
            try:
                enc.stdin.close()
            except OSError:
                pass
        if enc.poll() is None:
            enc.terminate()
            try:
                enc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                enc.kill()
                enc.wait(timeout=5)
    return kare


def pikselle(png: bytes, n: int) -> bytes:
    """Kareyi n kat küçültür, alfayı eşikler (yarı saydam hale kalmaz), en yakın komşuyla büyütür."""
    import io

    from PIL import Image
    im = Image.open(io.BytesIO(png)).convert("RGBA")
    w, h = im.size
    # Önçarpımlı küçültme: saydam pikselin siyahı kenar rengine karışıp koyu hale bırakmasın.
    k = im.convert("RGBa").resize((max(1, w // n), max(1, h // n)), Image.BOX).convert("RGBA")
    a = k.getchannel("A").point(lambda v: 255 if v >= 128 else 0)
    k.putalpha(a)
    b = io.BytesIO()
    k.resize((w, h), Image.NEAREST).save(b, "PNG")
    return b.getvalue()


