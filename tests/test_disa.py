"""Kurgu dışa aktarımı: FCPXML ve xmeml iyi biçimli, zamanlar karede, yollar mutlak."""
import subprocess
import xml.etree.ElementTree as ET

from vedit import disa, paths
from vedit.hizli import Proje
from vedit.schemas import Kurgu


def test_fcpxml_ve_xmeml(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "INPUTS", tmp_path / "in")
    monkeypatch.setattr(paths, "OUTPUTS", tmp_path / "out")
    p = Proje("instagram", "x")
    p.girdi.mkdir(parents=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=black:s=64x64:r=30:d=4",
                    "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-t", "4", "-c:v", "libx264", "-preset", "ultrafast",
                    str(p.girdi / "v.mp4")], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-t", "2",
                    str(p.girdi / "s.wav")], check=True)
    k = Kurgu.model_validate({
        "sekans": {"w": 1080, "h": 1920, "fps": 30},
        "kaynaklar": {"V": {"yol": "inputs:v.mp4"}, "S": {"yol": "inputs:s.wav", "sure": 2}},  # V probe'dan
        "izler": [{"id": "V2", "tur": "video", "gizli": True}, {"id": "V1", "tur": "video"}, {"id": "A1", "tur": "ses", "gain_db": -2}],
        "klipler": [
            {"id": "v1", "iz": "V1", "tur": "video", "kaynak": "V", "bas": 1.0, "sure": 2.0, "giris": 0.5},
            {"id": "sh", "iz": "V2", "tur": "sahne", "bas": 0.0, "sure": 1.5, "sahne": {"kind": "kod"}},
            {"id": "a1", "iz": "A1", "tur": "ses", "kaynak": "S", "bas": 2.0, "sure": 1.0, "ses": {"gain_db": -4}},
        ],
        "isaretler": [{"t": 3.0, "ad": "vurgu"}],
    })
    f, x = disa.yaz(p, k, p.cikti)
    assert f.read_text(encoding="utf-8").splitlines()[1] == "<!DOCTYPE fcpxml>"
    assert x.read_text(encoding="utf-8").splitlines()[1] == "<!DOCTYPE xmeml>"

    r = ET.parse(f).getroot()
    assert {a.find("media-rep").get("src") for a in r.iter("asset")} == {(p.girdi / "v.mp4").as_uri(), (p.girdi / "s.wav").as_uri()}
    assert all(a.find("media-rep").get("src").startswith("file:///") for a in r.iter("asset"))
    c = {e.get("name"): e for e in r.iter("asset-clip")}
    assert (c["v1"].get("offset"), c["v1"].get("start"), c["v1"].get("duration")) == ("30/30s", "15/30s", "60/30s")
    assert c["a1"].find("adjust-volume").get("amount") == "-6dB" and int(c["a1"].get("lane")) < 0
    im = {m.get("value"): m for m in r.iter("marker")}
    assert im["vurgu"].get("start") == "90/30s"
    assert im["sahne: sh (render gerekli)"].get("duration") == "45/30s"
    assert "sh" not in c

    r = ET.parse(x).getroot()
    ci = {e.get("id"): e for e in r.iter("clipitem")}
    v = ci["v1-v"]
    assert [v.findtext(a) for a in ("start", "end", "in", "out")] == ["30", "90", "15", "75"]
    assert "v1-a" in ci, "videonun sesi bağlı ses izine gelir"
    assert ci["a1-a"].find(".//parameter/value").text == f"{10 ** (-6 / 20):.5f}"
    assert r.find(".//file/pathurl").text.startswith("file:///")
    assert {m.findtext("name") for m in r.iter("marker")} == {"vurgu", "sahne: sh (render gerekli)"}
    assert [t.findtext("enabled") for t in r.find(".//media/video").iter("track")] == ["TRUE", "FALSE"]  # V1, V2 gizli
    assert disa.yer_tutucular(k)[0].startswith("V2 0.00-1.50 sn: sahne sh")


def test_hiz_eslenir(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "INPUTS", tmp_path / "in")
    monkeypatch.setattr(paths, "OUTPUTS", tmp_path / "out")
    p = Proje("instagram", "x")
    p.girdi.mkdir(parents=True)
    (p.girdi / "v.mp4").write_bytes(b"")  # meta verisi kurguda: probe çağrılmaz
    k = Kurgu.model_validate({
        "kaynaklar": {"V": {"yol": "inputs:v.mp4", "sure": 10, "w": 64, "h": 64}},
        "izler": [{"id": "V1", "tur": "video"}],
        "klipler": [{"id": "v", "iz": "V1", "tur": "video", "kaynak": "V", "bas": 0, "sure": 2, "giris": 1, "hiz": 2}],
    })
    tp = [t.get("value") for t in ET.fromstring(disa.fcpxml(p, k).split("\n", 2)[2]).iter("timept")]
    assert tp == ["30/30s", "150/30s"]
    v = ET.fromstring(disa.xmeml(p, k).split("\n", 2)[2]).find(".//clipitem")
    assert v.findtext("out") == "150" and v.find(".//effect/effectid").text == "timeremap"
