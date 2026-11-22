"""kurgu.json → HyperFrames render (ADR 0051): derleme, motor seçimi, render.

WHY: bkz. wiki/decisions/0051-uctan-uca-hyperframes.md. Derleyici TypeScript'tir (`studio/hf/derle.ts`) ve Stüdyo
önizlemesiyle aynı kodu çalıştırır; burada `studio/hf/cli.ts` vite-node ile çağrılır. Proje klasörü `work/public`'tir:
medya `_k/` hardlink'leri ve fontlar orada (kurgu.hazirla), HyperFrames proje dışındaki dosyayı okumaz.

Motor seçimi: kurgu `motor` alanı `hf` ya da `remotion` ise o; `oto` ise derleyicinin `desteklenmeyen` listesi boş ve
`library/hf_motor.json` `oto_hf: true` ise HyperFrames, değilse Remotion (son çare). Karar `work/edit/motor.json`'a yazılır.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import time
from pathlib import Path

from . import hf, hf_grafik, motion, paths

STUDIO = paths.ROOT / "studio"
AYAR = paths.LIBRARY / "hf_motor.json"


def _vite_node() -> list[str]:
    exe = STUDIO / "node_modules" / ".bin" / ("vite-node.cmd" if os.name == "nt" else "vite-node")
    return [str(exe), "--config", "web/vite.config.ts", "hf/cli.ts", "--"]


def _cli(props: Path, proje: Path, *ek: str) -> dict:
    r = subprocess.run([*_vite_node(), str(props.resolve()), str(proje.resolve()), *ek], cwd=STUDIO, capture_output=True,
                       text=True, encoding="utf-8", errors="replace", shell=os.name == "nt")
    satir = next((s for s in reversed(r.stdout.strip().splitlines()) if s.startswith("{")), None)
    if r.returncode or not satir:
        raise RuntimeError(f"HyperFrames derleyicisi durdu:\n{(r.stderr or r.stdout)[-1500:]}")
    return json.loads(satir)


def _hf_kutuphane() -> Path:
    return paths.LIBRARY / "motion" / "hf"


def native_harita() -> dict[str, dict]:
    """Taşınmış native bileşenler: ad → {meta, varsayilan}. `studio/hf/paketle.ts` nativeHarita ile aynı kural.

    WHY: ADR 0051. Stüdyo önizlemesi derleyiciyi tarayıcıda çalıştırır; hangi bileşenin HyperFrames sahnesi olduğunu ve
    meta/varsayılanını buradan alır. Kaynak library/motion/native/sema.json, klasörde meta.json/sema.json varsa o.
    """
    sema = json.loads((paths.LIBRARY / "motion" / "native" / "sema.json").read_text(encoding="utf-8"))["bilesenler"]
    cikti: dict[str, dict] = {}
    for d in sorted(_hf_kutuphane().iterdir()):
        if not (d / "sahne.html").is_file():
            continue
        ad = d.name.replace("-", "/", 1)
        yerel = {n: json.loads((d / n).read_text(encoding="utf-8")) for n in ("meta.json", "sema.json") if (d / n).is_file()}
        meta = yerel.get("meta.json") or sema.get(ad, {}).get("meta")
        sm = yerel.get("sema.json") or sema.get(ad, {}).get("sema") or {}
        if not meta:
            continue
        varsayilan = {k: v["default"] for k, v in (sm.get("properties") or {}).items() if "default" in v}
        cikti[ad] = {"meta": meta, "varsayilan": varsayilan}
    return cikti


def sahne_kopyasi(dizin: str, kok: str, w: int, h: int) -> str | None:
    """Bir bağlamanın sahne dosyası (paketle.ts sahneKopyasi ile aynı yer değiştirme); bilinmeyen dizin None."""
    f = _hf_kutuphane() / dizin / "sahne.html"
    if "/" in dizin or "\\" in dizin or not f.is_file():
        return None
    return f.read_text(encoding="utf-8").replace("__KOK__", kok).replace("__W__", str(w)).replace("__H__", str(h))


def desteklenmeyen(props: Path) -> list[str]:
    """Render'da HyperFrames'in yapamadığı özellikler. Fizik ve karakter sahnesi ön render ile yapılır (on_render)."""
    return _cli(props, props.parent, "--denetle", "--on-render")["desteklenmeyen"]


ON_RENDER_TURLERI = ("fizik", "karakter")


def on_render(p, props: Path, proje: Path, *, olcek: float = 1.0, pencere: tuple[float, float] | None = None) -> dict[str, str]:
    """Fizik ve karakter sahnelerini (three.js, ADR 0039) tek tek Remotion'da saydam webm'e alır; klip kimliği → adres.

    WHY: bkz. wiki/decisions/0051-uctan-uca-hyperframes.md. Sahneler React Three Fiber ve post-processing ile çizilir;
    HyperFrames'te birebir yeniden yazmak bloom, gölge ve sarsıntıyı riske atardı. Planın son çare yolu: yalnız o sahne
    Remotion'da, sonuç HyperFrames'e video klibi olarak girer. Önbellek: klip, bake verisi, tema ve ölçek değişince yenilenir.
    """
    import copy
    import hashlib

    from . import hizli
    d = json.loads(props.read_text(encoding="utf-8"))
    gizli = {i["id"] for i in d["izler"] if i.get("gizli")}
    hedef_k = proje / "hf" / "onrender"
    eslem: dict[str, str] = {}
    for k in d["klipler"]:
        s = k.get("sahne") or {}
        if k.get("tur") != "sahne" or s.get("kind") not in ON_RENDER_TURLERI or k["iz"] in gizli:
            continue
        if pencere and (k["bas"] + k["sure"] <= pencere[0] or k["bas"] >= pencere[1]):
            continue
        tek = copy.deepcopy(d)
        tek["klipler"] = [{**k, "bas": 0.0}]
        tek["izler"] = [i for i in d["izler"] if i["id"] == k["iz"]]
        tek["altyazi"] = {**d["altyazi"], "acik": False}
        tek["words"], tek["bitis"] = [], k["sure"]
        ham = json.dumps(tek, ensure_ascii=False, sort_keys=True)
        o = hashlib.sha1(ham.encode())
        if k.get("kaynak") and (y := d["kaynaklar"].get(k["kaynak"], {}).get("yol", "")).startswith("public:"):
            veri = p.work / "public" / y[7:]
            o.update(veri.read_bytes() if veri.is_file() else b"")
        o.update(f"{olcek:g}".encode())
        ad = f"{re.sub(r'[^A-Za-z0-9_-]', '_', k['id'])}-{o.hexdigest()[:10]}.webm"
        hedef = hedef_k / ad
        if not hedef.exists():
            hedef_k.mkdir(parents=True, exist_ok=True)
            tp = props.parent / f"kurgu.render.onrender-{k['id']}.json"
            tp.write_text(ham, encoding="utf-8")
            gecici = hedef.with_name(f".{ad}")
            print(f"  ön render (Remotion, {s.get('kind')}): {k['id']} · {k['sure']:g} sn", flush=True)
            try:
                hizli._remotion(tp, p.work / "public", gecici, "--codec=vp9", "--pixel-format=yuva420p", "--image-format=png",
                                *([f"--scale={olcek:g}"] if olcek != 1 else []))
                gecici.replace(hedef)
            finally:
                tp.unlink(missing_ok=True)
                gecici.unlink(missing_ok=True)
        eslem[k["id"]] = f"hf/onrender/{ad}"
    return eslem


def tema_css(tema: str | Path | None) -> str:
    """Seçili stilin token CSS'i + yazı tipleri; `hf/tema.css` konumuna göre `../fonts/` (work/public/fonts)."""
    t = motion.tema_yolu(tema) or motion.tema_yolu("varsayilan")
    return hf_grafik._font_css().replace('url("fonts/', 'url("../fonts/') + "\n" + (t.read_text(encoding="utf-8") if t else "")


def ayar() -> dict:
    try:
        return json.loads(AYAR.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"oto_hf": False}


def motor_sec(p, props: Path, *, olcek: bool = False) -> tuple[str, str]:
    """(motor, neden). Remotion yalnız HyperFrames yapamıyorsa ya da hız kapısı henüz açılmadıysa."""
    from . import kurgu
    istek = kurgu.oku(p.work).motor if kurgu.yol(p.work).exists() else "remotion"
    if not props.name.startswith("kurgu.render"):
        secim = ("remotion", "eski SplitReel projesi")
    elif istek == "remotion":
        secim = ("remotion", "kurgu motor: remotion")
    else:
        try:
            eksik = desteklenmeyen(props)
        except RuntimeError as e:
            eksik = [f"derleyici hatası: {str(e)[:120]}"]
        if olcek:
            eksik.append("çözünürlük ölçeği")
        if eksik:
            secim = ("remotion", "HyperFrames'te henüz yok: " + ", ".join(eksik))
        elif istek == "hf" or ayar().get("oto_hf"):
            secim = ("hf", "tüm özellikler HyperFrames'te")
        else:
            secim = ("remotion", "oto: HyperFrames hız kapısı henüz açılmadı (library/hf_motor.json)")
    (p.work / "edit").mkdir(parents=True, exist_ok=True)
    (p.work / "edit" / "motor.json").write_text(json.dumps({"motor": secim[0], "neden": secim[1], "istek": istek,
                                                            "zaman": time.strftime("%Y-%m-%dT%H:%M:%S")}, ensure_ascii=False),
                                                encoding="utf-8")
    return secim


def hazirla(p, props: Path, *, olcek: float = 1.0, pencere: tuple[float, float] | None = None) -> Path:
    """work/public'e index.html, hf/calisma.js, hf/gsap.min.js, hf/tema.css yazar; proje klasörünü döner.

    WHY: ADR 0051 hız. `olcek` taslağı yarım çözünürlükte çizer; `pencere` aralık render'ında yalnız o aralığa değen
    klipleri derler (HyperFrames her medya klibinin karelerini çıkarıp özetler, pencere dışı klip boşuna maliyet).
    """
    from . import kurgu
    proje = p.work / "public"
    (proje / "hf").mkdir(parents=True, exist_ok=True)
    k = kurgu.oku(p.work)
    (proje / "hf" / "tema.css").write_text(tema_css(kurgu.etkin_tema(p, k.motion_tema)), encoding="utf-8")
    ek = (["--olcek", f"{olcek:g}"] if olcek != 1 else []) + (["--pencere", f"{pencere[0]:g},{pencere[1]:g}"] if pencere else [])
    if eslem := on_render(p, props, proje, olcek=olcek, pencere=pencere):
        (proje / "hf" / "onrender.json").write_text(json.dumps(eslem), encoding="utf-8")
        ek += ["--onrender", str((proje / "hf" / "onrender.json").resolve())]
    _cli(props, proje, *ek)
    return proje


def bos_bellek_gb() -> float | None:
    """Boş fiziksel bellek (GB). Windows'ta GlobalMemoryStatusEx, Linux'ta /proc/meminfo; okunamazsa None."""
    try:
        if os.name == "nt":
            import ctypes

            class _Durum(ctypes.Structure):
                _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong), ("ullTotalPhys", ctypes.c_ulonglong),
                            ("ullAvailPhys", ctypes.c_ulonglong), ("ullTotalPageFile", ctypes.c_ulonglong),
                            ("ullAvailPageFile", ctypes.c_ulonglong), ("ullTotalVirtual", ctypes.c_ulonglong),
                            ("ullAvailVirtual", ctypes.c_ulonglong), ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]

            d = _Durum()
            d.dwLength = ctypes.sizeof(_Durum)
            if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(d)):
                return None
            return d.ullAvailPhys / 2**30
        for satir in Path("/proc/meminfo").read_text().splitlines():
            if satir.startswith("MemAvailable:"):
                return int(satir.split()[1]) / 2**20
    except (OSError, AttributeError, ValueError):
        return None
    return None


# Boş belleğe göre işçi: (eşik GB, işçi). Eşiğin altındaysa o işçi sayısı; hepsinin üstünde 0 (HyperFrames otomatik, 4).
BELLEK_ISCI = ((3.0, 1), (6.0, 2))


def isci_sec(istenen: int = 0, bos: float | None = None) -> int:
    """Render işçi sayısı. Açık istek (isci > 0) ya da VEDIT_HF_ISCI ortam değişkeni kazanır; yoksa boş belleğe göre."""
    # WHY: instagram/1 ekip koşusu (2026-11-22) G3 taslak render'ında bellek doldu (15,8 GB makine, ~5,8 GB boş);
    # 4 işçi 4 headless Chrome açıyor, aynı anda ekip ajanları da bellekte. Bellek darken işçi azalır, render yavaşlar ama düşmez.
    if istenen:
        return istenen
    if (ortam := os.environ.get("VEDIT_HF_ISCI", "").strip()).isdigit():
        return int(ortam)
    bos = bos_bellek_gb() if bos is None else bos
    if bos is None:
        return 0
    return next((n for esik, n in BELLEK_ISCI if bos < esik), 0)


def render(p, props: Path, cikti: Path, *, kalite: str = "draft", aralik: tuple[float, float] | None = None,
           fps: int | None = None, olcek: float = 1.0, crf: int | None = None, isci: int = 0) -> Path:
    proje = hazirla(p, props, olcek=olcek, pencere=aralik)
    cikti.parent.mkdir(parents=True, exist_ok=True)
    # WHY: ölçüldü (instagram/1, 2026-11-22): otomatik işçi (4) en hızlısı; 8 işçi bellek yüzünden 1,8 kat yavaş.
    # isci: 0 otomatik; bellek darsa isci_sec 2'ye ya da 1'e düşürür.
    bos = bos_bellek_gb()
    isci = isci_sec(isci, bos)
    print(f"  HyperFrames render · {kalite}" + (f" · ölçek {olcek:g}" if olcek != 1 else "")
          + (f" · {aralik[0]:g}-{aralik[1]:g} sn" if aralik else "")
          + f" · işçi {isci or 'otomatik'}" + (f" (boş bellek {bos:.1f} GB)" if bos is not None else ""), flush=True)
    t0 = time.time()
    hf.render(proje, cikti, quality=kalite, fps=fps, workers=isci, crf=crf)
    print(f"  HyperFrames bitti · {time.time() - t0:.0f} sn", flush=True)
    return cikti
