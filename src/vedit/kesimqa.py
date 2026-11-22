"""Kesim denetimi: dışa aktarılan sesi yeniden yazıya döker, beklenen metinle karşılaştırır.

Klip etiketine değil, gerçekten duyulana bakılır (fikir: Eyeline qa_cut/qa_edges, MIT).
Sonuç ipucudur: ASR yanlış pozitif verebilir, son karar dinleyerek verilir.
WHY: bkz. wiki/decisions/0014-altyazi-standardi-ve-repo-entegrasyonu.md
"""

from __future__ import annotations

import json
import re
import tempfile
from difflib import SequenceMatcher
from pathlib import Path


def norm(w: str) -> str:
    # Türkçe küçük harf: lower() tek başına İ/I'yı bozar.
    return re.sub(r"[^\w]", "", w.replace("İ", "i").replace("I", "ı").lower())


def karsilastir(beklenen: list[dict], duyulan: list[dict], kesimler: list[float] | None = None,
                tolerans: float = 0.6) -> dict:
    """Kelimeler {"w","s"} biçiminde; eksik ve fazla kelimeleri, kesim kenarı işaretiyle döner."""
    a = [w for w in beklenen if norm(w["w"])]
    b = [w for w in duyulan if norm(w["w"])]
    eksik, fazla = [], []
    sm = SequenceMatcher(None, [norm(w["w"]) for w in a], [norm(w["w"]) for w in b], autojunk=False)
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op in ("delete", "replace"):
            eksik += [{"kelime": w["w"], "t": w.get("s")} for w in a[i1:i2]]
        if op in ("insert", "replace"):
            fazla += [{"kelime": w["w"], "t": w.get("s")} for w in b[j1:j2]]
    for r in eksik + fazla:
        r["kesim_kenari"] = any(r["t"] is not None and abs(r["t"] - k) <= tolerans for k in kesimler or [])
    return {"benzerlik": round(sm.ratio(), 3), "eksik": eksik, "fazla": fazla,
            "beklenen": len(a), "duyulan": len(b)}


def metinden(yol: Path) -> list[dict]:
    return [{"w": w, "s": None} for w in yol.read_text(encoding="utf-8").split()]


def calistir(video: Path, beklenen: list[dict], *, dil: str | None, kesimler: list[float] | None = None) -> dict:
    from . import ff, transcribe
    with tempfile.TemporaryDirectory() as td:
        wav = ff.extract_audio(video, Path(td) / "kesimqa.wav")
        tr = transcribe.transcribe_file(wav, language=dil, model_name=transcribe.DEFAULT_MODEL)
    duyulan = [w for s in tr["segments"] for w in s["words"]]
    return karsilastir(beklenen, duyulan, kesimler)


def yaz(rep: dict, yol: Path) -> None:
    yol.parent.mkdir(parents=True, exist_ok=True)
    yol.write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
