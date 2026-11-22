"""Eski gecis-* motion bindirmelerini V1 kesim geçişine çevirir (ADR 0045).

WHY: instagram/1'de V2'deki opak gecis-* webm'leri kareyi düz mavi, beyaz ya da siyah blokla dolduruyor, sonraki
çekimi hiç göstermiyordu. Yeni geçişler V1 klip sınırında `gecis_giris` ile çalışır (studio/remotion/gecisler.tsx):
orta nokta kesimde, iki çekim her karede görünür. Bu modül eski bindirmeyi en yakın V1 kesimine taşır ve siler.
"""

from __future__ import annotations

import re

from .schemas import Gecis, Kurgu

# Eski kayıt adı → yeni geçiş türü ve yön. Eşleşmeyen gecis-* "sil"e düşer.
ESLEME = [
    (r"sil", ("sil", None)), (r"(yukari|asagi|sola|saga)-it|it", ("kay", None)), (r"iris|pencere", ("iris", None)),
    (r"piksel", ("piksel", None)), (r"isik|flas", ("isik", None)), (r"glitch|crt", ("piksel", None)),
    (r"perde|panjur|sekil-perde|capraz-serit", ("sil", None)), (r"murekkep|firca|kagit", ("isik", None)),
]
YON = {"yukari": "yukari", "asagi": "asagi", "sola": "sol", "saga": "sag"}
ESKI = re.compile(r"gecis-([a-z-]+?)(?:-(dikey|yatay))?(?:-[0-9a-f]{10})?\.webm$")


def eski_gecis_adi(k: Kurgu, c) -> str | None:
    if c.tur != "motion" or not c.kaynak:
        return None
    yol = k.kaynaklar.get(c.kaynak)
    m = ESKI.search(yol.yol if yol else "") or (ESKI.search(f"{c.sablon['ad']}.webm") if c.sablon else None)
    return m.group(1) if m else None


def donustur(k: Kurgu, *, sure: float = 0.33, pencere: float = 1.2) -> list[str]:
    """Bindirmeyi siler, ortasına en yakın V1 kesimine gecis_giris yazar. Yapılanları satır satır döner."""
    v1 = sorted((c for c in k.klipler if c.iz == "V1"), key=lambda c: c.bas)
    kesimler = [b for a, b in zip(v1, v1[1:]) if abs(a.bas + a.sure - b.bas) < 1e-3]
    rapor, sil = [], set()
    for c in k.klipler:
        ad = eski_gecis_adi(k, c)
        if not ad:
            continue
        orta = c.bas + c.sure / 2
        hedef = min(kesimler, key=lambda b: abs(b.bas - orta), default=None)
        sil.add(c.id)
        if hedef is None or abs(hedef.bas - orta) > pencere:
            rapor.append(f"{c.id}: {ad} silindi (yakında kesim yok; düz kesim kalır)")
            continue
        tur = next((t for d, (t, _) in ESLEME if re.search(d, ad)), "sil")
        yon = next((v for a, v in YON.items() if a in ad), "sol")
        hedef.gecis_giris = Gecis(tur=tur, sure=sure, yon=yon)
        rapor.append(f"{c.id}: {ad} → {hedef.id} kesiminde {tur}/{yon} ({hedef.bas:.2f} sn)")
    k.klipler = [c for c in k.klipler if c.id not in sil]
    return rapor
