"""HyperFrames CLI sarmalayıcısı (repo köküne sabit sürümle kurulu: package.json)."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

from . import paths


def surum() -> str:
    """Sabit sürüm tek yerden: package.json (ADR 0051, güncelleme `vedit hf-guncelle`)."""
    try:
        return json.loads((paths.ROOT / "package.json").read_text(encoding="utf-8"))["devDependencies"]["hyperframes"]
    except (OSError, ValueError, KeyError):
        return "latest"


def _bin() -> list[str]:
    # WHY: güncelleme adayı ayrı klasörde denenir (VEDIT_HF_KOK); sabit kurulum bozulmaz.
    kok = Path(os.environ["VEDIT_HF_KOK"]) if os.environ.get("VEDIT_HF_KOK") else paths.ROOT
    local = kok / "node_modules" / ".bin" / ("hyperframes.cmd" if os.name == "nt" else "hyperframes")
    if local.exists():
        return [str(local)]
    npx = shutil.which("npx") or "npx"
    return [npx, "--yes", f"hyperframes@{surum()}"]


def run(args: list[str], *, cwd: Path | None = None, check: bool = True,
        env: dict | None = None) -> subprocess.CompletedProcess:
    # WHY: bkz. wiki/decisions/0040-ikinci-repo-dalgasi.md. 0.9.x init skill'leri genel ~/.claude/skills altına kurar ve
    # kullanım telemetrisi gönderir; ikisi de kapalı. CLI'yi doğrudan çağırırken de aynı değişkenler verilmeli.
    e = {**os.environ, "HYPERFRAMES_SKIP_SKILLS": "1", "HYPERFRAMES_NO_TELEMETRY": "1", "DO_NOT_TRACK": "1",
         "HYPERFRAMES_NO_UPDATE_CHECK": "1", "NO_COLOR": "1",
         # WHY: 0.9.7x render'ı hesap başına tek render kilidi alır; render.py bölümleri paralel render eder (ADR 0050).
         "HYPERFRAMES_RENDER_LOCK": "off", **(env or {})}
    proc = subprocess.run([*_bin(), *args], cwd=cwd, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", env=e)
    if check and proc.returncode != 0:
        raise RuntimeError(f"hyperframes {' '.join(args[:3])} başarısız:\n{(proc.stdout + proc.stderr)[-2500:]}")
    return proc


def lint(comp_dir: Path) -> dict:
    proc = run(["lint", str(comp_dir), "--json"], check=False)
    try:
        start = proc.stdout.index("{")
        return json.loads(proc.stdout[start:])
    except (ValueError, json.JSONDecodeError):
        return {"raw": (proc.stdout + proc.stderr)[-2000:], "exit": proc.returncode}


def render(comp_dir: Path, out: Path, *, quality: str = "draft", fps: int | None = None, workers: int = 1,
           crf: int | None = None, video_frame_format: str | None = None,
           aralik: tuple[float, float] | None = None, chroma: str | None = None) -> subprocess.CompletedProcess:
    out, comp_dir = Path(out).resolve(), Path(comp_dir).resolve()  # HyperFrames comp_dir içinde çalışır; göreli yol oraya düşerdi
    args = ["render", str(comp_dir), "-o", str(out), "-q", quality, "-w", str(workers) if workers else "auto", "--quiet"]
    if aralik:  # yalnız SDR MP4 ve tam sayı fps (HyperFrames 0.9.7x)
        args += ["--start", f"{aralik[0]:g}", "--end", f"{aralik[1]:g}"]
    if fps:
        args += ["-f", str(fps)]
    if crf is not None:
        args += ["--crf", str(crf)]
    if video_frame_format:
        args += ["--video-frame-format", video_frame_format]
    if chroma:  # "444": kayıpsız PNG yakalama + yuv444p (ADR 0060 master ara render)
        args += ["--chroma-subsampling", chroma]
    return run(args, cwd=comp_dir)


def render_saydam(comp_dir: Path, out: Path, *, degiskenler: dict | None = None, fps: int | None = None,
                  quality: str = "delivery") -> Path:
    """HyperFrames kompozisyonunu saydam webm'e render eder; motion bindirmesi ve proje grafiği bu yoldan gelir.

    WHY: bkz. wiki/decisions/0050-hyperframes-birincil-motor.md. Kök saydam olmalı (`background: none`). Bazı Windows
    libvpx derlemeleri alfayı düşürür; sonuç ölçülür, alfa yoksa hata verilir ki siyah kutu kurguya girmesin.
    """
    from . import ff
    out, comp_dir = out.resolve(), comp_dir.resolve()  # HyperFrames comp_dir içinde çalışır; göreli yol oraya düşerdi
    out.parent.mkdir(parents=True, exist_ok=True)
    # WHY: önbellek "dosya varsa geçerli" sayar; alfasız ya da yarım çıktı hedef adına hiç yazılmamalı.
    gecici = out.with_name(f".{out.stem}.tmp.webm")
    args = ["render", str(comp_dir), "--format", "webm", "-o", str(gecici), "-q", quality, "--quiet"]
    if fps:
        args += ["-f", str(fps)]
    if degiskenler:
        args += ["--variables", json.dumps(degiskenler, ensure_ascii=False), "--strict-variables"]
    try:
        run(args, cwd=comp_dir)
        if not (ff.probe(gecici).get("video") or {}).get("alfa"):
            raise RuntimeError(f"HyperFrames webm alfasız çıktı: {out.name}. Kökte opak zemin var mı bak; yoksa --format mov dene.")
        os.replace(gecici, out)
    finally:
        gecici.unlink(missing_ok=True)
    return out
