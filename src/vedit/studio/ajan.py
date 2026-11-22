"""AI paneli: Claude Code, Antigravity, Codex ya da OpenCode'u arayüzden başlatır, modeli kullanıcı seçer, çıktı canlı akar.

WHY: bkz. wiki/decisions/0026-arayuzde-ajan.md. Ajan yine terminal CLI'ı olarak (`claude -p`, `agy -p`, `codex exec`,
`opencode run`) proje kökünde ayrı süreçte çalışır; arayüz yalnız başlatır, izler, durdurur. Motor tablosu
`vedit/motorlar.py`'dedir; komut argüman listesiyle kurulur, izin atlatma bayrağı yoktur.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .. import motorlar
from ..motorlar import OTURUM, cevirici  # noqa: F401  (cevirici: ajan_cagri ve testler buradan da alır)
from . import isler, ortak

router = APIRouter()
AD = {k: m.ad for k, m in motorlar.MOTORLAR.items()}


def _durum() -> dict:
    """Kurulum, sürüm, model listesi. Sunucu ömrü boyunca bir kez; `yenile` önbelleği boşaltır."""
    return motorlar.durum()


@router.get("/api/ajan/durum")
def durum(yenile: bool = False):
    if yenile:
        motorlar.durum.cache_clear()
    return _durum()


class AjanIstek(BaseModel):
    motor: str
    model: str
    mod: str = "duzenle"
    istem: str
    studyo: str | None = None
    ad: str | None = None
    oturum: str | None = None


def argumanlar(g: AjanIstek, modeller: list[str]) -> list[str]:
    """Beyaz liste. Bilinmeyen motor, model, mod ya da biçimsiz oturum burada durur."""
    if g.motor not in motorlar.MOTORLAR:
        raise HTTPException(400, "Bilinmeyen motor")
    if g.mod not in motorlar.MODLAR:
        raise HTTPException(400, "Mod duzenle ya da plan")
    if g.model not in modeller:
        raise HTTPException(400, f"Bu motorda olmayan model: {g.model}")
    if g.oturum and not OTURUM.fullmatch(g.oturum):
        raise HTTPException(400, "Geçersiz oturum")
    istem = g.istem.strip()
    if not istem or len(istem) > 20000:
        raise HTTPException(400, "İstem boş ya da çok uzun")
    if g.studyo and g.ad:
        p = ortak.proje(g.studyo, g.ad)
        istem = f"Proje: Projeler/inputs/{p.studyo}/{p.ad} (work/edit/kurgu.json varsa tek kaynak odur).\n\n{istem}"
    istem = " " + istem if istem.startswith("-") else istem  # WHY: '-' ile başlayan istem bayrak sanılmasın
    return motorlar.MOTORLAR[g.motor].arguman(istem, g.model, g.mod, g.oturum)


@router.post("/api/ajan")
def baslat(g: AjanIstek):
    d = _durum().get(g.motor)
    if not d or not d["kurulu"]:
        raise HTTPException(400, f"{AD.get(g.motor, g.motor)} kurulu değil")
    args = argumanlar(g, [m["id"] for m in d["modeller"]])
    bas = motorlar.bas(g.motor)
    if not bas:
        raise HTTPException(400, f"{AD[g.motor]} kurulu değil")
    ilk = g.istem.strip().splitlines()[0][:60]
    ad = next((m["ad"] for m in d["modeller"] if m["id"] == g.model), g.model)
    is_ = isler.ajan_kuyrugu().ekle("ajan", f"{AD[g.motor]} · {ad} · {ilk}", [*bas[1:], *args], exe=bas[0],
                                     motor=g.motor, model=g.model, oturum=g.oturum, cevir=cevirici())
    return is_.ozet()
