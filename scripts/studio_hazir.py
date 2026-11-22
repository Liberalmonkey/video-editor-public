"""studio.bat için hızlı hazırlık denetimi; ağır modül yüklemez.

Çıkış kodu: 0 hazır, 1 Python bağımlılığı eksik, 2 arayüz yeniden derlenmeli.
Mantık src/vedit/studio/baslat.py içindedir (ADR 0050); bu betik eski çağrılar için kalır.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from vedit.studio.baslat import hazirlik  # noqa: E402

sys.exit(hazirlik())
