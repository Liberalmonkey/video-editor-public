"""Wiki sağlık kontrolü (mekanik kısım).

Kontroller:
  - kırık wikilink'ler ([[hedef]] var olmayan bir sayfayı gösteriyor)
  - öksüz sayfalar (index dışında hiçbir sayfadan link almıyor)
  - index.md'de listelenmeyen sayfalar
  - eksik / hatalı frontmatter alanları
  - log.md başlık formatı

Kullanım:  python scripts/wiki_lint.py [--json]
Çıkış kodu: hata varsa 1, yoksa 0 (uyarılar çıkış kodunu etkilemez).
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WIKI = ROOT / "wiki"
META_PAGES = {"index", "log", "overview"}
REQUIRED = ("type", "title", "created", "updated")
TYPES = {"source", "concept", "entity", "decision", "spec", "query", "overview"}
STATUS = {
    "decision": {"proposed", "accepted", "superseded", "rejected"},
    "spec": {"draft", "active", "done", "dropped"},
}
TYPE_DIRS = {
    "source": "sources", "concept": "concepts", "entity": "entities",
    "decision": "decisions", "spec": "specs", "query": "queries",
}
LINK_RE = re.compile(r"(?<!!)\[\[([^\]|#^]+)(?:[#^][^\]|]*)?(?:\|[^\]]*)?\]\]")
CODE_RE = re.compile(r"```.*?```|`[^`\n]*`", re.S)
LOG_RE = re.compile(
    r"^## \[\d{4}-\d{2}-\d{2}\] (ingest|query|lint|decision|spec|code|setup|refactor) \| .+"
)


def parse_frontmatter(text: str) -> dict[str, str] | None:
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    fm = {}
    for line in text[3:end].splitlines():
        m = re.match(r"^([A-Za-z_]+):\s*(.*)$", line)
        if m:
            fm[m.group(1)] = m.group(2).strip().strip('"')
    return fm


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    pages = {p.stem: p for p in WIKI.rglob("*.md")}
    # raw/ ve diğer kök klasörlere yapılan yol linkleri ([[raw/articles/x]]) için
    vault_files = {
        str(p.relative_to(ROOT).with_suffix("")).replace("\\", "/")
        for p in ROOT.rglob("*")
        if p.is_file() and not any(part.startswith(".") for part in p.relative_to(ROOT).parts)
    }
    errors: list[str] = []
    warnings: list[str] = []
    inbound: dict[str, set[str]] = {name: set() for name in pages}
    index_links: set[str] = set()

    dupes = {}
    for p in WIKI.rglob("*.md"):
        dupes.setdefault(p.stem, []).append(p)
    for name, paths in dupes.items():
        if len(paths) > 1:
            errors.append(f"aynı isimli sayfalar (wikilink belirsiz): {name} -> {[str(x.relative_to(ROOT)) for x in paths]}")

    for name, path in pages.items():
        rel = path.relative_to(ROOT).as_posix()
        text = path.read_text(encoding="utf-8")

        fm = parse_frontmatter(text)
        if fm is None:
            errors.append(f"{rel}: frontmatter yok")
        else:
            for key in REQUIRED:
                if not fm.get(key):
                    errors.append(f"{rel}: frontmatter '{key}' eksik")
            t = fm.get("type")
            if t and t not in TYPES:
                errors.append(f"{rel}: bilinmeyen type '{t}'")
            if t in STATUS and fm.get("status") not in STATUS[t]:
                errors.append(f"{rel}: status '{fm.get('status')}' geçersiz ({'|'.join(sorted(STATUS[t]))})")
            if t in TYPE_DIRS and path.parent.name != TYPE_DIRS[t]:
                warnings.append(f"{rel}: type '{t}' ama klasör '{path.parent.name}' (beklenen {TYPE_DIRS[t]}/)")
            if t != "overview" and not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", name):
                warnings.append(f"{rel}: dosya adı kebab-case ASCII değil")

        body = CODE_RE.sub("", text)
        for target in LINK_RE.findall(body):
            target = target.strip().rstrip("\\")  # tablo içinde [[sayfa\|ad]] kaçışı
            key = target.split("/")[-1]
            if "/" in target and target.removesuffix(".md") in vault_files:
                continue
            if key.removesuffix(".md") in pages:
                key = key.removesuffix(".md")
                if key != name:
                    inbound[key].add("log" if name.startswith("log.part") else name)
                if name == "index":
                    index_links.add(key)
            elif not name.startswith("log"):  # log sadece-ekleme: silinmiş sayfalara tarihsel linkler kalabilir
                errors.append(f"{rel}: kırık link [[{target}]]")

    for name, path in pages.items():
        if name in META_PAGES or name.startswith("log.part"):  # log.partN: bölünmüş günlük arşivi
            continue
        rel = path.relative_to(ROOT).as_posix()
        if name not in index_links:
            errors.append(f"{rel}: index.md'de listelenmemiş")
        if not (inbound[name] - {"index", "log"}):
            warnings.append(f"{rel}: öksüz sayfa (index/log dışında link almıyor)")

    for log in sorted(WIKI.glob("log*.md")):
        for i, line in enumerate(log.read_text(encoding="utf-8").splitlines(), 1):
            if line.startswith("## ") and not LOG_RE.match(line):
                errors.append(f"wiki/{log.name}:{i}: başlık formatı hatalı -> {line}")

    if "--json" in sys.argv:
        print(json.dumps({"pages": len(pages), "errors": errors, "warnings": warnings},
                         ensure_ascii=False, indent=2))
    else:
        print(f"Wiki: {len(pages)} sayfa | {len(errors)} hata | {len(warnings)} uyarı")
        for e in errors:
            print(f"  HATA   {e}")
        for w in warnings:
            print(f"  UYARI  {w}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
