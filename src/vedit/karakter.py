"""Kodla çizilen konuşan karakter (`tur: "sahne"`, `sahne.kind: "karakter"`): denetim ve veri bağlama.

WHY: bkz. wiki/decisions/0039-fizik-ritim-galeri.md. Karakter tanımı `library/karakter/<ad>/karakter.json`; ağız
kare başına `viseme`den, baş ve kol vurgusu `ritim` vurgu anlarından gelir. İkisi klip aralığına kesilip tek JSON olarak
klibin kaynağına bağlanır (fizik sahnesi kalıbı). Ses değişirse özet değişir, veri yeniden yazılır.
"""
from __future__ import annotations

import hashlib
import json
import zlib
from pathlib import Path

from . import paths

KOK = paths.LIBRARY / "karakter"


def _stil_klasoru(p) -> Path | None:
    if p is None:
        return None
    from . import stil

    try:
        k = stil.secili(p)
        if k is not None:
            return k
    except SystemExit:
        pass
    try:
        ad = stil.secili_adi(p)
        return stil.klasor(p.studyo, ad) if ad else None
    except Exception:
        return None


def karakterler(stil_k: Path | None = None) -> dict[str, dict]:
    cikti = {}
    if KOK.is_dir():
        for f in sorted(KOK.glob("*/karakter.json")):
            try:
                cikti[f.parent.name] = json.loads(f.read_text(encoding="utf-8"))
            except ValueError:
                continue
    if stil_k is not None:
        ozel = Path(stil_k) / "varliklar" / "karakter"
        if ozel.is_dir():
            for f in sorted(ozel.glob("*.json")):
                try:
                    veri = json.loads(f.read_text(encoding="utf-8"))
                    if isinstance(veri, dict):
                        cikti[f.stem] = veri
                except ValueError:
                    continue
            for f in sorted(ozel.glob("*/*.json")):
                if f.name == "orijinal.json" and (f.parent / "karakter.json").exists():
                    continue
                try:
                    veri = json.loads(f.read_text(encoding="utf-8"))
                    if isinstance(veri, dict):
                        cikti[f.parent.name] = veri
                except ValueError:
                    continue
    return cikti


def hatalar(c, stil_k: Path | None = None) -> list[str]:
    s = c.sahne or {}
    if c.tur != "sahne" or s.get("kind") != "karakter":
        return []
    ad = s.get("karakter")
    tanimlar = karakterler(stil_k)
    if ad not in tanimlar:
        return [f"{c.id}: bilinmeyen karakter '{ad}'. Karakterler: {', '.join(tanimlar) or 'yok'}"]
    olcek = s.get("olcek", 0.78)
    if not isinstance(olcek, (int, float)) or not 0.2 <= olcek <= 1.2:
        return [f"{c.id}: karakter ölçeği {olcek!r}; 0,2-1,2 arası olmalı"]
    return []


def bagla(p, k, stil_k: Path | None = None) -> bool:
    """Karakter sahnelerine klip aralığının viseme ve vurgu verisini bağlar. Kurgu değiştiyse True."""
    from . import ritim, viseme
    from .schemas import KurguKaynak

    etkin_stil = stil_k or _stil_klasoru(p)
    hedef = [c for c in k.klipler if c.tur == "sahne" and (c.sahne or {}).get("kind") == "karakter" and not hatalar(c, stil_k=etkin_stil)]
    if not hedef:
        return False
    fps = k.sekans.fps
    tum = viseme.sekans(p, k)
    try:
        vurgu = [o["t"] for o in ritim.sekans(p, k)["vurgular"] if o["rol"] == "konusma"]
    except Exception:  # WHY: vurgu yalnız jest içindir; ölçülemezse karakter yine konuşur
        vurgu = []
    tanimlar = karakterler(etkin_stil)
    degisti = False
    for c in hedef:
        ad = c.sahne["karakter"]
        a, b = int(round(c.bas * fps)), int(round((c.bas + c.sure) * fps))
        veri = {"karakter": tanimlar[ad], "fps": fps, "viseme": tum[a:b].ljust(b - a, "K"),
                "vurgular": [round((t - c.bas) * fps) for t in vurgu if c.bas <= t < c.bas + c.sure],
                "tohum": zlib.crc32(f"{ad}|{c.id}".encode()) & 0x7FFFFFFF}
        metin = json.dumps(veri, ensure_ascii=False, sort_keys=True)
        oz = hashlib.sha1(metin.encode()).hexdigest()[:12]
        f = p.work / "public" / "karakter" / f"{ad}-{oz}.json"
        if not f.exists():
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(metin, encoding="utf-8")
        kid = "C_" + oz
        if kid not in k.kaynaklar:
            k.kaynaklar[kid] = KurguKaynak(yol=f"public:karakter/{f.name}", sure=c.sure, ses=False)
        if c.kaynak != kid:
            c.kaynak, degisti = kid, True
    return degisti


def katalog_metni(stil_k: Path | None = None) -> str:
    kar = karakterler(stil_k)
    if not kar:
        return ""
    return ("### Konuşan karakter (`tur: \"sahne\"`, `sahne.kind: \"karakter\"`)\n"
            'Klip: `{"tur": "sahne", "iz": "V2", "bas": 3.0, "sure": 6, "sahne": {"kind": "karakter", "layout": "full", '
            '"karakter": "<ad>", "bg": "saydam", "olcek": 0.6}}`. Ağız konuşma sesiyle kare kare açılır, vurgu anlarında '
            "baş sallar ve el kaldırır; elle zamanlama yazma. `bg: \"saydam\"` üst izde konuşmacının ya da sahnenin üstüne "
            "biner (`donus.x`/`donus.y` ile köşeye taşı), yoksa karakterin kendi zemin rengi tam ekran olur. Ancak "
            "seslendirme varken kullan.\n" + "\n".join(f"- `{a}` — {t.get('title', a)}. Ne zaman: {t.get('ne_zaman', '')}" for a, t in kar.items()))
