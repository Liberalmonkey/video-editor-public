"""HDR (HLG/PQ) kaynak BT.709 SDR'ye ton eşlenir; tam sinyal beyazı sınırlı aralık beyazına (Y≈235) düşer (ADR 0040)."""
import subprocess

import numpy as np
import pytest

from vedit import ff, kurgu, paths
from vedit.hizli import Proje


def hlg_klip(hedef, renk="white"):
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", f"color=c={renk}:s=320x180:d=1:r=30",
                    "-vf", "format=yuv420p10le", "-c:v", "libx265", "-x265-params", "log-level=error:colorprim=bt2020:transfer=arib-std-b67:colormatrix=bt2020nc",
                    "-color_primaries", "bt2020", "-color_trc", "arib-std-b67", "-colorspace", "bt2020nc", "-color_range", "tv",
                    "-tag:v", "hvc1", str(hedef)], check=True)
    return hedef


def ortalama_y(f):
    ham = subprocess.run(["ffmpeg", "-v", "error", "-i", str(f), "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "gray", "-"],
                         capture_output=True, check=True).stdout
    return float(np.frombuffer(ham, np.uint8).mean())


def test_hdr_tespit_ve_cevirme(tmp_path):
    src = hlg_klip(tmp_path / "hdr.mp4")
    assert ff.hdr_mi(ff.probe(src))
    out = ff.sdr_cevir(src, tmp_path / "sdr.mp4")
    v = ff.probe(out)["video"]
    assert not ff.hdr_mi(ff.probe(out))
    assert (v.get("color_transfer"), v.get("color_primaries"), v.get("color_space")) == ("bt709", "bt709", "bt709")
    # HLG %100 beyaz SDR beyazına (sınırlı aralık 235) yakın düşmeli; eski zincir 151'de bırakıyordu.
    assert ortalama_y(out) > 215


def test_sdr_girdi_dokunulmaz(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "INPUTS", tmp_path / "in")
    monkeypatch.setattr(paths, "OUTPUTS", tmp_path / "out")
    p = Proje("ugc", "x")
    p.girdi.mkdir(parents=True)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "color=c=gray:s=320x180:d=1:r=30", "-pix_fmt", "yuv420p",
                    str(p.girdi / "a.mp4")], check=True)
    hlg_klip(p.girdi / "b.mov")
    kurgu._public_bagla(p, "A", "inputs:a.mp4")
    kurgu._public_bagla(p, "B", "inputs:b.mov")
    a, b = p.work / "public" / "_k" / "A.mp4", p.work / "public" / "_k" / "B.mov"
    assert a.samefile(p.girdi / "a.mp4")            # SDR: yalnız bağlantı
    assert not b.samefile(p.girdi / "b.mov")         # HDR: SDR kopya, uzantı aynı
    assert not ff.hdr_mi(ff.probe(b))
