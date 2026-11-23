"""Native Remotion motion bileşenleri: kayıt, parametre doğrulama, zanaat kapıları.

WHY: bkz. wiki/decisions/0045-native-motion.md. Bileşen kodu ve Zod şeması `studio/remotion/motion/` altındadır;
`npm run sema` her bileşenin şemasını JSON Schema'ya çevirip meta.json ile birlikte `library/motion/native/sema.json`
dosyasına yazar. Python tarafı (kurgu-denetle, ai-edit kataloğu) yalnız bu dosyayı okur; TypeScript çalıştırmaz.
"""

from __future__ import annotations

import functools
import json
from pathlib import Path

from . import paths

SEMA = paths.LIBRARY / "motion" / "native" / "sema.json"

# Zanaat sınırları (motion-design skill'i, ADR 0045). Süre saniye.
SURE_SINIRI = {"ikon": (1.0, 1.6), "altbant": (2.5, 4.0), "kart": (0.8, 3.0), "cizim": (0.8, 2.5), "cta": (1.5, 4.0)}


def sema_yolu() -> Path:
    return paths.LIBRARY / "motion" / "native" / "sema.json"


@functools.lru_cache(maxsize=4)
def _oku(yol: str, _mtime: int) -> dict:
    return json.loads(Path(yol).read_text(encoding="utf-8"))


def kayitlar() -> dict[str, dict]:
    """ad → {"meta": {...}, "sema": JSON Schema}. Dosya yoksa boş (bileşen henüz üretilmedi)."""
    f = sema_yolu()
    if not f.exists():
        return {}
    return _oku(str(f), f.stat().st_mtime_ns).get("bilesenler", {})


def param_hatalari(ad: str, param: dict) -> list[str]:
    import jsonschema

    k = kayitlar().get(ad)
    if not k:
        return [f"bilinmeyen native bileşen '{ad}' (geçerli: {', '.join(sorted(kayitlar())) or 'yok'})"]
    v = jsonschema.Draft202012Validator(k["sema"])
    return [f"{'.'.join(map(str, e.absolute_path)) or 'param'}: {e.message}" for e in sorted(v.iter_errors(param), key=str)]


def hatalar(c) -> list[str]:
    """Render'ı bozacak yanlışlar: tür, ad, parametre. Zanaat uyarıları kurgu_kalite'dedir."""
    if c.bilesen is None:
        return []
    h = []
    if c.tur != "motion":
        h.append(f"{c.id}: bilesen yalnız motion klibinde olur")
    if c.sablon is not None or c.kaynak:
        h.append(f"{c.id}: bilesen ile sablon ya da kaynak birlikte olmaz")
    h += [f"{c.id}: bileşen {c.bilesen.ad}: {e}" for e in param_hatalari(c.bilesen.ad, c.bilesen.param)]
    return h


def sure_siniri(c) -> tuple[float | None, float | None]:
    """Native bileşenin (en az, en çok) süresi: meta `sure.min/max`, yoksa türün sınırı. Bilinmeyen bileşen: (None, None)."""
    k = kayitlar().get(c.bilesen.ad) if c.bilesen else None
    if not k:
        return None, None
    alt, ust = SURE_SINIRI.get(k["meta"].get("tur"), (None, None))
    m = k["meta"].get("sure") or {}
    return m.get("min", alt), m.get("max", ust)


def sure_uyarisi(c) -> str | None:
    alt, ust = sure_siniri(c)
    if alt is not None and c.sure < alt - 1e-3:
        return f"{c.id}: {c.bilesen.ad} {c.sure:.2f} sn kısa (en az {alt} sn; okunamaz)"
    if ust is not None and c.sure > ust + 1e-3:
        return f"{c.id}: {c.bilesen.ad} {c.sure:.2f} sn uzun (en çok {ust} sn; ekranda asılı kalır)"
    return None


def katalog_ozeti(izinli: set[str] | None = None) -> list[str]:
    """ai-edit bağlam paketi: tek satırda ad, tür, ne zaman, süre, parametre adları."""
    sat = []
    for ad, k in sorted(kayitlar().items()):
        m = k["meta"]
        if izinli is not None and ad not in izinli:
            continue
        s = m.get("sure") or {}
        par = ", ".join(f"{p}{'' if p in k['sema'].get('required', []) else '?'}" for p in (k["sema"].get("properties") or {}))
        sat.append(f"- `{ad}` ({m.get('tur')}, {s.get('varsayilan', '?')} sn): {m.get('ne_zaman', '')} · param: {par or '-'}")
    return sat


FAZLAR = {"giris": 0.15, "tut": 0.55, "cikis": 0.92}


def kontak(adlar: list[str] | None, cikti: Path, *, tema: str | None = None, kare: Path | None = None,
           hucre: tuple[int, int] = (360, 640), sutun: int = 6) -> list[Path]:
    """Galeri kontağı: her evre (giriş, tutma, çıkış) için dama zeminde ve gerçek karede birer jpg (ADR 0045).

    Dama zemin alfa kaybını, gerçek kare okunurluğu gösterir. Renk ve font `tema` stilinden (yoksa varsayılan).
    WHY: bkz. wiki/decisions/0051-uctan-uca-hyperframes.md. Bileşenler HyperFrames sahnesidir; kontak `studio/hf/kontak.ts`
    ile kurulur ve `hyperframes snapshot` ile tek anda yakalanır (eskiden Remotion still).
    """
    import os
    import shutil
    import subprocess
    import tempfile

    from . import hf, hf_grafik, hf_kurgu, tema_token

    adlar = adlar or sorted(kayitlar())
    studio = paths.ROOT / "studio"
    vite = studio / "node_modules" / ".bin" / ("vite-node.cmd" if os.name == "nt" else "vite-node")
    cikti.mkdir(parents=True, exist_ok=True)
    t = tema_token.oku(tema) if tema else None
    css = hf_kurgu.tema_css(tema)
    yazilan = []
    with tempfile.TemporaryDirectory(prefix="kontak-", dir=paths.ROOT / "work") as gecici:
        for zemin in (["dama", "kare"] if kare else ["dama"]):
            for faz, deger in FAZLAR.items():
                proje = Path(gecici) / f"{zemin}-{faz}"
                (proje / "fonts").mkdir(parents=True)
                for f in hf_grafik._font_dosyalari():
                    shutil.copy2(f, proje / "fonts" / f.name)
                secenek = Path(gecici) / f"{zemin}-{faz}.json"
                secenek.write_text(json.dumps({"adlar": adlar, "zemin": zemin, "kare": str(kare.resolve()) if kare else None, "faz": deger,
                                               "hucre": {"w": hucre[0], "h": hucre[1]}, "sutun": sutun,
                                               "tema": t.model_dump() if t else None, "tema_css": css}), encoding="utf-8")
                r = subprocess.run([str(vite), "--config", "web/vite.config.ts", "hf/kontak.ts", "--", str(secenek), str(proje)], cwd=studio,
                                   capture_output=True, text=True, encoding="utf-8", errors="replace", shell=os.name == "nt")
                satir = next((x for x in reversed(r.stdout.strip().splitlines()) if x.startswith("{")), None)
                if r.returncode or not satir:
                    raise RuntimeError(f"kontak derlenemedi: {(r.stderr or r.stdout)[-1200:]}")
                an = json.loads(satir)["t"]
                kareler = Path(gecici) / f"{zemin}-{faz}-kare"
                hf.run(["snapshot", str(proje), "--at", f"{an:.4f}", "--no-end", "--output", str(kareler)], cwd=proje)
                png = sorted(kareler.rglob("*.png"))
                if not png:
                    raise RuntimeError(f"kontak karesi alınamadı: {zemin}-{faz}")
                hedef = cikti / f"galeri-{zemin}-{faz}.jpg"
                subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(png[0]), "-q:v", "3", str(hedef)], check=True)
                yazilan.append(hedef)
    return yazilan
