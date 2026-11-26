"""HyperFrames grafikleri: kompozisyon → saydam webm → kurguda motion klibi.

WHY: bkz. wiki/decisions/0050-hyperframes-birincil-motor.md. Yeni animasyon, motion grafik, metin grafiği ve tam ekran
sahne HyperFrames'te yazılır; Stüdyo timeline'ı ve gerçek çekim birleştirmesi Remotion'da kalır. Klipte
`hf: {ad, param, tema}` niyeti yazılır, webm'i vedit üretir (sablon ile aynı kalıp, ADR 0036).

Kompozisyon yerleri (ilk bulunan geçerli):
  1. proje: `work/edit/hf/<ad>/index.html` (tek seferlik grafik ya da sahne; E2 ve ai-edit yazar)
  2. kütüphane: `library/motion/hf/<ad>/index.html` (tekrar kullanılan şablon)
Render, kompozisyonun bir kopyasında yapılır: kopyaya seçili stilin token'ı `tema.css`, yazı tipleri `fonts/` olarak
girer. Kompozisyon `<link rel="stylesheet" href="tema.css">` ile token'ı okur; sabit renk ve font yazılmaz (ADR 0043).
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
from html import unescape
from pathlib import Path

from . import hf, motion, paths

KUTUPHANE = paths.MOTION_DIR / "hf"
GSAP = paths.LIBRARY / "vendor" / "gsap.min.js"
# three.js çekirdeği (window.HFUC, ADR 0063): `studio` içinde `npm run uc` üretir.
UC = paths.LIBRARY / "vendor" / "uc.js"
_KOK_OZ = re.compile(r'data-(width|height|duration)\s*=\s*"([\d.]+)"')
ATLA = {"renders", ".thumbnails", "node_modules", ".hyperframes"}


def proje_kok(work: Path) -> Path:
    return work / "edit" / "hf"


def bul(ad: str, work: Path | None = None) -> Path | None:
    """Kompozisyon klasörü: önce proje, sonra kütüphane. Ad yalnız harf, rakam, tire ve alt çizgi olabilir."""
    if not re.fullmatch(r"[A-Za-z0-9_-]+", ad or ""):
        return None
    adaylar = ([proje_kok(work) / ad] if work else []) + [KUTUPHANE / ad]
    return next((d for d in adaylar if (d / "index.html").is_file()), None)


def adlar(work: Path | None = None) -> list[str]:
    kokler = ([proje_kok(work)] if work else []) + [KUTUPHANE]
    return sorted({d.name for k in kokler if k.is_dir() for d in k.iterdir() if (d / "index.html").is_file()})


def olcu_metin(html: str, ad: str = "kompozisyon") -> dict:
    """Kök öğenin boyutu ve süresi (`data-width`, `data-height`, `data-duration`): {w, h, sure}."""
    kok = re.search(r"<[^>]*data-composition-id[^>]*>", html)
    oz = dict(_KOK_OZ.findall(kok.group(0) if kok else html))
    if not {"width", "height", "duration"} <= oz.keys():
        raise ValueError(f"{ad}: kök öğede data-width, data-height ve data-duration olmalı")
    return {"w": int(float(oz["width"])), "h": int(float(oz["height"])), "sure": float(oz["duration"])}


def olcu(klasor: Path) -> dict:
    return olcu_metin((klasor / "index.html").read_text(encoding="utf-8"), klasor.name)


def degisken_tanimlari(klasor: Path) -> list[dict]:
    """`data-composition-variables` içindeki tam değişken tanımları (id, type, label, default)."""
    html = (klasor / "index.html").read_text(encoding="utf-8")
    m = re.search(r"""data-composition-variables\s*=\s*(?:'([^']*)'|"([^"]*)")""", html)
    if not m:
        return []
    try:
        veri = json.loads(unescape(m.group(1) if m.group(1) is not None else m.group(2)))
        return [d for d in veri if isinstance(d, dict) and d.get("id")]
    except (ValueError, KeyError, TypeError):
        return []


def degisken_adlari(klasor: Path) -> set[str] | None:
    """`data-composition-variables` içindeki değişken kimlikleri; bildirilmemişse None."""
    html = (klasor / "index.html").read_text(encoding="utf-8")
    m = re.search(r"""data-composition-variables\s*=\s*(?:'([^']*)'|"([^"]*)")""", html)
    if not m:
        return None
    try:
        return {d["id"] for d in json.loads(unescape(m.group(1) if m.group(1) is not None else m.group(2)))}
    except (ValueError, KeyError, TypeError):
        return set()


def ses_ipuclari(klasor: Path) -> list[dict]:
    """Kompozisyondaki `data-sound-cues='[{"t":0.42,"rol":"click","guc":"orta"}]'` ses ipuçları."""
    html = (klasor / "index.html").read_text(encoding="utf-8")
    m = re.search(r"""data-sound-cues\s*=\s*(?:'([^']*)'|"([^"]*)")""", html)
    if not m:
        return []
    try:
        veri = json.loads(unescape(m.group(1) if m.group(1) is not None else m.group(2)))
        return [x for x in veri if isinstance(x, dict) and isinstance(x.get("t"), (int, float)) and x.get("rol")]
    except (ValueError, TypeError):
        return []


def meta_bilgi(klasor: Path) -> dict:
    """Opsiyonel `data-hf-meta='{"tur":"...","ne_zaman":"..."}'` katalog açıklaması."""
    html = (klasor / "index.html").read_text(encoding="utf-8")
    m = re.search(r"""data-hf-meta\s*=\s*(?:'([^']*)'|"([^"]*)")""", html)
    if not m:
        return {}
    try:
        d = json.loads(unescape(m.group(1) if m.group(1) is not None else m.group(2)))
        return d if isinstance(d, dict) else {}
    except (ValueError, TypeError):
        return {}


def ses_olaylari(p, k) -> list[dict]:
    """Kurgudaki `hf` motion kliplerinin `data-sound-cues` bildirimlerinden +1 kare senkron olaysesi olayları.

    WHY: bkz. wiki/decisions/0062-modern-hyperframes-motion-mimarisi.md. Görsel darbeden 1 kare sonra (+1/fps)
    gelen ses darbesi görsel-işitsel kilit hissini güçlendirir (HyperFrames sound.md & fizik-sezgisi).
    """
    gizli = {i.id for i in k.izler if i.gizli}
    olaylar: list[dict] = []
    bir_kare = 1.0 / max(1, k.sekans.fps)
    for c in k.klipler:
        if c.iz in gizli or c.tur != "motion" or not c.hf:
            continue
        klasor = bul(c.hf.get("ad", ""), p.work)
        if not klasor:
            continue
        for ipucu in ses_ipuclari(klasor):
            t_yerel = float(ipucu["t"])
            if t_yerel < 0 or t_yerel > c.sure:
                continue
            kayit = {
                "t": round(c.bas + t_yerel + bir_kare, 3),
                "tur": str(ipucu["rol"]),
                "not": f"hf {c.hf['ad']} ({c.id})",
            }
            if ipucu.get("guc"):
                kayit["guc"] = str(ipucu["guc"])
            olaylar.append(kayit)
    return olaylar


def canli_mi(klasor: Path) -> bool:
    """Kompozisyon canlı `data-composition-src` gömmesine uygun mu.

    WHY: bkz. wiki/decisions/0063-gsap-eklentileri-ve-threejs-hf.md. three.js sahnesi (`uc.js`) `<template>` sarmalında
    çalışmaz (dış betik atılır, WebGL bağlamı ana sayfayla paylaşılmaz) ve ağırdır; önbellekli saydam WebM olarak bir
    kez üretilir. `data-hf-meta` içinde `"canli": false` aynı yolu elle seçer.
    """
    try:
        ham = (klasor / "index.html").read_text(encoding="utf-8")
    except OSError:
        return False
    return not (re.search(r"""src\s*=\s*["']uc\.js["']""", ham) or re.search(r'"canli"\s*:\s*false', ham))


def ayni_yon(klasor: Path, sekans: tuple[int, int]) -> bool:
    """Kompozisyonun tanımlı yönü (yatay/dikey) sekansla aynı mı. Ölçü okunamazsa True (eski davranış).

    WHY: bkz. wiki/specs/hf-canli-gomme-ve-dikey-duzen.md. Canlı gömme yalnız aynı yönde; farklı yönde WebM (derle.ts aynı kural)."""
    try:
        o = olcu(klasor)
    except ValueError:
        return True
    return (o["w"] >= o["h"]) == (sekans[0] >= sekans[1])


def grafik_harita(work: Path | None = None) -> dict[str, dict]:
    """Canlı alt-kompozisyon olarak gömülebilen tüm `hf` grafikleri: ad → {w, h, sure, varsayilan, yer}."""
    out: dict[str, dict] = {}
    for ad in adlar(work):
        d = bul(ad, work)
        if not d or not canli_mi(d):
            continue
        try:
            o = olcu(d)
        except ValueError:
            continue
        varsayilan = {t["id"]: t["default"] for t in degisken_tanimlari(d) if "default" in t}
        out[ad] = {**o, "varsayilan": varsayilan, "yer": "proje" if (work and d.parent == proje_kok(work)) else "kutuphane"}
    return out


def grafik_kopyasi(ad: str, kok: str, w: int, h: int, work: Path | None = None) -> str | None:
    """Standalone `index.html` HF kompozisyonunu canlı `data-composition-src` `<template>` sahnesine dönüştürür."""
    klasor = bul(ad, work)
    if not klasor:
        return None
    ham = (klasor / "index.html").read_text(encoding="utf-8")
    return _sablon_sar(ham, kok, w, h)


KOK_SORGU = re.compile(r"""document\s*\.\s*(?:getElementById\(\s*["']root["']\s*\)|querySelector\(\s*["']#root["']\s*\))""")
ANA_PARAM = re.compile(r"""window\.__HF_PARAM\s*(?:\.\s*main\b|\[\s*["']main["']\s*\])""")


def kok_sorgusu_cevir(js: str, kok: str) -> str:
    """Bağımsız kompozisyonun `#root` ve `__HF_PARAM.main` okumalarını gömülen klibin köküne ve parametresine çevirir.

    WHY: bkz. wiki/specs/hf-canli-gomme-ve-dikey-duzen.md. 42 kütüphane kompozisyonu kökü `document.getElementById("root")`
    ile arıyordu; canlı gömmede kök kimliği değiştiği için sorgu null dönüp betiği düşürüyor ya da sayfadaki başka kökü
    yakalıyordu (pilot: `kamera-crash-zoom` doruğu boş). paketle.ts `grafikKopyasi` aynı kuralı uygular."""
    js = KOK_SORGU.sub("__kok", js)
    return ANA_PARAM.sub(f'window.__HF_PARAM["{kok}"]', js)


def _sablon_sar(ham: str, kok: str, w: int, h: int) -> str:
    """index.html → <template> alt kompozisyon dönüşümü (paketle.ts grafikKopyasi ile aynı kural)."""
    if "<template" in ham and "__KOK__" in ham:
        return ham.replace("__KOK__", kok).replace("__W__", str(w)).replace("__H__", str(h))
    stiller = "\n".join(re.findall(r"<style[^>]*>([\s\S]*?)</style>", ham, flags=re.I))
    stiller = re.sub(r"\bhtml\s*,\s*body\s*,\s*#root\b", f"#{kok}", stiller)
    stiller = re.sub(r"#root\b", f"#{kok}", stiller)
    stiller = re.sub(r"\b(?:html|body)\s*\{[^}]*\}", "", stiller)
    body_m = re.search(r"<body[^>]*>([\s\S]*?)</body>", ham, flags=re.I)
    govde = body_m.group(1) if body_m else ham
    betikler: list[str] = []

    def _betik_al(m: re.Match) -> str:
        etiket, ic = m.group(1), m.group(2)
        if re.search(r"\bsrc\s*=", etiket, flags=re.I):
            return ""
        if ic.strip():
            betikler.append(ic)
        return ""

    govde = re.sub(r"<script([^>]*)>([\s\S]*?)</script>", _betik_al, govde, flags=re.I).strip()
    govde = re.sub(r'\bid\s*=\s*"root"', f'id="{kok}"', govde, count=1)
    govde = re.sub(r'\bdata-composition-id\s*=\s*"[^"]*"', f'data-composition-id="{kok}"', govde, count=1)
    govde = re.sub(r'\bdata-width\s*=\s*"[^"]*"', f'data-width="{w}"', govde, count=1)
    govde = re.sub(r'\bdata-height\s*=\s*"[^"]*"', f'data-height="{h}"', govde, count=1)
    vars_m = re.search(r"""data-composition-variables\s*=\s*(?:'([^']*)'|"([^"]*)")""", ham)
    vars_oz = ""
    if vars_m:
        raw_v = vars_m.group(1) if vars_m.group(1) is not None else vars_m.group(2)
        vars_oz = f" data-composition-variables='{raw_v}'"
    if vars_oz and "data-composition-variables" not in govde:
        govde = govde.replace(f'id="{kok}"', f'id="{kok}"{vars_oz}', 1)
    birlesik_js = "\n".join(betikler)
    birlesik_js = re.sub(r'window\.__timelines\[\s*["\']main["\']\s*\]', f'window.__timelines["{kok}"]', birlesik_js)
    birlesik_js = kok_sorgusu_cevir(birlesik_js, kok)
    sarmal_js = (
        "(() => {\n"
        f'  const __kok = document.getElementById("{kok}");\n'
        "  if (!__kok) return;\n"
        f'  const __param = (window.__HF_PARAM && window.__HF_PARAM["{kok}"]) || {{}};\n'
        "  __kok.querySelectorAll('[data-var-text]').forEach((el) => {\n"
        "    const k = el.getAttribute('data-var-text');\n"
        "    if (k && Object.prototype.hasOwnProperty.call(__param, k) && __param[k] != null) el.textContent = String(__param[k]);\n"
        "  });\n"
        "  const __q = (s) => (typeof s === 'string' && s.startsWith('#') ? __kok.querySelector(s) : __kok.querySelector(s));\n"
        "  const __qa = (s) => Array.from(__kok.querySelectorAll(s));\n"
        "  const _gsap = window.gsap;\n"
        "  const gsap = _gsap ? new Proxy(_gsap, {\n"
        "    get(target, prop) {\n"
        "      if (prop === 'timeline') return (cfg) => {\n"
        "        const tl = target.timeline(cfg);\n"
        "        const wrap = (fn) => (t, ...rest) => {\n"
        "          const el = typeof t === 'string' ? __qa(t) : t;\n"
        "          return fn.call(tl, el, ...rest);\n"
        "        };\n"
        "        ['to', 'from', 'fromTo', 'set'].forEach((m) => { const orig = tl[m]; tl[m] = wrap(orig); });\n"
        "        return tl;\n"
        "      };\n"
        "      return typeof target[prop] === 'function' ? target[prop].bind(target) : target[prop];\n"
        "    }\n"
        "  }) : _gsap;\n"
        "  const HF_CTX = { kok: __kok, param: __param, q: __q, qa: __qa, w: " + str(w) + ", h: " + str(h) + " };\n"
        + birlesik_js + "\n"
        "})();"
    )
    return (
        "<template>\n"
        f"<style>\n#{kok}{{position:absolute;inset:0;background:none;overflow:hidden;}}\n{stiller}\n"
        # WHY: bkz. wiki/specs/hf-canli-gomme-ve-dikey-duzen.md; bileşenin kök kuralı (position: relative; height: 100%)
        # sarmalı ezip yüksekliği sıfırlıyordu, container query kareyi yatay sanıyordu. Kaplama kuralı stillerden sonra gelir.
        f"#{kok}{{position:absolute !important;inset:0 !important;width:100% !important;height:100% !important;}}\n</style>\n"
        f"{govde}\n"
        f"<script>\n{sarmal_js}\n</script>\n"
        "</template>\n"
    )


def _dosyalar(klasor: Path) -> list[Path]:
    return sorted(f for f in klasor.rglob("*") if f.is_file() and not (ATLA & set(f.relative_to(klasor).parts)))


def ozet(klasor: Path, param: dict | None, tema: str | Path | None) -> str:
    """Önbellek anahtarı: kompozisyon dosyaları, tema token'ı ya da parametre değişince değişir."""
    s = hashlib.sha1()
    for f in _dosyalar(klasor):
        s.update(f.relative_to(klasor).as_posix().encode())
        s.update(f.read_bytes())
    t = motion.tema_yolu(tema) or motion.tema_yolu("varsayilan")
    s.update(t.read_bytes() if t else b"")
    # Render kopyasına giren ortak dosyalar da anahtarda: yazı tipi ya da GSAP değişince eski webm dönmesin.
    for f in (paths.FONTS_DIR / "fonts.json", GSAP, UC):
        s.update(f.read_bytes() if f.is_file() else b"")
    s.update(json.dumps(param or {}, sort_keys=True, ensure_ascii=False).encode())
    return s.hexdigest()[:10]


def _fontlar() -> dict[str, dict]:
    try:
        d = json.loads((paths.FONTS_DIR / "fonts.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return {ad: b for ad, b in d.items() if isinstance(b, dict) and b.get("file") and (paths.FONTS_DIR / b["file"]).is_file()}


def _font_dosyalari() -> list[Path]:
    return [paths.FONTS_DIR / b["file"] for b in _fontlar().values()]


def _font_css() -> str:
    return "".join(f'@font-face{{font-family:"{ad}";font-weight:{b.get("weight", "100 900")};src:url("fonts/{b["file"]}")}}'
                   for ad, b in _fontlar().items())


def _hazirla(klasor: Path, hedef: Path, tema: str | Path | None) -> None:
    """Render kopyası: kompozisyon + tema.css + yazı tipleri. HyperFrames proje dışındaki dosyayı okumaz (0.9.58+)."""
    if hedef.exists():
        shutil.rmtree(hedef)
    shutil.copytree(klasor, hedef, ignore=shutil.ignore_patterns(*ATLA))
    t = motion.tema_yolu(tema) or motion.tema_yolu("varsayilan")
    (hedef / "tema.css").write_text(_font_css() + "\n" + (t.read_text(encoding="utf-8") if t else ""), encoding="utf-8")
    # Ajan kompozisyonu GSAP'sız yazabilir; HyperFrames'in kendi kopyası konur (dış adres yok).
    if not (hedef / "gsap.min.js").exists() and "gsap.min.js" in (hedef / "index.html").read_text(encoding="utf-8"):
        if GSAP.is_file():
            shutil.copy2(GSAP, hedef / "gsap.min.js")
    if not (hedef / "uc.js").exists() and "uc.js" in (hedef / "index.html").read_text(encoding="utf-8") and UC.is_file():
        shutil.copy2(UC, hedef / "uc.js")
    fonts = hedef / "fonts"
    fonts.mkdir(exist_ok=True)
    for f in _font_dosyalari():
        if not (fonts / f.name).exists():
            shutil.copy2(f, fonts / f.name)


def boyut_ez(html: str, w: int, h: int) -> str:
    """Kök öğenin `data-width`/`data-height` değerini sekans boyutuna çevirir (ilk eşleşme kök öğedir)."""
    html = re.sub(r'\bdata-width\s*=\s*"[^"]*"', f'data-width="{w}"', html, count=1)
    return re.sub(r'\bdata-height\s*=\s*"[^"]*"', f'data-height="{h}"', html, count=1)


def uret(ad: str, param: dict | None, tema: str | Path | None, work: Path, klasor: Path,
         sekans: tuple[int, int] | None = None) -> tuple[Path, dict]:
    """Kompozisyonu `klasor` altına saydam webm olarak üretir (varsa yeniden üretmez). (dosya, {sure, w, h}) döner.

    `sekans` verilirse ve kompozisyonun boyutundan farklıysa sekans boyutunda üretilir. WHY: bkz.
    wiki/specs/hf-canli-gomme-ve-dikey-duzen.md; 16:9 kompozisyon 9:16 Reels'te küçülüp okunmuyordu (SOZLESME 11. madde)."""
    kaynak = bul(ad, work)
    if not kaynak:
        raise ValueError(f"HyperFrames kompozisyonu yok: {ad} (work/edit/hf/{ad}/ ya da library/motion/hf/{ad}/)")
    bilgi = olcu(kaynak)
    ez = sekans and tuple(sekans) != (bilgi["w"], bilgi["h"])
    if ez:
        bilgi = {**bilgi, "w": int(sekans[0]), "h": int(sekans[1])}
    hedef = klasor / f"hf-{ad}-{ozet(kaynak, param, tema)}{f'-{bilgi['w']}x{bilgi['h']}' if ez else ''}.webm"
    if not hedef.exists():
        kopya = work / "hf-render" / hedef.stem
        try:
            _hazirla(kaynak, kopya, tema)
            if ez:
                f = kopya / "index.html"
                f.write_text(boyut_ez(f.read_text(encoding="utf-8"), bilgi["w"], bilgi["h"]), encoding="utf-8")
            hf.render_saydam(kopya, hedef, degiskenler=param or None)
        finally:
            shutil.rmtree(kopya, ignore_errors=True)
    return hedef, bilgi


def denetle(ad: str | None, param: dict | None, work: Path) -> list[str]:
    """Kurgu denetimi için hata listesi: kompozisyon var mı, ölçüsü okunuyor mu, parametreler bildirilmiş mi."""
    kaynak = bul(ad or "", work)
    if not kaynak:
        return [f"bilinmeyen HyperFrames kompozisyonu '{ad}' (geçerli: {', '.join(adlar(work)) or 'yok'})"]
    try:
        olcu(kaynak)
    except ValueError as e:
        return [str(e)]
    if param is not None and not isinstance(param, dict):
        return [f"{ad}: param bir nesne olmalı"]
    bildirilen = degisken_adlari(kaynak)
    fazla = sorted(set(param or {}) - (bildirilen or set()))
    return [f"{ad}: bildirilmemiş parametre: {', '.join(fazla)} (data-composition-variables)"] if fazla else []
