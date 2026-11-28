"""Stüdyo AI paneli ekip modu: ön ayarlar, proje ezmesi, canlı durum (kapılar, slotlar) ve ajan çıktıları.

WHY: bkz. wiki/decisions/0053-seviyeli-ekip-orkestrator.md. İş kuyruğu `vedit ai-edit --ekip` başlatır; iç paralellik
`ekip_v3.py`'dedir. Panel durumu `work/edit/ekip/durum.json`'dan okur; "hepsini durdur" iş iptalidir (süreç ağacı
taskkill /T ile kapanır, kurgu son birleşen kapıda kalır).
"""

from __future__ import annotations

import json
import re
import threading

from fastapi import APIRouter, HTTPException
from pydantic import ValidationError

from .. import ekip as ekip_mod
from .. import kurgu, motorlar
from ..ekip_sema import EN_COK, SEVIYE, SLOT_DESEN, EkipAyar
from . import ortak

router = APIRouter()
AD = re.compile(r"[a-z0-9][a-z0-9-]{0,39}")
_kilit = threading.RLock()


def _global() -> dict:
    f = ekip_mod.GLOBAL
    return json.loads(f.read_text(encoding="utf-8")) if f.is_file() else {"varsayilan": None, "onayarlar": {}}


def _yaz_global(d: dict) -> None:
    # WHY: eşzamanlı ön ayar yazımları yarım JSON bırakmasın; geçici dosya + os.replace ile atomik yazılır.
    with _kilit:
        kurgu._atomik(ekip_mod.GLOBAL, json.dumps(d, ensure_ascii=False, indent=1) + "\n")


def dogrula(ayar: dict) -> EkipAyar:
    """Şema + motor ve model canlı listede mi. Kurulu olmayan motor grupta ya da ezmede kabul edilmez."""
    try:
        a = EkipAyar.model_validate(ayar)
    except ValidationError as e:
        raise HTTPException(422, str(e)[:600]) from e
    d = motorlar.durum()
    # Hızlıda orkestratör çağrılmaz: onun motoru kurulu olmasa da iş başlar (arayüz seviye.gerekenMotorlar ile aynı kural).
    for s, sl in [*a.gruplar.items(), *a.ezme.items()]:
        if a.hizli and s in ("orkestrator", "O"):
            continue
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
    return {"global": _global(), "seviyeler": {k: {"editor": e, "kk": q, "en_cok": EN_COK[k]} for k, (e, q) in SEVIYE.items()},
            "varsayilan_ayar": EkipAyar().model_dump()}


@router.put("/api/ekip/onayar/{ad}")
def onayar_yaz(ad: str, govde: dict, varsayilan: bool = False):
    if not AD.fullmatch(ad):
        raise HTTPException(400, "Ön ayar adı küçük harf, rakam, tire")
    a = dogrula({**govde, "ad": ad})
    # WHY: eşzamanlı oku-değiştir-yaz istekleri birbirinin ön ayarını ezmesin.
    with _kilit:
        g = _global()
        g.setdefault("onayarlar", {})[ad] = a.model_dump()
        if varsayilan or not g.get("varsayilan"):
            g["varsayilan"] = ad
        _yaz_global(g)
    return {"varsayilan": g["varsayilan"], "onayarlar": list(g["onayarlar"])}


@router.delete("/api/ekip/onayar/{ad}")
def onayar_sil(ad: str):
    # WHY: eşzamanlı silme/yazma istekleri global ekip.json üzerinde yarışmasın.
    with _kilit:
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
    # WHY: proje ekip.json yazımları eşzamanlı isteklerde bozulmasın ve yarım dosya bırakmasın.
    with _kilit:
        kurgu._atomik(f, a.model_dump_json(indent=1))
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
def cikti(studyo: str, ad: str, slot: str, son: int = 400):
    """Slotun en yeni çıktısı: ekip/<kapı klasörü>/<slot>.cikti.txt (orkestratör birden çok kapıda yazar)."""
    if not SLOT_DESEN.match(slot):
        raise HTTPException(400, "Bilinmeyen slot")
    p = ortak.proje(studyo, ad)
    kok = p.work / "edit" / "ekip"
    adaylar = sorted(kok.glob(f"*/{slot}.cikti.txt"), key=lambda f: f.stat().st_mtime) if kok.is_dir() else []
    if not adaylar:
        return {"asama": None, "satirlar": []}
    f = adaylar[-1]
    satirlar = f.read_text(encoding="utf-8", errors="replace").splitlines()[-max(1, min(son, 2000)):]
    meta = f.with_name(f"{slot}.meta.json")
    meta_veri = None
    if meta.is_file():
        try:
            meta_veri = json.loads(meta.read_text(encoding="utf-8"))
        except (OSError, ValueError):  # WHY: meta.json yazılırken okunur ya da bozuksa çıktı yoklaması 500 vermemeli
            meta_veri = None
    return {"asama": f.parent.name, "satirlar": satirlar, "meta": meta_veri}
