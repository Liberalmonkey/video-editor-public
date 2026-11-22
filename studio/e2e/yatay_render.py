"""Gerçek render: 8 sahne + hook + cta 16:9 ve 9:16, kontak sayfası gözle denetlenir; ayrık sesle tam final senkronu.
Dikey regresyon: mevcut SplitReel ham.mp4'üne karşı SSIM. Geçici kökte çalışır. argv: çıktı, [kıyas proje adı]."""
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

from vedit import ff, hizli, kurgu, paths
from vedit.schemas import Kurgu

GERCEK_OUT = paths.OUTPUTS
cikti = Path(sys.argv[1]).resolve()
cikti.mkdir(parents=True, exist_ok=True)
paths.INPUTS, paths.OUTPUTS = cikti / "in", cikti / "out"
SR = 48000
SURE = 34.0


def kaynak(p, ad, w, h):
    """440 Hz taban ve 7. saniyede tek belirgin tık: senkron ölçümü için."""
    y = p.girdi / ad
    y.parent.mkdir(parents=True, exist_ok=True)
    wav = cikti / f"{ad}.wav"
    n = int(SURE * SR)
    x = 0.1 * np.sin(2 * np.pi * 440 * np.arange(n) / SR)
    x[7 * SR:7 * SR + 480] = 0.95
    sf.write(wav, np.stack([x, x], axis=1).astype(np.float32), SR)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"testsrc2=s={w}x{h}:r=30:d={SURE}", "-i", str(wav),
                    "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest", str(y)], check=True)
    return y


# sablonlar.ts ile aynı içerikler; ad dosyadan okunur ki şablon değişince test de değişsin.
metin = (paths.ROOT / "studio/web/src/paneller/sablonlar.ts").read_text(encoding="utf-8")
dizi = metin[metin.index("= [") + 2:metin.rindex("]") + 1]
sablonlar = json.loads(subprocess.run(["node", "-e", "console.log(JSON.stringify(eval(require('fs').readFileSync(0,'utf8'))))"],
                                      input=dizi, capture_output=True, text=True, encoding="utf-8", check=True).stdout)
assert len(sablonlar) == 8


def proje(ad, w, h, kaynak_ad, kw, kh):
    p = hizli.Proje("instagram", ad)
    kaynak(p, kaynak_ad, kw, kh)
    (p.work / "public").mkdir(parents=True, exist_ok=True)
    ff.ffmpeg("-f", "lavfi", "-i", "testsrc2=s=1920x1080:r=1:d=1", "-frames:v", "1", str(p.work / "public" / "ekran.png"))
    klipler = [{"id": "v", "iz": "V1", "tur": "video", "kaynak": "K", "bas": 0, "sure": SURE, "konusmaci": True}]
    t = 0.0
    for i, s in enumerate(sablonlar):
        sahne = dict(s["sahne"])
        if sahne.get("kind") == "shot":
            sahne["img"] = "ekran.png"
        klipler.append({"id": f"s{i}", "iz": "V2", "tur": "sahne", "bas": t, "sure": s["sure"], "sahne": sahne})
        t += s["sure"] + 1.0  # araya tam ekran konuşmacı
    kelimeler = [{"w": f"kelime{i}", "s": i * 0.5, "e": i * 0.5 + 0.45} for i in range(int(SURE * 2))]
    k = Kurgu.model_validate({"sekans": {"w": w, "h": h, "fps": 30}, "kaynaklar": {"K": {"yol": f"inputs:{kaynak_ad}", "sure": SURE, "w": kw, "h": kh, "ses": True}},
                              "kelimeler": {"K": kelimeler}, "izler": [{"id": "V2", "tur": "video"}, {"id": "V1", "tur": "video"}, {"id": "A2", "tur": "ses"}, {"id": "A3", "tur": "ses"}], "klipler": klipler})
    kurgu.yaz(p.work, k)
    return p, t


def kareler(p, ad, sonuna):
    """Her sahnenin ortasından bir kare, sahne oturmuş halde."""
    y = hizli.taslak(p)
    d = cikti / ad
    d.mkdir(exist_ok=True)
    t = 0.0
    anlar = []
    for s in sablonlar:
        anlar.append((s["kind"], t + s["sure"] * 0.8))
        t += s["sure"] + 1.0
    anlar.append(("tam-ekran", sonuna - 0.5))
    for i, (n, a) in enumerate(anlar):
        ff.ffmpeg("-ss", f"{a:.2f}", "-i", str(y), "-frames:v", "1", str(d / f"{i:02}-{n}.png"))
        shutil.copy(d / f"{i:02}-{n}.png", d / f"k{i:02}.png")
    return d, anlar


def sayfa(d, anlar, kol, cik):
    satir = (len(anlar) + kol - 1) // kol
    ff.ffmpeg("-framerate", "1", "-i", str(d / "k%02d.png"), "-vf", f"tile={kol}x{satir}:padding=4:color=gray", "-frames:v", "1", str(cikti / cik))


yp, son = proje("yatay", 1920, 1080, "y.mp4", 1280, 720)
sayfa(*kareler(yp, "yatay", son), 3, "yatay-sayfa.png")
dp, son = proje("dikey", 1080, 1920, "d.mp4", 720, 1280)
sayfa(*kareler(dp, "dikey", son), 5, "dikey-sayfa.png")

# Tam final, ayrık ses 0,4 sn kaydırılmış: tık 7,4'te duyulmalı.
k = kurgu.oku(yp.work)
v = next(c for c in k.klipler if c.id == "v")
v.ses_kapali = True
v.bag = "b"
k.izler.insert(2, type(k.izler[0]).model_validate({"id": "A1", "tur": "ses", "ad": "Konuşma"}))
k.klipler.append(type(v).model_validate({"id": "ayrik", "iz": "A1", "tur": "ses", "kaynak": "K", "bas": 0.4, "sure": SURE - 0.4, "giris": 0, "bag": "b", "olay": {"konusma": True}}))
kurgu.yaz(yp.work, k)
r = hizli.final(yp, platform="youtube", ad="yatay-final")
print("final:", r)
wav = cikti / "final.wav"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(r), "-vn", "-ac", "1", "-ar", str(SR), str(wav)], check=True)
d, _ = sf.read(wav)
tepe = np.argmax(np.abs(d)) / SR
print(f"tik: {tepe:.3f} sn (beklenen 7,4)")
assert abs(tepe - 7.4) < 0.06, tepe
print("video boyutu:", ff.probe(r)["video"]["width"], ff.probe(r)["video"]["height"])
