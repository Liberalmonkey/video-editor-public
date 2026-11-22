"""Kesim geçişleri sonraki çekimi gösterir (ADR 0045, kabul maddesi 2).

WHY: instagram/1'de gecis-* bindirmeleri kareyi düz mavi, beyaz ya da siyah blokla dolduruyordu. Ölçüt:
geçiş karelerinin en az %80'inde gelen çekim görünür; düz tam kare en çok 2 kare; orta nokta kesimin üstünde.
Çekimler ayırt edilebilir dokulu iki görseldir (kırmızı tonlu A, mavi tonlu B); görünürlük ton oranıyla ölçülür.
"""

import os
import shutil
import subprocess

import numpy as np
import pytest

from vedit import hizli, kurgu, paths
from vedit.hizli import Proje
from vedit.schemas import Kurgu

KOK = paths.ROOT
REMOTION = KOK / "studio" / "node_modules" / ".bin" / ("remotion.cmd" if os.name == "nt" else "remotion")
W, H, FPS = 270, 480, 30
TURLER = ["sil", "kay", "saat", "iris", "kirbac", "isik", "piksel",
          "zoom_kirbac", "film_yanigi", "bolunme", "bozulma", "yirtma"]
SURE = 0.4  # 12 kare: Reels üst sınırı
PARCA = 1.0


def _goruntu(f, renk):
    # Dokulu: düz renk olsaydı "düz kare" ölçümü anlamsız olurdu.
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"testsrc2=s={W}x{H}:d=1", "-frames:v", "1",
                    "-vf", f"hue=s=0,colorchannelmixer={renk}", str(f)], check=True)


@pytest.fixture(scope="module")
def video(tmp_path_factory):
    if not (shutil.which("ffmpeg") and REMOTION.exists()):
        pytest.skip("ffmpeg ya da studio node_modules yok")
    tmp = tmp_path_factory.mktemp("gecis")
    mp = pytest.MonkeyPatch()
    mp.setattr(paths, "INPUTS", tmp / "in")
    mp.setattr(paths, "OUTPUTS", tmp / "out")
    p = Proje("instagram", "gecis")
    p.girdi.mkdir(parents=True)
    _goruntu(p.girdi / "a.png", "rr=1:rg=0:rb=0:gr=0.15:gg=0:gb=0:br=0.1:bg=0:bb=0")   # kırmızı tonlar
    _goruntu(p.girdi / "b.png", "rr=0.1:rg=0:rb=0:gr=0.2:gg=0:gb=0:br=1:bg=0:bb=0")    # mavi tonlar
    klipler = []
    for i in range(len(TURLER) + 1):
        c = {"id": f"k{i}", "iz": "V1", "tur": "gorsel", "bas": i * PARCA, "sure": PARCA, "kaynak": "a" if i % 2 == 0 else "b"}
        if i:
            c["gecis_giris"] = {"tur": TURLER[i - 1], "sure": SURE, "yon": "sol"}
        klipler.append(c)
    k = Kurgu.model_validate({"sekans": {"w": W, "h": H, "fps": FPS},
                              "kaynaklar": {"a": {"yol": "inputs:a.png", "ses": False}, "b": {"yol": "inputs:b.png", "ses": False}},
                              "izler": [{"id": "V1", "tur": "video"}], "klipler": klipler, "altyazi": {"acik": False}})
    kurgu.yaz(p.work, k)
    hizli._public_hazirla(p)
    props = kurgu.hazirla(p)
    out = tmp / "g.mp4"
    subprocess.run([str(REMOTION), "render", "remotion/index.tsx", "Kurgu", str(out), f"--props={props}",
                    f"--public-dir={p.work / 'public'}", "--log=error", "--crf=12"], check=True, cwd=KOK / "studio", shell=os.name == "nt")
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(out), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], check=True, capture_output=True).stdout
    yield np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3).astype(int)
    mp.undo()


def _oran(kare):
    """(A payı, B payı): kırmızı baskın ve mavi baskın piksel oranı."""
    r, b = kare[..., 0], kare[..., 2]
    renkli = (r + b) > 40
    return float(((r > b + 25) & renkli).mean()), float(((b > r + 25) & renkli).mean())


def _duz(kare) -> bool:
    return float(kare.std()) < 6.0


@pytest.mark.parametrize("i,tur", list(enumerate(TURLER, start=1)))
def test_gecis_sonraki_cekimi_gosterir(video, i, tur):
    kesim = int(round(i * PARCA * FPS))
    yarim = int(round(SURE * FPS / 2))
    kareler = video[kesim - yarim: kesim + yarim]
    onceki_a = i % 2 == 1  # i. kesimde çıkan çekim: tek i'de A
    gelen = [(_oran(k)[1] if onceki_a else _oran(k)[0]) for k in kareler]
    gorunur = sum(g > 0.02 for g in gelen) / len(gelen)
    assert gorunur >= 0.8, f"{tur}: gelen çekim karelerin yalnız %{gorunur * 100:.0f}'inde görünüyor"
    seri = enuzun = 0
    for k in kareler:
        seri = seri + 1 if _duz(k) else 0
        enuzun = max(enuzun, seri)
    assert enuzun <= 2, f"{tur}: {enuzun} kare düz tam kare"
    # Orta nokta kesimde: kesimden önce de sonra da gelen çekim kısmen görünür, kesimden sonra daha çok.
    assert gelen[0] < gelen[-1], f"{tur}: geçiş ilerlemiyor"
    assert gelen[yarim - 1] > 0.02, f"{tur}: kesimden önce gelen çekim hiç görünmüyor (orta nokta kesimde değil)"


def test_gecis_disinda_tek_cekim(video):
    # Geçişler arasında ekran tamamen o anki çekimdir: kuyruk ve ön pay taşmıyor.
    for i in range(len(TURLER) + 1):
        orta = int(round((i * PARCA + PARCA / 2) * FPS))
        a, b = _oran(video[orta])
        assert (a if i % 2 == 0 else b) > 0.5 and (b if i % 2 == 0 else a) < 0.02, f"parça {i}"
