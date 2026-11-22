"""Ritim: sesin onset, beat, vurgu ve enerji ölçümü; kaynak zamanından sekans zamanına izdüşüm.

WHY: bkz. wiki/decisions/0039-fizik-ritim-galeri.md. Kesim, ses efekti ve grafik vurgusu ölçülmüş anlara oturmazsa
"ses ile görüntü kaymış" hissi doğar. Ajan sesi duyamaz; bu modül anları sayıya çevirir, ai-edit ve kurgu denetimi okur.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


from .tembel import Tembel

# WHY: Stüdyo açılışında yüklenmesin (ADR 0050)
np = Tembel("numpy")

from . import ff

SR = 22050
HOP = 128  # 5,8 ms çözünürlük: 30 fps'de bir karenin altıda biri
ENERJI_HZ = 25  # enerji eğrisi örnekleme sıklığı (ai-edit ve viseme için yeterli)


def _anahtar(f: Path) -> str:
    st = f.stat()
    return hashlib.sha1(f"{f.resolve()}|{st.st_size}|{st.st_mtime_ns}|{HOP}|v2".encode()).hexdigest()[:16]


def _yukle(f: Path, onbellek: Path) -> np.ndarray:
    import soundfile as sf

    wav = onbellek / f"{_anahtar(f)}.wav"
    if not wav.exists():
        onbellek.mkdir(parents=True, exist_ok=True)
        ff.extract_audio(f, wav, sr=SR, mono=True)
    y, _ = sf.read(wav, dtype="float32", always_2d=False)
    return y if y.ndim == 1 else y.mean(axis=1)


def _norm(x: np.ndarray) -> np.ndarray:
    tepe = float(np.percentile(x, 99)) if x.size else 0.0
    return np.clip(x / tepe, 0, 1) if tepe > 0 else np.zeros_like(x)


def _yogunluk(y: np.ndarray, env: np.ndarray, kare: np.ndarray) -> list[float]:
    """Vurgu gücü: 0,45 onset + 0,25 yerel kontrast + 0,20 RMS + 0,10 bas (brag analyze_music_cues, MIT).

    WHY: bkz. wiki/decisions/0040-ikinci-repo-dalgasi.md. Yalnız onset gücü, sürekli yoğun müzikte her vuruşu aynı
    gösteriyordu; yerel kontrast (±0,5 sn ortancasının üstü) çevresinden sıyrılan vuruşu öne çıkarır.
    """
    import librosa

    on = _norm(env)
    yaricap = max(1, int(round(0.5 * SR / HOP)))
    kontrast = np.array([max(0.0, on[i] - float(np.median(on[max(0, i - yaricap): i + yaricap + 1]))) for i in kare])
    kaba = 512  # RMS ve bas kaba adımla: uzun seste bellek
    rms = _norm(librosa.feature.rms(y=y, frame_length=2048, hop_length=kaba)[0])
    S = np.abs(librosa.stft(y, n_fft=2048, hop_length=kaba))
    bas = _norm(S[librosa.fft_frequencies(sr=SR, n_fft=2048) < 150].sum(axis=0))
    ki = np.clip((kare * HOP) // kaba, 0, len(rms) - 1)
    kn = _norm(kontrast) if kontrast.size else kontrast
    g = 0.45 * on[kare] + 0.25 * kn + 0.20 * rms[ki] + 0.10 * bas[np.clip(ki, 0, len(bas) - 1)]
    return [round(float(v), 3) for v in np.clip(g, 0, 1)]


def analiz(f: Path, onbellek: Path) -> dict:
    """Tek ses/video dosyası: kaynak zamanında onset, beat, tempo, enerji. Sonuç dosya imzasıyla önbelleğe yazılır."""
    onbellek.mkdir(parents=True, exist_ok=True)
    kayit = onbellek / f"{_anahtar(f)}.json"
    if kayit.exists():
        return json.loads(kayit.read_text(encoding="utf-8"))
    import librosa  # yerel: numba ilk yüklemede birkaç saniye sürer

    y = _yukle(f, onbellek)
    sure = len(y) / SR
    if sure < 0.2 or float(np.abs(y).max(initial=0)) < 1e-4:
        r = {"sure": round(sure, 3), "tempo": None, "beats": [], "onsets": [], "enerji": [], "enerji_hz": ENERJI_HZ}
    else:
        env = librosa.onset.onset_strength(y=y, sr=SR, hop_length=HOP)
        kare = librosa.onset.onset_detect(onset_envelope=env, sr=SR, hop_length=HOP, units="frames")
        zaman = librosa.frames_to_time(kare, sr=SR, hop_length=HOP)
        onsets = [{"t": round(float(t), 3), "guc": g} for t, g in zip(zaman, _yogunluk(y, env, kare))]
        tempo, beats = librosa.beat.beat_track(onset_envelope=env, sr=SR, hop_length=HOP, units="time")
        tempo = float(np.atleast_1d(tempo)[0])
        rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=SR // ENERJI_HZ)[0]
        rt = float(rms.max()) or 1.0
        r = {"sure": round(sure, 3), "tempo": round(tempo, 2) if len(beats) >= 4 else None,
             "beats": [round(float(b), 3) for b in beats] if len(beats) >= 4 else [],
             "onsets": onsets, "enerji": [round(float(v) / rt, 3) for v in rms], "enerji_hz": ENERJI_HZ}
    kayit.write_text(json.dumps(r), encoding="utf-8")
    return r


def _sesli_klipler(k) -> list[tuple]:
    """(klip, rol) çiftleri: konuşma ya da müzik taşıyan, duyulan klipler."""
    izler = {i.id: i for i in k.izler}
    cikti = []
    for c in k.klipler:
        if not c.kaynak or izler.get(c.iz) is None or izler[c.iz].sessiz or izler[c.iz].gizli:
            continue
        kay = k.kaynaklar.get(c.kaynak)
        if kay is None or not kay.ses:
            continue
        o = c.olay or {}
        if c.tur == "video" and not c.ses_kapali:
            cikti.append((c, "konusma"))
        elif c.tur == "ses" and o.get("muzik"):
            cikti.append((c, "muzik"))
        elif c.tur == "ses" and o.get("konusma"):
            cikti.append((c, "konusma"))
    return cikti


def izdus(c, t: float) -> float | None:
    """Kaynak zamanı → sekans zamanı; klip dışındaysa None."""
    if t < c.giris or t >= c.giris + c.sure * c.hiz:
        return None
    return c.bas + (t - c.giris) / c.hiz


def sekans(p, k) -> dict:
    """Kurgudaki duyulan kliplerin anları sekans zamanında. Çıktı `work/edit/ritim.json` biçimi."""
    from . import kurgu

    onbellek = p.work / "ritim"
    onsets, beats, tempolar = [], [], []
    for c, rol in _sesli_klipler(k):
        f = kurgu.dosya(p, k.kaynaklar[c.kaynak].yol)
        if not f.is_file():
            continue
        a = analiz(f, onbellek)
        for o in a["onsets"]:
            if (t := izdus(c, o["t"])) is not None:
                onsets.append({"t": round(t, 3), "guc": o["guc"], "rol": rol, "klip": c.id})
        if rol == "muzik":
            beats += [round(t, 3) for b in a["beats"] if (t := izdus(c, b)) is not None]
            if a["tempo"]:
                tempolar.append(a["tempo"] * c.hiz)
    onsets.sort(key=lambda o: o["t"])
    beats.sort()
    # Vurgu: güçlü onsetler; birbirine 0,25 sn'den yakın olanlardan en güçlüsü kalır.
    vurgular: list[dict] = []
    for o in sorted((o for o in onsets if o["guc"] >= 0.45), key=lambda o: -o["guc"]):
        if all(abs(o["t"] - v["t"]) >= 0.25 for v in vurgular):
            vurgular.append(o)
    vurgular.sort(key=lambda o: o["t"])
    return {"fps": k.sekans.fps, "tempo": round(float(np.median(tempolar)), 2) if tempolar else None,
            "beats": beats, "onsets": onsets, "vurgular": vurgular}


def yaz(p, k) -> Path:
    r = sekans(p, k)
    f = p.work / "edit" / "ritim.json"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
    return f


def ozet(r: dict, *, en_cok: int = 40) -> str:
    """ai-edit isteği için kısa metin: tempo, beat ızgarası ve vurgu anları."""
    satir = []
    if r.get("tempo") and r.get("beats"):
        b = r["beats"]
        aralik = float(np.median(np.diff(b))) if len(b) > 1 else 0
        satir.append(f"- Müzik temposu {r['tempo']:g} BPM, beat aralığı {aralik:.3f} sn; ilk beatler: "
                     + ", ".join(f"{t:.2f}" for t in b[:16]) + (" ..." if len(b) > 16 else ""))
    v = r.get("vurgular") or []
    if v:
        satir.append(f"- Ses vurgu anları (sekans sn, güç 0-1): "
                     + ", ".join(f"{o['t']:.2f} ({o['guc']:.2f}, {o['rol']})" for o in v[:en_cok]) + (" ..." if len(v) > en_cok else ""))
    if not satir:
        return "- Ritim ölçümü yok ya da ses sessiz."
    return "\n".join(satir)


def yakin(t: float, anlar: list[float]) -> float | None:
    """t'ye en yakın anın farkı (sn, işaretli); anlar boşsa None."""
    if not anlar:
        return None
    a = np.asarray(anlar)
    i = int(np.abs(a - t).argmin())
    return float(a[i] - t)
