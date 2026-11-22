"""Kurallar API uçları: liste, ekle, düzenle, durum (aç, kapat, onayla, reddet, sil), toplu sil, içe ve dışa aktar, ayar.

WHY: bkz. wiki/decisions/0047-kural-deposu.md. Silme mezar taşı bırakır (durum 'silinen'); QC aynı kuralı yeniden önermez.
Her yazımda checks.md depodan yeniden üretilir.
"""

from __future__ import annotations

import threading

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, ValidationError

from .. import kural, paths
from .ortak import kok_ici

router = APIRouter()
_kilit = threading.Lock()  # WHY: iki sekme aynı anda yazarsa biri kaybolmasın


class Yeni(BaseModel):
    metin: str
    neden: str = ""
    kategori: str = "genel"
    onem: kural.Onem = "P1"
    hedef_rol: kural.Rol = "hepsi"
    kapsam: kural.Kapsam = "global"
    kapsam_deger: str | None = None
    olcut: str | None = None


class Duzen(BaseModel):
    metin: str | None = None
    neden: str | None = None
    kategori: str | None = None
    onem: kural.Onem | None = None
    hedef_rol: kural.Rol | None = None
    kapsam: kural.Kapsam | None = None
    kapsam_deger: str | None = None
    olcut: str | None = None


class Toplu(BaseModel):
    idler: list[str]
    durum: kural.Durum


def _ozet(d: kural.Depo) -> dict:
    return {"kurallar": [k.model_dump(by_alias=True) for k in d.kurallar], "ayar": kural.ayar().model_dump(),
            "kategoriler": list(kural.KATEGORILER), "kapi_onerileri": [k.id for k in kural.kapi_onerileri(d)]}


def _hata(e: Exception) -> HTTPException:
    if isinstance(e, ValidationError):
        return HTTPException(422, "; ".join(x["msg"] for x in e.errors()))
    if isinstance(e, KeyError):
        return HTTPException(404, str(e))
    return HTTPException(422, str(e))


@router.get("/api/kurallar")
def liste():
    return _ozet(kural.yukle())


@router.post("/api/kurallar")
def ekle(g: Yeni):
    with _kilit:
        d = kural.yukle()
        try:
            k = kural.ekle(d, g.metin, **g.model_dump(exclude={"metin"}), kaynak="kullanici")
        except (ValidationError, ValueError) as e:
            raise _hata(e) from e
        kural.kaydet(d)
    return {"kural": k.model_dump(by_alias=True), **_ozet(d)}


@router.patch("/api/kurallar/{kid}")
def duzenle(kid: str, g: Duzen):
    with _kilit:
        d = kural.yukle()
        try:
            k = kural.guncelle(d, kid, **g.model_dump(exclude_none=True))
        except (ValidationError, ValueError, KeyError) as e:
            raise _hata(e) from e
        kural.kaydet(d)
    return {"kural": k.model_dump(by_alias=True), **_ozet(d)}


@router.post("/api/kurallar/durum")
def durum(g: Toplu):
    """Tek ya da toplu: aç (aktif), kapat (pasif), onayla (aktif), reddet ve sil (silinen, mezar taşı)."""
    with _kilit:
        d = kural.yukle()
        try:
            for kid in g.idler:
                kural.durum_degistir(d, kid, g.durum)
        except KeyError as e:
            raise _hata(e) from e
        kural.kaydet(d)
    return _ozet(d)


@router.post("/api/kurallar/ice")
def ice(g: kural.Depo):
    with _kilit:
        d = kural.yukle()
        n = 0
        for k in g.kurallar:
            if kural.bul_benzer(d, k.metin) is None:
                d.kurallar.append(k.model_copy(update={"id": kural._yeni_id(d)}))
                n += 1
        kural.kaydet(d)
    return {"eklenen": n, **_ozet(d)}


@router.get("/api/kurallar/disa")
def disa():
    return kural.yukle().model_dump(by_alias=True, exclude_none=True)


@router.put("/api/kurallar/ayar")
def ayar(g: kural.Ayar):
    kural.ayar_yaz(g)
    return _ozet(kural.yukle())


@router.get("/api/kurallar/kare/{ic:path}")
def kare(ic: str):
    """Kanıt karesi: yalnız Projeler/outputs altı (kök içi denetimli)."""
    return FileResponse(kok_ici(paths.OUTPUTS, ic), headers={"X-Content-Type-Options": "nosniff"})
