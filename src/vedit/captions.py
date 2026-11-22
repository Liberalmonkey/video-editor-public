"""Kelime zamanlarından altyazı sayfaları (captions.json) + SRT.

Sayfa kırma kuralları: karakter/kelime sınırı, 0.45 sn üstü duraklama, cümle sonu noktalaması.
Reels stili (bold-pop) kısa sayfalar (1–3 kelime), YouTube stili (clean-sub) cümle parçaları.
"""

from __future__ import annotations

import json
from pathlib import Path

from .schemas import CaptionCfg

# WHY: odak her videonun standart stili, bkz. wiki/decisions/0014-altyazi-standardi-ve-repo-entegrasyonu.md
STYLE_LIMITS = {"odak": (26, 5), "bold-pop": (14, 3), "karaoke": (26, 5), "clean-sub": (42, 9), "underline": (40, 7)}
END_PUNCT = (".", "?", "!", "…", ":")


def source_words(root: Path, pipeline: str) -> list[dict]:
    cut = root / "build" / "transcript_cut.json"
    if pipeline != "animation" and cut.exists():
        return json.loads(cut.read_text(encoding="utf-8"))["words"]
    tr = json.loads((root / "analysis" / "transcript.json").read_text(encoding="utf-8"))
    # Animasyonda seslendirme dosyası (vo) tek kaynak; yoksa ilk dosya
    files = tr["files"]
    data = files.get("vo") or next(iter(files.values()))
    return [w for s in data["segments"] for w in s["words"]]


def paginate(words: list[dict], cfg: CaptionCfg, style: str) -> list[dict]:
    max_chars, max_words = STYLE_LIMITS.get(style, (cfg.max_chars, cfg.max_words))
    max_chars = min(max_chars, cfg.max_chars * max(cfg.lines, 1)) if style == "clean-sub" else max_chars
    pages, cur = [], []

    def flush():
        if cur:
            pages.append({"start": cur[0]["s"], "end": cur[-1]["e"], "text": " ".join(w["w"] for w in cur),
                          "words": [{"w": w["w"], "s": w["s"], "e": w["e"]} for w in cur]})
            cur.clear()

    for i, w in enumerate(words):
        if cur:
            chars = sum(len(x["w"]) + 1 for x in cur) + len(w["w"])
            gap = w["s"] - cur[-1]["e"]
            if chars > max_chars or len(cur) >= max_words or gap > 0.45 or \
                    (cur[-1]["w"].endswith(END_PUNCT) and len(cur) >= 2):
                flush()
        cur.append(w)
    flush()
    # Sayfa sürelerini düzelt: bir sonrakine kadar uzat (en fazla +0.35 sn), en az 0.5 sn
    for i, p in enumerate(pages):
        nxt = pages[i + 1]["start"] if i + 1 < len(pages) else p["end"] + 0.6
        p["end"] = round(min(max(p["end"] + 0.15, p["start"] + 0.5), nxt - 0.02, p["end"] + 0.35)
                         if nxt - 0.02 > p["start"] else p["end"], 3)
        p["start"] = round(p["start"], 3)
    return pages


def srt_time(t: float) -> str:
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def to_srt(pages: list[dict]) -> str:
    return "\n".join(f"{i}\n{srt_time(p['start'])} --> {srt_time(p['end'])}\n{p['text']}\n"
                     for i, p in enumerate(pages, 1))


def run(root: Path, *, pipeline: str, cfg: CaptionCfg, style: str | None = None) -> dict:
    words = [w for w in source_words(root, pipeline) if w["w"].strip()]
    st = style or cfg.style
    pages = paginate(words, cfg, st)
    out = root / "edit" / "captions.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"style": st, "pages": pages}, ensure_ascii=False, indent=1), encoding="utf-8")
    # SRT her zaman cümle düzeyinde (platform altyazısı için okunaklı)
    srt_pages = paginate(words, cfg, "clean-sub")
    (root / "edit" / "captions.srt").write_text(to_srt(srt_pages), encoding="utf-8")
    return {"pages": len(pages), "style": st, "words": len(words), "srt": "edit/captions.srt"}
