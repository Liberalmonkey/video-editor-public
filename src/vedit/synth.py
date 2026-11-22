"""Prosedürel SFX sentezi (numpy) — sıfır maliyet, lisans derdi yok, seed'li varyasyon.

# WHY: bkz. wiki/concepts/sfx-stratejisi.md (3. katman). Kaynak rehberdeki "Web Audio ile
# sentez" fikrinin offline karşılığı; kütüphanede eşleşme yoksa her zaman bir ses bulunur.
"""

from __future__ import annotations

from .tembel import Tembel

# WHY: Stüdyo açılışında yüklenmesin (ADR 0050)
np = Tembel("numpy")
sf = Tembel("soundfile")

import json
import zlib
from pathlib import Path


SR = 48000


def _t(dur: float) -> np.ndarray:
    return np.arange(int(dur * SR)) / SR


def _shaped_noise(rng: np.random.Generator, dur: float, centers: np.ndarray, width: float) -> np.ndarray:
    """Zamanla değişen bant geçiren gürültü (STFT şekillendirme + overlap-add)."""
    n = int(dur * SR)
    frame, hop = 1024, 256
    noise = rng.standard_normal(n + frame)
    out = np.zeros(n + frame)
    win = np.hanning(frame)
    freqs = np.fft.rfftfreq(frame, 1 / SR)
    for i, start in enumerate(range(0, n, hop)):
        c = centers[min(int(start / n * len(centers)), len(centers) - 1)]
        spec = np.fft.rfft(noise[start:start + frame] * win)
        spec *= np.exp(-0.5 * ((np.log2(freqs + 1) - np.log2(c)) / width) ** 2)
        out[start:start + frame] += np.fft.irfft(spec, frame) * win
    return out[:n]


def _norm(x: np.ndarray, peak_db: float = -4.0) -> np.ndarray:
    return x / (np.abs(x).max() + 1e-9) * 10 ** (peak_db / 20)


def _stereo(x: np.ndarray, width: float = 0.0, rng: np.random.Generator | None = None) -> np.ndarray:
    if width <= 0 or rng is None:
        return np.stack([x, x], axis=1)
    d = int(0.0004 * SR * width)
    return np.stack([x, np.concatenate([np.zeros(d), x[:-d]]) if d else x], axis=1)


def whoosh(rng, dur=0.7, lo=300, hi=2600, peak=0.55):
    centers = np.concatenate([np.geomspace(lo, hi, int(64 * peak)), np.geomspace(hi, lo * 1.5, int(64 * (1 - peak)))])
    x = _shaped_noise(rng, dur, centers, 0.9)
    n = len(x)
    p = int(peak * n)
    env = np.concatenate([np.linspace(0, 1, p) ** 2.2, np.linspace(1, 0, n - p) ** 1.6])
    return _norm(x * env), peak * dur


def riser(rng, dur=1.6):
    t = _t(dur)
    sweep = np.sin(2 * np.pi * np.cumsum(np.geomspace(180, 1800, len(t))) / SR) * 0.35
    noise = _shaped_noise(rng, dur, np.geomspace(400, 6000, 64), 1.1)
    noise = noise / (np.abs(noise).max() + 1e-9)
    env = (t / dur) ** 2.4
    x = (sweep + noise * 0.6) * env
    x[-int(0.01 * SR):] *= np.linspace(1, 0, int(0.01 * SR))
    return _norm(x), dur - 0.01


def pop(rng, dur=0.12, f0=950, f1=280):
    t = _t(dur)
    f = np.geomspace(f0 * rng.uniform(0.9, 1.1), f1, len(t))
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 38)
    return _norm(x), 0.004


def click(rng, dur=0.035, f=3200):
    t = _t(dur)
    x = rng.standard_normal(len(t)) * np.exp(-t * 900) * 0.6 + np.sin(2 * np.pi * f * rng.uniform(0.9, 1.15) * t) * np.exp(-t * 260)
    return _norm(x, -5), 0.001


def tick(rng, dur=0.02):
    t = _t(dur)
    x = np.sin(2 * np.pi * 5200 * rng.uniform(0.95, 1.05) * t) * np.exp(-t * 600)
    return _norm(x, -8), 0.0


def impact(rng, dur=0.9):
    t = _t(dur)
    f = np.geomspace(85, 38, len(t))
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 5.5)
    hit = _shaped_noise(rng, dur, np.geomspace(2500, 300, 32), 1.2) * np.exp(-t * 28)
    x = body + hit / (np.abs(hit).max() + 1e-9) * 0.5
    return _norm(x, -2), 0.006


def ding(rng, dur=1.1, f=1318.5):
    t = _t(dur)
    f = f * rng.uniform(0.97, 1.03)
    x = (np.sin(2 * np.pi * f * t) + 0.45 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t * 4)
         + 0.2 * np.sin(2 * np.pi * f * 5.4 * t) * np.exp(-t * 9)) * np.exp(-t * 3.2)
    x[: int(0.002 * SR)] *= np.linspace(0, 1, int(0.002 * SR))
    return _norm(x, -6), 0.002


def notify(rng, dur=0.5):
    a, _ = ding(rng, 0.45, 1046.5)
    b, _ = ding(rng, 0.5, 1568.0)
    x = np.zeros(int(dur * SR) + len(b))
    x[: len(a)] += a
    o = int(0.11 * SR)
    x[o:o + len(b)] += b
    return _norm(x[: int(0.62 * SR)], -6), 0.002


def success(rng):
    return notify(rng)


def error(rng, dur=0.4):
    t = _t(dur)
    x = np.sign(np.sin(2 * np.pi * 220 * t)) * 0.3 * np.exp(-t * 6)
    x[int(0.2 * SR):] += np.sign(np.sin(2 * np.pi * 185 * t[: len(t) - int(0.2 * SR)])) * 0.3 * np.exp(-t[: len(t) - int(0.2 * SR)] * 6)
    return _norm(x, -9), 0.002


def phone_ring(rng, dur=2.2):
    """Klasik telefon zili: 440+480 Hz, 20 Hz trillo, 2 sn çalma."""
    t = _t(dur)
    tone = np.sin(2 * np.pi * 440 * t) + np.sin(2 * np.pi * 480 * t)
    trill = (np.sin(2 * np.pi * 20 * t) > 0).astype(float) * 0.85 + 0.15
    env = np.clip(t / 0.02, 0, 1) * np.clip((dur - t) / 0.05, 0, 1)
    return _norm(tone * trill * env, -7), 0.02


def vibrate(rng, dur=0.9):
    t = _t(dur)
    x = np.sin(2 * np.pi * 155 * t) * (0.6 + 0.4 * np.sin(2 * np.pi * 31 * t))
    env = np.clip(t / 0.03, 0, 1) * np.clip((dur - t) / 0.03, 0, 1)
    gate = ((t % 0.45) < 0.35).astype(float)
    return _norm(x * env * gate, -8), 0.03


def typing(rng, dur=2.5, rate=9.0):
    """Klavye yazma döngüsü: seed'li aralıklarla mekanik tıklar (her biri farklı)."""
    n = int(dur * SR)
    x = np.zeros(n)
    t = 0.05
    while t < dur - 0.06:
        c, _ = click(rng, 0.03, rng.uniform(1800, 3600))
        thud = np.sin(2 * np.pi * rng.uniform(140, 220) * _t(0.03)) * np.exp(-_t(0.03) * 120) * 0.5
        k = (c[: len(thud)] + thud) * rng.uniform(0.55, 1.0)
        i = int(t * SR)
        x[i:i + len(k)] += k[: n - i]
        t += rng.exponential(1 / rate) + 0.035
    return _norm(x, -6), 0.05


def shutter(rng, dur=0.25):
    a, _ = click(rng, 0.04, 2600)
    b, _ = click(rng, 0.05, 1900)
    x = np.zeros(int(dur * SR))
    x[: len(a)] += a
    o = int(0.07 * SR)
    x[o:o + len(b)] += b * 0.8
    return _norm(x, -5), 0.001


def cash(rng, dur=1.0):
    d, _ = ding(rng, 0.9, 2093.0)
    c, _ = click(rng, 0.04, 3000)
    x = np.zeros(int(dur * SR))
    x[: len(c)] += c * 0.8
    o = int(0.05 * SR)
    x[o:o + len(d)] += d[: len(x) - o]
    return _norm(x, -5), 0.001


def glitch(rng, dur=0.35):
    x = np.zeros(int(dur * SR))
    for _ in range(9):
        i = int(rng.uniform(0, dur - 0.04) * SR)
        L = int(rng.uniform(0.008, 0.04) * SR)
        x[i:i + L] += np.sign(np.sin(2 * np.pi * rng.uniform(200, 3000) * np.arange(L) / SR)) * rng.uniform(0.3, 1)
    return _norm(x, -9), 0.0


RECIPES = {
    "whoosh": (lambda r: whoosh(r, dur=r.uniform(0.55, 0.85)), ["transition", "fast", "air"]),
    "swoosh": (lambda r: whoosh(r, dur=r.uniform(0.3, 0.45), lo=600, hi=5000, peak=0.5), ["transition", "short", "light"]),
    "riser": (lambda r: riser(r, dur=r.uniform(1.2, 2.0)), ["build", "tension", "reveal"]),
    "riser-short": (lambda r: riser(r, dur=r.uniform(0.6, 0.9)), ["build", "short"]),
    "pop": (pop, ["ui", "text", "appear", "bubble"]),
    "click": (click, ["ui", "tap", "button", "mouse"]),
    "tap": (lambda r: click(r, 0.03, r.uniform(1500, 2200)), ["ui", "touch", "phone"]),
    "tick": (tick, ["ui", "tiny", "counter"]),
    "impact": (impact, ["hit", "boom", "emphasis"]),
    "ding": (ding, ["bell", "positive", "notification"]),
    "notification": (notify, ["phone", "message", "alert"]),
    "success": (success, ["positive", "done"]),
    "error": (error, ["negative", "wrong", "buzz"]),
    "phone_ring": (phone_ring, ["phone", "ring", "call"]),
    "vibrate": (vibrate, ["phone", "buzz", "silent"]),
    "typing": (typing, ["keyboard", "type", "computer", "loop"]),
    "camera_shutter": (shutter, ["camera", "photo", "snap"]),
    "cash": (cash, ["money", "sale", "register", "kaching"]),
    "glitch": (glitch, ["digital", "error", "tech"]),
}


def generate(out_dir: Path, *, variants: int = 3, only: list[str] | None = None) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    meta = {}
    for name, (fn, tags) in RECIPES.items():
        if only and name not in only:
            continue
        for v in range(1, variants + 1):
            rng = np.random.default_rng(zlib.crc32(name.encode()) % 10_000 + v * 7919)
            x, peak = fn(rng)
            p = out_dir / f"{name}-{v:02d}.wav"
            sf.write(p, _stereo(np.asarray(x, dtype=np.float32), 1.0, rng), SR, subtype="PCM_24")
            meta[p.name] = {"category": name, "tags": tags, "peak_offset_s": round(float(peak), 4)}
            written.append(p)
    (out_dir / "source.json").write_text(json.dumps({
        "license": "CC0", "source": "synth", "source_url": "",
        "note": "vedit prosedürel sentez (src/vedit/synth.py)", "files": meta}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    return written
