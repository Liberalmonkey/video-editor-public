"""Render için yüz bölgeleri: native motion grafikleri yüzden kaçsın (ADR 0045).

WHY: instagram/1'de "?" alında, tik yüzdeydi. Yerleşim (studio/remotion/motion/cekirdek/yerlesim.ts) yüz kutusunu
bilirse kaçınır. Kutular kaynakta YuNet ile bulunur (reframe.py ile aynı model), Kurgu.tsx'in çizim geometrisiyle
(contain ya da konuşmacıda cover, ardından klip dönüşümü) sekans karesine eşlenir ve kare oranı (0..1) olarak
kurgu.render.json `bolgeler.yuzler`'e yazılır. Ölçüm kaynak dosya başına önbellektedir (work/cache/yuz/).
"""

from __future__ import annotations

import json
from pathlib import Path

from . import ff, kurgu, paths, reframe
from .schemas import Kurgu

ADIM = 0.5          # sn, sekans zamanında örnek aralığı
GORUNTU = (".mp4", ".mov", ".mkv", ".webm", ".m4v", ".avi")
RESIM = (".png", ".jpg", ".jpeg", ".webp")


def _olc(f: Path, zamanlar: list[float]) -> tuple[tuple[int, int], list[list[list[float]]]]:
    """Her zamanda bütün yüzler: [x, y, w, h] kaynak pikseli. Resimde tek kare."""
    import cv2

    if f.suffix.lower() in RESIM:
        kare = cv2.imread(str(f))
        kareler = [kare] * len(zamanlar)
        sh, sw = kare.shape[:2]
    else:
        cap = cv2.VideoCapture(str(f))
        sw, sh = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        kareler = []
        for t in zamanlar:
            cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
            ok, k = cap.read()
            kareler.append(k if ok else None)
        cap.release()
    dw = 480
    dh = max(1, int(sh * dw / max(sw, 1)))
    det = cv2.FaceDetectorYN.create(str(reframe.YUNET), "", (dw, dh), score_threshold=0.7)
    s = sw / dw
    cikti = []
    for k in kareler:
        yuzler = det.detect(cv2.resize(k, (dw, dh)))[1] if k is not None else None
        cikti.append([[float(v) * s for v in y[:4]] for y in (yuzler if yuzler is not None else [])])
    return (sw, sh), cikti


def _onbellekli(p, f: Path, zamanlar: list[float]) -> tuple[tuple[int, int], list[list[list[float]]]]:
    from .hizli import _ozet

    kok = p.work / "cache" / "yuz"
    kayit = kok / f"{f.stem}-{_ozet(f)}.json"
    eski = json.loads(kayit.read_text(encoding="utf-8")) if kayit.exists() else {"boyut": None, "t": {}}
    eksik = [t for t in zamanlar if f"{t:.2f}" not in eski["t"]]
    if eksik:
        boyut, sonuc = _olc(f, eksik)
        eski["boyut"] = list(boyut)
        eski["t"].update({f"{t:.2f}": r for t, r in zip(eksik, sonuc)})
        kok.mkdir(parents=True, exist_ok=True)
        kayit.write_text(json.dumps(eski), encoding="utf-8")
    return tuple(eski["boyut"]), [eski["t"][f"{t:.2f}"] for t in zamanlar]


def _kf(kfs, t: float, varsayilan: float) -> float:
    """Klip başından t sn'deki değer (doğrusal ara değer; yerleşim için yeterli)."""
    if not kfs:
        return varsayilan
    if t <= kfs[0].t:
        return kfs[0].v
    for a, b in zip(kfs, kfs[1:]):
        if a.t <= t <= b.t:
            return a.v + (b.v - a.v) * ((t - a.t) / max(b.t - a.t, 1e-6))
    return kfs[-1].v


def esle(kutu: list[float], kaynak: tuple[int, int], kare: tuple[int, int], *, kapla: bool, x: float = 0, y: float = 0, olcek: float = 1) -> dict:
    """Kaynak pikselindeki kutuyu sekans karesine (0..1 oran) taşır: contain/cover, sonra merkezden ölçek ve kaydırma."""
    sw, sh = kaynak
    W, H = kare
    s = (max if kapla else min)(W / sw, H / sh)
    ox, oy = (W - sw * s) / 2, (H - sh * s) / 2
    bx, by, bw, bh = kutu
    cx, cy = W / 2, H / 2
    x0 = cx + olcek * (ox + bx * s - cx) + x
    y0 = cy + olcek * (oy + by * s - cy) + y
    return {"x": round(x0 / W, 4), "y": round(y0 / H, 4), "w": round(bw * s * olcek / W, 4), "h": round(bh * s * olcek / H, 4)}


def hesapla(p, k: Kurgu) -> list[dict]:
    """[{bas, son, kutular:[{x,y,w,h}]}], sekans zamanı. Yüz yoksa aralık yazılmaz."""
    gizli = {i.id for i in k.izler if i.gizli or i.tur == "ses"}
    W, H = k.sekans.w, k.sekans.h
    cikti: list[dict] = []
    for c in k.klipler:
        if c.iz in gizli or c.tur not in ("video", "gorsel") or not c.kaynak:
            continue
        try:
            f = kurgu.dosya(p, k.kaynaklar[c.kaynak].yol)
        except (KeyError, ValueError):
            continue
        if not f.is_file() or f.suffix.lower() not in GORUNTU + RESIM:
            continue
        zaman = [c.bas + i * ADIM for i in range(max(1, int(c.sure / ADIM + 0.999)))]
        kaynak_t = [round(c.giris + (t - c.bas) * c.hiz, 2) for t in zaman]
        try:
            boyut, olcum = _onbellekli(p, f, kaynak_t)
        except Exception:  # noqa: BLE001  WHY: yüz ölçümü render'ı durdurmaz; yerleşim yalnız güvenli alanla çalışır
            continue
        for t, yuzler in zip(zaman, olcum):
            if not yuzler:
                continue
            ic = t - c.bas
            d = c.donus
            kutular = [esle(y, boyut, (W, H), kapla=c.konusmaci, x=_kf(d.x, ic, 0), y=_kf(d.y, ic, 0),
                            olcek=_kf(d.olcek, ic, 1) * (c.zoom if c.konusmaci else 1)) for y in yuzler]
            cikti.append({"bas": round(t, 3), "son": round(min(t + ADIM, c.bas + c.sure), 3), "kutular": kutular})
    return cikti


def model_var() -> bool:
    return Path(reframe.YUNET).exists() and ff is not None and paths is not None
