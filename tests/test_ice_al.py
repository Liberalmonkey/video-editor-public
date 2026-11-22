"""Dış varlık içe aktarma (ADR 0046): lisans zorunlu, alfa yöntemi tespiti, normalize dosya, manifest, atıf."""

import json
import shutil
import subprocess

import numpy as np
import pytest

from vedit import motion_ice, paths
from vedit.schemas import Kurgu

pytestmark = pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg yok")


def _ff(*a):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *a], check=True)


@pytest.fixture
def lib(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "ROOT", tmp_path)
    monkeypatch.setattr(paths, "LIBRARY", tmp_path / "library")
    monkeypatch.setattr(paths, "MOTION_DIR", tmp_path / "library" / "motion")
    (tmp_path / "library" / "motion").mkdir(parents=True)
    (tmp_path / "library" / "motion" / "manifest.json").write_text(json.dumps({"entries": [{"id": "eski", "file": "x"}]}), encoding="utf-8")
    return tmp_path


def _yesil(f):
    # Yeşil perde üstünde beyaz daire.
    _ff("-f", "lavfi", "-i", "color=c=0x00FF00:s=320x240:d=1:r=30", "-vf", "drawbox=x=120:y=80:w=80:h=80:color=white:t=fill",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", str(f))


def _siyah(f):
    _ff("-f", "lavfi", "-i", "color=c=black:s=320x240:d=1:r=30", "-vf", "drawbox=x=100:y=60:w=120:h=120:color=orange@0.8:t=fill",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", str(f))


def _alfa_merkez(f) -> tuple[int, int]:
    """(kenar alfa, merkez alfa) orta karede."""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-c:v", "libvpx-vp9", "-i", str(f), "-vf", "select=eq(n\\,10),alphaextract,scale=32:24",
                          "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True, check=True).stdout
    a = np.frombuffer(raw, np.uint8).reshape(24, 32)
    return int(a[1, 1]), int(a[12, 16])


def test_lisanssiz_reddedilir_ve_dosya_yazilmaz(lib, tmp_path):
    with pytest.raises(motion_ice.LisansHatasi):
        motion_ice.lisans_kur("bilinmeyen-site", url=None, lisans=None)
    with pytest.raises(motion_ice.LisansHatasi):
        motion_ice.lisans_kur("x", url="ftp://x", lisans="MIT")
    with pytest.raises(motion_ice.LisansHatasi, match="atıf"):
        motion_ice.lisans_kur("uppbeat", url=None, lisans=None)  # Uppbeat Free atıf ister
    assert not (paths.MOTION_DIR / "dis").exists()


def test_yesil_perde_alfaya_doner(lib, tmp_path):
    f = tmp_path / "g.mp4"
    _yesil(f)
    assert motion_ice.yontem_bul(f) == "yesil"
    e = motion_ice.ice_al(f, motion_ice.lisans_kur("pixabay", url="https://pixabay.com/videos/x-1/", lisans=None), tur="overlay")
    assert e["alfa_yontemi"] == "yesil" and e["license"] == "Pixabay Content License" and e["file"].endswith(".webm")
    kenar, merkez = _alfa_merkez(paths.ROOT / e["file"])
    assert kenar < 30 and merkez > 220, "yeşil saydam, nesne opak"
    assert (paths.ROOT / e["file"]).parent.joinpath("poster.jpg").exists()


def test_siyah_zemin_screen_karisimi(lib, tmp_path):
    f = tmp_path / "isik.mp4"
    _siyah(f)
    assert motion_ice.yontem_bul(f) == "siyah"
    e = motion_ice.ice_al(f, motion_ice.lisans_kur("mixkit", url="https://mixkit.co/free-stock-video/x-1/", lisans=None), tur="light-leak")
    assert e["karisim"] == "screen" and not e["alpha"]


def test_gif_lottie_svg(lib, tmp_path):
    gif = tmp_path / "a.gif"
    _ff("-f", "lavfi", "-i", "color=c=red@0.0:s=64x64:d=0.5:r=10,format=rgba", "-vf", "drawbox=x=16:y=16:w=32:h=32:color=red:t=fill", str(gif))
    lot = tmp_path / "k.json"
    lot.write_text(json.dumps({"v": "5.7", "fr": 30, "ip": 0, "op": 45, "w": 100, "h": 100, "layers": []}), encoding="utf-8")
    svg = tmp_path / "o.svg"
    svg.write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><path d="M0 0h10"/></svg>', encoding="utf-8")
    li = motion_ice.lisans_kur("github", url="https://github.com/x/y", lisans="MIT")
    assert motion_ice.ice_al(gif, li)["alfa_yontemi"] == "gif"
    e = motion_ice.ice_al(lot, li, tur="icon")
    assert e["alfa_yontemi"] == "lottie" and e["duration_s"] == 1.5
    assert motion_ice.ice_al(svg, li)["alfa_yontemi"] == "svg"


def test_manifest_yenile_ve_atif(lib, tmp_path):
    f = tmp_path / "g.mp4"
    _yesil(f)
    li = motion_ice.lisans_kur("uppbeat", url="https://uppbeat.io/x", lisans=None, atif_metni="Motion: Uppbeat (uppbeat.io/x)")
    e = motion_ice.ice_al(f, li)
    motion_ice.manifest_yenile()
    d = json.loads((paths.MOTION_DIR / "manifest.json").read_text(encoding="utf-8"))
    assert [x["id"] for x in d["entries"]] == ["eski", e["id"]], "kullanıcının eski kaydına dokunulmaz"
    assert "yalniz-kendi-kanalin" in d["entries"][1]["kisitlar"]
    k = Kurgu.model_validate({"kaynaklar": {"a": {"yol": "library:" + e["file"].removeprefix("library/")}}, "izler": [{"id": "V1", "tur": "video"}]})
    assert motion_ice.atif_satirlari(k) == ["Motion: Uppbeat (uppbeat.io/x)"]
    shutil.rmtree((paths.ROOT / e["file"]).parent)
    motion_ice.manifest_yenile()
    assert len(json.loads((paths.MOTION_DIR / "manifest.json").read_text(encoding="utf-8"))["entries"]) == 1


def test_yayin_md_atif_bolumu(lib, tmp_path, monkeypatch):
    from vedit import hizli, kurgu
    monkeypatch.setattr(paths, "INPUTS", tmp_path / "in")
    monkeypatch.setattr(paths, "OUTPUTS", tmp_path / "out")
    f = tmp_path / "g.mp4"
    _yesil(f)
    e = motion_ice.ice_al(f, motion_ice.lisans_kur("uppbeat", url="https://uppbeat.io/x", lisans=None, atif_metni="Uppbeat: x"))
    p = hizli.Proje("instagram", "a")
    p.cikti.mkdir(parents=True)
    (p.cikti / "yayin.md").write_text("# Açıklama\nMetin.\n", encoding="utf-8")
    kurgu.yaz(p.work, Kurgu.model_validate({"kaynaklar": {"m": {"yol": "library:" + e["file"].removeprefix("library/")}},
                                            "izler": [{"id": "V1", "tur": "video"}]}))
    assert hizli.atif_yaz(p) == ["Uppbeat: x"]
    hizli.atif_yaz(p)  # ikinci kez: bölüm tekrarlanmaz
    metin = (p.cikti / "yayin.md").read_text(encoding="utf-8")
    assert metin.count(hizli.ATIF_BASLIK) == 1 and "Metin." in metin and "- Uppbeat: x" in metin
