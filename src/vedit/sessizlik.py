"""Kesim önerileri: konuşmalı kliplerde sessizlik ve dolgu sözcükleri (sekans zamanında, uygulamaz).

# WHY: bkz. wiki/decisions/0024-oneri-araclari.md — öneri yalnız aday listesidir, kurgu.json'a yazılmaz.
"""

from __future__ import annotations

import re


from .tembel import Tembel

# WHY: Stüdyo açılışında yüklenmesin (ADR 0050)
np = Tembel("numpy")

from . import audio, kurgu
from .schemas import Kurgu

ESIK_DB = -40.0   # bunun altı sessizlik sayılır
ALT_DB = 20.0     # ya da konuşma düzeyinin bu kadar altı
PENCERE = 0.02    # enerji karesi, sn
# Tutucu dolgu listesi: yalnız anlamı olmayan sesler. "şey", "yani", "like" gibi anlamlı olabilen sözcükler bilerek yok.
DOLGU = re.compile(r"ı{2,}|e{2,}|eh+|hm+|m{2,}|u+m+|u+h+|e+rm+")


def _dolgu(w: str) -> str | None:
    t = re.sub(r"[^\w]", "", w.replace("I", "ı").casefold())  # Türkçe büyük I → ı
    return t if DOLGU.fullmatch(t) else None


def _sn(x: float) -> str:
    return f"{x:.1f}".replace(".", ",")


def _db(x: np.ndarray) -> float:
    return float(20 * np.log10(np.sqrt((x ** 2).mean()) + 1e-12)) if len(x) else -120.0


def _konusan(k: Kurgu):
    for c in k.klipler:
        if not c.kaynak:
            continue
        if c.tur == "video" and k.kaynaklar[c.kaynak].ses and not c.ses_kapali:
            yield c
        elif c.tur == "ses" and (c.olay or {}).get("konusma"):
            yield c


def _ses(p, yol: str) -> np.ndarray | None:
    """Kaynağın mono sesi; çözülemezse None (yalnız kelime boşluklarına düşülür)."""
    try:
        return audio._decode(kurgu.dosya(p, yol), p.work / "cache" / "ses").mean(axis=1)
    except Exception:
        return None


def oneriler(p, k: Kurgu, *, min_sessizlik: float = 0.6, pay: float = 0.12) -> list[dict]:
    kare = 1 / k.sekans.fps
    adaylar: list[dict] = []
    for c in _konusan(k):
        bit = c.giris + c.sure * c.hiz
        sek = lambda t: c.bas + (t - c.giris) / c.hiz  # noqa: E731 — kaynak → sekans, kurgu.izdusum kuralı
        ses = _ses(p, k.kaynaklar[c.kaynak].yol)
        parca = lambda a, b: ses[int(a * audio.SR):int(b * audio.SR)]  # noqa: E731

        def ekle(a, b, tur, neden):
            a, b = max(a, c.bas), min(b, c.bas + c.sure)
            if b - a >= kare:
                adaylar.append({"bas": round(a, 3), "bit": round(b, 3), "tur": tur, "klip": c.id, "neden": neden})

        # görünen aralığa taşan kelime de boşluğu sınırlar; uçlar aralığa kırpılır
        kelimeler = [(w.w, max(w.s, c.giris), min(w.e, bit)) for w in k.kelimeler.get(c.kaynak, []) if w.e > c.giris and w.s < bit]
        if kelimeler:
            esik = ESIK_DB
            if ses is not None:
                konusma = np.concatenate([parca(s, e) for _, s, e in kelimeler])
                esik = max(ESIK_DB, _db(konusma) - ALT_DB)
            sinirlar = [c.giris] + [t for _, s, e in kelimeler for t in (s, e)] + [bit]
            for gs, ge in zip(sinirlar[::2], sinirlar[1::2]):
                bosluk = (ge - gs) / c.hiz
                if bosluk > min_sessizlik and (ses is None or _db(parca(gs, ge)) < esik):
                    ekle(sek(gs) + pay, sek(ge) - pay, "sessizlik", f"{_sn(bosluk)} sn sessizlik")
            for w, s, e in kelimeler:
                if d := _dolgu(w):
                    ekle(sek(s), sek(e), "dolgu", f"dolgu: {d}")
        elif ses is not None:
            n = int(PENCERE * audio.SR)
            i0 = int(c.giris * audio.SR)
            x = ses[i0:int(bit * audio.SR)]
            m = len(x) // n
            sessiz = [_db(x[i * n:(i + 1) * n]) < ESIK_DB for i in range(m)] + [False]
            bas = None
            for i, s in enumerate(sessiz):
                if s and bas is None:
                    bas = i
                elif not s and bas is not None:
                    gs, ge = c.giris + bas * PENCERE, c.giris + i * PENCERE
                    if (ge - gs) / c.hiz >= min_sessizlik:
                        ekle(sek(gs) + pay, sek(ge) - pay, "sessizlik", f"{_sn((ge - gs) / c.hiz)} sn sessizlik")
                    bas = None
    cikti: list[dict] = []
    for a in sorted(adaylar, key=lambda a: (a["bas"], a["bit"])):
        if not cikti or a["bas"] >= cikti[-1]["bit"]:  # üst üste binen izlerde önce gelen kalır
            cikti.append(a)
    return cikti
