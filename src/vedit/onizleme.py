"""Saydam motion önizlemesi: doğru kare ve kırpım (poster.jpg + onizleme.mp4).

WHY: bkz. wiki/decisions/0061-kasa-ve-kesif.md. Eski poster sürenin ortasındaki tek kareyi tam tuvalden 360 px'e
küçültüyordu. Geçişte o an tam kaplamaydı ("Turuncu-koyu silme" düz renk, siyah kutu gibi görünüyordu). Zil gibi
kısa ikonlarda an boştu. 1080x1920 tuvalde küçük grafik mikroskobik kalıyordu. Burada alfa kaplaması kare kare
ölçülür, anlamlı kare seçilir, grafik alfa sınır kutusuna kırpılır ve kare biçimde koyu zemine oturtulur.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import numpy as np

from . import ff

ZEMIN = "0x1B1E25"  # motion.ZEMIN ile aynı: saydam grafiğin hem açık hem koyu öğesi görünür
OLCUM_FPS = 8
OLCUM_G = 96  # ölçüm genişliği (px); kaplama ve sınır kutusu bu ölçekte
POSTER = 480
DONGU = 320
PAY = 0.12
ESIK = 24  # alfa > ESIK piksel "dolu" sayılır
TAM = 0.92  # bu kaplamanın üstü tam ekran düz renk sayılır (geçişin ortası değil)


def alfa_olc(webm: Path, w: int, h: int, fps: float = OLCUM_FPS) -> tuple[np.ndarray, list[tuple[int, int, int, int] | None]]:
    """(kare başına kaplama 0..1, kare başına sınır kutusu x0,y0,x1,y1 ölçüm ölçeğinde ya da None)."""
    oh = max(2, round(h * OLCUM_G / w / 2) * 2)
    r = subprocess.run([ff.FFMPEG, "-v", "error", "-c:v", "libvpx-vp9", "-i", str(webm), "-vf",
                        f"fps={fps:g},alphaextract,scale={OLCUM_G}:{oh}:flags=area,format=gray", "-f", "rawvideo", "-"],
                       capture_output=True, check=True)
    kareler = np.frombuffer(r.stdout, np.uint8).reshape(-1, oh, OLCUM_G)
    dolu = kareler > ESIK
    kaplama = dolu.mean(axis=(1, 2))
    kutular: list[tuple[int, int, int, int] | None] = []
    for d in dolu:
        ys, xs = np.nonzero(d)
        kutular.append((int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1) if len(xs) else None)
    return kaplama, kutular


def kare_sec(kaplama: np.ndarray, tur: str = "") -> int:
    """Gösterilecek kare. Geçişte kaplaması 0,5'e en yakın an (silme yarıda); diğerlerinde tam kaplama olmayan en dolu an.

    Eşitlikte sonraki kare seçilir: giriş animasyonu bitmiş, grafik yerine oturmuş hâl. Hep boşsa orta kare.
    """
    if not len(kaplama) or kaplama.max() <= 0:
        return len(kaplama) // 2
    if tur == "transition":
        return int(np.argmin(np.abs(kaplama - 0.5)))
    aday = np.where(kaplama < TAM, kaplama, -1.0)
    if aday.max() <= 0:
        aday = kaplama
    en = aday.max()
    # Tepeye %95 yakın son kare: animasyon oturmuş, çıkış başlamamış
    yakin = np.nonzero(aday >= en * 0.95)[0]
    return int(yakin[len(yakin) // 2]) if len(yakin) > 2 else int(yakin[-1])


def kirpim(kutular: list, w: int, h: int, oh: int, tur: str = "") -> tuple[int, int, int, int]:
    """Tüm karelerin sınır kutusu birleşimi + pay, tam çözünürlükte (x, y, cw, ch). Geçiş ve boşsa tam tuval."""
    dolu = [k for k in kutular if k]
    if tur == "transition" or not dolu:
        return 0, 0, w, h
    x0, y0 = min(k[0] for k in dolu), min(k[1] for k in dolu)
    x1, y1 = max(k[2] for k in dolu), max(k[3] for k in dolu)
    sx, sy = w / OLCUM_G, h / oh
    x0, x1, y0, y1 = x0 * sx, x1 * sx, y0 * sy, y1 * sy
    pay = PAY * max(x1 - x0, y1 - y0)
    # En küçük kırpım tuvalin %20'si: tek noktalık ikon dev piksel olmasın
    en_az = 0.2 * min(w, h)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    yw, yh = max(x1 - x0 + 2 * pay, en_az), max(y1 - y0 + 2 * pay, en_az)
    x, y = max(0, cx - yw / 2), max(0, cy - yh / 2)
    cw, ch = min(w - x, yw), min(h - y, yh)
    return int(x) // 2 * 2, int(y) // 2 * 2, max(2, int(cw) // 2 * 2), max(2, int(ch) // 2 * 2)


def uret(webm: Path, klasor: Path, *, w: int, h: int, sure: float, tur: str = "", fps: float = 30.0) -> dict:
    """`klasor/poster.jpg` ve `klasor/onizleme.mp4` yazar; seçilen an ve kırpımı döner. Alfasız dosyada orta kare, kırpım yok."""
    klasor.mkdir(parents=True, exist_ok=True)
    alfa = bool((ff.probe(webm).get("video") or {}).get("alfa"))
    if alfa:
        # Kısa klip (geçiş, ikon) kare kare ölçülür: 0,8 sn'lik silmenin ortası 8 fps'te kaçıyordu
        o_fps = fps if tur == "transition" or sure <= 2 else OLCUM_FPS
        kaplama, kutular = alfa_olc(webm, w, h, o_fps)
        oh = max(2, round(h * OLCUM_G / w / 2) * 2)
        i = kare_sec(kaplama, tur)
        x, y, cw, ch = kirpim(kutular, w, h, oh, tur)
        an = i / o_fps
    else:
        kaplama, an, (x, y, cw, ch) = np.array([]), sure / 2, (0, 0, w, h)
    giris = ["-c:v", "libvpx-vp9"] if alfa else []
    if tur == "transition":
        # Geçiş paneli çoğu zaman koyu renktir; koyu zeminde kaybolur. Dama zemin alfanın sınırını gösterir.
        k = max(16, min(w, h) // 20)
        dama = f"if(mod(floor(X/{k})+floor(Y/{k})\\,2)\\,92\\,58)"
        zemin = (f"nullsrc=s={w}x{h}:r={fps:g},geq=lum='{dama}':cb=128:cr=128,"
                 f"format=yuv420p[b];[b][0:v]overlay=shortest=1")
    else:
        zemin = f"color={ZEMIN}:s={w}x{h}:r={fps:g}[b];[b][0:v]overlay=shortest=1"
    kare_kutu = lambda n: (f"crop={cw}:{ch}:{x}:{y},scale={n}:{n}:force_original_aspect_ratio=decrease:flags=lanczos,"
                           f"pad={n}:{n}:(ow-iw)/2:(oh-ih)/2:color={ZEMIN}")
    # -ss ile atlama alfa kanalını bazı karelerde boş çözüyordu (motion.py notu); kare numarasıyla seçilir
    kare = round(an * fps)
    ff.ffmpeg(*giris, "-i", str(webm), "-filter_complex", f"{zemin},select=eq(n\\,{kare}),{kare_kutu(POSTER)}",
              "-frames:v", "1", "-q:v", "3", str(klasor / "poster.jpg"))
    ff.ffmpeg(*giris, "-i", str(webm), "-filter_complex", f"{zemin},{kare_kutu(DONGU)},fps=24", "-an", "-c:v", "libx264",
              "-preset", "veryfast", "-crf", "26", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(klasor / "onizleme.mp4"))
    return {"an": round(an, 3), "kirpim": [x, y, cw, ch], "kaplama": round(float(kaplama.max()), 3) if len(kaplama) else None}
