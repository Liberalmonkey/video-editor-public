"""Referans analizi: YouTube linkleri + görseller → tempo istatistikleri, kontak sayfaları, kompakt digest.

# WHY: bkz. wiki/concepts/token-ekonomisi.md (madde 10) — referans bir kez ölçülür; yönetmen
# ajanı ham video değil, ~1–2k token'lık digest + 1–2 kontak sayfası görür ve stil gramerini çıkarır.
# Referansın içeriği değil grameri alınır (kesim temposu, metin yoğunluğu, kadraj, renk).
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

from . import ff, paths


def _ytdlp(*args: str) -> subprocess.CompletedProcess:
    exe = shutil.which("yt-dlp") or "yt-dlp"
    return subprocess.run([exe, *args], capture_output=True, text=True, encoding="utf-8", errors="replace")


def _subs_words(json3: Path) -> list[tuple[float, str]]:
    data = json.loads(json3.read_text(encoding="utf-8"))
    out = []
    for ev in data.get("events", []):
        t0 = ev.get("tStartMs", 0) / 1000
        for seg in ev.get("segs", []) or []:
            txt = seg.get("utf8", "").strip()
            if txt and txt != "\n":
                out.append((t0 + seg.get("tOffsetMs", 0) / 1000, txt))
    return out


def analyze_file(video: Path, out_dir: Path, *, minutes: float = 5.0, meta: dict | None = None) -> dict:
    # WHY: bkz. wiki/decisions/0029-stil-paneli.md — yerel referans videoları da YouTube ile aynı digest'i üretir.
    meta = meta or {}
    info = {} if ("duration" in meta and "width" in meta) else (ff.probe(video) if video.exists() else {})
    v = info.get("video") or {}
    vid = meta.get("id") or re.sub(r"[^\w\-]+", "-", video.stem, flags=re.UNICODE).strip("-") or "video"
    d = out_dir / vid
    d.mkdir(parents=True, exist_ok=True)
    total = float(meta.get("duration") or info.get("duration") or 0)
    span = min(total, minutes * 60) if total else minutes * 60
    subs = sorted(d.glob("subs*.json3"), key=lambda p: (".tr" not in p.name, "orig" not in p.name))
    words = _subs_words(subs[0]) if subs else []
    w = meta.get("width", v.get("width"))
    h = meta.get("height", v.get("height"))
    res: dict = {
        "id": vid,
        **({"url": meta["url"]} if "url" in meta else {}),
        "title": meta.get("title") or video.name,
        "channel": meta.get("channel") or "yerel",
        "duration": total,
        "analyzed_s": round(span, 1),
        "aspect": meta.get("aspect") or f"{w}x{h}",
    }
    if video.exists():
        from scenedetect import AdaptiveDetector, detect
        scenes = detect(str(video), AdaptiveDetector(), show_progress=False)
        cuts = [s[0].get_seconds() for s in scenes if s[0].get_seconds() <= span][1:]
        lens = [min(s[1].get_seconds(), span) - s[0].get_seconds() for s in scenes if s[0].get_seconds() < span] or [span]
        lens_sorted = sorted(lens)
        res["shots"] = {
            "count": len(lens), "cuts_per_min": round(len(cuts) / max(span / 60, 0.01), 1),
            "avg_shot_s": round(sum(lens) / len(lens), 2), "median_shot_s": round(lens_sorted[len(lens) // 2], 2),
            "first30_cuts": sum(1 for c in cuts if c < 30),
        }
        # Kontak sayfaları: tekdüze 4x4 + ilk 30 sn (hook) 4x2
        ff.contact_sheet(video, d / "sheet.jpg", duration=span, cols=4, rows=4, width=300)
        ff.contact_sheet(video, d / "hook.jpg", duration=min(30, span), cols=4, rows=2, width=300)
        res["sheets"] = [paths.rel(d / "sheet.jpg"), paths.rel(d / "hook.jpg")]
    if words:
        in_span = [w for w in words if w[0] <= span]
        wc = sum(len(t.split()) for _, t in in_span)
        res["speech"] = {"words_per_min": round(wc / max(span / 60, 0.01)),
                         "hook_text": " ".join(t for s, t in words if s <= 30)[:600]}
        (d / "transcript.txt").write_text(" ".join(t for _, t in words), encoding="utf-8")
        res["transcript"] = paths.rel(d / "transcript.txt")
    (d / "digest.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    return res


def analyze_url(url: str, out_dir: Path, *, minutes: float = 5.0) -> dict:
    meta_p = _ytdlp("--dump-json", "--no-playlist", url)
    if meta_p.returncode != 0:
        raise RuntimeError(f"yt-dlp meta alınamadı: {meta_p.stderr[-400:]}")
    meta = json.loads(meta_p.stdout.splitlines()[0])
    vid = meta["id"]
    d = out_dir / vid
    d.mkdir(parents=True, exist_ok=True)
    total = float(meta.get("duration") or 0)
    span = min(total, minutes * 60) if total else minutes * 60
    video = d / "ref.mp4"
    if not video.exists():
        r = _ytdlp("-f", "bv*[height<=360][ext=mp4]/bv*[height<=480]/b[height<=480]", "--no-playlist",
                   "--download-sections", f"*0-{int(span) + 1}", "-o", str(video), url)
        if not video.exists():  # sessizce eksik digest üretmek yerine nedenini söyle
            raise RuntimeError(f"video indirilemedi (yt-dlp {r.returncode}): {(r.stderr or r.stdout).strip()[-300:]}")
    _ytdlp("--skip-download", "--write-subs", "--write-auto-subs", "--sub-langs", "tr.*,en.*,tr,en",
           "--sub-format", "json3", "--no-playlist", "-o", str(d / "subs"), url)
    return analyze_file(video, out_dir, minutes=minutes, meta={**meta, "url": url})


def image_grid(images: list[Path], out: Path, *, cell: int = 420, cols: int = 4) -> Path:
    tmp = out.parent / "_grid_tmp"
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True)
    for i, img in enumerate(images):
        ff.ffmpeg("-i", str(img), "-vf", f"scale={cell}:{cell}:force_original_aspect_ratio=decrease,"
                  f"pad={cell}:{cell}:(ow-iw)/2:(oh-ih)/2:color=0x202020", str(tmp / f"img{i:03d}.png"))
    rows = (len(images) + cols - 1) // cols
    ff.ffmpeg("-framerate", "1", "-i", str(tmp / "img%03d.png"), "-vf", f"tile={cols}x{rows}:padding=6:color=0x101010",
              "-frames:v", "1", str(out))
    shutil.rmtree(tmp, ignore_errors=True)
    return out


def run(out_dir: Path, urls: list[str], images: list[Path], *, minutes: float = 5.0, videos: list[Path] = ()) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    results = {"videos": [], "images": None, "errors": []}
    for u in urls:
        try:
            results["videos"].append(analyze_url(u, out_dir, minutes=minutes))
        except Exception as e:
            results["errors"].append(f"{u}: {e}")
    for v in videos:
        try:
            results["videos"].append(analyze_file(Path(v), out_dir, minutes=minutes))
        except Exception as e:
            results["errors"].append(f"{v}: {e}")
    if images:
        results["images"] = paths.rel(image_grid(images, out_dir / "images-grid.jpg"))
    (out_dir / "digest.md").write_text(digest_md(results), encoding="utf-8")
    return results


def digest_md(r: dict) -> str:
    lines = ["# Referans digest (yönetmen ajanı için)"]
    for v in r["videos"]:
        s, sp = v.get("shots", {}), v.get("speech", {})
        lines.append(f"\n## {v['title']} — {v.get('channel')} ({v['duration'] / 60:.1f} dk, {v['aspect']}, ilk "
                     f"{v['analyzed_s'] / 60:.1f} dk analiz)")
        if s:
            lines.append(f"- Tempo: {s['cuts_per_min']} kesim/dk · ort. çekim {s['avg_shot_s']}s · medyan "
                         f"{s['median_shot_s']}s · ilk 30 sn'de {s['first30_cuts']} kesim")
        if sp:
            lines.append(f"- Konuşma: {sp['words_per_min']} kelime/dk")
            lines.append(f"- Hook (ilk 30 sn): {sp['hook_text']}")
        if v.get("sheets"):
            lines.append(f"- Kontak: {', '.join(v['sheets'])}")
    if r.get("images"):
        lines.append(f"\n## Referans görseller\n- Izgara: {r['images']}")
    for e in r["errors"]:
        lines.append(f"- HATA: {e}")
    return "\n".join(lines) + "\n"

