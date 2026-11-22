"""Hazır efektler (zoom, punch, odak zoom, ken burns, giriş/çıkış, sarsıntı...): ad ve parametre denetimi, ses olayı.

# WHY: bkz. wiki/decisions/0033-hazir-efektler.md. Keyframe matematiği yalnız studio/remotion/hazirEfekt.ts'tedir;
# burası aynı hazirEfekt.json'u okur, render'da sessizce yanlış çıkacak kaydı reddeder ve olaysesi'ne rol olayı verir.
"""

from __future__ import annotations

import json
from functools import lru_cache

from . import paths

KATALOG_YOLU = paths.ROOT / "studio" / "remotion" / "hazirEfekt.json"
GORUNTU = ("video", "gorsel", "metin", "motion")  # Kurgu.tsx'te Donusum'dan geçen türler
SABIT = ("ad", "t", "ses")  # parametre olmayan alanlar


@lru_cache(maxsize=1)
def katalog() -> dict:
    return json.loads(KATALOG_YOLU.read_text(encoding="utf-8"))


def _sayi(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def hatalar(c) -> list[str]:
    """Klibin `hazir` listesindeki bilinmeyen ad, bilinmeyen parametre ve aralık dışı değerler."""
    if not c.hazir:
        return []
    if c.tur not in GORUNTU:
        return [f"{c.id}: hazır efekt yalnız görüntü klibinde çalışır ({', '.join(GORUNTU)}), bu klip {c.tur}"]
    kat, h = katalog(), []
    for i, e in enumerate(c.hazir):
        ad = e.get("ad")
        yer = f"{c.id}: hazır efekt {i + 1} ({ad})"
        if ad not in kat:
            h.append(f"{c.id}: bilinmeyen hazır efekt '{ad}' (geçerli: {', '.join(kat)})")
            continue
        t = e.get("t")
        if t is not None and not (_sayi(t) and 0 <= t < c.sure):
            h.append(f"{yer}: t klibin içinde olmalı (0 ile {c.sure:.2f} sn arası), '{t}' yazılmış")
        if "ses" in e and not isinstance(e["ses"], bool):
            h.append(f"{yer}: ses true ya da false olmalı")
        param = kat[ad]["param"]
        for a, v in e.items():
            if a in SABIT:
                continue
            pr = param.get(a)
            if pr is None:
                h.append(f"{yer}: bilinmeyen parametre '{a}' (geçerli: {', '.join(param)})")
            elif isinstance(pr["vars"], bool):
                if not isinstance(v, bool):
                    h.append(f"{yer}: {a} true ya da false olmalı, '{v}' yazılmış")
            elif _sayi(pr["vars"]):
                # sure 0: klibin sonuna kadar (varsayılanı 0 olan efektlerde)
                if not _sayi(v):
                    h.append(f"{yer}: {a} sayı olmalı, '{v}' yazılmış")
                elif not (a == "sure" and v == 0 and pr["vars"] == 0) and not (pr.get("min", v) <= v <= pr.get("max", v)):
                    h.append(f"{yer}: {a} {pr.get('min')} ile {pr.get('max')} arasında olmalı, {v} yazılmış")
            elif v not in pr.get("secenek", []):
                h.append(f"{yer}: {a} '{v}' geçersiz (geçerli: {', '.join(pr.get('secenek', []))})")
    return h


def cozumle(c, e: dict) -> tuple[float, float]:
    """(t, sure): hazirEfekt.ts `cozumle` ile aynı. t yoksa 0 ya da `son` efektte klip sonu; sure 0 ise klibin sonuna kadar."""
    tn = katalog()[e["ad"]]
    pr = tn["param"]["sure"]
    d = e.get("sure")
    d = min(pr.get("max", d), max(pr.get("min", d), d)) if _sayi(d) else pr["vars"]
    t = e.get("t")
    t = max(0.0, t) if _sayi(t) else max(0.0, c.sure - d) if tn.get("son") else 0.0
    if not d:
        d = max(0.04, c.sure - t)
    return t, d


def ses_olaylari(k) -> list[dict]:
    """`ses: true` efektler (klipte `ses: false` denmemişse) için olaysesi rol olayı, olaylar.json biçiminde."""
    from .olaysesi import ROLLER  # geç içe aktarma: denetim yolu numpy/soundfile yüklemesin
    kat, gizli = katalog(), {i.id for i in k.izler if i.gizli}
    olaylar = []
    for c in k.klipler:
        if c.iz in gizli or c.tur not in GORUNTU:
            continue
        for e in c.hazir:
            tn = kat.get(e.get("ad"))
            if not tn or not tn["ses"] or e.get("ses") is False:
                continue
            t, d = cozumle(c, e)
            # Yumuşak güçte susan rol (punch_in) sesi açık efektte duyulsun diye orta; klipteki `guc` her zaman kazanır.
            guc = e.get("guc") or ("orta" if ROLLER.get(tn["rol"], {}).get("sessiz") else None)
            # WHY: ADR 0039. Düşüş ve çarpma efektinde ses efekt başında değil temas anındadır (ses_an oran, ses_kare kare).
            t += d * tn.get("ses_an", 0) + tn.get("ses_kare", 0) / k.sekans.fps
            olaylar.append({"t": round(c.bas + t, 3), "tur": tn["rol"], "sure": round(d, 3), "not": f"hazır {e['ad']} ({c.id})",
                            **({"guc": guc} if guc else {})})
    return olaylar
