"""Kasa: kullanıcının videodan kaydettiği motion, şablon, HyperFrames kompozisyonu, bileşen ve ses efekti.

WHY: bkz. wiki/decisions/0061-kasa-ve-kesif.md. Kullanıcı hibrit kütüphaneyi seçti (2026-11-25). Varsayılan görünüm
yalnız kendi onayladığı varlıklardır ("Kasam"); hazır paket "Keşif"te, eski 114 kayıt "Arşiv"de. Kayıt niyeti saklar:
şablon ve kompozisyon parametresiyle, bileşen param'ıyla kaydedilir, yalnız pişmiş webm değil. Böylece tema değişince
yeniden üretilir. Önizleme `onizleme.uret` ile alfa kırpımlı.
"""

from __future__ import annotations

import datetime as dt
import json
import re
import shutil
import threading
from pathlib import Path

from . import ff, kurgu, paths

HF_ONEK = "kasa-"  # library/motion/hf/kasa-<id>/: hf_grafik.bul ile çözülür
_kilit = threading.Lock()
SES_UZANTI = {".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg"}


def kok() -> Path:
    """Yol çağrı anında çözülür: testte ve taşınmış kökte kütüphane yolu değişebilir."""
    return paths.LIBRARY / "kasa"


def manifest_yolu() -> Path:
    return kok() / "manifest.json"


def oku() -> list[dict]:
    try:
        return json.loads(manifest_yolu().read_text(encoding="utf-8")).get("entries", [])
    except (OSError, ValueError):
        return []


def _yaz(kayitlar: list[dict]) -> None:
    kok().mkdir(parents=True, exist_ok=True)
    gecici = manifest_yolu().with_name(".manifest.tmp")
    gecici.write_text(json.dumps({"_not": "Kasa (ADR 0061): elle yazılmaz; Stüdyo > Kütüphane > Motion > Kasam ya da "
                                          "timeline klibinde 'Kütüphaneye kaydet'.", "entries": kayitlar},
                                 ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    gecici.replace(manifest_yolu())


def _kimlik(ad: str, mevcut: set[str]) -> str:
    taban = re.sub(r"[^a-z0-9]+", "-", ad.casefold().translate(str.maketrans("çğıöşü", "cgiosu"))).strip("-")[:40] or "kayit"
    k, n = taban, 2
    while k in mevcut:
        k, n = f"{taban}-{n}", n + 1
    return k


def _lisans(yol: str) -> tuple[str, str | None]:
    """Kaynak kütüphanedeyse manifest lisansı ve atfı; proje dosyası kullanıcınındır."""
    if not yol.startswith("library:"):
        return "kullanici", None
    ic = "library/" + yol.split(":", 1)[1]
    for d in (paths.SFX_DIR, paths.MUSIC_DIR, paths.MOTION_DIR):
        try:
            for e in json.loads((d / "manifest.json").read_text(encoding="utf-8"))["entries"]:
                if e.get("file") == ic:
                    return e.get("license") or "bilinmiyor", e.get("attribution")
        except (OSError, ValueError, KeyError):
            continue
    return "bilinmiyor", None


def kaydet(p, klip_id: str, ad: str | None = None) -> dict:
    """Projedeki klibi kasaya kaydeder; manifest kaydını döner. Desteklenmeyen klipte ValueError."""
    k = kurgu.oku(p.work)
    c = next((x for x in k.klipler if x.id == klip_id), None)
    if c is None:
        raise ValueError(f"Klip yok: {klip_id}")
    kay = k.kaynaklar.get(c.kaynak) if c.kaynak else None
    dosya = kurgu.dosya(p, kay.yol) if kay else None
    baslik = ad or (c.sablon or {}).get("ad") or (c.hf or {}).get("ad") or (c.bilesen.ad if c.bilesen else None) \
        or (c.olay or {}).get("tur") or (Path(kay.yol.split(":", 1)[1]).stem if kay else c.id)
    with _kilit:
        kayitlar = oku()
        kid = _kimlik(str(baslik), {e["id"] for e in kayitlar})
    klasor = kok() / kid
    klasor.mkdir(parents=True, exist_ok=True)
    kayit: dict = {"id": kid, "title": str(baslik), "kaynak": {"proje": f"{p.studyo}/{p.ad}", "klip": c.id},
                   "olusturma": dt.datetime.now().isoformat(timespec="seconds"), "sure": round(c.sure, 3)}
    try:
        if c.tur == "ses":
            if not dosya or dosya.suffix.lower() not in SES_UZANTI or not dosya.is_file():
                raise ValueError("Bu ses klibinin dosyası yok (rol olayı): ses efekti kütüphaneden seçilir, kaydedilemez.")
            hedef = klasor / f"{kid}{dosya.suffix.lower()}"
            shutil.copyfile(dosya, hedef)
            lisans, atif = _lisans(kay.yol)
            kayit.update(tur="sfx", file=_rel(hedef), license=lisans, attribution=atif, ses=c.ses.model_dump() if c.ses else None)
        elif c.tur == "motion" or c.tur == "gorsel":
            if c.bilesen:
                kayit.update(tur="bilesen", bilesen=c.bilesen.model_dump(), license="project-made")
                _taslak_karesi(p, c, klasor)
            else:
                if not dosya or not dosya.is_file():
                    raise ValueError("Klibin dosyası bulunamadı; önce taslak al ki motion üretilsin.")
                hedef = klasor / f"{kid}{dosya.suffix.lower()}"
                shutil.copyfile(dosya, hedef)
                lisans, atif = _lisans(kay.yol)
                kayit.update(tur="motion" if c.tur == "motion" else "gorsel", file=_rel(hedef), license=lisans, attribution=atif)
                if c.sablon:
                    kayit.update(tur="sablon", sablon=dict(c.sablon))
                if c.hf:
                    kayit.update(tur="hf", hf=_hf_tasi(p, c.hf, kid))
                if c.tur == "motion":
                    _onizle(hedef, klasor, kayit)
        else:
            raise ValueError(f"'{c.tur}' klibi kasaya kaydedilmez: motion, şablon, kompozisyon, bileşen ya da ses efekti seç.")
    except Exception:
        shutil.rmtree(klasor, ignore_errors=True)
        raise
    if (klasor / "poster.jpg").is_file():
        kayit["poster"] = _rel(klasor / "poster.jpg")
    if (klasor / "onizleme.mp4").is_file():
        kayit["onizleme"] = _rel(klasor / "onizleme.mp4")
    with _kilit:
        kayitlar = oku()
        kayitlar.append(kayit)
        _yaz(kayitlar)
    return kayit


def _rel(f: Path) -> str:
    return f.relative_to(paths.ROOT).as_posix()


def _hf_tasi(p, hf: dict, kid: str) -> dict:
    """Projeye özel kompozisyon (work/edit/hf/<ad>) kütüphaneye kopyalanır; kütüphanedeki olduğu gibi kalır."""
    from . import hf_grafik
    kaynak = hf_grafik.bul(hf["ad"], p.work)
    if kaynak and kaynak.is_relative_to(hf_grafik.proje_kok(p.work)):
        hedef = hf_grafik.KUTUPHANE / f"{HF_ONEK}{kid}"
        shutil.copytree(kaynak, hedef, dirs_exist_ok=True, ignore=shutil.ignore_patterns(*hf_grafik.ATLA))
        return {**hf, "ad": hedef.name}
    return dict(hf)


def _onizle(webm: Path, klasor: Path, kayit: dict) -> None:
    from . import onizleme
    v = ff.probe(webm)
    vv = v.get("video") or {}
    if vv:
        kayit.update(width=vv["width"], height=vv["height"])
        onizleme.uret(webm, klasor, w=vv["width"], h=vv["height"], sure=v["duration"] or kayit["sure"])


def _taslak_karesi(p, c, klasor: Path) -> None:
    """Bileşenin kendi dosyası yok: son taslaktan klibin ortasındaki kare poster olur (yoksa poster yok)."""
    taslak = p.work / "renders" / "taslak.mp4"
    if taslak.is_file():
        ff.ffmpeg("-ss", f"{c.bas + c.sure / 2:.3f}", "-i", str(taslak), "-frames:v", "1",
                  "-vf", "scale=480:480:force_original_aspect_ratio=decrease,pad=480:480:(ow-iw)/2:(oh-ih)/2:color=0x1B1E25",
                  "-q:v", "3", str(klasor / "poster.jpg"), check=False)


def sil(kid: str) -> dict:
    """Kaydı ve klasörünü siler (geri dönüşüm kutusu); taşınmış kompozisyon da gider."""
    from .studio import ortak
    with _kilit:
        kayitlar = oku()
        e = next((x for x in kayitlar if x["id"] == kid), None)
        if not e:
            raise KeyError(kid)
        klasor = kok() / kid
        if klasor.is_dir():
            ortak.sil(klasor)
        if (e.get("hf") or {}).get("ad", "").startswith(HF_ONEK):
            from . import hf_grafik
            d = hf_grafik.KUTUPHANE / e["hf"]["ad"]
            if d.is_dir():
                ortak.sil(d)
        _yaz([x for x in kayitlar if x["id"] != kid])
    return e


# --- Gizleme: kodla tanımlı galeri öğeleri (fizik, ışık, karakter, efekt) silinemez, gizlenir ---------------------

def gizli() -> set[str]:
    try:
        return set(json.loads((kok() / "gizli.json").read_text(encoding="utf-8")))
    except (OSError, ValueError):
        return set()


def gizle(anahtar: str, gizle_: bool = True) -> set[str]:
    with _kilit:
        g = gizli()
        (g.add if gizle_ else g.discard)(anahtar)
        kok().mkdir(parents=True, exist_ok=True)
        (kok() / "gizli.json").write_text(json.dumps(sorted(g), ensure_ascii=False), encoding="utf-8")
    return g
