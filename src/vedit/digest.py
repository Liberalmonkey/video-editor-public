"""LLM için kompakt transkript özeti (digest).

# WHY: bkz. wiki/concepts/token-ekonomisi.md — ana oturum ham transkript JSON'u (kelime
# başına 4 alan) yerine segment düzeyinde, işaretli düz metin okur. Tipik oran ~8–10x daha az token.

Biçim:
  ## take1.mp4 · 95.2s · tr
  S001 00:00.0–00:04.2 Merhaba arkadaşlar bugün…
     ~1.3s
  S002 00:05.5–00:09.0 … [dolgu: ıı×2]
  S003 00:09.4–00:12.0 … [↻ S005 ile %88 benzer → muhtemel kötü take]
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from rapidfuzz import fuzz

HARD_FILLERS = {"ıı", "ııı", "ıım", "ee", "eee", "eh", "hmm", "hım", "mmm", "um", "uh", "uhm", "erm", "ah", "eeh"}
SOFT_FILLERS = {"yani", "şey", "hani", "işte", "like", "basically", "actually"}
_PUNCT = re.compile(r"[^\wçğıöşü]+", re.I)


def fmt_t(t: float) -> str:
    m, s = divmod(t, 60)
    return f"{int(m):02d}:{s:04.1f}"


def _norm(w: str) -> str:
    return _PUNCT.sub("", w.lower().replace("I", "ı").replace("İ", "i"))


def digest_file(name: str, data: dict, *, gap_mark: float = 0.6, retake_window: int = 6,
                retake_threshold: int = 75) -> str:
    segs = data["segments"]
    lines = [f"## {name} · {data['duration']:.1f}s · {data['language']}"]
    norm_texts = [" ".join(_norm(w["w"]) for w in s["words"]) for s in segs]
    retake_of: dict[int, tuple[int, int]] = {}
    for i, a in enumerate(norm_texts):
        if len(a) < 12:
            continue
        for j in range(i + 1, min(i + 1 + retake_window, len(segs))):
            b = norm_texts[j]
            score = fuzz.partial_ratio(a, b) if min(len(a), len(b)) > 20 else fuzz.ratio(a, b)
            if score >= retake_threshold:
                retake_of[i] = (j, int(score))
                break
    prev_end = 0.0
    for i, s in enumerate(segs):
        gap = s["start"] - prev_end
        if gap >= gap_mark:
            lines.append(f"   ~{gap:.1f}s")
        hard = [w["w"] for w in s["words"] if _norm(w["w"]) in HARD_FILLERS]
        soft = [w["w"] for w in s["words"] if _norm(w["w"]) in SOFT_FILLERS]
        low = [w["w"] for w in s["words"] if w["p"] < 0.4]
        tags = []
        if hard:
            tags.append(f"dolgu: {'/'.join(sorted({_norm(h) for h in hard}))}×{len(hard)}")
        if len(soft) >= 2:
            tags.append(f"yumuşak dolgu×{len(soft)}")
        if len(low) >= 3:
            tags.append(f"düşük güven×{len(low)}")
        if i in retake_of:
            j, sc = retake_of[i]
            tags.append(f"↻ {segs[j]['id']} ile %{sc} benzer → muhtemel kötü take")
        tag = f" [{'; '.join(tags)}]" if tags else ""
        lines.append(f"{s['id']} {fmt_t(s['start'])}–{fmt_t(s['end'])} {s['text']}{tag}")
        prev_end = s["end"]
    tail = data["duration"] - prev_end
    if tail >= gap_mark:
        lines.append(f"   ~{tail:.1f}s (son)")
    return "\n".join(lines)


def run(root: Path) -> tuple[Path, int]:
    tr = json.loads((root / "analysis" / "transcript.json").read_text(encoding="utf-8"))
    index = json.loads((root / "analysis" / "media_index.json").read_text(encoding="utf-8"))
    by_stem = {Path(i["file"]).stem: i for i in index["files"]}
    parts = ["# Medya"]
    for i in index["files"]:
        v = i.get("video")
        vs = f" {v['width']}x{v['height']}@{v['fps']:g}" if v else ""
        parts.append(f"- {i['file']} · {i['kind']}/{i['role']} · {i['duration']:.1f}s{vs}"
                     + (f" · sheet: {i['sheet']}" if i.get("sheet") else ""))
    parts.append("\n# Transkript (segment id'leri EDL'de not olarak kullanılabilir; zamanlar kaynak saniyesi)")
    for stem, data in tr["files"].items():
        name = by_stem.get(stem, {}).get("file", stem)
        parts.append(digest_file(name, data))
    text = "\n".join(parts) + "\n"
    out = root / "analysis" / "digest.txt"
    out.write_text(text, encoding="utf-8")
    return out, len(text) // 4
