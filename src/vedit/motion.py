"""Motion kütüphanesi: kaynak (html + meta.json) → saydam webm, poster, kontak sayfası ve manifest kaydı.

WHY: bkz. wiki/decisions/0036-motion-kutuphanesi-ve-ajanlar.md. Manifest elle yazılmaz; her kayıt kendi klasöründeki
meta.json'dan üretilir ki alt ajanlar aynı dosyaya yazmasın. `param` taşıyan kayıt şablondur: kurguda
`sablon: {ad, param, tema}` ile kullanılır, webm'i proje başına üretilir ve özetle önbelleğe alınır.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path

from . import hf_motion, paths

TURLER = ("overlay", "background", "transition", "lower-third", "icon", "broll")
ZEMIN = "0x1B1E25"  # poster ve kontak zemini: saydam grafiğin hem açık hem koyu öğesi görünür


def kok() -> Path:
    return paths.MOTION_DIR / "custom"


def tema_yolu(ad: str | Path | None) -> Path | None:
    """Tema CSS'i; ad boşsa ya da 'varsayilan' dosyası yoksa None (HTML'deki yedek değerler geçerli).

    Path verilirse (proje teması `work/edit/motion_tema.css`, ADR 0042) olduğu gibi döner.
    """
    if isinstance(ad, Path):
        return ad if ad.is_file() else None
    if not ad:
        return None
    from .tema_token import TAKMA  # eski ad (editorial-acik) kanonik temaya gider, ADR 0043
    ad = TAKMA.get(ad, ad)
    if not re.fullmatch(r"[A-Za-z0-9_-]+", ad):  # WHY: ad kullanıcıdan gelir; tema klasörü dışına çıkamasın (ADR 0050)
        return None
    f = paths.MOTION_DIR / "tema" / f"{ad}.css"
    return f if f.is_file() else None


def temalar() -> list[str]:
    return sorted(f.stem for f in (paths.MOTION_DIR / "tema").glob("*.css"))


def meta(kimlik: str) -> dict:
    """meta.json'u okur ve sözleşmeyi sınar; hata Türkçe ve kaydı adıyla söyler."""
    d = kok() / kimlik
    if not (d / f"{kimlik}.html").is_file():
        raise SystemExit(f"Motion kaynağı yok: {paths.rel(d / f'{kimlik}.html')}")
    try:
        m = json.loads((d / "meta.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise SystemExit(f"{kimlik}: meta.json okunamadı: {e}")
    eksik = [a for a in ("title", "kind", "sure", "w", "h") if m.get(a) in (None, "")]
    if eksik:
        raise SystemExit(f"{kimlik}: meta.json'da eksik alan: {', '.join(eksik)}")
    if m["kind"] not in TURLER:
        raise SystemExit(f"{kimlik}: tür '{m['kind']}' geçersiz (geçerli: {', '.join(TURLER)})")
    if not (0 < m["sure"] <= 30):
        raise SystemExit(f"{kimlik}: sure 0-30 sn arasında olmalı")
    for ad, pr in (m.get("param") or {}).items():
        if not isinstance(pr, dict) or "vars" not in pr:
            raise SystemExit(f"{kimlik}: param.{ad} için {{\"vars\": ...}} gerekli")
    return m


def kimlikler() -> list[str]:
    return sorted(d.name for d in kok().iterdir() if (d / "meta.json").is_file()) if kok().is_dir() else []


def sablonlar() -> dict[str, dict]:
    """Parametre alan kayıtlar. Bozuk meta atlanır: tek bozuk kayıt tüm kurguyu durdurmasın."""
    cikti = {}
    for k in kimlikler():
        try:
            m = meta(k)
        except SystemExit:
            continue
        if m.get("param"):
            cikti[k] = m
    return cikti


def param_hatalari(m: dict, param: dict) -> list[str]:
    """Bilinmeyen ad, tür uyuşmazlığı, uzun metin, aralık dışı sayı."""
    h = []
    tanim = m.get("param") or {}
    for ad, v in (param or {}).items():
        if ad not in tanim:
            h.append(f"bilinmeyen parametre '{ad}' (geçerli: {', '.join(tanim) or 'yok'})")
            continue
        pr = tanim[ad]
        if isinstance(pr["vars"], bool) or not isinstance(pr["vars"], (int, float)):
            if isinstance(pr["vars"], str):
                if not isinstance(v, str):
                    h.append(f"'{ad}' metin olmalı")
                elif pr.get("max") and len(v) > pr["max"]:
                    h.append(f"'{ad}' en çok {pr['max']} karakter ({len(v)} yazılmış)")
                elif pr.get("secenek") and v not in pr["secenek"]:
                    h.append(f"'{ad}' şunlardan biri olmalı: {', '.join(pr['secenek'])}")
            continue
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            h.append(f"'{ad}' sayı olmalı")
        elif not (pr.get("min", v) <= v <= pr.get("max", v)):
            h.append(f"'{ad}' {pr.get('min')}-{pr.get('max')} aralığında olmalı ({v} yazılmış)")
    return h


def _ff(*a: str) -> None:
    # WHY: Türkçe Windows varsayılan cp1254 kodlamasında ffmpeg UTF-8 çıktısı UnicodeDecodeError vermesin.
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", *a], capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise SystemExit(f"ffmpeg başarısız: {r.stderr.strip()[-300:]}")


def _onizleme(webm: Path, m: dict) -> None:
    """poster.jpg + onizleme.mp4 (alfa kırpımlı, anlamlı kare; ADR 0061) ve kontak.jpg (altı kare) koyu zeminde.

    libvpx çözücü olmadan alfa okunmaz.
    """
    from . import onizleme
    w, h, sure = m["w"], m["h"], m["sure"]
    zemin = f"color={ZEMIN}:s={w}x{h}:r=30[b];[b][0:v]overlay=shortest=1"
    onizleme.uret(webm, webm.parent, w=w, h=h, sure=sure, tur=m.get("kind", ""))
    _ff("-c:v", "libvpx-vp9", "-i", str(webm), "-filter_complex",
        f"{zemin},fps=6/{sure},scale=-2:320,tile=6x1", "-frames:v", "1", "-q:v", "4", str(webm.with_name("kontak.jpg")))


def kayit(kimlik: str, m: dict) -> dict:
    """Manifest satırı. Alan adları ADR 0012 ile aynı; ne_zaman, poster ve param bu ADR'la geldi."""
    rel = f"library/motion/custom/{kimlik}"
    e = {"id": kimlik, "file": f"{rel}/{kimlik}.webm", "title": m["title"], "site": "custom", "kind": m["kind"],
         "tags": m.get("tags", []), "ne_zaman": m.get("ne_zaman", ""), "alpha": True, "width": m["w"], "height": m["h"],
         "duration_s": m["sure"], "loop": bool(m.get("loop")), "license": "project-made", "source": f"{rel}/{kimlik}.html",
         "source_url": m.get("source_url"), "poster": f"{rel}/poster.jpg", "onizleme": f"{rel}/onizleme.mp4",
         "attribution": f"proje yapımı (ADR 0036); yeniden üret: vedit motion kur {kimlik}"}
    if m.get("param"):
        e.update(param=m["param"], tam=bool(m.get("tam")))
    if yerine := arsiv().get(kimlik):
        e["arsiv"] = yerine  # ADR 0045: native karşılığı var; dosya yerinde, AI edit seçmez
    return e


def arsiv() -> dict[str, str]:
    """library/motion/arsiv.json: eski kimlik → native karşılığı ya da 'V1:<geçiş>'."""
    f = paths.MOTION_DIR / "arsiv.json"
    try:
        return json.loads(f.read_text(encoding="utf-8")).get("kayitlar", {})
    except (OSError, ValueError):
        return {}


def manifest_yaz(kayitlar: list[dict]) -> None:
    """Verilen custom kayıtları ekler ya da günceller; kullanıcının yüklediği diğer kayıtlara dokunmaz."""
    f = paths.MOTION_DIR / "manifest.json"
    d = json.loads(f.read_text(encoding="utf-8"))
    yeni = {e["id"]: e for e in kayitlar}
    d["entries"] = [yeni.pop(e["id"], e) for e in d["entries"]] + list(yeni.values())
    f.write_text(json.dumps(d, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def onizleme_yenile(hedefler: list[str] | None = None) -> list[str]:
    """Var olan webm'lerin posterini ve döngü önizlemesini yeniden üretir; render etmez, manifesti günceller (ADR 0061)."""
    yapilan, kayitlar = [], []
    for k in hedefler or kimlikler():
        webm = kok() / k / f"{k}.webm"
        if not webm.is_file():
            continue
        m = meta(k)
        _onizleme(webm, m)
        kayitlar.append(kayit(k, m))
        yapilan.append(k)
    if kayitlar:
        manifest_yaz(kayitlar)
    return yapilan


def kur(hedefler: list[str] | None = None, *, yalniz_manifest: bool = False, manifest: bool = True) -> list[dict]:
    """Kaynaktan webm + poster + kontak üretir, manifesti günceller. Kilitli kayıt atlanır (ADR 0012)."""
    kilitli = set(json.loads((paths.LIBRARY / "kit.json").read_text(encoding="utf-8")).get("locked", []))
    cikti = []
    for k in hedefler or kimlikler():
        m = meta(k)
        webm = kok() / k / f"{k}.webm"
        if k in kilitli and webm.exists():
            print(f"  {k}: kilitli, yeniden üretilmedi")
        elif not yalniz_manifest:
            # WHY: bkz. wiki/decisions/0051-uctan-uca-hyperframes.md. Üretim HyperFrames'te (eskiden Playwright, pano.render).
            hf_motion.render(kok() / k / f"{k}.html", webm, sure=m["sure"], w=m["w"], h=m["h"],
                        css=tema_yolu("varsayilan"), param={a: pr["vars"] for a, pr in (m.get("param") or {}).items()} or None,
                        son_tam=not m.get("loop"))
            _onizleme(webm, m)
            print(f"  {k}: {m['kind']} · {m['sure']} sn · {m['w']}x{m['h']}")
        cikti.append(kayit(k, m))
    if manifest:  # paralel çalışan tasarımcı ajanlar manifesti yazmaz (--onizle); ana oturum sonda bir kez yazar
        manifest_yaz(cikti)
    return cikti


def ozet(ad: str, param: dict, tema: str | Path | None, w: int, h: int) -> str:
    """Önbellek anahtarı: kaynak HTML, tema CSS'i, parametre ya da boyut değişince değişir."""
    s = hashlib.sha1()
    s.update((kok() / ad / f"{ad}.html").read_bytes())
    t = tema_yolu(tema)
    s.update(t.read_bytes() if t else b"")
    if t and (j := t.with_suffix(".json")).is_file():  # adımlı zaman ve piksel token'ı render'ı değiştirir (ADR 0043)
        s.update(j.read_bytes())
    s.update(json.dumps([param, w, h], sort_keys=True, ensure_ascii=False).encode())
    return s.hexdigest()[:10]


def sablon_uret(ad: str, param: dict | None, tema: str | Path | None, klasor: Path, *, sekans: tuple[int, int]) -> tuple[Path, dict]:
    """Şablonu parametreyle `klasor` altına üretir (varsa yeniden üretmez). (dosya, {sure, w, h}) döner."""
    m = meta(ad)
    w, h = sekans if m.get("tam") else (m["w"], m["h"])
    tam = {**{a: pr["vars"] for a, pr in (m.get("param") or {}).items()}, **(param or {})}
    hedef = klasor / f"{ad}-{ozet(ad, tam, tema, w, h)}.webm"
    if not hedef.exists():
        hf_motion.render(kok() / ad / f"{ad}.html", hedef, sure=m["sure"], w=w, h=h, css=tema_yolu(tema) or tema_yolu("varsayilan"), param=tam,
                    son_tam=not m.get("loop"))
    return hedef, {"sure": m["sure"], "w": w, "h": h}


def olc(hedefler: list[str] | None = None) -> list[tuple[str, list[str]]]:
    """Üretilmiş webm'i ölçer: alfa, boyut, kare sayısı, son karenin boşluğu, geçişte orta karenin kapalılığı. (kimlik, kusurlar)."""
    cikti = []
    for k in hedefler or kimlikler():
        m, f, kusur = meta(k), kok() / k / f"{k}.webm", []
        if not f.is_file():
            cikti.append((k, ["webm yok: vedit motion kur " + k]))
            continue
        # WHY: cp1254 kodlamasında UnicodeDecodeError ve bozuk/akışsız ffprobe çıktısında KeyError/IndexError önlenir.
        r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height:stream_tags=alpha_mode",
                            "-of", "json", str(f)], capture_output=True, text=True, encoding="utf-8", errors="replace")
        if r.returncode != 0:
            raise RuntimeError(f"ffprobe başarısız ({k}): {(r.stderr or r.stdout).strip()[-300:]}")
        try:
            streams = json.loads(r.stdout or "{}").get("streams") or []
        except ValueError as e:
            raise RuntimeError(f"ffprobe çıktısı okunamadı ({k}): {e}") from e
        if not streams:
            raise RuntimeError(f"Video akışı bulunamadı ({k})")
        st = streams[0]
        if st.get("tags", {}).get("alpha_mode") != "1":
            kusur.append("alfa kanalı yok")
        if (st["width"], st["height"]) != (m["w"], m["h"]):
            kusur.append(f"boyut {st['width']}x{st['height']}, meta {m['w']}x{m['h']}")
        # Kare başına alfa en büyük ve en küçük değeri (0-255); libvpx çözücü olmadan alfa okunmaz.
        r = subprocess.run(["ffmpeg", "-v", "error", "-c:v", "libvpx-vp9", "-i", str(f), "-vf",
                            "alphaextract,signalstats,metadata=print:key=lavfi.signalstats.YMAX:file=-,metadata=print:key=lavfi.signalstats.YMIN:file=-",
                            "-f", "null", "-"], capture_output=True, text=True, encoding="utf-8", errors="replace")
        if r.returncode != 0:
            raise RuntimeError(f"ffmpeg alfa ölçümü başarısız ({k}): {(r.stderr or r.stdout).strip()[-300:]}")
        enb = [float(x.split("=")[1]) for x in r.stdout.splitlines() if "YMAX=" in x]
        enk = [float(x.split("=")[1]) for x in r.stdout.splitlines() if "YMIN=" in x]
        beklenen = round(m["sure"] * 30)
        if len(enb) != beklenen:
            kusur.append(f"{len(enb)} kare, beklenen {beklenen}")
        if enb and max(enb) < 8:
            kusur.append("bütün kareler boş")
        if enb and not m.get("loop") and enb[-1] > 8:
            kusur.append(f"son kare boş değil (alfa {enb[-1]:.0f})")
        if enk and m["kind"] == "transition" and enk[len(enk) // 2] < 250:
            kusur.append(f"orta karede ekran tam kapanmıyor (en düşük alfa {enk[len(enk) // 2]:.0f})")
        if enb and m.get("loop") and m["kind"] != "background" and enb[0] < 8:
            kusur.append("döngünün ilk karesi boş")
        cikti.append((k, kusur))
    return cikti
