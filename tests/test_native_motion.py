"""Native motion sözleşmesi (ADR 0045): kayıt dosyası, parametre doğrulama, kurgu-denetle ve render."""

import os
import shutil
import subprocess

import numpy as np
import pytest

from vedit import hizli, kurgu, native_motion, paths
from vedit.hizli import Proje
from vedit.schemas import Kurgu

KOK = paths.ROOT
REMOTION = KOK / "studio" / "node_modules" / ".bin" / ("remotion.cmd" if os.name == "nt" else "remotion")
W, H = 270, 480


@pytest.fixture
def kayit(monkeypatch):
    # LIBRARY başka teste göre değişse de kayıt gerçek dosyadan okunur.
    f = KOK / "library" / "motion" / "native" / "sema.json"
    monkeypatch.setattr(native_motion, "sema_yolu", lambda: f)
    return native_motion.kayitlar()


def test_kayit_tik_icerir_ve_meta_tam(kayit):
    m = kayit["ikon/tik"]["meta"]
    assert m["tur"] == "ikon" and m["cikis_sn"] < m["giris_sn"] and m["en_kucuk_px"] >= 160


def test_param_dogrulama(kayit):
    assert native_motion.param_hatalari("ikon/tik", {}) == []
    assert native_motion.param_hatalari("ikon/tik", {"renk": "olumlu"}) == []
    assert native_motion.param_hatalari("ikon/tik", {"renk": "#00FF00"}), "onaltılık renk reddedilir"
    assert native_motion.param_hatalari("ikon/tik", {"fazla": 1}), "bilinmeyen alan reddedilir"
    assert native_motion.param_hatalari("ikon/yok", {})


def _proje(tmp_path, monkeypatch, klipler):
    monkeypatch.setattr(paths, "INPUTS", tmp_path / "in")
    monkeypatch.setattr(paths, "OUTPUTS", tmp_path / "out")
    p = Proje("instagram", "nm")
    p.girdi.mkdir(parents=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"color=c=0x808080:s={W}x{H}:r=30:d=2",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", str(p.girdi / "gri.mp4")], check=True)
    k = Kurgu.model_validate({
        "sekans": {"w": W, "h": H, "fps": 30},
        "kaynaklar": {"gri": {"yol": "inputs:gri.mp4", "sure": 2.0, "ses": False}},
        "izler": [{"id": "V2", "tur": "video"}, {"id": "V1", "tur": "video"}],
        "klipler": [{"id": "v", "iz": "V1", "tur": "video", "bas": 0, "sure": 2, "kaynak": "gri"}, *klipler],
    })
    kurgu.yaz(p.work, k)
    return p, k


def test_denetle_bilesen_klibini_kaynaksiz_kabul_eder_yanlisi_reddeder(tmp_path, monkeypatch, kayit):
    if not shutil.which("ffmpeg"):
        pytest.skip("ffmpeg yok")
    p, k = _proje(tmp_path, monkeypatch, [{"id": "m", "iz": "V2", "tur": "motion", "bas": 0.2, "sure": 1.3, "bilesen": {"ad": "ikon/tik"}}])
    assert kurgu.denetle(p, k) == []
    k.klipler[1].bilesen.param = {"renk": "#FF0000"}
    assert any("bileşen ikon/tik" in h for h in kurgu.denetle(p, k))


@pytest.mark.skipif(not REMOTION.exists(), reason="studio node_modules yok")
def test_render_tik_cizilir_zemin_gorunur(tmp_path, monkeypatch, kayit):
    if not shutil.which("ffmpeg"):
        pytest.skip("ffmpeg yok")
    p, _ = _proje(tmp_path, monkeypatch, [{"id": "m", "iz": "V2", "tur": "motion", "bas": 0.0, "sure": 1.3, "bilesen": {"ad": "ikon/tik"}}])
    hizli._public_hazirla(p)
    props = kurgu.hazirla(p)
    png = tmp_path / "k.png"
    subprocess.run([str(REMOTION), "still", "remotion/index.tsx", "Kurgu", str(png), f"--props={props}",
                    f"--public-dir={p.work / 'public'}", "--frame=20", "--log=error"], check=True, cwd=KOK / "studio", shell=os.name == "nt")
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(png), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], check=True, capture_output=True).stdout
    img = np.frombuffer(raw, np.uint8).reshape(H, W, 3).astype(int)
    gri = (np.abs(img - 128) < 12).all(axis=2)
    assert gri.mean() > 0.85, "zemin büyük ölçüde görünür kalmalı (siyah kutu yok)"
    assert (~gri).sum() > 150, "tik çizilmiş olmalı"
    siyah = (img < 20).all(axis=2)
    assert siyah.sum() < (~gri).sum() * 0.6, "grafik siyah kutu değil, ince kontur olmalı"


def test_yuz_kutusu_contain_ve_cover_eslemesi():
    from vedit import yuz_bolge

    # 1920x1080 kaynak, 1080x1920 dikey kare. Contain: genişlik sığar, üst-alt bant; merkezdeki kutu merkezde kalır.
    k = yuz_bolge.esle([860, 440, 200, 200], (1920, 1080), (1080, 1920), kapla=False)
    assert abs(k["x"] + k["w"] / 2 - 0.5) < 0.01 and abs(k["y"] + k["h"] / 2 - 0.5) < 0.01
    assert abs(k["w"] - 200 * (1080 / 1920) / 1080) < 1e-3
    # Cover: yükseklik doldurur, kutu büyür; ölçek 2 merkezden büyütür, kaydırma oranca taşır.
    c = yuz_bolge.esle([860, 440, 200, 200], (1920, 1080), (1080, 1920), kapla=True, olcek=2, x=108)
    assert abs(c["w"] - 2 * 200 * (1920 / 1080) / 1080) < 1e-3
    assert abs((c["x"] + c["w"] / 2) - 0.6) < 0.01
