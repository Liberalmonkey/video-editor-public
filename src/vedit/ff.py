"""FFmpeg / ffprobe yardımcıları: çalıştırma, envanter, loudness ölçümü, kontak sayfası."""

from __future__ import annotations

import copy
import functools
import json
import os
import re
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

FFMPEG = shutil.which("ffmpeg") or "ffmpeg"
FFPROBE = shutil.which("ffprobe") or "ffprobe"
# drawtext, fontconfig olmayan Windows build'lerinde font yolu verilmezse çöker
LABEL_FONT = Path(__file__).resolve().parents[2] / "library" / "fonts" / "Inter-Variable.ttf"


def filter_path(p: Path) -> str:
    r"""FFmpeg filtre argümanı için yol kaçışı (C: → C\:)."""
    return str(p).replace("\\", "/").replace(":", r"\:")


def run(args: list[str], *, capture: bool = True, check: bool = True) -> subprocess.CompletedProcess:
    proc = subprocess.run(args, capture_output=capture, text=True, encoding="utf-8", errors="replace")
    if check and proc.returncode != 0:
        tail = (proc.stderr or "")[-1500:]
        raise RuntimeError(f"Komut başarısız ({proc.returncode}): {' '.join(args[:6])} ...\n{tail}")
    return proc


def ffmpeg(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    return run([FFMPEG, "-hide_banner", "-nostdin", "-y", *args], check=check)


@functools.lru_cache(maxsize=1024)
def _probe_onbellek(yol: str, _mtime: int, _boyut: int) -> dict:
    return probe(Path(yol))


def probe_ob(path: Path) -> dict:
    """probe, mtime ve boyut anahtarlı önbellekle; dosya değişince yeniden ölçer.

    WHY: Stüdyo her panel ve şerit isteğinde aynı dosyaya ffprobe başlatıyordu (ADR 0050). Kopya döner: çağıran değiştirebilir.
    """
    st = path.stat()
    return copy.deepcopy(_probe_onbellek(str(path.resolve()), st.st_mtime_ns, st.st_size))


def probe(path: Path) -> dict:
    out = run([FFPROBE, "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(path)]).stdout
    data = json.loads(out)
    fmt = data.get("format", {})
    info: dict = {"file": path.name, "duration": round(float(fmt.get("duration", 0) or 0), 3),
                  "size_mb": round(int(fmt.get("size", 0) or 0) / 1e6, 1)}
    for s in data.get("streams", []):
        if s.get("codec_type") == "video" and "video" not in info:
            num, _, den = (s.get("avg_frame_rate") or "0/1").partition("/")
            fps = float(num) / float(den or 1) if float(den or 1) else 0.0
            rotation = 0
            for sd in s.get("side_data_list", []) or []:
                if "rotation" in sd:
                    rotation = int(sd["rotation"])
            w, h = int(s.get("width", 0)), int(s.get("height", 0))
            if abs(rotation) in (90, 270):
                w, h = h, w
            rn, _, rd = (s.get("r_frame_rate") or "0/1").partition("/")
            r_fps = float(rn) / float(rd or 1) if float(rd or 1) else 0.0
            info["video"] = {"codec": s.get("codec_name"), "width": w, "height": h,
                             "fps": round(fps, 3), "pix_fmt": s.get("pix_fmt"), "rotation": rotation, "alfa": _alfa_mi(s),
                             # WHY: bkz. wiki/decisions/0060-proxy-master-conform.md. Ortalama ve nominal hız ayrışırsa VFR.
                             "vfr": bool(fps and r_fps and abs(r_fps - fps) / r_fps > 0.01),
                             "bit_rate": int(s.get("bit_rate") or fmt.get("bit_rate") or 0),
                             **{k: s[k] for k in ("color_transfer", "color_primaries", "color_space", "color_range") if s.get(k)}}
        elif s.get("codec_type") == "audio" and "audio" not in info:
            info["audio"] = {"codec": s.get("codec_name"), "sample_rate": int(s.get("sample_rate", 0)),
                             "channels": int(s.get("channels", 0))}
    return info


ALFA_PIX = ("yuva", "rgba", "bgra", "argb", "abgr", "gbrap", "ya8", "ya16")


def _alfa_mi(s: dict) -> bool:
    """VP8/VP9 alfası ayrı akışta taşınır: ffprobe pix_fmt'i yuv420p gösterir, işaret `alpha_mode` etiketidir."""
    # WHY: ffmpeg'in kendi webm'i `alpha_mode`, HyperFrames 0.9.7x `ALPHA_MODE` yazar (ADR 0050).
    if any(k.lower() == "alpha_mode" and str(v) == "1" for k, v in (s.get("tags") or {}).items()):
        return True
    return (s.get("pix_fmt") or "").startswith(ALFA_PIX)


def kind_of(info: dict) -> str:
    if "video" in info and info.get("video", {}).get("codec") not in ("png", "mjpeg") and info["duration"] > 0.5:
        return "video"
    if "video" in info:
        return "image"
    if "audio" in info:
        return "audio"
    return "other"


_LOUD_RE = re.compile(r"\{[^{}]*\"input_i\"[^{}]*\}", re.S)


def loudness(path: Path, *, start: float | None = None, dur: float | None = None) -> dict:
    """loudnorm ölçüm geçişi: integrated LUFS, true peak, LRA, threshold."""
    args = []
    if start is not None:
        args += ["-ss", f"{start:.3f}"]
    if dur is not None:
        args += ["-t", f"{dur:.3f}"]
    proc = ffmpeg(*args, "-i", str(path), "-vn", "-af", "loudnorm=print_format=json", "-f", "null", "-", check=False)
    m = _LOUD_RE.search(proc.stderr or "")
    if not m:
        return {}
    d = json.loads(m.group(0))
    return {"I": float(d["input_i"]), "TP": float(d["input_tp"]), "LRA": float(d["input_lra"]),
            "thresh": float(d["input_thresh"])}


def silences(path: Path, *, noise_db: float = -35, min_dur: float = 0.35) -> list[tuple[float, float]]:
    proc = ffmpeg("-i", str(path), "-vn", "-af", f"silencedetect=noise={noise_db}dB:d={min_dur}",
                  "-f", "null", "-", check=False)
    out, start = [], None
    for line in (proc.stderr or "").splitlines():
        if "silence_start:" in line:
            start = float(line.split("silence_start:")[1].split()[0])
        elif "silence_end:" in line and start is not None:
            end = float(line.split("silence_end:")[1].split()[0])
            out.append((round(start, 3), round(end, 3)))
            start = None
    return out


def contact_sheet(src: Path, dst: Path, *, duration: float, cols: int = 4, rows: int = 4,
                  width: int = 320, start: float = 0.0, label: bool = True, times: list[float] | None = None) -> Path:
    """cols×rows kareyi eşit aralıklarla tek görselde topla (LLM'e ucuz görsel özet).

    Her kare ayrı, kesin seek ile alınır ve üzerine gerçek zamanı yazılır. (fps filtresi + giriş
    seek'i kareleri 1–2 sn kaydırıyordu; eleştirmen yanlış zamana düzeltme önermesin diye.)
    """
    import shutil
    import tempfile

    if times:  # verilen anlar: satır sayısı kare sayısından çıkar
        rows = -(-len(times) // cols)
    else:
        n = cols * rows
        span = max(duration - start, 0.1)
        times = [start + span * (i + 0.5) / n for i in range(n)]
    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="vsheet_", dir=dst.parent))
    try:
        def kare(i: int, t: float) -> None:
            vf = f"scale={width}:-2"
            if label:
                m, s = divmod(t, 60)
                vf += (f",drawtext=fontfile='{filter_path(LABEL_FONT)}':text='{int(m):02d}m{s:04.1f}s':x=6:y=6:"
                       "fontsize=18:fontcolor=white:box=1:boxcolor=black@0.6:boxborderw=4")
            ffmpeg("-ss", f"{t:.3f}", "-i", str(src), "-frames:v", "1", "-vf", vf, str(tmp / f"f{i:03d}.png"))

        with ThreadPoolExecutor(max_workers=min(8, os.cpu_count() or 4)) as havuz:
            list(havuz.map(kare, range(len(times)), times))  # list: bir karenin hatası burada yükselsin
        ffmpeg("-framerate", "1", "-i", str(tmp / "f%03d.png"), "-vf", f"tile={cols}x{rows}:padding=4:margin=4",
               "-frames:v", "1", "-q:v", "4", str(dst))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return dst


def extract_audio(src: Path, dst: Path, *, sr: int = 16000, mono: bool = True) -> Path:
    dst.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg("-i", str(src), "-vn", "-ac", "1" if mono else "2", "-ar", str(sr), "-c:a", "pcm_s16le", str(dst))
    return dst


def still(src: Path, dst: Path, t: float, *, width: int | None = None) -> Path:
    vf = ["-vf", f"scale={width}:-2"] if width else []
    ffmpeg("-ss", f"{t:.3f}", "-i", str(src), "-frames:v", "1", *vf, str(dst))
    return dst


# WHY: bkz. wiki/decisions/0040-ikinci-repo-dalgasi.md. iPhone ve Android HDR çekimi (HLG, PQ) Chrome'da soluk ve yanlış
# renkte çizilir, teslim de onu reddeder. Kaynak render ve önizlemeye girmeden BT.709 SDR'ye ton eşlenir.
# Zincir ffmpeg-skill (MIT, kajisho5) düzeltmesine göre: 100 nit referansla doğrusallaştır, kaynak tepesini SDR beyazına
# eşle (HLG her zaman 1000 nit), sınırlı aralık BT.709'a dön. Bizim yazımımız; ilk sürümleri beyazı 151/235'te bırakıyordu.
HDR_TRC = ("smpte2084", "arib-std-b67")


def hdr_mi(info: dict) -> bool:
    return (info.get("video") or {}).get("color_transfer") in HDR_TRC


def sdr_zinciri(video: dict, *, tepe: float = 1000.0, egri: str = "hable") -> str:
    trc = video.get("color_transfer") or "smpte2084"
    prim, mat = video.get("color_primaries") or "bt2020", video.get("color_space") or "bt2020nc"
    kaynak_tepe = 1000.0 if trc == "arib-std-b67" else tepe
    etiket = [] if video.get("color_primaries") and video.get("color_space") else [f"setparams=color_primaries={prim}:color_trc={trc}:colorspace={mat}"]
    return ",".join(etiket + [
        f"zscale=tin={trc}:pin={prim}:min={mat}:rin={video.get('color_range') or 'tv'}:t=linear:npl=100",
        "format=gbrpf32le", "zscale=p=bt709", f"tonemap=tonemap={egri}:desat=0:peak={kaynak_tepe / 100:g}",
        "zscale=t=bt709:m=bt709:r=tv:d=error_diffusion", "format=yuv420p"])


def sdr_cevir(src: Path, dst: Path, *, tepe: float = 1000.0, master: bool = False) -> Path:
    """HDR kaynağı SDR kopyaya çevirir; ses kopyalanır. Son kalite kodlaması teslimdedir.

    Ara kalite CRF 14 veryfast; `master` (ADR 0060) CRF 6 medium: teslimden önce görünür kayıp bırakmaz, kayıpsızın
    disk bedelini (4K'da dakikada ~8 GB) ödemez.
    """
    v = probe(src)["video"]
    dst.parent.mkdir(parents=True, exist_ok=True)
    gecici = dst.with_name(f".{dst.stem}.tmp{dst.suffix}")
    preset, crf = ("medium", "6") if master else ("veryfast", "14")
    ffmpeg("-y", "-i", str(src), "-vf", sdr_zinciri(v, tepe=tepe), "-c:v", "libx264", "-preset", preset, "-crf", crf,
           "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-color_range", "tv",
           "-c:a", "copy", "-movflags", "+faststart", str(gecici))
    gecici.replace(dst)
    return dst
