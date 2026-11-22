"""Kurgu klibi için otomatik yeniden çerçeve: kareyi doldur, konuşmacının yüzünü yatayda izle.

Kurgu.tsx klibi sekans karesine `objectFit: contain` ile çizer, sonra merkez orijinli
`translate(x px, y px) scale(olcek)` uygular. Karenin merkezine göre p noktası p*olcek + x'e gider.
Kaynakta yatay oranı u (0–1) olan yüz, contain görüntüde merkezden (u-0.5)*containW uzaktadır;
merkeze oturması için x = -olcek*(u-0.5)*containW. Siyah bant olmasın diye |x| <= (containW*olcek - W)/2.
"""

from __future__ import annotations

from collections.abc import Callable


from .tembel import Tembel

# WHY: Stüdyo açılışında yüklenmesin (ADR 0050)
cv2 = Tembel("cv2")

from . import kurgu, reframe
from .schemas import Kurgu

# WHY: bkz. wiki/decisions/0024-oneri-araclari.md — öneri aracı, kurgu.json'a yalnız kullanıcı onayıyla yazılır.

Bulucu = Callable[[str, list[float]], list[float | None]]


def _yunet(yol: str, zamanlar: list[float]) -> list[float | None]:
    """Her kaynak saniyesinde en büyük yüzün yatay merkezi (0–1), yoksa None. reframe.py ile aynı YuNet."""
    cap = cv2.VideoCapture(yol)
    sw, sh = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    dh = max(1, int(sh * 480 / max(sw, 1)))
    det = cv2.FaceDetectorYN.create(str(reframe.YUNET), "", (480, dh), score_threshold=0.75)
    cikti: list[float | None] = []
    for t in zamanlar:
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
        ok, kare = cap.read()
        faces = det.detect(cv2.resize(kare, (480, dh)))[1] if ok else None
        if faces is not None and len(faces):
            x, _, w, _ = max(faces, key=lambda f: f[2] * f[3])[:4]
            cikti.append(float(x + w / 2) / 480)
        else:
            cikti.append(None)
    cap.release()
    return cikti


def _boyut(yol: str) -> tuple[int, int]:
    cap = cv2.VideoCapture(yol)
    wh = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()
    if not all(wh):
        raise ValueError(f"Video okunamadı: {yol}")
    return wh


def _klip(k: Kurgu, klip_id: str):
    for c in k.klipler:
        if c.id == klip_id:
            return c
    raise ValueError(f"Klip yok: {klip_id}")


def donus_hesapla(p, k: Kurgu, klip_id: str, *, adim: float = 0.25, olu_bolge: float = 0.05,
                  bul: Bulucu | None = None) -> dict:
    c = _klip(k, klip_id)
    if c.tur != "video" or not c.kaynak:
        raise ValueError(f"{klip_id}: yalnız video klibi yeniden çerçevelenir")
    kay = k.kaynaklar[c.kaynak]
    yol = str(kurgu.dosya(p, kay.yol))
    sw, sh = (kay.w, kay.h) if kay.w and kay.h else _boyut(yol)
    W, H = k.sekans.w, k.sekans.h
    c_ = min(W / sw, H / sh)
    cw, ch = sw * c_, sh * c_
    olcek = max(W / cw, H / ch)
    sinir = max(0.0, (cw * olcek - W) / 2)

    son = c.giris + c.sure * c.hiz
    n = max(1, int((son - c.giris) / adim))
    zamanlar = [c.giris + i * adim for i in range(n)] + [son]
    merkez = (bul or _yunet)(yol, zamanlar)
    bilinen = [m for m in merkez if m is not None]
    yuz_orani = round(len(bilinen) / len(merkez), 3)

    # Boşluk son bilineni tutar; ölü bölge küçük kaymayı yutar; 5'li hareketli ortalama titremeyi alır.
    hedef, seri = (bilinen[0] if bilinen else 0.5), []
    for m in merkez:
        if m is not None and abs(m - hedef) > olu_bolge:
            hedef = m
        seri.append(hedef)
    seri = [sum(seri[max(0, i - 2):i + 3]) / len(seri[max(0, i - 2):i + 3]) for i in range(len(seri))]

    xs = [min(sinir, max(-sinir, -olcek * (u - 0.5) * cw)) for u in seri]
    ts = [(z - c.giris) / c.hiz for z in zamanlar]
    kf = [{"t": round(ts[0], 3), "v": round(xs[0], 1), "ease": "yumusak"}]
    for t, x in zip(ts[1:], xs[1:]):
        if abs(x - kf[-1]["v"]) >= olu_bolge * W:
            kf.append({"t": round(t, 3), "v": round(x, 1), "ease": "yumusak"})
    if len(kf) > 1 and kf[-1]["t"] < round(ts[-1], 3):
        kf.append({"t": round(ts[-1], 3), "v": round(xs[-1], 1), "ease": "yumusak"})
    return {"olcek": [{"t": 0.0, "v": round(olcek, 4), "ease": "dogrusal"}], "x": kf, "anim": ["x"],
            "yuz_orani": yuz_orani}


def uygula(k: Kurgu, klip_id: str, sonuc: dict) -> Kurgu:
    """Saf: klibin donus x/olcek/anim alanları güncellenmiş kopyayı döndürür."""
    yeni = k.model_copy(deep=True)
    d = _klip(yeni, klip_id).donus
    anim = [a for a in d.anim if a not in ("x", "olcek")] + list(sonuc["anim"])
    _klip(yeni, klip_id).donus = d.model_validate({**d.model_dump(), "x": sonuc["x"], "olcek": sonuc["olcek"], "anim": anim})
    return yeni
