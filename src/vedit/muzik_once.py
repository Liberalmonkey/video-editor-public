"""Müzik öncülü yapı (ADR 0064, adım 8): parça editörlerden önce seçilir, beat ve cümle haritası herkese gider.

WHY: bkz. wiki/decisions/0064-yaratici-yon.md. Müzik, kesim ve grafikle aynı anda (paralel ses editöründe) seçiliyordu; kesim ve
imza anları müziğin cümlelerine oturamıyordu. Seçim LLM çağrısı değildir: kütüphane manifest'inden brifin ses fikri, tezi ve enerji
eğrisine göre puanlanır; parçanın ritmi bir kez ölçülür ve önbelleğe yazılır. Hiçbir hata edit'i durdurmaz: harita yoksa akış
bugünkü gibi sürer, müzik editörü başka parça seçebilir (gerekçesini yazar).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from . import paths

DOSYA = "muzik-once.json"
ONBELLEK = paths.ROOT / "work" / "ritim-muzik"  # parça analizi projeler arasında paylaşılır
CUMLE_BEAT = 8           # 4/4'te iki ölçü: kesim ve grafik girişi için doğal cümle başı
YUKSELIS_ESIK = 0.22     # 1 sn yumuşatılmış enerjide 2 sn içindeki artış (0-1)
YUKSELIS_ARA = 4.0       # sn; iki yükseliş arasında en az
ENERJI_SOZ = {"düşük": 1, "orta-düşük": 2, "orta": 3, "orta-yüksek": 4, "yüksek": 5}


def _kucuk(s: str) -> str:
    return (s or "").replace("İ", "i").replace("I", "ı").lower()


def _kelimeler(*metinler: str) -> set[str]:
    return {w for m in metinler for w in re.findall(r"[a-zçğıöşü]+", _kucuk(m)) if len(w) > 2}


def _enerji(e: dict) -> int | None:
    v = e.get("energy")
    if isinstance(v, (int, float)):
        return max(1, min(5, int(v)))
    return ENERJI_SOZ.get(_kucuk(str(v or "")).strip())


def _brif_enerjisi(brif) -> float:
    """Brifin süreye göre ağırlıklı enerji ortalaması; brif yoksa 3."""
    dilim = [(e.aralik[1] - e.aralik[0], e.seviye) for e in (getattr(brif, "enerji", None) or [])]
    toplam = sum(d for d, _ in dilim)
    return sum(d * s for d, s in dilim) / toplam if toplam > 0 else 3.0


def kayitlar() -> list[dict]:
    """Lisanslı ve diskte var olan müzik kayıtları."""
    try:
        girdi = json.loads((paths.LIBRARY / "music" / "manifest.json").read_text(encoding="utf-8")).get("entries") or []
    except (OSError, ValueError):
        return []
    out = []
    for e in girdi:
        if not e.get("license") or not e.get("file"):
            continue
        yol = str(e["file"]).replace("\\", "/").removeprefix("library/").removeprefix("music/")
        f = paths.LIBRARY / "music" / yol
        if f.is_file():
            out.append({**e, "_yol": f, "_kaynak": f"library:music/{yol}"})
    return out


def puan(e: dict, istek_kelime: set[str], enerji: float, sure: float) -> float:
    """Yüksek puan daha uygun parça: ruh hâli örtüşmesi, enerji yakınlığı, süre yeterliliği."""
    ruh = _kelimeler(" ".join(e.get("mood") or []), str(e.get("genre") or ""))
    p = 2.0 * len(ruh & istek_kelime)
    if (en := _enerji(e)) is not None:
        p += 2.0 - abs(en - enerji)
    if sure > 0 and e.get("duration_s"):
        p += 1.0 if float(e["duration_s"]) >= sure else -1.0
    return p


def sec(brif, istek: str | None, sure: float, girdi: list[dict] | None = None) -> dict | None:
    adaylar = kayitlar() if girdi is None else girdi
    if not adaylar:
        return None
    k = _kelimeler(istek or "", *(([brif.ses, brif.tez, brif.metafor]) if brif else []))
    en = _brif_enerjisi(brif)
    return max(adaylar, key=lambda e: (puan(e, k, en, sure), str(e.get("id"))))


def yukselisler(enerji: list[float], hz: int) -> list[float]:
    """Enerji eğrisinde belirgin yükseliş anları (drop, giriş, tam açılış): imza anı ve bölüm başı adayları."""
    if not enerji or hz <= 0:
        return []
    n = max(1, hz)  # 1 sn kayan ortalama
    yum = [sum(enerji[max(0, i - n + 1): i + 1]) / len(enerji[max(0, i - n + 1): i + 1]) for i in range(len(enerji))]
    out: list[float] = []
    for i in range(2 * hz, len(yum)):
        if yum[i] - yum[i - 2 * hz] >= YUKSELIS_ESIK:
            t = round(i / hz, 2)
            if not out or t - out[-1] >= YUKSELIS_ARA:
                out.append(t)
    return out


def harita(e: dict, sure: float | None = None) -> dict:
    """Seçilen parçanın kesim haritası: tempo, cümle başları (her 8 beat), enerji yükselişleri. Süre verilirse ona kırpılır."""
    from . import ritim
    a = ritim.analiz(Path(e["_yol"]), ONBELLEK)
    son = sure if sure and sure > 0 else float("inf")
    beats = [b for b in a.get("beats") or [] if b <= son]
    return {"kaynak": e["_kaynak"], "id": e.get("id"), "tempo": a.get("tempo"), "yapi": e.get("structure"),
            "cumle_baslari": [round(b, 2) for b in beats[::CUMLE_BEAT]][:24],
            "yukselisler": [t for t in yukselisler(a.get("enerji") or [], int(a.get("enerji_hz") or 0)) if t <= son][:8]}


def hazirla(p, brif, istek: str | None, sure: float) -> dict | None:
    """Parçayı seçer, haritasını çıkarır ve `work/edit/muzik-once.json`'a yazar. Hata ya da kütüphane boşsa None."""
    try:
        e = sec(brif, istek, sure)
        if e is None:
            return None
        h = harita(e, sure)
    except Exception as hata:  # noqa: BLE001 - ölçüm edit'i durdurmaz (ADR 0039 ile aynı ilke)
        print(f"  Müzik öncülü atlandı ({type(hata).__name__}: {str(hata)[:120]})", flush=True)
        return None
    f = p.work / "edit" / DOSYA
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(h, ensure_ascii=False, indent=1), encoding="utf-8")
    return h


def metin(h: dict | None) -> str:
    """Editör istemine giden bölüm."""
    if not h:
        return ""
    sat = [f"## Müzik öncülü (ADR 0064): `{h['kaynak']}`" + (f", {h['tempo']:g} BPM" if h.get("tempo") else "")]
    if h.get("yapi"):
        sat.append(f"- Parçanın yapısı: {h['yapi']}")
    if h.get("cumle_baslari"):
        sat.append("- Cümle başları (sn, her 8 beat): " + ", ".join(f"{t:g}" for t in h["cumle_baslari"]))
    if h.get("yukselisler"):
        sat.append("- Enerji yükselişleri (imza anı ve bölüm başı adayı): " + ", ".join(f"{t:g}" for t in h["yukselisler"]))
    sat.append("- Müzik bu parçayla 0. saniyeden başlar; müzik editörü başka parça seçerse raporda gerekçesini yazar. Kurgu kesimleri, "
               "bölüm geçişleri ve imza anları mümkünse bir cümle başına ya da yükselişe oturur (en çok 2 kare); her beat'e kesim koyma. "
               "Söz ve anlatı müziğin önündedir: konuşmayı müziğe uydurmak için kesme.")
    return "\n".join(sat)
