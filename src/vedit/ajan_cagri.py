"""vedit komutlarının içinden headless ajan (Claude Code, Antigravity, Codex, OpenCode) çağrısı. WHY: bkz. wiki/decisions/0028-ai-edit.md

Ajan yalnız dosya okur ve yazar; kabuk komutlarını (hazirla, taslak, final) vedit kendisi koşar, çünkü headless
ajanlarda komut izni yoktur. Uzun istek dosyaya yazılır, ajana yalnız dosyanın yolu verilir (Windows komut satırı sınırı).
Motor tablosu ve akış çevirisi `motorlar.py`'dedir; Stüdyo AI paneliyle aynıdır.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from types import SimpleNamespace

from . import motorlar, paths

MOTORLAR = tuple(motorlar.MOTORLAR)


def komut(istek: str, motor: str, model: str | None, oturum: str | None) -> list[str]:
    """Düzenle modunda tam komut; model yoksa motorun kendi varsayılanı.

    Claude'da MCP sunucuları ve slash komutları yüklenmez (ADR 0054): ajan yalnız dosya okur ve yazar, 15 MCP sunucusunun ve
    151 komutun araç tanımı her istekte boşa token ve süre harcıyordu. Araçlar ve oturum sürdürme (--resume) korunur."""
    k = motorlar.komut(motor, istek, model, "duzenle", oturum)
    if motor == "claude":
        i = k.index("-p")
        k = [*k[:i], "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}', "--disable-slash-commands", *k[i:]]
    return k


def calistir(istek: str, *, motor: str = "claude", model: str | None = None, oturum: str | None = None) -> tuple[str, str | None]:
    """Ajanı çalıştırır, okunur satırları canlı basar. (yanıt metni, oturum kimliği) döner; hata SystemExit."""
    is_ = SimpleNamespace(oturum=oturum, model=model or "varsayılan")
    cevir, satirlar = motorlar.cevirici(), []
    s = subprocess.Popen(komut(istek, motor, model, oturum), cwd=paths.ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         stdin=subprocess.DEVNULL, text=True, encoding="utf-8", errors="replace",
                         env={**os.environ, "NO_COLOR": "1"})
    for ham in s.stdout:
        for satir in cevir(is_, ham.rstrip()):
            print(f"  {satir[:2000]}", flush=True)
            satirlar.append(satir)
    kod = s.wait()
    hata = next((x for x in satirlar if x.startswith("Hata:")), None)
    if kod or hata:
        raise SystemExit(f"Ajan başarısız ({motor}, kod {kod}): {hata or (satirlar[-1] if satirlar else 'çıktı yok')}")
    return "\n".join(satirlar), is_.oturum


def dosyadan(istek_dosyasi: Path, **ek) -> tuple[str, str | None]:
    return calistir(f"Read the file {istek_dosyasi.resolve()} completely and do exactly what it says. "
                    "Do not run shell commands; only read and write files.", **ek)
