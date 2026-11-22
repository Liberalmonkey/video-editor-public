"""Claude kaynaklarından diğer ajanların kopyalarını üretir: Antigravity CLI ve Codex.

Tek kaynak `.claude/` altındadır; elle `.agents/` ya da `.codex/` düzenleme, burada üret.
WHY: bkz. wiki/decisions/0023-coklu-ajan.md. Eski kopya kör "Claude -> Codex" değişimiyle `.Codex/...` gibi
var olmayan yollar üretmişti. Skill'ler artık birebir kopyalanır.

Antigravity: skill `.agents/skills/<ad>/SKILL.md`, alt ajan `.agents/agents/<ad>.md`, kural `AGENTS.md`
(https://antigravity.google/docs/skills/, /docs/subagents/, /docs/rules/).

Kullanım:
  python scripts/ajan_esitle.py            # yaz
  python scripts/ajan_esitle.py --denetle  # fark varsa listele, çıkış kodu 1
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
SKILL = KOK / ".claude" / "skills"
AJAN = KOK / ".claude" / "agents"

# Claude araç adı -> Antigravity araç adı. WHY: eşlenmemiş ya da yanlış yazılmış araç adı sessizce düşer.
# agy 1.5.9'da ölçüldü (2026-11-15): read_file, write_file, edit_file, run_command, search_web, invoke_subagent,
# run_workflow. Eski view_file read_file'a çevriliyor, find_by_name düşüyordu. Ayrı arama aracı yok: Glob ve Grep
# read_file ile karşılanır.
AGY_ARAC = {"Read": ["read_file"], "Write": ["write_file"], "Edit": ["edit_file"], "Glob": ["read_file"],
            "Grep": ["read_file"], "Bash": ["run_command"], "WebFetch": ["search_web"], "WebSearch": ["search_web"],
            "Agent": ["invoke_subagent", "run_workflow"]}
# Claude modeli -> Antigravity: inherit | flash | pro
AGY_MODEL = {"opus": "pro", "sonnet": "pro", "haiku": "flash"}


def onyuz(metin: str) -> tuple[dict[str, str], str]:
    """Düz YAML ön yüzü: `anahtar: değer` satırları. Skill ve ajan dosyalarımız iç içe yapı kullanmaz."""
    m = re.match(r"---\r?\n(.*?)\r?\n---\r?\n?(.*)", metin, re.S)
    if not m:
        return {}, metin
    alan = {}
    for satir in m.group(1).splitlines():
        a, _, d = satir.partition(":")
        if d:
            alan[a.strip()] = d.strip()
    return alan, m.group(2)


def toml_metin(s: str) -> str:
    # Çok satırlı metin okunur kalsın: TOML ham çok satırlı dize, içinde ''' yoksa.
    if "\n" in s and "'''" not in s:
        return "'''\n" + s + "'''"
    return json.dumps(s, ensure_ascii=False)


def beklenen() -> dict[Path, bytes]:
    cikti: dict[Path, bytes] = {}
    for d in sorted(p for p in SKILL.iterdir() if (p / "SKILL.md").is_file()):
        for f in d.rglob("*"):
            if f.is_file() and "__pycache__" not in f.parts:
                cikti[KOK / ".agents" / "skills" / f.relative_to(SKILL)] = f.read_bytes()

    for f in sorted(AJAN.glob("*.md")):
        alan, govde = onyuz(f.read_text(encoding="utf-8"))
        araclar = list(dict.fromkeys(x for a in alan.get("tools", "").split(",") for x in AGY_ARAC.get(a.strip(), [])))
        ust = [f"name: {alan['name']}", f"description: {json.dumps(alan['description'], ensure_ascii=False)}",
               f"model: {AGY_MODEL.get(alan.get('model', ''), 'inherit')}"]
        if araclar:
            ust.append("tools:\n" + "\n".join(f"  - {a}" for a in araclar))
        cikti[KOK / ".agents" / "agents" / f.name] = ("---\n" + "\n".join(ust) + "\n---\n" + govde).encode()
        cikti[KOK / ".codex" / "agents" / f"{alan['name']}.toml"] = (
            f"name = {toml_metin(alan['name'])}\ndescription = {toml_metin(alan['description'])}\n"
            f"developer_instructions = {toml_metin(govde)}\n").encode()
    return cikti


def eski_kopyalar() -> list[Path]:
    """Kaynakta artık olmayan, üretilmiş dosyalar."""
    bilinen = set(beklenen())
    l = [f for f in (KOK / ".agents" / "skills").rglob("*") if f.is_file() and "__pycache__" not in f.parts]
    l += list((KOK / ".agents" / "agents").glob("*.md")) + list((KOK / ".codex" / "agents").glob("*.toml"))
    return [f for f in l if f not in bilinen]


def ayni(y: Path, b: bytes) -> bool:
    # Windows klonunda git CRLF ile açar (core.autocrlf); satır sonu fark sayılmaz.
    return y.exists() and y.read_bytes().replace(b"\r\n", b"\n") == b.replace(b"\r\n", b"\n")


def farklar() -> list[str]:
    f = [str(y.relative_to(KOK)) for y, b in beklenen().items() if not ayni(y, b)]
    return f + [f"fazla: {y.relative_to(KOK)}" for y in eski_kopyalar()]


def main() -> int:
    if "--denetle" in sys.argv:
        f = farklar()
        for x in f:
            print(x)
        if f:
            print(f"{len(f)} dosya eşit değil: python scripts/ajan_esitle.py")
        return 1 if f else 0
    for y, b in beklenen().items():
        if not ayni(y, b):
            y.parent.mkdir(parents=True, exist_ok=True)
            y.write_bytes(b)
    for y in eski_kopyalar():
        y.unlink()
    print("Ajan kopyaları eşitlendi.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
