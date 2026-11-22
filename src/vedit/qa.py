"""Otomatik kalite kontrol — eleştirmen ajanından ÖNCE çalışır (sıfır token).

Kontroller: loudness/true peak, siyah kare, donuk kare, uzun sessizlik, süre hedefi, SFX yoğunluğu,
altyazı sayfa hızı, TR glif desteği, HyperFrames lint. Çıktı: qa/report.json + qa/sheet.jpg.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from fontTools.ttLib import TTFont

from . import ff, paths, project
from .schemas import Timeline, load_json

TR_CHARS = set("İıŞşĞğÜüÖöÇç")


def _detect(path: Path, vf: str, key: str) -> list[tuple[float, float]]:
    proc = ff.ffmpeg("-i", str(path), "-vf", vf, "-an", "-f", "null", "-", check=False)
    out = []
    for line in (proc.stderr or "").splitlines():
        if key == "black" and "black_start" in line:
            m = re.search(r"black_start:([\d.]+).*black_end:([\d.]+)", line)
            if m:
                out.append((float(m.group(1)), float(m.group(2))))
        elif key == "freeze" and "freeze_start" in line:
            out.append((float(line.split("freeze_start:")[1].split()[0]), -1.0))
        elif key == "freeze" and "freeze_end" in line and out:
            out[-1] = (out[-1][0], float(line.split("freeze_end:")[1].split()[0]))
    return out


def glyph_issues(root: Path, tl: Timeline, tokens: dict) -> list[str]:
    """Kullanılan metinlerdeki her karakter stil fontlarında var mı?"""
    reg = json.loads((paths.FONTS_DIR / "fonts.json").read_text(encoding="utf-8"))
    texts = []
    for o in tl.overlays:
        texts += [str(v) for v in o.props.values() if isinstance(v, (str, int, float))]
        texts += [str(x) for v in o.props.values() if isinstance(v, list) for x in v]
    cap = root / "edit" / "captions.json"
    if cap.exists():
        texts += [p["text"] for p in json.loads(cap.read_text(encoding="utf-8"))["pages"]]
    chars = {c for t in texts for c in t if not c.isspace()} | TR_CHARS
    issues = []
    for role in ("display", "body"):
        fam = tokens["fonts"][role]
        if fam not in reg:
            issues.append(f"font '{fam}' library/fonts'ta yok")
            continue
        cmap = TTFont(paths.FONTS_DIR / reg[fam]["file"]).getBestCmap()
        miss = sorted(c for c in chars if ord(c) not in cmap and ord(c) > 0x20)
        if miss:
            issues.append(f"{fam} ({role}) eksik glifler: {''.join(miss[:20])}")
    return issues


def run(root: Path, *, video: Path | None = None) -> dict:
    from .build import load_tokens

    proj = project.load(root)
    studio = project.studio_for(proj)
    tl = load_json(root / "edit" / "timeline.json", Timeline)
    video = video or root / "renders" / "preview.mp4"
    rep: dict = {"video": paths.rel(video), "checks": [], "fails": 0, "warns": 0}

    def check(name: str, ok: bool, detail: str, *, warn_only: bool = False):
        level = "ok" if ok else ("warn" if warn_only else "fail")
        rep["checks"].append({"name": name, "level": level, "detail": detail})
        if level == "fail":
            rep["fails"] += 1
        elif level == "warn":
            rep["warns"] += 1

    info = ff.probe(video)
    dur = info["duration"]
    v = info.get("video", {})
    check("format", v.get("width") == tl.format.width and v.get("height") == tl.format.height,
          f"{v.get('width')}x{v.get('height')}@{v.get('fps')} (hedef {tl.format.width}x{tl.format.height})")
    check("süre", abs(dur - tl.duration) < 0.25, f"{dur:.2f}s (timeline {tl.duration:.2f}s)")
    lo, hi = studio.target_duration
    check("hedef süre", lo * 0.8 <= dur <= hi * 1.25, f"{dur:.0f}s (stüdyo hedefi {lo:.0f}–{hi:.0f}s)", warn_only=True)

    L = ff.loudness(video)
    tgt = studio.loudness
    if L:
        check("loudness", abs(L["I"] - tgt.integrated) <= 1.0, f"{L['I']:.1f} LUFS (hedef {tgt.integrated})")
        check("true peak", L["TP"] <= tgt.true_peak + 0.2, f"{L['TP']:.1f} dBTP (en fazla {tgt.true_peak})")
    else:
        check("ses", False, "ses akışı yok ya da ölçülemedi")

    blacks = [b for b in _detect(video, "blackdetect=d=0.25:pix_th=0.02:pic_th=0.995", "black") if not (b[0] < 0.05 and b[1] < 0.6)]
    check("siyah kare", not blacks, ", ".join(f"{a:.2f}–{b:.2f}" for a, b in blacks[:6]) or "yok")
    freezes = [f for f in _detect(video, "freezedetect=n=0.001:d=3.5", "freeze") if f[1] - f[0] >= 3.5 or f[1] < 0]
    check("donuk görüntü (≥3.5s)", not freezes, ", ".join(f"{a:.1f}–{b:.1f}" for a, b in freezes[:6]) or "yok",
          warn_only=True)
    if info.get("audio"):
        sil = [s for s in ff.silences(video, noise_db=-45, min_dur=1.5) if s[0] > 0.3 and s[1] < dur - 0.3]
        check("uzun sessizlik (≥1.5s)", not sil, ", ".join(f"{a:.1f}–{b:.1f}" for a, b in sil[:6]) or "yok",
              warn_only=True)

    sfx_file = root / "audio" / "sfx_resolved.json"
    if sfx_file.exists():
        ts = sorted(c["t"] for c in json.loads(sfx_file.read_text(encoding="utf-8"))["cues"] if c.get("file"))
        dense = [round(b, 2) for a, b in zip(ts, ts[1:]) if b - a < 0.4]
        check("SFX yoğunluğu", not dense, f"{len(ts)} SFX; <0.4s aralık: {dense[:6] or 'yok'}", warn_only=True)

    cap = root / "edit" / "captions.json"
    if cap.exists() and json.loads(cap.read_text(encoding="utf-8")).get("style") == "clean-sub":
        # Kelime-pop stillerinde sayfa zaten konuşmaya kilitli; okuma hızı yalnızca cümle altyazısında anlamlı
        pages = json.loads(cap.read_text(encoding="utf-8"))["pages"]
        fast = [round(p["start"], 1) for p in pages if len(p["text"]) / max(p["end"] - p["start"], 0.01) > 22]
        check("altyazı okuma hızı (≤22 kr/sn)", not fast, f"hızlı sayfalar: {fast[:8] or 'yok'}", warn_only=True)

    cap_style = (tl.captions.style if tl.captions else None) or (
        json.loads(cap.read_text(encoding="utf-8")).get("style") if cap.exists() else None)
    check("altyazı standardı", bool(tl.captions and tl.captions.enabled and cap_style == "odak"),
          f"stil {cap_style}, gömülü {bool(tl.captions and tl.captions.enabled)} (standart: odak, gömülü)", warn_only=True)

    tokens = load_tokens(root, tl.style or proj.style)
    gi = glyph_issues(root, tl, tokens)
    check("TR glif", not gi, "; ".join(gi) or "tüm karakterler fontlarda var")

    man = root / "build" / "comp_manifest.json"
    if man.exists():
        m = json.loads(man.read_text(encoding="utf-8"))
        lint = m.get("lint", {})
        check("hyperframes lint", not lint.get("errors"), f"{lint.get('errors', '?')} hata, {lint.get('warnings', '?')} uyarı"
              + (f": {lint['top'][:3]}" if lint.get("top") else ""))
        if m.get("errors"):
            check("build", False, "; ".join(m["errors"][:5]))

    sheet = root / "qa" / "sheet.jpg"
    cols, rows = (5, 4) if dur > 120 else (4, 4)
    ff.contact_sheet(video, sheet, duration=dur, cols=cols, rows=rows,
                     width=260 if tl.format.height > tl.format.width else 360)
    rep["sheet"] = paths.rel(sheet)
    rep["loudness"] = L
    (root / "qa").mkdir(exist_ok=True)
    (root / "qa" / "report.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    return rep


def summary(rep: dict) -> str:
    icon = {"ok": "✓", "warn": "!", "fail": "✗"}
    lines = [f"QA: {rep['fails']} hata, {rep['warns']} uyarı — {rep['video']}"]
    lines += [f" {icon[c['level']]} {c['name']}: {c['detail']}" for c in rep["checks"]]
    lines.append(f"Kontak sayfası: {rep['sheet']}")
    return "\n".join(lines)
