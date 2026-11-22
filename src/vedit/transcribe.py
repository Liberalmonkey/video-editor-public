"""faster-whisper ile kelime zaman damgalı transkripsiyon (TR/EN).

Çıktı: analysis/transcript.json
  {"files": {"<stem>": {"language", "duration", "segments": [{"id","start","end","text",
                                                               "words": [{"w","s","e","p"}]}]}}}
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

DEFAULT_MODEL = os.environ.get("VEDIT_WHISPER_MODEL", "large-v3-turbo")


def _cuda_dlls() -> None:
    """Windows: CUDA 12 cuBLAS/cuDNN pip tekerleklerinin DLL klasörlerini yükleme yoluna ekle.

    # WHY: ctranslate2 cublas64_12.dll / cudnn64_9.dll arar; sistemde CUDA Toolkit yok,
    # kütüphaneler .venv'deki nvidia-cublas-cu12 + nvidia-cudnn-cu12 paketlerinden gelir.
    """
    if os.name != "nt":
        return
    try:
        import nvidia
    except ImportError:
        return
    for base in nvidia.__path__:
        for bin_dir in Path(base).glob("*/bin"):
            os.add_dll_directory(str(bin_dir))
            os.environ["PATH"] = str(bin_dir) + os.pathsep + os.environ.get("PATH", "")


def _device() -> tuple[str, str]:
    if os.environ.get("VEDIT_DEVICE") == "cpu":
        return "cpu", "int8"
    try:
        _cuda_dlls()
        import ctranslate2
        if ctranslate2.get_cuda_device_count() > 0:
            if os.name == "nt":
                # Kart var ama [gpu] eki kurulu değilse cuBLAS yok; CPU'ya düş, çökme.
                import ctypes
                ctypes.WinDLL("cublas64_12.dll")
            return "cuda", "int8_float16"
    except Exception:
        pass
    return "cpu", "int8"


def transcribe_file(wav: Path, *, language: str | None, model_name: str, prompt: str | None = None,
                    _cache: dict = {}) -> dict:
    from faster_whisper import WhisperModel

    device, compute = _device()
    key = (model_name, device, compute)
    if key not in _cache:
        print(f"  model yükleniyor: {model_name} ({device}/{compute}) — ilk seferde indirilir")
        _cache[key] = WhisperModel(model_name, device=device, compute_type=compute,
                                   cpu_threads=max(os.cpu_count() or 4, 4))
    model = _cache[key]
    # 16 kHz mono WAV'ı doğrudan dizi olarak ver: faster-whisper'ın PyAV çözücüsü sürüm
    # uyumsuzluklarına açık; ingest zaten doğru formatta WAV üretiyor.
    import soundfile as sf
    audio, sr = sf.read(str(wav), dtype="float32")
    if sr != 16000:
        raise SystemExit(f"{wav.name}: 16 kHz bekleniyordu ({sr})")
    segs, info = model.transcribe(
        audio, language=language, word_timestamps=True, vad_filter=True,
        vad_parameters={"min_silence_duration_ms": 300}, beam_size=5,
        initial_prompt=prompt, condition_on_previous_text=False,
    )
    out = []
    for i, s in enumerate(segs, 1):
        words = [{"w": w.word.strip(), "s": round(w.start, 3), "e": round(w.end, 3), "p": round(w.probability, 2)}
                 for w in (s.words or []) if w.word.strip()]
        out.append({"id": f"S{i:03d}", "start": round(s.start, 3), "end": round(s.end, 3),
                    "text": s.text.strip(), "words": words})
    return {"language": info.language, "duration": round(info.duration, 3), "segments": out}


def run(root: Path, *, language: str | None, model_name: str = DEFAULT_MODEL, files: list[str] | None = None,
        prompt: str | None = None, force: bool = False) -> dict:
    index = json.loads((root / "analysis" / "media_index.json").read_text(encoding="utf-8"))
    out_path = root / "analysis" / "transcript.json"
    result = json.loads(out_path.read_text(encoding="utf-8")) if out_path.exists() and not force else {"files": {}}
    targets = [i for i in index["files"] if i.get("wav") and i["role"] not in ("broll",)]
    if files:
        targets = [i for i in index["files"] if i.get("wav") and (i["file"] in files or Path(i["file"]).stem in files)]
    for item in targets:
        stem = Path(item["file"]).stem
        if stem in result["files"] and not force:
            print(f"  {item['file']}: önbellekte, atlandı")
            continue
        t0 = time.time()
        print(f"  {item['file']} ({item['duration']:.0f}s) transkribe ediliyor…")
        result["files"][stem] = transcribe_file(root / item["wav"], language=language, model_name=model_name,
                                                prompt=prompt)
        n = sum(len(s["words"]) for s in result["files"][stem]["segments"])
        print(f"    {n} kelime, {time.time() - t0:.0f}s")
        out_path.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    return result
