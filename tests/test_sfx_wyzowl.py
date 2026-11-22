"""fetch wyzowl: ağsız; sahte zip ile açma, yol kaçışı reddi, kategori eşlemesi."""
import io
import json
import zipfile

import pytest

from vedit import sfx


def _zip(extra: dict | None = None) -> bytes:
    meta = {"sounds": [{"file": "sounds/whooshes/whoosh-fast-soft.wav", "tags": ["Whoosh"], "sync": {"at": 0.09}}]}
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("kit-main/sounds.json", json.dumps(meta))
        for n in ("whooshes/whoosh-fast-soft", "swishes-and-zips/whip-pan", "reverse-whooshes/reverse-whoosh-short",
                  "mechanical/mechanical-shutter-light", "everyday-props/props-page-turn", "interface/ui-tap-soft",
                  "logo-stings/sting-01"):
            z.writestr(f"kit-main/sounds/{n}.wav", b"RIFF")
        z.writestr("kit-main/README.md", "x")
        for n, d in (extra or {}).items():
            z.writestr(n, d)
    return buf.getvalue()


def test_acma_ve_kategori(tmp_path):
    out = sfx._wyzowl_ac(_zip(), tmp_path / "w")
    assert "sting-01.wav" not in out  # eşlemesi olmayan klasör alınmaz
    assert not (tmp_path / "w" / "README.md").exists()
    f = json.loads((tmp_path / "w" / "source.json").read_text(encoding="utf-8"))
    assert f["license"] == "CC0"
    cats = {k: v["category"] for k, v in f["files"].items()}
    assert cats == {"whoosh-fast-soft.wav": "whoosh", "whip-pan.wav": "whip", "reverse-whoosh-short.wav": "riser",
                    "mechanical-shutter-light.wav": "camera_shutter", "props-page-turn.wav": "page_turn",
                    "ui-tap-soft.wav": "tap"}
    assert f["files"]["whoosh-fast-soft.wav"]["peak_offset_s"] == 0.09


def test_yol_kacisi_reddedilir(tmp_path):
    with pytest.raises(ValueError):
        sfx._wyzowl_ac(_zip({"kit-main/sounds/../../evil.wav": b"x"}), tmp_path / "w")
    assert not (tmp_path / "evil.wav").exists()
