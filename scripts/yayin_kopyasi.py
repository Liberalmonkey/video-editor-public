"""Herkese açık yayın için temiz kopya üretir: son commit'in dosyaları, dağıtılamayan parçalar çıkarılmış, taranmış.

Geçmiş taşınmaz. Kopya ayrı bir klasöre yazılır; oradan ayrı bir repoya tek commit olarak gönderilir.

Kullanım:
  python scripts/yayin_kopyasi.py <hedef-klasör>     # hedef boş olmalı ya da yalnız .git içermeli
Çıkış kodu 1: taramada gizli anahtar ya da kişisel iz bulundu.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tarfile
import io
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
# Dağıtım izni olmayan ya da kişisel parçalar. WHY: bkz. THIRD_PARTY_NOTICES.md, "Repoda olmayanlar".
# Müşteri markası. Parçalardan kurulur: düz yazılsa bu betiğin yayın kopyası da kendi temizliğine uğrardı.
MARKA_AD = "net" + "2lead"
MARKA_AD_BUYUK = "Net" + "2Lead"
HARIC = [f"studios/ugc/styles/{MARKA_AD}"]
# Kopyada değiştirilen adlar: müşteri markası örnek adla, özel skill kütüphanesi genel adla, klon adresi public repoyla.
# Sıra önemli: uzun kalıp önce. WHY: önceki yayınlarda elle yapılan temizlik, artık her kopyada kendiliğinden.
DEGISTIR = [(f"{MARKA_AD_BUYUK} Sistem".encode(), b"skill-kutuphanesi"), (MARKA_AD.upper().encode(), "ÖRNEK MARKA".encode()),
            (MARKA_AD_BUYUK.encode(), "Örnek Marka".encode()), (MARKA_AD.encode(), b"ornek-marka"),
            (b"github.com/Liberalmonkey/video-editor-public.git", b"github.com/Liberalmonkey/video-editor-public.git")]
MARKA = re.compile(MARKA_AD.encode(), re.I)  # değiştirmeden kaçan iz (ör. başka harf düzeni) bulgu sayılır
GIZLI = re.compile(rb"sk-ant-[A-Za-z0-9_-]{20,}|AIza[0-9A-Za-z_-]{35}|ghp_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{40,}"
                   rb"|-----BEGIN [A-Z ]*PRIVATE KEY|xox[bp]-[0-9A-Za-z-]{20,}")
KISISEL = re.compile(rb"[A-Za-z]:[\\/]+Users[\\/]+[A-Za-z0-9._-]+|/home/[a-z][a-z0-9._-]+/|[A-Za-z0-9._%+-]+@(gmail|hotmail|outlook|yahoo)\.com", re.I)
# Üçüncü taraf kaynakların kendi yazar iletişimleri kişisel iz sayılmaz.
KISISEL_HARIC = ("library/vendor/", "licenses/", ".claude/skills/hyperframes", ".agents/skills/hyperframes")
MEDYA = (".mp4", ".mov", ".mkv", ".webm", ".wav", ".mp3", ".m4a", ".srt")


def _temizle(hedef: Path) -> list[str]:
    """Kopyadaki metinlerde proje kökünün mutlak yolunu göreli yapar (ör. ajan notlarındaki `file:///<kök>/`) ve DEGISTIR'i uygular.

    WHY: `raw/` asla değiştirilmez (wiki kuralı), ama içindeki ajan notları makinenin mutlak yolunu ve marka adını taşır.
    Düzeltme yalnız yayın kopyasında yapılır; kaynak dokunulmaz kalır.
    """
    kok = KOK.as_posix()
    kaliplar = [f"file:///{kok}/", f"{kok}/", f"{KOK}\\", str(KOK).replace("\\", "\\\\") + "\\\\"]  # son kalıp: JSON kaçışlı biçim (çift ters bölü)
    kaliplar = sorted({k.encode() for k in kaliplar} | {k.lower().encode() for k in kaliplar}, key=len, reverse=True)
    degisimler = [(k, b"") for k in kaliplar] + DEGISTIR
    degisen = []
    for f in hedef.rglob("*"):
        if not f.is_file() or ".git" in f.relative_to(hedef).parts:
            continue
        veri = f.read_bytes()
        if b"\0" in veri[:2048]:
            continue
        yeni = veri
        for eski, yerine in degisimler:
            yeni = yeni.replace(eski, yerine)
        if yeni != veri:
            f.write_bytes(yeni)
            degisen.append(f.relative_to(hedef).as_posix())
    return degisen


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    hedef = Path(sys.argv[1]).resolve()
    hedef.mkdir(parents=True, exist_ok=True)
    kalan = [p for p in hedef.iterdir() if p.name != ".git"]
    for p in kalan:  # önceki kopyanın dosyaları: silinen dosya yeni kopyada kalmasın
        shutil.rmtree(p) if p.is_dir() else p.unlink()
    arsiv = subprocess.run(["git", "archive", "HEAD"], cwd=KOK, capture_output=True, check=True).stdout
    with tarfile.open(fileobj=io.BytesIO(arsiv)) as t:
        t.extractall(hedef, filter="data")
    for h in HARIC:
        shutil.rmtree(hedef / h, ignore_errors=True)
    goreli = _temizle(hedef)

    bulgu, medya, n = [], [], 0
    for f in hedef.rglob("*"):
        if not f.is_file() or ".git" in f.relative_to(hedef).parts:
            continue
        n += 1
        yol = f.relative_to(hedef).as_posix()
        if f.suffix.lower() in MEDYA:
            medya.append(yol)
        veri = f.read_bytes()
        if b"\0" in veri[:2048]:
            continue  # ikili dosya
        if m := GIZLI.search(veri):
            bulgu.append(f"gizli anahtar: {yol}: {m.group(0)[:12].decode(errors='replace')}…")
        if MARKA.search(veri) or MARKA.search(yol.encode()):
            bulgu.append(f"marka izi: {yol}")
        if not yol.startswith(KISISEL_HARIC) and (m := KISISEL.search(veri)):
            bulgu.append(f"kişisel iz: {yol}: {m.group(0).decode(errors='replace')}")
    print(f"{n} dosya -> {hedef}")
    print(f"çıkarılan: {', '.join(HARIC)}")
    for x in goreli:
        print(f"temizlendi: {x}")
    for x in medya:
        print(f"medya: {x}")
    for x in bulgu:
        print(f"BULGU  {x}")
    if not (hedef / "LICENSE").is_file():
        bulgu.append("LICENSE yok")
        print("BULGU  LICENSE yok")
    print("Temiz." if not bulgu else f"{len(bulgu)} bulgu: gönderme.")
    return 1 if bulgu else 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
