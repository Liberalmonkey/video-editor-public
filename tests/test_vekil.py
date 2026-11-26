"""Proxy (vekil) ve master conform (ADR 0060): ağır kaynak taslakta proxy'ye, finalde orijinale bağlanır; sızıntı kapıda durur."""
import json
import subprocess

import pytest

from vedit import ff, kurgu, paths, vekil
from vedit.hizli import Proje


def klip_4k(hedef, *, sure=1.0, fps=30, vfr=False):
    """3840x2160 HEVC 10-bit; vfr ise ilk saniyeden sonra her 4 kareden biri kalır, zaman damgaları korunur
    (telefon VFR'si gibi ortalama hız nominal hızdan ayrışır)."""
    vf = "format=yuv420p10le" + (r",select='not(mod(n\,4))+lt(n\,30)'" if vfr else "")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", f"testsrc2=s=3840x2160:d={sure}:r={fps}",
                    "-vf", vf, *(["-fps_mode", "vfr"] if vfr else []),
                    "-c:v", "libx265", "-preset", "ultrafast", "-x265-params", "log-level=error", "-tag:v", "hvc1", str(hedef)],
                   check=True)
    return hedef


def test_neden_olcutleri():
    hafif = {"video": {"codec": "h264", "width": 1920, "height": 1080, "pix_fmt": "yuv420p", "bit_rate": 9_000_000}}
    assert vekil.neden(hafif) == []
    assert "3840x2160" in vekil.neden({"video": {**hafif["video"], "width": 3840, "height": 2160}})
    assert "hevc" in vekil.neden({"video": {**hafif["video"], "codec": "hevc"}})
    assert "yuv420p10le" in vekil.neden({"video": {**hafif["video"], "pix_fmt": "yuv420p10le"}})
    assert "VFR" in vekil.neden({"video": {**hafif["video"], "vfr": True}})
    assert "80 Mbps" in vekil.neden({"video": {**hafif["video"], "bit_rate": 80_000_000}})
    # Alfalı motion kaynağı asla proxy'lenmez (alfa kaybolur, siyah kutu olur)
    assert vekil.neden({"video": {**hafif["video"], "width": 3840, "height": 2160, "alfa": True}}) == []


def test_taslak_proxy_uretimi(tmp_path):
    src = klip_4k(tmp_path / "a.mp4")
    assert vekil.gerekli(ff.probe(src))
    px = vekil.uret(tmp_path / "work", src, "taslak")
    v = ff.probe(px)["video"]
    assert (min(v["width"], v["height"]), v["codec"], v["pix_fmt"]) == (1080, "h264", "yuv420p")
    assert vekil.esles(src, px)
    kayit = vekil.kayitlar(tmp_path / "work")["a.mp4"]["taslak"]
    assert kayit["dosya"] == px.name and "3840x2160" in kayit["neden"]
    assert vekil.uret(tmp_path / "work", src, "taslak") == px  # ikinci çağrı yeniden üretmez


def test_vfr_algilama(tmp_path):
    src = klip_4k(tmp_path / "v.mp4", sure=2.0, vfr=True)
    assert ff.probe(src)["video"]["vfr"]
    assert not ff.probe(klip_4k(tmp_path / "c.mp4"))["video"]["vfr"]


@pytest.fixture
def proje(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "INPUTS", tmp_path / "in")
    monkeypatch.setattr(paths, "OUTPUTS", tmp_path / "out")
    p = Proje("ugc", "x")
    p.girdi.mkdir(parents=True)
    klip_4k(p.girdi / "a.mp4")
    return p


def test_taslak_proxy_final_master(proje):
    p, kaynak = proje, proje.girdi / "a.mp4"
    bag = p.work / "public" / "_k" / "A.mp4"
    # Proxy hazır değilken taslak da orijinali bağlar
    assert kurgu._public_bagla(p, "A", "inputs:a.mp4", mod="taslak")[2] is False and bag.samefile(kaynak)
    px = vekil.uret(p.work, kaynak, "taslak")
    ad, hedef, proxy = kurgu._public_bagla(p, "A", "inputs:a.mp4", mod="taslak")
    assert proxy and bag.samefile(px) and ad == "A.mp4"
    # Final: orijinale döner, conform kapısı geçer
    ad, hedef, proxy = kurgu._public_bagla(p, "A", "inputs:a.mp4", mod="final")
    assert not proxy and bag.samefile(kaynak)
    assert vekil.conform_denetle(p.work / "public", {ad: kaynak}) == []
    kurgu._conform_yaz(p, "final", {ad: kaynak}, [])
    assert json.loads((p.work / "edit" / "conform.json").read_text(encoding="utf-8"))["master"] == 1


def test_conform_kapisi_proxy_sizintisinda_durur(proje):
    p, kaynak = proje, proje.girdi / "a.mp4"
    vekil.uret(p.work, kaynak, "taslak")
    ad, _, _ = kurgu._public_bagla(p, "A", "inputs:a.mp4", mod="taslak")  # bağlantı proxy'de kaldı
    assert vekil.conform_denetle(p.work / "public", {ad: kaynak})
    with pytest.raises(SystemExit, match="Master conform"):
        kurgu._conform_yaz(p, "master", {ad: kaynak}, [])
    with pytest.raises(SystemExit, match="proxy bağlı"):
        kurgu._conform_yaz(p, "final", {ad: kaynak}, ["A"])
    kurgu._conform_yaz(p, "taslak", {ad: kaynak}, ["A"])  # taslakta proxy beklenen durum
