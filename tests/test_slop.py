"""Çalıştır: .venv/Scripts/python -X utf8 tests/test_slop.py"""
import numpy as np

from vedit.slop import hareket_analizi, metin_analizi, olay_analizi, palet_analizi, ritim_analizi, ses_analizi


def kodlar(b):
    return {x["kod"] for x in b}


# Ritim: eşit planlar işaretlenir, değişken planlar işaretlenmez
assert "RITIM_METRONOM" in kodlar(ritim_analizi([3.0 * i for i in range(1, 15)], 45.0))
assert not ritim_analizi([1.2, 2.5, 7.0, 8.1, 15.0, 17.5, 26.0, 27.0], 35.0)
blok = [1.5, 8.0, 12.0, 16.0, 20.0, 24.0, 28.0, 29.0, 37.0, 38.5, 48.0, 49.0]
assert "RITIM_ESIT_BLOK" in kodlar(ritim_analizi(blok, 60.0))

# Hareket: durgunluk ve düzenli süzülme
assert "STATIK_UZUN" in kodlar(hareket_analizi(np.zeros(4 * 30), [], 30.0))
assert "KEN_BURNS_HER_YERDE" in kodlar(hareket_analizi(np.full(4 * 40, 0.6), [8.0, 16.0, 24.0, 32.0], 40.0))
canli = np.abs(np.random.default_rng(1).normal(6, 5, 4 * 40))
assert not hareket_analizi(canli, [8.0, 16.0, 24.0, 32.0], 40.0)

assert "ACILIS_YAVAS" in kodlar(hareket_analizi(np.full(4 * 30, 0.2), [5.0], 30.0))
assert "ACILIS_YAVAS" not in kodlar(hareket_analizi(np.full(4 * 30, 3.0), [5.0], 30.0))

# Palet
mor = np.zeros((10, 54, 96, 3), np.uint8)
mor[..., 0], mor[..., 2] = 110, 220
assert "PALET_MOR" in kodlar(palet_analizi(mor))
assert "PALET_KOYU_SABLON" in kodlar(palet_analizi(np.full((10, 54, 96, 3), 12, np.uint8)))
assert not palet_analizi(np.full((10, 54, 96, 3), 150, np.uint8))

# Ses
duz = np.full(600, -20.0)
assert kodlar(ses_analizi(duz, 1.5, 60.0)) == {"SES_NEFES_YOK", "SES_DUZ_DINAMIK"}
nefesli = duz.copy()
for k in (100, 250, 400, 550):
    nefesli[k:k + 5] = -45
assert not ses_analizi(nefesli, 7.0, 60.0)

# Olaylar
esit = {"fps": 30, "olaylar": [{"tur": "zoom_in", "t": 5.0 * i} for i in range(1, 9)]}
assert "OLAY_TEKDUZE" in kodlar(olay_analizi(esit, 60.0))
tek = {"fps": 30, "olaylar": [{"tur": "gecis", "ad": "whip", "t": t} for t in (2, 9, 13, 27, 41)]}
assert "OLAY_TEK_TUR" in kodlar(olay_analizi(tek, 60.0))

# Metin: Türkçe büyük harf, zaman eşleme, olağan cümlede sessizlik
b = metin_analizi([{"w": w, "s": float(i)} for i, w in enumerate("Bu OYUNUN KURALLARI artık başka".split())])
assert b[0]["kod"] == "METIN_KLISE" and b[0]["bas"] == 1.0
assert not metin_analizi([{"w": w, "s": None} for w in "Bugün kahveyi iki dakika demledik ve tadına baktık".split()])
assert "METIN_KARSITLIK" in kodlar(metin_analizi(
    [{"w": w, "s": None} for w in "sadece hız değil, kalite. yalnız fiyat değil, süre. sadece iş değil, hayat.".split()]))
print("slop testleri geçti")
