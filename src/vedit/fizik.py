"""Fizik sahnesi (`tur: "sahne"`, `sahne.kind: "fizik"`): denetim, bake ve temas sesleri.

WHY: bkz. wiki/decisions/0039-fizik-ritim-galeri.md. Simülasyon `studio/remotion/fizik/bake.mjs` ile bir kez koşar
(Rapier, sabit adım); sonuç `work/public/fizik/<preset>-<özet>.json` olur ve klibin kaynağına bağlanır. Remotion yalnız
okur. Temas anları aynı dosyadan ses olayına gider: çarpma sesi görüntüdeki temas karesine oturur, el ile hizalanmaz.
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
from functools import lru_cache
from pathlib import Path

from . import motion, paths

KOK = paths.ROOT / "studio" / "remotion" / "fizik"
BAKE = KOK / "bake.mjs"
KATALOG_DOSYA = KOK / "presetler.json"
# Sahne başına ses sınırları. Kule çöküşü 60, dubalı araba 30 temas üretir; hepsi duyulursa gürültü olur.
# WHY: viral-kurgu ve usta-editor kuralı: `sert` videoda bir iki büyük an içindir. Tık zinciri (domino) ritimdir, ayrı sayılır.
EN_COK_DARBE, DARBE_ARALIK = 8, 0.1
EN_COK_TIK, TIK_ARALIK = 24, 0.06
EN_COK_SERT = 2


@lru_cache(maxsize=1)
def katalog() -> dict:
    return json.loads(KATALOG_DOSYA.read_text(encoding="utf-8"))


def presetler() -> dict:
    return katalog()["presetler"]


def isiklar() -> dict:
    return katalog()["isik"]


def hatalar(c) -> list[str]:
    """Render'da yanlış çıkacak fizik sahnesi alanları: bilinmeyen preset, parametre, aralık dışı sayı, uzun metin."""
    s = c.sahne or {}
    if c.tur != "sahne" or s.get("kind") != "fizik":
        return []
    h = []
    ad = s.get("preset")
    tanim = presetler().get(ad)
    if not tanim:
        return [f"{c.id}: bilinmeyen fizik preseti '{ad}'. Presetler: {', '.join(presetler())}"]
    for k, v in (s.get("param") or {}).items():
        t = tanim["param"].get(k)
        if t is None:
            h.append(f"{c.id}: '{ad}' presetinde '{k}' parametresi yok ({', '.join(tanim['param'])})")
        elif t["tip"] == "sayi" and (not isinstance(v, (int, float)) or not t["min"] <= v <= t["max"]):
            h.append(f"{c.id}: {ad}.{k} = {v!r}; {t['min']}-{t['max']} arası sayı olmalı")
        elif t["tip"] == "secim" and v not in t["secenek"]:
            h.append(f"{c.id}: {ad}.{k} = {v!r}; seçenekler: {', '.join(t['secenek'])}")
        elif t["tip"] == "metin" and len(str(v)) > t.get("en_cok", 60):
            h.append(f"{c.id}: {ad}.{k} metni {len(str(v))} karakter; en çok {t.get('en_cok', 60)}")
    isik = (s.get("isik") or {}).get("preset")
    if isik and isik not in isiklar():
        h.append(f"{c.id}: bilinmeyen ışık preseti '{isik}'. Işıklar: {', '.join(isiklar())}")
    return h


def tema_renkleri(ad) -> tuple[dict, str | None]:
    """Motion temasının token renkleri ve başlık fontu: fizik sahnesi videonun geri kalanıyla aynı paleti kullanır.

    WHY: bkz. wiki/decisions/0043-stile-bagli-tema-tokenlari.md. Token tek kaynak; CSS ayrıştırma kalktı.
    """
    from . import tema_token
    t = tema_token.oku(motion.tema_yolu(ad) or motion.tema_yolu("varsayilan"))
    if not t:
        return {}, None
    r = t.renk
    return {k: getattr(r, k) for k in ("vurgu", "ikincil", "zemin", "yazi", "soluk")}, t.font.baslik


def _ozet(girdi: dict) -> str:
    h = hashlib.sha1(BAKE.read_bytes() + KATALOG_DOSYA.read_bytes())
    h.update(json.dumps(girdi, sort_keys=True, ensure_ascii=False).encode())
    return h.hexdigest()[:12]


def bake(girdi: dict, hedef: Path) -> Path:
    """node bake.mjs ile simülasyonu koşar. Aynı girdi her zaman aynı dosyayı üretir (deterministik)."""
    node = shutil.which("node")
    if not node:
        raise SystemExit("Fizik sahnesi için Node.js gerekli (node bulunamadı).")
    hedef.parent.mkdir(parents=True, exist_ok=True)
    gecici = hedef.with_suffix(".girdi.json")
    gecici.write_text(json.dumps(girdi, ensure_ascii=False), encoding="utf-8")
    try:
        r = subprocess.run([node, str(BAKE), str(gecici), str(hedef)], capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=120)
    except subprocess.TimeoutExpired:
        gecici.unlink(missing_ok=True)
        raise SystemExit(f"Fizik bake 120 sn'de bitmedi ({girdi.get('preset')}); süreyi ya da gövde sayısını azalt.")
    gecici.unlink(missing_ok=True)
    if r.returncode != 0 or not hedef.exists():
        raise SystemExit(f"Fizik bake başarısız ({girdi.get('preset')}): {(r.stderr or r.stdout).strip()[-600:]}")
    return hedef


def bagla(p, k) -> bool:
    """Fizik sahnelerini bake eder, JSON'u klibin kaynağına bağlar. Kurgu değiştiyse True (motion_bagla kalıbı)."""
    from .schemas import KurguKaynak

    degisti = False
    for c in k.klipler:
        s = c.sahne or {}
        if c.tur != "sahne" or s.get("kind") != "fizik" or hatalar(c):
            continue
        from .kurgu import etkin_tema  # döngüsel içe aktarım: kurgu fizik'i içe aktarır
        renk, font = tema_renkleri(etkin_tema(p, s.get("tema") or k.motion_tema))
        girdi = {"preset": s["preset"], "param": s.get("param") or {}, "fps": k.sekans.fps, "sure": round(c.sure, 3),
                 "w": k.sekans.w, "h": k.sekans.h}
        oz = _ozet({**girdi, "renk": renk, "font": font})
        f = p.work / "public" / "fizik" / f"{s['preset']}-{oz}.json"
        if not f.exists():
            bake(girdi, f)
            veri = json.loads(f.read_text(encoding="utf-8"))
            veri.update(renk=renk, font=font)
            f.write_text(json.dumps(veri, ensure_ascii=False), encoding="utf-8")
        kid = "F_" + oz
        if kid not in k.kaynaklar:
            k.kaynaklar[kid] = KurguKaynak(yol=f"public:fizik/{f.name}", sure=c.sure, ses=False)
        if c.kaynak != kid:
            c.kaynak, degisti = kid, True
    return degisti


def _veri(p, k, c) -> dict | None:
    from . import kurgu

    if not c.kaynak or c.kaynak not in k.kaynaklar:
        return None
    try:
        return json.loads(kurgu.dosya(p, k.kaynaklar[c.kaynak].yol).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def temaslar(p, k) -> list[dict]:
    """Bütün fizik sahnelerinin temasları sekans zamanında: {t, hiz, guc, klip, cift}."""
    gizli = {i.id for i in k.izler if i.gizli}
    cikti = []
    for c in k.klipler:
        if c.iz in gizli or c.tur != "sahne" or (c.sahne or {}).get("kind") != "fizik":
            continue
        v = _veri(p, k, c)
        for t in (v or {}).get("temas", []):
            if t["t"] < c.sure:
                cikti.append({"t": round(c.bas + t["t"], 3), "hiz": t["hiz"], "guc": t["guc"], "klip": c.id, "cift": f"{t['a']}-{t['b']}",
                              "ses": (c.sahne or {}).get("ses", True) is not False})
    return sorted(cikti, key=lambda x: x["t"])


def ses_olaylari(p, k) -> list[dict]:
    """Temas → olaysesi rol olayı. Hafif temas tık, orta ve sert temas darbe; kalabalıkta en güçlüler kalır."""
    secilen: list[dict] = []
    for t in sorted((t for t in temaslar(p, k) if t["ses"]), key=lambda t: -t["hiz"]):
        tik = t["guc"] == "yumusak"
        ayni = [s for s in secilen if s["klip"] == t["klip"] and (s["guc"] == "yumusak") == tik]
        sinir, aralik = (EN_COK_TIK, TIK_ARALIK) if tik else (EN_COK_DARBE, DARBE_ARALIK)
        if len(ayni) >= sinir or any(abs(s["t"] - t["t"]) < aralik for s in ayni):
            continue
        if t["guc"] == "sert" and sum(s["guc"] == "sert" for s in ayni) >= EN_COK_SERT:
            t = {**t, "guc": "orta"}  # en güçlü iki darbe sert kalır, gerisi orta
        secilen.append(t)
    return [{"t": t["t"], "tur": "tik" if t["guc"] == "yumusak" else "vurgu", "guc": t["guc"], "sure": 0.2,
             "not": f"fizik teması {t['cift']} {t['hiz']:g} m/s ({t['klip']})"} for t in sorted(secilen, key=lambda t: t["t"])]


def katalog_metni() -> str:
    """ai-edit isteği için preset ve ışık kataloğu."""
    satir = ["### Fizik sahneleri (`tur: \"sahne\"`, `sahne.kind: \"fizik\"`)",
             'Klip: `{"tur": "sahne", "iz": "V2", "bas": 12.0, "sure": 4, "sahne": {"kind": "fizik", "layout": "full", '
             '"preset": "<ad>", "param": {...}, "isik": {"preset": "<ışık>"}, "olcum": true}}`. Simülasyon gerçek fiziktir '
             "(Rapier, yerçekimi 9,81 m/s²); temas sesi kendiliğinden gelir, ona ses olayı yazma. `param.etiket` kısa başlık "
             "(formül ya da kavram), `olcum: true` canlı değeri (hız, yükseklik) köşede gösterir. Tam ekrandır; konuşmacının "
             "üstüne gelir, sahne bitince konuşmacı döner."]
    for ad, t in presetler().items():
        pr = ", ".join(f"`{a}` ({v['min']}-{v['max']}{' ' + v['birim'] if v.get('birim') else ''}, vars {v['vars']})" if v["tip"] == "sayi"
                       else f"`{a}` ({'/'.join(v['secenek'])})" if v["tip"] == "secim" else f"`{a}` (metin)" for a, v in t["param"].items())
        satir.append(f"- `{ad}` — {t['title']}. Ne zaman: {t['ne_zaman']} Önerilen süre {t['sure']} sn. Parametre: {pr}.")
    satir.append("Işık presetleri (`sahne.isik.preset`): " + "; ".join(f"`{a}` ({v['ne_zaman']})" for a, v in isiklar().items()))
    return "\n".join(satir)
