"""Senkron: bir video klibinde sesin görüntüden kaç kare kaydığını ölçer, istenirse ayrık sesi kaydırır.

WHY: bkz. wiki/decisions/0039-fizik-ritim-galeri.md. Flow/Veo karakter kliplerinde ses birkaç kare önde ya da geride
gelebiliyor; göz bunu 2 kareden sonra "dudak oynamıyor" diye okur. Ses onset zarfı ile görüntü hareket başlangıcı
(kare farkının artışı) çapraz ilişkiyle eşlenir. Ölçüm genel harekete bakar: çarpma, adım, jest ve konuşma başı
iyi sonuç verir; sabit kamerada yalnız dudak oynayan klipte güven düşük çıkar ve rapor bunu söyler.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


from .tembel import Tembel

# WHY: Stüdyo açılışında yüklenmesin (ADR 0050)
np = Tembel("numpy")

from . import ritim

GUVEN_ESIGI = 0.25  # bunun altındaki eşleşme "belirsiz" sayılır, uygulanmaz
# Konuşmada dudak sesten önce açılır (görsel konuşma işitselden ortalama 40-100 ms önde). Ağız ölçümünde bu aralıktaki
# "ses geç" kayması kusur değildir; düzeltilirse dudak sesle aynı anda açılır ve yapay görünür.
DOGAL_ONDE_MS = (0, 110)


@dataclass
class Olcum:
    klip: str
    kayma_kare: int       # > 0: ses görüntüden geç geliyor
    guven: float          # 0-1, çapraz ilişki tepe değeri
    ayirt: float          # tepenin tüm gecikmelerin ortanca skorundan farkı
    fps: float
    kaynak: str = "kare"  # hareket nereden ölçüldü: tüm kare ya da ağız bölgesi

    @property
    def dogal(self) -> bool:
        ms = self.kayma_kare / self.fps * 1000
        return self.kaynak == "ağız" and DOGAL_ONDE_MS[0] <= ms <= DOGAL_ONDE_MS[1]

    @property
    def belirsiz(self) -> bool:
        return self.guven < GUVEN_ESIGI or self.ayirt < 0.15

    def metin(self) -> str:
        ms = self.kayma_kare / self.fps * 1000
        yon = "ses geç" if self.kayma_kare > 0 else "ses erken" if self.kayma_kare < 0 else "senkron"
        ek = ("  (doğal: konuşmada dudak sesten önce açılır, düzeltme gerekmez)" if self.dogal
              else "  (belirsiz: klipte belirgin hareket ya da ses vurgusu az)" if self.belirsiz else "")
        return f"{self.klip}: {self.kayma_kare:+d} kare ({ms:+.0f} ms, {yon}), güven {self.guven:.2f}, ölçüm {self.kaynak}{ek}"


def agiz_bolgesi(f: Path, bas: float, bit: float) -> tuple[float, float, float, float] | None:
    """Ağız bölgesi (oran olarak x, y, w, h): YuNet yüz tespitinin ağız köşesi işaretlerinden. Yüz yoksa None.

    WHY: konuşan kafada tüm kare neredeyse durgundur; hareket ağızdadır. Model reframe ile aynı
    (library/models, OpenCV 5'te Haar kaldırıldı). Bölge yedi karenin ortancasıyla sabit tutulur (kamera sabit varsayımı).
    """
    import cv2

    from .reframe import YUNET

    try:  # OpenCV 5 dnn her çağrıda hedef uyarısı basıyor; ölçümü etkilemez
        cv2.utils.logging.setLogLevel(cv2.utils.logging.LOG_LEVEL_ERROR)
    except AttributeError:
        pass

    if not YUNET.exists():
        return None
    cap = cv2.VideoCapture(str(f))
    kfps = cap.get(cv2.CAP_PROP_FPS) or 30
    W, H = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    olcek = 480 / max(1, W)
    det = cv2.FaceDetectorYN.create(str(YUNET), "", (480, int(H * olcek)), score_threshold=0.7)
    kutular = []
    for t in np.linspace(bas, max(bas, bit - 0.1), 7):
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(round(t * kfps)))
        ok, kare = cap.read()
        if not ok:
            continue
        _, yuz = det.detect(cv2.resize(kare, (480, int(H * olcek))))
        if yuz is None or not len(yuz):
            continue
        y = max(yuz, key=lambda r: r[2] * r[3])
        (sx, sy), (lx, ly) = y[10:12], y[12:14]  # ağız sağ ve sol köşe
        gen = abs(lx - sx)
        x0, y0 = min(sx, lx) - gen * 0.35, (sy + ly) / 2 - gen * 0.55
        kutular.append((x0 / 480, y0 / (H * olcek), gen * 1.7 / 480, gen * 1.25 / (H * olcek)))
    cap.release()
    if len(kutular) < 3:
        return None
    x, y, w, h = (float(v) for v in np.median(np.asarray(kutular), axis=0))
    return max(0.0, x), max(0.0, y), min(w, 1 - max(0.0, x)), min(h, 1 - max(0.0, y))


def hareket_egrisi(f: Path, bas: float, bit: float, fps: float, bolge: tuple | None = None) -> np.ndarray:
    """Kaynak [bas, bit) aralığında, sekans fps'ine örneklenmiş hareket başlangıcı eğrisi (kare farkının artışı)."""
    import cv2

    cap = cv2.VideoCapture(str(f))
    kfps = cap.get(cv2.CAP_PROP_FPS) or fps
    ilk = int(round(bas * kfps))
    cap.set(cv2.CAP_PROP_POS_FRAMES, ilk)
    onceki, fark, zaman = None, [], []
    # WHY: POS_MSEC arka uca göre okunan ya da sıradaki kareyi verir; zaman kare sırasından hesaplanır.
    for n in range(ilk, 10**9):
        t = n / kfps
        ok, kare = cap.read()
        if not ok or t >= bit:
            break
        if bolge:
            H, W = kare.shape[:2]
            x, y, w, h = bolge
            kare = kare[int(y * H): int((y + h) * H), int(x * W): int((x + w) * W)]
        g = cv2.cvtColor(cv2.resize(kare, (160, max(1, int(160 * kare.shape[0] / kare.shape[1])))), cv2.COLOR_BGR2GRAY).astype(np.float32)
        if onceki is not None:
            fark.append(float(np.abs(g - onceki).mean()))
            zaman.append(t)
        onceki = g
    cap.release()
    if len(fark) < 4:
        return np.zeros(0)
    m = np.asarray(fark)
    artis = np.maximum(0, np.diff(m, prepend=m[0]))
    # Kaynak fps'i sekanstan farklı olabilir; eğri sekans karesine taşınır ki kayma doğrudan kare çıksın.
    return np.interp(np.arange(bas, bit, 1 / fps), zaman, artis)


def ses_egrisi(f: Path, onbellek: Path, bas: float, bit: float, fps: float) -> np.ndarray:
    import librosa

    y = ritim._yukle(f, onbellek)
    env = librosa.onset.onset_strength(y=y, sr=ritim.SR, hop_length=ritim.HOP)
    t = librosa.frames_to_time(np.arange(len(env)), sr=ritim.SR, hop_length=ritim.HOP)
    return np.interp(np.arange(bas, bit, 1 / fps), t, env)


def kayma(ses: np.ndarray, goruntu: np.ndarray, en_cok: int) -> tuple[int, float, float]:
    """Normalize çapraz ilişki: ses[i + L] ~ görüntü[i]. (L, tepe, belirginlik) döndürür."""
    n = min(len(ses), len(goruntu))
    if n < en_cok * 2 + 4:
        return 0, 0.0, 0.0
    a, b = ses[:n], goruntu[:n]
    a = (a - a.mean()) / (a.std() or 1)
    b = (b - b.mean()) / (b.std() or 1)
    skor = {}
    for L in range(-en_cok, en_cok + 1):
        if L >= 0:
            x, y = a[L:], b[: n - L]
        else:
            x, y = a[: n + L], b[-L:]
        skor[L] = float(np.dot(x, y) / len(x))
    sirali = sorted(skor.items(), key=lambda kv: -kv[1])
    L, tepe = sirali[0]
    # Belirginlik: tepenin tüm gecikmelerin ortancasından farkı. Komşu tepe (flaşın sönüşü, adımın ikinci vuruşu)
    # gerçek klipte de olur; ikinci en iyiyle kıyas güvenilir eşleşmeyi belirsiz sayıyordu.
    return L, max(0.0, tepe), max(0.0, tepe - float(np.median(list(skor.values()))))


def olc(p, k, klip_id: str, *, en_cok: int = 12) -> Olcum:
    from . import kurgu

    c = next((c for c in k.klipler if c.id == klip_id), None)
    if c is None or c.tur != "video" or not c.kaynak:
        raise SystemExit(f"{klip_id}: video klibi değil.")
    f = kurgu.dosya(p, k.kaynaklar[c.kaynak].yol)
    if not k.kaynaklar[c.kaynak].ses:
        raise SystemExit(f"{klip_id}: kaynağında ses yok.")
    fps = k.sekans.fps
    bas, bit = c.giris, c.giris + c.sure * c.hiz
    s = ses_egrisi(f, p.work / "ritim", bas, bit, fps)
    L, tepe, ayirt = kayma(s, hareket_egrisi(f, bas, bit, fps), en_cok)
    bolge = None
    if tepe < GUVEN_ESIGI * 1.6 and (bolge := agiz_bolgesi(f, bas, bit)):
        # Genel hareket zayıfsa konuşan kafa varsayılır: ağız bölgesiyle yeniden ölçülür, güçlü olan alınır.
        L2, t2, a2 = kayma(s, hareket_egrisi(f, bas, bit, fps, bolge), en_cok)
        if t2 > tepe:
            L, tepe, ayirt = L2, t2, a2
        else:
            bolge = None
    return Olcum(c.id, L, round(tepe, 3), round(ayirt, 3), fps, "ağız" if bolge else "kare")


def uygula(k, o: Olcum) -> str:
    """Ayrık ses klibini (aynı `bag`) kaymanın tersine kaydırır. Ayrılmamışsa ne yapılacağını söyler."""
    v = next(c for c in k.klipler if c.id == o.klip)
    sesler = [c for c in k.klipler if c.tur == "ses" and v.bag and c.bag == v.bag and (c.olay or {}).get("konusma")]
    if not sesler:
        raise SystemExit(f"{o.klip}: ses görüntüden ayrılmamış. Stüdyo'da klibi seçip Shift+A ile ayır, sonra --uygula.")
    dt = o.kayma_kare / o.fps
    for s in sesler:
        # Ses geç geliyorsa (L > 0) kaynakta daha ileriden okunur.
        s.giris = max(0.0, round(s.giris + dt, 4))
    return f"{len(sesler)} ses klibi {dt * 1000:+.0f} ms kaydırıldı."
