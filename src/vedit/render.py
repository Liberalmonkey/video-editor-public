"""Render: tek kompozisyon ya da bölüm bölüm (paralel, önbellekli) + master ses mux.

# WHY: bkz. wiki/decisions/0002-renderer-hyperframes.md — Windows'ta çoklu worker diske kare
# yazar; bunun yerine her bölüm tek worker ile stream edilir ve 2–3 bölüm paralel işlenir.
# Bölümler sessiz render edilir, master.wav tek seferde mux'lanır (AAC sınır boşluğu olmaz).
"""

from __future__ import annotations

import json
import shutil
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from . import ff, hf, paths

QUALITY = {"preview": ("draft", 1), "final": ("delivery", 1)}


def _render_one(comp_dir: Path, out: Path, quality: str, fps: int) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".tmp.mp4")
    # WHY: render hatasında yarım kalan .tmp.mp4 dosyası diskte sızıntı bırakmasın.
    try:
        hf.render(comp_dir, tmp, quality=quality, fps=fps, workers=1)
        tmp.replace(out)
    finally:
        tmp.unlink(missing_ok=True)
    return out


def mux(video: Path, audio: Path | None, out: Path) -> Path:
    if audio and audio.exists():
        ff.ffmpeg("-i", str(video), "-i", str(audio), "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy",
                  "-c:a", "aac", "-b:a", "320k", "-ar", "48000", "-shortest", "-movflags", "+faststart", str(out))
    else:
        shutil.copy2(video, out)
    return out


def run(root: Path, *, mode: str, fps: int, parallel: int = 2) -> dict:
    quality, _ = QUALITY[mode]
    manifest = json.loads((root / "build" / "comp_manifest.json").read_text(encoding="utf-8"))
    master = root / "build" / "master.wav"
    final = root / "renders" / f"{mode}.mp4"
    t0 = time.time()
    chapters = manifest.get("chapters") or []
    if not chapters:
        silent = root / "renders" / f".{mode}.video.mp4"
        _render_one(root / "comp", silent, quality, fps)
        mux(silent, master, final)
        silent.unlink(missing_ok=True)
        return {"out": f"renders/{mode}.mp4", "seconds": round(time.time() - t0, 1), "chapters": 0}

    cache_dir = root / "renders" / "chapters"
    cache_dir.mkdir(parents=True, exist_ok=True)
    jobs, outs, reused = [], [], 0
    for ch in chapters:
        out = cache_dir / f"{ch['id']}.{mode}.{ch['hash']}.mp4"
        outs.append(out)
        if out.exists():
            reused += 1
            continue
        for stale in cache_dir.glob(f"{ch['id']}.{mode}.*.mp4"):
            stale.unlink(missing_ok=True)
        jobs.append((paths.ROOT / ch["dir"], out))
    with ThreadPoolExecutor(max_workers=max(1, parallel)) as ex:
        list(ex.map(lambda j: _render_one(j[0], j[1], quality, fps), jobs))
    lst = cache_dir / f"concat.{mode}.txt"
    lst.write_text("".join(f"file '{o.name}'\n" for o in outs), encoding="utf-8")
    joined = root / "renders" / f".{mode}.video.mp4"
    ff.ffmpeg("-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(joined))
    mux(joined, master, final)
    joined.unlink(missing_ok=True)
    return {"out": f"renders/{mode}.mp4", "seconds": round(time.time() - t0, 1), "chapters": len(chapters),
            "rendered": len(jobs), "reused": reused}
