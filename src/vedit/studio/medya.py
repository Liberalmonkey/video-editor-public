"""Proje, girdi ve çıktı dosyaları: listele, yükle, sil, küçük resim."""

from __future__ import annotations

import hashlib
import os
import re
import subprocess
from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel

from .. import ff, hizli, kurgu, paths
from . import ortak

YUKLENEBILIR = hizli.MEDYA | hizli.GORSEL | {".md", ".txt", ".srt", ".json"}
METIN = {".md", ".txt", ".srt", ".json"}
router = APIRouter()
_sure_onbellek: dict[tuple[str, int, int], float | None] = {}


def tur_bul(ad: str) -> str:
    uz = Path(ad).suffix.lower()
    if uz in hizli.VIDEO:
        return "video"
    if uz in hizli.MEDYA:
        return "ses"
    if uz in hizli.GORSEL:
        return "gorsel"
    return "metin" if uz in METIN else "diger"


def _sure(f: Path, st: os.stat_result) -> float | None:
    anahtar = (str(f), st.st_size, st.st_mtime_ns)
    if anahtar not in _sure_onbellek:
        try:
            _sure_onbellek[anahtar] = ff.probe(f).get("duration")
        except Exception:  # WHY: bozuk tek dosya listeyi düşürmemeli
            _sure_onbellek[anahtar] = None
    return _sure_onbellek[anahtar]


def bolge_kok(p: hizli.Proje, bolge: str) -> Path:
    if bolge == "inputs":
        return p.girdi
    if bolge == "outputs":
        return p.cikti
    raise HTTPException(404, "Bölge yok")


def listele(p: hizli.Proje, bolge: str) -> list[dict]:
    kok = bolge_kok(p, bolge)
    if not kok.exists():
        return []
    cikti = []
    for f in kok.rglob("*"):
        rel = f.relative_to(kok).as_posix()
        # WHY: work/ ara dosyadır (ADR 0017); kullanıcı teslimleri ve girdileri görür.
        if not f.is_file() or rel.startswith("work/") or f.name.startswith("."):
            continue
        st, tur = f.stat(), tur_bul(f.name)
        cikti.append({"yol": rel, "ad": f.name, "tur": tur, "boyut": st.st_size, "degisme": st.st_mtime,
                      "sure": _sure(f, st) if tur in ("video", "ses") else None,
                      "url": f"/dosya/{p.studyo}/{p.ad}/{bolge}/{quote(rel)}"})
    return sorted(cikti, key=lambda d: hizli.dogal(d["yol"]))


@router.get("/api/projeler")
def projeler():
    bulunan: dict[tuple[str, str], dict] = {}
    for kok in (paths.INPUTS, paths.OUTPUTS):
        for d in kok.glob("*/*"):
            if d.is_dir() and not d.name.startswith((".", "_")) and not d.parent.name.startswith((".", "_")):
                bulunan[(d.parent.name, d.name)] = {"studyo": d.parent.name, "ad": d.name}
    for (s, a), kayit in bulunan.items():
        work = hizli.Proje(s, a).work
        kayit["kurgu"] = kurgu.yol(work).exists()
        kayit["props"] = (work / "edit" / "props.json").exists()
    return {"studyolar": list(paths.STUDIO_NAMES),
            "projeler": sorted(bulunan.values(), key=lambda x: (x["studyo"], hizli.dogal(x["ad"])))}


class YeniProje(BaseModel):
    studyo: str
    ad: str


@router.post("/api/projeler")
def proje_olustur(y: YeniProje):
    if y.studyo not in paths.STUDIO_NAMES:
        raise HTTPException(400, "Bilinmeyen stüdyo")
    ad = re.sub(r"[^\w\-]+", "-", y.ad.strip(), flags=re.UNICODE).strip("-").casefold()
    if not ad:
        raise HTTPException(400, "Proje adı boş olamaz")
    p = ortak.proje(y.studyo, ad)
    if p.girdi.exists() or p.cikti.exists():
        raise HTTPException(409, f"Bu adda proje var: {ad}")
    p.girdi.mkdir(parents=True)
    return {"studyo": y.studyo, "ad": ad}


@router.delete("/api/projeler/{studyo}/{ad}")
def proje_sil(studyo: str, ad: str):
    p = ortak.proje(studyo, ad)
    mesajlar = [ortak.sil(d) for d in (p.girdi, p.cikti) if d.exists()]
    if not mesajlar:
        raise HTTPException(404, "Proje yok")
    return {"mesaj": "; ".join(dict.fromkeys(mesajlar))}


@router.get("/api/dosyalar/{studyo}/{ad}/{bolge}")
def dosyalar(studyo: str, ad: str, bolge: str):
    return listele(ortak.proje(studyo, ad), bolge)


@router.put("/api/yukle/{studyo}/{ad}")
async def yukle(studyo: str, ad: str, dosya: str, request: Request):
    p = ortak.proje(studyo, ad)
    temiz = ortak.dosya_adi(dosya, YUKLENEBILIR)
    f = await ortak.akisi_yaz(request, p.girdi / temiz)
    return {"boyut": f.stat().st_size, "ad": f.name}


@router.delete("/api/dosya/{studyo}/{ad}/{bolge}")
def dosya_sil(studyo: str, ad: str, bolge: str, yol: str):
    p = ortak.proje(studyo, ad)
    if yol.startswith("work/"):
        raise HTTPException(403, "work/ arayüzden silinmez")
    return {"mesaj": ortak.sil(ortak.kok_ici(bolge_kok(p, bolge), yol))}


@router.post("/api/klasor-ac/{studyo}/{ad}/{bolge}")
def klasor_ac(studyo: str, ad: str, bolge: str):
    kok = bolge_kok(ortak.proje(studyo, ad), bolge)
    kok.mkdir(parents=True, exist_ok=True)
    if os.name == "nt":
        os.startfile(kok)  # noqa: S606  kök sunucu tarafından çözüldü, kullanıcı girdisi yol değil
    else:
        subprocess.Popen(["xdg-open", str(kok)])
    return {"tamam": True}


@router.get("/api/kucuk/{studyo}/{ad}/{bolge}")
def kucuk(studyo: str, ad: str, bolge: str, yol: str):
    p = ortak.proje(studyo, ad)
    f = ortak.kok_ici(bolge_kok(p, bolge), yol)
    if tur_bul(f.name) == "gorsel":  # WHY: görsel zaten karedir; ffmpeg seek'i tek kareli dosyada başarısız olur
        return FileResponse(f, headers={"Cache-Control": "max-age=86400", "X-Content-Type-Options": "nosniff"})
    st = f.stat()
    anahtar = hashlib.sha1(f"{f}|{st.st_size}|{st.st_mtime_ns}".encode()).hexdigest()[:16]
    hedef = p.work / "kucuk" / f"{anahtar}.jpg"
    if not hedef.exists():
        hedef.parent.mkdir(parents=True, exist_ok=True)
        try:
            ff.still(f, hedef, min(1.0, _sure(f, st) or 0) if tur_bul(f.name) == "video" else 0, width=320)
        except Exception as e:
            raise HTTPException(415, "Küçük resim üretilemedi") from e
    return FileResponse(hedef, headers={"Cache-Control": "max-age=86400"})
