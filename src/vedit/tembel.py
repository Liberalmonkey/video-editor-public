"""Ağır modülü ilk kullanımda yükleyen vekil.

WHY: bkz. wiki/decisions/0050-hyperframes-birincil-motor.md (Stüdyo açılışı). cv2, numpy, requests ve soundfile
modül düzeyinde yüklenince Stüdyo sunucusu her açılışta bunları bekliyordu; çoğu oturumda hiç kullanılmıyorlar.
"""

from __future__ import annotations

import importlib
from types import ModuleType


class Tembel:
    """`np = Tembel("numpy")`: ilk öznitelik erişiminde modülü içe aktarır, sonra doğrudan ona yönlendirir."""

    def __init__(self, ad: str) -> None:
        self._ad = ad
        self._modul: ModuleType | None = None

    def _yukle(self) -> ModuleType:
        if self._modul is None:
            object.__setattr__(self, "_modul", importlib.import_module(self._ad))
        return self._modul

    def __getattr__(self, oz: str):
        return getattr(self._yukle(), oz)

    def __setattr__(self, oz: str, deger) -> None:
        # WHY: monkeypatch.setattr(np, "x", ...) gerçek modüle yazılsın; vekilin kendi alanları ayrı
        if oz in ("_ad", "_modul"):
            object.__setattr__(self, oz, deger)
        else:
            setattr(self._yukle(), oz, deger)

    def __delattr__(self, oz: str) -> None:
        delattr(self._yukle(), oz)

    def __dir__(self):
        return dir(self._yukle())

    def __repr__(self) -> str:
        return f"<tembel {self._ad} {'yüklü' if self._modul else 'bekliyor'}>"
