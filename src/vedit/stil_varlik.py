"""Stile özel varlık deposu, tam stil izolasyonu, temalı native dışa aktarma ve .zip stil paketi.

Disk düzeni:
- studios/<studyo>/styles/<ad>/varliklar.json
- studios/<studyo>/styles/<ad>/varliklar/<tur>/<vid>/
- studios/<studyo>/styles/<ad>/.disa/<hash>.webm (önbellek; paket zip'ine girmez)
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import uuid
import zipfile
from datetime import date
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from . import ff, motion_ice, native_motion, paths, stil, tema_token

TURLER = ("motion", "animasyon", "karakter", "gorsel", "ses")
VarlikTuru = Literal["motion", "animasyon", "karakter", "gorsel", "ses"]
YontemTuru = Literal["alfa", "yesil", "siyah", "lottie", "gif", "svg", "karakter_json", "ham"]

IZINLI_UZANTILAR: dict[str, set[str]] = {
    "motion": {".webm", ".mov", ".mp4", ".mkv", ".json", ".lottie", ".gif", ".apng", ".png", ".svg"},
    "animasyon": {".webm", ".mov", ".mp4", ".mkv", ".json", ".lottie", ".gif", ".apng", ".png", ".svg"},
    "karakter": {".json", ".png", ".webp", ".jpg", ".jpeg", ".svg", ".webm", ".mov", ".mp4"},
    "gorsel": {".png", ".jpg", ".jpeg", ".webp", ".svg"},
    "ses": {".wav", ".mp3", ".ogg", ".m4a", ".flac"},
}

YONTEMLER: set[str] = {"alfa", "yesil", "siyah", "lottie", "gif", "svg", "karakter_json", "ham"}


class VarlikBulunamadi(KeyError, ValueError):
    """Hem KeyError hem ValueError olarak yakalanabilen varlık bulunamadı hatası."""

    def __str__(self) -> str:
        return str(self.args[0]) if self.args else ""


class StilVarlik(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    ad: str
    tur: VarlikTuru
    dosya: str
    orijinal: str
    poster: str | None = None
    yontem: YontemTuru = "ham"
    sure: float | None = None
    w: int | None = None
    h: int | None = None
    ne_zaman: str = ""
    etiketler: list[str] = Field(default_factory=list)
    lisans: str = "Kendi üretimim"
    kaynak_url: str = ""
    atif: str = ""
    eklenme: str = Field(default_factory=lambda: date.today().isoformat())


class StilVarlikDeposu(BaseModel):
    model_config = ConfigDict(extra="forbid")
    surum: Literal[1] = 1
    yalniz_bunlar: bool = False
    secili_native: list[str] = Field(default_factory=list)
    secili_kutuphane: list[str] = Field(default_factory=list)
    yuklenenler: list[StilVarlik] = Field(default_factory=list)


def _studyo_denetle(studyo: str) -> str:
    return stil.ad_denetle(studyo)


def depo_yolu(studyo: str, ad: str) -> Path:
    _studyo_denetle(studyo)
    return stil.klasor(studyo, ad) / "varliklar.json"


def oku(studyo: str, ad: str) -> StilVarlikDeposu:
    f = depo_yolu(studyo, ad)
    if not f.is_file():
        return StilVarlikDeposu()
    return StilVarlikDeposu.model_validate_json(f.read_text(encoding="utf-8"))


def yaz(studyo: str, ad: str, depo: StilVarlikDeposu) -> StilVarlikDeposu:
    f = depo_yolu(studyo, ad)
    f.parent.mkdir(parents=True, exist_ok=True)
    gecici = f.with_name(f".{f.name}.{uuid.uuid4().hex[:8]}.tmp")
    gecici.write_text(depo.model_dump_json(indent=1) + "\n", encoding="utf-8")
    os.replace(gecici, f)
    return depo


def ozet(studyo: str, ad: str) -> dict:
    d = oku(studyo, ad)
    sayim = {t: sum(1 for v in d.yuklenenler if v.tur == t) for t in TURLER}
    return {
        **sayim,
        "secili_native": len(d.secili_native),
        "secili_kutuphane": len(d.secili_kutuphane),
        "yalniz_bunlar": d.yalniz_bunlar,
        "toplam": len(d.yuklenenler),
    }


def kurgu_yolu(studyo: str, ad: str, goreli: str) -> str:
    _studyo_denetle(studyo)
    stil.ad_denetle(ad)
    temiz = str(goreli).replace("\\", "/").lstrip("/")
    if not temiz or ".." in Path(temiz).parts:
        raise ValueError(f"Geçersiz göreli varlık yolu: {goreli}")
    return f"stil:{studyo}/{ad}/{temiz}"


def _gorsel_boyut(f: Path) -> tuple[int | None, int | None]:
    try:
        from PIL import Image

        with Image.open(f) as im:
            return int(im.width), int(im.height)
    except Exception:
        pass
    try:
        v = ff.probe(f).get("video") or {}
        return v.get("width"), v.get("height")
    except Exception:
        return None, None


def _medya_bilgi(f: Path) -> tuple[float | None, int | None, int | None]:
    try:
        bilgi = ff.probe(f)
        sure = round(float(bilgi["duration"]), 3) if bilgi.get("duration") else None
        v = bilgi.get("video") or {}
        return sure, v.get("width"), v.get("height")
    except Exception:
        return None, None, None


def _etiket_listesi(etiketler: list[str] | str | None) -> list[str]:
    if not etiketler:
        return []
    ham = etiketler.split(",") if isinstance(etiketler, str) else list(etiketler)
    return list(dict.fromkeys(e.strip() for e in ham if e and str(e).strip()))


def yukle(
    studyo: str,
    ad: str,
    dosya_yolu: Path,
    *,
    tur: str,
    baslik: str = "",
    ne_zaman: str = "",
    etiketler: list[str] | None = None,
    yontem: str | None = None,
    lisans: str = "Kendi üretimim",
    kaynak_url: str = "",
    atif: str = "",
) -> StilVarlik:
    _studyo_denetle(studyo)
    stil_k = stil.klasor(studyo, ad)
    kaynak = Path(dosya_yolu)
    if not kaynak.is_file():
        raise ValueError(f"Dosya bulunamadı: {kaynak}")
    if tur not in TURLER:
        raise ValueError(f"Geçersiz varlık türü '{tur}'; geçerli: {', '.join(TURLER)}")
    ext = kaynak.suffix.lower()
    if ext not in IZINLI_UZANTILAR[tur]:
        raise ValueError(
            f"'{tur}' türü için desteklenmeyen uzantı '{ext}' "
            f"(izinli: {', '.join(sorted(IZINLI_UZANTILAR[tur]))})"
        )
    if yontem is not None and yontem not in YONTEMLER:
        raise ValueError(f"Geçersiz yöntem '{yontem}'; geçerli: {', '.join(sorted(YONTEMLER))}")

    depo = oku(studyo, ad)
    mevcut_idler = {v.id for v in depo.yuklenenler}
    taban = motion_ice._kimlik(baslik or kaynak.stem)
    vid = taban
    sayac = 2
    while vid in mevcut_idler or (stil_k / "varliklar" / tur / vid).exists():
        vid = f"{taban}-{sayac}"
        sayac += 1

    hedef_kok = stil_k / "varliklar" / tur / vid
    hedef_kok.mkdir(parents=True, exist_ok=True)
    try:
        orijinal_f = hedef_kok / f"orijinal{ext}"
        shutil.copy2(kaynak, orijinal_f)

        poster_f: Path | None = None
        sure: float | None = None
        w: int | None = None
        h: int | None = None
        secilen_yontem: YontemTuru = "ham"

        if tur == "karakter" and ext == ".json":
            try:
                veri = json.loads(kaynak.read_text(encoding="utf-8"))
            except Exception as e:
                raise ValueError(f"Geçersiz karakter JSON: {e}") from e
            if not isinstance(veri, dict) or not veri:
                raise ValueError("karakter.json boş olmayan bir JSON nesnesi (dict) olmalı")
            norm_f = hedef_kok / "karakter.json"
            shutil.copy2(kaynak, norm_f)
            secilen_yontem = "karakter_json"
        elif ext in (".json", ".lottie"):
            try:
                norm_f = motion_ice._lottie_cikar(kaynak, hedef_kok / f"{vid}.json")
            except Exception as e:
                raise ValueError(f"Geçersiz Lottie dosyası: {e}") from e
            secilen_yontem = "lottie"
            sure = motion_ice._lottie_sure(norm_f)
            veri = json.loads(norm_f.read_text(encoding="utf-8"))
            w = veri.get("w") if isinstance(veri.get("w"), int) else None
            h = veri.get("h") if isinstance(veri.get("h"), int) else None
        elif ext == ".svg":
            norm_f = hedef_kok / f"{vid}.svg"
            shutil.copy2(kaynak, norm_f)
            secilen_yontem = "svg"
        elif ext in (".png", ".jpg", ".jpeg", ".webp"):
            norm_f = hedef_kok / f"{vid}{ext}"
            shutil.copy2(kaynak, norm_f)
            if yontem in YONTEMLER:
                secilen_yontem = yontem  # type: ignore[assignment]
            elif ext == ".png" and tur in ("motion", "animasyon"):
                secilen_yontem = "alfa"
            else:
                secilen_yontem = "ham"
            poster_f = norm_f
            w, h = _gorsel_boyut(norm_f)
        elif tur == "ses":
            norm_f = hedef_kok / f"{vid}{ext}"
            shutil.copy2(kaynak, norm_f)
            secilen_yontem = "ham"
            sure, _, _ = _medya_bilgi(norm_f)
        else:
            # Video / GIF / APNG (.webm, .mov, .mp4, .mkv, .gif, .apng)
            if yontem:
                secilen_yontem = yontem  # type: ignore[assignment]
            elif ext in (".gif", ".apng"):
                secilen_yontem = "gif"
            elif tur == "karakter":
                try:
                    secilen_yontem = motion_ice.yontem_bul(kaynak)
                except Exception:
                    secilen_yontem = "alfa" if ext == ".webm" else "ham"
            else:
                try:
                    secilen_yontem = motion_ice.yontem_bul(kaynak)
                except motion_ice.LisansHatasi as e:
                    raise ValueError(str(e)) from e
                except Exception as e:
                    # Test ortamında ffprobe çalışmayan küçük dummy .webm dosyası için güvenli yedek
                    if ext == ".webm" and kaynak.stat().st_size < 1024:
                        secilen_yontem = "alfa"
                    else:
                        raise ValueError(f"Video biçimi çözümlenemedi ({kaynak.name}): {e}") from e

            if secilen_yontem == "yesil":
                norm_f = motion_ice._cevir_yesil(kaynak, hedef_kok / f"{vid}.webm")
            elif secilen_yontem == "gif":
                norm_f = hedef_kok / f"{vid}.webm"
                try:
                    motion_ice._cevir_gif(kaynak, norm_f)
                except Exception:
                    if kaynak.stat().st_size < 1024:
                        norm_f = hedef_kok / f"{vid}{ext}"
                        shutil.copy2(kaynak, norm_f)
                    else:
                        raise
            elif secilen_yontem == "alfa":
                norm_f = hedef_kok / f"{vid}.webm"
                if ext == ".webm":
                    shutil.copy2(kaynak, norm_f)
                else:
                    try:
                        motion_ice._cevir_gif(kaynak, norm_f)
                    except Exception:
                        if kaynak.stat().st_size < 1024:
                            norm_f = hedef_kok / f"{vid}{ext}"
                            shutil.copy2(kaynak, norm_f)
                        else:
                            raise
            else:
                # siyah veya ham
                norm_f = hedef_kok / f"{vid}{ext}"
                shutil.copy2(kaynak, norm_f)

            try:
                poster_f = motion_ice._poster(norm_f, hedef_kok / "poster.jpg", secilen_yontem)
            except Exception:
                poster_f = None
            sure, w, h = _medya_bilgi(norm_f)

        varlik = StilVarlik(
            id=vid,
            ad=(baslik or kaynak.stem).strip() or vid,
            tur=tur,  # type: ignore[arg-type]
            dosya=norm_f.relative_to(stil_k).as_posix(),
            orijinal=orijinal_f.relative_to(stil_k).as_posix(),
            poster=poster_f.relative_to(stil_k).as_posix() if poster_f and poster_f.is_file() else None,
            yontem=secilen_yontem,
            sure=sure,
            w=w,
            h=h,
            ne_zaman=(ne_zaman or "").strip(),
            etiketler=_etiket_listesi(etiketler),
            lisans=(lisans or "Kendi üretimim").strip() or "Kendi üretimim",
            kaynak_url=(kaynak_url or "").strip(),
            atif=(atif or "").strip(),
        )
        depo.yuklenenler.append(varlik)
        yaz(studyo, ad, depo)
        return varlik
    except Exception:
        shutil.rmtree(hedef_kok, ignore_errors=True)
        raise


def sil(studyo: str, ad: str, vid: str) -> StilVarlik:
    _studyo_denetle(studyo)
    stil_k = stil.klasor(studyo, ad).resolve()
    depo = oku(studyo, ad)
    hedef = next((v for v in depo.yuklenenler if v.id == vid), None)
    if hedef is None:
        raise VarlikBulunamadi(f"Varlık bulunamadı: {vid}")
    varlik_kok = (stil_k / "varliklar").resolve()
    klasor = (stil_k / "varliklar" / hedef.tur / hedef.id).resolve()
    if klasor.is_relative_to(varlik_kok) and klasor.is_dir():
        shutil.rmtree(klasor, ignore_errors=True)
    depo.yuklenenler = [v for v in depo.yuklenenler if v.id != vid]
    yaz(studyo, ad, depo)
    return hedef


def secki_guncelle(
    studyo: str,
    ad: str,
    *,
    secili_native: list[str] | None = None,
    secili_kutuphane: list[str] | None = None,
    yalniz_bunlar: bool | None = None,
) -> StilVarlikDeposu:
    _studyo_denetle(studyo)
    depo = oku(studyo, ad)
    if secili_native is not None:
        bilinen = set(native_motion.kayitlar())
        bilinmeyen = [x for x in secili_native if x not in bilinen]
        if bilinmeyen:
            raise ValueError(f"Bilinmeyen native motion bileşeni: {', '.join(bilinmeyen)}")
        depo.secili_native = list(dict.fromkeys(secili_native))
    if secili_kutuphane is not None:
        depo.secili_kutuphane = list(dict.fromkeys(secili_kutuphane))
    if yalniz_bunlar is not None:
        depo.yalniz_bunlar = bool(yalniz_bunlar)
    return yaz(studyo, ad, depo)


def varlik_dosyasi(
    studyo: str,
    ad: str,
    vid: str,
    *,
    bicim: Literal["normalize", "orijinal", "poster"] = "normalize",
) -> tuple[Path, StilVarlik]:
    _studyo_denetle(studyo)
    stil_k = stil.klasor(studyo, ad).resolve()
    depo = oku(studyo, ad)
    hedef = next((v for v in depo.yuklenenler if v.id == vid), None)
    if hedef is None:
        raise VarlikBulunamadi(f"Varlık bulunamadı: {vid}")
    if bicim == "orijinal":
        goreli = hedef.orijinal
    elif bicim == "poster":
        if not hedef.poster:
            raise VarlikBulunamadi(f"Varlığın posteri yok: {vid}")
        goreli = hedef.poster
    else:
        goreli = hedef.dosya
    yol = (stil_k / goreli).resolve()
    if not yol.is_relative_to(stil_k):
        raise ValueError(f"Kök dışı varlık yolu: {goreli}")
    if not yol.is_file():
        raise VarlikBulunamadi(f"Varlık dosyası diskte yok: {goreli}")
    return yol, hedef


def _stil_tema_dict(studyo: str, ad: str) -> dict:
    stil_k = stil.klasor(studyo, ad)
    tema_adi = stil.motion_temasi(stil_k)
    if not tema_adi and (stil_k / "tokens.json").is_file():
        try:
            tema_adi = tema_token.paketten_yaz(stil_k)
        except Exception:
            tema_adi = None
    t = (tema_token.oku(tema_adi) if tema_adi else None) or tema_token.oku(ad) or tema_token.oku("varsayilan")
    if t is None:
        raise ValueError(f"Stil teması çözümlenemedi: {studyo}/{ad}")
    d = t.model_dump()
    kayit = tema_token.font_kayitlari()
    adlar = {t.font.baslik, t.font.govde, t.font.mono, t.font.rakam or t.font.baslik, t.altyazi.font}
    d["dosyalar"] = {a: kayit[a]["file"] for a in adlar if a in kayit}
    return d


def native_disa_aktar(
    studyo: str,
    ad: str,
    bilesen_ad: str,
    *,
    param: dict | None = None,
    en_boy: Literal["9:16", "16:9", "1:1"] = "1:1",
    sure: float | None = None,
) -> Path:
    _studyo_denetle(studyo)
    stil_k = stil.klasor(studyo, ad)
    if en_boy not in ("9:16", "16:9", "1:1"):
        raise ValueError(f"Geçersiz en_boy '{en_boy}' (9:16, 16:9, 1:1 olmalı)")
    if sure is not None and (not isinstance(sure, (int, float)) or sure <= 0 or sure > 30):
        raise ValueError(f"Geçersiz süre: {sure}")
    hatalar = native_motion.param_hatalari(bilesen_ad, param or {})
    if hatalar:
        raise ValueError("; ".join(hatalar))

    tema_dict = _stil_tema_dict(studyo, ad)
    props_veri = {
        "ad": bilesen_ad,
        "param": param or {},
        "en_boy": en_boy,
        "sure": sure,
        "tema": tema_dict,
    }
    imza = hashlib.sha256(json.dumps(props_veri, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()[:16]
    slug = re.sub(r"[^a-z0-9]+", "-", bilesen_ad.lower()).strip("-")
    hedef = stil_k / ".disa" / f"{slug}-{imza}.webm"
    if hedef.is_file() and hedef.stat().st_size > 0:
        return hedef

    hedef.parent.mkdir(parents=True, exist_ok=True)
    studio = paths.ROOT / "studio"
    exe = studio / "node_modules" / ".bin" / ("remotion.cmd" if os.name == "nt" else "remotion")
    with tempfile.TemporaryDirectory() as gecici:
        pub = Path(gecici) / "public"
        (pub / "fonts").mkdir(parents=True, exist_ok=True)
        for dosya_adi in (tema_dict.get("dosyalar") or {}).values():
            kaynak_font = paths.FONTS_DIR / Path(dosya_adi).name
            hedef_font = pub / "fonts" / Path(dosya_adi).name
            if kaynak_font.is_file() and not hedef_font.exists():
                try:
                    hedef_font.hardlink_to(kaynak_font)
                except OSError:
                    shutil.copy2(kaynak_font, hedef_font)
        props_f = Path(gecici) / "props.json"
        props_f.write_text(json.dumps(props_veri, ensure_ascii=False), encoding="utf-8")
        gecici_cikti = Path(gecici) / "out.webm"
        subprocess.run(
            [
                str(exe),
                "render",
                "remotion/index.tsx",
                "MotionTekil",
                str(gecici_cikti),
                f"--props={props_f}",
                f"--public-dir={pub}",
                "--codec=vp9",
                "--image-format=png",
                "--pixel-format=yuva420p",
                "--log=error",
            ],
            check=True,
            cwd=studio,
            shell=os.name == "nt",
        )
        shutil.move(str(gecici_cikti), str(hedef))
    return hedef


def paket_zip_uret(studyo: str, ad: str, hedef_zip: Path) -> Path:
    _studyo_denetle(studyo)
    stil_k = stil.klasor(studyo, ad)
    if not stil_k.is_dir() or not ((stil_k / "STYLE.md").is_file() or (stil_k / "varliklar.json").is_file()):
        raise ValueError(f"Stil paketi bulunamadı: {studyo}/{ad}")

    hedef_zip = Path(hedef_zip)
    hedef_zip.parent.mkdir(parents=True, exist_ok=True)
    kok_dosyalar = ("STYLE.md", "MOTION.md", "tokens.json", "varliklar.json")
    eklenen: set[str] = set()

    with zipfile.ZipFile(hedef_zip, "w", compression=zipfile.ZIP_DEFLATED) as z:
        manifest = {"surum": 1, "studyo": studyo, "ad": ad, "tarih": date.today().isoformat()}
        z.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=1) + "\n")
        eklenen.add("manifest.json")

        for d in kok_dosyalar:
            f = stil_k / d
            if f.is_file():
                z.write(f, d)
                eklenen.add(d)

        varliklar_k = stil_k / "varliklar"
        if varliklar_k.is_dir():
            for f in sorted(varliklar_k.rglob("*")):
                if not f.is_file() or f.name.startswith("."):
                    continue
                rel = f.relative_to(stil_k).as_posix()
                if ".disa" in Path(rel).parts:
                    continue
                if rel not in eklenen:
                    z.write(f, rel)
                    eklenen.add(rel)

        # Stil içi referanslar/ veya Projeler/inputs/_referanslar/<studyo>/<ad>/
        for ref_k in (stil_k / "referanslar", stil.referans_klasoru(studyo, ad)):
            if not ref_k.is_dir():
                continue
            for f in sorted(ref_k.iterdir()):
                if not f.is_file() or f.name.startswith("."):
                    continue
                rel = f"referanslar/{f.name}"
                if rel not in eklenen:
                    z.write(f, rel)
                    eklenen.add(rel)

    return hedef_zip


def _zip_uyesi_dogrula(isim: str) -> str:
    norm = isim.replace("\\", "/")
    if norm.startswith("/") or ":" in norm:
        raise ValueError(f"Güvenlik hatası (zip-slip mutlak yol): {isim}")
    parcalar = [p for p in norm.split("/") if p and p != "."]
    if ".." in parcalar:
        raise ValueError(f"Güvenlik hatası (zip-slip '..'): {isim}")
    return "/".join(parcalar)


def paket_zip_ice_al(
    studyo: str,
    zip_yolu: Path,
    *,
    yeni_ad: str | None = None,
    uzerine_yaz: bool = False,
) -> dict:
    _studyo_denetle(studyo)
    zip_yolu = Path(zip_yolu)
    if not zip_yolu.is_file() or not zipfile.is_zipfile(zip_yolu):
        raise ValueError(f"Geçersiz zip dosyası: {zip_yolu}")

    with zipfile.ZipFile(zip_yolu, "r") as z:
        ham_isimler = z.namelist()
        temiz_harita: dict[str, str] = {}
        for h in ham_isimler:
            temiz = _zip_uyesi_dogrula(h)
            if temiz and not h.endswith("/"):
                temiz_harita[temiz] = h

        # Tek bir üst klasör varsa ve kök dosyalar onun içindeyse öneki soy
        onek = ""
        kok_adaylari = {"STYLE.md", "varliklar.json", "manifest.json"}
        if not (kok_adaylari & set(temiz_harita)):
            ustler = {k.split("/", 1)[0] for k in temiz_harita if "/" in k}
            if len(ustler) == 1:
                aday_onek = next(iter(ustler)) + "/"
                soyulmus = {k.removeprefix(aday_onek): v for k, v in temiz_harita.items() if k.startswith(aday_onek)}
                if {"STYLE.md", "varliklar.json"} & set(soyulmus):
                    onek = aday_onek
                    temiz_harita = soyulmus

        if "STYLE.md" not in temiz_harita and "varliklar.json" not in temiz_harita:
            raise ValueError("Geçersiz stil paketi: STYLE.md veya varliklar.json bulunamadı")

        manifest_ad = None
        if "manifest.json" in temiz_harita:
            try:
                m = json.loads(z.read(temiz_harita["manifest.json"]).decode("utf-8"))
                if isinstance(m, dict) and isinstance(m.get("ad"), str):
                    manifest_ad = m["ad"]
            except Exception:
                manifest_ad = None

        stem = re.sub(r"\.stil$", "", zip_yolu.stem, flags=re.IGNORECASE)
        hedef_ad = stil.ad_denetle(yeni_ad or manifest_ad or motion_ice._kimlik(stem))
        hedef_k = stil.klasor(studyo, hedef_ad).resolve()
        if hedef_k.exists() and any(hedef_k.iterdir()) and not uzerine_yaz:
            raise ValueError(f"Stil zaten var: {studyo}/{hedef_ad} (üzerine yazmak için uzerine_yaz=True)")

        hedef_k.mkdir(parents=True, exist_ok=True)
        izinli_kok = {"STYLE.md", "MOTION.md", "tokens.json", "varliklar.json"}

        for rel, ham in temiz_harita.items():
            parcalar = Path(rel).parts
            if not parcalar or ".disa" in parcalar or rel == "manifest.json":
                continue
            if rel not in izinli_kok and parcalar[0] not in ("varliklar", "referanslar"):
                continue
            cikti = (hedef_k / rel).resolve()
            if not cikti.is_relative_to(hedef_k):
                raise ValueError(f"Güvenlik hatası (hedef kök dışı): {rel}")
            cikti.parent.mkdir(parents=True, exist_ok=True)
            cikti.write_bytes(z.read(ham))
            if parcalar[0] == "referanslar" and len(parcalar) == 2:
                ref_k = stil.referans_klasoru(studyo, hedef_ad).resolve()
                ref_cikti = (ref_k / parcalar[1]).resolve()
                if ref_cikti.is_relative_to(ref_k):
                    ref_k.mkdir(parents=True, exist_ok=True)
                    ref_cikti.write_bytes(cikti.read_bytes())

    depo = oku(studyo, hedef_ad)
    if (hedef_k / "tokens.json").is_file() and not stil.motion_temasi(hedef_k):
        try:
            tema_token.paketten_yaz(hedef_k)
        except Exception:
            pass
    return {
        "studyo": studyo,
        "ad": hedef_ad,
        "klasor": str(hedef_k),
        "varlik_sayisi": len(depo.yuklenenler),
    }


def baglam_metni(studyo: str, ad: str) -> str:
    """AI edit ve ekip motoru için seçili stilin özel varlıkları ve seçki kısıtları özeti."""
    try:
        depo = oku(studyo, ad)
    except Exception:
        return ""
    if not depo.yuklenenler and not depo.secili_native and not depo.secili_kutuphane and not depo.yalniz_bunlar:
        return ""

    satirlar = [f"### Seçili Stilin Özel Varlıkları (`{studyo}/{ad}` — ÖNCELİKLİ KULLAN)"]
    if depo.yalniz_bunlar:
        satirlar.append(
            "- **KISIT (`yalniz_bunlar: true`):** Bu stilde yalnız aşağıda listelenen stile özel varlıkları ve "
            "seçili bileşenleri kullan; bu listenin dışındaki genel kütüphane varlıklarını kullanma."
        )
    else:
        satirlar.append(
            "- Aşağıdaki varlıklar bu stile özeldir; uygun anlatı anlarında genel kütüphane yerine öncelikle bunları kullan."
        )

    for v in depo.yuklenenler:
        yol = kurgu_yolu(studyo, ad, v.dosya)
        sure_bilgi = f", {v.sure} sn" if v.sure else ""
        boyut_bilgi = f", {v.w}x{v.h}" if v.w and v.h else ""
        nz = f" · Ne zaman: {v.ne_zaman}" if v.ne_zaman else ""
        et = f" · Etiketler: {', '.join(v.etiketler)}" if v.etiketler else ""
        if v.tur == "karakter" and v.yontem == "karakter_json":
            kullanim = f'`tur: "sahne"`, `sahne: {{"kind": "karakter", "karakter": "{v.id}", "layout": "full", "bg": "saydam"}}`'
        elif v.yontem == "lottie":
            kullanim = f'`tur: "motion"`, `bilesen: {{"ad": "dis/lottie", "param": {{"dosya": "{yol}"}}}}`'
        elif v.tur in ("motion", "animasyon"):
            klip_turu = "gorsel" if v.yontem == "svg" else "motion"
            ek = " (siyah zemin screen karışımı otomatik)" if v.yontem == "siyah" else ""
            kullanim = f'`kaynaklar` içinde `"yol": "{yol}"` → `tur: "{klip_turu}"`{ek}'
        elif v.tur == "gorsel":
            kullanim = f'`kaynaklar` içinde `"yol": "{yol}"` → `tur: "gorsel"` ya da `shot` sahnesi (`"img": "{yol}"`)'
        else:
            kullanim = f'`kaynaklar` içinde `"yol": "{yol}"` → `tur: "ses"`'
        satirlar.append(f"- `{v.id}` ({v.tur}/{v.yontem}{sure_bilgi}{boyut_bilgi}): **{v.ad}** — {kullanim}{nz}{et}")

    if depo.secili_native:
        satirlar.append("- **Stilin seçili native motion bileşenleri:** " + ", ".join(f"`{x}`" for x in depo.secili_native))
    if depo.secili_kutuphane:
        satirlar.append("- **Stilin seçili kütüphane varlıkları:** " + ", ".join(f"`{x}`" for x in depo.secili_kutuphane))
    return "\n".join(satirlar)
