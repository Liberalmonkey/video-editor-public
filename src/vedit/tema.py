"""Videodan motion teması: girdinin baskın renklerinden `work/edit/motion_tema.css` yazar.

WHY: bkz. wiki/decisions/0042-stil-katalogu-ve-video-temasi.md. Stil seçilmemiş videoda motion grafiği hep turuncu
(`varsayilan`) geliyordu. Aynı animasyon tekniği kalır; vurgu, ikincil ve zemin rengi videonun kendi paletinden gelir.
Okunurluk ölçülür: vurgu zeminde en az 3:1, yazı en az 4.5:1 kontrast.
"""

from __future__ import annotations

import colorsys
import json
import re
import subprocess
from pathlib import Path


from .tembel import Tembel

# WHY: Stüdyo açılışında yüklenmesin (ADR 0050)
np = Tembel("numpy")

from . import ff, hizli, paths

KARE = 10  # video başına örnek kare
KUCUK = (48, 27)  # örnek karenin piksel boyutu; renk kümesi için yeter


def _kareler(f: Path) -> np.ndarray:
    """Videodan eşit aralıklı KARE kare (görselden tek kare), küçültülmüş RGB pikseller (N, 3)."""
    w, h = KUCUK
    if f.suffix.lower() in hizli.GORSEL:
        filtre, giris = f"scale={w}:{h}", ["-i", str(f)]
    else:
        sure = ff.probe(f).get("duration") or 1.0
        filtre, giris = f"fps={KARE / max(sure, 0.1):.5f},scale={w}:{h}", ["-i", str(f)]
    r = subprocess.run(["ffmpeg", "-v", "error", *giris, "-vf", filtre, "-frames:v", str(KARE),
                        "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True)
    if r.returncode or not r.stdout:
        return np.zeros((0, 3))
    return np.frombuffer(r.stdout, dtype=np.uint8).reshape(-1, 3).astype(float)


def kumele(px: np.ndarray, k: int = 8, tur: int = 12) -> list[tuple[tuple[int, int, int], float]]:
    """Deterministik k-ortalama: (renk, ağırlık) listesi, ağırlığa göre azalan."""
    if not len(px):
        return []
    sira = np.argsort(px.sum(axis=1))
    merkez = px[sira[np.linspace(0, len(px) - 1, k).astype(int)]].copy()  # parlaklık sırasına yayılmış başlangıç
    for _ in range(tur):
        etiket = ((px[:, None, :] - merkez[None]) ** 2).sum(-1).argmin(1)
        for i in range(k):
            if (sec := px[etiket == i]).size:
                merkez[i] = sec.mean(0)
    agirlik = np.bincount(etiket, minlength=k) / len(px)
    cikti = [(tuple(int(round(v)) for v in merkez[i]), float(agirlik[i])) for i in range(k) if agirlik[i] > 0]
    return sorted(cikti, key=lambda x: -x[1])


def _hsv(c) -> tuple[float, float, float]:
    return colorsys.rgb_to_hsv(*(v / 255 for v in c))


def _rgb(h: float, s: float, v: float) -> tuple[int, int, int]:
    return tuple(int(round(x * 255)) for x in colorsys.hsv_to_rgb(h % 1, min(max(s, 0), 1), min(max(v, 0), 1)))


def parlaklik(c) -> float:
    """WCAG göreli parlaklık."""
    def kanal(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (kanal(x) for x in c)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def kontrast(a, b) -> float:
    la, lb = sorted((parlaklik(a), parlaklik(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def hex_(c) -> str:
    return "#{:02X}{:02X}{:02X}".format(*c)


def _ton_farki(a: float, b: float) -> float:
    d = abs(a - b) % 1
    return min(d, 1 - d) * 360


def palet_kur(kumeler: list[tuple[tuple[int, int, int], float]]) -> dict[str, str]:
    """Kümelerden tema değişkenleri. Doygun renk yoksa (gri video) soğuk camgöbeği vurgu; turuncuya düşmez."""
    if not kumeler:
        kumeler = [((20, 24, 30), 1.0)]
    # Zemin: en koyu belirgin küme, tonu korunur, panel olarak okunacak kadar koyulaştırılır.
    koyu = min((c for c, a in kumeler if a >= 0.04) or [kumeler[0][0]], key=parlaklik)
    zh, zs, _ = _hsv(koyu)
    zemin = _rgb(zh, min(zs, 0.45), 0.09)
    # Vurgu: ağırlık × doygunluk × parlaklık en yüksek küme; doygunluk ve parlaklık yükseltilir.
    adaylar = sorted(((a ** 0.5) * _hsv(c)[1] * _hsv(c)[2], c) for c, a in kumeler if a >= 0.015)
    puan, kaynak = adaylar[-1] if adaylar else (0, (62, 230, 201))
    if puan < 0.12 or _hsv(kaynak)[1] < 0.22:
        # Soluk video: vurgu görüntünün baskın tonunun karşıtıdır ki grafik görüntüden ayrışsın.
        # Karşıt ton turuncu bandına (20-45°) düşerse camgöbeğine kayar: turuncu altyazının rengidir.
        x = sum(a * np.cos(2 * np.pi * _hsv(c)[0]) for c, a in kumeler)
        y = sum(a * np.sin(2 * np.pi * _hsv(c)[0]) for c, a in kumeler)
        karsit = (np.arctan2(y, x) / (2 * np.pi) + 0.5) % 1
        if 20 <= karsit * 360 <= 45:
            karsit = 186 / 360
        kaynak = _rgb(karsit, 0.75, 0.95)
    vh, vs, vv = _hsv(kaynak)
    vurgu = _rgb(vh, max(vs, 0.72), max(vv, 0.92))
    while kontrast(vurgu, zemin) < 3 and vv < 1:
        vv = min(vv + 0.05, 1)
        vurgu = _rgb(vh, max(vs, 0.72), max(vv, 0.92))
    # İkincil: vurgudan en az 40° ayrı ikinci doygun küme, yoksa tamamlayıcıya yakın (150°) ton.
    ikinci = [c for _, c in reversed(adaylar) if _ton_farki(_hsv(c)[0], vh) >= 40 and _hsv(c)[1] >= 0.25]
    ih = _hsv(ikinci[0])[0] if ikinci else vh + 150 / 360
    if 20 <= (ih % 1) * 360 <= 45 and not 20 <= vh * 360 <= 45:
        ih = 50 / 360  # turuncu yerine sıcak altın; turuncu altyazıyla yarışmasın
    ikincil = _rgb(ih, 0.62, 0.96)
    yazi = (255, 255, 255) if kontrast((255, 255, 255), zemin) >= 4.5 else (12, 12, 14)
    soluk = _rgb(zh, min(zs, 0.18), 0.68)
    return {"vurgu": hex_(vurgu), "ikincil": hex_(ikincil), "zemin": hex_(zemin), "yazi": hex_(yazi), "soluk": hex_(soluk)}


def girdiler(p) -> list[Path]:
    if not p.girdi.is_dir():
        return []
    return sorted((f for f in p.girdi.iterdir() if f.is_file() and f.suffix.lower() in hizli.VIDEO | hizli.GORSEL),
                  key=lambda f: hizli.dogal(f.name))


def cikar(p, *, font: str = "'Montserrat',sans-serif", agirlik: int = 800) -> Path:
    """Projenin girdi videolarından temayı çıkarır, `work/edit/motion_tema.css` yazar."""
    dosyalar = girdiler(p)
    if not dosyalar:
        raise SystemExit(f"Girdi yok: {paths.rel(p.girdi)}")
    px = np.concatenate([_kareler(f) for f in dosyalar[:6]])
    renk = palet_kur(kumele(px))
    hedef = p.work / "edit" / "motion_tema.css"
    hedef.parent.mkdir(parents=True, exist_ok=True)
    # WHY: bkz. wiki/decisions/0051-uctan-uca-hyperframes.md. Eskiden yalnız 5 renk ve font yazılırdı; HyperFrames grafikleri
    # ve motion kayıtları tema.css'teki öteki değişkenleri (vurgu-ustu, olumlu, ikon-kontur, ease, gölge...) kendi yedeğine,
    # çoğu turuncuya düşürüyordu. Palet stil kartı gibi karttan geçer: tam token (JSON) ve tam CSS yazılır.
    from . import tema_token
    ad = re.match(r"\s*'?([^',]+)'?", font)
    e = {"id": f"proje-{p.ad}", "palet": renk, "font": {"baslik": ad.group(1).strip() if ad else font},
         "agirlik": agirlik, "kose": 16, "cizgi": 8}
    t = tema_token.karttan(e)
    hedef.write_text(tema_token.css_metni(t, f"Proje teması: {p.studyo}/{p.ad} girdisinin baskın renklerinden (vedit tema-cikar, ADR 0042)."),
                     encoding="utf-8")
    hedef.with_suffix(".json").write_text(json.dumps(t.model_dump(), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    for n in tema_token.denetle(t):
        print(f"  uyarı: {n}")
    print(f"Yazıldı: {paths.rel(hedef)}  " + "  ".join(f"{a} {v}" for a, v in renk.items()))
    return hedef
