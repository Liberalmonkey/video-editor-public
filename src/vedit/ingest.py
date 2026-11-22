"""input/ envanteri: ffprobe, rol tahmini, kontak sayfası, 16 kHz ses çıkarımı."""

from __future__ import annotations

import json
import re
from pathlib import Path

from . import ff, paths

MEDIA_EXT = {".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v", ".mp3", ".wav", ".m4a", ".aac", ".flac",
             ".ogg", ".png", ".jpg", ".jpeg", ".webp"}
SCREEN_RE = re.compile(r"(screen|ekran|kayit|kayıt|record|rec|capture|demo)", re.I)
BROWSER_SAFE = {"h264", "vp9", "av1", "vp8"}


def guess_role(info: dict) -> str:
    kind = ff.kind_of(info)
    if kind != "video":
        return {"audio": "audio", "image": "image"}.get(kind, "other")
    name = info["file"]
    if SCREEN_RE.search(name):
        return "screen"
    v = info["video"]
    if "audio" not in info:
        return "broll"
    # Dikey ya da sesli kamera çekimi → büyük olasılıkla konuşan kafa
    return "talking" if v["height"] >= v["width"] or info["duration"] > 20 else "broll"


def run(root: Path, *, sheets: bool = True) -> dict:
    files = sorted(p for p in paths.input_dir(root).iterdir()
                   if p.is_file() and p.suffix.lower() in MEDIA_EXT and not p.name.startswith("."))
    if not files:
        raise SystemExit(f"Girdi boş. Çekimleri, ekran kayıtlarını ve sesleri {paths.rel(paths.input_dir(root))} klasörüne koy.")
    index = {"files": []}
    for f in files:
        info = ff.probe(f)
        info["kind"] = ff.kind_of(info)
        info["role"] = guess_role(info)
        info["path"] = f"input/{f.name}"
        if info["kind"] == "video":
            info["needs_transcode"] = info["video"]["codec"] not in BROWSER_SAFE or info["video"]["rotation"] != 0
            if sheets:
                sheet = root / "analysis" / "sheets" / f"{f.stem}.jpg"
                if not sheet.exists() or sheet.stat().st_mtime < f.stat().st_mtime:
                    ff.contact_sheet(f, sheet, duration=info["duration"])
                info["sheet"] = paths.rel(sheet)
        if "audio" in info and info["kind"] in ("video", "audio"):
            wav = root / "analysis" / "audio" / f"{f.stem}.wav"
            if not wav.exists() or wav.stat().st_mtime < f.stat().st_mtime:
                ff.extract_audio(f, wav)
            info["wav"] = f"analysis/audio/{f.stem}.wav"
        index["files"].append(info)
    out = root / "analysis" / "media_index.json"
    out.write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")
    return index


def summary(index: dict) -> str:
    lines = []
    for i in index["files"]:
        v = i.get("video")
        vs = f"{v['width']}x{v['height']}@{v['fps']:g} {v['codec']}" if v else "-"
        a = "ses" if "audio" in i else "sessiz"
        tc = " ⚠transcode" if i.get("needs_transcode") else ""
        lines.append(f"- {i['file']}: {i['kind']}/{i['role']} {i['duration']:.1f}s {vs} {a}{tc}")
    return "\n".join(lines)
