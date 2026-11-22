"""HyperFrames'e taşınan native bileşen sahneleri (library/motion/hf/<aile>-<ad>/sahne.html) sözleşmeye uyar.

WHY: bkz. wiki/decisions/0051-uctan-uca-hyperframes.md ve library/motion/hf/SOZLESME.md "Native bileşen taşıma".
Görüntünün aynılığını scripts/hf_native_karsilastir.py ölçer; bu test yapıyı ve deterministikliği denetler.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

KOK = Path(__file__).resolve().parents[1]
HF = KOK / "library" / "motion" / "hf"
SEMA = json.loads((KOK / "library" / "motion" / "native" / "sema.json").read_text(encoding="utf-8"))["bilesenler"]
SAHNELER = sorted(HF.glob("*/sahne.html"))
YASAK = ["Math.random", "Date.now", "performance.now", "requestAnimationFrame", "setTimeout", "setInterval",
         "@keyframes", "animation:", "transition:", 'src="http', 'href="http', "url(http", "fetch(", "import("]


def test_en_az_bir_sahne():
    assert SAHNELER, "pilot sahneler (ikon-begeni, kart-cip) eksik"


@pytest.mark.parametrize("yol", SAHNELER, ids=[p.parent.name for p in SAHNELER])
def test_sahne_sozlesmesi(yol: Path):
    s = yol.read_text(encoding="utf-8")
    ad = yol.parent.name.replace("-", "/", 1)
    assert ad in SEMA, f"{ad}: library/motion/native/sema.json'da yok (klasör adı <aile>-<ad>)"
    assert s.lstrip().startswith("<!--") or s.lstrip().startswith("<template>")
    assert "<template>" in s and "</template>" in s
    assert 'id="__KOK__" data-composition-id="__KOK__"' in s
    assert 'data-width="__W__" data-height="__H__"' in s
    assert 'H.sahne("__KOK__"' in s
    assert "data-var-text" not in s, "metni betik yazar (harf dönüşümü)"
    kod = re.sub(r"<!--.*?-->", "", s, flags=re.S)  # yorumdaki lisans adresi serbest
    for y in YASAK:
        assert y not in kod, f"{ad}: yasak ifade {y}"
    # Sabit kimlik yalnız kök: aynı sahne bir karede iki kez bağlanabilir.
    kimlikler = set(re.findall(r'\bid="([^"]+)"', s))
    assert kimlikler <= {"__KOK__"}, f"{ad}: sabit kimlik {kimlikler - {'__KOK__'}}; b.kimlik() kullan"
    assert not re.search(r'class="[^"]*kz-', s), f"{ad}: kz- öneki ana kompozisyonundur"
    m = re.search(r"data-composition-variables='([^']*)'", s)
    degisken = {d["id"]: d for d in json.loads(m[1])} if m else {}
    ozellik = SEMA[ad]["sema"].get("properties", {})
    assert set(degisken) == set(ozellik), f"{ad}: değişkenler şemayla aynı olmalı"
    for k, v in ozellik.items():
        if "default" in v:
            assert degisken[k].get("default") == v["default"], f"{ad}.{k}: varsayılan şemayla farklı"
