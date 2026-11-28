"""Proxy (vekil) yaşam döngüsü: ağır kaynağa hafif kopya, kurguda ve taslakta o; teslimde orijinal.

WHY: bkz. wiki/decisions/0060-proxy-master-conform.md. 4K, HEVC, 10-bit, HDR ve VFR kaynak Stüdyo'da takılır, taslak
render'ında HyperFrames her klibin karesini tam çözünürlükte çıkarır. Proxy yalnız düzenleme ve taslak içindir; final
`work/public/_k/` bağlantılarını orijinale (ya da master SDR kopyasına) geri bağlar ve `conform_denetle` bunu doğrular.

İki katman:
- `onizleme`: 540p, Stüdyo Player'ı (sık anahtar kare, B-kare yok: sarma gecikmesi düşük).
- `taslak`: kısa kenar 1080, taslak ve QC render'ı.
"""

from __future__ import annotations

import hashlib
import json
import threading
from pathlib import Path

from . import ff

KATMAN = {"onizleme": 540, "taslak": 1080}
CRF = {"onizleme": 23, "taslak": 18}
BAGLANABILIR = {".mp4", ".mov", ".m4v"}  # proxy mp4'ü orijinalin adıyla bağlanır; bu kapsayıcılar H.264'ü taşır
AGIR_KODEK = {"hevc", "prores", "dnxhd", "av1", "vp9"}
AGIR_MBPS = 50
SURE_TOLERANS = 0.1  # sn; CFR'ye çevirme son kareyi oynatabilir
_kilit = threading.Lock()
_suren: set[str] = set()


def imza(f: Path) -> str:
    """İçerik özeti (boyut + baş + son MB). `hizli._ozet` ile aynı kural; taşınan dosyada da geçerli."""
    st = f.stat()
    h = hashlib.sha1(str(st.st_size).encode())
    with f.open("rb") as d:
        h.update(d.read(1 << 20))
        d.seek(max(0, st.st_size - (1 << 20)))
        h.update(d.read(1 << 20))
    return h.hexdigest()[:12]


def neden(info: dict) -> list[str]:
    """Proxy gerektiren özellikler; boşsa kaynak doğrudan oynar."""
    v = info.get("video") or {}
    if not v or v.get("alfa"):
        return []
    n = []
    if min(v.get("width", 0), v.get("height", 0)) > 1080:
        n.append(f"{v['width']}x{v['height']}")
    if v.get("codec") in AGIR_KODEK:
        n.append(str(v["codec"]))
    if "10" in str(v.get("pix_fmt") or "") or "12" in str(v.get("pix_fmt") or ""):
        n.append(str(v["pix_fmt"]))
    if ff.hdr_mi(info):
        n.append("HDR")
    if v.get("vfr"):
        n.append("VFR")
    if v.get("bit_rate", 0) / 1e6 > AGIR_MBPS:
        n.append(f"{v['bit_rate'] / 1e6:.0f} Mbps")
    return n


def gerekli(info: dict) -> bool:
    return bool(neden(info))


def klasor(work: Path) -> Path:
    return work / "proxy"


def yol(work: Path, kaynak: Path, katman: str = "onizleme") -> Path:
    ek = "" if katman == "onizleme" else f"-{katman}"  # onizleme adı eski Stüdyo proxy'leriyle aynı kalır
    return klasor(work) / f"{kaynak.stem}-{imza(kaynak)}{ek}.mp4"


def _filtre(info: dict, katman: str, fps: float | None) -> str:
    kisa = KATMAN[katman]
    v = info["video"]
    olcek = f"scale='if(gt(iw,ih),-2,{kisa})':'if(gt(iw,ih),{kisa},-2)':flags=bicubic"
    if min(v["width"], v["height"]) <= kisa:
        olcek = "null"
    zincir = [ff.sdr_zinciri(v)] if ff.hdr_mi(info) else []
    zincir.append(olcek)
    if fps:
        zincir.append(f"fps={fps:g}")
    zincir.append("format=yuv420p")
    return ",".join(zincir)


def uret(work: Path, kaynak: Path, katman: str = "onizleme", *, fps: float | None = None) -> Path | None:
    """Proxy'yi üretir (varsa dokunmaz). Aynı dosya için ikinci çağrı beklemeden döner (None)."""
    hedef = yol(work, kaynak, katman)
    if hedef.exists():
        return hedef
    anahtar = str(hedef)
    with _kilit:
        if anahtar in _suren:
            return None
        _suren.add(anahtar)
    gecici: Path | None = None
    try:
        info = ff.probe(kaynak)
        v = info["video"]
        # VFR kaynak sabit hıza çevrilir; hız bilinmiyorsa kaynağın ortalaması
        fps = fps or (round(v["fps"]) if v.get("vfr") and v.get("fps") else None)
        hedef.parent.mkdir(parents=True, exist_ok=True)
        gecici = hedef.with_name(f".{hedef.stem}.tmp.mp4")
        ses = ["-c:a", "aac", "-b:a", "128k"] if katman == "onizleme" else ["-c:a", "copy"]
        r = ff.ffmpeg("-i", str(kaynak), "-map", "0:v:0", "-map", "0:a:0?", "-vf", _filtre(info, katman, fps),
                      "-c:v", "libx264", "-preset", "veryfast", "-crf", str(CRF[katman]), "-g", "12", "-bf", "0",
                      "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-color_range", "tv",
                      *ses, "-movflags", "+faststart", str(gecici), check=False)
        if r.returncode and katman != "onizleme":  # ses kapsayıcıya sığmadıysa (pcm → mp4) yeniden kodla
            ff.ffmpeg("-i", str(kaynak), "-map", "0:v:0", "-map", "0:a:0?", "-vf", _filtre(info, katman, fps),
                      "-c:v", "libx264", "-preset", "veryfast", "-crf", str(CRF[katman]), "-g", "12", "-bf", "0",
                      "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-color_range", "tv",
                      "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", str(gecici))
        elif r.returncode:
            raise RuntimeError(f"Proxy üretilemedi: {kaynak.name}\n{(r.stderr or '')[-800:]}")
        if not esles(kaynak, gecici, info):
            raise RuntimeError(f"Proxy süresi kaynakla eşleşmedi: {kaynak.name}")
        gecici.replace(hedef)
        _kayit_yaz(work, kaynak, hedef, katman, info)
        return hedef
    finally:
        # WHY: ff.ffmpeg veya süre uyuşmazlığı hatasında work/proxy altında .tmp.mp4 kalmasın.
        if gecici is not None:
            gecici.unlink(missing_ok=True)
        with _kilit:
            _suren.discard(anahtar)


def esles(kaynak: Path, proxy: Path, info: dict | None = None) -> bool:
    """Proxy kaynağın yerine geçebilir mi: süre ±0,1 sn, yön aynı."""
    a, b = info or ff.probe(kaynak), ff.probe(proxy)
    va, vb = a.get("video") or {}, b.get("video") or {}
    if not va or not vb:
        return False
    ayni_yon = (va["width"] >= va["height"]) == (vb["width"] >= vb["height"])
    return ayni_yon and abs(a["duration"] - b["duration"]) <= SURE_TOLERANS


def _kayit_yolu(work: Path) -> Path:
    return klasor(work) / "vekil.json"


def kayitlar(work: Path) -> dict:
    try:
        return json.loads(_kayit_yolu(work).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _kayit_yaz(work: Path, kaynak: Path, proxy: Path, katman: str, info: dict) -> None:
    with _kilit:
        k = kayitlar(work)
        k.setdefault(kaynak.name, {})[katman] = {"dosya": proxy.name, "imza": imza(kaynak), "neden": neden(info),
                                                 "sure": info["duration"]}
        _kayit_yolu(work).parent.mkdir(parents=True, exist_ok=True)
        _kayit_yolu(work).write_text(json.dumps(k, ensure_ascii=False, indent=1), encoding="utf-8")


def hazir(work: Path, kaynak: Path, katman: str) -> Path | None:
    """Hazır ve güncel proxy; yoksa None (üretmez)."""
    try:
        f = yol(work, kaynak, katman)
    except OSError:
        return None
    return f if f.is_file() else None


def arka_planda(work: Path, kaynaklar: list[Path], katmanlar: tuple[str, ...] = ("onizleme", "taslak")) -> list[threading.Thread]:
    """Gerekli olan kaynaklar için proxy üretimini iş parçacığında başlatır; parçacıkları döner (CLI bitmeden `join`).

    Aynı anda en çok iki ffmpeg (makine transkript ve render ile de yarışır).
    """
    isler = []
    for f in kaynaklar:
        if f.suffix.lower() not in BAGLANABILIR or not f.is_file():
            continue
        try:
            info = ff.probe_ob(f)
        except Exception:  # WHY: okunamayan dosya hattı düşürmesin; render zaten hata verir
            continue
        if not gerekli(info):
            continue
        for katman in katmanlar:
            if not hazir(work, f, katman):
                t = threading.Thread(target=sessiz_uret, args=(work, f, katman), daemon=True)
                t.start()
                isler.append(t)
    return isler


_sinir = threading.BoundedSemaphore(2)


def sessiz_uret(work: Path, f: Path, katman: str) -> None:
    try:
        with _sinir:
            uret(work, f, katman)
    except Exception as e:  # WHY: arka plan işi; hata yalnız raporlanır, orijinal oynamaya devam eder
        print(f"  ! proxy ({katman}) üretilemedi: {f.name}: {str(e)[:200]}", flush=True)


def conform_denetle(public: Path, beklenen: dict[str, Path]) -> list[str]:
    """Final öncesi: her `_k/<ad>` bağlantısı beklenen master dosyası mı. Hata listesi (boşsa geçti).

    `beklenen`: bağlantı adı → master dosya (orijinal ya da master SDR kopyası).
    """
    hatalar = []
    for ad, master in beklenen.items():
        bag = public / "_k" / ad
        if not bag.exists():
            hatalar.append(f"{ad}: bağlantı yok")
        elif not bag.samefile(master):
            hatalar.append(f"{ad}: master değil (proxy ya da eski kopya)")
    return hatalar
