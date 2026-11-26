"""Stil token'ları: katalog kartından tek şema, tek CSS ve tek JSON; her render yolu bunu okur.

WHY: bkz. wiki/decisions/0043-stile-bagli-tema-tokenlari.md. Tema CSS'i yalnız renk ve font taşıyordu; stilin yapısı
(köşe, kontur, gölge türü, doku, adımlı hareket) hiçbir grafiğe ulaşmıyor, Remotion bileşenleri Montserrat ve turuncuyu
sabit yazıyordu. Kart (`library/stiller/katalog.json`) tek kaynaktır; `library/motion/tema/<id>.css` motion HTML'i,
`<id>.json` Remotion ve Python içindir. Kontrast ölçülür: yazı en az 4.5:1, vurgu ve yardımcı renkler en az 3:1.
"""

from __future__ import annotations

import colorsys
import json
import re
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from . import paths
from .tema import hex_, kontrast

HEX = re.compile(r"#[0-9A-Fa-f]{6}")
TURKCE = "şğıİçöüŞĞÇÖÜ"
YAZI_ESIK, VURGU_ESIK = 4.5, 3.0
# Eski ad → kanonik ad. Eski projelerin kurgu geçmişi eski adı taşır.
TAKMA = {"editorial-acik": "editoryal-acik"}


class _M(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Renk(_M):
    vurgu: str
    ikincil: str  # dolgu ve şekil rengi; stilin kimliği, kaydırılmaz
    ikincil_yazi: str  # ikincil renk yazı ya da ince çizgi olarak zeminde kullanılırsa (3:1'e kaydırılmış)
    zemin: str
    yazi: str
    soluk: str
    olumlu: str
    olumsuz: str
    ikon_kontur: str  # ikonun okunurluk konturu; şekil değil, ince dış çizgi
    ikon_golge: str  # drop-shadow rengi (rgba); arka plan şekli çizilmez


class Font(_M):
    baslik: str = "Montserrat"
    govde: str = "Inter"
    mono: str = "JetBrains Mono"
    rakam: str | None = None  # sayaç ve grafik rakamı; None: başlık fontu (Pixelify'da 5 ile S aynı, piksel stil VT323 kullanır)
    agirlik_baslik: int = Field(default=800, ge=100, le=900)
    agirlik_govde: int = Field(default=500, ge=100, le=900)
    izleme: float = 0.0  # em
    harf: Literal["normal", "buyuk"] = "normal"


class Sekil(_M):
    kose: int = Field(default=12, ge=0, le=64)
    cizgi: int = Field(default=6, ge=0, le=24)
    kontur: int = Field(default=0, ge=0, le=16)  # yazı ve şekil dış konturu (px)
    golge: Literal["yok", "yumusak", "sert", "glow"] = "yumusak"
    doku: Literal["yok", "gren", "kagit", "halftone", "tarama", "piksel"] = "yok"
    piksel: int = Field(default=1, ge=1, le=8)  # >1: grafik bu katsayıyla küçültülüp en yakın komşuyla büyütülür
    # İkon çizgi kalınlığı, 1080 px kısa kenarda (ADR 0045). None: cizgi'den türetilir. Telefonda okunması için en az 6.
    ikon_cizgi: float | None = Field(default=None, ge=6, le=24)


Bezier = tuple[float, float, float, float]


class Egri(_M):
    """Adlı easing eğrileri (ADR 0045). Bezier [x1, y1, x2, y2]; adim > 0 ise piksel stil gibi basamaklı (steps)."""
    enter: Bezier = (0.16, 1.0, 0.3, 1.0)
    exit: Bezier = (0.7, 0.0, 0.84, 0.0)
    emphasis: Bezier = (0.34, 1.56, 0.64, 1.0)
    settle: Bezier = (0.22, 1.0, 0.36, 1.0)
    adim: int | None = Field(default=None, ge=2, le=12)

    @field_validator("enter", "exit", "emphasis", "settle")
    @classmethod
    def _dogrusal_degil(cls, v: Bezier) -> Bezier:
        if not (0 <= v[0] <= 1 and 0 <= v[2] <= 1):
            raise ValueError("bezier x1 ve x2 0..1 arasında olmalı")
        if abs(v[0] - v[1]) < 1e-6 and abs(v[2] - v[3]) < 1e-6:
            raise ValueError("doğrusal eğri yasak (ADR 0045)")
        return v


class Hareket(_M):
    easing: Literal["yumusak", "keskin", "yay", "basamak"] = "keskin"
    sure_kat: float = Field(default=1.0, ge=0.5, le=2.0)
    davranis: Literal["yok", "titresim", "titreme-giris"] = "yok"
    adim_fps: int | None = Field(default=None, ge=4, le=30)  # adımlı hareket: zaman bu kare hızına yuvarlanır
    egri: Egri | None = None  # None: easing türünden türetilir (studio/remotion/tema.ts egriler)


class AltyaziToken(_M):
    font: str
    agirlik: int = Field(default=800, ge=100, le=900)
    renk: str
    aktif_renk: str
    kontur: int = Field(default=12, ge=0, le=24)
    kontur_renk: str
    kutu: bool = False
    pop: bool = False
    solma: bool = False


class Tokens(_M):
    ad: str
    renk: Renk
    font: Font
    sekil: Sekil
    hareket: Hareket
    altyazi: AltyaziToken
    gecis: list[str] = []
    kacin: list[str] = []
    notlar: list[str] = []  # üreticinin kontrast için yaptığı kaydırmalar


# ---------------------------------------------------------------- renk yardımcıları

def _rgb(h: str) -> tuple[int, int, int]:
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def _koyu(zemin: str) -> bool:
    return kontrast(_rgb(zemin), (255, 255, 255)) >= kontrast(_rgb(zemin), (0, 0, 0))


def kontrast_duzelt(renk: str, zemin: str, esik: float) -> str:
    """Rengin tonunu koruyup açıklığını zemine göre kaydırır, eşiğe ulaşınca durur."""
    r = _rgb(renk)
    if kontrast(r, _rgb(zemin)) >= esik:
        return renk.upper()
    h, l, s = colorsys.rgb_to_hls(*(v / 255 for v in r))
    yon = 1 if _koyu(zemin) else -1
    for _ in range(100):
        l = min(max(l + yon * 0.01, 0), 1)
        c = tuple(round(v * 255) for v in colorsys.hls_to_rgb(h, l, s))
        if kontrast(c, _rgb(zemin)) >= esik or l in (0, 1):
            return hex_(c)
    return hex_(c)


def _tonlu(ton: float, zemin: str) -> str:
    """Verilen tonda (derece) zemine 3:1 okunan doygun renk; olumlu/olumsuz yoksa türetilir."""
    c = tuple(round(v * 255) for v in colorsys.hls_to_rgb(ton / 360, 0.5, 0.75))
    return kontrast_duzelt(hex_(c), zemin, VURGU_ESIK)


def _rgba(h: str, a: float) -> str:
    r, g, b = _rgb(h)
    return f"rgba({r},{g},{b},{a})"


# ---------------------------------------------------------------- karttan token

def karttan(e: dict) -> Tokens:
    """Katalog kartı → token. Eksik yapı alanı tempodan ve kategoriden türetilir."""
    tk = e.get("token") or {}
    pal = dict(e["palet"])
    notlar: list[str] = []
    zemin = pal["zemin"].upper()
    for ad, esik in (("yazi", YAZI_ESIK), ("vurgu", VURGU_ESIK), ("soluk", VURGU_ESIK)):
        yeni = kontrast_duzelt(pal[ad], zemin, esik)
        if yeni != pal[ad].upper():
            notlar.append(f"{ad} {pal[ad]} → {yeni} (zemine {esik}:1)")
        pal[ad] = yeni
    ek = tk.get("renk") or {}
    olumlu = kontrast_duzelt(ek["olumlu"], zemin, VURGU_ESIK) if ek.get("olumlu") else _tonlu(142, zemin)
    olumsuz = kontrast_duzelt(ek["olumsuz"], zemin, VURGU_ESIK) if ek.get("olumsuz") else _tonlu(356, zemin)
    renk = Renk(vurgu=pal["vurgu"], ikincil=pal["ikincil"].upper(), ikincil_yazi=kontrast_duzelt(pal["ikincil"], zemin, VURGU_ESIK), zemin=zemin, yazi=pal["yazi"], soluk=pal["soluk"],
                olumlu=olumlu, olumsuz=olumsuz, ikon_kontur=zemin, ikon_golge=_rgba(zemin if _koyu(zemin) else "#000000", 0.45))
    f = e.get("font") or {}
    font = Font(baslik=f.get("baslik", "Montserrat"), govde=f.get("govde", "Inter"), mono=f.get("mono", "JetBrains Mono"),
                agirlik_baslik=e.get("agirlik", 800), **(tk.get("font") or {}))
    sekil = Sekil(kose=e.get("kose", 12), cizgi=e.get("cizgi", 6), **(tk.get("sekil") or {}))
    hareket = Hareket(**({"sure_kat": {"yavas": 1.2, "orta": 1.0, "hizli": 0.85}[e.get("tempo", "orta")]} | (tk.get("hareket") or {})))
    altyazi = altyazi_tokeni(renk, font, tk.get("altyazi") or {})
    return Tokens(ad=e["id"], renk=renk, font=font, sekil=sekil, hareket=hareket, altyazi=altyazi,
                  gecis=list(e.get("gecis", [])), kacin=list(e.get("kacin", [])), notlar=notlar)


def altyazi_tokeni(renk: Renk, font: Font, ek: dict) -> AltyaziToken:
    """Stilli altyazı: video üstünde okunur kalsın diye beyaz gövde, koyu kontur; okunan kelime stilin vurgusu.

    WHY: bkz. wiki/decisions/0043-stile-bagli-tema-tokenlari.md (ADR 0014 güncellemesi). Kutu, pop ve solma yalnız
    stil açıkça isterse açılır. Aktif renk kontur rengine en az 4.5:1 kaydırılır.
    """
    kontur_renk = ek.get("kontur_renk", "#000000")
    aktif = kontrast_duzelt(ek.get("aktif_renk", renk.vurgu), kontur_renk, YAZI_ESIK)
    govde = kontrast_duzelt(ek.get("renk", "#FFFFFF"), kontur_renk, YAZI_ESIK)
    # Serif ve el yazısı başlık fontu altyazıda okunmaz; stil ayrıca istemedikçe gövde fontu kullanılır.
    secilen = ek.get("font") or (font.baslik if font.baslik in ("Montserrat", "Outfit", "Space Grotesk", "Inter", "Bungee", "Pixelify Sans") else font.govde)
    return AltyaziToken(font=secilen, agirlik=ek.get("agirlik", 800), renk=govde, aktif_renk=aktif,
                        # 12 px kontur Montserrat'a göre; dar harfli fontlarda harfleri yapıştırır, stilli altyazıda 8 px
                        kontur=ek.get("kontur", 8), kontur_renk=kontur_renk,
                        kutu=bool(ek.get("kutu")), pop=bool(ek.get("pop")), solma=bool(ek.get("solma")))


def cssden(css: Path, ad: str) -> Tokens:
    """Kartı olmayan tema (varsayilan, turuncu, ek temalar, proje teması): CSS değişkenlerinden varsayılan yapı."""
    v = dict(re.findall(r"--([a-z-]+)\s*:\s*([^;}\n]+)", css.read_text(encoding="utf-8")))
    pal = {k: v[k].strip() for k in ("vurgu", "ikincil", "zemin", "yazi", "soluk")}
    m = re.match(r"\s*'?([^',]+)'?", v.get("font", "'Montserrat'"))
    e = {"id": ad, "palet": pal, "font": {"baslik": m.group(1).strip() if m else "Montserrat"},
         "agirlik": int(v.get("agirlik", 800)), "kose": int(re.sub(r"\D", "", v.get("kose", "12")) or 12),
         "cizgi": int(re.sub(r"\D", "", v.get("cizgi", "6")) or 6)}
    t = karttan(e)
    if ad in ("varsayilan", "turuncu"):
        # ADR 0014: stil seçilmemiş videoda altyazı standardı aynen sürer.
        t.altyazi = AltyaziToken(font="Montserrat", agirlik=800, renk="#FFFFFF", aktif_renk="#FF7A00", kontur=12, kontur_renk="#000000")
    return t


# ---------------------------------------------------------------- CSS ve JSON

EASING = {
    "yumusak": ("cubic-bezier(.45,0,.2,1)", "cubic-bezier(.5,0,.75,0)"),
    "keskin": ("cubic-bezier(.16,1,.3,1)", "cubic-bezier(.7,0,.84,0)"),
    "yay": ("cubic-bezier(.34,1.56,.64,1)", "cubic-bezier(.36,0,.66,-.56)"),
    "basamak": ("steps(4,end)", "steps(3,end)"),
}
_GREN = ("url(\"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='160' height='160'><filter id='n'>"
         "<feTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='2' stitchTiles='stitch'/></filter>"
         "<rect width='100%' height='100%' filter='url(%23n)' opacity='.22'/></svg>\")")
_KAGIT = _GREN.replace(".9' numOctaves='2'", ".035' numOctaves='4'").replace("opacity='.22'", "opacity='.18'")


def golge(t: Tokens) -> tuple[str, str]:
    """(box/text gölgesi, filter drop-shadow). Şekil çizmez; yalnız mevcut biçimin gölgesi."""
    r, s = t.renk, t.sekil
    if s.golge == "yumusak":
        return "0 10px 28px rgba(0,0,0,.35)", "drop-shadow(0 8px 16px rgba(0,0,0,.35))"
    if s.golge == "sert":
        k = max(4, s.cizgi)
        c = "#000000" if _koyu(r.zemin) else r.yazi
        return f"{k}px {k}px 0 {c}", f"drop-shadow({k}px {k}px 0 {c})"
    if s.golge == "glow":
        return f"0 0 18px {_rgba(r.vurgu, .55)}, 0 0 4px {_rgba(r.vurgu, .9)}", f"drop-shadow(0 0 10px {_rgba(r.vurgu, .7)})"
    return "none", "none"


def doku(t: Tokens) -> str:
    r = t.renk
    return {
        "gren": _GREN, "kagit": _KAGIT,
        "halftone": f"radial-gradient({_rgba(r.yazi, .18)} 22%, transparent 24%) 0 0/14px 14px",
        "tarama": f"repeating-linear-gradient(0deg, {_rgba('#000000', .22)} 0 2px, transparent 2px 5px)",
    }.get(t.sekil.doku, "none")


def _yigin(ad: str) -> str:
    """Font yığını: serif ve el yazısı doğru yedeğe düşer."""
    yedek = {"Fraunces": "serif", "Playfair Display": "serif", "EB Garamond": "serif", "Caveat": "cursive",
             "JetBrains Mono": "monospace", "VT323": "monospace"}.get(ad, "sans-serif")
    return f"'{ad}',{yedek}"


def ustu(dolgu: str, r: Renk) -> str:
    return max((r.zemin, r.yazi, "#000000", "#FFFFFF"), key=lambda c: (round(kontrast(_rgb(c), _rgb(dolgu)), 1), c in (r.zemin, r.yazi)))


def _rgb_str(h: str) -> str:
    r, g, b = _rgb(h)
    return f"{r} {g} {b}"


def _bezier_css(b: Bezier | None, yedek: str) -> str:
    if not b:
        return yedek
    return f"cubic-bezier({b[0]:g},{b[1]:g},{b[2]:g},{b[3]:g})"


def css_metni(t: Tokens, baslik: str = "") -> str:
    r, f, s, h = t.renk, t.font, t.sekil, t.hareket
    gol, filt = golge(t)
    gir, cik = EASING[h.easing]
    eg = h.egri
    piksel_mod = s.doku == "piksel" or s.piksel > 1
    if piksel_mod:
        e_enter = e_exit = e_emph = e_settle = f"steps({eg.adim if eg and eg.adim else 4},end)"
        yuzey_cam = r.zemin
        kenar_ince = f"{max(2, s.kontur)}px solid {r.yazi}"
        yukselti_golge = gol
        izgara_desen = "none"
    else:
        e_enter = _bezier_css(eg.enter if eg else None, gir)
        e_exit = _bezier_css(eg.exit if eg else None, cik)
        e_emph = _bezier_css(eg.emphasis if eg else None, "cubic-bezier(.34,1.56,.64,1)")
        e_settle = _bezier_css(eg.settle if eg else None, "cubic-bezier(.22,1,.36,1)")
        yuzey_cam = _rgba(r.zemin, 0.78)
        kenar_ince = f"1px solid {_rgba(r.yazi, 0.14)}"
        yukselti_golge = f"0 2px 6px rgba(0,0,0,.22), 0 14px 34px rgba(0,0,0,.32), inset 0 1px 0 {_rgba(r.yazi, 0.14)}"
        izgara_desen = f"radial-gradient({_rgba(r.yazi, 0.14)} 1.2px, transparent 1.2px) 0 0/28px 28px"
    d = {
        **{k: getattr(r, k) for k in ("vurgu", "ikincil", "zemin", "yazi", "soluk", "olumlu", "olumsuz")},
        **{f"{k}-rgb": _rgb_str(getattr(r, k)) for k in ("vurgu", "ikincil", "zemin", "yazi", "soluk", "olumlu", "olumsuz")},
        "ikincil-yazi": r.ikincil_yazi,
        # Dolgunun üstündeki yazı: zemin, yazı, siyah ve beyazdan dolguya en yüksek kontrastlı olan (etiket, rozet, buton).
        "vurgu-ustu": ustu(r.vurgu, r), "ikincil-ustu": ustu(r.ikincil, r),
        "ikon-kontur": r.ikon_kontur, "ikon-golge": r.ikon_golge,
        "font": _yigin(f.baslik), "font-govde": _yigin(f.govde), "font-mono": _yigin(f.mono), "font-rakam": _yigin(f.rakam or f.baslik),
        "agirlik": f.agirlik_baslik, "agirlik-govde": f.agirlik_govde, "izleme": f"{f.izleme}em",
        "harf": "uppercase" if f.harf == "buyuk" else "none",
        "kose": f"{s.kose}px", "cizgi": f"{s.cizgi}px", "kontur": f"{s.kontur}px",
        # Köşesiz stilde (piksel, brutalist, bauhaus) çizgi ucu ve birleşimi de köşeli olur.
        "ucu": "square" if s.kose == 0 else "round", "birlesim": "miter" if s.kose == 0 else "round",
        "golge": gol, "golge-filtre": filt, "doku": doku(t),
        "yuzey-cam": yuzey_cam, "kenar-ince": kenar_ince, "yukselti-golge": yukselti_golge, "izgara-desen": izgara_desen,
        "ease": gir, "ease-cik": cik, "ease-enter": e_enter, "ease-exit": e_exit, "ease-emphasis": e_emph, "ease-settle": e_settle,
        "sure-kat": h.sure_kat, "adim-fps": h.adim_fps or 0,
    }
    kurallar = ":root{" + ";".join(f"--{k}:{v}" for k, v in d.items()) + "}"
    # Yapı sınıfları: şablon gövdesi bunları kullanır; şekil çizmez, var olan biçimi stile uydurur.
    kurallar += (".tema-golge{filter:var(--golge-filtre)}.tema-yazi{text-transform:var(--harf);letter-spacing:var(--izleme)}"
                 ".tema-doku{background:var(--doku);mix-blend-mode:overlay}")
    if s.doku == "piksel" or s.piksel > 1:
        kurallar += "svg *{shape-rendering:crispEdges}img,canvas{image-rendering:pixelated}*{-webkit-font-smoothing:none}"
    if h.davranis == "titreme-giris":
        kurallar += ("@keyframes tema-titreme{0%,8%,14%{opacity:.25}4%,11%,100%{opacity:1}}"
                     "body>*{animation:tema-titreme .45s steps(1,end) both}")
    return (f"/* {baslik} Üreten: vedit stil-katalog kur (ADR 0043); elle düzenleme, kartı değiştir. */\n" if baslik else "") + kurallar + "\n"


def pano_css(t: Tokens) -> str:
    """Açıklama panoları (library/boards, vendor): .ebs değişkenlerini stilin token'ıyla ezer."""
    r, f, s = t.renk, t.font, t.sekil
    gol = golge(t)[0]
    return (".ebs{" + ";".join([
        f"--space:{_yigin(f.baslik)}", f"--mono:{_yigin(f.mono)}", f"--hand:{_yigin(f.govde)}",
        f"--ink:{r.yazi}", f"--paper:{r.zemin}", f"--wash:{_karisim(r.zemin, r.yazi, .06)}", f"--line:{_karisim(r.zemin, r.yazi, .2)}",
        f"--indigo:{r.vurgu}", f"--indigo-l:{_karisim(r.zemin, r.vurgu, .14)}", f"--mint:{r.ikincil_yazi}", f"--mint-l:{_karisim(r.zemin, r.ikincil, .16)}",
        f"--hi:{_karisim(r.zemin, r.vurgu, .22)}", f"--sticker:{_karisim(r.zemin, r.ikincil, .2)}",
        f"--sh-soft:{gol}", f"--sh-film:{gol}", f"background:{r.zemin}!important", f"color:{r.yazi}"]) + "}"
        f".ebs .card,.ebs .tbl,.ebs .swatch,.ebs .film,.ebs .image{{border-radius:{s.kose}px!important;box-shadow:{gol}!important}}"
        f".ebs .title{{text-transform:{'uppercase' if f.harf == 'buyuk' else 'none'};font-weight:{f.agirlik_baslik}}}\n")


def _karisim(a: str, b: str, k: float) -> str:
    x, y = _rgb(a), _rgb(b)
    return hex_(tuple(round(x[i] + (y[i] - x[i]) * k) for i in range(3)))


def tema_klasoru() -> Path:
    return paths.MOTION_DIR / "tema"


def yaz(e: dict) -> tuple[Path, Path, Tokens]:
    t = karttan(e)
    k = tema_klasoru()
    css = k / f"{e['id']}.css"
    css.write_text(css_metni(t, f"{e['ad']}: {e['ozet']} Kaynak: {e['kaynak']} ({e['lisans']})."), encoding="utf-8")
    js = k / f"{e['id']}.json"
    js.write_text(json.dumps(t.model_dump(), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return css, js, t


def ek_temalari_yaz() -> list[Path]:
    """Kartı olmayan temalar (varsayilan, turuncu, ek temalar): JSON ve tam biçimli CSS.

    CSS de yeniden yazılır: şablonlar `--ease`, `--ucu`, `--ikon-kontur` gibi yapı değişkenlerini kullanır; eski biçimde
    eksik değişken animasyonu geçersiz kılar. Renk ve font eski CSS'ten okunur, baştaki açıklama korunur (idempotent).
    """
    from .stil_katalog import stiller
    kartli = {e["id"] for e in stiller()}
    yazilan = []
    for css in sorted(tema_klasoru().glob("*.css")):
        if css.stem in kartli:
            continue
        js = css.with_suffix(".json")
        if js.is_file() and css.stem.startswith("paket-"):
            continue  # paketten üretilen tema: JSON kaynağıdır, CSS'ten yeniden türetilmez
        t = cssden(css, css.stem)
        eski = css.read_text(encoding="utf-8")
        m = re.match(r"\s*/\*(.*?)\*/", eski, flags=re.S)
        aciklama = re.sub(r"\s*Üreten: vedit stil-katalog kur \(ADR 0043\); elle düzenleme, kartı değiştir\.\s*$", "", m.group(1).strip()) if m else css.stem
        css.write_text(css_metni(t, aciklama), encoding="utf-8")
        js.write_text(json.dumps(t.model_dump(), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        yazilan.append(js)
    return yazilan


def oku(tema: str | Path | None) -> Tokens | None:
    """Tema adı ya da CSS yolu → token. JSON yanındaysa o, yoksa CSS'ten türetilir; tema yoksa None."""
    if tema is None:
        return None
    if isinstance(tema, Path):
        css = tema if tema.is_file() else None
        ad = tema.stem
    else:
        ad = TAKMA.get(tema, tema)
        css = tema_klasoru() / f"{ad}.css"
        css = css if css.is_file() else None
    if css is None:
        return None
    js = css.with_suffix(".json")
    if js.is_file():
        return Tokens.model_validate_json(js.read_text(encoding="utf-8"))
    return cssden(css, ad)


def yapi(css: Path | None) -> dict:
    """Pano render'ının uyguladığı yapı: adımlı zaman ve piksel katsayısı."""
    t = oku(css) if css else None
    if not t:
        return {"adim_fps": None, "piksel": 1}
    return {"adim_fps": t.hareket.adim_fps, "piksel": t.sekil.piksel}


# ---------------------------------------------------------------- denetim

def font_kayitlari() -> dict:
    return {k: v for k, v in json.loads((paths.FONTS_DIR / "fonts.json").read_text(encoding="utf-8")).items() if not k.startswith("_")}


def turkce_eksik(ad: str) -> str:
    from fontTools.ttLib import TTFont
    c = TTFont(paths.FONTS_DIR / font_kayitlari()[ad]["file"]).getBestCmap()
    return "".join(g for g in TURKCE if ord(g) not in c)


def denetle(t: Tokens) -> list[str]:
    h: list[str] = []
    r = t.renk
    for ad in ("vurgu", "ikincil", "ikincil_yazi", "zemin", "yazi", "soluk", "olumlu", "olumsuz", "ikon_kontur"):
        if not HEX.fullmatch(getattr(r, ad)):
            h.append(f"{t.ad}: renk {ad} geçersiz")
    if h:
        return h
    z = _rgb(r.zemin)
    if kontrast(_rgb(r.yazi), z) < YAZI_ESIK:
        h.append(f"{t.ad}: yazı/zemin kontrastı {kontrast(_rgb(r.yazi), z):.2f} < {YAZI_ESIK}")
    for ad in ("vurgu", "ikincil_yazi", "soluk", "olumlu", "olumsuz"):
        if (k := kontrast(_rgb(getattr(r, ad)), z)) < VURGU_ESIK:
            h.append(f"{t.ad}: {ad}/zemin kontrastı {k:.2f} < {VURGU_ESIK}")
    a = t.altyazi
    for ad in ("renk", "aktif_renk"):
        if (k := kontrast(_rgb(getattr(a, ad)), _rgb(a.kontur_renk))) < YAZI_ESIK:
            h.append(f"{t.ad}: altyazı {ad}/kontur kontrastı {k:.2f} < {YAZI_ESIK}")
    kayit = font_kayitlari()
    for f in {t.font.baslik, t.font.govde, t.font.mono, t.font.rakam or t.font.baslik, a.font}:
        if f not in kayit:
            h.append(f"{t.ad}: font kayıtlı değil: {f}")
        elif eksik := turkce_eksik(f):
            h.append(f"{t.ad}: {f} Türkçe glif eksik: {eksik}")
    return h


def paketten_yaz(k: Path) -> str:
    """Elle ya da `stil-uret` ile yazılmış stil paketinin `tokens.json` renklerinden kendi temasını üretir.

    WHY: ADR 0043. Paketi başka bir temaya eşlemek stilin rengini kaybettirir; paket kendi paletiyle temalanır.
    Tema adı `paket-<stüdyo>-<ad>`; `tokens.json`'a `motion_tema` olarak yazılır. Ad katalog kimlikleriyle çakışmaz.
    """
    veri = json.loads((k / "tokens.json").read_text(encoding="utf-8"))
    c, f = veri.get("colors") or {}, veri.get("fonts") or {}
    gerek = {"vurgu": c.get("accent"), "zemin": c.get("bg"), "yazi": c.get("fg")}
    if not all(isinstance(v, str) and HEX.fullmatch(v) for v in gerek.values()):
        raise SystemExit(f"{paths.rel(k)}: tokens.json colors.accent/bg/fg hex olmalı")
    ikincil = next((v for v in (c.get("accent2"), c.get("brand2"), c.get("brand")) if isinstance(v, str) and HEX.fullmatch(v)), gerek["vurgu"])
    soluk = c.get("muted") if isinstance(c.get("muted"), str) and HEX.fullmatch(c["muted"]) else gerek["yazi"]
    kayit = font_kayitlari()
    font = {r: f[a] for r, a in (("baslik", "display"), ("govde", "body"), ("mono", "mono")) if f.get(a) in kayit}
    ad = f"paket-{k.parent.parent.name}-{k.name}"
    e = {"id": ad, "ad": veri.get("name", k.name), "ozet": (veri.get("description") or "")[:160], "kaynak": paths.rel(k / "tokens.json"),
         "lisans": "proje", "palet": {**gerek, "ikincil": ikincil, "soluk": soluk}, "font": font,
         "agirlik": (veri.get("weights") or {}).get("display", 800), "kose": round(12 * float(veri.get("radius_u", 1))), "cizgi": 4,
         "token": {"sekil": {"golge": "glow" if c.get("glow") else "yumusak", "doku": "gren" if veri.get("grain") else "yok"}}}
    yaz(e)
    veri["motion_tema"] = ad
    (k / "tokens.json").write_text(json.dumps(veri, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return ad


def eksik_temalar() -> list[str]:
    """Teması (CSS + JSON) olmayan ya da kartıyla uyuşmayan katalog stilleri ve çözülemeyen stil paketleri.

    WHY: ADR 0043. `vedit kontrol` (tests/test_tema_token.py) bunu boş ister: hiçbir stil başka temaya düşmez.
    """
    from . import motion, stil
    from .stil_katalog import stiller
    h: list[str] = []
    for e in stiller():
        css, js = tema_klasoru() / f"{e['id']}.css", tema_klasoru() / f"{e['id']}.json"
        if not css.is_file() or not js.is_file():
            h.append(f"{e['id']}: tema dosyası yok (vedit stil-katalog kur)")
        elif Tokens.model_validate_json(js.read_text(encoding="utf-8")) != karttan(e):
            h.append(f"{e['id']}: tema kartla uyuşmuyor (vedit stil-katalog kur)")
    for k in sorted(paths.STUDIOS.glob("*/styles/*/tokens.json")):
        t = stil.motion_temasi(k.parent)
        if not t or not motion.tema_yolu(t):
            h.append(f"{paths.rel(k.parent)}: motion teması çözülemiyor ({t})")
    return h
