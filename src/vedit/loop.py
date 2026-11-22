"""Kesintisiz loop mührü ve sarma noktası ölçümü (Google Flow / Veo çıktıları için).

# WHY: bkz. .claude/skills/loop-flow/SKILL.md — üretici modeller son kareyi ilk kareye her zaman bağlamaz;
# mühür sonrası sarma farkı ölçülmeden loop "temiz" sayılmaz.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


from .tembel import Tembel

# WHY: Stüdyo açılışında yüklenmesin (ADR 0050)
np = Tembel("numpy")

from . import ff

W, H = 160, 90


def _kareler(path: Path) -> np.ndarray:
    p = subprocess.run([ff.FFMPEG, "-v", "error", "-i", str(path), "-vf", f"scale={W}:{H},format=gray", "-f", "rawvideo", "-"],
                       capture_output=True, check=True)
    return np.frombuffer(p.stdout, dtype=np.uint8).reshape(-1, H, W).astype(np.float32)


def olc(path: Path) -> dict:
    """Son→ilk kare farkını ardışık kare farklarının medyanıyla karşılaştır."""
    k = _kareler(path)
    if len(k) < 3:
        raise SystemExit(f"Çok kısa video: {path}")
    ardisik = np.abs(k[1:] - k[:-1]).mean(axis=(1, 2))
    medyan, sarma = float(np.median(ardisik)), float(np.abs(k[0] - k[-1]).mean())
    # Hız değişen klipte dönüş, klibin kendi en hızlı adımlarından büyük değilse göze batmaz.
    esik = max(1.5 * medyan, float(np.percentile(ardisik, 95)), 0.5)
    return {"kare": len(k), "medyan": round(medyan, 3), "sarma": round(sarma, 3), "temiz": sarma <= esik}


def muhurle(src: Path, dst: Path, *, mod: str = "otomatik", capraz: float = 0.5, sure: float = 0.0) -> dict:
    """otomatik: sarma temizse dokunma, değilse ping-pong · pingpong · capraz: kuyruk başa erir (tek yönlü hareket için)."""
    src, dst = Path(src), Path(dst)
    once = olc(src)
    if mod == "otomatik":
        mod = "dogal" if once["temiz"] else "pingpong"
    kod = ["-an", "-c:v", "libx264", "-crf", "17", "-pix_fmt", "yuv420p", "-movflags", "+faststart"]
    if mod == "dogal":
        ff.ffmpeg("-i", str(src), *kod, str(dst))
    elif mod == "pingpong":
        # Dönüşte uç kareler atılır; yoksa dönüş noktasında iki kare aynı kalır ve takılma görünür.
        n = once["kare"]
        ff.ffmpeg("-i", str(src), "-filter_complex",
                  f"[0:v]split[a][b];[b]reverse,trim=start_frame=1:end_frame={n - 1},setpts=PTS-STARTPTS[r];[a][r]concat=n=2:v=1[v]",
                  "-map", "[v]", *kod, str(dst))
    elif mod == "capraz":
        L = ff.probe(src)["duration"]
        if L <= capraz * 2:
            raise SystemExit(f"Video çapraz geçiş için kısa: {L} sn")
        ff.ffmpeg("-i", str(src), "-filter_complex",
                  f"[0:v]split[g][k];[k]trim=start={L - capraz},setpts=PTS-STARTPTS,format=yuva420p,fade=t=out:st=0:d={capraz}:alpha=1[t];"
                  f"[g]trim=end={L - capraz},setpts=PTS-STARTPTS[b];[b][t]overlay=eof_action=pass[v]",
                  "-map", "[v]", *kod, str(dst))
    else:
        raise SystemExit("mod: otomatik | pingpong | capraz")
    sonra = olc(dst)
    if sure:  # kurguda istenen süreye sar; yeniden kodlamaz
        tmp = dst.with_suffix(".tmp.mp4")
        ff.ffmpeg("-stream_loop", "-1", "-i", str(dst), "-t", str(sure), "-c", "copy", "-movflags", "+faststart", str(tmp))
        tmp.replace(dst)
    return {"mod": mod, "once": once, "sonra": sonra, "cikti": str(dst)}
