"""Çalıştır: .venv/Scripts/python -X utf8 tests/test_kesimqa.py"""
from vedit.kesimqa import karsilastir, norm


def kel(metin, adim=1.0):
    return [{"w": w, "s": i * adim} for i, w in enumerate(metin.split())]


assert norm("İSTANBUL,") == "istanbul" and norm("IŞIK.") == "ışık"
assert karsilastir(kel("bir iki üç"), kel("Bir, iki üç."))["benzerlik"] == 1.0

r = karsilastir(kel("bugün hava çok güzel oldu"), kel("bugün hava güzel oldu"), kesimler=[2.0])
assert [e["kelime"] for e in r["eksik"]] == ["çok"] and r["eksik"][0]["kesim_kenari"] and not r["fazla"]

r = karsilastir(kel("bugün hava güzel"), kel("bugün bugün hava güzel"))
assert [f["kelime"] for f in r["fazla"]] == ["bugün"] and not r["eksik"]

r = karsilastir(kel("a b c d"), kel("a b c d"), kesimler=[0.0])
assert not r["eksik"] and not r["fazla"]
print("kesimqa testleri geçti")
