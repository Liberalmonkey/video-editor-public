"""Transkript düzeltme sözlüğü: Whisper'ın karıştırdığı özel adları düzeltir ("cloud code" → "Claude Code").

WHY: bkz. wiki/decisions/0041-avenox-kurgu-dersleri.md. Modeller sesi duyamaz; altyazı, kesim ve grafik zamanlaması
transkriptten çıkar. Ad hatası her videoda aynı yerden geri gelir, bu yüzden düzeltme kod olur, not değil.

`library/sozluk.json`:
  isimler: Whisper'a ipucu (`initial_prompt`) olarak verilen doğru yazımlar; `--prompt` verilirse o kazanır.
  duzelt:  "yanlış ifade" → "doğru ifade". Anahtar bir ya da birkaç kelimedir, büyük-küçük harf ve noktalama yok sayılır.
           Tek başına gerçek bir kelime olan anahtar (ör. yalnız "cloud") konmaz: her geçişini değiştirir.

Önbellekteki ham transkript değişmez; sözlük her okumada uygulanır, sözlük güncellenince yeniden transkript gerekmez.
"""

from __future__ import annotations

import copy
import json
import re
from functools import lru_cache
from pathlib import Path

from . import paths

DOSYA = paths.ROOT / "library" / "sozluk.json"


def _norm(s: str) -> str:
    return re.sub(r"[^\w]+", "", s.casefold())


@lru_cache(maxsize=4)
def _oku(yol: str, mtime: float) -> dict:
    try:
        d = json.loads(Path(yol).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"isimler": [], "duzelt": {}}
    return {"isimler": [str(x) for x in d.get("isimler", [])], "duzelt": {str(a): str(b) for a, b in d.get("duzelt", {}).items()}}


def yukle(yol: Path = DOSYA) -> dict:
    try:
        mt = yol.stat().st_mtime
    except OSError:
        return {"isimler": [], "duzelt": {}}
    return _oku(str(yol), mt)


def ipucu(s: dict | None = None) -> str | None:
    """Whisper `initial_prompt`: doğru yazımlar virgülle. Boşsa None."""
    isimler = (s or yukle())["isimler"]
    return ", ".join(isimler) + "." if isimler else None


def _kurallar(s: dict) -> list[tuple[list[str], str, re.Pattern]]:
    """Uzun anahtar önce: "claude code" kuralı "code" kuralından önce denenir."""
    out = []
    for yanlis, dogru in s["duzelt"].items():
        tok = [_norm(x) for x in yanlis.split() if _norm(x)]
        if tok:
            desen = re.compile(r"(?<!\w)" + r"[\s\-]+".join(re.escape(x) for x in yanlis.split()) + r"(?!\w)", re.I)
            out.append((tok, dogru, desen))
    return sorted(out, key=lambda k: -len(k[0]))


def _kelimeler(words: list[dict], kurallar) -> list[dict]:
    out, i = [], 0
    while i < len(words):
        for tok, dogru, _ in kurallar:
            n = len(tok)
            if [_norm(w["w"]) for w in words[i:i + n]] == tok:
                son = words[i + n - 1]
                kuyruk = re.search(r"[^\w]*$", son["w"]).group(0)  # "code," → virgül kalır
                yeni = {**words[i], "w": dogru + kuyruk, "e": son["e"]}
                if "p" in words[i]:
                    yeni["p"] = min(w.get("p", 1) for w in words[i:i + n])
                out.append(yeni)
                i += n
                break
        else:
            out.append(words[i])
            i += 1
    return out


def uygula(t: dict, s: dict | None = None) -> dict:
    """Transkript (`segments` [{text, words}]) kopyasını düzeltir. Kelime zamanları korunur: birleşen kelimeler ilkinin
    başından sonuncunun sonuna uzanır."""
    kurallar = _kurallar(s or yukle())
    if not kurallar:
        return t
    t = copy.deepcopy(t)
    for seg in t.get("segments", []):
        if seg.get("words"):
            seg["words"] = _kelimeler(seg["words"], kurallar)
        metin = seg.get("text", "")
        for _, dogru, desen in kurallar:
            metin = desen.sub(dogru, metin)
        seg["text"] = metin
    return t
