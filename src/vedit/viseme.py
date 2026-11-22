"""Viseme: konuşma sesinden sekans karesi başına ağız şekli (kodla çizilen karakter için).

WHY: bkz. wiki/decisions/0039-fizik-ritim-galeri.md. Ücretsiz ve kurulumsuz yol: kare penceresinde enerji (RMS) ve
spektral ağırlık merkezi. Sınıflar: K kapalı, U yarı açık, A geniş, E yayvan, O yuvarlak. Fonem tanıyıcı (Rhubarb)
kadar doğru değildir ama açılıp kapanma zamanı sesle birebirdir; göz en çok bunu yakalar.
"""
from __future__ import annotations

import json
from pathlib import Path


from .tembel import Tembel

# WHY: Stüdyo açılışında yüklenmesin (ADR 0050)
np = Tembel("numpy")

from . import ritim

SINIFLAR = "KUAEO"
ESIK_KAPALI = 0.08     # normalize RMS; altı kapalı ağız
ESIK_YARI = 0.2        # altı yarı açık
MERKEZ_O, MERKEZ_E = 1100.0, 2200.0  # Hz: altı yuvarlak (O), üstü yayvan (E), arası geniş (A)
ON_ACILMA = 1          # kare: ağız sesten bir kare önce açılır (göz sesi önden bekler)
EN_AZ_TUT = 2          # kare: tek karelik çırpınma olmasın


def kaynak_sinif(f: Path, onbellek: Path, fps: float) -> tuple[str, float]:
    """Kaynak dosya için kare başına sınıf dizisi (kaynak zamanında, kare 0 = 0 sn) ve kare süresi."""
    import librosa

    y = ritim._yukle(f, onbellek)
    hop = max(1, int(round(ritim.SR / fps)))
    rms = librosa.feature.rms(y=y, frame_length=hop * 2, hop_length=hop, center=True)[0]
    merkez = librosa.feature.spectral_centroid(y=y, sr=ritim.SR, n_fft=2048, hop_length=hop, center=True)[0]
    tepe = float(np.percentile(rms, 98)) or 1.0
    e = np.clip(rms / tepe, 0, 1)
    s = []
    for en, m in zip(e, merkez):
        if en < ESIK_KAPALI:
            s.append("K")
        elif en < ESIK_YARI:
            s.append("U")
        else:
            s.append("O" if m < MERKEZ_O else "E" if m > MERKEZ_E else "A")
    return _duzelt("".join(s)), hop / ritim.SR


def _duzelt(s: str) -> str:
    """Ön açılma ve en az tutma: K'dan açığa geçişte açılma bir kare öne alınır, tek karelik sınıflar komşuya katılır."""
    a = list(s)
    for i in range(len(a) - 1):
        if a[i] == "K" and a[i + 1] != "K":
            for j in range(max(0, i - ON_ACILMA + 1), i + 1):
                a[j] = "U"
    sonuc = a[:]
    i = 0
    while i < len(a):
        j = i
        while j < len(a) and a[j] == a[i]:
            j += 1
        if j - i < EN_AZ_TUT and i > 0:
            for x in range(i, j):
                sonuc[x] = sonuc[i - 1]
        i = j
    return "".join(sonuc)


def sekans(p, k) -> str:
    """Kurgudaki konuşmanın sekans karesi başına sınıf dizisi; konuşma olmayan kare K."""
    from . import kurgu

    fps = k.sekans.fps
    bitis = max((c.bas + c.sure for c in k.klipler), default=0.0)
    dizi = ["K"] * int(np.ceil(bitis * fps))
    for c, rol in ritim._sesli_klipler(k):
        if rol != "konusma":
            continue
        f = kurgu.dosya(p, k.kaynaklar[c.kaynak].yol)
        if not f.is_file():
            continue
        s, adim = kaynak_sinif(f, p.work / "ritim", fps / c.hiz)
        for n in range(int(round(c.bas * fps)), min(len(dizi), int(round((c.bas + c.sure) * fps)))):
            i = int(round(((n / fps - c.bas) * c.hiz + c.giris) / adim))
            if 0 <= i < len(s) and s[i] != "K":
                dizi[n] = s[i]
    return "".join(dizi)


def yaz(p, k) -> Path:
    f = p.work / "edit" / "viseme.json"
    f.parent.mkdir(parents=True, exist_ok=True)
    s = sekans(p, k)
    f.write_text(json.dumps({"fps": k.sekans.fps, "siniflar": SINIFLAR, "kareler": s}, ensure_ascii=False), encoding="utf-8")
    return f


def acik_oran(s: str) -> float:
    return sum(ch != "K" for ch in s) / max(1, len(s))
