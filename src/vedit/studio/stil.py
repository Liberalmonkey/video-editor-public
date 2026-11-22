"""Stil paketleri API uçları: listele, referans yükle/sil, STYLE.md kaydet, projeye stil seç.

WHY: bkz. wiki/decisions/0029-stil-paneli.md
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse
from pydantic import BaseModel
from starlette.background import BackgroundTask

from .. import hizli, karakter, native_motion, paths, stil, stil_katalog, stil_varlik
from . import ortak

IZINLI = hizli.VIDEO | hizli.GORSEL
router = APIRouter()


def _studyo(studyo: str) -> str:
    if studyo not in paths.STUDIO_NAMES:
        raise HTTPException(400, "Bilinmeyen stüdyo")
    return studyo


def _ad(ad: str) -> str:
    try:
        return stil.ad_denetle(ad)
    except SystemExit as e:
        raise HTTPException(400, str(e)) from e


class StilKaydet(BaseModel):
    style_md: str


class StilSec(BaseModel):
    proje: str
    stil: str


class KatalogdanEkle(BaseModel):
    id: str
    proje: str | None = None


class StilSecki(BaseModel):
    secili_native: list[str] | None = None
    secili_kutuphane: list[str] | None = None
    yalniz_bunlar: bool | None = None


class NativeIndir(BaseModel):
    ad: str
    param: dict = {}
    en_boy: str = "1:1"
    sure: float | None = None


def _varlik_dict(studyo: str, ad: str, v: stil_varlik.StilVarlik) -> dict:
    return {
        **v.model_dump(),
        "kurgu_yolu": stil_varlik.kurgu_yolu(studyo, ad, v.dosya),
        "onizleme_url": f"/api/stil/{studyo}/{ad}/varlik/{v.id}/onizleme",
        "indir_url": f"/api/stil/{studyo}/{ad}/varlik/{v.id}/indir",
    }


def _depo_dict(studyo: str, ad: str, depo: stil_varlik.StilVarlikDeposu) -> dict:
    return {
        **depo.model_dump(),
        "yuklenenler": [_varlik_dict(studyo, ad, v) for v in depo.yuklenenler],
    }


def _katalog_dict() -> dict:
    native = []
    for k, kayit in sorted(native_motion.kayitlar().items()):
        m = kayit.get("meta") or kayit
        native.append(
            {
                "ad": k,
                "tur": m.get("tur", ""),
                "ne_zaman": m.get("ne_zaman", ""),
                "sure": (m.get("sure") or {}).get("varsayilan", 2.0),
                "etiketler": m.get("etiketler", []),
            }
        )
    karakterler = [
        {"ad": a, "baslik": t.get("title", a), "ne_zaman": t.get("ne_zaman", "")}
        for a, t in sorted(karakter.karakterler().items())
    ]
    motion_manifest = paths.MOTION_DIR / "manifest.json"
    entries = (
        json.loads(motion_manifest.read_text(encoding="utf-8")).get("entries", [])
        if motion_manifest.is_file()
        else []
    )
    motionlar = [
        {
            "id": e["id"],
            "title": e.get("title", e["id"]),
            "kind": e.get("kind", "overlay"),
            "file": e.get("file", ""),
        }
        for e in entries
        if isinstance(e, dict) and e.get("id")
    ]
    return {"native": native, "karakterler": karakterler, "motionlar": motionlar}


@router.get("/api/stil/{studyo}")
def stil_liste(studyo: str, proje: str | None = None):
    _studyo(studyo)
    secili = stil.secili_adi(ortak.proje(studyo, proje)) if proje else None
    return {"stiller": stil.liste(studyo), "secili": secili}


@router.put("/api/stil/{studyo}/paket-yukle")
async def paket_yukle(
    studyo: str,
    request: Request,
    dosya: str,
    yeni_ad: str = "",
    uzerine_yaz: bool = False,
):
    _studyo(studyo)
    if yeni_ad.strip():
        _ad(yeni_ad.strip())
    temiz = ortak.dosya_adi(dosya, {".zip"})
    with tempfile.TemporaryDirectory() as gecici:
        temp_zip = await ortak.akisi_yaz(request, Path(gecici) / temiz)
        try:
            sonuc = await run_in_threadpool(
                stil_varlik.paket_zip_ice_al,
                studyo,
                temp_zip,
                yeni_ad=yeni_ad.strip() or None,
                uzerine_yaz=uzerine_yaz,
            )
        except (ValueError, SystemExit) as e:
            kod = 409 if "zaten var" in str(e).lower() else 422
            raise HTTPException(kod, str(e)) from e
    return {"tamam": True, **sonuc}


@router.put("/api/stil/{studyo}/{ad}/referans")
async def referans_yukle(studyo: str, ad: str, dosya: str, request: Request):
    _studyo(studyo)
    _ad(ad)
    temiz = ortak.dosya_adi(dosya, IZINLI)
    f = await ortak.akisi_yaz(request, stil.referans_klasoru(studyo, ad) / temiz)
    return {"boyut": f.stat().st_size, "ad": f.name}


@router.delete("/api/stil/{studyo}/{ad}/referans")
def referans_sil(studyo: str, ad: str, dosya: str):
    _studyo(studyo)
    _ad(ad)
    return {"mesaj": ortak.sil(ortak.kok_ici(stil.referans_klasoru(studyo, ad), dosya))}


@router.get("/api/stil/{studyo}/{ad}/referans/indir")
def referans_indir(studyo: str, ad: str, dosya: str):
    _studyo(studyo)
    _ad(ad)
    f = ortak.kok_ici(stil.referans_klasoru(studyo, ad), dosya)
    return FileResponse(f, filename=f.name, headers={"X-Content-Type-Options": "nosniff"})


@router.get("/api/stil/{studyo}/{ad}/varliklar")
def stil_varliklar_liste(studyo: str, ad: str):
    _studyo(studyo)
    _ad(ad)
    depo = stil_varlik.oku(studyo, ad)
    return {"depo": _depo_dict(studyo, ad, depo), "katalog": _katalog_dict()}


@router.put("/api/stil/{studyo}/{ad}/varlik")
async def stil_varlik_yukle(
    studyo: str,
    ad: str,
    request: Request,
    dosya: str,
    tur: str = "motion",
    baslik: str = "",
    ne_zaman: str = "",
    etiket: str = "",
    yontem: str = "",
    lisans: str = "Kendi üretimim",
    kaynak_url: str = "",
    atif: str = "",
):
    _studyo(studyo)
    _ad(ad)
    if tur not in stil_varlik.TURLER:
        raise HTTPException(400, f"Geçersiz varlık türü: {tur}")
    temiz = ortak.dosya_adi(dosya, stil_varlik.IZINLI_UZANTILAR[tur])
    etiketler = [x.strip() for x in etiket.split(",") if x.strip()]
    with tempfile.TemporaryDirectory() as gecici:
        kaynak = await ortak.akisi_yaz(request, Path(gecici) / temiz)
        try:
            v = await run_in_threadpool(
                lambda: stil_varlik.yukle(
                    studyo,
                    ad,
                    kaynak,
                    tur=tur,
                    baslik=baslik,
                    ne_zaman=ne_zaman,
                    etiketler=etiketler,
                    yontem=yontem.strip() or None,
                    lisans=lisans,
                    kaynak_url=kaynak_url,
                    atif=atif,
                )
            )
        except (ValueError, SystemExit) as e:
            raise HTTPException(422, str(e)) from e
    return {"tamam": True, "varlik": _varlik_dict(studyo, ad, v)}


@router.delete("/api/stil/{studyo}/{ad}/varlik/{vid}")
def stil_varlik_sil(studyo: str, ad: str, vid: str):
    _studyo(studyo)
    _ad(ad)
    try:
        v = stil_varlik.sil(studyo, ad, vid)
    except stil_varlik.VarlikBulunamadi as e:
        raise HTTPException(404, str(e)) from e
    except (ValueError, SystemExit) as e:
        raise HTTPException(400, str(e)) from e
    return {"silinen": v.model_dump()}


@router.put("/api/stil/{studyo}/{ad}/secki")
def stil_secki_kaydet(studyo: str, ad: str, g: StilSecki):
    _studyo(studyo)
    _ad(ad)
    try:
        depo = stil_varlik.secki_guncelle(
            studyo,
            ad,
            secili_native=g.secili_native,
            secili_kutuphane=g.secili_kutuphane,
            yalniz_bunlar=g.yalniz_bunlar,
        )
    except (ValueError, SystemExit) as e:
        raise HTTPException(422, str(e)) from e
    return {"depo": _depo_dict(studyo, ad, depo)}


@router.get("/api/stil/{studyo}/{ad}/varlik/{vid}/onizleme")
def stil_varlik_onizleme(studyo: str, ad: str, vid: str):
    _studyo(studyo)
    _ad(ad)
    try:
        try:
            yol, _ = stil_varlik.varlik_dosyasi(studyo, ad, vid, bicim="poster")
        except stil_varlik.VarlikBulunamadi:
            yol, _ = stil_varlik.varlik_dosyasi(studyo, ad, vid, bicim="normalize")
    except (stil_varlik.VarlikBulunamadi, FileNotFoundError) as e:
        raise HTTPException(404, str(e)) from e
    except (ValueError, SystemExit) as e:
        raise HTTPException(400, str(e)) from e
    baslik = {"Cache-Control": "no-cache", "X-Content-Type-Options": "nosniff"}
    if yol.suffix.lower() == ".svg":
        baslik["Content-Security-Policy"] = "sandbox"
    return FileResponse(yol, headers=baslik)


@router.get("/api/stil/{studyo}/{ad}/varlik/{vid}/indir")
def stil_varlik_indir(studyo: str, ad: str, vid: str, bicim: str = "normalize"):
    _studyo(studyo)
    _ad(ad)
    if bicim not in ("normalize", "orijinal"):
        raise HTTPException(400, "Biçim 'normalize' veya 'orijinal' olmalı")
    try:
        yol, v = stil_varlik.varlik_dosyasi(studyo, ad, vid, bicim=bicim)  # type: ignore[arg-type]
    except (stil_varlik.VarlikBulunamadi, FileNotFoundError) as e:
        raise HTTPException(404, str(e)) from e
    except (ValueError, SystemExit) as e:
        raise HTTPException(400, str(e)) from e
    return FileResponse(
        yol,
        filename=f"{ad}-{v.id}{yol.suffix}",
        headers={"X-Content-Type-Options": "nosniff"},
    )


@router.post("/api/stil/{studyo}/{ad}/native-indir")
async def stil_native_indir(studyo: str, ad: str, g: NativeIndir):
    _studyo(studyo)
    _ad(ad)
    if g.en_boy not in ("1:1", "9:16", "16:9"):
        raise HTTPException(400, "Geçersiz en_boy (1:1, 9:16, 16:9 olmalı)")
    try:
        yol = await run_in_threadpool(
            stil_varlik.native_disa_aktar,
            studyo,
            ad,
            g.ad,
            param=g.param,
            en_boy=g.en_boy,  # type: ignore[arg-type]
            sure=g.sure,
        )
    except (ValueError, SystemExit, subprocess.CalledProcessError) as e:
        raise HTTPException(422, str(e)) from e
    dosya_adi = f"{ad}-{g.ad.replace('/', '-')}.webm"
    return FileResponse(
        yol,
        media_type="video/webm",
        filename=dosya_adi,
        headers={"X-Content-Type-Options": "nosniff"},
    )


@router.get("/api/stil/{studyo}/{ad}/paket.zip")
def stil_paket_indir(studyo: str, ad: str):
    _studyo(studyo)
    _ad(ad)
    gecici_klasor = Path(tempfile.mkdtemp(prefix="vedit-stil-zip-"))
    hedef = gecici_klasor / f"{studyo}-{ad}.zip"
    try:
        stil_varlik.paket_zip_uret(studyo, ad, hedef)
    except (ValueError, SystemExit) as e:
        shutil.rmtree(gecici_klasor, ignore_errors=True)
        kod = 404 if "bulunamadı" in str(e).lower() else 422
        raise HTTPException(kod, str(e)) from e
    return FileResponse(
        hedef,
        media_type="application/zip",
        filename=f"{studyo}-{ad}.zip",
        headers={"X-Content-Type-Options": "nosniff"},
        background=BackgroundTask(shutil.rmtree, gecici_klasor, True),
    )


@router.put("/api/stil/{studyo}/{ad}")
def stil_kaydet(studyo: str, ad: str, g: StilKaydet):
    _studyo(studyo)
    _ad(ad)
    if len(g.style_md) > 20000:
        raise HTTPException(422, "STYLE.md en çok 20000 karakter olabilir")
    try:
        stil.kaydet(studyo, ad, g.style_md)
    except SystemExit as e:
        raise HTTPException(422, str(e)) from e
    return {"tamam": True}


@router.delete("/api/stil/{studyo}/{ad}")
def stil_sil(studyo: str, ad: str):
    _studyo(studyo)
    _ad(ad)
    try:
        silinen = stil.sil(studyo, ad)
    except SystemExit as e:
        raise HTTPException(404, str(e)) from e
    return {"silinen": silinen}


@router.post("/api/stil/{studyo}/sec")
def stil_sec(studyo: str, g: StilSec):
    _studyo(studyo)
    ad = _ad(g.stil)
    p = ortak.proje(studyo, g.proje)
    try:
        stil.sec(p, ad)
    except SystemExit as e:
        raise HTTPException(422, str(e)) from e
    return {"secili": ad}


# WHY: bkz. wiki/decisions/0042-stil-katalogu-ve-video-temasi.md. Hazır stil kataloğu: anime, çizgi film, editoryal...
@router.get("/api/stil-katalog")
def katalog():
    return {"kategoriler": stil_katalog.yukle()["kategoriler"], "stiller": stil_katalog.liste()}


@router.get("/api/stil-katalog/{kimlik}/onizleme")
def katalog_onizleme(kimlik: str):
    _ad(kimlik)
    f = stil_katalog.onizleme_yolu(kimlik)
    if not f.is_file():
        raise HTTPException(404, "Önizleme yok: vedit stil-katalog kur")
    return FileResponse(f, media_type="image/jpeg", headers={"Cache-Control": "no-cache"})


@router.get("/api/stil-katalog/{kimlik}/kart")
def katalog_kart(kimlik: str):
    """Stil kartı (ADR 0043): altyazı, alt bant, ikon, ok, sayaç, grafik, karşılaştırma, geçiş tek görselde."""
    from .. import stil_kart
    _ad(kimlik)
    f = stil_kart.kart_yolu(kimlik)
    if not f.is_file():
        raise HTTPException(404, "Kart yok: vedit stil-katalog kart")
    return FileResponse(f, media_type="image/jpeg", headers={"Cache-Control": "no-cache"})


@router.post("/api/stil/{studyo}/katalogdan")
def katalogdan_ekle(studyo: str, g: KatalogdanEkle):
    _studyo(studyo)
    _ad(g.id)
    p = ortak.proje(studyo, g.proje) if g.proje else None
    try:
        hedef = stil_katalog.ekle(studyo, g.id, p)
    except SystemExit as e:
        raise HTTPException(409 if "zaten var" in str(e) else 422, str(e)) from e
    return {"stil": g.id, "yol": paths.rel(hedef), "secili": g.id if p else None}
