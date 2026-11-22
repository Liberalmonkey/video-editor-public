"""Kelime çapası: olayın sekans zamanı kaynak kelimesinden türetilir (ADR 0048).

WHY: Ekip motoru v2'de E1 (kesim), E2 (grafik) ve E3 (ses) aynı anda çalışır. E2 ve E3 olayı sekans saniyesine değil
kaynak kelimesine bağlar (`capa: {kaynak, kelime | t, once_kare}`); E1 kesimi değiştirince vedit bu fonksiyonla bütün
çapalı olayları yeni zamana taşır. Kelime kesimde düştüyse olay düşmez: sahibine bulgu olur. Saf fonksiyonlar.
"""

from __future__ import annotations

from .schemas import Kurgu

TOLERANS = 1e-3


def _kaynak_zamani(k: Kurgu, c) -> float | None:
    if c.capa is None:
        return None
    if c.capa.kelime is not None:
        kel = k.kelimeler.get(c.capa.kaynak) or []
        return kel[c.capa.kelime].s if c.capa.kelime < len(kel) else None
    return c.capa.t


def sekans_zamani(k: Kurgu, kaynak: str, t: float, *, izler: set[str] | None = None) -> float | None:
    """Kaynak zamanı t'yi gösteren görüntü klibinin sekans zamanı (ilk eşleşen, sekans sırasıyla). Kesildiyse None."""
    izler = izler or {i.id for i in k.izler if i.tur == "video"}
    for c in sorted(k.klipler, key=lambda c: c.bas):
        if c.kaynak != kaynak or c.iz not in izler or c.tur not in ("video",):
            continue
        if c.giris - TOLERANS <= t < c.giris + c.sure * c.hiz - TOLERANS:
            return c.bas + (t - c.giris) / c.hiz
    return None


def esle(k: Kurgu) -> tuple[list[str], list[dict]]:
    """Çapalı bütün klipleri yeni kesime taşır (yerinde). Döner: (taşınan klip kimlikleri, düşen çapa bulguları)."""
    fps = k.sekans.fps
    tasinan, bulgu = [], []
    for c in k.klipler:
        t = _kaynak_zamani(k, c)
        if t is None:
            if c.capa is not None:
                bulgu.append({"klip": c.id, "iz": c.iz, "sorun": f"çapa kelimesi yok ({c.capa.kaynak}#{c.capa.kelime})"})
            continue
        s = sekans_zamani(k, c.capa.kaynak, t)
        if s is None:
            bulgu.append({"klip": c.id, "iz": c.iz, "sorun": f"çapalı kelime kesimde düştü ({c.capa.kaynak} @ {t:.2f} sn)",
                          "kaynak_t": round(t, 3)})
            continue
        yeni = round(max(0.0, s - c.capa.once_kare / fps), 3)
        if abs(yeni - c.bas) > TOLERANS:
            c.bas = yeni
            tasinan.append(c.id)
    return tasinan, bulgu


def capala(k: Kurgu, c, kaynak: str) -> None:
    """Klibi bulunduğu sekans zamanına en yakın kaynak kelimesine çapalar (editör çapasız yazdıysa vedit tamamlar)."""
    from .schemas import Capa

    fps = k.sekans.fps
    hedef = c.bas + 3 / fps
    en = None
    for v in sorted((x for x in k.klipler if x.kaynak == kaynak and x.tur == "video"), key=lambda x: x.bas):
        for i, w in enumerate(k.kelimeler.get(kaynak, [])):
            if v.giris <= w.s < v.giris + v.sure * v.hiz:
                s = v.bas + (w.s - v.giris) / v.hiz
                if en is None or abs(s - hedef) < en[0]:
                    en = (abs(s - hedef), i)
    if en is not None and en[0] < 1.0:
        c.capa = Capa(kaynak=kaynak, kelime=en[1])
