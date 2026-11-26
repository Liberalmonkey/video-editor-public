"""Teslim: platform varyantları (yeniden build + render), SRT, YouTube bölüm listesi,
atıf listesi (credits.txt); hepsi Projeler/outputs/<stüdyo>/<proje>/ klasörüne de konur."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from . import build, paths, project, render
from .schemas import Format, Timeline, load_json


def chapters_text(tl: Timeline) -> str:
    def ts(t: float) -> str:
        m, s = divmod(int(t), 60)
        h, m = divmod(m, 60)
        return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"
    chs = sorted(tl.chapters, key=lambda c: c.start)
    if chs and chs[0].start > 0:
        chs[0] = chs[0].model_copy(update={"start": 0})
    return "\n".join(f"{ts(c.start)} {c.title or c.id}" for c in chs)


def credits(root: Path, tl: Timeline) -> list[str]:
    """Timeline'da kullanılan müzik/motion/SFX'in atıf satırları (manifest'lerdeki `attribution` alanı)."""
    known: dict[str, dict] = {}
    for man in (paths.MUSIC_DIR / "manifest.json", paths.MOTION_DIR / "manifest.json",
                paths.SFX_DIR / "manifest.json"):
        if man.exists():
            for e in json.loads(man.read_text(encoding="utf-8")).get("entries", []):
                known[Path(e.get("file", "")).as_posix()] = e
    used = [c.src for c in tl.audio.music] + [c.src for c in tl.video]
    resolved = root / "audio" / "sfx_resolved.json"
    if resolved.exists():
        used += [c["file"] for c in json.loads(resolved.read_text(encoding="utf-8"))["cues"] if c.get("file")]
    lines = []
    for src in dict.fromkeys(Path(u).as_posix() for u in used):
        e = known.get(src)
        if e and e.get("attribution") and e["attribution"] not in lines:
            lines.append(e["attribution"])
    return lines


def deliver(root: Path, proj, files: list[Path]) -> Path:
    """Teslim dosyalarını work/ üstündeki proje klasörüne koy (aynı diskte hardlink, yer kaplamaz)."""
    dest = root.resolve().parent
    dest.mkdir(parents=True, exist_ok=True)
    for f in files:
        # final.mp4 → <proje-id>.mp4, final_9x16.mp4 → <proje-id>_9x16.mp4
        dst = dest / (proj.id + f.name[5:] if f.name.startswith("final") else f.name)
        dst.unlink(missing_ok=True)
        try:
            dst.hardlink_to(f)
        except OSError:
            shutil.copy2(f, dst)
    return dest


def run(root: Path, *, variants: list[str] | None = None) -> dict:
    proj = project.load(root)
    studio = project.studio_for(proj)
    tl = load_json(root / "edit" / "timeline.json", Timeline)
    final = root / "renders" / "final.mp4"
    if not final.exists():
        raise SystemExit("Önce final render: vedit render final")
    res: dict = {"final": "renders/final.mp4", "variants": []}
    srt = root / "edit" / "captions.srt"
    if srt.exists():
        shutil.copy2(srt, root / "renders" / f"{proj.id}.srt")
        res["srt"] = f"renders/{proj.id}.srt"
    if tl.chapters:
        (root / "renders" / "youtube-chapters.txt").write_text(chapters_text(tl), encoding="utf-8")
        res["chapters"] = "renders/youtube-chapters.txt"
    wanted = [v for v in studio.variants if not variants or v.name in variants]
    for v in wanted:
        fmt = Format(width=v.width, height=v.height, fps=tl.format.fps)
        name = f"comp_{v.name}"
        build.run(root, fmt_override=fmt, out_name=name, lint=False)
        silent = root / "renders" / f".{v.name}.video.mp4"
        render._render_one(root / name, silent, "delivery", fmt.fps)
        out = root / "renders" / f"final_{v.name}.mp4"
        render.mux(silent, root / "build" / "master.wav", out)
        silent.unlink(missing_ok=True)
        res["variants"].append(f"renders/{out.name}")
    cred = credits(root, tl)
    if cred:
        (root / "renders" / "credits.txt").write_text("\n".join(cred) + "\n", encoding="utf-8")
        res["credits"] = "renders/credits.txt"
    files = [root / res["final"], *(root / v for v in res["variants"])]
    files += [root / res[k] for k in ("srt", "chapters", "credits") if k in res]
    res["delivery"] = paths.rel(deliver(root, proj, files))
    (root / "renders" / "export.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    return res
