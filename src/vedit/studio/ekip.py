"""Stüdyo AI paneli Ekip modu: ön ayarlar, proje ezmesi, canlı durum ve ajan çıktıları.

WHY: bkz. wiki/decisions/0044-ekip-motoru.md. İş kuyruğu `vedit ai-edit --ekip` başlatır; iç paralellik `ekip.py`'dedir.
Panel durumu `work/edit/ekip/durum.json`'dan okur; "hepsini durdur" iş iptalidir (süreç ağacı taskkill /T ile kapanır,
kurgu son birleşen turda kalır).
"""

from __future__ import annotations

import json
import re

from fastapi import APIRouter, HTTPException
from pydantic import ValidationError

from .. import ekip as ekip_mod
from .. import motorlar
from ..ekip_sema import SLOTLAR, EkipAyar
from . import ortak

router = APIRouter()
AD = re.compile(r"[a-z0-9][a-z0-9-]{0,39}")


def _global() -> dict:
    f = ekip_mod.GLOBAL
    return json.loads(f.read_text(encoding="utf-8")) if f.is_file() else {"varsayilan": None, "onayarlar": {}}


def _yaz_global(d: dict) -> None:
    ekip_mod.GLOBAL.write_text(json.dumps(d, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def dogrula(ayar: dict) -> EkipAyar:
    """Şema + motor ve model canlı listede mi. Kurulu olmayan motor slotta kabul edilmez."""
    try:
        a = EkipAyar.model_validate(ayar)
    except ValidationError as e:
        raise HTTPException(422, str(e)[:600]) from e
    d = motorlar.durum()
    for s, sl in a.slotlar.items():
        for motor, model, seviye, ek in ((sl.motor, sl.model, sl.seviye, ""), (sl.yedek_motor, sl.yedek_model, sl.yedek_seviye, " yedek")):
            if not motor:
                continue
            m = d.get(motor) or {}
            if not m.get("kurulu"):
                raise HTTPException(400, f"{s}{ek}: motor kurulu değil: {motor}")
            if model and model not in [x["id"] for x in m.get("modeller", [])]:
                raise HTTPException(400, f"{s}{ek}: bu motorda olmayan model: {model}")
            if seviye and seviye not in motorlar.SEVIYELER.get(motor, ()):
                raise HTTPException(400, f"{s}{ek}: seviye geçersiz: {seviye}")
    return a


@router.get("/api/ekip")
def ekip_oku():
    return {"global": _global(), "slotlar": list(SLOTLAR), "varsayilan_ayar": EkipAyar().model_dump()}


@router.put("/api/ekip/onayar/{ad}")
def onayar_yaz(ad: str, govde: dict, varsayilan: bool = False):
    if not AD.fullmatch(ad):
        raise HTTPException(400, "Ön ayar adı küçük harf, rakam, tire")
    a = dogrula({**govde, "ad": ad})
    g = _global()
    g.setdefault("onayarlar", {})[ad] = a.model_dump()
    if varsayilan or not g.get("varsayilan"):
        g["varsayilan"] = ad
    _yaz_global(g)
    return {"varsayilan": g["varsayilan"], "onayarlar": list(g["onayarlar"])}


@router.delete("/api/ekip/onayar/{ad}")
def onayar_sil(ad: str):
    g = _global()
    if ad not in g.get("onayarlar", {}):
        raise HTTPException(404, "Ön ayar yok")
    del g["onayarlar"][ad]
    if g.get("varsayilan") == ad:
        g["varsayilan"] = next(iter(g["onayarlar"]), None)
    _yaz_global(g)
    return {"varsayilan": g["varsayilan"], "onayarlar": list(g["onayarlar"])}


@router.get("/api/ekip/{studyo}/{ad}")
def proje_oku(studyo: str, ad: str):
    p = ortak.proje(studyo, ad)
    f = p.work / "edit" / "ekip.json"
    try:
        etkin = ekip_mod.ayar_yukle(p).model_dump()
    except (ValidationError, ValueError):
        etkin = EkipAyar().model_dump()
    return {"ezme": json.loads(f.read_text(encoding="utf-8")) if f.is_file() else None, "etkin": etkin}


@router.put("/api/ekip/{studyo}/{ad}")
def proje_yaz(studyo: str, ad: str, govde: dict):
    p = ortak.proje(studyo, ad)
    a = dogrula(govde)
    f = p.work / "edit" / "ekip.json"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(a.model_dump_json(indent=1), encoding="utf-8")
    return {"tamam": True}


@router.get("/api/ekip/{studyo}/{ad}/durum")
def durum(studyo: str, ad: str):
    p = ortak.proje(studyo, ad)
    f = p.work / "edit" / "ekip" / "durum.json"
    if not f.is_file():
        return {"yok": True}
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except ValueError:
        return {"yok": True}  # yazılırken okundu; panel bir sonraki yoklamada alır


@router.get("/api/ekip/{studyo}/{ad}/cikti/{slot}")
def cikti(studyo: str, ad: str, slot: str, tur: int | None = None, son: int = 400):
    if slot not in SLOTLAR:
        raise HTTPException(400, "Bilinmeyen slot")
    p = ortak.proje(studyo, ad)
    kok = p.work / "edit" / "ekip"
    if tur is None:
        turlar = sorted((int(x.name[4:]) for x in kok.glob("tur-*") if x.name[4:].isdigit()), reverse=True)
        tur = next((t for t in turlar if (kok / f"tur-{t}" / f"{slot}.cikti.txt").is_file()), None)
    f = kok / f"tur-{tur}" / f"{slot}.cikti.txt" if tur else None
    if not f or not f.is_file():
        return {"tur": tur, "satirlar": []}
    satirlar = f.read_text(encoding="utf-8", errors="replace").splitlines()[-max(1, min(son, 2000)):]
    meta = f.with_name(f"{slot}.meta.json")
    return {"tur": tur, "satirlar": satirlar, "meta": json.loads(meta.read_text(encoding="utf-8")) if meta.is_file() else None}
