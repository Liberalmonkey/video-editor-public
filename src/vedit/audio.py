"""Konuşma temizleme zinciri ve master miks.

# WHY: bkz. wiki/concepts/loudness-standartlari.md — teslim -14 LUFS / -1 dBTP; müzik konuşma
# altında ducking ile ezilir; SFX konuşmanın 8–14 dB altında. Miks numpy'da yapılır (yüzlerce
# SFX'te FFmpeg komut satırı sınırına takılmamak ve örnek-hassas yerleştirme için).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


from .tembel import Tembel

# WHY: Stüdyo açılışında yüklenmesin (ADR 0050)
np = Tembel("numpy")
sf = Tembel("soundfile")

from . import ff, paths
from .schemas import AudioClip, Timeline, load_json

SR = 48000
DENOISE = {"off": "", "light": "afftdn=nf=-28:nr=8", "medium": "afftdn=nf=-25:nr=12", "strong": "afftdn=nf=-22:nr=18"}
INTENSITY_DB = {"soft": -9.0, "medium": -5.0, "hard": -1.5}


def clean_voice(src: Path, dst: Path, *, denoise: str = "light", eq: bool = True) -> Path:
    """highpass → gürültü azaltma → EQ (çamur kes, netlik) → kompresör. Loudness master'da."""
    chain = ["highpass=f=80", DENOISE.get(denoise, "")]
    if eq:
        chain += ["equalizer=f=250:t=q:w=1.2:g=-2.5", "equalizer=f=4200:t=q:w=1.5:g=2"]
    chain += ["acompressor=threshold=-21dB:ratio=3:attack=6:release=90:makeup=2", f"aresample={SR}"]
    dst.parent.mkdir(parents=True, exist_ok=True)
    ff.ffmpeg("-i", str(src), "-vn", "-ac", "1", "-af", ",".join(c for c in chain if c), "-c:a", "pcm_s24le", str(dst))
    return dst


def _decode(path: Path, cache: Path) -> np.ndarray:
    """Herhangi bir ses/video dosyasını 48 kHz stereo float32 diziye çöz (önbellekli)."""
    st = path.stat()
    key = hashlib.sha1(f"{path}|{st.st_size}|{int(st.st_mtime)}".encode()).hexdigest()[:12]
    wav = cache / f"{path.stem}-{key}.wav"
    if not wav.exists():
        cache.mkdir(parents=True, exist_ok=True)
        ff.ffmpeg("-i", str(path), "-vn", "-ac", "2", "-ar", str(SR), "-c:a", "pcm_f32le", str(wav))
    data, _ = sf.read(wav, dtype="float32", always_2d=True)
    return data


def _db(x: float) -> float:
    return float(10 ** (x / 20))


def _place(buf: np.ndarray, clip: np.ndarray, start: float, gain: float, fade_in: float = 0, fade_out: float = 0) -> None:
    i0 = int(round(start * SR))
    if i0 >= len(buf):
        return
    if i0 < 0:
        clip, i0 = clip[-i0:], 0
    n = min(len(clip), len(buf) - i0)
    seg = clip[:n].copy() * gain
    if fade_in > 0:
        k = min(int(fade_in * SR), n)
        seg[:k] *= np.linspace(0, 1, k, dtype=np.float32)[:, None]
    if fade_out > 0:
        k = min(int(fade_out * SR), n)
        seg[n - k:] *= np.linspace(1, 0, k, dtype=np.float32)[:, None]
    buf[i0:i0 + n] += seg


def voice_envelope(voice: np.ndarray, *, win: float = 0.05, thresh_db: float = -40, attack: float = 0.08,
                   release: float = 0.45) -> np.ndarray:
    """Konuşma varlığı zarfı (0..1): RMS penceresi → eşik → attack/release yumuşatma."""
    mono = voice.mean(axis=1)
    hop = int(win * SR)
    n = len(mono) // hop + 1
    pad = np.pad(mono, (0, n * hop - len(mono)))
    rms = np.sqrt((pad.reshape(n, hop) ** 2).mean(axis=1) + 1e-12)
    active = (20 * np.log10(rms) > thresh_db).astype(np.float32)
    env = np.zeros_like(active)
    a_k, r_k = win / attack, win / release
    for i in range(1, n):
        target = active[i]
        k = a_k if target > env[i - 1] else r_k
        env[i] = env[i - 1] + (target - env[i - 1]) * min(k, 1.0)
    # Konuşma başlamadan biraz önce inmeye başla (look-ahead ~1 pencere)
    env = np.maximum(env, np.roll(env, -2))
    return np.repeat(env, hop)[: len(mono)]


def mix(root: Path, *, duck_db: float = -11.0) -> dict:
    """timeline.audio → build/mix_raw.wav → 2 geçişli loudnorm → build/master.wav"""
    from .project import load as load_project, studio_for

    tl = load_json(root / "edit" / "timeline.json", Timeline)
    proj = load_project(root)
    target = studio_for(proj).loudness
    cache = root / "build" / "cache" / "audio"
    total = int(np.ceil(tl.duration * SR))
    voice_bus = np.zeros((total, 2), dtype=np.float32)
    music_bus = np.zeros((total, 2), dtype=np.float32)
    sfx_bus = np.zeros((total, 2), dtype=np.float32)

    voices = list(tl.audio.voice)
    if not voices and (root / "build" / "voice.wav").exists():
        voices = [AudioClip(id="voice", src="build/voice.wav")]
    for v in voices:
        data = _decode(_resolve(root, v.src), cache)
        data = data[int(v.in_ * SR):]
        if v.dur:
            data = data[: int(v.dur * SR)]
        _place(voice_bus, data, v.start, _db(v.gain_db), v.fade_in, v.fade_out)

    env = voice_envelope(voice_bus) if voice_bus.any() else np.zeros(total, dtype=np.float32)
    for m in tl.audio.music:
        data = _decode(_resolve(root, m.src), cache)[int(m.in_ * SR):]
        length = int((m.dur or (tl.duration - m.start)) * SR)
        if len(data) < length and len(data) > 0:  # kısa parçayı döngüle
            reps = int(np.ceil(length / len(data)))
            data = np.tile(data, (reps, 1))
        data = data[:length]
        seg = np.zeros((total, 2), dtype=np.float32)
        _place(seg, data, m.start, _db(m.gain_db), m.fade_in or 1.0, m.fade_out or 2.0)
        if m.duck:
            seg *= (1 - env * (1 - _db(duck_db)))[:, None]
        music_bus += seg

    resolved = root / "audio" / "sfx_resolved.json"
    n_sfx = 0
    if resolved.exists():
        for cue in json.loads(resolved.read_text(encoding="utf-8"))["cues"]:
            if not cue.get("file"):
                continue
            data = _decode(paths.ROOT / cue["file"], cache)
            gain = cue["gain_db"] if cue.get("gain_db") is not None else INTENSITY_DB.get(cue.get("intensity"), -5)
            _place(sfx_bus, data, cue["t"] - cue.get("peak_offset_s", 0.0), _db(gain))
            n_sfx += 1

    mixed = voice_bus + music_bus + sfx_bus
    raw = root / "build" / "mix_raw.wav"
    sf.write(raw, np.clip(mixed, -4, 4), SR, subtype="FLOAT")
    master = root / "build" / "master.wav"
    loudnorm_2pass(raw, master, I=target.integrated, TP=target.true_peak, LRA=target.lra)
    meas = ff.loudness(master)
    return {"master": "build/master.wav", "duration": round(total / SR, 3), "sfx": n_sfx,
            "music": len(tl.audio.music), "loudness": meas}


def loudnorm_2pass(src: Path, dst: Path, *, I: float = -14, TP: float = -1, LRA: float = 11) -> None:
    m = ff.loudness(src)
    if not m or m["I"] < -70:  # sessiz dosya — normalize edilecek bir şey yok
        ff.ffmpeg("-i", str(src), "-ar", str(SR), "-c:a", "pcm_s24le", str(dst))
        return
    af = (f"loudnorm=I={I}:TP={TP}:LRA={LRA}:measured_I={m['I']}:measured_TP={m['TP']}:"
          f"measured_LRA={m['LRA']}:measured_thresh={m['thresh']}:linear=true:print_format=summary,"
          f"alimiter=limit={_db(TP - 0.3):.4f}:level=disabled,aresample={SR}")
    ff.ffmpeg("-i", str(src), "-af", af, "-ar", str(SR), "-c:a", "pcm_s24le", str(dst))


def _resolve(root: Path, src: str) -> Path:
    p = Path(src)
    if p.is_absolute():
        return p
    return paths.pj(root, p) if paths.pj(root, p).exists() else paths.ROOT / p


# WHY: bkz. wiki/decisions/0024-oneri-araclari.md. Yüksek geçiren + FFT gürültü azaltma; ücretsiz, model yok.
# afftdn ancak `nf` gerçek gürültü tabanına yakınsa çalışır, `tn=1` ölçüldü ve etkisiz çıktı (0,3 dB). Taban her aralıkta ölçülür.
TEMIZLE_AZALT = 12  # dB, üstü konuşmada metalik iz bırakır


def gurultu_tabani(seg: np.ndarray) -> float:
    """50 ms karelerin en sessiz %10'unun RMS'i, dBFS."""
    n = int(0.05 * SR)
    kare = seg[:len(seg) // n * n, 0].reshape(-1, n) if len(seg) >= n else seg[:, :1].T
    rms = np.sqrt(np.mean(kare.astype(np.float64) ** 2, axis=1)) + 1e-9
    return float(20 * np.log10(np.percentile(rms, 10)))


def zarf(data: np.ndarray, noktalar: list | None) -> np.ndarray:
    """Kazanç keyframe'leri: [[t, dB farkı], ...] klip başından, doğrusal dB geçiş. Sabit kazanç ayrıca uygulanır."""
    if not noktalar or not len(data):
        return data
    ts, vs = zip(*noktalar)
    return data * (10 ** (np.interp(np.arange(len(data)) / SR, ts, vs) / 20)).astype(np.float32)[:, None]


def temizle(buf: np.ndarray, araliklar: list) -> np.ndarray:
    """Konuşma busunda verilen aralıkları gürültüden temizler; uçlarda 10 ms geçiş, kesim tıkı olmaz."""
    import tempfile
    for a, b in araliklar:
        i0, i1 = max(0, int(a * SR)), min(len(buf), int(b * SR))
        if i1 - i0 < SR // 10:
            continue
        seg = buf[i0:i1]
        with tempfile.TemporaryDirectory() as g:
            x, y = Path(g) / "a.wav", Path(g) / "b.wav"
            sf.write(x, seg, SR, subtype="FLOAT")
            nf = min(-20.0, max(-80.0, gurultu_tabani(seg) + 3))
            ff.ffmpeg("-i", str(x), "-af", f"highpass=f=80,afftdn=nr={TEMIZLE_AZALT}:nf={nf:.0f}", "-c:a", "pcm_f32le", str(y))
            temiz, _ = sf.read(y, dtype="float32", always_2d=True)
        temiz = np.pad(temiz[:len(seg)], ((0, max(0, len(seg) - len(temiz))), (0, 0)))
        k = min(int(0.01 * SR), len(seg) // 2)
        w = np.ones(len(seg), dtype=np.float32)
        w[:k], w[len(seg) - k:] = np.linspace(0, 1, k), np.linspace(1, 0, k)
        buf[i0:i1] = seg * (1 - w[:, None]) + temiz * w[:, None]
    return buf
