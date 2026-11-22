"""Animasyon hattı: yönetmenin scenes.json'unu seslendirmeye hizala ve timeline.json'a çevir.

align: her sahnenin `vo_from` (sahneyi başlatan cümlenin ilk kelimeleri) metni, transkriptte bulanık
eşleşmeyle bulunur → start/dur doldurulur. Kaynak rehberdeki "Whisper kelime zamanları sahne
sürelerini belirler" fikri.
scenes2timeline: blok sahneler deterministik olarak overlay'e dönüşür; custom/hero sahneler
edit/custom/<sahne>.html dosyasına işaret eder (ana oturum yazar).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from rapidfuzz import fuzz

from .schemas import (AudioClip, AudioTracks, CaptionTrack, Chapter, Format, Overlay, Scenes, Timeline,
                      load_json, save_json)

_P = re.compile(r"[^\wçğıöşü%]+", re.I)


def _n(w: str) -> str:
    return _P.sub("", w.lower().replace("İ", "i").replace("I", "ı"))


def vo_words(root: Path) -> list[dict]:
    tr = json.loads((root / "analysis" / "transcript.json").read_text(encoding="utf-8"))
    data = tr["files"].get("vo") or next(iter(tr["files"].values()))
    return [w for s in data["segments"] for w in s["words"] if _n(w["w"])]


def align(root: Path, *, lead: float = 0.12, tail: float = 1.2) -> dict:
    sc = load_json(root / "direction" / "scenes.json", Scenes)
    words = vo_words(root)
    toks = [_n(w["w"]) for w in words]
    cursor, low = 0, []
    starts: list[float | None] = []
    for s in sc.scenes:
        if not s.vo_from:
            starts.append(None)
            continue
        q = [_n(x) for x in s.vo_from.split() if _n(x)][:7]
        qs = " ".join(q)
        best, best_i = -1.0, None
        horizon = min(len(toks), cursor + 900)
        for i in range(cursor, horizon):
            cand = " ".join(toks[i:i + len(q)])
            score = fuzz.ratio(qs, cand)
            if score > best:
                best, best_i = score, i
                if score >= 97:
                    break
        if best_i is None or best < 60:
            low.append(f"{s.id}: eşleşmedi (en iyi %{best:.0f}) — «{s.vo_from[:40]}»")
            starts.append(None)
            continue
        if best < 80:
            low.append(f"{s.id}: zayıf eşleşme %{best:.0f}")
        starts.append(max(0.0, words[best_i]["s"] - lead))
        cursor = best_i + 1
    end_all = (words[-1]["e"] + tail) if words else sum(s.dur or 3 for s in sc.scenes)
    # Eşleşmeyenleri komşuların arasına eşit dağıt
    filled = list(starts)
    if filled and filled[0] is None:
        filled[0] = 0.0
    i = 0
    while i < len(filled):
        if filled[i] is None:
            j = i
            while j < len(filled) and filled[j] is None:
                j += 1
            a = filled[i - 1]
            b = filled[j] if j < len(filled) else end_all
            for k in range(i, j):
                filled[k] = a + (b - a) * (k - i + 1) / (j - i + 1)
            i = j
        else:
            i += 1
    filled[0] = 0.0
    for k, s in enumerate(sc.scenes):
        nxt = filled[k + 1] if k + 1 < len(filled) else end_all
        s.start = round(filled[k], 3)
        s.dur = round(max(nxt - filled[k], 0.6), 3)
    save_json(root / "direction" / "scenes.aligned.json", sc)
    return {"scenes": len(sc.scenes), "duration": round(end_all, 2), "warnings": low}


def scenes2timeline(root: Path, fmt: Format, *, burn_captions: bool, caption_style: str | None = None) -> dict:
    sc = load_json(root / "direction" / "scenes.aligned.json", Scenes)
    duration = round(max(s.start + s.dur for s in sc.scenes), 3)
    prev_path = root / "edit" / "timeline.json"
    prev = load_json(prev_path, Timeline) if prev_path.exists() else None
    overlays: list[Overlay] = []
    placeholders = []
    has_bg = any(b.get("block") == "bg" for s in sc.scenes for b in s.blocks)
    if not has_bg:
        overlays.append(Overlay(id="bg-main", block="bg", start=0, dur=duration, props={"kind": "soft", "drift": "slow"}, z=0))
    chapters: dict[str, list[float]] = {}
    titles: dict[str, str] = {}
    for s in sc.scenes:
        end = s.start + s.dur
        ch = chapters.setdefault(s.chapter, [s.start, end])
        ch[0], ch[1] = min(ch[0], s.start), max(ch[1], end)
        if s.complexity in ("custom", "hero"):
            custom = root / "edit" / "custom" / f"{s.id}.html"
            if custom.exists():
                overlays.append(Overlay(id=f"{s.id}-custom", block="custom", src=f"edit/custom/{s.id}.html",
                                        start=s.start, dur=s.dur, z=5))
            else:
                placeholders.append(s.id)
                overlays.append(Overlay(id=f"{s.id}-ph", block="kinetic-text", start=s.start, dur=s.dur,
                                        props={"text": f"[{s.id}] {s.intent}"[:90], "size": "m"}, z=5))
        for k, b in enumerate(s.blocks):
            at = float(b.get("at", 0))
            st = round(s.start + at, 3)
            d = b.get("dur")
            d = round(min(float(d), end - st) if d else end - st, 3)
            if d <= 0.05:
                continue
            if b.get("block") == "chapter-card" and b.get("props", {}).get("title"):
                titles.setdefault(s.chapter, b["props"]["title"])
            overlays.append(Overlay(id=f"{s.id}-b{k}", block=b["block"], start=st, dur=d,
                                    props=b.get("props", {}), z=int(b.get("z", 10)), src=b.get("src")))
    chs = [Chapter(id=cid, title=titles.get(cid, ""), start=round(a, 3), end=round(b, 3))
           for cid, (a, b) in sorted(chapters.items(), key=lambda kv: kv[1][0])]
    tl = Timeline(format=fmt, duration=duration, style=sc.style, chapters=chs if len(chs) > 1 else [],
                  overlays=overlays,
                  captions=CaptionTrack(style=caption_style, enabled=burn_captions),
                  audio=prev.audio if prev else AudioTracks())
    if not tl.audio.voice:
        tl.audio.voice = [AudioClip(id="vo", src="build/voice.wav")]
    save_json(prev_path, tl)
    return {"overlays": len(overlays), "chapters": len(chs), "duration": duration, "placeholders": placeholders}
