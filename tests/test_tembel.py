"""Tembel modül vekili (ADR 0050): ilk erişimde yükler, yazma ve silme gerçek modüle gider."""

import sys

from vedit.tembel import Tembel


def test_ilk_erisimde_yukler_ve_yonlendirir():
    sys.modules.pop("colorsys", None)
    m = Tembel("colorsys")
    assert "colorsys" not in sys.modules
    assert m.rgb_to_hsv(1, 0, 0)[0] == 0
    assert "colorsys" in sys.modules
    assert "yüklü" in repr(m)


def test_yazma_ve_silme_gercek_modulde(monkeypatch):
    import colorsys
    m = Tembel("colorsys")
    monkeypatch.setattr(m, "ONE_THIRD", 0.5)
    assert colorsys.ONE_THIRD == 0.5
    m.yeni_alan = 1
    assert colorsys.yeni_alan == 1
    del m.yeni_alan
    assert not hasattr(colorsys, "yeni_alan")
    assert "rgb_to_hsv" in dir(m)
