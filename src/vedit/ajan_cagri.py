"""vedit komutlarının içinden headless ajan (Claude Code, Antigravity, Codex, OpenCode) çağrısı. WHY: bkz. wiki/decisions/0028-ai-edit.md

Ajan yalnız dosya okur ve yazar; kabuk komutlarını (hazirla, taslak, final) vedit kendisi koşar, çünkü headless
ajanlarda komut izni yoktur. Uzun istek dosyaya yazılır, ajana yalnız dosyanın yolu verilir (Windows komut satırı sınırı).
Motor tablosu ve akış çevirisi `motorlar.py`'dedir; Stüdyo AI paneliyle aynıdır.
"""

from __future__ import annotations

import os
import subprocess
import threading
from pathlib import Path
from types import SimpleNamespace

from . import motorlar, paths

MOTORLAR = tuple(motorlar.MOTORLAR)
AJAN_SURE = 3600  # sn; tek headless ajan çağrısının üst sınırı. WHY: tek ajan ai-edit tüm kurguyu tek çağrıda yazar, swarm kartından (ekip.AJAN_SURE 1800) uzun sürebilir


def agac_oldur(s: subprocess.Popen) -> None:
    """Süreci ve alt süreçlerini sonlandırır; Windows'ta boruyu tutan çocuk süreçler açık kalmasın."""
    # WHY: Windows'ta s.kill() yalnız ana süreci öldürür; boruyu miras alan alt süreçler stdout okumasını kilitler.
    if s.poll() is not None:
        return
    if os.name == "nt":
        try:
            subprocess.run(["taskkill", "/T", "/F", "/PID", str(s.pid)], capture_output=True, timeout=15)
            return
        except (OSError, subprocess.SubprocessError):
            pass
    try:
        s.kill()
    except OSError:
        pass


def komut(istek: str, motor: str, model: str | None, oturum: str | None, seviye: str | None = None) -> list[str]:
    """Düzenle modunda tam komut; model yoksa motorun kendi varsayılanı.

    Claude'da MCP sunucuları ve slash komutları yüklenmez (ADR 0054): ajan yalnız dosya okur ve yazar, 15 MCP sunucusunun ve
    151 komutun araç tanımı her istekte boşa token ve süre harcıyordu. Araçlar ve oturum sürdürme (--resume) korunur."""
    k = motorlar.komut(motor, istek, model, "duzenle", oturum, seviye)
    if motor == "claude":
        i = k.index("-p")
        k = [*k[:i], "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}', "--disable-slash-commands", *k[i:]]
    return k


def calistir(istek: str, *, motor: str = "claude", model: str | None = None, oturum: str | None = None,
             seviye: str | None = None, sure: float | None = None) -> tuple[str, str | None]:
    """Ajanı çalıştırır, okunur satırları canlı basar. (yanıt metni, oturum kimliği) döner; hata SystemExit."""
    sinir = AJAN_SURE if sure is None else sure
    is_ = SimpleNamespace(oturum=oturum, model=model or "varsayılan")
    cevir, satirlar = motorlar.cevirici(), []
    s = subprocess.Popen(komut(istek, motor, model, oturum, seviye), cwd=paths.ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         stdin=subprocess.DEVNULL, text=True, encoding="utf-8", errors="replace",
                         env={**os.environ, "NO_COLOR": "1"})
    zaman_asimi = False

    def _zaman_doldu() -> None:
        nonlocal zaman_asimi
        zaman_asimi = True
        agac_oldur(s)

    # WHY: zaman aşımı veya iptalde süreç ağacı sonlandırılır ve stdout kapatılarak sonsuz bekleme önlenir.
    zaman = threading.Timer(sinir, _zaman_doldu)
    zaman.start()
    try:
        for ham in s.stdout:
            for satir in cevir(is_, ham.rstrip()):
                print(f"  {satir[:2000]}", flush=True)
                satirlar.append(satir)
        kod = s.wait()
    finally:
        zaman.cancel()
        if s.poll() is None:
            agac_oldur(s)
            try:
                s.wait(timeout=5)
            except subprocess.TimeoutExpired:
                pass
        if s.stdout:
            try:
                s.stdout.close()
            except OSError:
                pass
    hata = next((x for x in satirlar if x.startswith("Hata:")), None)
    if zaman_asimi:
        raise SystemExit(f"Ajan zaman aşımı ({motor}, {sinir} sn)")
    if kod or hata:
        raise SystemExit(f"Ajan başarısız ({motor}, kod {kod}): {hata or (satirlar[-1] if satirlar else 'çıktı yok')}")
    return "\n".join(satirlar), is_.oturum


def dosyadan(istek_dosyasi: Path, **ek) -> tuple[str, str | None]:
    return calistir(f"Read the file {istek_dosyasi.resolve()} completely and do exactly what it says. "
                    "Do not run shell commands; only read and write files.", **ek)
