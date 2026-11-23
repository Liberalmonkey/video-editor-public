"""AI slop ölçümü: bitmiş videoda ritim, hareket, palet, ses ve metin kalıplarını zaman damgasıyla işaretler.

Çıktı karar değil şüphe listesidir; yargı ve düzeltme önerisi `denetim` skill'indedir. Motordan bağımsızdır,
yalnız mp4'e bakar. WHY: bkz. wiki/decisions/0015-ai-slop-denetimi.md
"""

from __future__ import annotations

import json
import re
import subprocess
import tempfile
from pathlib import Path


from .tembel import Tembel

# WHY: Stüdyo açılışında yüklenmesin (ADR 0050)
np = Tembel("numpy")

from . import ff

KISA_SURE = 120.0     # bu süreye kadar Reels/UGC eşikleri
OLCUM_FPS = 4
OLAY_YOGUN_DAKIKA = 6  # dakikada en çok zoom/punch olayı; üstü OLAY_YOGUN (ekip_v3.oto_duzelt aynı eşiği kullanır)
ZOOM_ROLLERI = ("zoom_in", "zoom_out", "punch_in")
W, H = 96, 54
DURGUN = 0.15         # kareler arası ortalama fark (0-255); altı "kıpırdamıyor"
SUZULME = 2.0         # üstü artık yavaş kamera hareketi sayılmaz

ONERI = {
    "RITIM_METRONOM": "Kesim sürelerini bilgi yoğunluğuna göre boz: hook 1-3 sn, açıklama 4-8 sn, büyük an 6-10 sn.",
    "RITIM_ESIT_BLOK": "Bu aralıkta bir kesimi kaldır ya da iki planı birleştir; bir planı belirgin kısalt.",
    "STATIK_UZUN": "Söylenen kelimede yeni öğe, B-roll ya da gerekçeli punch-in ekle.",
    "KEN_BURNS_HER_YERDE": "Süzülmeyi yalnız anlam taşıyan planda bırak, diğerlerini sabit tut ya da gerçek hareketli malzeme kullan.",
    "ACILIS_YAVAS": "İlk 3 sn içinde görsel değişim koy; en güçlü kareyi öne al.",
    "PALET_MOR": "Rengi konunun malzemesinden türet (çekim, marka, baskı); mor/çivit gradyanı kaldır.",
    "PALET_KOYU_SABLON": "Koyu zemini bir sahnede kır: gerçek görüntü, açık zemin ya da malzeme dokusu kullan.",
    "SES_NEFES_YOK": "Büyük andan önce 0.3-0.6 sn sessizlik aç; müziği tek bir yerde tamamen çek.",
    "SES_DUZ_DINAMIK": "Müziği bölüm geçişinde düşür ya da kes; miksi tek seviyede bırakma.",
    "SES_OLU_HAVA": "Bu aralığı kes ya da altına ortam sesi, müzik ya da söz koy; 3 sn'den uzun tam sessizlik izleyiciyi düşürür.",
    "OLAY_TEKDUZE": "Olayları sözün vurgusuna bağla, eşit aralıklı olanları sil.",
    "OLAY_TEK_TUR": "Geçişlerin çoğunu düz kesime çevir; özel geçişi yalnız konu değişiminde kullan.",
    "OLAY_YOGUN": "Her cümleye değil, yalnız kilit vurguya olay koy; gerisini sil.",
    "METIN_KLISE": "Cümleyi somut bilgiyle yeniden yaz (humanizer); kaydı yeniden almadan olmuyorsa kes.",
    "METIN_KARSITLIK": "\"X değil, Y\" kalıbının çoğunu düz cümleye çevir.",
}

# Slop kalıpları kasıtlı olarak kısa ve belirgin; "aynı zamanda" gibi olağan ifadeler listeye girmez.
KLISE = [
    "oyunun kuralları", "devrim niteliğinde", "devrim yarat", "bir üst seviye", "bir üst seviyeye", "yeni bir çağ",
    "hayal edin", "gelin birlikte", "günümüz dünyasında", "hiç olmadığı kadar", "sınırları zorl", "işte tam bu noktada",
    "işte burada devreye", "şaşırtıcı bir şekilde", "bir düşünün", "her şeyi değiştir", "kaçırmamanız gereken",
    "game changer", "game-changer", "seamless", "unlock", "elevate", "let's dive", "dive into", "in today's world",
    "revolutionary", "next level", "it's not just", "buckle up", "here's the thing",
]
KARSITLIK = re.compile(r"\b(sadece|yalnızca|yalnız)\b[^.!?]{1,50}\bdeğil\b|\bdeğil[,;]\s|\bnot just\b")


def bulgu(kod: str, seviye: str, bas: float | None, bit: float | None, kanit: str) -> dict:
    return {"kod": kod, "seviye": seviye, "bas": None if bas is None else round(float(bas), 2),
            "bit": None if bit is None else round(float(bit), 2), "kanit": kanit, "oneri": ONERI[kod]}


def _esit_bloklar(sureler: list[float], bas: float, *, en_az: int = 5, pay: float = 0.15) -> list[tuple[float, float, int]]:
    """Art arda en az `en_az` planın süresi medyanlarından ±pay içindeyse o bloğu döner."""
    out, i = [], 0
    while i < len(sureler):
        j = i + 1
        while j < len(sureler):
            m = float(np.median(sureler[i:j + 1]))
            if any(abs(s - m) > pay * m for s in sureler[i:j + 1]):
                break
            j += 1
        if j - i >= en_az:
            out.append((bas + sum(sureler[:i]), bas + sum(sureler[:j]), j - i))
            i = j
        else:
            i += 1
    return out


def ritim_analizi(kesimler: list[float], sure: float) -> list[dict]:
    noktalar = [0.0] + [k for k in kesimler if 0 < k < sure] + [sure]
    sureler = [b - a for a, b in zip(noktalar, noktalar[1:]) if b - a > 0.05]
    out = []
    if len(sureler) >= 6:
        ic = sureler[1:-1]  # ilk ve son plan genelde bilerek farklı uzunlukta
        cv = float(np.std(ic) / max(np.mean(ic), 0.01))
        if cv < 0.25:
            return out + [bulgu("RITIM_METRONOM", "P1", 0, sure,
                                f"{len(sureler)} plan, ortalama {np.mean(ic):.1f} sn, değişkenlik {cv:.2f} (eşik 0.25)")]
    for a, b, n in _esit_bloklar(sureler, 0.0):
        out.append(bulgu("RITIM_ESIT_BLOK", "P2", a, b, f"art arda {n} plan neredeyse aynı uzunlukta"))
    return out


def hareket_analizi(fark: np.ndarray, kesimler: list[float], sure: float, fps: float = OLCUM_FPS) -> list[dict]:
    """fark: ardışık ölçüm kareleri arasındaki ortalama mutlak fark."""
    out, esik = [], 5.0 if sure <= KISA_SURE else 10.0
    ilk = fark[:int(3 * fps)]
    if sure > 3 and len(ilk) and float(ilk.max()) < 1.0 and not any(k < 3 for k in kesimler):
        out.append(bulgu("ACILIS_YAVAS", "P1", 0, 3, "ilk 3 sn görüntü neredeyse hiç değişmiyor"))
    i = 0
    while i < len(fark):
        if fark[i] < DURGUN:
            j = i
            while j < len(fark) and fark[j] < DURGUN:
                j += 1
            if (j - i) / fps >= esik:
                d = (j - i) / fps
                out.append(bulgu("STATIK_UZUN", "P1" if d >= 20 else "P2", i / fps, j / fps, f"{d:.1f} sn görüntü kıpırdamıyor"))
            i = j
        else:
            i += 1
    noktalar = [0.0] + [k for k in kesimler if 0 < k < sure] + [sure]
    planlar = sabit = 0
    for a, b in zip(noktalar, noktalar[1:]):
        p = fark[int(a * fps) + 1:int(b * fps) - 1]
        if b - a < 2 or len(p) < 4:
            continue
        planlar += 1
        # Ken Burns imzası: düşük ama sıfır olmayan ve kare kare çok düzenli değişim
        if DURGUN < np.median(p) < SUZULME and np.std(p) / max(np.mean(p), 0.01) < 0.35:
            sabit += 1
    if planlar >= 4 and sabit / planlar >= 0.6:
        out.append(bulgu("KEN_BURNS_HER_YERDE", "P1", 0, sure, f"{planlar} planın {sabit} tanesinde düzenli yavaş süzülme"))
    return out


def palet_analizi(rgb: np.ndarray) -> list[dict]:
    """rgb: (kare, yükseklik, genişlik, 3) uint8."""
    if not len(rgb):
        return []
    x = rgb.astype(np.float32) / 255
    mx, mn = x.max(-1), x.min(-1)
    c = mx - mn
    sat = np.where(mx > 0, c / np.maximum(mx, 1e-6), 0)
    r, g, b = x[..., 0], x[..., 1], x[..., 2]
    hue = np.where(mx == r, (g - b) / np.maximum(c, 1e-6) % 6,
                   np.where(mx == g, (b - r) / np.maximum(c, 1e-6) + 2, (r - g) / np.maximum(c, 1e-6) + 4)) * 60
    mor = (hue >= 235) & (hue <= 300) & (sat > 0.35) & (mx > 0.25)
    mor_kare = float((mor.mean((1, 2)) > 0.25).mean())
    koyu_kare = float(((mx < 0.16).mean((1, 2)) > 0.7).mean())
    out = []
    if mor_kare > 0.3:
        out.append(bulgu("PALET_MOR", "P1", None, None, f"karelerin %{mor_kare * 100:.0f}'inde mor/çivit alan %25'ten büyük"))
    if koyu_kare > 0.7:
        out.append(bulgu("PALET_KOYU_SABLON", "P2", None, None, f"karelerin %{koyu_kare * 100:.0f}'i siyaha yakın zemin"))
    return out


def ses_zarfi(wav: Path, pencere: float = 0.1) -> np.ndarray:
    """100 ms pencerelerde RMS, dB."""
    import soundfile as sf
    x, sr = sf.read(str(wav), dtype="float32", always_2d=True)
    x = x.mean(1)
    n = int(pencere * sr)
    if len(x) < n:
        return np.empty(0)
    k = len(x) // n
    return 20 * np.log10(np.sqrt((x[:k * n].reshape(k, n) ** 2).mean(1)) + 1e-6)


def ses_analizi(zarf: np.ndarray, lra: float | None, sure: float, pencere: float = 0.1) -> list[dict]:
    """Nefes: en az 0.3 sn boyunca medyanın 8 dB altına düşen an. Müzik altında konuşma duraklaması da sayılır."""
    out = []
    if len(zarf) and sure > 20:
        taban = float(np.median(zarf)) - 8
        nefesler, i = [0.0], 0
        while i < len(zarf):
            if zarf[i] < taban:
                j = i
                while j < len(zarf) and zarf[j] < taban:
                    j += 1
                if (j - i) * pencere >= 0.3:
                    nefesler.append(i * pencere)
                i = j
            else:
                i += 1
        nefesler.append(sure)
        a, b = max(zip(nefesler, nefesler[1:]), key=lambda c: c[1] - c[0])
        if b - a > 30:
            out.append(bulgu("SES_NEFES_YOK", "P2", a, b, f"{b - a:.0f} sn boyunca belirgin ses düşüşü yok"))
    # WHY: ADR 0040 (open-edit dead-air eşiği). Nefes 0,3-0,6 sn'dir; 3 sn'den uzun tam sessizlik kusurdur.
    if len(zarf):
        sessiz = zarf < -50
        i = 0
        while i < len(sessiz):
            if not sessiz[i]:
                i += 1
                continue
            j = i
            while j < len(sessiz) and sessiz[j]:
                j += 1
            if (j - i) * pencere >= 3.0 and i * pencere > 0.5 and j * pencere < sure - 0.5:
                out.append(bulgu("SES_OLU_HAVA", "P1", i * pencere, j * pencere, f"{(j - i) * pencere:.1f} sn tam sessizlik (-50 dB altı)"))
            i = j
    if lra is not None and sure > 30 and lra < 2.5:
        out.append(bulgu("SES_DUZ_DINAMIK", "P2", 0, sure, f"LRA {lra:.1f} LU (eşik 2.5)"))
    return out


def olay_analizi(spec: dict, sure: float) -> list[dict]:
    from .olaysesi import olay_ani
    fps = float(spec.get("fps") or 30)
    olaylar = sorted(spec.get("olaylar", []), key=lambda o: olay_ani(o, fps))
    out = []
    zoomlar = [olay_ani(o, fps) for o in olaylar if str(o.get("tur")) in ZOOM_ROLLERI]
    if len(zoomlar) >= 6:
        ara = np.diff(zoomlar)
        cv = float(np.std(ara) / max(np.mean(ara), 0.01))
        if cv < 0.3:
            out.append(bulgu("OLAY_TEKDUZE", "P1", zoomlar[0], zoomlar[-1], f"{len(zoomlar)} zoom eşit aralıkla (değişkenlik {cv:.2f})"))
    gecis = [str(o.get("ad") or o.get("tur")) for o in olaylar if "gecis" in str(o.get("tur"))]
    if len(gecis) >= 5:
        en = max(set(gecis), key=gecis.count)
        if gecis.count(en) / len(gecis) >= 0.8:
            out.append(bulgu("OLAY_TEK_TUR", "P2", None, None, f"{len(gecis)} geçişin {gecis.count(en)} tanesi '{en}'"))
    if sure > 0 and len(zoomlar) / (sure / 60) > OLAY_YOGUN_DAKIKA:
        out.append(bulgu("OLAY_YOGUN", "P1", None, None, f"dakikada {len(zoomlar) / (sure / 60):.1f} zoom"))
    return out


def metin_analizi(kelimeler: list[dict]) -> list[dict]:
    """kelimeler: {"w","s"}. Süresiz düz metin için s None olabilir."""
    parca, konum, uz = [], [], 0
    for w in kelimeler:
        k = w["w"].strip().replace("İ", "i").replace("I", "ı").lower().replace("’", "'")
        parca.append(k)
        konum.append((uz, w.get("s")))
        uz += len(k) + 1
    metin = " ".join(parca)

    def zaman(i: int):
        son = None
        for bas, s in konum:
            if bas > i:
                break
            son = s
        return son

    out = []
    for kalip in KLISE:
        for m in re.finditer(re.escape(kalip), metin):
            t = zaman(m.start())
            out.append(bulgu("METIN_KLISE", "P2", t, t, f'"{kalip}"'))
    if len(out) >= 4:
        for o in out:
            o["seviye"] = "P1"
    karsit = [zaman(m.start()) for m in KARSITLIK.finditer(metin)]
    if len(karsit) >= 3:
        out.append(bulgu("METIN_KARSITLIK", "P2", karsit[0], karsit[-1], f"{len(karsit)} kez \"X değil, Y\" kalıbı"))
    return out


# ---------------------------------------------------------------- video okuma


def kesimleri_bul(video: Path, esik: float = 0.3) -> list[float]:
    # shortcut: yumuşak geçişler kesim sayılmaz; olaylar.json verilince geçişler oradan da denetlenir.
    proc = ff.ffmpeg("-i", str(video), "-an", "-vf", f"select='gt(scene,{esik})',showinfo", "-f", "null", "-", check=False)
    return [float(m) for m in re.findall(r"pts_time:([\d.]+)", proc.stderr or "")]


def kareleri_oku(video: Path) -> tuple[np.ndarray, np.ndarray]:
    """Ölçüm karelerini akıtır; ardışık farkı ve saniyede bir kare RGB örneğini döner."""
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(video), "-an", "-vf", f"fps={OLCUM_FPS},scale={W}:{H}",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    fark, ornek, onceki, i = [], [], None, 0
    while True:
        ham = p.stdout.read(W * H * 3)
        if len(ham) < W * H * 3:
            break
        kare = np.frombuffer(ham, np.uint8).reshape(H, W, 3)
        gri = kare.mean(-1)
        if onceki is not None:
            fark.append(float(np.abs(gri - onceki).mean()))
        onceki = gri
        if i % OLCUM_FPS == 0:
            ornek.append(kare)
        i += 1
    p.wait()
    return np.array(fark), np.array(ornek) if ornek else np.empty((0, H, W, 3), np.uint8)


def calistir(video: Path, cikti: Path, *, olaylar: Path | None = None, metin: Path | None = None,
             yazisiz: bool = False, dil: str | None = None, lra: float | None = None) -> dict:
    info = ff.probe(video)
    sure = float(info["duration"])
    kesimler = kesimleri_bul(video)
    fark, ornek = kareleri_oku(video)
    bulgular = ritim_analizi(kesimler, sure) + hareket_analizi(fark, kesimler, sure) + palet_analizi(ornek)
    metin_durumu = "yok"
    if olaylar and olaylar.exists():
        bulgular += olay_analizi(json.loads(olaylar.read_text(encoding="utf-8")), sure)
    if metin:
        bulgular += metin_analizi([{"w": w, "s": None} for w in metin.read_text(encoding="utf-8").split()])
        metin_durumu = "dosya"
    if info.get("audio"):
        with tempfile.TemporaryDirectory() as td:
            wav = ff.extract_audio(video, Path(td) / "slop.wav")
            bulgular += ses_analizi(ses_zarfi(wav), ff.loudness(video).get("LRA") if lra is None else lra, sure)
            if not metin and not yazisiz:
                from . import transcribe
                tr = transcribe.transcribe_file(wav, language=dil, model_name=transcribe.DEFAULT_MODEL)
                bulgular += metin_analizi([w for s in tr["segments"] for w in s["words"]])
                metin_durumu = "transkript"
    bulgular.sort(key=lambda b: (b["seviye"], b["bas"] if b["bas"] is not None else -1))

    # Klişe testi kareleri + şüpheli anlar: göz denetimi bunlara bakar.
    ani = [t for t in (0.2, 1, 3, 6, 10, sure - 0.2) if t < sure]
    for b in bulgular:
        if b["bas"] is not None and b["bit"] is not None:
            ani.append((b["bas"] + b["bit"]) / 2)
    ani = sorted({round(t, 1) for t in ani})[:24]
    cikti.mkdir(parents=True, exist_ok=True)
    sayfa = ff.contact_sheet(video, cikti / "slop-kareler.jpg", duration=sure, times=ani, cols=4, width=360)
    rep = {"video": str(video), "sure": round(sure, 2), "plan": len(kesimler) + 1, "metin_kaynagi": metin_durumu,
           "kareler": str(sayfa), "bulgular": bulgular}
    (cikti / "slop-olcum.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    return rep
