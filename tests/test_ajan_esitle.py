"""Antigravity ve Codex kopyaları Claude kaynağıyla eşit olmalı."""
import importlib.util
import tomllib
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("ajan_esitle", KOK / "scripts" / "ajan_esitle.py")
es = importlib.util.module_from_spec(spec)
spec.loader.exec_module(es)


def test_kopyalar_esit():
    assert es.farklar() == [], "python scripts/ajan_esitle.py çalıştır"


def test_uretilenler_gecerli():
    for y, b in es.beklenen().items():
        if y.suffix == ".toml":
            tomllib.loads(b.decode())
    assert b".Codex/" not in b"".join(es.beklenen().values()), "kör metin değişimi geri gelmesin"


def test_antigravity_alt_ajan():
    metin = (KOK / ".agents" / "agents" / "render-qc.md").read_text(encoding="utf-8")
    alan, _ = es.onyuz(metin)
    assert alan["name"] == "render-qc" and alan["model"] == "flash"
    assert "run_command" in metin and "read_file" in metin


def test_kurallar_satir_ici_aliniyor():
    # Antigravity `@dosya` biçimini içe almaz; `@[ad](yol)` ister. Dosya başına sınır 24 000 bayt.
    agents = (KOK / "AGENTS.md").read_text(encoding="utf-8")
    assert "@[CLAUDE.md](CLAUDE.md)" in agents
    assert len((KOK / "AGENTS.md").read_bytes()) + len((KOK / "CLAUDE.md").read_bytes()) < 24000
