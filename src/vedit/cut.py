"""EDL → A-roll (FFmpeg) + eski→yeni zaman eşlemesi + kesilmiş transkript.

Her segment ayrı dosyaya, aynı parametrelerle kodlanır (segment hash'i ile önbellekli);
sonra concat demuxer ile kopyalanarak birleştirilir. EDL'de tek segment değişirse sadece o
segment yeniden kodlanır. Kesim noktaları kelime sınırına yaslanır ve 10–15 ms ses fade'i
ile tık sesi önlenir.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from . import ff, paths
from .schemas import Edl, load_json, save_json

PRE_PAD, POST_PAD = 0.06, 0.10


def _words_for(root: Path, src_rel: str) -> list[dict]:
    tr_path = root / "analysis" / "transcript.json"
    if not tr_path.exists():
        return []
    tr = json.loads(tr_path.read_text(encoding="utf-8"))
    data = tr["files"].get(Path(src_rel).stem)
    if not data:
        return []
    return [w for s in data["segments"] for w in s["words"]]


def snap(in_: float, out: float, words: list[dict], src_dur: float) -> tuple[float, float]:
    """Kesimi kelime sınırına yasla: kelimenin ortasından kesme, nefes payı bırak."""
    if not words:
        return max(0.0, in_), min(src_dur, out)
    # in: in_ noktasını içeren ya da ondan sonra başlayan ilk kelime
    first = next((w for w in words if w["e"] > in_ + 0.02), None)
    if first:
        # önceki kelime yoksa sınır yok (default 0.0 olsaydı 0.0'da başlayan ilk kelime atılırdı)
        prev_end = max((w["e"] for w in words if w["e"] <= first["s"]), default=-1.0)
        in_ = max(min(in_, first["s"] - PRE_PAD), prev_end + 0.02, first["s"] - 0.35)
    last = next((w for w in reversed(words) if w["s"] < out - 0.02), None)
    if last:
        next_start = min((w["s"] for w in words if w["s"] >= last["e"]), default=src_dur)
        out = min(max(out, last["e"] + POST_PAD), next_start - 0.02, last["e"] + 0.45)
    return round(max(0.0, in_), 3), round(min(src_dur, out), 3)


def run(root: Path, *, fps: int, width: int | None = None, height: int | None = None, snap_words: bool = True) -> dict:
    edl = load_json(root / "edit" / "edl.json", Edl)
    seg_dir = root / "build" / "cut"
    seg_dir.mkdir(parents=True, exist_ok=True)
    probes = {k: ff.probe(paths.pj(root, v)) for k, v in edl.sources.items()}
    # Hedef çözünürlük: ilk kaynağın (A-roll) kendi çözünürlüğü — kadraj sonra build'de yapılır
    first = next(iter(probes.values()))
    W = width or first["video"]["width"]
    H = height or first["video"]["height"]
    xf = edl.audio_xfade_ms / 1000
    words_cache: dict[str, list[dict]] = {}
    timemap, list_lines, t = [], [], 0.0
    for i, seg in enumerate(edl.segments):
        src_rel = edl.sources[seg.src]
        info = probes[seg.src]
        if seg.src not in words_cache:
            words_cache[seg.src] = _words_for(root, src_rel) if snap_words else []
        a, b = snap(seg.in_, seg.out, words_cache[seg.src], info["duration"])
        dur = round(b - a, 3)
        key = hashlib.sha1(f"{src_rel}|{a}|{b}|{W}x{H}@{fps}|{xf}".encode()).hexdigest()[:10]
        out = seg_dir / f"seg{i:03d}-{key}.mp4"
        if not out.exists():
            vf = (f"scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2,"
                  f"setsar=1,fps={fps}")
            af = f"afade=t=in:d={xf},afade=t=out:st={max(dur - xf, 0):.3f}:d={xf},aresample=48000"
            has_audio = "audio" in info
            args = ["-ss", f"{a:.3f}", "-t", f"{dur:.3f}", "-i", str(paths.pj(root, src_rel))]
            if not has_audio:
                args += ["-f", "lavfi", "-t", f"{dur:.3f}", "-i", "anullsrc=r=48000:cl=stereo"]
            args += ["-map", "0:v:0", "-map", "0:a:0" if has_audio else "1:a:0", "-vf", vf, "-af", af,
                     "-c:v", "libx264", "-preset", "medium", "-crf", "14", "-pix_fmt", "yuv420p",
                     "-g", str(fps), "-c:a", "aac", "-b:a", "192k", "-ac", "2", "-shortest", str(out)]
            ff.ffmpeg(*args)
        real = ff.probe(out)["duration"]
        timemap.append({"i": i, "src": seg.src, "in": a, "out": b, "start": round(t, 3),
                        "end": round(t + real, 3), "note": seg.note})
        list_lines.append(f"file '{out.name}'")
        t += real
    lst = seg_dir / "list.txt"
    lst.write_text("\n".join(list_lines) + "\n", encoding="utf-8")
    aroll = root / "build" / "aroll.mp4"
    ff.ffmpeg("-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", "-movflags", "+faststart", str(aroll))
    save_json(root / "edit" / "timemap.json", {"duration": round(t, 3), "segments": timemap})
    remap_transcript(root, edl, timemap, words_cache)
    # Eski segment dosyalarını temizle (EDL'de artık olmayanlar)
    keep = {Path(line[6:-1]).name for line in list_lines}
    for f in seg_dir.glob("seg*.mp4"):
        if f.name not in keep:
            f.unlink(missing_ok=True)
    return {"aroll": "build/aroll.mp4", "duration": round(t, 3), "segments": len(timemap)}


def remap_transcript(root: Path, edl: Edl, timemap: list[dict], words_cache: dict[str, list[dict]]) -> None:
    """Kesilmiş A-roll zamanına göre kelimeler → build/transcript_cut.json (altyazı ve SFX ipuçları için)."""
    words_out = []
    for seg in timemap:
        for w in words_cache.get(seg["src"]) or []:
            if w["s"] >= seg["in"] - 0.01 and w["e"] <= seg["out"] + 0.05:
                off = seg["start"] - seg["in"]
                words_out.append({"w": w["w"], "s": round(w["s"] + off, 3), "e": round(min(w["e"] + off, seg["end"]), 3),
                                  "p": w.get("p", 1.0)})
    save_json(root / "build" / "transcript_cut.json", {"words": words_out})


