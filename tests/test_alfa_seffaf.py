"""Saydam motion klibi görüntünün üstünde siyah kutu olmadan görünmeli: önizleme yolu ve render.

WHY: instagram/1 (2026-11-19). Stüdyo önizlemesi motion webm'ini libx264 yuv420p proxy'ye çeviriyordu;
alfa düştü, grafik konuşmacının yüzünde siyah kare oldu. Render yolu ayrıca piksel örneğiyle sınanır.
"""

import os
import shutil
import subprocess

import numpy as np
import pytest

from vedit import ff, hizli, kurgu, paths
from vedit.hizli import Proje
from vedit.schemas import Kurgu

pytest.importorskip("fastapi")
from vedit.studio import app as studio_app  # noqa: E402

KOK = paths.ROOT
REMOTION = KOK / "studio" / "node_modules" / ".bin" / ("remotion.cmd" if os.name == "nt" else "remotion")
W, H = 270, 480


def _ffmpeg(*a: str) -> None:
    subprocess.run(["ffmpeg", "-v", "error", "-y", *a], check=True)


def _gri_video(f):
    # Düz orta gri: siyah kutu (Y≈16) ile karışmaz.
    _ffmpeg("-f", "lavfi", "-i", f"color=c=0x808080:s={W}x{H}:r=30:d=1", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(f))


def _saydam_webm(f):
    # Saydam zemin, ortada 60 px kırmızı kare.
    # drawbox rgba'da alfaya yazmaz; opak kare overlay ile basılır.
    _ffmpeg("-filter_complex", f"color=c=black@0.0:s={W}x{H}:r=30:d=1,format=rgba[z];color=c=red:s=60x60:r=30:d=1,format=rgba[k];"
            f"[z][k]overlay={W // 2 - 30}:{H // 2 - 30}:format=auto",
            "-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p", "-b:v", "0", "-crf", "30", "-auto-alt-ref", "0", str(f))


@pytest.fixture
def proje(tmp_path, monkeypatch):
    if not shutil.which("ffmpeg"):
        pytest.skip("ffmpeg yok")
    monkeypatch.setattr(paths, "INPUTS", tmp_path / "in")
    monkeypatch.setattr(paths, "OUTPUTS", tmp_path / "out")
    monkeypatch.setattr(paths, "LIBRARY", tmp_path / "lib")
    p = Proje("instagram", "alfa")
    p.girdi.mkdir(parents=True)
    (p.work / "public" / "motion").mkdir(parents=True)
    _gri_video(p.girdi / "gri.mp4")
    _saydam_webm(p.work / "public" / "motion" / "kare.webm")
    k = Kurgu.model_validate({
        "sekans": {"w": W, "h": H, "fps": 30},
        "kaynaklar": {"gri": {"yol": "inputs:gri.mp4", "sure": 1.0, "ses": False},
                      "kare": {"yol": "public:motion/kare.webm", "sure": 1.0, "ses": False}},
        "izler": [{"id": "V2", "tur": "video"}, {"id": "V1", "tur": "video"}],
        "klipler": [{"id": "v", "iz": "V1", "tur": "video", "bas": 0, "sure": 1, "kaynak": "gri"},
                    {"id": "m", "iz": "V2", "tur": "motion", "bas": 0, "sure": 1, "kaynak": "kare"}],
    })
    kurgu.yaz(p.work, k)
    return p, k


def test_probe_vp9_alfasini_gorur(proje):
    p, _ = proje
    assert ff.probe(p.work / "public" / "motion" / "kare.webm")["video"]["alfa"] is True
    assert ff.probe(p.girdi / "gri.mp4")["video"]["alfa"] is False


def test_onizleme_alfali_kaynagi_proxyye_vermez(proje, monkeypatch):
    p, k = proje
    baslayan = []
    monkeypatch.setattr(studio_app.threading, "Thread", lambda target, args, daemon: baslayan.append(args[1]) or type("T", (), {"start": lambda s: None})())
    es = studio_app.medya_eslemesi(p, k)
    assert "/proxy/" not in es["kare"] and es["kare"].endswith("/public/motion/kare.webm")
    assert [f.name for f in baslayan] == ["gri.mp4"], "yalnız opak video proxy'ye girer"


def test_onizleme_motion_disi_alfali_webm_de_proxysiz(proje, monkeypatch):
    p, k = proje
    monkeypatch.setattr(studio_app.threading, "Thread", lambda target, args, daemon: type("T", (), {"start": lambda s: None})())
    k2 = k.model_copy(update={"klipler": [c for c in k.klipler if c.id != "m"]})
    es = studio_app.medya_eslemesi(p, k2)
    assert "/proxy/" not in es["kare"]


def test_tarayici_vp9_alfasini_gri_zemin_ustunde_cizer(proje, tmp_path):
    """Player önizlemede <video> kullanır; Chromium VP9 alfasını çözmeli (WebView2 de Chromium'dur)."""
    sp = pytest.importorskip("playwright.sync_api")
    p, _ = proje
    sayfa = tmp_path / "v.html"
    webm = (p.work / "public" / "motion" / "kare.webm").as_uri()
    sayfa.write_text(f"""<body style="margin:0;background:#808080"><video id=v src="{webm}" muted playsinline
      style="display:block;width:{W}px;height:{H}px"></video></body>""", encoding="utf-8")
    with sp.sync_playwright() as pw:
        try:
            b = pw.chromium.launch()
        except Exception as e:  # noqa: BLE001
            pytest.skip(f"chromium yok: {e}")
        s = b.new_page(viewport={"width": W, "height": H})
        s.goto(sayfa.as_uri())
        s.wait_for_function("document.getElementById('v').readyState >= 2", timeout=10000)
        s.evaluate("new Promise(r => { const v = document.getElementById('v'); v.currentTime = 0.5; v.onseeked = r; })")
        png = s.screenshot()
        b.close()
    f = tmp_path / "s.png"
    f.write_bytes(png)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(f), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         check=True, capture_output=True).stdout
    img = np.frombuffer(raw, np.uint8).reshape(H, W, 3).astype(int)
    assert all(abs(c - 128) < 20 for c in img[40, 40]), f"köşe {img[40, 40]}: alfa düştü"
    assert img[H // 2, W // 2][0] > 180, "grafik çizilmeli"


@pytest.mark.skipif(not REMOTION.exists(), reason="studio node_modules yok")
def test_render_grafik_disinda_goruntu_gorunur(proje, tmp_path):
    p, _ = proje
    hizli._public_hazirla(p)  # fontlar: render yolu taslak ile aynı olsun
    props = kurgu.hazirla(p)
    png = tmp_path / "kare.png"
    subprocess.run([str(REMOTION), "still", "remotion/index.tsx", "Kurgu", str(png), f"--props={props}",
                    f"--public-dir={p.work / 'public'}", "--frame=15", "--log=error"],
                   check=True, cwd=KOK / "studio", shell=os.name == "nt")
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(png), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         check=True, capture_output=True).stdout
    img = np.frombuffer(raw, np.uint8).reshape(H, W, 3).astype(int)
    # Grafik dışı köşeler: gri görüntü görünmeli, siyah kutu değil.
    for y, x in ((40, 40), (40, W - 40), (H - 140, 40), (H // 2, W // 2 - 60), (H // 2, W // 2 + 60)):
        r, g, b = img[y, x]
        assert abs(r - 128) < 20 and abs(g - 128) < 20 and abs(b - 128) < 20, f"({x},{y}) {img[y, x]} siyah kutu"
    r, g, b = img[H // 2, W // 2]
    assert r > 180 and g < 80 and b < 80, "grafiğin kendisi çizilmeli"
