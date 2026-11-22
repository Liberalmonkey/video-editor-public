"""Sunucu ortak yardımcıları: ad doğrulama, kök içi yol, yükleme ve geri alınabilir silme."""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import shutil
import uuid
from pathlib import Path

from fastapi import HTTPException, Request

from .. import hizli, paths

GERI_DONUSUM_SINIRI = 1 << 30
GUVENLI_AD = re.compile(r"[^\w.\- ()]+", re.UNICODE)


def send2trash(yol: str) -> None:
    """Geri dönüşüm kutusu; send2trash modülü ilk silmede yüklenir. WHY: açılışta yüklenmesin (ADR 0050)."""
    from send2trash import send2trash as _cop
    _cop(yol)


def proje(studyo: str, ad: str) -> hizli.Proje:
    """Tek klasör adı olmalı; `..` ve ayraç reddedilir."""
    for parca in (studyo, ad):
        if not parca or parca.startswith((".", "_")) or "/" in parca or "\\" in parca or ":" in parca:
            raise HTTPException(400, "Geçersiz proje adı")
    return hizli.Proje(studyo, ad)


def kok_ici(taban: Path, ic: str, *, dosya: bool = True) -> Path:
    t = taban.resolve()
    hedef = (t / ic).resolve()
    if not hedef.is_relative_to(t) or hedef == t or (dosya and not hedef.is_file()):
        raise HTTPException(404, "Dosya yok")
    return hedef


def dosya_adi(ad: str, izinli: set[str]) -> str:
    """Yol parçalarını atar, tehlikeli karakterleri temizler, uzantıyı beyaz listeyle denetler."""
    temiz = GUVENLI_AD.sub("-", Path(ad.replace("\\", "/")).name).strip(" .-")
    if not temiz or Path(temiz).suffix.lower() not in izinli:
        raise HTTPException(415, f"Bu dosya türü yüklenemez: {Path(ad).suffix or ad}")
    return temiz


def bos_ad(klasor: Path, ad: str) -> Path:
    """Var olan dosyanın üzerine yazmaz: ad.mp4, ad-2.mp4 …"""
    f, n, yol = klasor / ad, 2, Path(ad)
    while f.exists():
        f, n = klasor / f"{yol.stem}-{n}{yol.suffix}", n + 1
    return f


async def akisi_yaz(request: Request, hedef: Path) -> Path:
    """İstek gövdesini geçici dosyaya akıtır, bitince taşır. Kopan yükleme yarım dosya bırakmaz.
    Yazılan dosyayı döner: ad doluysa `ad-2` gibi boş bir ada yazılır."""
    hedef.parent.mkdir(parents=True, exist_ok=True)
    gecici = hedef.with_name(f".{uuid.uuid4().hex[:10]}.yukleniyor")
    boyut = 0
    try:
        with gecici.open("xb") as f:
            async for parca in request.stream():
                f.write(parca)
                boyut += len(parca)
        if not boyut:
            raise HTTPException(400, "Boş dosya")
        yazilan = bos_ad(hedef.parent, hedef.name)
        os.replace(gecici, yazilan)
    finally:
        gecici.unlink(missing_ok=True)
    return yazilan


def _boyut(y: Path) -> int:
    return y.stat().st_size if y.is_file() else sum(f.stat().st_size for f in y.rglob("*") if f.is_file())


def sil(y: Path) -> str:
    """Geri dönüşüm kutusu; sığmayacak kadar büyükse Projeler/.cop altına taşır.

    WHY: Windows kutuya sığmayan öğeyi FOFX_RECYCLEONDELETE ile sessizce kalıcı silebilir. Veri kaybı olmasın.
    """
    if _boyut(y) <= GERI_DONUSUM_SINIRI:
        send2trash(str(y))
        return "Geri dönüşüm kutusuna taşındı"
    hedef = paths.ROOT / "Projeler" / ".cop" / dt.datetime.now().strftime("%Y%m%d-%H%M%S") / y.name
    hedef.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(y), hedef)
    return f"Çok büyük olduğu için taşındı: {paths.rel(hedef)}"


def json_yaz(yol: Path, veri) -> None:
    gecici = yol.with_name(f".{yol.name}.{uuid.uuid4().hex[:8]}.tmp")
    gecici.write_text(json.dumps(veri, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(gecici, yol)
