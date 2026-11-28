"""Motion kütüphanesi kayıtlarını (library/motion/custom/<id>/<id>.html) HyperFrames ile saydam webm'e çevirir.

WHY: bkz. wiki/decisions/0051-uctan-uca-hyperframes.md. Kayıtlar CSS `@keyframes`, WAAPI ya da `window.seek(t)` ile
oynar ve eskiden Playwright ile kare kare yakalanıyordu (`pano.render`). Kayıt HTML'i değiştirilmez: geçici bir
HyperFrames projesine sarılır, duraklatılmış tek GSAP zaman çizelgesinin her karesinde `pano.SEEK`'in yaptığı sürülür
(animasyonlar duraklatılıp zamana konur, `window.seek` çağrılır). Davranış eski yolla aynıdır:
  - `window.PARAM` sayfa betiklerinden önce (şablon parametresi, ADR 0036),
  - kütüphane yazı tipleri ve seçili stilin tema CSS'i (ADR 0043), saydam zemin,
  - adımlı stilde zaman tema kare hızına yuvarlanır, `son_tam` ile son kare tam süre anındadır,
  - piksel stilde kare küçültülüp alfası eşiklenir ve en yakın komşuyla büyütülür (ffmpeg, `pano.pikselle` karşılığı).
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from . import hf, hf_grafik, paths

ATLA = ("*.webm", "*.mp4", "poster.jpg", "kontak.jpg")

SURUCU = """<script>
(() => {
  // HyperFrames sürücüsü (vedit hf_motion): kayıt kendi saatini kullanmaz; her kare yalnız t'den türer.
  const Y = window.__HFM;
  const seek = (t) => {
    for (const a of document.getAnimations()) { a.pause(); a.currentTime = t * 1000; }
    if (typeof window.seek === "function") window.seek(t);
  };
  // HyperFrames CSS animasyonunu (CSSAnimation) kendi saatiyle sürer; adımlı zaman ve son_tam ezilirdi. Her biri aynı
  // anahtar kare ve zamanlamayla WAAPI animasyonuna çevrilir, CSS olanı iptal edilir: zamanı yalnız bu sürücü verir.
  // getKeyframes() @keyframes'te yazılmamış uç kareyi (yalnız `to` olan çıkış gibi) o anki değerle açık kareye çevirir;
  // çevrilen animasyon başta o değeri dayatırdı (fiyat-etiketi 0. karede görünürdü). Kuralda olmayan uç kare atılır, örtük kalır.
  const ofsetler = new Map();
  const kuralOfsetleri = (ad) => {
    if (ofsetler.has(ad)) return ofsetler.get(ad);
    let s = null;
    for (const ss of document.styleSheets) {
      let kurallar; try { kurallar = ss.cssRules; } catch { continue; }
      for (const r of kurallar) {
        if (r.type !== 7 || r.name !== ad) continue; // CSSKeyframesRule
        s = new Set();
        for (const k of r.cssRules) for (const p of k.keyText.split(",")) { const t = p.trim(); s.add(t === "from" ? 0 : t === "to" ? 1 : parseFloat(t) / 100); }
      }
    }
    ofsetler.set(ad, s);
    return s;
  };
  const cevir = () => {
    if (typeof CSSAnimation === "undefined") return;
    for (const a of document.getAnimations()) {
      if (!(a instanceof CSSAnimation) || !a.effect || !a.effect.target) continue;
      const ef = a.effect;
      const acik = kuralOfsetleri(a.animationName);
      const tum = ef.getKeyframes();
      const kareler = tum
        .filter((k) => !acik || [...acik].some((o) => Math.abs(o - k.computedOffset) < 1e-6))
        .map(({ computedOffset, ...k }) => k);
      const zaman = { ...ef.getTiming(), pseudoElement: ef.pseudoElement || undefined };
      // CSS'te bölüm eğrisi bölümün başındaki karede durur: örtük başlangıç atılıp tek bölüm kaldıysa eğri bütün animasyona geçer.
      if (kareler.length === 1 && tum.length > 1 && tum[0].computedOffset === 0 && kareler[0] !== tum[0]) zaman.easing = tum[0].easing || "linear";
      const yeni = new Animation(new KeyframeEffect(ef.target, kareler, zaman), document.timeline);
      a.cancel();
      yeni.pause();
    }
  };
  const kare = (zaman) => {
    cevir(); // her karede: ilk kare load'dan önce yakalanabilir, betik sonradan animasyonlu öğe ekleyebilir
    const i = Math.round(zaman * Y.fps);
    let t = zaman;
    if (Y.son_tam && i >= Y.kare - 1) t = Y.sure;
    else if (Y.adim) t = Math.floor(zaman * Y.adim + 1e-6) / Y.adim;
    seek(t);
    // HyperFrames adaptörleri zaman çizelgesinden sonra aynı görevde animasyonları kendi t'sine sarar; mikrogörev onlardan
    // sonra, kare yakalanmadan önce koşar: adımlı ve son_tam zamanı kalıcı olur.
    queueMicrotask(() => seek(t));
  };
  const tl = gsap.timeline({ paused: true });
  const saat = { s: 0 };
  tl.to(saat, { s: Y.sure, duration: Y.sure, ease: "none", onUpdate: () => kare(tl.time()) }, 0);
  window.__timelines = window.__timelines || {};
  window.__timelines["main"] = tl;
  const ilk = () => kare(0);
  if (document.readyState === "complete") ilk(); else window.addEventListener("load", ilk);
})();
</script>"""


def _govde_sar(html: str, w: int, h: int, sure: float) -> str:
    """Gövde içeriğini HyperFrames kök öğesine alır (kanvas = kök).

    WHY: HyperFrames sayfaya kendi sıfırlamasını uygular (body iç boşluğu, vh birimleri); kayıtlar tam kare mutlak
    konumlu çizer ve sarılınca birebir aynı kalır (35/35 ölçüldü). Düzeni body'ye bağlayan sayfa (tema kartı) içeriğini
    bir kapsayıcıda tutmalı. Kökü body yapmak ya da boş kardeş öğe koymak bu sıfırlamayı engellemedi.
    """
    kok = (f'<div id="hfm-kok" data-composition-id="main" data-start="0" data-duration="{sure:g}" data-width="{w}" '
           f'data-height="{h}" style="position:relative;width:{w}px;height:{h}px;overflow:hidden">')
    m = re.search(r"<body[^>]*>", html, re.I)
    if not m:
        raise ValueError("kayıt HTML'inde <body> yok")
    sonlar = list(re.finditer(r"</body\s*>", html, re.I))  # .lower() değil: "İ".lower() iki karakter, konum kayar
    son = sonlar[-1].start() if sonlar else len(html)
    return html[:m.end()] + kok + html[m.end():son] + "</div>" + html[son:]


def hazirla(html: Path, hedef: Path, *, sure: float, w: int, h: int, fps: int, css: Path | None, param: dict | None,
            son_tam: bool, adim: int | None) -> None:
    """Geçici HyperFrames projesi: kayıt klasörünün kopyası, sarılmış index.html, fontlar, tema, GSAP."""
    if hedef.exists():
        shutil.rmtree(hedef)
    shutil.copytree(html.parent, hedef, ignore=shutil.ignore_patterns(*ATLA))
    fonts = hedef / "fonts"
    fonts.mkdir(exist_ok=True)
    for f in hf_grafik._font_dosyalari():
        shutil.copy2(f, fonts / f.name)
    shutil.copy2(hf_grafik.GSAP, hedef / "hfm-gsap.min.js")
    tema = (css.read_text(encoding="utf-8") if css and css.is_file() else "")
    y = {"sure": sure, "fps": fps, "kare": round(sure * fps), "son_tam": son_tam, "adim": adim or 0}
    bas = ("<script>window.__HFM = " + json.dumps(y) + ";"
           + (" window.PARAM = " + json.dumps(param, ensure_ascii=False) + ";" if param is not None else "") + "</script>"
           + "<style>" + hf_grafik._font_css() + "</style>")
    # Tema ve saydamlık sayfanın kendi stilinden sonra (pano.ac add_style_tag ile aynı öncelik).
    son = ("<style>" + tema + "\nhtml,body{background:transparent!important}</style>"
           + '<script src="hfm-gsap.min.js"></script>' + SURUCU)
    kaynak = (html.read_text(encoding="utf-8"))
    m = re.search(r"<head[^>]*>", kaynak, re.I)
    kaynak = kaynak[:m.end()] + bas + kaynak[m.end():] if m else bas + kaynak
    kaynak = _govde_sar(kaynak, w, h, sure)
    # .lower() kullanılmaz: "İ".lower() iki karakterdir, Türkçe metinde konum kayardı (tema kartında "<" artığı kaldı).
    govde_sonu = list(re.finditer(r"</body\s*>", kaynak, re.I))
    i = govde_sonu[-1].start() if govde_sonu else -1
    kaynak = kaynak[:i] + son + kaynak[i:] if i >= 0 else kaynak + son
    (hedef / "index.html").write_text(kaynak, encoding="utf-8")


def _pikselle(webm: Path, n: int) -> None:
    """pano.pikselle karşılığı: n kat küçült (alan ortalaması), alfayı 128'de eşikle, en yakın komşuyla büyüt."""
    gecici = webm.with_name(f".{webm.stem}.piksel.webm")
    from .pano import kodlayici
    # WHY: Türkçe Windows varsayılan cp1254 kodlamasında ffmpeg UTF-8 çıktısı UnicodeDecodeError vermesin.
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-c:v", "libvpx-vp9", "-i", str(webm), "-vf",
                        f"format=rgba,scale=iw/{n}:ih/{n}:flags=area,lut=a='if(gte(val\\,128)\\,255\\,0)',"
                        f"scale=iw*{n}:ih*{n}:flags=neighbor", *kodlayici(gecici), str(gecici)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode:
        gecici.unlink(missing_ok=True)
        raise RuntimeError(f"piksel işlemi başarısız: {r.stderr[-300:]}")
    gecici.replace(webm)


def render(html: Path, out: Path, *, sure: float, w: int, h: int, fps: int = 30, css: Path | None = None,
           param: dict | None = None, son_tam: bool = False) -> Path:
    """Kaydı saydam webm'e render eder (pano.render ile aynı imza ve sonuç)."""
    from .tema_token import yapi
    y = yapi(css)
    with tempfile.TemporaryDirectory(prefix="hfm-", dir=paths.ROOT / "work") as d:
        proje = Path(d) / html.stem
        hazirla(html, proje, sure=sure, w=w, h=h, fps=fps, css=css, param=param, son_tam=son_tam, adim=y["adim_fps"])
        hf.render_saydam(proje, out, fps=fps)
    if y["piksel"] > 1:
        _pikselle(out, y["piksel"])
    return out


def kare(html: Path, out: Path, *, t: float = 0.0, w: int, h: int, css: Path | None = None, param: dict | None = None) -> Path:
    """Tek kare (jpg/png): kayıt ya da kart HTML'inin `t` anı, `hyperframes snapshot` ile (eskiden Playwright ekran görüntüsü)."""
    with tempfile.TemporaryDirectory(prefix="hfk-", dir=paths.ROOT / "work") as d:
        proje = Path(d) / html.stem
        sure = max(t + 0.1, 0.2)
        hazirla(html, proje, sure=sure, w=w, h=h, fps=30, css=css, param=param, son_tam=False, adim=None)
        # Kart tam karedir: saydamlık yok, sayfanın kendi zemini kalır.
        i = (proje / "index.html").read_text(encoding="utf-8").replace("html,body{background:transparent!important}", "")
        (proje / "index.html").write_text(i, encoding="utf-8")
        kareler = Path(d) / "kare"
        hf.run(["snapshot", str(proje), "--at", f"{t:.4f}", "--no-end", "--output", str(kareler)], cwd=proje)
        png = sorted(kareler.rglob("*.png"))
        if not png:
            raise RuntimeError(f"kare alınamadı: {html.name}")
        out.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(png[0]), *(["-q:v", "3"] if out.suffix.lower() in (".jpg", ".jpeg") else []),
                        str(out)], check=True)
    return out


def kare_saydam(html: Path, out: Path, *, t: float, w: int, h: int, css: Path | None = None, param: dict | None = None,
                fps: int = 30) -> Path:
    """Saydam tek kare (RGBA png): `t` anına kadar kısa saydam render, o kare çıkarılır (snapshot alfa vermez)."""
    n = round(t * fps)
    with tempfile.TemporaryDirectory(prefix="hfs-", dir=paths.ROOT / "work") as d:
        webm = Path(d) / "k.webm"
        render(html, webm, sure=(n + 2) / fps, w=w, h=h, fps=fps, css=css, param=param)
        out.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-c:v", "libvpx-vp9", "-i", str(webm), "-vf", f"select=eq(n\\,{n})",
                        "-frames:v", "1", "-pix_fmt", "rgba", str(out)], check=True)
    return out

