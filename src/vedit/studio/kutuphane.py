"""Kütüphane: SFX, müzik, motion, pano, font. Kilit ve kit kuralları ADR 0012.

WHY: manifest tek kayıt yeridir; dosya ve kayıt birlikte değişir. Lisans zorunludur (ADR 0008).
"""

from __future__ import annotations

import json
import re
import threading
import tempfile
from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel

from .. import ff, kasa, motion, motion_ice, paths, sfx
from . import ortak

SES = sfx.AUDIO_EXT
MOTION = {".mp4", ".mov", ".webm", ".mkv", ".json", ".lottie", ".gif", ".apng", ".png", ".svg"}
FONT = {".ttf", ".otf", ".woff2"}
KORUNAN_FONT = {"Montserrat", "Inter", "Space Grotesk", "JetBrains Mono"}  # ADR 0014 ve SplitReel
router = APIRouter()
_kilit = threading.Lock()


def _oku(y: Path) -> dict:
    return json.loads(y.read_text(encoding="utf-8"))


def _kit() -> dict:
    return _oku(paths.LIBRARY / "kit.json")


def _url(rel: str) -> str:
    return "/lib/" + quote(rel.removeprefix("library/"))


def _bosluk(s: str) -> str:
    return re.sub(r"[^\w\-]+", "-", s.strip(), flags=re.UNICODE).strip("-").casefold()


@router.get("/api/kutuphane")
def liste():
    kit = _kit()
    kilitli, yuvalar = set(kit.get("locked", [])), kit.get("always", {})
    atanan = {v for roller in yuvalar.values() for v in roller.values() if v}
    def isle(e: dict) -> dict:
        return {**e, **({"url": _url(e["file"])} if e.get("file") else {}), "kilitli": e["id"] in kilitli, "yuvada": e["id"] in atanan,
                **({"poster_url": _url(e["poster"])} if e.get("poster") else {}),
                **({"onizleme_url": _url(e["onizleme"])} if e.get("onizleme") else {})}

    def motion_isle(e: dict) -> dict:
        # WHY: bkz. wiki/decisions/0061-kasa-ve-kesif.md. Eski custom kayıtlar silinmez, varsayılan görünümden
        # Arşiv'e iner (eski). AI edit onları seçmeye devam eder: Keşif paketi yerini alana dek yetenek kaybı olmasın.
        r = isle(e)
        # Tema token'ıyla yeniden üretilen şablonlar (param) Keşif'te kalır; yalnız sabit eski grafik iner.
        if e.get("site") == "custom" and not e.get("arsiv") and not e.get("param"):
            r["eski"] = True
        return r
    fontlar = _oku(paths.FONTS_DIR / "fonts.json")
    return {
        "sfx": [isle(e) for e in _oku(paths.SFX_DIR / "manifest.json")["entries"]],
        "muzik": [isle(e) for e in _oku(paths.MUSIC_DIR / "manifest.json")["entries"]],
        "motion": [motion_isle(e) for e in _oku(paths.MOTION_DIR / "manifest.json")["entries"]],
        "kasa": [isle(e) for e in kasa.oku()],
        "pano": [{"id": b["file"], "title": b.get("title", b["file"]), "animated": b.get("animated", False),
                  "url": f"/lib/boards/boards/{quote(b['file'])}"} for b in _oku(paths.LIBRARY / "boards" / "catalog.json")],
        "font": [{"id": ad, **v, "url": f"/lib/fonts/{quote(v['file'])}", "kilitli": ad in KORUNAN_FONT}
                 for ad, v in fontlar.items() if not ad.startswith("_")],
        "kit": {"locked": kit.get("locked", []), "always": yuvalar},
        "temalar": motion.temalar(),
    }


def kullanimda(rel: str) -> list[str]:
    """Bu dosyayı kaynak gösteren projeler. Uyarı içindir; kurgu ve olaylar taranır."""
    ic = rel.removeprefix("library/")
    bulunan = []
    for work in paths.OUTPUTS.glob("*/*/work"):
        for ad in ("kurgu.json", "olaylar.json"):
            f = work / "edit" / ad
            if f.exists() and (ic in f.read_text(encoding="utf-8")):
                bulunan.append(f"{work.parent.parent.name}/{work.parent.name}")
                break
    return bulunan


def _kilit_kaldir(eid: str) -> list[str]:
    """Kimliği kit.json kilidinden ve atandığı yuvalardan çıkarır; boşalan yuvaları döner. WHY: ADR 0061, çıkmaz 403 yerine onaylı yol."""
    y = paths.LIBRARY / "kit.json"
    kit = _oku(y)
    kit["locked"] = [x for x in kit.get("locked", []) if x != eid]
    bos = []
    for s, roller in kit.get("always", {}).items():
        for r, v in roller.items():
            if v == eid:
                roller[r] = None
                bos.append(f"{s}.{r}")
    ortak.json_yaz(y, kit)
    return bos


def _silme_denetimi(eid: str, rel: str, zorla: bool, kit: dict) -> None:
    if eid in kit.get("locked", []):
        # 423: arayüz "Kilidi kaldır ve sil" onayı sorar (ADR 0061); onaylanınca kilit_ac=true ile yeniden gelir
        raise HTTPException(423, json.dumps({"kilitli": eid}, ensure_ascii=False))
    yuva = [f"{s}.{r}" for s, roller in kit.get("always", {}).items() for r, v in roller.items() if v == eid]
    projeler = kullanimda(rel)
    if (yuva or projeler) and not zorla:
        raise HTTPException(409, json.dumps({"yuva": yuva, "projeler": projeler}, ensure_ascii=False))


def _sidecar_temizle(raw: Path) -> None:
    """Silinen dosyanın source.json kaydı kalmasın: aynı ad yeniden yüklenince eski kategoriyi almasın."""
    sc = raw.parent / "source.json"
    if sc.exists():
        v = _oku(sc)
        if raw.name in v.get("files", {}):
            v["files"].pop(raw.name)
            ortak.json_yaz(sc, v)


@router.delete("/api/kutuphane/{tur}/{eid}")
def sil(tur: str, eid: str, zorla: bool = False, kilit_ac: bool = False):
    if tur == "kasa":
        try:
            kasa.sil(eid)
        except KeyError:
            raise HTTPException(404, "Kayıt yok") from None
        return {"mesaj": f"{eid} kasadan silindi, dosya geri dönüşüm kutusunda"}
    if kilit_ac:
        with _kilit:
            bos = _kilit_kaldir(eid)
        if bos:
            zorla = True  # yuva boşaltıldı; kullanıcı onayladı
    kit = _kit()
    if tur == "font":
        return _font_sil(eid)
    manifest = {"sfx": paths.SFX_DIR, "muzik": paths.MUSIC_DIR, "motion": paths.MOTION_DIR}.get(tur)
    if manifest is None:
        raise HTTPException(404, "Bu tür silinemez")
    with _kilit:
        y = manifest / "manifest.json"
        veri = _oku(y)
        e = next((x for x in veri["entries"] if x["id"] == eid), None)
        if not e:
            raise HTTPException(404, "Kayıt yok")
        _silme_denetimi(eid, e["file"], zorla, kit)
        if e.get("dis"):
            # WHY: ADR 0046. Dış varlık klasördür (orijinal, normalize, poster, meta.json); meta kalırsa manifest geri getirir.
            klasor = (paths.ROOT / e["file"]).parent
            if klasor.resolve().is_relative_to((paths.MOTION_DIR / "dis").resolve()) and klasor.is_dir():
                ortak.sil(klasor)
            veri["entries"] = [x for x in veri["entries"] if x["id"] != eid]
            ortak.json_yaz(y, veri)
            return {"mesaj": f"{eid} silindi, klasör geri dönüşüm kutusunda"}
        # WHY: SFX ham dosyası kalırsa bir sonraki `sfx index` kaydı geri getirir.
        for rel in (e["file"], e.get("raw")):
            f = paths.ROOT / rel if rel else None
            if f and f.is_file() and f.resolve().is_relative_to(paths.LIBRARY.resolve()):
                ortak.sil(f)
        if e.get("raw"):
            _sidecar_temizle(paths.ROOT / e["raw"])
        veri["entries"] = [x for x in veri["entries"] if x["id"] != eid]
        ortak.json_yaz(y, veri)
    return {"mesaj": f"{eid} silindi, dosya geri dönüşüm kutusunda"}


def _font_sil(ad: str):
    if ad in KORUNAN_FONT:
        raise HTTPException(403, f"{ad} korunuyor: altyazı standardı ve sahneler kullanır.")
    with _kilit:
        y = paths.FONTS_DIR / "fonts.json"
        veri = _oku(y)
        if ad not in veri or ad.startswith("_"):
            raise HTTPException(404, "Font yok")
        ortak.sil(ortak.kok_ici(paths.FONTS_DIR, veri[ad]["file"]))
        veri.pop(ad)
        ortak.json_yaz(y, veri)
    return {"mesaj": f"{ad} silindi"}


def _lisans(l: str) -> str:
    if not l.strip():
        raise HTTPException(422, "Lisans zorunlu (ADR 0008)")
    return l.strip()


def _sfx_kaydet(temiz: str, klasor: Path, lisans: str, kategori: str, url: str, atif: str) -> dict:
    """source.json'a dosya kaydını ekler, mevcut `sfx.index` işler (normalize, tepe, LUFS)."""
    with _kilit:
        sc_yol = klasor / "source.json"
        sc = _oku(sc_yol) if sc_yol.exists() else {"source": "kullanici", "license": lisans, "source_url": url, "attribution": atif or None, "files": {}}
        sc["files"].setdefault(temiz, {})
        if kategori:
            sc["files"][temiz]["category"] = kategori
        if url:
            sc["files"][temiz]["url"] = url
        ortak.json_yaz(sc_yol, sc)
        return sfx.index()


@router.put("/api/kutuphane/sfx")
async def sfx_yukle(request: Request, dosya: str, lisans: str, kategori: str = "", url: str = "", atif: str = ""):
    temiz = ortak.dosya_adi(dosya, SES)
    # WHY: source.json klasör başına tek lisans taşır; lisansa göre klasör, kayıtlar karışmaz.
    klasor = sfx.RAW / "kullanici" / (_bosluk(_lisans(lisans)) or "lisans")
    hedef = ortak.bos_ad(klasor, temiz)
    await ortak.akisi_yaz(request, hedef)
    sonuc = await run_in_threadpool(_sfx_kaydet, hedef.name, klasor, lisans, _bosluk(kategori), url, atif)
    if not sonuc["added"]:
        ortak.sil(hedef)
        raise HTTPException(422, "Ses işlenemedi: " + "; ".join(sonuc["skipped"][:2]))
    return sonuc


def _ekle(y: Path, kayit: dict) -> None:
    with _kilit:
        veri = _oku(y)
        if any(e["id"] == kayit["id"] for e in veri["entries"]):
            kayit["id"] = f"{kayit['id']}-{len(veri['entries'])}"
        veri["entries"].append(kayit)
        ortak.json_yaz(y, veri)


@router.put("/api/kutuphane/muzik")
async def muzik_yukle(request: Request, dosya: str, lisans: str, baslik: str = "", sanatci: str = "", site: str = "kullanici",
                      duygu: str = "", tur: str = "", url: str = "", atif: str = ""):
    temiz = ortak.dosya_adi(dosya, SES)
    klasor = paths.MUSIC_DIR / (_bosluk(site) or "kullanici")
    hedef = ortak.bos_ad(klasor, temiz)
    _lisans(lisans)
    await ortak.akisi_yaz(request, hedef)
    sure = (await run_in_threadpool(ff.probe, hedef))["duration"]
    _ekle(paths.MUSIC_DIR / "manifest.json", {
        "id": _bosluk(hedef.stem), "file": hedef.relative_to(paths.ROOT).as_posix(), "title": baslik or hedef.stem, "artist": sanatci,
        "site": klasor.name, "mood": [d.strip() for d in duygu.split(",") if d.strip()], "genre": tur, "bpm": None, "energy": None,
        "vocals": None, "duration_s": sure, "license": lisans.strip(), "source_url": url, "attribution": atif or None, "used_in": []})
    return {"tamam": True}


@router.put("/api/kutuphane/motion")
async def motion_yukle(request: Request, dosya: str, site: str, lisans: str = "", baslik: str = "", kind: str = "overlay",
                       url: str = "", atif: str = "", atif_gerekli: bool = False, kisit: str = "", yontem: str = "",
                       ne_zaman: str = "", etiket: str = ""):
    """Dış varlık içe aktarma (ADR 0046): lisans kaydı zorunlu; alfa yöntemi bulunur, normalize dosya ve poster üretilir."""
    temiz = ortak.dosya_adi(dosya, MOTION)
    kaynak = _bosluk(site) or "kullanici"
    try:
        li = motion_ice.lisans_kur(kaynak, url=url or None, lisans=lisans or None, atif_gerekli=atif_gerekli or None,
                                   atif_metni=atif, kisitlar=[k.strip() for k in kisit.split(",") if k.strip()] or None)
    except motion_ice.LisansHatasi as e:
        raise HTTPException(422, f"Lisans kaydı zorunlu (ADR 0046): {e}") from e
    with tempfile.TemporaryDirectory() as gecici:
        hedef = Path(gecici) / temiz
        await ortak.akisi_yaz(request, hedef)
        try:
            e = await run_in_threadpool(lambda: motion_ice.ice_al(
                hedef, li, ad=baslik or None, tur=kind, ne_zaman=ne_zaman, yontem=yontem or None,
                etiketler=[x.strip() for x in etiket.split(",") if x.strip()]))
        except (motion_ice.LisansHatasi, ValueError) as er:
            raise HTTPException(422, str(er)) from er
    with _kilit:
        motion_ice.manifest_yenile()
    return {"tamam": True, "kayit": e}


@router.put("/api/kutuphane/font")
async def font_yukle(request: Request, dosya: str, lisans: str, ad: str, rol: str = "display"):
    temiz = ortak.dosya_adi(dosya, FONT)
    _lisans(lisans)
    ad = ad.strip()
    if not ad or ad.startswith("_"):
        raise HTTPException(422, "Font adı geçersiz")
    hedef = ortak.bos_ad(paths.FONTS_DIR, temiz)
    await ortak.akisi_yaz(request, hedef)
    with _kilit:
        y = paths.FONTS_DIR / "fonts.json"
        veri = _oku(y)
        if ad in veri:
            ortak.sil(hedef)
            raise HTTPException(409, f"Bu adda font var: {ad}")
        veri[ad] = {"file": hedef.name, "weight": "100 900", "role": rol, "license": lisans.strip()}
        ortak.json_yaz(y, veri)
    return {"tamam": True}


class TopluSil(BaseModel):
    tur: str
    idler: list[str]
    zorla: bool = False
    kilit_ac: bool = False


@router.post("/api/kutuphane/toplu-sil")
def toplu_sil(g: TopluSil):
    """Birden çok kaydı siler; her biri için sonuç. Kilitli ya da kullanımdaki kayıt `zorla`/`kilit_ac` yoksa atlanır."""
    if len(g.idler) > 500:
        raise HTTPException(422, "Tek seferde en çok 500 kayıt")
    silinen, atlanan = [], []
    for eid in g.idler:
        try:
            sil(g.tur, eid, zorla=g.zorla, kilit_ac=g.kilit_ac)
            silinen.append(eid)
        except HTTPException as e:
            atlanan.append({"id": eid, "durum": e.status_code, "neden": e.detail})
    return {"silinen": silinen, "atlanan": atlanan,
            "mesaj": f"{len(silinen)} kayıt silindi" + (f", {len(atlanan)} atlandı" if atlanan else "")}


class KasaKayit(BaseModel):
    klip: str
    ad: str | None = None


@router.post("/api/kasa/kaydet/{studyo}/{ad}")
async def kasa_kaydet(studyo: str, ad: str, g: KasaKayit):
    """Timeline klibini kasaya kaydeder (ADR 0061). Kurgu diskten okunur: arayüz önce kaydeder."""
    p = ortak.proje(studyo, ad)
    try:
        e = await run_in_threadpool(kasa.kaydet, p, g.klip, (g.ad or "").strip()[:60] or None)
    except ValueError as er:
        raise HTTPException(422, str(er)) from er
    return {"tamam": True, "kayit": e, "mesaj": f"Kasaya kaydedildi: {e['title']}"}


class Gizle(BaseModel):
    anahtar: str
    gizle: bool = True


@router.post("/api/galeri/gizle")
def galeri_gizle(g: Gizle):
    """Kodla tanımlı galeri öğesi (fizik, ışık, karakter, efekt, stil) silinemez; gizlenir. Anahtar `tur:id`."""
    if not re.fullmatch(r"[a-z]+:[\w\-/.]{1,120}", g.anahtar):
        raise HTTPException(422, "Geçersiz anahtar")
    return {"gizli": sorted(kasa.gizle(g.anahtar, g.gizle))}


class Kilit(BaseModel):
    id: str
    kilitli: bool


@router.put("/api/kit/kilit")
def kit_kilit(k: Kilit):
    """Varlığı kilitler ya da kilidini kaldırır (ADR 0012, 0061). Kilit yalnız kullanıcı isteğiyle değişir: bu uç arayüzden çağrılır."""
    with _kilit:
        if k.kilitli:
            y = paths.LIBRARY / "kit.json"
            kit = _oku(y)
            if k.id not in kit.setdefault("locked", []):
                kit["locked"].append(k.id)
            ortak.json_yaz(y, kit)
            return {"tamam": True, "bos_yuva": []}
        return {"tamam": True, "bos_yuva": _kilit_kaldir(k.id)}


class KitYuva(BaseModel):
    studyo: str
    rol: str
    id: str | None


@router.put("/api/kit")
def kit_ata(k: KitYuva):
    with _kilit:
        y = paths.LIBRARY / "kit.json"
        kit = _oku(y)
        roller = kit.setdefault("always", {}).setdefault(k.studyo, {})
        if roller.get(k.rol) in kit.get("locked", []):
            raise HTTPException(403, f"{k.rol} yuvası kilitli (ADR 0012)")
        roller[k.rol] = k.id
        ortak.json_yaz(y, kit)
    return {"tamam": True}


@router.get("/lib/{ic:path}")
def lib(ic: str):
    f = ortak.kok_ici(paths.LIBRARY, ic)
    baslik = {"X-Content-Type-Options": "nosniff"}
    # WHY: pano HTML'i betik çalıştırır; kendi kökünde sandbox, API'ye ve çereze erişemez.
    if f.suffix.lower() in (".html", ".htm", ".svg"):
        baslik["Content-Security-Policy"] = "sandbox allow-scripts"
    return FileResponse(f, headers=baslik)
