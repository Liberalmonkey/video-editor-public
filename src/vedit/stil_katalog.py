"""Hazır stil kataloğu: kurulu skill ve repolardaki video stillerini seçilebilir stil paketine çevirir.

WHY: bkz. wiki/decisions/0042-stil-katalogu-ve-video-temasi.md. Stiller (anime, çizgi film, editoryal...) diskte
`library/vendor/*`, `openmontage/styles/*` ve `library/motion/tema/*` altında dağınıktı ve arayüzden seçilemiyordu.
Katalog `library/stiller/katalog.json`; paket eklenirken karttan yazılır (STYLE.md, MOTION.md, tokens.json),
kullanıcı sonra düzenleyebilir. Her stilin motion teması vardır: grafikler turuncu değil stilin renginde gelir.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from . import kurgu, motion, native_motion, paths, stil, tema_token

YENI_NATIVE = {
    "tipografi/kinetik-baslik",
    "tipografi/bolum-baslik",
    "tipografi/vurgu-soz",
    "tipografi/durum-rozeti",
    "tipografi/kayan-kelime",
    "kart/cta-karti",
}

KOK = paths.LIBRARY / "stiller"
HEX = re.compile(r"#[0-9A-Fa-f]{6}")
TEMPO = {"yavas": "yavaş", "orta": "orta", "hizli": "hızlı"}
RENKLER = ("vurgu", "ikincil", "zemin", "yazi", "soluk")


def kok() -> Path:
    return paths.LIBRARY / "stiller"


def yukle() -> dict:
    return json.loads((kok() / "katalog.json").read_text(encoding="utf-8"))


def stiller() -> list[dict]:
    return yukle()["stiller"]


def bul(kimlik: str) -> dict:
    for e in stiller():
        if e["id"] == kimlik:
            return e
    raise SystemExit(f"Katalogda stil yok: {kimlik}")


def tema_adi(e: dict) -> str:
    # WHY: bkz. wiki/decisions/0043-stile-bagli-tema-tokenlari.md. Her kartın kendi teması vardır; başka temaya düşmez.
    return e["id"]


def palet(e: dict) -> dict[str, str]:
    """Kartın paleti; kart tema adı veriyorsa temanın CSS değişkenlerinden okunur."""
    if e.get("palet"):
        return dict(e["palet"])
    f = motion.tema_yolu(tema_adi(e))
    d = dict(re.findall(r"--([a-z]+)\s*:\s*([^;}\n]+)", f.read_text(encoding="utf-8"))) if f else {}
    return {k: d[k].strip() for k in RENKLER if k in d}


def dogrula() -> list[str]:
    """Katalog sözleşmesi: benzersiz kimlik, bilinen kategori, geçerli renk, var olan tema, geçiş, efekt ve motion."""
    d = yukle()
    h: list[str] = []
    eski_kimlikler = motion.kimlikler()
    kimlikler = set(eski_kimlikler) | set(native_motion.kayitlar()) | YENI_NATIVE
    gecisler = {re.sub(r"^gecis-|-(dikey|yatay)$", "", k) for k in eski_kimlikler if k.startswith("gecis-")} | set(kurgu.ORTA_GECIS)
    try:
        hazirlar = set(json.loads((paths.ROOT / "studio" / "remotion" / "hazirEfekt.json").read_text(encoding="utf-8")))
    except OSError:
        hazirlar = set()
    fontlar = set(json.loads((paths.FONTS_DIR / "fonts.json").read_text(encoding="utf-8")))
    gorulen = set()
    for e in d["stiller"]:
        k = e.get("id", "?")
        if not stil.AD.fullmatch(k) or k in gorulen:
            h.append(f"{k}: kimlik geçersiz ya da tekrar")
        gorulen.add(k)
        if e.get("kategori") not in d["kategoriler"]:
            h.append(f"{k}: bilinmeyen kategori {e.get('kategori')}")
        if e.get("tempo") not in TEMPO:
            h.append(f"{k}: tempo yavas|orta|hizli olmalı")
        if e.get("motion_tema"):
            h.append(f"{k}: motion_tema alanı kalktı (ADR 0043); kartın kendi paleti ve token bloğu olmalı")
        if not e.get("palet"):
            h.append(f"{k}: palet yok")
            continue
        try:
            h += tema_token.denetle(tema_token.karttan(e))
        except Exception as x:  # noqa: BLE001 - şema hatası katalog hatası olarak raporlanır
            h.append(f"{k}: token geçersiz: {x}")
        renk = palet(e)
        h += [f"{k}: renk {a} geçersiz: {renk.get(a)}" for a in RENKLER if not HEX.fullmatch(renk.get(a) or "")]
        h += [f"{k}: bilinmeyen geçiş ailesi {g}" for g in e.get("gecis", []) if g not in gecisler]
        h += [f"{k}: bilinmeyen hazır efekt {x}" for x in e.get("hazir", []) if hazirlar and x not in hazirlar]
        h += [f"{k}: bilinmeyen motion {x}" for x in e.get("motion", []) if x not in kimlikler]
        h += [f"{k}: font yok {f}" for f in (e.get("font") or {}).values() if f not in fontlar]
    return h


def tema_yaz(e: dict) -> Path:
    """Kartın temasını library/motion/tema/<id>.{css,json} olarak yazar (ADR 0043)."""
    css, _, t = tema_token.yaz(e)
    for n in t.notlar:
        print(f"  {e['id']}: kontrast {n}")
    return css


def _madde(liste: list[str]) -> str:
    return "\n".join(f"- {x}" for x in liste)


def paket(e: dict) -> dict[str, str]:
    """Karttan stil paketi: STYLE.md, MOTION.md, tokens.json (Türkçe düzyazı, style-pack düzeni)."""
    r, f = palet(e), e.get("font") or {}
    a, b = e.get("kesim") or [2.0, 4.0]
    tema = tema_adi(e)
    style = (
        f"# {e['ad']}\n\n"
        f"{e['ozet']}\n\n"
        f"Kaynak: {e['kaynak']} ({e['lisans']}). Hazır stil kataloğundan eklendi (ADR 0042); kural ölçülmüş referans değil, kaynağın tarifidir.\n\n"
        "## Ne zaman\n"
        f"{e['uygun']}\n\n"
        "## Görsel dil\n"
        f"{_madde(e['gorsel'])}\n\n"
        "## Palet\n"
        + "\n".join(f"- {ad}: `{r[ad]}`" for ad in RENKLER if ad in r)
        + f"\n- Motion teması: `{tema}` (grafikler bu renklerle gelir)\n\n"
        "## Tipografi\n"
        f"- Başlık: {f.get('baslik', 'Montserrat')} {e.get('agirlik', 800)}\n"
        f"- Gövde: {f.get('govde', 'Inter')}\n"
        + (f"- Kod: {f['mono']}\n" if f.get("mono") else "")
        + "- Altyazı stilin token'larını alır (ADR 0043): okunan kelime stilin vurgusu, gövde beyaz, koyu kontur; kutu, pop ve solma yok.\n\n"
        "## Kurgu\n"
        f"- Tempo {TEMPO[e['tempo']]}; ortalama çekim {a:g}-{b:g} sn.\n"
        f"- Geçiş aileleri: {', '.join(f'`{g}`' for g in e.get('gecis', [])) or 'düz kesim'}.\n"
        f"- Hazır efektler: {', '.join(f'`{x}`' for x in e.get('hazir', [])) or 'gerekirse'}.\n\n"
        "## Kaçın\n"
        f"{_madde(e['kacin'])}\n"
        + (f"\n## Üretilen görsel\nSahne görseli gerektiğinde (gorsel-uret) bu stil soneki kullanılır, yazı görsele gömülmez:\n\n"
           f"`{e['gorsel_prompt']}`\n" if e.get("gorsel_prompt") else "")
    )
    motion_md = (
        f"# {e['ad']}: hareket\n\n"
        f"Motion teması `{tema}`; kütüphanedeki her klip ve şablon bu temayla yeniden renklenir.\n\n"
        "## Hareket dili\n"
        f"{_madde(e['hareket'])}\n\n"
        "## Öncelikli kütüphane klipleri\n"
        f"{_madde([f'`{x}`' for x in e.get('motion', [])])}\n\n"
        "## Geçiş\n"
        + _madde([f"`{g}` (V1 `gecis_giris`)" if g in kurgu.ORTA_GECIS else f"`gecis-{g}-dikey` / `gecis-{g}-yatay`" for g in e.get("gecis", [])])
        + "\n\nAynı geçiş art arda iki kez kullanılmaz; geçişler konu değişiminde, kesim içinde değil.\n"
    )
    tokens = {
        "name": e["id"],
        "description": e["ozet"],
        "motion_tema": tema,
        "colors": {"bg": r.get("zemin"), "fg": r.get("yazi"), "muted": r.get("soluk"), "accent": r.get("vurgu"),
                   "accent2": r.get("ikincil"), "on_accent": r.get("zemin")},
        "fonts": {"display": f.get("baslik", "Montserrat"), "body": f.get("govde", "Inter"), "mono": f.get("mono", "JetBrains Mono")},
        "weights": {"display": e.get("agirlik", 800)},
        "tempo": {"kesim_sn": [a, b], "seviye": e["tempo"]},
        "gecis": e.get("gecis", []),
        "kaynak": e["kaynak"],
    }
    return {"STYLE.md": style, "MOTION.md": motion_md, "tokens.json": json.dumps(tokens, ensure_ascii=False, indent=1) + "\n"}


def ekle(studyo: str, kimlik: str, proje=None, *, uzerine: bool = False) -> Path:
    """Katalog stilini stüdyonun stil klasörüne yazar; `proje` verilirse o projede seçer. Var olan pakete dokunmaz."""
    e = bul(kimlik)
    hedef = stil.klasor(studyo, kimlik)
    if (hedef / "STYLE.md").exists() and not uzerine:
        raise SystemExit(f"Stil zaten var: {kimlik}. Stillerim listesinden düzenle ya da silip yeniden ekle.")
    tema_yaz(e)
    hedef.mkdir(parents=True, exist_ok=True)
    for ad, metin in paket(e).items():
        (hedef / ad).write_text(metin, encoding="utf-8")
    if proje is not None:
        stil.sec(proje, kimlik)
    return hedef


def onizleme_yolu(kimlik: str) -> Path:
    return kok() / "onizleme" / f"{kimlik}.jpg"


def ornek_yolu(kimlik: str) -> Path | None:
    # Kullanıcı başka uzantıyla yeniden yüklerse en yenisi geçerli olur.
    adaylar = [f for uz in (".jpg", ".png", ".webp") if (f := kok() / "ornek" / f"{kimlik}{uz}").is_file()]
    return max(adaylar, key=lambda f: f.stat().st_mtime) if adaylar else None


def liste() -> list[dict]:
    """Arayüz için kart özeti."""
    cikti = []
    for e in stiller():
        cikti.append({k: e.get(k) for k in ("id", "ad", "kategori", "kaynak", "lisans", "ozet", "uygun", "tempo", "gecis", "kacin")}
                     | {"palet": palet(e), "motion_tema": tema_adi(e), "font": e.get("font") or {},
                        "onizleme": onizleme_yolu(e["id"]).is_file(),
                        "kart": (kok() / "onizleme" / e["id"] / "kart.jpg").is_file()})
    return cikti


def kur(hedefler: list[str] | None = None, *, onizleme: bool = True) -> list[str]:
    """Temaları yazar ve önizleme kartlarını üretir. Hata listesi boş değilse durur."""
    if h := dogrula():
        raise SystemExit("Katalog geçersiz:\n  " + "\n  ".join(h))
    secilen = [bul(k) for k in hedefler] if hedefler else stiller()
    for e in secilen:
        print(f"  tema: {paths.rel(tema_yaz(e))}")
    if not hedefler:
        tema_token.ek_temalari_yaz()
    if onizleme:
        _onizlemeler(secilen)
    return [e["id"] for e in secilen]


# Önizleme kartı: örnek görsel (yoksa paletten gradyan) üstüne stilin temasıyla başlık ve alt bant şablonu.
KART = (540, 960)
SABLONLAR = (("baslik-acilis", 2.2, lambda e: {"ust": e["kategori"].upper()[:16], "metin": e["ad"][:40]}),
             ("altbant-konu", 2.6, lambda e: {"etiket": TEMPO[e["tempo"]].upper()[:14], "metin": e["uygun"].split(",")[0][:40]}))


def _zemin(e: dict):
    from PIL import Image, ImageDraw
    w, h = KART
    if (f := ornek_yolu(e["id"])):
        im = Image.open(f).convert("RGB")
        o = max(w / im.width, h / im.height)
        im = im.resize((round(im.width * o), round(im.height * o)))
        x, y = (im.width - w) // 2, (im.height - h) // 2
        return im.crop((x, y, x + w, y + h))
    r = palet(e)
    hx = lambda s: tuple(int(s[i:i + 2], 16) for i in (1, 3, 5))  # noqa: E731
    a, b = hx(r["zemin"]), hx(r["vurgu"])
    im = Image.new("RGB", KART, a)
    d = ImageDraw.Draw(im)
    for y in range(h):
        t = (y / h) ** 2 * 0.35
        d.line([(0, y), (w, y)], fill=tuple(round(a[i] * (1 - t) + b[i] * t) for i in range(3)))
    return im


def _onizlemeler(secilen: list[dict]) -> None:
    import tempfile

    from PIL import Image

    from . import hf_motion
    (kok() / "onizleme").mkdir(parents=True, exist_ok=True)
    for e in secilen:
        kart = _zemin(e).convert("RGBA")
        css = motion.tema_yolu(tema_adi(e))
        for ad, t, param in SABLONLAR:
            m = motion.meta(ad)
            tam = {k: pr["vars"] for k, pr in (m.get("param") or {}).items()} | param(e)
            # WHY: bkz. wiki/decisions/0051-uctan-uca-hyperframes.md. Şablonun saydam karesi HyperFrames'ten (eskiden Playwright).
            with tempfile.TemporaryDirectory() as d:
                png = hf_motion.kare_saydam(motion.kok() / ad / f"{ad}.html", Path(d) / "k.png", t=t, w=1080, h=1920, css=css, param=tam)
                kat = Image.open(png).convert("RGBA").resize(KART)
            kart.alpha_composite(kat)
        hedef = onizleme_yolu(e["id"])
        kart.convert("RGB").save(hedef, quality=86)
        print(f"  önizleme: {paths.rel(hedef)}")
