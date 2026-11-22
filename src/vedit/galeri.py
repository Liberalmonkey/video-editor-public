"""Stil ve motion galerisi: stil paketleri, temalar, motion kayıtları, fizik ve ışık presetleri, karakterler tek listede.

WHY: bkz. wiki/decisions/0039-fizik-ritim-galeri.md. Kullanıcı çok farklı seçeneği bir arada görmek istedi (2026-11-16).
Önizlemeler kütüphane düzeyindedir (`library/galeri/<tür>/<ad>.jpg|.mp4`), proje başına üretilmez. Fizik, ışık ve
karakter önizlemeleri tek Remotion render'ında sırayla çizilip ffmpeg ile parçalanır: her önizleme için ayrı paketleme
dakikalar sürerdi.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path
from urllib.parse import quote

from . import ff, fizik, karakter, motion, paths, stil

KOK = paths.LIBRARY / "galeri"
TEMA_KART = KOK / "tema-kart.html"
TURLER = ("stil", "tema", "motion", "fizik", "isik", "karakter", "hazir")
ONIZLEME_SURE = 3.0
ONIZLEME_ISIK_PRESETI = "kule-cokus"  # ışık karşılaştırması için: gölge, parlama ve hareket aynı sahnede


def _url(f: Path) -> str | None:
    return "/lib/" + quote(f.relative_to(paths.LIBRARY).as_posix()) if f.exists() else None


def _onizleme(tur: str, ad: str) -> dict:
    return {"poster_url": _url(KOK / tur / f"{ad}.jpg"), "video_url": _url(KOK / tur / f"{ad}.mp4")}


def ogeler() -> list[dict]:
    """Galerinin bütün öğeleri; arayüz tür çipleriyle süzer."""
    cikti: list[dict] = []
    for studyo in paths.STUDIO_NAMES:
        for s in stil.liste(studyo):
            if not s["hazir"]:
                continue
            tok = paths.STUDIOS / studyo / "styles" / s["ad"] / "tokens.json"
            try:
                t = json.loads(tok.read_text(encoding="utf-8")) if tok.exists() else {}
            except ValueError:
                t = {}
            renk = t.get("colors") or {}
            cikti.append({"tur": "stil", "id": f"{studyo}/{s['ad']}", "title": s["ad"], "studyo": studyo,
                          "ne_zaman": (t.get("description") or "")[:220],
                          "palet": [v for k, v in renk.items() if isinstance(v, str) and v.startswith("#")][:6],
                          **_onizleme("stil", f"{studyo}-{s['ad']}")})
    for ad in motion.temalar():
        f = motion.tema_yolu(ad)
        bas = f.read_text(encoding="utf-8").split("*/")[0].strip("/* \n") if f else ""
        renk, font = fizik.tema_renkleri(ad)
        cikti.append({"tur": "tema", "id": ad, "title": ad, "ne_zaman": bas, "palet": list(renk.values()), "font": font,
                      **_onizleme("tema", ad)})
    man = paths.MOTION_DIR / "manifest.json"
    for e in (json.loads(man.read_text(encoding="utf-8")).get("entries", []) if man.exists() else []):
        dosya = paths.ROOT / e["file"] if e.get("file") else None
        poster = dosya.parent / "poster.jpg" if dosya else None
        cikti.append({"tur": "motion", "id": e["id"], "title": (e.get("title") or e["id"]).split(":")[0], "kind": e.get("kind"),
                      "ne_zaman": e.get("ne_zaman", ""), "sablon": bool(e.get("param")), "file": e.get("file"),
                      "poster_url": _url(poster) if poster else None, "video_url": _url(dosya) if dosya else None,
                      "tags": e.get("tags", [])})
    for ad, t in fizik.presetler().items():
        cikti.append({"tur": "fizik", "id": ad, "title": t["title"], "ne_zaman": t["ne_zaman"], "sure": t["sure"],
                      "param": t["param"], **_onizleme("fizik", ad)})
    for ad, t in fizik.isiklar().items():
        cikti.append({"tur": "isik", "id": ad, "title": t["title"], "ne_zaman": t["ne_zaman"], **_onizleme("isik", ad)})
    for ad, t in karakter.karakterler().items():
        cikti.append({"tur": "karakter", "id": ad, "title": t.get("title", ad), "ne_zaman": t.get("ne_zaman", ""),
                      "palet": [v for v in t.get("renk", {}).values()][:5], **_onizleme("karakter", ad)})
    from . import hazir_efekt
    for ad, t in hazir_efekt.katalog().items():
        cikti.append({"tur": "hazir", "id": ad, "title": ad.replace("_", " "), "ne_zaman": t.get("ne_zaman", ""),
                      "amac": t.get("amac", ""), **_onizleme("hazir", ad)})
    return cikti


# --- Önizleme üretimi -------------------------------------------------------------------------------------------------

def _klip(i: int, bas: float, sahne: dict, kaynak: str) -> dict:
    return {"id": f"g{i}", "iz": "V1", "bas": bas, "sure": ONIZLEME_SURE, "tur": "sahne", "kaynak": kaynak, "sahne": sahne}


def _sira_render(isim: str, girdiler: list[tuple[str, dict, Path]], is_klasor: Path) -> Path:
    """Sahneleri art arda tek kurguya dizip 640x360 (yatay) render eder. girdiler: (ad, sahne, veri JSON)."""
    from . import hizli

    public = is_klasor / "public"
    # Kurgu.tsx yazı tiplerini staticFile("fonts/...") ile yükler; proje hattındaki _public_hazirla ile aynı bağlama.
    (public / "fonts").mkdir(parents=True, exist_ok=True)
    for f in paths.FONTS_DIR.glob("*.ttf"):
        if not (public / "fonts" / f.name).exists():
            (public / "fonts" / f.name).hardlink_to(f)
    kaynaklar, klipler = {}, []
    for i, (_, sahne, veri) in enumerate(girdiler):
        hedef = public / "veri" / veri.name
        hedef.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(veri, hedef)
        kid = f"K{i}"
        kaynaklar[kid] = {"yol": f"public:veri/{veri.name}", "sure": ONIZLEME_SURE, "w": None, "h": None, "ses": False}
        klipler.append(_klip(i, i * ONIZLEME_SURE, sahne, kid))
    # 1280x720 ve 0,5 ölçek: tam 640x360. 1920x1080 ve 1/3 ölçek tamsayı olmayan yükseklik verip render'ı durduruyordu.
    props = {"sekans": {"w": 1280, "h": 720, "fps": 30}, "kaynaklar": kaynaklar,
             "izler": [{"id": "V1", "tur": "video", "ad": "", "kilit": False, "sessiz": False, "gizli": False, "gain_db": 0}],
             "klipler": [_tam_klip(c) for c in klipler], "altyazi": {"acik": False, "iz": "V1", "stil": None},
             "words": [], "bitis": len(klipler) * ONIZLEME_SURE}
    pf = is_klasor / f"kurgu.render.galeri-{isim}.json"
    pf.write_text(json.dumps(props, ensure_ascii=False), encoding="utf-8")
    out = is_klasor / f"{isim}.mp4"
    hizli._remotion(pf, public, out, "--scale=0.5", "--crf=24", "--x264-preset=veryfast", "--image-format=jpeg")
    return out


def _tam_klip(c: dict) -> dict:
    """Kurgu.tsx'in beklediği bütün klip alanları (schemas.Klip varsayılanları)."""
    from .schemas import Klip
    return Klip.model_validate(c).model_dump()


def _parcala(video: Path, adlar: list[str], hedef: Path, poster_an: float) -> None:
    hedef.mkdir(parents=True, exist_ok=True)
    for i, ad in enumerate(adlar):
        bas = i * ONIZLEME_SURE
        ff.ffmpeg("-y", "-ss", f"{bas:.3f}", "-t", f"{ONIZLEME_SURE:.3f}", "-i", str(video), "-an", "-c:v", "libx264", "-preset", "veryfast",
                  "-crf", "26", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(hedef / f"{ad}.mp4"))
        ff.ffmpeg("-y", "-ss", f"{bas + poster_an:.3f}", "-i", str(video), "-frames:v", "1", "-q:v", "3", str(hedef / f"{ad}.jpg"))


def _gecici_proje(is_klasor: Path):
    """fizik.bagla / bake için yalnız `work` yolu gereken sahte proje."""
    class P:
        work = is_klasor
    return P()


def _fizik_verisi(is_klasor: Path, preset: str, param: dict, isik: str | None = None) -> tuple[dict, Path]:
    renk, font = fizik.tema_renkleri("sinematik-koyu" if isik else "varsayilan")
    girdi = {"preset": preset, "param": param, "fps": 30, "sure": ONIZLEME_SURE, "w": 1280, "h": 720}
    f = is_klasor / "veri" / f"fizik-{preset}-{isik or 'std'}.json"
    fizik.bake(girdi, f)
    v = json.loads(f.read_text(encoding="utf-8"))
    v.update(renk=renk, font=font)
    f.write_text(json.dumps(v, ensure_ascii=False), encoding="utf-8")
    return {"kind": "fizik", "layout": "full", "preset": preset, "param": param, "isik": {"preset": isik or "studyo"}, "olcum": True}, f


def kur(turler: list[str] | None = None, *, yenile: bool = False) -> list[str]:
    """Eksik önizlemeleri üretir; üretilenlerin listesini döner."""
    turler = turler or ["tema", "fizik", "isik", "karakter"]
    is_klasor = paths.ROOT / "work" / "galeri"
    is_klasor.mkdir(parents=True, exist_ok=True)
    yapilan: list[str] = []
    eksik = lambda tur, ad: yenile or not (KOK / tur / f"{ad}.jpg").exists()
    if "tema" in turler:
        from . import hf_motion
        for ad in motion.temalar():
            if eksik("tema", ad):
                (KOK / "tema").mkdir(parents=True, exist_ok=True)
                hf_motion.kare(TEMA_KART, KOK / "tema" / f"{ad}.jpg", t=0.0, w=640, h=360, css=motion.tema_yolu(ad))  # ADR 0051
                yapilan.append(f"tema/{ad}")
    if "fizik" in turler:
        adlar = [a for a in fizik.presetler() if eksik("fizik", a)]
        if adlar:
            g = [(a, *_fizik_verisi(is_klasor, a, {})) for a in adlar]
            _parcala(_sira_render("fizik", g, is_klasor), adlar, KOK / "fizik", 1.4)
            yapilan += [f"fizik/{a}" for a in adlar]
    if "isik" in turler:
        adlar = [a for a in fizik.isiklar() if eksik("isik", a)]
        if adlar:
            g = [(a, *_fizik_verisi(is_klasor, ONIZLEME_ISIK_PRESETI, {"kat": 6}, a)) for a in adlar]
            _parcala(_sira_render("isik", g, is_klasor), adlar, KOK / "isik", 0.4)
            yapilan += [f"isik/{a}" for a in adlar]
    if "karakter" in turler:
        adlar = [a for a in karakter.karakterler() if eksik("karakter", a)]
        if adlar:
            g = []
            for a in adlar:
                # Sessiz önizleme: örnek bir konuşma deseni (kapalı-açık-yuvarlak) ve iki vurgu.
                desen = ("KKKUAAAAEEEUKKOOOOAAAKKKUEEEEAAOOKK" * 4)[: int(ONIZLEME_SURE * 30)]
                v = {"karakter": karakter.karakterler()[a], "fps": 30, "viseme": desen, "vurgular": [18, 60], "tohum": 7}
                f = is_klasor / "veri" / f"karakter-{a}.json"
                f.parent.mkdir(parents=True, exist_ok=True)
                f.write_text(json.dumps(v, ensure_ascii=False), encoding="utf-8")
                g.append((a, {"kind": "karakter", "layout": "full", "karakter": a, "olcek": 0.85}, f))
            _parcala(_sira_render("karakter", g, is_klasor), adlar, KOK / "karakter", 0.7)
            yapilan += [f"karakter/{a}" for a in adlar]
    return yapilan
