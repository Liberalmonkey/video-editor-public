"""Olay sesi ve loop mührü testi: `.venv/Scripts/python scripts/test_olaysesi.py`. Geçici klasörde çalışır."""

import json
import tempfile
from pathlib import Path
from types import SimpleNamespace as E

import numpy as np

from vedit import ff, loop, olaysesi as os_

ENTRIES = [E(id="w1", file="w1.wav", category="whoosh", tags=[], duration_s=0.6, peak_offset_s=0.3),
           E(id="w2", file="w2.wav", category="whoosh", tags=["zoom", "in"], duration_s=0.7, peak_offset_s=0.4),
           E(id="c1", file="c1.wav", category="click", tags=[], duration_s=0.1, peak_offset_s=0.0)]


def plan(olaylar, **kw):
    return os_.planla({"fps": 30, "olaylar": olaylar}, ENTRIES, {"always": {"*": {"mouse_click": "c1"}}}, **kw)


def birim():
    p = plan([{"t": 1.0, "tur": "zoom_in", "sure": 1.0}])["yerler"][0]
    assert abs(p["tepe"] - 1.9) < 1e-6 and p["dosya"] == "w2.wav", p  # tepe varışta, zoom etiketi öncelikli
    assert plan([{"t": 1.0, "tur": "gecis", "sure": 0.5}])["yerler"][0]["tepe"] == 1.25  # kesme karesinde
    assert plan([{"kare": 60, "tur": "tik"}])["yerler"][0]["dosya"] == "c1.wav"  # kit rolü, kareden zaman
    r = plan([{"t": 2, "tur": "punch_in"}, {"t": 3, "tur": "kesme"}])
    assert not r["yerler"] and len(r["sessiz"]) == 2  # görünmez olaylar sessiz
    r = plan([{"t": 5.0, "tur": "tik"}, {"t": 5.1, "tur": "gecis", "sure": 0.2, "guc": "hard"}])
    assert [y["tur"] for y in r["yerler"]] == ["gecis"] and len(r["dusen"]) == 1  # çakışmada güçlü olan kalır
    try:
        plan([{"t": 1, "tur": "uydurma"}])
        raise AssertionError("bilinmeyen tür geçmemeli")
    except SystemExit:
        pass
    # yükselen istenip düşen örnek gelince çevrilir: tepe sona yakın olmalı
    d = np.zeros((48000, 2), dtype=np.float32)
    d[1000] = 1
    _, tepe = os_._sekillendir(d, {"yon": "yukselen", "uydur": False, "sure": 0, "tur": "zoom_in", "sira": 0})
    assert tepe > 24000, tepe


def uctan_uca(t: Path):
    v = t / "v.mp4"
    ff.ffmpeg("-f", "lavfi", "-i", "testsrc2=s=320x180:r=30:d=6", "-f", "lavfi", "-i", "sine=f=220:d=6", "-shortest",
              "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", str(v))
    spec = t / "olaylar.json"
    spec.write_text(json.dumps({"video": "v.mp4", "fps": 30, "olaylar": [
        {"t": 1.0, "tur": "zoom_in", "sure": 0.5}, {"t": 2.5, "tur": "zoom_out", "sure": 0.5},
        {"t": 3.5, "tur": "gecis", "sure": 0.4}, {"t": 4.5, "tur": "tik"}, {"t": 5.0, "tur": "kesme"}]}), encoding="utf-8")
    r = os_.calistir(spec)
    info = ff.probe(Path(r["cikti"]))
    assert r["yerlesen"] == 4 and info.get("audio") and abs(info["duration"] - 6) < 0.3, r
    assert abs(r["loudness"]["I"] + 14) <= 1.5, r["loudness"]
    # loop: ham test deseni sarmaz, ping-pong sarar, çapraz da sarar
    ham = t / "ham.mp4"
    ff.ffmpeg("-f", "lavfi", "-i", "gradients=s=320x180:r=30:d=4:speed=0.02:seed=7", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(ham))
    assert not loop.olc(ham)["temiz"], loop.olc(ham)
    for mod in ("pingpong", "capraz"):
        s = loop.muhurle(ham, t / f"{mod}.mp4", mod=mod)
        assert s["sonra"]["temiz"], s
    assert loop.muhurle(ham, t / "o.mp4")["mod"] == "pingpong"
    uz = loop.muhurle(ham, t / "uz.mp4", mod="pingpong", sure=20)
    assert abs(ff.probe(Path(uz["cikti"]))["duration"] - 20) < 0.5


if __name__ == "__main__":
    birim()
    with tempfile.TemporaryDirectory() as d:
        uctan_uca(Path(d))
    print("Tümü geçti.")
