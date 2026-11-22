"""Galeri API uçları: stil ve motion seçeneklerinin tek listesi; fizik ve karakter sahnesinin verisini bağlama.

WHY: bkz. wiki/decisions/0039-fizik-ritim-galeri.md
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .. import fizik, galeri, karakter, kurgu
from ..schemas import Klip
from .ortak import proje

router = APIRouter()


class SahneIstek(BaseModel):
    sahne: dict[str, Any]
    bas: float = Field(ge=0)
    sure: float = Field(gt=0, le=120)


@router.get("/api/galeri")
def liste():
    return {"ogeler": galeri.ogeler(), "turler": list(galeri.TURLER)}


@router.post("/api/sahne-bagla/{studyo}/{ad}")
def sahne_bagla(studyo: str, ad: str, g: SahneIstek):
    """Fizik ya da karakter sahnesinin verisini üretir (bake, viseme) ve kaynağını döner; klip arayüzde eklenir.

    Kurgu diskten okunur: karakterin ağzı o aralıktaki konuşmadan gelir. Önce kaydedilmemiş ses değişikliği varsa
    arayüz önce kaydeder.
    """
    p = proje(studyo, ad)
    tur = g.sahne.get("kind")
    if tur not in ("fizik", "karakter"):
        raise HTTPException(422, "Yalnız fizik ve karakter sahnesi bağlanır")
    k = kurgu.oku(p.work) if kurgu.yol(p.work).exists() else kurgu.bos(studyo)
    c = Klip(id="__galeri", iz="V1", bas=g.bas, sure=g.sure, tur="sahne", sahne={"layout": "full", **g.sahne})
    if h := fizik.hatalar(c) + karakter.hatalar(c):
        raise HTTPException(422, "; ".join(h))
    k.klipler.append(c)
    try:
        (fizik if tur == "fizik" else karakter).bagla(p, k)
    except SystemExit as e:
        raise HTTPException(500, str(e)) from e
    kay = k.kaynaklar[c.kaynak]
    ic = kay.yol.partition(":")[2]
    return {"id": c.kaynak, "yol": kay.yol, "sure": kay.sure, "url": f"/dosya/{p.studyo}/{p.ad}/public/{ic}"}
