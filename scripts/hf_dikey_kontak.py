"""HyperFrames kompozisyonlarının dikey (1080x1920) ve yatay (1920x1080) kontak sayfası.

Kullanım:
    .venv/Scripts/python -X utf8 scripts/hf_dikey_kontak.py kamera-crash-zoom akis-ajan-agi [--tema minimal-diyagram]
    .venv/Scripts/python -X utf8 scripts/hf_dikey_kontak.py --hepsi --yalniz-dikey

Her kompozisyon `hf_grafik.uret` ile (sekans boyutuna ezilerek) saydam WebM olarak üretilir, temanın zemin rengine bindirilir
ve süresinin %30, %60 ve %90'ındaki kareler yan yana dizilir. Üst sıra dikey, alt sıra yatay. Çıktı
`work/hf-dikey/<ad>.jpg`; WebM önbelleği `work/hf-dikey/webm/` (kompozisyon, tema ya da boyut değişince yeniden üretilir).
WHY: bkz. wiki/specs/hf-canli-gomme-ve-dikey-duzen.md. 46 kompozisyon 16:9 tanımlıydı, 9:16 Reels'te okunmuyordu.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KOK / "src"))

from vedit import hf_grafik, motion  # noqa: E402

CIKTI = KOK / "work" / "hf-dikey"
ORANLAR = {"dikey": (1080, 1920), "yatay": (1920, 1080)}
YUZDE = (0.3, 0.6, 0.9)
SIRA_Y = 640  # kontak sayfasında satır yüksekliği (px)


def zemin(tema: str) -> str:
    t = motion.tema_yolu(tema) or motion.tema_yolu("varsayilan")
    m = re.search(r"--zemin\s*:\s*(#[0-9A-Fa-f]{6})", t.read_text(encoding="utf-8")) if t else None
    return (m.group(1) if m else "#808080").replace("#", "0x")


def satir(webm: Path, sure: float, renk: str, hedef: Path) -> Path:
    """Saydam WebM'den üç kare, zemin rengine bindirilmiş, yan yana."""
    # WHY: saydam VP9'da girişten önceki -ss yanlış kareye atlıyordu; kare çıkış tarafında, tam konumda alınır.
    kareler = []
    for i, y in enumerate(YUZDE):
        k = hedef.with_name(f"{hedef.stem}.{i}.png")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-c:v", "libvpx-vp9", "-i", str(webm), "-ss", f"{sure * y:.3f}",
                        "-frames:v", "1", "-filter_complex",
                        f"[0:v]format=rgba,scale=-2:{SIRA_Y}[k];color=c={renk}:s=16x16[z];[z][k]scale2ref[zb][kb];"
                        "[zb][kb]overlay=format=auto,drawbox=c=white@0.6:t=2", str(k)], check=True)
        kareler.append(k)
    girdi = [x for k in kareler for x in ("-i", str(k))]
    subprocess.run(["ffmpeg", "-v", "error", "-y", *girdi, "-filter_complex", f"hstack=inputs={len(kareler)}", str(hedef)], check=True)
    for k in kareler:
        k.unlink(missing_ok=True)
    return hedef


def kontak(ad: str, tema: str, oranlar: list[str], etiket: str = "") -> Path:
    renk = zemin(tema)
    satirlar = []
    for oran in oranlar:
        f, bilgi = hf_grafik.uret(ad, None, tema, CIKTI, CIKTI / "webm", sekans=ORANLAR[oran])
        satirlar.append(satir(f, float(bilgi["sure"]), renk, CIKTI / f".{ad}-{oran}.png"))
    hedef = CIKTI / f"{ad}{'-' + etiket if etiket else ''}.jpg"
    if len(satirlar) == 1:
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(satirlar[0]), "-q:v", "3", str(hedef)], check=True)
    else:
        # Dikey satır (3 × 360 px) yatay satırdan (3 × 1138 px) dardır: sola yaslanıp sağı doldurulur.
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(satirlar[0]), "-i", str(satirlar[1]), "-filter_complex",
                        "[0:v]pad=w=3414:h=ih:x=0:y=0:color=0x202020[d];[1:v]pad=w=3414:h=ih:x=0:y=0:color=0x202020[e];"
                        "[d][e]vstack=inputs=2",
                        "-q:v", "3", str(hedef)], check=True)
    for s in satirlar:
        s.unlink(missing_ok=True)
    return hedef


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("adlar", nargs="*")
    ap.add_argument("--hepsi", action="store_true", help="kütüphanedeki bütün kompozisyonlar")
    ap.add_argument("--tema", default="minimal-diyagram")
    ap.add_argument("--yalniz-dikey", action="store_true")
    ap.add_argument("--etiket", default="", help="çıktı adına ek, ör. once: <ad>-once.jpg")
    a = ap.parse_args()
    adlar = hf_grafik.adlar(None) if a.hepsi else a.adlar
    if not adlar:
        ap.error("kompozisyon adı ya da --hepsi")
    CIKTI.mkdir(parents=True, exist_ok=True)
    oranlar = ["dikey"] if a.yalniz_dikey else ["dikey", "yatay"]
    hata = 0
    for ad in adlar:
        try:
            print(f"{ad}: {kontak(ad, a.tema, oranlar, a.etiket).relative_to(KOK)}", flush=True)
        except Exception as e:  # noqa: BLE001 - bir kompozisyonun hatası ötekileri durdurmasın
            hata += 1
            print(f"{ad}: HATA {type(e).__name__}: {str(e)[:300]}", flush=True)
    sys.exit(1 if hata else 0)


if __name__ == "__main__":
    main()
