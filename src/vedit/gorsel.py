"""Antigravity CLI (agy) ile ücretsiz görsel üretimi. WHY: bkz. wiki/decisions/0025-gorsel-uretimi-google.md

agy headless modda dosya taşıyamaz; görsel ~/.gemini/antigravity-cli/brain/<conversation_id>/ altına iner.
Bu modül agy'yi çağırır, görseli oradan alıp hedefe kopyalar ve work/gorsel/log.md'ye satır yazar.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from datetime import date, datetime, timezone
from pathlib import Path

BRAIN = Path.home() / ".gemini" / "antigravity-cli" / "brain"
AGY_LOG = Path.home() / ".gemini" / "antigravity-cli" / "log"
UZANTI = (".jpg", ".jpeg", ".png", ".webp")
EFORLAR = ("low", "medium", "high", "xhigh", "max")


def agy_yolu() -> str:
    yol = shutil.which("agy") or str(Path(os.environ.get("LOCALAPPDATA", "")) / "agy" / "bin" / "agy.exe")
    if not Path(yol).exists():
        raise SystemExit("agy yok: PowerShell'de `irm https://antigravity.google/cli/install.ps1 | iex`, sonra `agy` ile giriş")
    return yol


def son_gorsel(klasor: Path) -> Path:
    # WHY: agy 1.5.x görseli image-generator alt ajanına verir; dosya konuşma kökünde ya da alt klasöründe olabilir.
    gorseller = [p for p in klasor.rglob("*") if p.suffix.lower() in UZANTI] if klasor.is_dir() else []
    if not gorseller:
        k = kota()
        if k.get("kapali"):
            raise SystemExit(f"agy görsel kotası dolu ({k['model']}; açılış {k['acilis']}): {klasor}")
        raise SystemExit(f"agy görsel üretmedi (kota dolmuş olabilir): {klasor}")
    return max(gorseller, key=lambda p: p.stat().st_mtime)


def log_yaz(log: Path, motor: str, oran: str, prompt: str, sonuc: str) -> None:
    if not log.exists():
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_text("| tarih | motor | oran | prompt | sonuç |\n|---|---|---|---|---|\n", encoding="utf-8")
    kisa = prompt.replace("|", "/").replace("\n", " ")[:80]
    with log.open("a", encoding="utf-8") as f:
        f.write(f"| {date.today()} | {motor} | {oran} | {kisa} | {sonuc} |\n")


def agy(istek: str, ekler: list[Path] = (), model: str | None = None, efor: str | None = None) -> dict:
    """agy'yi headless çağırır, son JSON satırını döner; başarısızlıkta SystemExit.

    model: yönlendiren model (`agy models`). Görsel modelini seçmez: generate_image agy'nin kendi modelini kullanır (ADR 0052)."""
    komut = [agy_yolu(), "--output-format", "json", "--print-timeout", "600s"]
    if model:
        komut += ["--model", model]
    if efor:
        if efor not in EFORLAR:
            raise SystemExit(f"Efor şunlardan biri olmalı: {', '.join(EFORLAR)}")
        komut += ["--effort", efor]
    for d in ekler:
        komut += ["--add-dir", str(d)]
    komut += ["-p", istek]
    try:
        r = subprocess.run(komut, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=660)
    except subprocess.TimeoutExpired:
        raise SystemExit("agy 10 dakikada yanıt vermedi; daha hızlı bir model seç ya da sonra dene")
    try:
        yanit = json.loads(r.stdout.strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError):
        raise SystemExit(f"agy yanıtı okunamadı:\n{r.stdout[-500:]}\n{r.stderr[-500:]}")
    if yanit.get("status") != "SUCCESS":
        neden = f"{yanit.get('status')} {yanit.get('finished_reason') or ''} {str(yanit.get('response', ''))[:300]}".strip()
        if re.search(r"quota|exhausted|429", neden, re.I):
            acilis = kota().get("acilis")
            raise SystemExit(f"agy kotası dolu{f' (açılış {acilis})' if acilis else ''}: {neden}")
        raise SystemExit(f"agy başarısız: {neden}")
    return yanit


def uret(prompt: str, out: Path, oran: str = "16:9", log: Path | None = None, refler: list[Path] = (),
         model: str | None = None, ref_metni: str | None = None) -> Path:
    """ref_metni: referansların numaralı tarifi (Image 1 ... ); yoksa genel "referansı koru" cümlesi."""
    refler = [Path(r).resolve() for r in refler]
    ref_metin = (
        f"Use these reference image file(s) as visual input for generate_image (pass them as image paths, in this order): "
        f"{', '.join(str(p) for p in refler)}. "
        + (ref_metni or "Keep the subject, style and colors of the reference unless the description says otherwise. ")
    ) if refler else ""
    ekler = [Path(d) for d in sorted({str(r.parent) for r in refler})]
    istek = (f"Use generate_image to create: {prompt}. Aspect ratio {oran}. {ref_metin}"
             "No text, letters or logos in the image. Do not run any commands; just generate the image.")
    yanit = agy(istek, ekler=ekler, model=model) if (ekler or model) else agy(istek)
    kaynak = son_gorsel(BRAIN / yanit["conversation_id"])
    out = out if out.suffix else out.with_suffix(kaynak.suffix)
    out.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(kaynak, out)
    ref_ek = f", ref: {', '.join(r.name for r in refler)}" if refler else ""
    log_yaz(log or out.parent / "log.md", "agy", oran, prompt, f"{out.name}, {yanit.get('duration_seconds', 0):.0f} sn{ref_ek}")
    return out


_KOTA_ONBELLEK: dict = {}


def kota(log_klasoru: Path | None = None) -> dict:
    """agy'nin görsel modeli ve kota açılışı, loglardan: {model, acilis (ISO), kapali}.

    agy görsel modelini seçtirmez; adı ve kotası yalnız kota hatasında loga düşer. Bulunamazsa {"model": None}.
    Loglar (≈300 dosya, ≈9 MB) yeniden okunmasın diye sonuç en yeni logun zamanına göre önbellekte tutulur."""
    kok = log_klasoru or AGY_LOG
    try:
        dosyalar = sorted(kok.glob("cli-*.log"), key=lambda f: f.stat().st_mtime, reverse=True)
    except OSError:
        return {"model": None}
    imza = (str(kok), len(dosyalar), dosyalar[0].stat().st_mtime if dosyalar else 0)
    sonuc: dict = {"model": None}
    if _KOTA_ONBELLEK.get("imza") == imza:
        sonuc = dict(_KOTA_ONBELLEK["sonuc"])
    else:
        for f in dosyalar:
            try:
                metin = f.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            modeller = re.findall(r'"model":\s*"([\w.\-]*image[\w.\-]*)"', metin)
            if modeller:
                acilis = re.findall(r'"quotaResetTimeStamp":\s*"([^"]+)"', metin)
                sonuc = {"model": modeller[-1], "acilis": acilis[-1] if acilis else None}
                break
        _KOTA_ONBELLEK.update(imza=imza, sonuc=dict(sonuc))
    sonuc["kapali"] = False
    if sonuc.get("acilis"):
        try:
            sonuc["kapali"] = datetime.fromisoformat(sonuc["acilis"].replace("Z", "+00:00")) > datetime.now(timezone.utc)
        except ValueError:
            pass
    return sonuc
