"""Dış motion varlığı içe aktarma: lisans kaydı zorunlu, alfa yöntemi otomatik, normalize dosya + poster + kontak (ADR 0046).

WHY: Kullanıcı Mixkit, Pixabay, LottieFiles, Uppbeat ve GitHub'dan elle indirir (kazıma ve API yok). Her varlık lisans,
atıf ve kısıt bilgisiyle `library/motion/dis/<kaynak>/<id>/` altına girer; AI edit kısıtları görür, atıf gereken varlık
kullanılırsa yayin.md'ye atıf satırı yazılır. Lisans kaydı olmayan varlık reddedilir.

Biçimler ve kurguda kullanım:
- alfa (webm/mov alfalı)        → olduğu gibi webm, motion klibi
- yesil (yeşil perde mp4)       → chromakey + despill → VP9 yuva420p webm, motion klibi
- siyah (siyah zeminli mp4)     → dosya olduğu gibi, kaynakta `karisim: screen` (light leak, film yanığı, parıltı)
- lottie (json / dotLottie)     → json; native `dis/lottie` bileşeni çizer, renkleri temaya eşlenir
- gif (GIF/APNG)                → VP9 yuva420p webm, motion klibi
- svg                           → olduğu gibi, görsel klibi
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import zipfile
from datetime import date
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from . import ff, paths

Yontem = Literal["alfa", "yesil", "siyah", "lottie", "gif", "svg"]
TURLER = ("overlay", "icon", "transition", "lower-third", "background", "broll", "cta", "reaction", "light-leak", "texture")

# Kaynak başına varsayılan lisans kaydı (library/motion/indirme-listesi.md, 2026-11-19 doğrulaması). Kullanıcı ezebilir.
VARSAYILAN = {
    "mixkit": {"lisans": "Mixkit Stock Video Free License", "url": "https://mixkit.co/license/", "atif_gerekli": False,
               "kisitlar": ["ham dosya tek başına dağıtılamaz", "'Restricted' etiketli videolar ticari kullanılamaz"]},
    "pixabay": {"lisans": "Pixabay Content License", "url": "https://pixabay.com/service/license-summary/", "atif_gerekli": False,
                "kisitlar": ["ham dosya tek başına dağıtılamaz", "tanınabilir marka onay ima edemez"]},
    "lottiefiles": {"lisans": "Lottie Simple License", "url": "https://lottiefiles.com/page/license", "atif_gerekli": False,
                    "kisitlar": ["yalnız Free etiketli animasyon", "logo ya da marka olarak kullanılamaz"]},
    "uppbeat": {"lisans": "Uppbeat Basic License", "url": "https://uppbeat.io/uppbeat-basic-license", "atif_gerekli": True,
                "kisitlar": ["yalniz-kendi-kanalin", "ücretli reklam yok", "müşteri işi yok", "yalnız Drag & Drop dosyası"]},
    "github": {"lisans": "MIT", "url": "", "atif_gerekli": False, "kisitlar": ["MIT bildirimi kaynak kopyasında korunur"]},
}


class Lisans(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kaynak: str = Field(min_length=2)
    url: str = Field(min_length=8)
    lisans: str = Field(min_length=2)
    atif_gerekli: bool = False
    atif_metni: str = ""
    kisitlar: list[str] = []
    indirme_tarihi: str = Field(default_factory=lambda: date.today().isoformat())

    @field_validator("url")
    @classmethod
    def _http(cls, v: str) -> str:
        if not re.match(r"^https?://", v.strip()):
            raise ValueError("url http(s) adresi olmalı")
        return v.strip()

    @field_validator("atif_metni")
    @classmethod
    def _atif(cls, v: str, info) -> str:
        return v.strip()


class LisansHatasi(ValueError):
    pass


def lisans_kur(kaynak: str, *, url: str | None, lisans: str | None, atif_gerekli: bool | None = None,
               atif_metni: str = "", kisitlar: list[str] | None = None) -> Lisans:
    """Eksik alan kaynağın varsayılanından tamamlanır; yine eksikse LisansHatasi (varlık reddedilir)."""
    v = VARSAYILAN.get(kaynak, {})
    try:
        k = Lisans(kaynak=kaynak, url=url or v.get("url") or "", lisans=lisans or v.get("lisans") or "",
                   atif_gerekli=v.get("atif_gerekli", False) if atif_gerekli is None else atif_gerekli,
                   atif_metni=atif_metni, kisitlar=kisitlar if kisitlar is not None else list(v.get("kisitlar", [])))
    except Exception as e:  # noqa: BLE001
        raise LisansHatasi(f"lisans kaydı eksik ya da geçersiz ({kaynak}): {e}") from e
    if k.atif_gerekli and not k.atif_metni:
        raise LisansHatasi(f"{kaynak}: atıf gerekli ama atıf metni yok (--atif-metni)")
    return k


# ------------------------------------------------------------------ biçim tespiti

def _kenar_ort(f: Path) -> tuple[float, float, float]:
    """Kenar piksellerinin ortalama RGB'si (orta karede, 2 px çerçeve)."""
    sure = ff.probe(f)["duration"] or 0
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{sure / 2:.2f}", "-i", str(f), "-frames:v", "1",
                          "-vf", "scale=64:64", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    import numpy as np

    a = np.frombuffer(raw, np.uint8).reshape(64, 64, 3).astype(float)
    kenar = np.concatenate([a[:2].reshape(-1, 3), a[-2:].reshape(-1, 3), a[:, :2].reshape(-1, 3), a[:, -2:].reshape(-1, 3)])
    return tuple(kenar.mean(axis=0))


def yontem_bul(f: Path) -> Yontem:
    s = f.suffix.lower()
    if s in (".json", ".lottie"):
        return "lottie"
    if s == ".svg":
        return "svg"
    if s in (".gif", ".apng", ".png"):
        return "gif"
    v = ff.probe(f).get("video") or {}
    if v.get("alfa"):
        return "alfa"
    r, g, b = _kenar_ort(f)
    if g > 90 and g > r * 1.4 and g > b * 1.4:
        return "yesil"
    if max(r, g, b) < 28:
        return "siyah"
    raise LisansHatasi(f"{f.name}: alfa yok, yeşil perde ya da siyah zemin değil; bindirme olarak kullanılamaz")


# ------------------------------------------------------------------ dönüştürme

VP9 = ["-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p", "-b:v", "0", "-crf", "28", "-row-mt", "1", "-auto-alt-ref", "0", "-an"]


def anahtar_filtresi(benzerlik: float = 0.18, yumusaklik: float = 0.08, renk: str = "0x00FF00") -> str:
    return f"chromakey={renk}:{benzerlik}:{yumusaklik},despill=type=green,format=yuva420p"


def anahtar_dene(f: Path, cikti: Path, esikler=(0.1, 0.18, 0.28)) -> list[Path]:
    """Yeşil perde ayar önizlemesi: her eşik için dama zeminde tek kare (kullanıcı en temizini seçer)."""
    cikti.mkdir(parents=True, exist_ok=True)
    sure = ff.probe(f)["duration"] or 0
    yazilan = []
    for e in esikler:
        hedef = cikti / f"anahtar-{e:.2f}.jpg"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{sure / 2:.2f}", "-i", str(f), "-f", "lavfi", "-i",
                        "color=c=0xc8c8c8:s=16x16,format=rgb24", "-filter_complex",
                        f"[0:v]scale=480:-2,{anahtar_filtresi(e)}[k];[1:v]scale=480:270[z];[z][k]overlay=shortest=1,"
                        f"drawgrid=w=24:h=24:t=fill:c=0xffffff@0.35", "-frames:v", "1", str(hedef)], check=True)
        yazilan.append(hedef)
    return yazilan


def _cevir_gif(f: Path, hedef: Path) -> Path:
    dec = ["-c:v", "libvpx-vp9"] if f.suffix.lower() == ".webm" else []
    subprocess.run(["ffmpeg", "-v", "error", "-y", *dec, "-i", str(f), "-vf", "format=yuva420p", *VP9, str(hedef)], check=True)
    return hedef


def _cevir_yesil(f: Path, hedef: Path, benzerlik: float = 0.18) -> Path:
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(f), "-vf", anahtar_filtresi(benzerlik), *VP9, str(hedef)], check=True)
    return hedef


def _lottie_cikar(f: Path, hedef: Path) -> Path:
    if f.suffix.lower() == ".lottie":  # dotLottie: zip içinde animations/*.json
        with zipfile.ZipFile(f) as z:
            ad = next((n for n in z.namelist() if n.startswith("animations/") and n.endswith(".json")), None)
            if not ad:
                raise LisansHatasi(f"{f.name}: dotLottie içinde animasyon yok")
            hedef.write_bytes(z.read(ad))
    else:
        shutil.copy(f, hedef)
    veri = json.loads(hedef.read_text(encoding="utf-8"))
    if not isinstance(veri, dict) or "layers" not in veri:
        raise LisansHatasi(f"{f.name}: geçerli Lottie JSON değil ('layers' yok)")
    return hedef


def _poster(h: Path, hedef: Path, yontem: str = "alfa") -> Path | None:
    if yontem in ("lottie", "svg"):
        return None
    dec = ["-c:v", "libvpx-vp9"] if h.suffix == ".webm" else []
    sure = ff.probe(h)["duration"] or 1
    zemin = "color=c=0x6e6e6e:s=320x320" if yontem == "siyah" else "color=c=0xc8c8c8:s=320x320,drawgrid=w=20:h=20:t=fill:c=0xffffff@0.5"
    karis = "blend=all_mode=screen:shortest=1" if yontem == "siyah" else "overlay=0:0:shortest=1"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{sure * 0.5:.2f}", *dec, "-i", str(h),
                    "-f", "lavfi", "-i", zemin, "-filter_complex",
                    f"[0:v]format=rgba,scale=320:320:force_original_aspect_ratio=decrease,"
                    f"pad=320:320:(ow-iw)/2:(oh-ih)/2:color=black@0[a];"
                    f"[1:v]format=rgba[z];[z][a]{karis}",
                    "-frames:v", "1", "-update", "1", str(hedef)], check=True)
    return hedef if hedef.is_file() else None


def _donustur(f: Path, yontem: Yontem, hedef_kok: Path, kid: str, benzerlik: float) -> Path:
    if yontem == "alfa" and f.suffix.lower() == ".webm":
        return shutil.copy(f, hedef_kok / f"{kid}.webm") and hedef_kok / f"{kid}.webm"
    if yontem in ("alfa", "gif"):
        return _cevir_gif(f, hedef_kok / f"{kid}.webm")
    if yontem == "yesil":
        return _cevir_yesil(f, hedef_kok / f"{kid}.webm", benzerlik)
    if yontem == "siyah":
        h = hedef_kok / f"{kid}{f.suffix.lower()}"
        shutil.copy(f, h)
        return h
    if yontem == "lottie":
        return _lottie_cikar(f, hedef_kok / f"{kid}.json")
    h = hedef_kok / f"{kid}.svg"
    shutil.copy(f, h)
    return h


def _onizleme(h: Path, yontem: Yontem, kok: Path) -> None:
    """poster.jpg ve kontak.jpg; alfalı olanlar dama zeminde (alfa kaybı görünsün), siyah-screen gri zeminde screen ile."""
    if yontem in ("lottie", "svg"):
        return  # Lottie ve SVG posterini galeri (vedit motion kontak) üretir
    _poster(h, kok / "poster.jpg", yontem)
    dec = ["-c:v", "libvpx-vp9"] if h.suffix == ".webm" else []
    sure = ff.probe(h)["duration"] or 1
    zemin = "color=c=0x6e6e6e:s=320x320" if yontem == "siyah" else "color=c=0xc8c8c8:s=320x320,drawgrid=w=20:h=20:t=fill:c=0xffffff@0.5"
    karis = "blend=all_mode=screen:shortest=1" if yontem == "siyah" else "overlay=0:0:shortest=1"
    secim = f"fps={6 / sure:.4f},"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "0.00", *dec, "-i", str(h),
                    "-f", "lavfi", "-i", zemin, "-filter_complex",
                    f"[0:v]{secim}format=rgba,scale=320:320:force_original_aspect_ratio=decrease,"
                    f"pad=320:320:(ow-iw)/2:(oh-ih)/2:color=black@0[a];"
                    f"[1:v]format=rgba[z];[z][a]{karis},tile=6x1",
                    "-frames:v", "1", "-update", "1", str(kok / "kontak.jpg")], check=True)


# ------------------------------------------------------------------ kayıt

def _kimlik(ad: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", ad.lower().translate(str.maketrans("çğıöşü", "cgiosu"))).strip("-")
    return s[:48] or "varlik"


def kok() -> Path:
    return paths.MOTION_DIR / "dis"


def ice_al(f: Path, lisans: Lisans, *, ad: str | None = None, tur: str = "overlay", etiketler: list[str] | None = None,
           ne_zaman: str = "", yontem: Yontem | None = None, benzerlik: float = 0.18) -> dict:
    """Tek dosya. Döner: manifest kaydı. Lisans kaydı Lisans modeliyle doğrulanmış olmalı."""
    if tur not in TURLER:
        raise LisansHatasi(f"tür {', '.join(TURLER)} olmalı")
    yontem = yontem or yontem_bul(f)
    kid = _kimlik(f"{lisans.kaynak}-{ad or f.stem}")
    hedef = kok() / _kimlik(lisans.kaynak) / kid
    if hedef.exists():
        raise LisansHatasi(f"{kid} zaten var: {paths.rel(hedef)}")
    hedef.mkdir(parents=True)
    try:
        shutil.copy(f, hedef / f"orijinal{f.suffix.lower()}")
        h = _donustur(f, yontem, hedef, kid, benzerlik)
        _onizleme(h, yontem, hedef)
        bilgi = ff.probe(h) if yontem not in ("lottie", "svg") else {"duration": _lottie_sure(h) if yontem == "lottie" else 0}
        v = bilgi.get("video") or {}
        meta = {"id": f"dis-{kid}", "title": ad or f.stem, "kind": tur, "tags": etiketler or [], "ne_zaman": ne_zaman,
                "alfa_yontemi": yontem, "karisim": "screen" if yontem == "siyah" else "normal",
                "width": v.get("width"), "height": v.get("height"), "duration_s": round(bilgi.get("duration") or 0, 3),
                "dosya": h.name, "lisans": lisans.model_dump()}
        (hedef / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    except Exception:
        shutil.rmtree(hedef, ignore_errors=True)
        raise
    return manifest_kaydi(hedef)


def _lottie_sure(h: Path) -> float:
    j = json.loads(h.read_text(encoding="utf-8"))
    return round((j.get("op", 0) - j.get("ip", 0)) / (j.get("fr") or 30), 3)


def manifest_kaydi(klasor: Path) -> dict:
    m = json.loads((klasor / "meta.json").read_text(encoding="utf-8"))
    rel = klasor.relative_to(paths.ROOT).as_posix()
    li = m["lisans"]
    e = {"id": m["id"], "file": f"{rel}/{m['dosya']}", "title": m["title"], "site": li["kaynak"], "kind": m["kind"],
         "tags": m.get("tags", []), "ne_zaman": m.get("ne_zaman", ""), "alpha": m["alfa_yontemi"] != "siyah",
         "alfa_yontemi": m["alfa_yontemi"], "karisim": m.get("karisim", "normal"), "width": m.get("width"), "height": m.get("height"),
         "duration_s": m.get("duration_s"), "license": li["lisans"], "source_url": li["url"],
         "attribution": li["atif_metni"] or None, "atif_gerekli": li["atif_gerekli"], "kisitlar": li["kisitlar"], "dis": True}
    if (klasor / "poster.jpg").exists():
        e["poster"] = f"{rel}/poster.jpg"
    return e


def manifest_yenile() -> list[dict]:
    """library/motion/dis/**/meta.json → manifest.json'daki dış kayıtlar (elle yazılmaz). Silinen klasörün kaydı düşer."""
    f = paths.MOTION_DIR / "manifest.json"
    d = json.loads(f.read_text(encoding="utf-8"))
    dis = [manifest_kaydi(m.parent) for m in sorted(kok().glob("*/*/meta.json"))] if kok().exists() else []
    d["entries"] = [e for e in d["entries"] if not e.get("dis")] + dis
    f.write_text(json.dumps(d, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return dis


def _stil_varlik_bul(yol: str) -> dict | None:
    if not yol.startswith("stil:"):
        return None
    parcalar = [x for x in yol.removeprefix("stil:").replace("\\", "/").split("/") if x]
    if len(parcalar) < 3 or ".." in parcalar:
        return None
    studyo, stil_ad = parcalar[0], parcalar[1]
    alt = "/".join(parcalar[2:])
    f = paths.STUDIOS / studyo / "styles" / stil_ad / "varliklar.json"
    if not f.is_file():
        return None
    try:
        depo = json.loads(f.read_text(encoding="utf-8"))
        for v in depo.get("yuklenenler") or []:
            if v.get("dosya") == alt or v.get("orijinal") == alt:
                return v
    except (OSError, ValueError):
        return None
    return None


def atif_satirlari(k) -> list[str]:
    """Kurguda kullanılan, atıf isteyen dış varlıkların atıf satırları (yayin.md için)."""
    yollar = {kay.yol.removeprefix("library:") for kay in k.kaynaklar.values() if kay.yol.startswith("library:motion/dis/")}
    yollar |= {str((c.bilesen.param or {}).get("dosya", "")).removeprefix("library:") for c in k.klipler
               if c.bilesen and c.bilesen.ad == "dis/lottie"}
    sat = []
    for m in sorted(kok().glob("*/*/meta.json")) if kok().exists() else []:
        meta = json.loads(m.read_text(encoding="utf-8"))
        rel = (m.parent / meta["dosya"]).relative_to(paths.LIBRARY).as_posix()
        if rel in yollar and meta["lisans"]["atif_gerekli"]:
            sat.append(meta["lisans"]["atif_metni"])
    stil_yollari = [kay.yol for kay in k.kaynaklar.values() if kay.yol.startswith("stil:")]
    stil_yollari += [str((c.bilesen.param or {}).get("dosya", "")) for c in k.klipler
                     if c.bilesen and c.bilesen.ad == "dis/lottie" and str((c.bilesen.param or {}).get("dosya", "")).startswith("stil:")]
    for sy in stil_yollari:
        v = _stil_varlik_bul(sy)
        if v and (v.get("atif") or "").strip():
            sat.append(v["atif"].strip())
    return list(dict.fromkeys(sat))


def karisim_haritasi(k) -> dict[str, str]:
    """kaynak id → "screen": siyah zeminli dış ve stil varlıklarının kurgudaki kaynakları."""
    sonuc = {}
    for ad, kay in k.kaynaklar.items():
        if kay.yol.startswith("library:motion/dis/"):
            meta = paths.LIBRARY / Path(kay.yol.removeprefix("library:")).parent / "meta.json"
            try:
                if json.loads(meta.read_text(encoding="utf-8")).get("karisim") == "screen":
                    sonuc[ad] = "screen"
            except (OSError, ValueError):
                continue
        elif kay.yol.startswith("stil:"):
            v = _stil_varlik_bul(kay.yol)
            if v and v.get("yontem") == "siyah":
                sonuc[ad] = "screen"
    return sonuc
