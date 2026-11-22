"""Stil kartı regresyonu (ADR 0043): her stilin kartı var, taşma ve kontrast temiz; bir kart canlı yeniden çizilir."""
import json

import pytest

from vedit import stil_kart, stil_katalog


@pytest.mark.parametrize("kimlik", [e["id"] for e in stil_katalog.stiller()])
def test_kart_var_ve_temiz(kimlik):
    f = stil_kart.olcum_yolu(kimlik)
    assert stil_kart.kart_yolu(kimlik).is_file() and f.is_file(), "vedit stil-katalog kart"
    o = json.loads(f.read_text(encoding="utf-8"))
    assert o["tasma"] == [] and o["kontrast"] == [], o


def test_kart_canli_cizilir_ve_tasmaz(tmp_path, monkeypatch):
    sync = pytest.importorskip("playwright.sync_api")
    monkeypatch.setattr(stil_kart, "kart_yolu", lambda k: tmp_path / k / "kart.jpg")
    with sync.sync_playwright() as p:
        o = stil_kart.uret("piksel-8bit", p)
    assert (tmp_path / "piksel-8bit" / "kart.jpg").stat().st_size > 20_000
    assert o["tasma"] == [] and o["kontrast"] == [] and o["gecis"] == "gecis-piksel-cozunme-yatay"
